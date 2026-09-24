# peekaboo

> 스포일러: 이 문서는 문제의 분석 과정과 최종 풀이를 포함합니다.

## 개요

| 항목 | 내용 |
|---|---|
| 상태 | solved |
| 대회·플랫폼 | PwnSec CTF 2026 |
| 분야 | pwn |
| 난이도 | Medium |
| Flag 형식 | `pwnsec{...}` |

프로그램은 플래그를 암호화해 무작위 페이지에 숨긴 뒤 임의 코드를 실행하지만, seccomp가 직접 읽기와 자유로운 출력을 막는다. 결정적인 관찰은 허용된 `mmap(MAP_FIXED_NOREPLACE)`가 기존 매핑과 겹칠 때 `EEXIST`를 반환한다는 점이다. 이 오라클로 페이지 주소를 이진 탐색하고 암호문을 유출한 뒤, 24비트 glibc PRNG seed와 AES-256-GCM-SIV 키를 복원했다.

## 환경 및 초기 분석

공식 입력은 [`public.zip`](../challenge/public.zip), [`prob`](../challenge/prob), [`libcrypto.so.3`](../challenge/lib/libcrypto.so.3)이다. 공용 Python 환경은 [`requirements.txt`](../../../requirements.txt)로 복원하며 solver는 NumPy와 `cryptography`를 사용한다.

`prob`는 stripped x86-64 PIE다. ELF program header, dynamic flags, symbol과 GNU property를 대조해 PIE, NX, stack canary, Full RELRO, IBT, SHSTK를 확인했다. 프로그램은 `./flag`를 읽어 암호화하고, 세 개의 고정 페이지를 매핑한 뒤 `0x3133709a`에서 사용자 코드를 실행한다. TLS 서비스는 입력 전 banner를 보내지 않는다.

## 핵심 분석

세 바이트를 `/dev/urandom`에서 읽어 `srand()`에 전달한다. 첫 `rand()`에 대해 다음 주소를 만든다.

```text
hidden = (0x100000000 + (rand() & 0x3fffff)) << 12
```

암호화된 Base64 문자열은 이 페이지에 남는다. seccomp는 `mmap`, `munmap`, `exit_group`을 허용하고, `write`는 `buf & ~0xfff == 0x31339000`, `count <= 8`일 때만 허용한다.

[`leak.S`](../analysis/leak.S)는 전체 16 GiB 후보 범위의 절반에 `MAP_FIXED_NOREPLACE`를 시도한다. 반환값이 `-EEXIST`이면 숨겨진 페이지가 그 절반에 있고, 성공하면 즉시 `munmap`한 뒤 반대 절반을 선택한다. 22회 후 정확한 4 KiB 페이지가 남는다. 그 내용을 허용된 출력 페이지로 옮겨 8바이트씩 출력한다. 로컬 더미 플래그와 원격에서 모두 264바이트 출력(주소 8바이트와 데이터 256바이트)을 관찰했다.

주소 하위 22비트로 24비트 seed 공간을 거르면 원격에서는 `0x0cbec1`, `0x5abf7c`, `0x8eec08`만 남았다. 각 seed의 다음 32개 `rand()` 하위 바이트를 키로 시험했을 때 `0x5abf7c`만 인증에 성공했다. OpenSSL 호출을 다시 확인하면 저장된 첫 12바이트는 IV 인자가 아니라 `EVP_EncryptUpdate`의 AAD로 전달된다. 따라서 실제 nonce는 `00` 12바이트이고 저장 형식은 `AAD || tag || ciphertext`다. 이 해석은 debugger로 얻은 로컬 키와 버퍼로 더미 플래그를 인증 복호화해 독립적으로 확인했다. 상세 값은 [`findings.md`](../analysis/findings.md)에 보존했다.

## 풀이 및 재현

[`solve.py`](../solve.py)는 `instance.json`에서 TLS endpoint를 읽고, 164바이트 shellcode를 전송한다. 유출된 주소로 NumPy를 사용해 모든 24비트 seed를 검색하고, 후보 키마다 AES-256-GCM-SIV 인증 복호화를 수행한다.

```bash
python -m pip install -r ../../requirements.txt
python -m pip check
python solve.py
```

교체된 live endpoint를 [`instance.json`](../instance.json)에 기록한 뒤 challenge root 밖의 임시 working directory에서도 solver를 재실행했다.

## 결과

인스턴스 만료 전 원격 유출과 인증 복호화로 다음 flag를 확인했다.

```text
pwnsec{ad7aa53d59d0f8af}
```

최종 `python solve.py` 실행은 약 10.7초 만에 exit code 0, 빈 stderr, newline 없는 24바이트 flag만 stdout으로 반환했다. 잘못된 두 seed 후보는 `InvalidTag`로 기각됐다.

## 정리 및 회고

넓은 ASLR 후보 공간도 `MAP_FIXED_NOREPLACE`의 범위 충돌 여부를 사용하면 페이지별 선형 탐색이 아니라 이진 탐색으로 줄일 수 있다. 또한 EVP 호출에서는 버퍼의 의미를 이름으로 추측하지 않고 실제 인자 레지스터를 확인해야 한다. 이 문제에서는 무작위 12바이트가 nonce가 아니라 AAD였고, 그 차이가 인증 성공 여부를 결정했다.

## 참고 자료

외부 자료는 사용하지 않았다. ELF metadata, disassembly, 로컬 debugger 관찰, 제공된 `libcrypto.so.3`, 원격 요청·응답만 사용했다.
