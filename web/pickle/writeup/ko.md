# pickle

> 스포일러: 이 문서는 문제의 분석 과정과 최종 풀이를 포함합니다.

## 개요

| 항목 | 내용 |
|---|---|
| 상태 | solved |
| 대회·플랫폼 | PwnSec CTF 2026 |
| 분야 | web |
| 난이도 | Easy |
| Flag 형식 | `pwnsec{...}` |

이 문제는 base64로 받은 Python pickle을 제한된 unpickler로 복원한다. 결정적인 결함은 disassembly가 실패하면 `REDUCE` 검사까지 건너뛰지만, 같은 불완전한 pickle을 실제 unpickler가 먼저 실행한다는 점이다. 이 차이를 이용해 금지된 문자열 없이 `/app/flag.txt`를 읽었다.

## 환경 및 초기 분석

공식 입력은 [public.zip](../challenge/public.zip)과 그 안의 [webapp.py](../challenge/challenge/webapp.py), [sessionstore.py](../challenge/challenge/sessionstore.py), Docker 구성이다. 공용 Python 환경은 `../../../requirements.txt`로 복원한다. 서비스는 `POST /restore`의 JSON `payload`를 base64 decode한 뒤 byte blocklist, `pickletools.dis()`, `RestrictedUnpickler.load()` 순서로 처리한다. 허용 module의 첫 segment는 `sessionstore`와 `collections`뿐이며, `REDUCE` opcode와 `.`, `flag`, `getattr` 같은 raw byte 문자열을 차단한다. 원격 서비스 주소 `https://d5680026f8c80379.chal.ctf.ae` 를 확인했다.

## 핵심 분석

`check()`는 `pickletools.dis()`와 `REDUCE` 문자열 검사를 같은 `try` 안에 두고 모든 예외를 무시한다. Pickle 끝의 `STOP` opcode는 바이트 `.`이므로 정상 pickle은 byte blocklist에도 걸린다. Payload에서 `STOP`을 생략하면 `pickletools.dis()`가 EOF에서 `ValueError`를 내어 `REDUCE` 검사가 생략된다. 이어지는 실제 unpickler는 EOF에 도달하기 전 모든 opcode와 부작용을 실행하며, 마지막 예외는 `restore()`가 억제한다.

허용된 `sessionstore.render`의 dotted name을 `STACK_GLOBAL`로 해석하면 `render.__globals__.__class__.__getitem__`, 즉 unbound `dict.__getitem__`을 얻는다. 이를 `render.__globals__['__builtins__']`에 적용해 `open`, `getattr`, `print`를 차례로 꺼낸다. `/app/flag.txt`를 열고 `read()` 결과를 `print()`하면 Flask가 redirect한 stdout에 flag가 들어간다. 모든 문자열은 `\\uXXXX`로 인코딩하므로 raw payload에는 금지된 `.`, `flag`, `getattr`이 없다. 상세 실행 근거는 [evidence.md](../analysis/evidence.md)에 보존했다.

## 풀이 및 재현

[solve.py](../solve.py)는 `instance.json`의 `main` URL을 읽고, 위 pickle을 생성하여 `POST /restore`로 전송한 뒤 `output`에서 `pwnsec{...}`를 추출한다. Competition의 `.venv`를 활성화하고 challenge root에서 실행한다.

```bash
python -m pip install -r ../../requirements.txt
python -m pip check
python solve.py
```

새 인스턴스가 발급되면 `instance.json`의 `url`만 바꾼다. Solver source에는 endpoint가 중복되어 있지 않다.

## 결과

[payload_probe.py](../analysis/payload_probe.py)는 제공 소스와 동일한 byte filter 및 restricted unpickler에서 disassembly 실패, blocklist 통과, 파일 내용 출력까지 확인했다. 이어서 `python solve.py`를 원격 인스턴스에 실행했으며 exit code 0, 빈 stderr, trailing newline 없는 24-byte stdout을 얻었다. 기록된 flag는 다음과 같다.

```text
pwnsec{d51962f679918668}
```

## 정리 및 회고

안전성 검사는 parser 오류를 허용한 채 위험한 deserializer로 진행해서는 안 된다. 특히 pickle은 `STOP` 전에 이미 함수 호출의 부작용을 실행할 수 있으므로, disassembler와 unpickler의 성공 조건이 다르면 malformed stream이 검사를 우회한다. Dotted global allowlist 역시 허용 module의 객체 그래프 전체를 노출하므로 module 이름만 확인하는 방식은 충분하지 않다.

## 참고 자료

- 외부 웹 자료는 사용하지 않았다.
- Python 표준 라이브러리 `pickle` 및 `pickletools` 동작은 제공 소스와 로컬 Python 3.12 실행으로 검증했다.
