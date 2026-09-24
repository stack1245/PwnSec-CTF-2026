# Neon Skies

> 스포일러: 이 문서는 문제의 분석 과정과 최종 풀이를 포함합니다.

## 개요

| 항목 | 내용 |
|---|---|
| 상태 | solved |
| 대회·플랫폼 | PwnSec CTF 2026 |
| 분야 | web |
| 난이도 | Medium |
| Flag 형식 | `pwnsec{...}` |

목표는 관리자 봇의 HttpOnly `FLAG` 쿠키를 회수하는 것이다. 결정적인 결함은 앱이 동일 이름의 도메인 쿠키를 허용하고, Crystal의 중복 쿠키 파서가 마지막 값을 선택하며, `/admin`이 그 값을 HTML 이스케이프 없이 출력한다는 조합이다.

## 환경 및 초기 분석

공식 입력은 [public.zip](../challenge/public.zip)과 그 안의 Crystal 웹 앱, nginx 설정, Playwright 봇이다. 공용 Python 환경은 [requirements.txt](../../../requirements.txt)로 복원한다.

봇은 공개 앱 원점에 host-only, HttpOnly, `SameSite=Strict`인 `FLAG` 쿠키를 추가하고 `archivist`로 로그인한 다음 제출 URL을 방문한다. `/admin`은 유효한 `sid`가 있을 때 `FLAG` 쿠키를 `<output id="flag">` 안에 이스케이프 없이 출력한다. 직접 로그인, request-path XSS, `javascript:` redirect, 공개 컨테이너 포트 접근은 각각 원격 비밀번호 변경, `HTML.escape`, Chromium의 navigation 차단, 외부 포트 차단 때문에 실패했다.

## 핵심 분석

`FLAG`에는 `__Host-` prefix가 없으므로 다른 `*.chal.ctf.ae` 문서는 `Domain=chal.ctf.ae`인 동일 이름 쿠키를 만들 수 있다. 활성 `mouse in the house` 인스턴스의 이미 검증된 PrismJS dynamic-import gadget을 이용해 그 형제 원점에서 JavaScript를 실행했다.

스크립트는 다음 두 쿠키를 심는다.

```text
FLAG=<svg/onload=eval(atob(location.hash.slice(1)))>; Domain=chal.ctf.ae; Path=/admin
FLAG=<svg/onload=eval(atob(location.hash.slice(1)))>; Domain=chal.ctf.ae; Path=/
```

브라우저는 더 긴 path를 먼저, 같은 path에서는 먼저 생성된 쿠키를 먼저 전송한다. 따라서 `/admin` 요청의 `FLAG` 값은 공격 값, 원래 host-only secret, 공격 값 순서가 된다. Crystal 1.18.2의 `HTTP::Cookies#<<`는 같은 이름을 Hash에 다시 대입하므로 마지막 공격 값이 선택된다. 이 값은 `admin.ecr`의 raw sink에서 SVG `onload`로 실행된다.

관리자 원점에서 실행된 handler는 두 `Domain=chal.ctf.ae` 쿠키를 삭제하고 `/admin`을 다시 `fetch`한다. 남은 host-only HttpOnly `FLAG`는 JavaScript의 `document.cookie`로는 보이지 않지만 HTTP 요청에는 포함되고, 두 번째 관리자 응답 본문에 출력된다. 스크립트는 본문에서 flag를 추출해 callback으로 전송한다.

## 풀이 및 재현

[solve.py](../solve.py)는 `instance.json`에서 Neon 앱, 형제 스테이지, loader, callback 주소를 읽는다. 스테이지 note 생성, `window.name` data-module loader 구성, 도메인 쿠키 토싱, Neon 봇 report, callback 조회를 한 번에 수행한다.

Competition의 `.venv`를 활성화하고 challenge root에서 실행한다.

```bash
python -m pip install -r ../../requirements.txt
python -m pip check
python solve.py
```

## 결과

원격 end-to-end 실행은 exit code `0`, 빈 stderr, trailing newline 없는 24바이트 stdout을 생성했다. 같은 바이트가 `flag` 파일에 기록됐다.

```text
pwnsec{7f655c6d59355727}
```

## 정리 및 회고

민감한 쿠키 이름은 `__Host-` prefix로 domain cookie shadowing을 차단해야 한다. 서버는 중복 쿠키의 순서에 보안 결정을 의존해서는 안 되며, 쿠키 값도 신뢰하지 말고 출력 문맥에 맞게 이스케이프해야 한다. `HttpOnly`는 JavaScript의 직접 cookie 조회만 막으므로, 동일 원점 XSS가 보호 응답을 다시 가져올 수 있으면 secret을 보호하지 못한다.

## 참고 자료

- [neon_skies.cr](../challenge/public/web/src/neon_skies.cr): session, cookie 선택, `/admin` route 확인.
- [admin.ecr](../challenge/public/web/src/views/admin.ecr): raw `FLAG` HTML sink 확인.
- [conf.js](../challenge/public/bot/conf.js): 봇 cookie 속성과 navigation 순서 확인.
- [Crystal 1.18.2 `HTTP::Cookies`](https://github.com/crystal-lang/crystal/blob/1.18.2/src/http/cookies.cr): 중복 이름이 마지막 값으로 덮어써지는 동작 확인.
- 기존 `mouse in the house` 공식 입력과 solver: PrismJS 스테이지 gadget의 재사용 가능성을 확인.
