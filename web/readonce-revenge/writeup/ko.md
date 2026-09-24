# readonce-revenge

> 스포일러: 이 문서는 문제의 분석 과정과 최종 풀이를 포함합니다.

## 개요

| 항목 | 내용 |
|---|---|
| 상태 | solved |
| 대회·플랫폼 | PwnSec CTF 2026 |
| 분야 | web |
| 난이도 | Hard |
| Flag 형식 | `pwnsec{...}` |

관리자 봇은 flag를 메모리에 넣은 뒤 공격자 URL을 방문한다. 결정적인 관찰은 숨은 `state`가 든 최초 `/reports/check` URL이 같은 탭의 session history에 남고, 관리자 전용 `/review`와 `/sandbox`도 봇의 top-level navigation으로 접근할 수 있다는 점이다. 이를 sandbox 승인 우회, history traversal, 저장 XSS로 연결한다.

## 환경 및 초기 분석

공식 입력은 [public.zip](../challenge/public.zip)이며 SHA-256은 `2F8E225AE02DEB8C0A66B82246CAB0895FA6A5C2948E8BD68B6683ACAE0F3187`이다. 압축 해제된 Node.js/Express 소스는 [challenge](../challenge)에 보존했다. Python 환경은 challenge root에서 competition의 [requirements.txt](../../../requirements.txt), 즉 shell 경로 `../../requirements.txt`로 복원한다.

`bot.js`의 방문 순서는 다음과 같다.

1. `GET /reports/check?rid=<id>&state=<nonce>`
2. `GET /api/flag`
3. `POST /reports/arm/<id>`
4. 공격자가 제출한 URL 방문 후 10초 대기

세션 cookie는 `HttpOnly; SameSite=Lax`이고, `/reports/check`의 두 번째 분기는 `prepared`, `approved`, 미사용 상태, 정확한 `rid/state`, 그리고 `Sec-Fetch-Site: none`, `Sec-Fetch-Dest: document`를 모두 요구한다.

## 핵심 분석

`/review`는 관리자 세션과 `rid`를 확인하고 공격자 script URL을 `currentReview.document`에 저장한다. 이어 `/sandbox`를 iframe으로 열고, 첫 iframe load 직후 `&end` 문서로 바꾼다. 공격자 script가 이전 문서의 `pagehide`에서 `top.postMessage()`를 실행하면, 부모가 받는 `event.source`는 이전 `WindowProxy`이고 현재 `viewer.contentWindow`와 다르다. 따라서 부모의 조건을 통과해 숨은 `state`를 포함한 `/complete` 요청이 전송되고 `approved=true`가 된다.

revenge 변경으로 `/sandbox`는 `sandbox allow-scripts` CSP를 사용하므로 iframe 내부 script의 origin은 opaque이다. 이를 직접 탈출하지 않고 다음 구조를 사용한다.

1. callback `/start`가 내부 `http://localhost:3000/review` 를 popup으로 연다. top-level GET이므로 봇의 Lax 관리자 cookie가 포함된다.
2. 원래 탭은 내부 `/sandbox?rid=...`로 이동한다. 같은 외부 `payload.js`가 이번에는 top-level sandbox에서 실행된다.
3. 단순 `history.go(-3)`는 최초 check가 BFCache에서 복원되어 서버에 도달하지 않는다. `/start`는 callback origin에 service worker를 등록하고, worker가 완전히 load된 문서 40개를 10ms 간격으로 합성한다. 이 history 채우기가 오래된 check 항목을 BFCache에서 축출한다.
4. 마지막 합성 문서는 `sessionStorage.done`을 설정한 뒤 `location.replace()`로 내부 sandbox에 들어간다. 이 표식은 history 복귀 중 마지막 navigation timer가 되살아나 check를 다시 덮는 현상을 막는다.
5. top-level sandbox의 payload는 `history.go(2-history.length)`로 숨은 nonce를 모른 채 최초 check 항목을 선택한다. 축출된 항목은 실제 네트워크 요청이 되며, 첫 응답이 설정한 `view` cookie 때문에 `Vary: Cookie` cache variant도 달라지고 Fetch Metadata는 요구값 `none/document`가 된다.
6. 승인된 두 번째 check는 지정한 note HTML을 raw로 렌더링한다. 128바이트 이하 저장 XSS가 callback의 `final.js`를 로드하고, 동기 XHR로 `/api/flag`를 읽어 navigation 경쟁 전에 callback으로 전송한다.

활성 BFCache 상태의 headless Chrome에서 service-worker history 채우기, 실제 두 번째 check 요청, flag 회수까지 연속 두 번 확인했다. 증거는 [local-validation.txt](../analysis/local-validation.txt)에 기록했다.

## 풀이 및 재현

[solve.py](../solve.py)는 `instance.json`의 `main`과 `callback` URL만 읽는다. callback URL은 실행 호스트의 TCP 8000번으로 전달되어야 한다. Solver는 note 생성, callback HTTP server 시작, report 제출, flag 형식 검증을 한 번에 수행한다.

```bash
python -m pip install -r ../../requirements.txt
python -m pip check
python solve.py
```

성공 시 stdout에는 trailing newline 없이 flag만 출력되고 stderr는 비어 있다.

## 결과

로컬 계측 환경에서 활성 BFCache를 그대로 둔 `python solve.py`가 연속 두 번 exit code `0`, 빈 stderr, 로컬 placeholder flag만 담긴 stdout으로 완료됐다. 이어 원격 인스턴스 `https://eb2735d8a9a959a2.chal.ctf.ae` 에서 같은 솔버를 실행해 exit code `0`과 정확히 24바이트의 stdout을 확인했다. 회수한 flag는 `pwnsec{917872750f693769}`이다.

## 정리 및 회고

`SameSite=Lax`는 외부 script의 fetch에는 cookie를 주지 않지만 top-level GET에는 보낸다. opaque sandbox가 직접적인 same-origin 접근을 막더라도 관리자 popup에서 상태 전이를 끝내고, service worker로 BFCache를 축출한 뒤 기존 session history를 네트워크 요청으로 되살릴 수 있다. 일회성 URL 방어에는 Fetch Metadata와 nonce뿐 아니라 `Cache-Control: no-store` 및 history/BFCache 동작까지 함께 고려해야 한다.

## 참고 자료

- [HTML Standard sandboxing flags](https://html.spec.whatwg.org/multipage/browsers.html): CSP sandbox의 opaque origin, popup, navigation 제한 확인.
- [Chromium BFCache overview](https://chromium.googlesource.com/chromium/src/+/main/docs/bfcache.md): history 복원과 네트워크 재요청 차이 확인.
- 공식 challenge source: route, session, bot 방문 순서의 기준.
