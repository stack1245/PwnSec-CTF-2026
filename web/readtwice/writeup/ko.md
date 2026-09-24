# readtwice

> 스포일러: 이 문서는 문제의 분석 과정과 최종 풀이를 포함합니다.

## 개요

| 항목 | 내용 |
|---|---|
| 상태 | solved |
| 대회·플랫폼 | PwnSec CTF 2026 · CTF.ae |
| 분야 | web |
| 난이도 | Hard |
| Flag 형식 | `pwnsec{...}` |

검사 시 JavaScript가 꺼진 DOM과 실제 검토 시 JavaScript가 켜진 DOM의 파싱 차이로 제한된 노트에서 스크립트를 실행하고, 봇의 승인 절차와 브라우저 history traversal을 결합해 보호된 문서를 두 번째로 읽었다.

## 환경 및 초기 분석

공식 소스는 [`../challenge/`](../challenge/)에 있다. 공용 환경은 [`../../../requirements.txt`](../../../requirements.txt)로 복원한다. `/create`는 JavaScript·네트워크를 끈 Chromium으로 최종 DOM을 검사하며, `/sandbox`는 `sandbox allow-scripts` CSP로 노트를 렌더링한다. `/reports/check`의 두 번째 요청은 관리자 세션, 승인·finalized 상태와 `Sec-Fetch-Site: none`, `Sec-Fetch-Dest: document`를 모두 요구한다.

## 핵심 분석

Declarative Partial Updates 처리 명령과 declarative shadow DOM의 `noscript` 파싱 차이를 사용했다. 검증기에서는 결과가 CSP meta 하나와 빈 `div` 하나로 정리되지만, 실제 검토에서는 외부 `/s.js`가 CSP meta 적용 전에 실행된다. 스크립트는 review iframe의 `MessagePort`를 공격자 창으로 전달하고 `ready`를 보내 `/complete`가 승인 상태를 설정하게 한다.

일반 교차 사이트 이동은 `Sec-Fetch-Site: cross-site` 라서 실패한다. 최초 공격자 문서가 `about:blank` 로 이동한 뒤 같은 origin의 helper 창이 `opener.history.back()` 을 호출하면, `Cache-Control: no-store` 인 최초 URL을 다시 요청하면서 `Sec-Fetch-Site: none` 이 생성된다. 두 번째 응답을 `http://localhost:3000/reports/check?rid=...` 로 302 redirect하면 이 값과 관리자 Lax 쿠키가 유지된다. 해당 navigation request 자체가 watcher의 `finalized` 를 설정하므로 raw note가 반환되고, 실행된 스크립트가 `/api/flag` 를 읽어 callback으로 보낸다.

## 풀이 및 재현

[`../solve.py`](../solve.py)는 [`../instance.json`](../instance.json)의 main·callback URL을 읽고 로컬 callback 서버를 연다. callback URL은 로컬 8000번 포트로 연결되는 공개 HTTPS tunnel이어야 한다.

```bash
python -m pip install -r ../../requirements.txt
python -m pip check
python solve.py
```

## 결과

`python solve.py`는 exit code 0과 개행 없는 다음 stdout을 반환했고 [`../flag`](../flag)와 byte 단위로 일치했다.

```text
pwnsec{1503fc99f750c466}
```

## 정리 및 회고

DOM 검증과 실행의 JavaScript 설정 차이는 parser differential을 만들 수 있다. Fetch Metadata 검사는 애플리케이션 상태 검사와 결합되어도 history traversal과 redirect가 만드는 `none` 요청을 신뢰 경계로 사용하면 우회될 수 있다.

## 참고 자료

- [`../challenge/bot/bot.js`](../challenge/bot/bot.js): DOM 검사기와 검토 봇 동작.
- [`../challenge/src/server.js`](../challenge/src/server.js): route, session, 상태 및 Fetch Metadata 정책.
- 외부 자료는 최종 풀이에 사용하지 않았다.
