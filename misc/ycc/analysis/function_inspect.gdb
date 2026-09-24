set debuginfod enabled off
break *0x4058dd
run
info registers rsp r13
x/32gx $rsp
quit
