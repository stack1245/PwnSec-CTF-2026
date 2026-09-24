# Gap Gap

> 스포일러: 이 문서는 문제의 분석 과정과 최종 풀이를 포함합니다.

## 개요

| 항목 | 내용 |
|---|---|
| 상태 | solved |
| 대회·플랫폼 | PwnSec CTF 2026 |
| 분야 | crypto |
| 난이도 | Medium |
| Flag 형식 | `pwnsec{...}` |

이 문제는 `p-1`과 `q-1`이 큰 소수 `g`를 공유하는 Common Prime RSA와, 124자리 개인 지수 `d`의 가운데 30자리 누출 공백을 결합한다. 결정적인 관찰은 누락 블록에 대한 식이 `g`로 나누어지고 `N+1-(p+q)=phi(N)`가 `g^2`로 나누어진다는 점이다. 두 식의 작은 근을 동시 modular lattice로 복구한 뒤 continued fraction으로 `2g`와 RSA 인수를 얻는다.

## 환경 및 초기 분석

공식 첨부물은 [`chall.py`](../challenge/chall.py), [`output.txt`](../challenge/output.txt), 암호화된 원본 [`public.zip`](../challenge/public.zip)이다. 실제 서비스가 반환한 인스턴스는 원문 그대로 [`remote-output.txt`](../challenge/remote-output.txt)에 보존했다. 대회 공용 환경은 [`../../../requirements.txt`](../../../requirements.txt)로 복원하며, 풀이에 `python-flint==0.8.0`의 LLL과 `sympy==1.14.0`의 다항식 gcd를 사용한다.

`chall.py`는 다음 값을 생성한다.

```text
p = 2*g*a + 1
q = 2*g*b + 1
lambda = lcm(p-1, q-1) = 2*g*a*b
e*d - 1 = k*lambda
```

`d_leak`는 47자리 prefix와 47자리 suffix만 공개하며 가운데 30자리를 `*`로 가린다. 원격 TLS endpoint는 [`../instance.json`](../instance.json)에 저장했다. 첨부된 정적 `output.txt`는 샘플 문자열을 암호화한 데이터였으므로 제출 플래그는 라이브 서비스 출력으로 구했다. 기본 재현은 캡처한 `remote-output.txt`를 사용하고, `GAP_GAP_REMOTE=1`이면 새 인스턴스를 읽으며, `GAP_GAP_SAMPLE=1`이면 첨부 샘플을 별도로 검사한다.

## 핵심 분석

`G=2g`, `A=ed-1`로 두면 `A=kGab`이다. 이를 각 RSA 소수로 줄이면 다음과 같다.

```text
A + b*k = b*k*p ≡ 0 (mod p)
A + a*k = a*k*q ≡ 0 (mod q)
```

개인 지수를 `d=D0+10^47*x`, `0<=x<10^30`으로 쓴다. `N-1`의 인수 `g`를 직접 알 수는 없지만 다음 두 선형식에는 동일한 작은 근이 존재한다.

```text
f1(x) = x + a1 ≡ 0 (mod g)
f2(y) = y + N + 1 ≡ 0 (mod g^2),  y = -(p+q)
```

두 번째 식은 `N+1-p-q=(p-1)(q-1)=4g^2ab`에서 나온다. `f1`과 `f2`에 각각 가중치 1과 2를 부여해 `f1^i f2^j (N-1)^r`가 `g^t`로 나누어지도록 하고, `t=3`의 27차원 정수 lattice를 만든다. LLL 결과 다항식들의 pairwise gcd는 다음 선형 인수를 준다.

```text
x - 629965031111793143531495543250
```

이를 누출 형식에 대입한 `d`는 `2^(ed-1) mod N = 1`을 만족한다. 두 번째 공백은 `h=p*b+a=lambda+a+b`라는 생성 조건이다.

```text
N - 1 = G*h
G*(e*d-1) - k*(N-1) = -G*k*(a+b)
```

오른쪽이 주항보다 충분히 작고 `gcd(k,G)=1`이므로 `k/G`가 `(ed-1)/(N-1)`의 continued-fraction convergent로 나타난다. 601-bit 분모 `G`를 찾은 뒤 `lambda=(ed-1)/k`, `a+b=h-lambda`, `ab=lambda/G`를 계산한다. 판별식 `(a+b)^2-4ab`가 완전제곱이므로 `a,b`, 이어서 `p=Ga+1`, `q=Gb+1`을 복구하고 `pq=N`을 확인할 수 있다. 전체 유도는 [`../analysis/derivation.md`](../analysis/derivation.md)에 보존했다.

## 풀이 및 재현

최종 구현은 [`../solve.py`](../solve.py) 하나에 입력 parsing, simultaneous modular lattice, 누락 자리 복구, continued-fraction 인수분해, RSA 복호화를 통합한다. 대회 `.venv`를 활성화하고 challenge root에서 실행한다.

```bash
python -m pip install -r ../../requirements.txt
python -m pip check
python solve.py
```

원격에서 새 인스턴스를 직접 풀려면 동일한 위치에서 `GAP_GAP_REMOTE=1`을 설정한 뒤 `python solve.py`를 실행한다. 서비스의 키 생성에는 약 2분이 걸릴 수 있다.

## 결과

`python solve.py`는 exit code 0, 빈 stderr, trailing newline 없는 24-byte stdout을 생성했고, 그 byte가 [`../flag`](../flag)와 일치했다. 복구한 인수는 `p*q=N`을 만족하며, 복호문을 다시 공개 지수로 거듭제곱한 결과도 원래 `c`와 일치했다.

```text
pwnsec{a037f98cd3e49a5f}
```

## 정리 및 회고

Common Prime RSA에서는 일반 RSA의 `ed-k*phi(N)=1`만 보는 대신 공유 인수의 차수를 추적해야 한다. `ed-1`에서 얻은 modulo `g` 식과 `phi(N)`에서 얻은 modulo `g^2` 식을 함께 쓰면 MSB와 LSB 사이의 짧은 공백을 낮은 차원의 lattice로 복구할 수 있다. 또한 `N-1=2g*h`와 작은 오차 관계는 완전한 `d`가 나온 뒤 continued fraction으로 공유 인수를 분리한다.

## 참고 자료

- [M. Zheng and A. Nitaj, Partial Key Exposure Attack on Common Prime RSA](https://eprint.iacr.org/2024/061.pdf): simultaneous modular polynomial과 MSB/LSB 노출 공격의 근거.
- [MengceZheng/PKEA_CPRSA](https://github.com/MengceZheng/PKEA_CPRSA): 가중 shift 구성과 lattice parameter 선택을 대조하는 데 사용한 저자 구현.
- 공식 [`chall.py`](../challenge/chall.py): 실제 키 생성 관계와 bit/decimal 경계의 최종 기준.
