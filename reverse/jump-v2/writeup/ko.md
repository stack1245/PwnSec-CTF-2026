# jump-v2

> 스포일러: 이 문서는 문제의 분석 과정과 최종 풀이를 포함합니다.

## 개요

| 항목 | 내용 |
|---|---|
| 상태 | solved |
| 대회·플랫폼 | PwnSec CTF 2026 |
| 분야 | reverse |
| 난이도 | Hard |
| Flag 형식 | `pwnsec{...}` |

Rust 래퍼가 입력을 ChaCha20으로 변환해 난독화된 내부 ELF에 삽입한다. 내부 프로그램의 seccomp BPF 14개를 복호화하면 최종 상태에 대한 비트 제약이 되고, 체크섬을 함께 풀어 상태를 유일하게 정한 뒤 세 변환을 역산할 수 있다.

## 환경 및 초기 분석

공식 배포물은 암호 `infected`를 사용하는 [public.zip](../challenge/public.zip)과 그 안의 [jump_v2](../challenge/jump_v2)이다. ZIP SHA-256은 `bd9972edbf78713cc4b013335d2c52ea1baf06745d60158df5a7109eefca64e5`, 실행 파일 SHA-256은 `ee8973d9a3a88c6a70e557d1c6cb1fb717b7f72ef41c7bea20e4c654c6e68008`이다. x86-64 PIE Rust 래퍼는 `memfd_create`로 내부 ELF를 실행한다. 내부 ELF는 파일 offset `0x7a90`, 길이 `0x145b48`이며 분석본은 [embedded.elf](../analysis/embedded.elf)이다.

공용 환경은 [requirements.txt](../../../requirements.txt)로 복원했다. 주요 도구는 Python 3.12, Unicorn 2.1.4, Capstone 5.0.3, Z3 5.1.0 및 GNU `objdump`, `strace`, `gdb`이다.

## 핵심 분석

내부 ELF는 `0x5463a0`의 48바이트 입력을 네 단계로 처리한다. 첫 단계는 16바이트 레지스터 세 개를 사용하는 12라운드 shift-register 구조다. 각 라운드는 `PSHUFB`, XOR, `AESENC`를 적용하고 상태를 `(x1, x2, new)`로 이동한다. 두 번째 단계는 각 16바이트 블록에 대해 세 MBA 함수(`0x544218`, `0x5443fa`, `0x54450d`)를 사용하는 8라운드 일반화 Feistel이다. [model_f2.py](../analysis/model_f2.py)는 관측한 모든 라운드 상태와 일치한다. 세 번째 단계는 단어별로 `bswap`, `x ^= x >> {8,16,24}`, `x ^= 0xa1b2c3d4`, `bswap`을 수행한다. 네 번째 단계는 `0x243f6a88`에서 시작해 각 단어마다 `rol(acc ^ word, 5) * 0x9e3779b1 + 0x7f4a7c15`를 계산한다.

복호화한 [filters.bin](../analysis/filters.bin)의 각 BPF는 커스텀 syscall `0x1337`–`0x1344`에 대해 `((arg ^ k1) + k2) & mask == target`을 검사한다. 마스크 제약과 마지막 체크섬을 Z3로 결합하면 13개 상태가 유일해진다. 역산 결과 내부 ELF에 들어가야 할 48바이트는 `55872b6b5f0ab8006676b24b37685c11811e6e757abcad32be64de10f7e8616f8b9795e7f9009478cfa04b535b80a0ad`이다.

Rust 래퍼는 사용자 입력을 고정 ChaCha20 keystream과 XOR한다. `A` 48개의 변환 결과를 memfd write에서 덤프해 keystream을 얻고 위 내부 입력과 XOR하면 `hi_astra_i_believe_you_can_jump_4c6a05cc40f5d4cb`가 나온다.

## 풀이 및 재현

[solve.py](../solve.py)는 공식 바이너리의 SHA-256을 확인하고 복구한 입력을 원본 래퍼에 전달한 뒤, 원본이 출력한 flag만 stdout에 기록한다. Competition의 `.venv`를 활성화하고 challenge root에서 실행한다.

```bash
python -m pip install -r ../../requirements.txt
python -m pip check
python solve.py
```

## 결과

원본 `jump_v2`는 exit code `0`과 함께 `Congrats!`를 출력했고 다음 flag를 반환했다. `solve.py`의 stdout 및 `flag` 파일과 byte-for-byte 일치한다.

```text
pwnsec{hi_astra_i_believe_you_can_jump_4c6a05cc40f5d4cb}
```

## 정리 및 회고

알 수 없는 syscall의 정상 Linux 반환값 `-ENOSYS`와 seccomp의 `ERRNO(1)` 반환값 `-1` 차이가 검증 오라클을 만든다. 간접 점프와 무의미한 SIMD 명령이 많은 바이너리는 전체 정적 복원보다 실제 basic-block 경로, 메모리 write, seccomp BPF를 동적으로 추출하는 편이 효과적이다. MBA 함수는 실행 경로가 직선이면 명령 의미를 Z3 식으로 옮겨 검증할 수 있다.

## 참고 자료

외부 자료는 사용하지 않았다. ELF, seccomp BPF, AES-NI 동작은 로컬 GNU 도구의 출력과 실제 실행 결과로 확인했다.
