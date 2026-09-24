# Two Worlds, One Heart

> 스포일러: 이 문서는 문제의 분석 과정과 최종 풀이를 포함합니다.

## 개요

| 항목 | 내용 |
|---|---|
| 상태 | solved |
| 대회·플랫폼 | PwnSec CTF 2026 |
| 분야 | reverse |
| 난이도 | Easy (194 points) |
| Flag 형식 | `pwnsec{...}` |

`portal33.exe`는 같은 검증 함수 바이트를 x86과 x86-64로 각각 실행한다. 핵심은 40바이트 입력의 앞 20바이트가 32비트 해석에서, 뒤 20바이트가 64비트 해석에서 검증된다는 점이다. 각 비교식의 rotate와 XOR을 역산하면 전체 입력을 복구할 수 있다.

## 환경 및 초기 분석

공식 입력은 암호 `infected`가 설정된 [public.zip](../challenge/public.zip)이며, 내부 파일은 [portal33.exe](../challenge/portal33.exe) 하나다. ZIP과 EXE의 SHA-256은 각각 `16f7079aec0118b57faca43cc0b2fa73963887b9d3bc5837f944e9eddf8b11d9`, `d35911333fae7cfc7a305c93e2f14cad678487ef724d4ea610c3e047a42194f0`이다.

`file` 5.45와 GNU `objdump` 2.42로 확인한 EXE는 Intel i386용 PE32 console 실행 파일이다. VA `0x408e1e`의 길이 비교는 입력을 정확히 `0x28`(40)바이트로 제한한다. Solver는 Python 3.12.10 표준 라이브러리만 사용하며, 대회 공용 환경은 [requirements.txt](../../../requirements.txt)로 복원한다.

## 핵심 분석

VA `0x401600`은 실행 모드에 따라 다르게 디코딩된다. 32비트 경로는 4바이트 little-endian word 다섯 개에 대해 다음 식을 검사한다.

```text
T[i] = ROL32(word[i] XOR previous, 11)
previous = 0x1337c0de (i = 0), otherwise T[i-1]
T = [0xcdbd7302, 0x30833d2e, 0xb310ea05, 0xdef1b433, 0x1c3b640e]
```

VA `0x4016b3`의 wrapper는 selector `0x33`으로 `retf`하여 같은 VA를 64비트 코드로 호출하고, selector `0x23`으로 32비트 모드에 복귀한다. 64비트에서는 시작 바이트 `31 c0 48 85 c0`가 `xor eax,eax; test rax,rax`로 해석되어 32비트 검사 블록을 건너뛴다. 이어지는 검사는 다음과 같다.

```text
ROL64(qword[0] XOR 0x5a33c0d313379090, 19) == 0x87326027c52b7005
ROL64(qword[1] XOR 0x87326027c52b7005, 29) == 0x7e6e88add6ebc7e2
ROL32(word[9] XOR 0xd6ebc7e2, 13)          == 0x5e929579
```

따라서 각 `ROL`을 같은 폭의 `ROR`로 되돌린 후 이전 target 또는 key와 XOR하면 원본 word를 직접 얻는다. 주소와 식의 정적 근거는 [verifier.md](../analysis/verifier.md)에 정리했다.

## 풀이 및 재현

[solve.py](../solve.py)는 원본 PE의 opcode skeleton을 먼저 검사하고, instruction immediate를 직접 읽어 역연산한다. 복구한 40바이트에 대해 32비트와 64비트 검증식을 모두 다시 계산한 경우에만 flag를 stdout에 쓴다. 대회 `.venv`를 활성화하고 challenge root에서 실행한다.

```bash
python -m pip install -r ../../requirements.txt
python -m pip check
python solve.py
```

## 결과

`python solve.py`는 exit code 0, 빈 stderr, trailing newline 없는 40바이트 stdout을 반환했다. 같은 입력을 원본 `portal33.exe`에 전달했을 때도 exit code 0과 `Access Granted! Flag verified.`가 확인되었다.

```text
pwnsec{h3_5p34k5_32_5h3_5p34k5_64_l0v3!}
```

## 정리 및 회고

Heaven's Gate 패턴에서는 하나의 바이트열을 현재 디스어셈블 모드로만 해석하면 실제 분기 절반을 놓칠 수 있다. `retf`의 selector와 호출 대상 VA를 확인하고 동일 구간을 두 아키텍처 모드로 각각 디스어셈블하는 것이 결정적이었다. rotate/XOR chain은 비교 target 자체가 다음 블록의 상태이므로 앞에서부터 결정적으로 역산할 수 있다.

## 참고 자료

외부 자료는 사용하지 않았다. 분석에는 로컬 `file`, GNU `objdump`, Python 표준 라이브러리와 제공 바이너리만 사용했다.
