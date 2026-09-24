# PHP Sandbox Escape

> 스포일러: 이 문서는 문제의 분석 과정과 최종 풀이를 포함합니다.

## 개요

| 항목 | 내용 |
|---|---|
| 상태 | solved |
| 대회·플랫폼 | PwnSec CTF 2026 |
| 분야 | pwn |
| 난이도 | Hard |
| Flag 형식 | `pwnsec{...}` |

서비스는 POST 매개변수 `cmd`를 `eval()`하지만 `disable_functions`와 `open_basedir`로 파일·프로세스 API를 차단한다. 결정적인 관찰은 전역 `unserialize()`가 비활성화되어도 `SplDoublyLinkedList::unserialize()`가 같은 PHP 직렬화 파서를 호출한다는 점이다. `Serializable::unserialize()` 콜백에서 이미 등록된 객체의 property HashTable을 확장해 파서의 공유 `var_hash`가 해제된 bucket을 계속 가리키게 만들었고, 이를 임의 읽기와 가짜 `Closure` 객체로 발전시켜 `/readflag`를 실행했다.

## 환경 및 초기 분석

공식 입력은 암호 `infected`로 압축된 [`public.zip`](../challenge/public.zip)이며 SHA-256은 `4cb98c42514e5f1925ace170d8762c1f663b4328fdb34f0f7c8b0b5068e63778`이다. 압축을 푼 [`Dockerfile`](../challenge/public/Dockerfile)은 Ubuntu 이미지에서 PHP master를 빌드해 PHP-FPM으로 실행한다. [`php.ini`](../challenge/public/src/php.ini)는 `open_basedir=/home/ctf/scripts/:/tmp`를 지정하고 `system`, `exec`, `unserialize`, 파일 읽기 API를 포함한 대량의 함수를 비활성화한다. [`readflag.c`](../challenge/public/src/readflag.c)는 setuid root로 `/flag`를 읽는다.

원격 서비스는 PHP `8.6.0-dev`였고, 함수 호출 여부를 확인하는 초기 probe 뒤 정확한 빌드의 PHP를 WSL에서 컴파일해 구조체 크기와 exploit 조건을 검증했다. Python 실행 환경은 challenge root에서 `../../../requirements.txt`가 아니라 표의 상대 링크 기준 [`../../../requirements.txt`](../../../requirements.txt), shell 기준 `../../requirements.txt`로 복원한다.

## 핵심 분석

직렬화 스트림의 첫 원소로 property 8개를 가진 `stdClass`, 둘째 원소로 `CachedData implements Serializable`, 뒤쪽에는 spray 문자열과 `R:3`부터 `R:10`까지의 참조를 둔다. `SplDoublyLinkedList::unserialize()`가 스트림을 읽는 중 `CachedData::unserialize()`가 실행되고, 콜백은 전역으로 보관한 첫 객체에 아홉 번째 property `x`를 추가한다. 이 삽입은 property HashTable을 8개에서 16개로 확장하면서 원래 288-byte `arData`를 해제한다. 그러나 외부 파서의 공유 `var_hash`에 저장된 property zval 주소는 갱신되지 않는다.

해제된 288-byte chunk를 280-byte 문자열로 재할당하면 `R:n` 참조가 문자열 내부를 zval로 해석한다. exploit은 다음 순서로 이 원시 동작을 확장한다.

1. long zval spray의 참조 write-through 차이로 `zend_reference` heap 주소를 누출한다.
2. 같은 2 MiB Zend heap chunk를 문자열로 노출하고, 256개 `Closure` spray에서 반복되는 `zend_object` 패턴을 찾아 `ce`와 handlers 포인터를 얻는다.
3. handlers 인근 `.bss`를 읽어 `executor_globals`의 `function_table`과 `symbol_table`을 식별한다.
4. 활성 함수 `bin2hex`의 `zend_internal_function.module`에서 standard module을 찾는다. 이 PHP 8.6 빌드의 `zend_function_entry` 크기는 `0x38`이고, 원격 테이블에서 `system`은 287번 엔트리였다. 비활성화된 함수는 실행 테이블에서 제거되지만 module의 정적 엔트리와 원래 handler 주소는 남아 있다.
5. 원래 Closure의 `ce`/handlers와 `zif_system` handler를 넣은 가짜 `zend_closure`를 문자열에 작성한다. 마지막 UAF로 그 주소를 `IS_OBJECT` zval로 노출한 뒤 `/readflag` 인자로 호출한다.

전체 연구용 PHP와 단계별 진단은 [`exploit.php`](../analysis/exploit.php)에 보존했다. 최종 solver는 같은 payload를 gzip/base64로 자체 포함하므로 `analysis/` 파일에 의존하지 않는다.

## 풀이 및 재현

[`solve.py`](../solve.py)는 [`instance.json`](../instance.json)에서 HTTPS endpoint를 읽고, 자체 포함한 PHP payload를 `cmd`로 POST한다. 응답에서 `pwnsec{...}`만 추출해 stdout에 개행 없이 기록하고, 실패 진단은 stderr로 보낸다. Competition의 `.venv`를 활성화하고 challenge root에서 실행한다.

```bash
python -m pip install -r ../../requirements.txt
python -m pip check
python solve.py
```

## 결과

실제 `python solve.py` 실행은 exit code `0`, stderr 0 byte, stdout 24 byte를 반환했다. stdout은 [`flag`](../flag)의 byte와 정확히 일치했다.

```text
pwnsec{5dbe4132b1294725}
```

## 정리 및 회고

`disable_functions`는 internal function handler를 메모리에서 제거하지 않으며, 메모리 손상 원시 동작이 있으면 sandbox 경계가 아니다. 또한 wrapper 메서드가 동일한 직렬화 엔진을 노출할 수 있으므로 전역 함수 이름만 차단하는 방식은 불충분하다. 이 exploit에서는 PHP 8.6의 `zend_function_entry` 크기 `0x38`과 빌드별 함수 인덱스 287을 원격 메모리에서 검증한 것이 안정적인 재현의 핵심이었다.

## 참고 자료

- [PHP Sandbox Escape 공식 첨부 파일](../challenge/public/README.md): 서비스 구성, sandbox 목표, 로컬 실행 조건.
- [Calif, “21-Year-Old PHP Serializable shared-var_hash UAF”](https://calif.io/research/php-uaf): `Serializable` 재진입과 공유 `var_hash` UAF의 원리 및 원래 exploit chain.
- [Calif 공개 local exploit](https://github.com/califio/publications/blob/main/MADBugs/php/local_exploit.php): heap spray, executor globals 탐색, 가짜 Closure 구성의 기준 구현.

