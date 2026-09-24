# skill issue '@'aelmo

> 스포일러: 이 문서는 문제의 분석 과정과 최종 풀이를 포함합니다.

## 개요

| 항목 | 내용 |
|---|---|
| 상태 | solved |
| 대회·플랫폼 | PwnSec CTF 2026 |
| 분야 | crypto |
| 난이도 | Hard |
| Flag 형식 | `pwnsec{...}` |

서비스는 2048-bit 소수 `p`와 세 개의 작은 16×16 정수 행렬을 숨긴 뒤, 이들을 48×48 상삼각 블록 행렬 `x`로 쌓아 `f(x) mod p`만 공개한다. 결정적인 관찰은 `x`와 `f(x)`가 가환한다는 점이다. 가환식 두 개에서 숨은 모듈러 몫을 제거하면 LLL로 첫 블록을 복원할 수 있고, 이어서 `p`와 나머지 블록도 순서대로 구할 수 있다.

## 환경 및 초기 분석

공식 입력은 [`public.zip`](../challenge/public.zip)과 그 안의 [`chall.py`](../challenge/chall.py)이다. ZIP의 SHA-256은 `a1c1b741d0df527a6cfc4fd35af0f98267b5aaba58702382b8e431ebdd4abd44`, `chall.py`의 SHA-256은 `84758908e6a037b7a1af18fd6ee5820f4cbe5f7720b964188d558022da9637d1`이다. 원격 TLS endpoint는 [`instance.json`](../instance.json)에만 기록했다.

공용 환경은 [`requirements.txt`](../../../requirements.txt)로 복원하며, 풀이에 직접 필요한 비표준 패키지는 `python-flint==0.8.0`, `sympy==1.14.0`, `mpmath==1.3.0`이다. 서비스 출력은 `seed`, `flag_len=24`, 그리고 48×48 행렬 `cap`이다. `cap`은 대각 블록 `Y`, 첫 상부 블록 `Z`, 둘째 상부 블록 `W`가 반복되는 형태이고 하부 블록은 0이다.

## 핵심 분석

`A=x0`, `B=x1`, `C=x2`라 두면 다음과 같다.

```text
x   = [[A, B, C], [0, A, B], [0, 0, A]]
cap = [[Y, Z, W], [0, Y, Z], [0, 0, Y]] = f(x) mod p
```

먼저 `AY=YA mod p`이다. 각 `(i,j)`에 대해

```text
t[i,j] p = A[i]·Y^T[j] - Y[i]·A^T[j]
```

이고, 같은 행 또는 열을 공유하는 두 식을 교차 곱하면 `p`가 제거된다. 그러면 `t·A`를 계수로 갖는 짧은 정수 kernel 벡터가 생긴다. [`solve.py`](../solve.py)는 48차원 격자 `[I | u]`를 `python-flint`의 LLL로 줄여 `A`의 각 열을 복원한다. `mix()`의 공개 계수 `1+d_i-d_j`로 나눈 값이 모두 byte 범위인지 검사하므로 LLL 후보의 부호와 배율도 확정된다.

가환식은 스칼라 행렬을 구분하지 못하므로 이 단계에서 대각 원소에는 공통 shift가 남는다. 대각을 0으로 둔 행렬을 `A'`라 하면

```text
[A,Y]i,j = [A',Y]i,j + (A[i,i]-A[j,j])Y[i,j] = 0 mod p.
```

두 원소에 대해 가능한 대각 차이 `[-255,255]`를 대입하고 GCD를 취하면 2048-bit 소수 `p`가 나온다. 세 번째 원소로 공약수의 작은 배수를 제거한 뒤 primality를 확인한다. 이후 대각 차이를 모듈러 나눗셈으로 구하고, 가능한 공통 shift 12개 중 `f(A)=Y`를 만족하는 값으로 전체 `A`를 확정한다.

다음 두 블록은 가환식의 선형화로 구한다.

```text
YB - BY = AZ - ZA
YC - CY = AW - WA + BZ - ZB
```

각 Sylvester 식은 대각을 제외한 240개 미지수에 rank 240인 선형계를 준다. 대각 16개를 매개변수로 둔 affine 해를 구한 뒤, `mix()`로 나눈 모든 원소가 byte라는 조건을 24-sample LWE/CVP로 바꾼다. 40차원 embedding을 LLL로 줄이고 Babai nearest-plane을 적용해 대각 byte를 얻는다. 남은 공통 scalar shift는 다항식 f의 Fréchet derivative `f'(A)`와 공개 블록 `Z` 또는 `W`로 결정한다. 복원한 두 블록은 공개 블록 전체를 다시 생성하는지 검사한다.

마지막으로 seed가 정한 `C` 내부 offset 59에서 24바이트 `sealed`를 꺼낸다. 복원한 `p`를 원본과 같은 SHA-512 입력 형식으로 직렬화해 mask를 재생성하고 XOR하면 flag가 나온다.

## 풀이 및 재현

전체 원격 파싱, LLL, 모듈러스 복구, 두 Sylvester/CVP 단계, mask 복호화는 [`solve.py`](../solve.py) 하나에 통합되어 있다. 대회 `.venv`를 활성화하고 challenge root에서 실행한다.

```bash
python -m pip install -r ../../requirements.txt
python -m pip check
python solve.py
```

solver는 [`instance.json`](../instance.json)의 `main` TLS endpoint를 읽으며 성공 시 trailing newline 없이 flag byte만 출력한다.

## 결과

`python solve.py`는 exit code 0, 빈 stderr로 아래 24바이트를 출력했고, 같은 byte를 `flag` 파일과 대조했다.

```text
pwnsec{6a9c2ea004a8dee0}
```

## 정리 및 회고

숨은 모듈러스 아래의 큰 행렬 거듭제곱도 `M·f(M)=f(M)·M`이라는 선형 가환 관계를 먼저 쓰면 작은 비밀 행렬을 직접 노출할 수 있다. 블록 확장은 새 비선형 문제가 아니라 순차 Sylvester 식을 만들며, 각 단계의 16차원 kernel은 byte 범위를 작은-error LWE로 해석해 제거할 수 있다. 마지막 공통 scalar 모호성은 원래 다항식 또는 Fréchet derivative로 검증해야 한다.

## 참고 자료

- [HITCON CTF 2025 MRSA write-up](https://rechn0.github.io/2025/08/25/2025-hitconctf/): 숨은 모듈러스 행렬에서 가환식 두 개와 LLL로 작은 행렬을 행/열 단위 복구하는 기법.
- [fplll README](https://github.com/fplll/fplll): LLL 및 CVP/Babai 격자 입력과 알고리즘 동작 확인. 최종 구현은 같은 계열의 `python-flint` LLL과 자체 Babai 단계를 사용한다.
