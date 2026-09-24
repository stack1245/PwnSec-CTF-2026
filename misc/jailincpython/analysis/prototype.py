class hint_A:
    pass


hint_B = "%jailincpython"

payload = r'''{
f:
    ({False:
        ({False for v[1] in {hint_A[a]}} if i == 0
         else {False:{False for v[5] in {hint_A["__class__"]}},True:{False for v[7] in {hint_A[a]}},None:{False for l[5] in {l[3]}}} if i == 4
         else {False for l[7] in {hint_A[a]["__subclasses__"]}} if i == 6
         else {False for l[i+1] in {hint_A[a]}}),
      True:{False for c[0] in {i+1}}}
     if i < 7 else hint_A[a])
for g in {lambda *x: x[-1].__getattribute__}
for *l, in {hint_B[:8]}
for *v, in {hint_B[:8]}
for *c, in {hint_B[:1]}
for l[0] in {g}
for l[1] in {g}
for v[0] in {hint_A}
for v[2] in {"__get__"}
for v[3] in {hint_A}
for v[4] in {"__base__"}
for v[6] in {"__dict__"}
for c[0] in {0}
for f in l
for i in c
for a in v[i:i+1]
for hint_A.__class_getitem__ in {f}
}'''

print(eval(payload))
