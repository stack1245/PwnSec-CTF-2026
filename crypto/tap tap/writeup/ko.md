# tap tap

> 스포일러: 이 문서는 문제의 분석 과정과 최종 풀이를 포함합니다.

## 개요

| 항목 | 내용 |
|---|---|
| 상태 | solved |
| 대회·플랫폼 | PwnSec CTF 2026 |
| 분야 | crypto |
| 난이도 | 미제공 |
| Flag 형식 | `pwnsec{...}` |

이 문제는 128비트 소수체 위 25차 Fibonacci 선형 점화식의 연속 상태 180개에서 상위 80비트만 공개한다. 결정적인 관찰은 모듈러스가 `2^128`에 매우 가깝기 때문에 truncated output에서도 짧은 annihilating polynomial이 격자 벡터로 남는다는 점이다. 이를 이용해 모듈러스와 탭을 복구한 뒤, 작은 하위 48비트를 BDD/CVP로 구하면 SHAKE-256 키를 재생성할 수 있다.

## 환경 및 초기 분석

공식 입력은 암호 `infected`가 설정된 [public.zip](../challenge/public.zip)과 내부의 [chall.py](../challenge/chall.py)이다. SHA-256은 각각 `e1f54c52394d42987246afa0dacdfd771e09a8552e6480631244437b819f639c`, `21ad8088a41b9b4d03a0ff7cbeac79ec98eebbef12de0ab2b9f5e24ce31dd247`이다. 공용 환경은 [requirements.txt](../../../requirements.txt)로 복원하며, solver는 고정 버전 `python-flint==0.8.0`과 `mpmath==1.3.0`을 사용한다.

`chall.py`는 `p = 2^128 - d` 꼴의 소수를 만들며 `2^48 <= d <= 2^50`이다. 임의 탭 `C[0..24]`와 초기 상태 `A[0..24]`를 뽑은 뒤

```text
A[i+25] = sum(C[j] * A[i+j] for j=0..24) mod p
```

를 180회 수행한다. 공개 값은 `Y_i = A[25+i] >> 48`이고, 키는 205개 상태의 10진수 문자열 전체를 SHA-256 및 SHAKE-256에 넣어 만든다. 원격 endpoint는 없으므로 `instance.json`은 필요하지 않다.

## 핵심 분석

각 상태를 `A_i = 2^48 Y_i + Z_i`, `0 <= Z_i < 2^48`로 쓴다. 길이 90의 짧은 annihilating vector `eta`가 있으면 90개 sliding window에 대한 `sum(eta_i Y_{i+j}) mod 2^80`도 작다. `2^128-p`가 숨긴 범위보다 최대 4배 크므로 residue 좌표와 계수 좌표의 크기를 맞추기 위해 계수 좌표를 64배 스케일했다. 180차원 기저를 BKZ-35로 축약해 독립적인 89차 annihilating polynomial들을 얻었다.

두 다항식의 resultant에는 공통 최소 다항식 차수 25만큼 `p^25`가 들어간다. 여러 resultant의 GCD에서 다음 값을 복구했다.

```text
p = 340282366920938463463374127620052448857
2^128 - p = 479811715762599
```

다항식들을 `F_p[x]`로 내린 뒤 GCD를 구하면 25차 characteristic polynomial이 나오고, 0차부터 24차 계수를 부호 반전하면 탭 `C`가 된다. 상세 식과 검증 값은 [derivation.md](../analysis/derivation.md)에 보존했다.

탭이 알려지면 이후 상태는 첫 25개 공개 상태의 선형 결합 `q_j`로 표현된다. `Z_i = W_i + 2^47`로 중심을 옮기면 `q_j W - t_j = W_j (mod p)`이고 모든 미지수와 잔차는 절댓값 `2^47` 미만이다. 미래 식 50개로 다음 75차원 BDD 격자를 만들었다.

```text
[ I_25   Q ]
[  0    pI_50 ]
```

LLL과 Babai nearest-plane으로 첫 25개 하위 비트를 복구했다. 복구 상태로 생성한 180개 값의 상위 80비트가 공개 `Y` 전체와 정확히 일치했다. 마지막으로 `C[0]^-1 mod p`를 이용해 25단계 역진행하여 원래 `A[0..204]`를 얻었다.

## 풀이 및 재현

[solve.py](../solve.py)는 분석에서 확정한 `p`와 탭을 포함하고, 공식 `chall.py`에서 `Y`와 ciphertext를 읽어 75차원 상태 격자를 구성한다. LLL, Babai CVP, 전체 180개 출력 검증, 25단계 역진행, SHA-256/SHAKE-256 복호화를 한 실행에서 수행한다. 대회 `.venv`를 활성화하고 challenge root에서 실행한다.

```bash
python -m pip install -r ../../requirements.txt
python -m pip check
python solve.py
```

## 결과

`python solve.py`는 exit code 0, 빈 stderr로 종료했으며 stdout은 아래 flag byte만 출력했다. 복구 점화식은 공개된 180개 truncated output 전부와 일치했고, 이 stdout은 `flag` 파일과 byte-for-byte 동일하다.

```text
pwnsec{wR17in6_17_t0oK_m3_thRe3__d4y5_d1d_4I_50lv3_i7_1n_thRe3_53c0nDs??}
```

## 정리 및 회고

모듈러스가 알려지지 않은 truncated Fibonacci generator도 모듈러스가 2의 거듭제곱에 가까우면 annihilating relation이 짧은 격자 벡터로 남는다. 이 문제에서는 `2^128-p`의 실제 상한 때문에 좌표 스케일링이 필요했고, 모듈러스·탭 복구보다 이후 상태 BDD가 훨씬 강한 거리 간격을 가졌다. 전체 공개 출력을 재생성하는 검증이 격자 오탐과 탭 방향 오류를 동시에 제거했다.

## 참고 자료

- [Lattice Attacks on Truncated Fibonacci LFSRs](https://hackmd.io/@at20n0118/BkxzTRLgGg): unknown-modulus annihilating lattice, resultant 기반 모듈러스 복구, state-recovery 구성의 기준으로 사용했다.
- [Reconstructing Truncated Integer Variables Satisfying Linear Congruences](https://epubs.siam.org/doi/10.1137/0217016): truncated modular state를 격자로 복구하는 이론적 배경을 확인했다.
- `python-flint 0.8.0`: 정수 LLL 및 유한체 다항식 GCD 계산에 사용했다.
