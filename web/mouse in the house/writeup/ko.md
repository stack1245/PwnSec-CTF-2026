# mouse in the house

> 스포일러: 이 문서는 문제의 분석 과정과 최종 풀이를 포함합니다.

## 개요

| 항목 | 내용 |
|---|---|
| 상태 | solved |
| 대회·플랫폼 | PwnSec CTF 2026 |
| 분야 | web |
| 난이도 | 미제공 |
| Flag 형식 | `pwnsec{...}` |

봇 전용 세션에 저장된 비공개 노트를 읽는 문제다. 결정적인 관찰은 DOMPurify를 통과하는 `data-prism-*` 속성으로 PrismJS의 동적 모듈 경로를 `data:` URL로 바꿀 수 있고, `postMessage`의 `event.source`를 이용하면 `window.opener = null` 이후에도 외부 부모 창을 다시 참조할 수 있다는 점이다.

## 환경 및 초기 분석

공식 입력은 [public.zip](../challenge/public.zip)이며 암호 `infected`로 해제했다. 앱은 Express 5.2.1, markdown-it 14.2.0, DOMPurify 3.4.10을 사용하고 봇은 Chromium 152와 Puppeteer 25.1.0을 사용한다. 공용 Python 환경은 [requirements.txt](../../../requirements.txt)로 복원한다.

`server.js`는 시작 시 `crypto.randomBytes(4)`로 8자리 16진수 ID를 만들고, `owner: BOT_SESSION_ID`인 플래그 노트를 `Map`에 넣는다. `/notes`는 `Sec-Fetch-Mode: navigate`만 받지만 `/notes/:id`는 세션 소유권만 확인한다. 노트 페이지에는 `sandbox allow-scripts allow-same-origin`과 제한된 `script-src`, `connect-src` CSP가 적용된다.

## 핵심 분석

PrismJS의 `src/global.js`는 문서에서 `data-prism-plugins`와 `data-prism-plugin-path`를 찾아 `import(pluginPath + plugin + ".js")`를 실행한다. 다음 본문은 정확히 80자이고 DOMPurify 뒤에도 두 속성이 보존된다.

```html
<p data-prism-plugins data-prism-plugin-path=data:text/javascript,import(name)#>
```

빈 `data-prism-plugins`는 빈 plugin ID 하나를 만들고, 첫 번째 `data:` 모듈은 `import(name)`을 실행한다. `window.name`에 URL 인코딩된 두 번째 `data:text/javascript,...` 모듈을 넣으면 `unsafe-eval` 없이 임의 JavaScript가 실행된다.

노트의 인라인 스크립트가 `window.opener = null`을 설정하고 CSP sandbox가 새 창 제어를 제한한다. 그러나 외부 부모가 팝업에 `postMessage`를 보내면 팝업은 `message` 이벤트의 `event.source`로 부모의 `WindowProxy`를 얻는다. 이어 부모를 봇 내부의 `/notes/`로 이동시키면 부모와 팝업이 같은 출처가 된다. 팝업은 부모 DOM의 `/notes/<id>` 링크를 열거하고, 허용된 `connect-src` 아래의 `/notes/:id`를 각각 fetch해 플래그 패턴을 찾는다.

## 풀이 및 재현

[solve.py](../solve.py)는 공개 노트에 80자 Prism payload를 만들고, 임시 HTTP loader와 callback을 준비한 뒤 봇을 방문시킨다. loader는 XSS 팝업을 열고 메시지를 보낸 다음 자신을 내부 `/notes/`로 이동한다. 팝업은 목록 DOM에서 ID를 얻고 비공개 노트를 fetch해 flag만 callback으로 전달한다. 변경 가능한 주소는 [instance.json](../instance.json)에만 있다.

Competition의 `.venv`를 활성화하고 challenge root에서 실행한다.

```bash
python -m pip install -r ../../requirements.txt
python -m pip check
python solve.py
```

## 결과

원격 봇의 callback에서 flag가 확인됐고, `python solve.py`의 stdout 및 `flag` 파일과 byte 단위로 일치했다.

```text
pwnsec{c723fccfe77783ae}
```

## 정리 및 회고

DOM sanitizer가 이벤트 핸들러와 `<script>`를 제거해도, 라이브러리가 DOM 속성을 설정으로 읽어 동적 import에 사용하면 script gadget이 된다. 또한 `window.opener = null`은 `postMessage`의 `event.source`로 복구되는 참조까지 막지 못한다. CSP sandbox와 Fetch Metadata 검사를 각각 따로 우회하기보다, 부모를 허용된 top-level navigation으로 같은 출처에 들여보내는 조합이 핵심이었다.

## 참고 자료

- [PrismJS global 모듈](https://esm.sh/gh/PrismJS/prism@36ad7f8/src/global.js): `data-prism-*` 설정과 동적 import 동작 확인.
- [TikTok 문제 힌트](https://www.tiktok.com/@ketnipz/video/7193363887985659142): 문제 설명에 제공된 원문 링크.
- [분석 증거](../analysis/evidence.md): sanitizer 결과, CSP 실패 원인, 원격 callback 근거.
