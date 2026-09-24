# PHault

> 스포일러: 이 문서는 문제의 분석 과정과 최종 풀이를 포함합니다.

## 개요

| 항목 | 내용 |
|---|---|
| 상태 | solved |
| 대회·플랫폼 | PwnSec CTF 2026 |
| 분야 | web |
| 난이도 | 미제공 |
| Flag 형식 | `pwnsec{...}` |

`id`가 MySQL 쿼리에 그대로 연결되지만 정상·오류 응답의 문구와 실행 시간이 같아 일반적인 Boolean 또는 timing oracle은 보이지 않는다. 결정적인 관찰은 `SELECT ... INTO @var`가 성공하면 `mysqli::query()`가 결과 객체가 아닌 boolean `true`를 반환한다는 점이다. 뒤이은 `fetch_row()`를 의도적으로 PHP fatal error로 만들어 조건의 참·거짓을 구분하고 flag를 추출할 수 있다.

## 환경 및 초기 분석

공식 첨부 파일은 없고 HTTPS 인스턴스만 제공되었다. 접속 정보는 `../instance.json`, 재현 코드는 `../solve.py`, 요청·응답 근거는 [oracle.md](../analysis/oracle.md)에 보존했다. 솔버는 Python 표준 라이브러리만 사용하며 대회 공용 환경은 `../../../requirements.txt`로 복원한다.

루트 경로는 PHP 소스를 그대로 표시한다. 핵심 쿼리는 `SELECT username FROM users WHERE id = ` 뒤에 `$_GET["id"]`를 연결한다. 쿼리 실패와 정상 경로는 모두 `ill try to tell him, dw`를 출력하고, shutdown handler가 전체 실행 시간을 최소 2초로 맞춘다. 실제로 `SLEEP(4)`와 `BENCHMARK(...)`를 넣어도 두 요청 모두 약 2.6초에 끝나 timing 차이가 없었다.

## 핵심 분석

MySQL의 `SELECT ... INTO @x`는 result set을 반환하지 않는다. 쿼리가 0행 또는 1행이면 `mysqli::query()`는 boolean `true`를 반환하고, 애플리케이션의 `$res->fetch_row()`는 `Call to a member function fetch_row() on bool` fatal error를 낸다.

다음과 같이 외부 `users` 쿼리가 조건에 따라 0행 또는 전체 행을 반환하도록 만들었다.

```sql
0 OR IF((<condition>),1,0) INTO @phault
```

`users`에는 `admin`, `guest` 두 행이 있다. 조건이 참이면 두 행 이상을 `@phault`에 넣으려 해 SQL 오류가 발생하고 명시적 `die()` 경로로 간다. 조건이 거짓이면 0행 SELECT가 성공해 PHP fatal error가 난다. 관측된 응답은 각각 4557바이트와 4744바이트였으며 fatal error 문자열로 안정적으로 구분된다.

같은 오라클로 `information_schema`를 확인해 `flag,users` 테이블과 `flag(flag)` 열을 확정했다. 최종 대상 식은 `(SELECT flag FROM flag LIMIT 1)`이다.

## 풀이 및 재현

[solve.py](../solve.py)는 먼저 flag의 byte 길이를 이분 탐색한 뒤 각 위치의 `ORD(SUBSTRING(...))`를 0부터 255 사이에서 이분 탐색한다. 문자 위치는 최대 8개 요청으로 병렬 처리하며, 각 요청은 실패 시 최대 세 번 재시도한다. endpoint는 소스에 고정하지 않고 `instance.json`에서 읽는다.

대회 공용 `.venv`를 활성화한 뒤 challenge root에서 실행한다.

```bash
python -m pip install -r ../../requirements.txt
python -m pip check
python solve.py
```

## 결과

`python solve.py`는 exit code 0, 빈 stderr로 다음 stdout byte만 반환했다. 이 값은 `flag` 파일과 runtime validator 결과에 일치한다.

```text
pwnsec{74f8b0da59cbf20c}
```

## 정리 및 회고

출력과 시간이 모두 정규화된 blind SQL injection에서도 쿼리의 result-set 유무와 후속 PHP API의 타입 기대가 별도 오류 오라클이 될 수 있다. `SELECT ... INTO`의 0/1행 성공과 다중 행 실패를 조합하면 데이터 자체를 응답에 반영하지 않아도 1비트 조건을 복구할 수 있다.

## 참고 자료

외부 자료는 최종 풀이에 사용하지 않았다. 애플리케이션이 공개한 PHP 소스와 원격 요청·응답만 사용했으며 세부 증거는 [oracle.md](../analysis/oracle.md)에 기록했다.
