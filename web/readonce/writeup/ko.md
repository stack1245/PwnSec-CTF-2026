# readonce

> 스포일러: 이 문서는 문제의 분석 과정과 최종 풀이를 포함합니다.

## 개요

| 항목 | 내용 |
|---|---|
| 상태 | solved |
| 대회·플랫폼 | PwnSec CTF 2026 |
| 분야 | web |
| 난이도 | Hard |
| Flag 형식 | `pwnsec{...}` |

목표는 관리자 봇의 세션으로만 접근 가능한 `/api/flag`의 값을 얻는 것이다. 결정적인 관찰은 `/review`가 공격자 URL을 서버 생성 nonce가 붙은 `<script src>`로 저장하고, 봇이 공격자 페이지의 리다이렉트를 따라 내부 `/sandbox`를 최상위 문서로 열 수 있다는 점이다. 이 조합은 의도된 iframe sandbox를 우회해 공격자 JavaScript를 관리자 origin에서 실행시킨다.

## 환경 및 초기 분석

공식 입력은 암호 `infected`로 해제한 [public.zip](../challenge/public.zip)이며, Express 애플리케이션과 Puppeteer 관리자 봇이 포함되어 있다. 애플리케이션은 Express 4.19.2, 봇은 Puppeteer 25.3.0을 선언한다. 분석과 재현에는 Python 3.12.10, Node.js 24.20.0, cloudflared 2026.9.1을 사용했다. 공용 Python 환경은 [requirements.txt](../../../requirements.txt)로 복원했다.

`bot/bot.js`의 `review()`는 관리자 세션을 만든 뒤 `/reports/check`, `/api/flag`, `/reports/arm/:id`를 차례로 요청한다. 마지막으로 신고 URL에 `rid`를 추가하여 같은 브라우저 context에서 열고 10초간 기다린다. 따라서 신고 URL에서 실행되는 코드가 내부 애플리케이션 origin으로 이동할 수 있다면 이미 관리자 cookie가 준비되어 있다.

## 핵심 분석

`GET /review?rid=RID&u=URL`은 인증 없이 현재 신고의 `rid`만 확인하고, `URL`에 `rid`를 추가한 뒤 `currentReview.document.url`에 저장한다. 이어 `GET /sandbox?rid=RID`는 다음 형태의 요소를 렌더링한다.

```html
<script nonce="SERVER_NONCE" src="ATTACKER_URL"></script>
```

CSP는 `script-src 'nonce-SERVER_NONCE'`와 Trusted Types를 요구하지만, 이 요소는 서버 템플릿이 만든 올바른 nonce를 가진 parser-created script다. 그러므로 공격자 URL의 JavaScript가 허용된다. 정상 `/review` 화면에서는 `/sandbox`가 제한된 iframe에 들어가지만, 봇의 신고 URL에서 `http://localhost:3000/sandbox?rid=RID` 로 302 응답을 보내면 같은 문서가 최상위 browsing context에 열린다.

이 스크립트의 `fetch` exfiltration은 `/sandbox`의 `default-src 'none'` 때문에 막힌다. 대신 스크립트는 `target=flagwin` 인 GET form을 `/api/flag`로 제출한다. 새 auxiliary window는 같은 origin의 JSON 응답을 표시한다. 500 ms 뒤 `open('', 'flagwin')`으로 기존 창을 다시 얻어 `document.body.innerText`를 읽고, 최상위 문서를 공격자 `/leak?data=...`로 이동시킨다. 실제 요청 흐름은 [exploit-notes.md](../analysis/exploit-notes.md)에 보존했다.

## 풀이 및 재현

[solve.py](../solve.py)는 Python 표준 라이브러리만 사용해 callback HTTP 서버를 실행한다. 봇이 `/start?rid=...`를 호출하면 solver가 원격 `/review`를 호출하여 `/payload.js`를 등록하고, 내부 `/sandbox`로 리다이렉트한다. payload는 form 대상 창에서 flag JSON을 읽어 `/leak`으로 돌려보낸다.

callback 서버는 인터넷에서 접근 가능해야 한다. 예를 들어 로컬 8000번 포트로 전달되는 HTTPS tunnel URL을 `READONCE_PUBLIC_URL`에 설정한다. `READONCE_LISTEN_PORT`의 기본값은 `8000`이다. 대상 주소는 [instance.json](../instance.json)에서만 읽는다.

```bash
python -m pip install -r ../../requirements.txt
python -m pip check
python solve.py
```

PowerShell 실행 시 tunnel을 준비한 뒤 `$env:READONCE_PUBLIC_URL='https://your-public-tunnel.example'`을 설정한다.

## 결과

원격 인스턴스에서 solver는 exit code 0, 빈 stderr, trailing newline 없는 24-byte stdout을 생성했다. stdout은 `flag` 파일과 byte 단위로 일치했다.

```text
pwnsec{f73af0e53bf677dc}
```

## 정리 및 회고

nonce 기반 CSP는 nonce를 가진 서버 생성 script 요소의 `src`가 공격자 입력이면 신뢰 경계를 만들지 못한다. 또한 iframe에만 적용한 sandbox는 같은 자원을 최상위 문서로 직접 열 수 있을 때 보호 수단이 아니다. `connect-src`가 외부 전송을 차단해도 navigation과 form target 같은 별도 브라우저 primitive를 함께 검토해야 한다.

## 참고 자료

- [bot/bot.js](../challenge/bot/bot.js): 관리자 세션과 신고 URL 방문 순서.
- [server.js](../challenge/src/server.js): `/review`, `/sandbox`, `/api/flag`, `/report`의 입력·상태·응답 조건.
- [sandbox.ejs](../challenge/src/views/sandbox.ejs): nonce가 붙은 외부 script 요소.
- 외부 기술 문서는 사용하지 않았다.
