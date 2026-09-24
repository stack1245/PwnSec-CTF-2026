set debuginfod enabled off
break *0x4017ff
run
info registers rax rbx rbp r12 r13 r14 r15 rdi rsi rdx rsp
x/20gx $rsp
x/4gx $rbp
set $q=*(void**)($rbp+8)
x/8gx $q
quit
