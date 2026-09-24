# Freal World Manipulation

> 스포일러: 이 문서는 문제의 분석 과정과 최종 풀이를 포함합니다.

## 개요

| 항목 | 내용 |
|---|---|
| 상태 | solved |
| 대회·플랫폼 | PwnSec CTF 2026 |
| 분야 | pwn |
| 난이도 | Medium (500 points) |
| Flag 형식 | `pwnsec{...}` |

이 문제는 decimal 객체 관리기의 인덱스 검증과 부동소수점 예외 처리 순서를 결합해 임의 읽기·쓰기를 만드는 문제다. `__dso_handle` 자기참조로 PIE를 누수하고, 512 MiB 초과 할당 및 overflow 곱셈으로 OOB 인덱스를 연 뒤 GOT, libc, `__environ`, 스택 순으로 주소를 복구한다.

## 환경 및 초기 분석

공식 입력은 [public.zip](../challenge/public.zip), [Dockerfile](../challenge/Dockerfile), [freal](../challenge/src/freal), placeholder [flag.txt](../challenge/flag.txt)이다. ZIP 암호 `infected`는 문제 화면에 공개되어 있다. 공용 Python 환경은 [requirements.txt](../../../requirements.txt)로 복원하지만, 최종 [solve.py](../solve.py)는 Python 표준 라이브러리만 사용한다.

`freal`은 심볼이 남은 x86-64 PIE ELF다. `GNU_RELRO`와 `BIND_NOW`가 있어 Full RELRO이고, `GNU_STACK`은 비실행이며 stack canary도 존재한다. Dockerfile은 Ubuntu 22.04에서 바이너리를 사용자 `ctf`로 실행하고 플래그 파일명을 무작위 suffix로 변경한다.

## 핵심 분석

`decimal`은 `0x5060`, `__dso_handle`은 `0x5008`에 있으므로 index `-11`이 정확히 자기참조 relocation을 가리킨다. `view(-11)`은 relocation된 `PIE+0x5008`을 출력하므로 PIE base를 얻는다.

`calibrated()`는 page-rounded live allocation 합계가 `0x1fffffff`를 초과하는지 검사한다. 첫 8 MiB mmap 청크를 해제하면 glibc의 동적 mmap threshold가 올라가고, 이후 65개 8 MiB 청크가 연속 heap에 배치된다. 두 슬롯에 `1e308`을 넣고 upward rounding으로 곱하면 infinity가 된다. `multiply`가 실제 곱셈 전에 `fetestexcept`를 호출하는 순서 오류 때문에 이를 거부하지 않고, usable size의 곱으로 인덱스 상한을 크게 만든다.

8 MiB 청크 하나를 `p64(PIE+0x5060)`로 채운 뒤 PIE부터 8 MiB 간격으로 최대 약 1 GiB를 탐색한다. 패턴 청크를 만나는 OOB `view`는 `decimal` 테이블 256바이트를 반환한다. 같은 OOB index에 `load`하면 `decimal`을 덮을 수 있으므로 slot 0 pointer와 usable size를 조작해 임의 읽기·쓰기를 얻는다.

그 뒤 `puts@GOT`을 읽고 libc 주소에서 page 단위로 뒤로 이동해 ELF header를 찾는다. solver는 remote ELF의 program header, `PT_DYNAMIC`, GNU hash를 직접 해석해 `system`과 `__environ`을 찾는다. `__environ`으로 스택을 누수하고, `[rsp+8] == rsp+0x10`인 `main` 프레임을 찾아 saved return address에 `ret; pop rdi; ret; command; system`을 쓴다. 세부 offset과 실행 증거는 [evidence.md](../analysis/evidence.md)에 정리했다.

## 풀이 및 재현

대회 루트의 `.venv`를 활성화하고 challenge root에서 실행한다. endpoint가 바뀌면 [instance.json](../instance.json)만 수정한다.

```bash
python -m pip install -r ../../requirements.txt
python -m pip check
python solve.py
```

[solve.py](../solve.py)는 TLS 연결, PIE 누수, heap calibration, OOB pattern 탐색, remote GNU-hash symbol resolution, stack 탐색, ROP 실행을 한 파일에서 비대화형으로 수행한다.

## 결과

로컬 `socat` 래퍼에서는 최종 명령만 `echo pwnsec{local_test}`로 바꾼 검증 실행이 exit code 0과 정확한 stdout `pwnsec{local_test}`를 냈다. 이후 solver는 원격 플래그 명령과 `pwnsec{...}` matcher로 복원했다.

새 원격 인스턴스 `b31501f4e8de5bb6.chal.ctf.ae:443`에 대해 복원된 solver를 실행했다. 실행은 exit code 0으로 종료됐고 stdout은 정확히 `pwnsec{34910c7c74c2525b}`였다. 검증된 플래그는 [flag](../flag)에 기록했다.

## 정리 및 회고

검증 루틴 하나만 보면 방어가 강해 보여도 signed index, pointer coherence, allocation accounting이 서로 다른 경로에서 적용되면 조합 취약점이 생긴다. 또한 libc 파일이 제공되지 않아도 안정적인 임의 읽기가 있으면 in-memory ELF와 GNU hash를 직접 해석해 버전 독립적으로 필요한 심볼을 구할 수 있다.

## 참고 자료

- 공식 제공 `Dockerfile`과 `freal`: 서비스 구성, memory layout, 취약 경로 분석.
- GNU binutils `readelf`, `objdump`, `nm`, `strings`: ELF header, relocation, symbol, gadget 확인.
- 외부 공개 풀이나 동일 문제 write-up은 사용하지 않았다.
