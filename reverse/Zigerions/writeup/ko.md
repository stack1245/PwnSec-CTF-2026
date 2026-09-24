# Zigerions

> 스포일러: 이 문서는 문제의 분석 과정과 최종 풀이를 포함합니다.

## 개요

| 항목 | 내용 |
|---|---|
| 상태 | solved |
| 대회·플랫폼 | PwnSec CTF 2026 |
| 분야 | reverse |
| 난이도 | Hard |
| Flag 형식 | `psctf{...}` |

암호화된 ZIP 안의 Linux ELF는 Windows PyInstaller 실행 파일을 품고 있고, 그 파일은 다시 VMProtect PE와 Game Boy ROM, 위장 ELF를 차례로 만든다. 결정적인 관찰은 Game Boy의 도달 불가능한 opcode 표가 최종 데이터가 아니라 미끼이며, VMProtect가 복원한 PE 메모리의 별도 ELF 리소스에 AES key와 ciphertext가 함께 있다는 점이다.

## 환경 및 초기 분석

공식 입력은 [`public.zip`](../challenge/public.zip)이며 password는 문제 페이지에 제시된 `infected`이다. ZIP의 SHA-256은 `39f883b263363a25d52f2227dca764bacf4fa5f4c534baab0d1701a232ebae83`이고, 내부 [`Pickle_Riiiiick`](../challenge/Pickle_Riiiiick)은 43,434,736바이트의 static ELF64 x86-64 파일이다. 공용 환경은 [`requirements.txt`](../../../requirements.txt)로 복원했으며, 최종 solver가 직접 사용하는 주요 package는 `pyzipper 0.3.6`, `frida 17.18.0`, `pycryptodomex 3.23.0`이다.

ELF의 `main`은 내장 PE를 `$HOME/.cache/.icons/.hidden/update.exe`로 쓴다. PE는 PyInstaller Python 3.10 stub이며 `<<<PAYLOAD_START>>>` marker 뒤에 길이와 난독화된 다음 PE를 둔다. 정적 문자열과 Python bytecode를 확인해 다음 역변환을 얻었다.

```text
payload_length = LE32(data_after_marker[0:4]) = 0x555000
decoded = reverse(scrambled[i] XOR [a5, 3c, ff, 00, 55, aa][i mod 6])
```

복원된 [`final.exe`](../output/final.exe)는 5,591,040바이트이며 SHA-256은 `89a4f03151228ced4fbaf0ec4ff89bbf7895e25e67d55b8331e2e0543d3c8de7`이다. `.vmp0`/`.vmp1` section과 비정상 entry point 때문에 VMProtect로 보호된 것을 확인했다.

## 핵심 분석

`final.exe`를 Frida로 spawn한 뒤 `ShellExecuteA`를 실행 전에 hook했다. 이 함수의 인자는 `%TEMP%\AURA.gb`였고, 32 KiB Game Boy ROM의 SHA-256은 `3141a477c0f440248e71146b2c6f4c582ef0a3a8db30a797df27d272e6812071`이다. ROM 게임은 다섯 stage 뒤 `YOU GOT A / LITTLE GIFT ;)`를 표시한다. `0x15f2`의 gift routine은 즉시 `RET`하는 `0x0af2`를 호출하며, 그 뒤에는 140개짜리 가상 opcode metadata 표가 있다. 이 표는 추가 분석 계층처럼 보이도록 만든 미끼였다.

같은 시점에 VMProtect가 복원한 main module을 조사하면 실제 `.data`가 보인다. `base+0x4000`에는 ROM, `base+0xc000`에는 ROM 길이 `0x8000`, `base+0xc020`에는 또 다른 ELF가 있고 `base+0xd618`에는 그 길이 `0x15f8`이 있다. Solver는 `ShellExecuteA`를 성공값 `33`으로 대체해 GUI 실행을 막은 상태에서 이 5,624바이트를 읽는다. 결과물은 [`hidden-elf`](../output/hidden-elf)이고 SHA-256은 `eaccb6522ec941e1a00ad6360c26888de73da7316892e50b4ab752c81dc9e107`이다.

이 ELF는 실행 code 없이 AES 상수만 담은 위장 container이다. `.rodata` offset `0x1000`의 첫 16바이트는 ASCII key `M68K_AES_FLAGKEY`이고, 그 뒤에는 AES Rcon, S-box, inverse S-box가 있다. `.data` offset `0x1220`의 48바이트가 ciphertext다. AES-128-ECB로 복호화하면 마지막 block이 `0x09` 아홉 개로 끝나므로 PKCS#7 unpadding이 적용된다.

```text
AES-128-ECB(key = "M68K_AES_FLAGKEY")
ciphertext = 674e0e339bc75891878e9418bb3fb91a
             f8fa389587016dfbe91db26b39b41c51
             bc8a191fbdc5ad5fb30b22aa6c0d35b3
```

## 풀이 및 재현

[`solve.py`](../solve.py)는 ZIP을 memory에서 열고 marker 기반 XOR·reverse를 수행한다. 복원된 PE를 `output/final.exe`에 쓴 뒤 Frida로 spawn하고, `ShellExecuteA`와 message-box API를 대체해 외부 GUI를 띄우지 않는다. unpack 완료 시점의 RVA에서 ELF를 가져와 ELF64 section header를 직접 parsing하고 AES-ECB 복호화와 PKCS#7 unpadding을 수행한다. Competition의 `.venv`를 활성화하고 challenge root에서 실행한다.

```bash
python -m pip install -r ../../requirements.txt
python -m pip check
python solve.py
```

Solver는 현재 작업 디렉터리에 의존하지 않으며, 성공 시 newline 없이 flag 39바이트만 stdout에 출력한다.

## 결과

실제 `python solve.py` 실행은 exit code `0`, stderr `0`바이트, stdout `39`바이트로 완료되었다. stdout은 challenge root의 `flag` 파일과 byte 단위로 일치했다.

```text
psctf{U_sh0u1dvebeen_@_g@m3r_0rHighIQ!}
```

## 정리 및 회고

파일 형식 표식은 실행 architecture를 확정하지 않는다. 이 문제는 ELF, PyInstaller, VMProtect, Game Boy, 다시 ELF를 겹쳐 분석가가 눈앞의 형식에 머물도록 유도한다. 동적 분석에서는 최종 행위 자체보다 그 직전의 unpacked module memory를 확보하는 편이 보호기법 전체를 해제하는 것보다 짧고 재현 가능했다. 또한 ROM의 정교한 VM metadata도 별도 리소스가 존재한다는 PE-level 증거와 대조해 미끼로 판정할 수 있었다.

## 참고 자료

외부 자료는 최종 풀이에 사용하지 않았다. 파일 형식, offset, 변환식, key와 ciphertext는 모두 제공 artifact의 정적 분석과 격리된 local runtime 관찰에서 얻었다.
