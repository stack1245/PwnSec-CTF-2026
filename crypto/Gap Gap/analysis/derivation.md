# Gap Gap derivation

Let `G = 2g`. The generated primes and Carmichael exponent are

`p = Ga + 1`, `q = Gb + 1`, and `lambda = Gab`.

For `A = ed - 1 = k lambda`, reduction modulo each RSA prime gives

- `A + bk = kGa b + bk = bk p`,
- `A + ak = kGa b + ak = ak q`.

The missing decimal block is represented as `d = D0 + 10^47 x`, with
`0 <= x < 10^30`. A simultaneous modular lattice uses

- `f1(x) = x + a1`, which is zero modulo `g`, and
- `f2(y) = y + N + 1`, which is zero modulo `g^2` at `y = -(p+q)` because
  `N + 1 - p - q = phi(N)`.

LLL reduction at `t=3` produces polynomials whose pairwise gcd is
`x - 629965031111793143531495543250`. Substitution reconstructs a valid `d`
and verifies `2^(ed-1) mod N = 1`.

For the second gap, define `h = p*b + a = lambda + a + b`. Then

`N - 1 = G h`

and

`G(ed-1) - k(N-1) = -Gk(a+b)`.

The right side is small enough that `k/G` occurs as a continued-fraction
convergent of `(ed-1)/(N-1)`. The source condition `gcd(k, 2g) = 1` keeps the
fraction reduced. Its 601-bit denominator recovers `G`, after which
`lambda`, `a+b`, and `ab` determine `a,b` from a quadratic equation and yield
the verified factorization `p*q=N`.

For the captured live instance, RSA decryption produces
`pwnsec{a037f98cd3e49a5f}`. Verification checks both `p*q=N` and
`pow(m,e,N)=c`. The attachment's static `output.txt` decrypts to a different
sample string and is not the submission flag.
