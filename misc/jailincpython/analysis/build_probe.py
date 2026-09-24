from pathlib import Path
import subprocess
import re


root = Path(__file__).resolve().parents[1]
py = root.parents[1] / ".venv" / "Scripts" / "python.exe"

idx = {
    0: "False",
    1: "True",
    2: "z",
    3: "z+True",
    4: "q",
    5: "q+True",
    6: "q+z",
    7: "q+z+True",
    8: "p",
    10: "p+z",
    17: "n+True",
    19: "n+z+True",
    20: "n+q",
    21: "n+q+True",
    22: "n+q+z",
    26: "n+p+z",
    27: "n+p+z+True",
    28: "n+p+q",
    29: "n+p+q+True",
    48: "n+n+n",
    49: "n+n+n+True",
    50: "n+n+n+z",
}

template = r'''{f:
hint_A[a]if i>6 else
{False for v[1]in{hint_A[a]}}if i<1 else
{False for l[i+1]in{hint_A[a]}}if i%2 else
{False for r in{A%f}for u,k,g,e,t,j,b,w,s,x,d in{r[17:22]+r[26:29]+r[48:50]+r[6]}for v[4]in{u+k+x+h[4]+h[2]+s+s+u+k}for v[6]in{u+k+d+j+x+t+u+k}for l[1]in{u+k+s+w+b+x+h[4]+h[2]+s+s+e+s+u+k}for l[3]in{hint_A[u+k+g+e+t+u+k]}}if i<4 else
{False for v[5]in{hint_A[a]}for v[7]in{hint_A[a]}for l[5]in{l[3]}}if i==4 else
{False for x in{l[1]}for l[7]in{hint_A[a][x]}}
for z in{True+True}for q in{z*z}for p in{q*z}for n in{p*z}for h in{hint_B}for A in{h[0]+h[2]}
for G in{lambda*x:x[-1].__getattribute__}
for*l,in{h[:8]}for*v,in{h[:8]}for*c,in{h[:1]}
for l[0]in{G}for l[1]in{G}for v[0]in{hint_A}for v[3]in{hint_A}for c[0]in{False}
for f in l for i in c for a in v[i:i+1]
for hint_A.__class_getitem__ in{f}for c[0]in{i+1}}'''

template = re.sub(r"\d+", lambda match: idx[int(match.group())], template)
template = template.replace("hint_A", "X").replace("True", "T").replace("False", "F")
template = template.replace("for z in", "for T in{True}for F in{T-T}for X in{hint_A}for z in", 1)
template = "".join(line.strip() for line in template.splitlines())
template = template.replace("u+k", "U").replace("for v[q]in", "for U in{u+k}for v[q]in", 1)
template = template.replace("for*c,in{h[:T]}", "")
template = template.replace("for*v,in{h[:p]}", "for*v,in{h[:p+T]}", 1)
template = template.replace("for c[F]in{F}", "for v[p]in{F}", 1)
template = template.replace("for i in c", "for i in v[p:p+T]", 1)
template = template.replace("for c[F]in{i+T}", "for v[p]in{i+T}", 1)
template = template.replace("for*v,in{h[:p+T]}", "for*v,in{h}", 1)
template = template.replace("v[p]", "v[-T]").replace("v[p:p+T]", "v[-T:]")
template = template.replace("] for a", "]for a")
bindings = "for T in{True}for F in{T-T}for X in{hint_A}for z in{T+T}for q in{z*z}for p in{q*z}for n in{p*z}for h in{hint_B}for A in{h[F]+h[z]}for G in{lambda*x:x[-T].__getattribute__}"
initializers = "T:=True,F:=T-T,X:=hint_A,z:=T+T,q:=z*z,p:=q*z,n:=p*z,h:=hint_B,A:=h[F]+h[z],G:=lambda*x:x[-True].__getattribute__"
template = template.replace(bindings, "")
template = "{False:{" + initializers + "},T:" + template + "}"

print("length", len(template), "dots", template.count("."))
pat = re.compile(r'^(?:[^\[\]"\'0-9()]+|\[[^\[\]"\'0-9()]*\])*$')
print("filter", bool(pat.fullmatch(template)))
print(template)
result = subprocess.run(
    [str(py), str(root / "challenge" / "main.py")],
    input=template + "\n",
    text=True,
    capture_output=True,
)
print(result.stdout)
print(result.stderr)
