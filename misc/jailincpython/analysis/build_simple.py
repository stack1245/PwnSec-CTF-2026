from pathlib import Path
import re
root=Path(__file__).resolve().parents[1]
idx={0:"F",1:"T",2:"z",3:"z+T",4:"q",5:"q+T",6:"q+z",7:"q+z+T",8:"p",9:"p+T",10:"p+z",11:"p+z+T",12:"p+q",17:"n+T",22:"n+q+z",26:"n+p+z",29:"n+p+q+T",36:"n+n+q",48:"n+n+n",50:"n+n+n+z"}
template=r'''{_:{F:
{y for y in X[a]}if i>9 else
{f:=X[a][O],a:=P}if i>8 else
{f:=X[a],a:=I}if i>7 else
{a:=X[a],f:=G}if i>6 else
{f:=X[a],a:=R}if i>5 else
{a:=X[a][F],f:=G}if i>4 else
{A%{f:=d[s]}for d in{X[a]}for _,_,_,_,_,_,_,_,_,_,s,*_ in d}if i>3 else
{f:=X[a],a:=D}if i>2 else
{o:=X[a],f:=G,a:=o}if i>1 else
{A%{C:=U+x+h[4]+h[2]+s+s+U,D:=U+d+j+x+t+U,R:=U+h[6]+e+w+U,I:=U+b+w+j+h[4]+t+j+h[6]+s+U,O:=h[12]+h[8]+e+h[6],P:=y+h[4]+h[2]+g,f:=a,a:=C}for r in{A%a}for u,k,g,e,t,j,b,w,s,x,d,y in{r[17:22]+r[26:29]+r[48:50]+r[6]+r[36]}for U in{u+k}}if i else
{a:=X[a]},T:{i:=i+1}}
for _ in h[:11]for X.__class_getitem__ in{f}}'''
template=re.sub(r"\d+",lambda m:idx[int(m.group())],template)
template="".join(x.strip() for x in template.splitlines())
init="T:=True,F:=T-T,X:=hint_A,z:=T+T,q:=z*z,p:=q*z,n:=p*z,h:=hint_B,A:=h[F]+h[z],G:=lambda x:x.__getattribute__,f:=G,a:=X,i:=F"
template="{False:{"+init+"},T:"+template+"}"
print("length",len(template),"dots",template.count("."));print(template)
ns={};exec((root/"challenge"/"main.py").read_text().split("def main")[0],ns)
for k,v in idx.items():
 if not 1<=k<=11: continue
 loc={};gl={"__builtins__":{"hint_A":ns["hint_A"],"hint_B":ns["hint_B"]}}
 try:
  out=eval(template.replace("h[:p+z+T]",f"h[:{v}]"),gl,loc)
  print(k,"ok",{x:repr(gl.get(x))[:80] for x in "iaforukgetjbwsxdyUCDRIOP"})
 except Exception as e: print(k,type(e).__name__,e,{x:repr(gl.get(x))[:80] for x in "iaforukgetjbwsxdyUCDRIOP"})
