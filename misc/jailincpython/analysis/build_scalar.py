from pathlib import Path
import re
import subprocess

root = Path(__file__).resolve().parents[1]
py = root.parents[1] / ".venv" / "Scripts" / "python.exe"

idx = {0:"F",1:"T",2:"z",3:"z+T",4:"q",5:"q+T",6:"q+z",7:"q+z+T",8:"p",9:"p+T",10:"p+z",11:"p+z+T",12:"p+q",13:"p+q+T",17:"n+T",22:"n+q+z",26:"n+p+z",29:"n+p+q+T",36:"n+n+q",48:"n+n+n",50:"n+n+n+z"}

template = r'''{i:
{y for y in X[a]}if i>11 else
{f:=X[a][I][O],a:=P}if i>10 else
{f:=X[a],a:=L}if i>9 else
{a:=X[a],f:=G}if i>8 else
{f:=X[a],a:=R}if i>7 else
{a:=X[a][F],f:=B}if i>6 else
{f:=X[a][S],a:=o}if i>5 else
{f:=X[a],a:=D}if i>4 else
{o:=X[a],f:=B,a:=o}if i>3 else
{f:=X[a],a:=C}if i>2 else
{B:=X[a],f:=B,a:=X}if i>1 else
{A%{f:=E,a:=K,C:=U+x+h[4]+h[2]+s+s+U,D:=U+d+j+x+t+U,S:=U+s+w+b+x+h[4]+h[2]+s+s+e+s+U,R:=r[9]+e+g+j+s+t+e+r[9],L:=U+g+h[4]+h[12]+b+h[2]+h[4]+s+U,I:=U+b+w+j+h[4]+t+j+h[6]+s+U,O:=h[12]+h[8]+e+h[6],P:=y+h[4]+h[2]+g}
 for E in{X[a]}for r in{A%E}for u,k,g,e,t,j,b,w,s,x,d,y in{r[17:22]+r[26:29]+r[48:50]+r[6]+r[36]}for U in{u+k}}if i else
{a:=X[a]}
for*c,in{h[:1]}for c[0]in{F}for _ in h[:13]for i in c
for X.__class_getitem__ in{f}for c[0]in{i+1}}'''

template = re.sub(r"\d+", lambda m: idx[int(m.group())], template)
template = "".join(line.strip() for line in template.splitlines())
initializers = "T:=True,F:=T-T,X:=hint_A,z:=T+T,q:=z*z,p:=q*z,n:=p*z,h:=hint_B,A:=h[F]+h[z],G:=lambda*x:x[-True].__getattribute__,f:=G,a:=X"
template = "{False:{" + initializers + "},T:" + template + "}"

print("length", len(template), "dots", template.count("."))
print(template)
if len(template) <= 800:
    result = subprocess.run([str(py), str(root / "challenge" / "main.py")], input=template + "\n", text=True, capture_output=True, timeout=5)
    print(result.stdout)
    print(result.stderr)
