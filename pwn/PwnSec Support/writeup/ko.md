# PwnSec Support

> 스포일러: 이 문서는 문제의 분석 과정과 최종 풀이를 포함합니다.

## 개요

| 항목 | 내용 |
|---|---|
| 상태 | solved |
| 대회·플랫폼 | PwnSec CTF 2026 |
| 분야 | pwn |
| 난이도 | Hard |
| Flag 형식 | `pwnsec{...}` |

제공된 서비스는 사용자 정의 32비트 ISA 위에서 Lua 5.5와 티켓 포털을 실행한다. 결정적인 관찰은 `/admin`의 SQL injection으로 Lua 콘솔에 들어갈 수 있고, 콘솔에 노출된 `note_save`로 writable code를 패치해 무작위 `FLAGPAD` 뒤의 플래그를 Lua 문자열로 반환할 수 있다는 점이다.

## 환경 및 초기 분석

공식 입력은 [public.zip](../challenge/public.zip), [l3afvm](../challenge/l3afvm), [ctf_sql.l3af](../challenge/ctf_sql.l3af)이다. 대회 공용 환경은 [requirements.txt](../../../requirements.txt)와 Python 3.12.10으로 복원했다. `l3afvm`은 stripped x86-64 PIE이며 NX와 GNU RELRO가 활성화되어 있다.

`ctf_sql.l3af`는 NDJSON 형식의 L3afVM 명령과 데이터를 담는다. 그 안의 `DATA_BYTES`를 복원하면 Lua 애플리케이션과 SQL 엔진 소스가 나온다. 복원본은 [analysis/lua](../analysis/lua)에 보존했다.

제공 바이너리는 `sqrtf@GLIBC_2.43`을 요구해 Debian bookworm 기반 Dockerfile과 직접 호환되지 않았다. 원본을 바꾸지 않고 ELF symbol version mapping만 조정한 [l3afvm.compat](../analysis/l3afvm.compat) 사본으로 로컬 실행을 재현했다. `--trace`는 다음 배치를 출력했다.

```text
data=0x00010000..0x003f9d04 code=0x003f9d10..0x006b2fd0 (178476 instructions)
```

로컬 이미지의 `pwnsec{test_local_build}`는 테스트 값이므로 원격 플래그로 사용하지 않았다.

## 핵심 분석

`check_admin()`은 다음과 같이 `token`을 SQL 문자열에 직접 연결한다.

```sql
SELECT u.id, u.username FROM sessions s, users u
WHERE s.token = '<token>' AND s.user_id = u.id AND u.is_admin = 1
```

초기 `sessions` 테이블이 비어 있어 단순 `OR`만으로는 행이 생기지 않는다. 다음 token은 `UNION`으로 함수가 기대하는 두 열을 직접 만든다.

```sql
' UNION SELECT 1, 'root' FROM users -- 
```

관리자 콘솔은 `load(code)`를 실행하고 전역 C 함수 `note_save(address, value)`를 노출한다. 이 함수는 VM 주소에 32비트 값을 저장하며 code와 data가 같은 writable memory에 있다.

인스턴스마다 `FLAGPAD` 크기가 달라 절대 주소는 변하지만 상대 배치는 일정하다. `n = address(note_save)`라 하면:

```text
code_base = n - 0x4150
FLAG      = code_base - 0x24 = n - 0x4174
patch     = code_base + 0x50c0 + 8 = n + 0xf78
```

`patch`는 `rand_hex()`가 `lua_pushlstring`에 넘기는 포인터를 적재하는 `LC` 명령의 immediate word다. 다음 Lua 한 줄로 그 포인터를 `FLAG`로 바꾸면 `rand_hex(24)`가 실제 24바이트 플래그를 반환한다.

```lua
local n=tonumber(tostring(note_save):match("(%x+)$"),16);note_save(n+0xf78,n-0x4174);print(rand_hex(24))
```

동일한 상대 주소 페이로드가 로컬 테스트 플래그와 원격 실제 플래그를 모두 반환해 배치 가설을 검증했다. 상세 관찰은 [observations.md](../analysis/observations.md)에 정리했다.

## 풀이 및 재현

[solve.py](../solve.py)는 [instance.json](../instance.json)의 `main` URL을 읽고 다음 과정을 자동화한다.

1. SQL `UNION` token과 Lua 패치 코드를 `/admin`에 POST한다.
2. Lua 출력의 `pwnsec{...}`만 검증해 추출한다.
3. 성공 시 flag byte만 개행 없이 stdout에 출력한다.

대회 `.venv`를 활성화하고 challenge root에서 실행한다.

```bash
python -m pip install -r ../../requirements.txt
python -m pip check
python solve.py
```

## 결과

`python solve.py`의 stdout과 [flag](../flag)의 byte가 일치하며 stderr는 비어 있고 exit code는 0이다.

```text
pwnsec{3644e5ca073c4089}
```

## 정리 및 회고

빈 테이블이 포함된 join에서는 `OR` 기반 인증 우회가 행을 만들지 못하므로 `UNION`으로 결과 shape를 직접 구성할 수 있다. 또한 주소 무작위화가 있어도 누출된 함수 주소와 고정된 코드 내부 상대 오프셋을 결합하면 위치 독립적인 guest-memory 패치를 만들 수 있다. writable code와 임의 word write가 함께 노출된 것이 최종 플래그 read primitive로 이어졌다.

## 참고 자료

외부 자료는 사용하지 않았다. 분석은 공식 handout, `readelf`, `objdump`, L3afVM `--trace`, Python 3.12.10, `curl`로 수행했다.
