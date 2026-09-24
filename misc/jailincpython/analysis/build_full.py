from pathlib import Path
import re
import subprocess

root = Path(__file__).resolve().parents[1]
py = root.parents[1] / ".venv" / "Scripts" / "python.exe"

idx = {0:"F",1:"T",2:"z",3:"z+T",4:"q",5:"q+T",6:"q+z",7:"q+z+T",8:"p",9:"p+T",10:"p+z",11:"p+z+T",12:"p+q",13:"p+q+T",17:"n+T",22:"n+q+z",26:"n+p+z",29:"n+p+q+T",36:"n+n+q",48:"n+n+n",50:"n+n+n+z"}

template = r'''{f:
{x for x in X[a]}if i>11 else
{F for v[8]in{X[a][F]}for l[8]in{l[3]}}if i==7 else
{F for v[1]in{X[a]}}if i<1 else
{F for l[i+1]in{X[a]}}if i%2!=b else
{F for r in{A%f}for u,k,g,e,t,j,B,w,s,x,d,y in{r[17:22]+r[26:29]+r[48:50]+r[6]+r[36]}for U in{u+k}
 for v[4]in{U+x+h[4]+h[2]+s+s+U}
 for v[6]in{U+d+j+x+t+U}for v[9]in{v[6]}
 for l[2]in{U+s+w+B+x+h[4]+h[2]+s+s+e+s+U}
 for l[0]in{U+B+w+j+h[4]+t+j+h[6]+s+U}
 for l[1]in{h[12]+h[8]+e+h[6]}
 for v[11]in{U+g+h[4]+h[12]+B+h[2]+h[4]+s+U}
 for v[12]in{y+h[4]+h[2]+g}
 for l[3]in{X[U+g+e+t+U]}}if i<4 else
{F for v[5]in{X[a]}for v[7]in{X[a]}for l[5]in{l[3]}}if i==4 else
{F for x in{l[2]}for l[7]in{X[a][x]}}if i<8 else
{F for m in{X[a]}for _,_,x,*_ in m for v[10]in{m[x]}for l[10]in{G}}if i<11 else
{F for m in{X[a]}for l[12]in{m[l[0]][l[1]]}}
for*l,_ in{h}for*v,in{h+h}for l[0]in{G}for l[1]in{G}for v[0]in{X}for v[3]in{X}for v[-1]in{F}
for f in l for i in v[-1:]for b in{i>7}for a in v[i:i+1]
for X.__class_getitem__ in{f}for v[-1]in{i+1}}'''

template = re.sub(r"\d+", lambda m: idx[int(m.group())], template)
template = "".join(line.strip() for line in template.splitlines())
initializers = "T:=True,F:=T-T,X:=hint_A,z:=T+T,q:=z*z,p:=q*z,n:=p*z,h:=hint_B,A:=h[F]+h[z],G:=lambda*x:x[-True].__getattribute__"
template = "{False:{" + initializers + "},T:" + template + "}"

print("length", len(template), "dots", template.count("."))
print(template)
result = subprocess.run([str(py), str(root / "challenge" / "main.py")], input=template + "\n", text=True, capture_output=True, timeout=5)
print(result.stdout)
print(result.stderr)
