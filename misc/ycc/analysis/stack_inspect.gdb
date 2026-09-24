set pagination off
break *0x4058d1
run
info registers rdx rcx r8 r9 rsp
x/30gx $rsp
x/gx 0x4090f8
