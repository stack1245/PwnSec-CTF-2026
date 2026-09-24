# Death Ops

> 스포일러: 이 문서는 문제의 분석 과정과 최종 풀이를 포함합니다.

## 개요

| 항목 | 내용 |
|---|---|
| 상태 | solved |
| 대회·플랫폼 | PwnSec CTF 2026 |
| 분야 | pwn |
| 난이도 | Medium |
| Flag 형식 | `pwnsec{...}` |

이 문제는 alphanumeric shellcode만 허용하는 seccomp 샌드박스와, 커널 모듈이 제공하는 2회 제한 임의 8바이트 쓰기를 결합한다. 결정적인 관찰은 모듈 주소를 `/proc/modules`에서 얻을 수 있고, 모듈의 `used` 카운터와 실행 코드를 쓰기 원시 기능 자체로 바꿀 수 있다는 점이다. 이를 통해 커널 KASLR을 누출한 뒤 `core_pattern`을 덮어써 root usermode helper로 플래그를 출력한다.

## 환경 및 초기 분석

공식 입력은 암호 `infected`가 설정된 [`public.zip`](../challenge/public.zip)이다. 압축을 해제한 [`dist`](../challenge/public/dist/)에는 Linux 4.9.333 `bzImage`, `rootfs.cpio.gz`, QEMU 실행 스크립트와 Dockerfile이 있다. 공용 Python 환경은 [`../../../requirements.txt`](../../../requirements.txt)에서 challenge root 기준으로 다음과 같이 복원한다.

```bash
python -m pip install -r ../../requirements.txt
python -m pip check
```

`blackops`는 PIE 실행 파일이며 `/dev/shadowops`를 연 뒤 메뉴를 제공한다. Intel Extract는 `flag`가 포함된 경로를 거부하지만 임의 파일의 앞 0x1000바이트를 한 번 출력한다. Payload 경로는 최대 0x60바이트의 alphanumeric 입력만 받고, 이후 seccomp가 `read`, `write`, `exit`, `exit_group`만 허용한다. `shadowops.ko`의 `shadowops_write`는 16바이트 구조체 `{target, value}`를 받아 `*(u64 *)target = value`를 수행하지만 `.bss`의 `used` 때문에 두 번만 성공한다.

## 핵심 분석

먼저 Intel Extract로 `/proc/modules`를 읽으면 `shadowops ... Live 0xffffffffc...` 행에서 독립적으로 랜덤화된 모듈 base를 얻는다. 모듈 배치는 `.text = base`, `.data = base + 0xc80`, `.bss = base + 0xcd0`이며 `used`는 `base + 0xcd0`이다.

초기 alphanumeric 단계는 ALPHA3의 RAX decoder를 사용한다. 복호화된 12바이트 코드는 `read(0, r8+0x7a, 0x60)`으로 두 번째 단계를 불러온다. 이후 단계들은 짧은 read loop로 TCP 분할과 관계없이 각각 0x200바이트와 0x400바이트를 정확히 수신한다.

모듈의 `.text`가 로컬 커널에서 쓰기 가능하므로, 사용하지 않는 `shadowops_open`/`shadowops_release` 영역 `base+0x00..0x1f`에 30바이트 원시 기능을 쓴다. 이 코드는 `count == 8`이면 요청의 첫 qword가 가리키는 커널 주소를 읽어 사용자 요청 버퍼에 돌려주고, `count == 16`이면 `{target, value}` 쓰기를 수행한다. 8바이트 조각 사이마다 `base+0xcd0`을 0으로 만들어 원래 2회 제한을 초기화한 다음, `shadowops_write`의 `base+0x30`을 `jmp base`로 바꾼다.

원래 `shadowops_write+0x57`에는 `_copy_from_user`를 호출하는 `e8 disp32`가 있다. 새 read 원시 기능으로 `base+0x57`의 8바이트를 읽고 다음 식으로 실제 커널 주소와 KASLR slide를 구한다.

```text
copy_from_user = module_base + 0x5c + sign_extend(disp32)
slide = copy_from_user - 0xffffffff81371700
core_pattern = 0xffffffff820674e0 + slide
```

마지막으로 writable kernel data의 `core_pattern`을 다음 문자열로 교체한다.

```text
|/bin/sh -c cat${IFS}/flag*${IFS}>/dev/console
```

사용자 공간에서 NULL을 역참조하면 core dump pipe가 root 권한으로 `/bin/sh`를 실행한다. `${IFS}`를 사용한 이유는 core helper의 공백 기반 argv 분리 뒤에도 세 번째 인자가 하나의 shell command로 유지되게 하기 위해서다. syscall seccomp는 이 신호 및 core-dump 경로를 막지 않는다.

실패한 두 가설도 다음 판단에 영향을 주었다. `sys_call_table` 직접 덮어쓰기는 read-only 매핑에서 page fault가 났고, 위조 LSM hook이 사용자 RWX payload를 호출하도록 한 방식은 KPTI/NX 때문에 사용자 주소 instruction fetch에서 실패했다. `SIDT`로 얻은 IDT 주소도 KASLR slide와 무관하게 고정되어 누출원으로 사용할 수 없었다.

## 풀이 및 재현

전체 구현은 [`solve.py`](../solve.py)에 있다. [`instance.json`](../instance.json)은 TLS endpoint를 보관한다. Competition의 `.venv`를 활성화하고 challenge root에서 실행한다.

```bash
python -m pip install -r ../../requirements.txt
python -m pip check
python solve.py
```

솔버는 최대 세 번 새 연결을 시도하며 성공 시 stdout에 flag만 출력한다. 로컬 재현은 공식 `bzImage`와 `rootfs.cpio.gz`를 사용한 QEMU 인스턴스를 TCP로 노출하고, 검증할 때만 `instance.json`을 로컬 endpoint로 바꾸어 수행했다.

## 결과

KASLR이 켜진 로컬 QEMU에서 여러 번 다음 테스트 플래그를 출력했다.

```text
flag{test_flag_for_ctf_challenge}
```

증거는 [`analysis/validation.txt`](../analysis/validation.txt)에 기록했다. 갱신된 원격 TLS endpoint `9ee4d30c7a4bbd0c.chal.ctf.ae:443`에서 `python solve.py`가 exit status 0으로 다음 flag를 출력했다.

```text
pwnsec{527916de221fe1c8}
```

## 정리 및 회고

횟수 제한 임의 쓰기는 카운터 자체가 writable이면 제한으로 기능하지 않는다. 커널 base를 직접 누출하지 못해도 모듈의 core-kernel relocation을 읽으면 KASLR slide를 복구할 수 있다. 또한 seccomp가 syscall을 강하게 제한해도 signal 처리에서 실행되는 piped core helper처럼 syscall 밖에서 이어지는 커널 경로는 별도로 검토해야 한다.

## 참고 자료

- [`challenge/public/dist/README.md`](../challenge/public/dist/README.md): 커널 버전과 alphabet-seccomp 설명.
- [`challenge/public/dist/rootfs.cpio.gz`](../challenge/public/dist/rootfs.cpio.gz): `blackops`, `shadowops.ko`, init 동작의 정적·동적 분석.
- ALPHA3, commit `4faca5302c81f7ff8a93943d62d765d18569fd4b`: RAX 기반 alphanumeric decoder 생성에 사용.
- 외부 취약점 설명이나 공개 풀이 코드는 사용하지 않았다.
