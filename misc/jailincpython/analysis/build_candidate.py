from pathlib import Path
import re
root=Path(__file__).resolve().parents[1]
idx={0:"F",1:"T",2:"z",3:"z+T",4:"q",5:"q+T",6:"m",7:"m+T",8:"p",9:"p+T",10:"p+z",11:"p+z+T",12:"p+q",13:"p+q+T",14:"p+m",15:"p+m+T",16:"n",17:"n+T",22:"n+m",26:"n+p+z",29:"n+p+q+T",36:"n+n+q",48:"n+n+n",50:"n+n+n+z",68:"n+n+n+n+q"}
template=r'''{_:{F:
{a:=X[a][F]if i==7 else X[a],f:=B}if i in{4,7,9,12}else X[a]if i>14 else
{f:=X[a][J],a:=Q}if i==11 else
{f:=X[a][S],a:=X[C]}if i==6 else
{f:=X[a],a:={3:C,5:D,8:R,10:I,13:Y,14:W}[i]}if i>2 else
{B:=X[a],f:=B,a:=X}if i>1 else
{F:{U:=u+k,K:=U+g+e+t+U,C:=U+x+h[4]+h[2]+L+L+U,S:=U+L+w+b+C[2:-2]+e+L+U,D:=U+r[6]+j+x+t+U,R:=v+e+g+j+L+t+e+v,I:=U+b+w+j+h[4]+t+j+h[6]+L+U,J:=U+j+r[1]+h[8]+h[12]+v+t+U,Q:=h[12]+L,Y:=L+h[9]+L+t+e+r[1],W:=L+h[11],f:=E,a:=K}for E in{X[a]}for r in{h[:3:2]%E}for u,k,g,e,t,j,b,w,L,x,v in{r[17:22]+r[26:29]+r[48:50]+r[9]}}if i else
{a:=X[a]},T:{i:=i+1}}
for _ in h+h[:2]for X.__class_getitem__ in{f}}'''
template=re.sub(r"\d+",lambda m:idx[int(m.group())],template)
template="".join(x.strip() for x in template.splitlines())
init="T:=True,F:=T-T,X:=hint_A,z:=T+T,q:=z*z,m:=q+z,p:=q*z,n:=p*z,h:=hint_B,f:=lambda x:x.__getattribute__,a:=X,i:=F"
template="{False:{"+init+"},T:"+template+"}"
print("length",len(template),"dots",template.count("."));print(template)
compile(template,"<payload>","eval")
