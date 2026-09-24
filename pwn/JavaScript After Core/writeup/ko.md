# JavaScript After Core

> 스포일러: 이 문서는 문제의 분석 과정과 최종 풀이를 포함합니다.

## 개요

| 항목 | 내용 |
|---|---|
| 상태 | solved |
| 대회·플랫폼 | PwnSec CTF 2026 |
| 분야 | pwn |
| 난이도 | Elite |
| Flag 형식 | `pwnsec{...}` |

목표는 동일한 `JSString`이 `win()`의 첫 검사에서는 `hello!!!`, 첫 콜백 뒤에는 `pwned!!!`, 둘째 콜백 뒤에는 `world!!!`로 보이게 만드는 것이다. 결정적 원인은 pinned JavaScriptCore의 FTL allocation sinking이 `haveABadTime()` 이후 배열을 잘못된 butterfly layout으로 rematerialize하는 버그다. 로컬 exact build에서 두 문자열 전환과 `./readflag` 호출을 확인했고, 새 원격 인스턴스에서 실제 flag를 회수했다.

## 환경 및 초기 분석

공식 입력은 [`public.zip`](../challenge/public.zip), [`diff.patch`](../challenge/diff.patch), [`Dockerfile`](../challenge/Dockerfile), [`README.md`](../challenge/README.md), `REVISION`, 서비스 스크립트 및 `readflag.c`다. ZIP의 SHA-256은 `EDBEE20504AD2B9C0BC5545C40822B62D120CCA2B660B75D7B840F3CDF3605C6`이다. `REVISION`에 고정된 x86-64 JavaScriptCore를 patch와 동일하게 빌드해 분석했다.

서비스는 TLS 뒤의 raw TCP로 JavaScript 한 프로그램을 EOF까지 받은 뒤 `/jsc/bin/jsc`로 한 번 실행한다. shell에서는 일반적인 exploit helper가 제거됐지만 `generateHeapSnapshotForGCDebugging()`은 남아 있었다. Python 의존성은 competition root의 [`requirements.txt`](../../../requirements.txt)와 공용 `.venv`를 사용했고 `pip check`가 통과했다.

## 핵심 분석

`Array.prototype[0]`에 accessor를 추가하면 VM이 `haveABadTime()` 경로로 들어간다. 취약 revision의 FTL OSR materialization은 원래 `Contiguous` butterfly를 80바이트 단위로 할당한 뒤, 바뀐 `SlowPutArrayStorage` structure를 가진 `JSArray`와 결합한다. 이후 index 7을 채우는 동작은 layout 차이 때문에 다음 allocation의 `IndexingHeader`를 덮는다.

8개의 길이 8 배열에서 index 0과 1을 hole로 남기고 index 2부터 6까지 객체를 넣어 `Contiguous`를 유도했다. index 7에는 IEEE-754 하위 32비트가 각각 `0x101`부터 `0x108`이 되는 finite double을 넣었다. 손상 뒤 유일하게 길이 8인 배열이 physical rank 0이고, 길이가 `0x101 + rank`인 배열을 반복해서 찾으면 8개 butterfly의 실제 연속 순서를 복원할 수 있다. rank 1 배열은 매우 큰 `vectorLength`를 얻어 forward OOB 접근 수단이 된다.

사전 heap snapshot에서 `target`, 두 source string, 일반 double `victim` 배열의 cell 주소를 얻었다. exact build에서 첫 vulnerable buffer는 `target + 0x5960` 또는 `target + 0x9960`에 놓였으며, `victim`의 첫 word를 두 후보로 읽어 `typeof`가 `number`인 후보를 선택했다. `victim`이 OOB보다 아래에 놓인 실행은 안전하게 재시도한다.

boxed number로 임의 pointer bit pattern을 저장하면 JSValue tag 때문에 cell로 재해석된다. 따라서 `victim`의 butterfly word에는 숫자가 아니라 source string 객체 자체를 저장했다. 이어 cell header를 exact-build double-array 값 `0x01082907010024e0`으로 바꾸면 `victim[1]`이 source `JSString`의 `StringImpl*` word를 raw double로 읽는다. butterfly를 `target` cell로 다시 지정하고 같은 index에 쓰면 동일한 target string의 impl을 `pwned!!!`, 이어 `world!!!`의 impl로 교체할 수 있다.

## 풀이 및 재현

최종 진입점은 [`solve.py`](../solve.py)다. payload를 내부에 압축해 포함하고 [`instance.json`](../instance.json)의 `main` endpoint만 읽는다. TLS `close_notify` 뒤에도 application data를 복호화해야 하므로 표준 라이브러리 `ssl.MemoryBIO`로 half-close를 구현했다. 힙 배치가 불리하거나 프로세스가 종료되는 경우 새 연결로 최대 40회 재시도하며, 성공 시 stdout에는 flag byte만 쓴다.

Competition의 `.venv`를 활성화하고 challenge root에서 실행한다.

```bash
python -m pip install -r ../../requirements.txt
python -m pip check
python solve.py
```

로컬 exact build의 성공 증거는 다음과 같다.

```text
targetNow=pwned!!!
targetNow=world!!!
sh: 1: ./readflag: not found
```

마지막 줄은 로컬 분석 디렉터리에 challenge container의 setuid `readflag`가 없기 때문이며, gate가 `system("./readflag")`까지 도달했음을 뜻한다.

## 결과

`d665d13875d6caa7.chal.ctf.ae:443`에 대해 `python solve.py`를 실행한 결과 exit code 0, 빈 stderr, trailing newline 없는 다음 stdout을 얻었다.

```text
pwnsec{d1f6845ef4379573}
```

이 byte sequence는 [`flag`](../flag)에 동일하게 기록했다. 성공 뒤 인스턴스는 `404 Deployment not found` 상태로 전환되어 추가 원격 재실행은 불가능했다.

## 정리 및 회고

이 문제의 핵심은 단순 OOB 길이 손상이 아니라 FTL rematerialization의 structure와 butterfly layout 불일치다. marker로 allocation 순서를 자기 기술적으로 복원하면 비결정적인 materialization 순서를 제거할 수 있다. 또한 NaN-boxed JSValue 저장에서는 임의 pointer를 숫자로 만들기보다 실제 객체 값을 이용해 cell pointer를 저장하고, forged double view의 index 보정으로 내부 field를 읽는 편이 안정적이었다.

## 참고 자료

- [`README.md`](../challenge/README.md): 서비스 입출력, 제거된 shell helper, `win()` 조건.
- [`diff.patch`](../challenge/diff.patch): shell hardening과 `win()` 구현.
- [`REVISION`](../challenge/REVISION) 및 [`Dockerfile`](../challenge/Dockerfile): 정확한 WebKit revision과 빌드 환경.
- 외부 자료는 사용하지 않았다.
