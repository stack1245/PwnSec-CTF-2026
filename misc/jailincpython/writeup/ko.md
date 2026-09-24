# jailincpython

> 스포일러: 이 문서는 문제의 분석 과정과 최종 풀이를 포함합니다.

## 개요

| 항목 | 내용 |
|---|---|
| 상태 | solved |
| 대회·플랫폼 | PwnSec CTF 2026 |
| 분야 | misc |
| 난이도 | Medium (347점) |
| Flag 형식 | `pwnsec{...}` |

입력은 따옴표·숫자·괄호를 금지하고 점을 두 개로 제한하지만, comprehension target에 대한 대입과 `hint_A.__class_getitem__` 변경은 허용한다. 이를 이용해 subscription을 함수 호출 primitive로 바꾸고, descriptor를 거쳐 `ABCMeta.register.__builtins__`와 `os.system`에 도달하는 것이 핵심이다.

## 환경 및 초기 분석

공식 입력은 [`../challenge/main.py`](../challenge/main.py)이며 Python 3.12.3 원격 서비스로 확인했다. 공용 환경은 `../../../requirements.txt`와 competition `.venv`를 사용한다. 필터는 ASCII 800바이트 이하, 점 최대 2개, 따옴표·숫자·괄호 금지를 적용하지만 `{... for hint_A.__class_getitem__ in{f}}` 형태의 attribute target은 차단하지 않는다.

## 핵심 분석

`hint_A[x]`는 런타임에 교체한 `__class_getitem__`을 호출하므로 괄호 없이 함수를 실행할 수 있다. 페이로드는 `lambda x:x.__getattribute__`로 `object.__getattribute__` descriptor를 얻고, descriptor의 `__get__`을 바인딩해 임의 객체의 attribute getter를 만든다.

필요한 문자열은 허용된 `hint_B == "%jailincpython"`과 bound method repr의 고정 구간에서 합성한다. 이 방식으로 `__class__`, `__dict__`, `__subclasses__`, `register`, `__builtins__`, `__import__`, `os`, `system`, `sh`를 만든다. `type.__dict__["__subclasses__"]`로 `ABCMeta`를 구한 뒤 `ABCMeta.register`의 실제 Python 함수에서 정상 builtins dictionary를 회수한다. 최종 788바이트 페이로드는 `os.system("sh")`를 실행하며, 이어지는 소켓 입력이 셸 명령으로 처리된다.

원격 [`run.sh`](../analysis/remote_test.py)는 시작할 때 `/${RAND}.txt`에 flag를 기록하고 `FLAG` 환경 변수를 제거했다. 따라서 셸에 `cat /*.txt`를 보내 인스턴스별 랜덤 파일명을 직접 알 필요 없이 flag를 읽는다.

## 풀이 및 재현

최종 구현은 [`../solve.py`](../solve.py)에 있다. endpoint는 [`../instance.json`](../instance.json)에서 읽으며, TLS 연결 후 jail 페이로드를 보내 셸 prompt를 기다린 다음 `cat /*.txt`를 전송한다.

```bash
python -m pip install -r ../../requirements.txt
python -m pip check
python solve.py
```

## 결과

`python solve.py`는 exit code 0, 빈 stderr, trailing newline 없는 24바이트 stdout을 반환했고 [`../flag`](../flag)와 byte-for-byte 일치했다.

```text
pwnsec{974f89d15ad10e5c}
```

## 정리 및 회고

Pyjail에서는 금지된 문자 목록뿐 아니라 comprehension target과 special method 재대입 가능성을 함께 확인해야 한다. `__class_getitem__`은 `obj[arg]`를 호출 primitive로 바꾸며, descriptor binding과 Python 함수의 `__builtins__`를 조합하면 제한된 eval globals를 벗어날 수 있다. 또한 flag 위치가 랜덤이므로 solver는 특정 인스턴스의 파일명을 고정하지 않고 glob으로 처리해야 한다.

## 참고 자료

- [`../challenge/main.py`](../challenge/main.py): 필터와 eval globals의 공식 근거.
- [`../solve.py`](../solve.py): 최종 788바이트 페이로드와 원격 재현 코드.
- 외부 자료는 사용하지 않았다.
