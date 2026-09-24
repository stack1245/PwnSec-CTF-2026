set pagination off
set debuginfod enabled off
set breakpoint pending on
break __libc_start_main
run
set $main = $rdi
set $base = $main - 0x2040
break *($base + 0x237f)
continue
printf "base=%p\n", $base
x/gx $base + 0x5050
x/32bx $rsp + 0xb0
printf "encrypted_length=%u encrypted=%p\n", $r13d, $r12
x/64bx $r12
quit
