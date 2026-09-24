from pathlib import Path
import re
root=Path(__file__).resolve().parents[1]
idx={0:"F",1:"T",2:"z",3:"z+T",4:"q",5:"q+T",6:"q+z",7:"q+z+T",8:"p",9:"p+T",10:"p+z",11:"p+z+T",12:"p+q",13:"p+q+T",17:"n+T",19:"n+z+T",20:"n+z+z",21:"n+q+T",22:"n+q+z",26:"n+p+z",27:"n+p+z+T",28:"n+p+q",29:"n+p+q+T",36:"n+n+q",48:"n+n+n",49:"n+n+n+T",50:"n+n+n+z"}
template=r'''{_:{F:
{y for y in X[a]}if i>11 else
{f:=X[a][O],a:=P}if i>10 else
{f:=X[a],a:=I}if i>9 else
{a:=X[a],f:=B}if i>8 else
{f:=X[a],a:=R}if i>7 else
{a:=X[a][F],f:=B}if i>6 else
{A%{f:=X[a][s]}for s in X[a]if s[11]==L}if i>5 else
{f:=X[a],a:=D}if i>4 else
{o:=X[a],f:=B,a:=o}if i>3 else
{f:=X[a],a:=C}if i>2 else
{B:=X[a],f:=B,a:=X}if i>1 else
{A%{U:=r[17:19],K:=r[17:22]+U,C:=U+r[49]+h[4]+h[2]+r[48]+r[48]+U,D:=U+r[6]+r[26]+r[49]+r[21]+U,R:=U+h[6]+r[20]+r[8]+U,I:=U+r[27]+r[28]+r[26]+h[4]+r[21]+r[26]+h[6]+r[48]+U,O:=h[12]+h[8]+r[20]+h[6],P:=r[36]+h[4]+h[2]+r[19],f:=E,a:=K}for E in{X[a]}for r in{A%E}}if i else
{a:=X[a]},T:{i:=i+1}}
for _ in h[:13]for X.__class_getitem__ in{f}}'''
template=re.sub(r"\d+",lambda m:idx[int(m.group())],template)
template="".join(x.strip() for x in template.splitlines())
init="T:=True,F:=T-T,X:=hint_A,z:=T+T,q:=z*z,p:=q*z,n:=p*z,h:=hint_B,A:=h[F]+h[z],G:=lambda x:x.__getattribute__,f:=G,a:=X,i:=F"
template="{False:{"+init+"},T:"+template+"}"
print("length",len(template),"dots",template.count("."));print(template)
ns={};exec((root/"challenge"/"main.py").read_text().split("def main")[0],ns)
for k,v in idx.items():
 if not 1<=k<=13: continue
 gl={"__builtins__":{"hint_A":ns["hint_A"],"hint_B":ns["hint_B"]}}
 try:
  eval(template.replace("h[:p+q+T]",f"h[:{v}]"),gl,{})
  print(k,"ok",{x:repr(gl.get(x))[:100] for x in "iafBoKCDRIOP"})
 except Exception as e: print(k,type(e).__name__,e,{x:repr(gl.get(x))[:100] for x in "iafBoKCDRIOP"})
