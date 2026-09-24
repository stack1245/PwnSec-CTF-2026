# tap tap derivation

## Inputs

- `challenge/public.zip` SHA-256: `e1f54c52394d42987246afa0dacdfd771e09a8552e6480631244437b819f639c`
- `challenge/chall.py` SHA-256: `21ad8088a41b9b4d03a0ff7cbeac79ec98eebbef12de0ab2b9f5e24ce31dd247`
- ZIP password published for the event archives: `infected`
- The 180 leaked values are `Y_i = A_{25+i} >> 48`.

## Unknown-modulus recurrence recovery

Write each full value as `A_i = 2^48 Y_i + Z_i`, where `0 <= Z_i < 2^48`.
For a short annihilating vector `eta` and an 90-value sliding window,

```text
sum eta_i Y_{i+j} (mod 2^80)
```

is small because `p` is close to `2^128`.  The lattice used 90 residue
coordinates and 90 coefficient coordinates.  Coefficient coordinates were
scaled by 64 to balance the extra term caused by `2^128 - p` being as large
as `2^50`.

BKZ-35 on the resulting 180-dimensional lattice produced independent degree-89
annihilating polynomials.  Pairwise resultants share `p^25`; their GCD gives

```text
p = 340282366920938463463374127620052448857
2^128 - p = 479811715762599
```

Reducing the annihilating polynomials modulo `p` and taking their polynomial
GCD gives the monic degree-25 characteristic polynomial.  The feedback taps
embedded in `solve.py` are the negated coefficients of degrees 0 through 24.

## State recovery and verification

Every later observed state is a linear combination `q_j` of the first 25
observed states.  With `Z_i = W_i + 2^47`, the equations become

```text
q_j W - t_j = W_j (mod p),  |W_i| < 2^47.
```

Fifty equations produce the 75-dimensional BDD lattice

```text
[ I_25   Q ]
[  0    pI_50 ]
```

and target `(0, t)`.  `python-flint` LLL followed by Babai nearest-plane
recovers the 25 centered low parts.  Regenerating the recurrence matches all
180 leaked high parts exactly.  Since the leak begins at `A[25]`, inversion
through the nonzero first tap recovers the preceding 25 values.  Recomputing
`SHA256(''.join(map(str, A)))`, expanding it with SHAKE-256, and XORing the
ciphertext yields the verified flag.
