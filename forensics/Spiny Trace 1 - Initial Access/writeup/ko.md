# Spiny Trace 1 - Initial Access

> 스포일러: 이 문서는 문제의 분석 과정과 최종 풀이를 포함합니다.

## 개요

| 항목 | 내용 |
|---|---|
| 상태 | partial |
| 대회·플랫폼 | PwnSec CTF 2026 |
| 분야 | forensics |
| 난이도 | Easy |
| Flag 형식 | `T1234.001` |

문제는 공격자가 서비스 취약점이나 첨부파일을 쓰지 않고 피해자의 첫 실행을 얻은 방식을 설명하는 MITRE ATT&CK 서브테크닉을 요구한다. 결정적인 관찰은 피해자가 정기 검증 단계라고 믿고 코드를 직접 실행했다는 점이다.

## 환경 및 초기 분석

공식 입력은 문제 설명을 담은 [스크린샷](../challenge/codex-clipboard-693933eb-7841-4998-80ed-4c1a134a7b2c.png) 하나다. SHA-256은 `a63bd7ab2a2fcbcf6dd70fbe65575bcf23dfebee323da9234c8713ad1fd21651`이며 원본을 수정하지 않았다. 풀이에는 표준 라이브러리만 사용하며 대회 공용 Python 환경은 [`../../../requirements.txt`](../../../requirements.txt)로 복원한다.

화면은 공식 문제명 `Spiny Trace 1 - Initial Access`, 분야 `Forensics`, 난이도 `Easy`, 그리고 답 형식 `T1234.001`을 제시한다. 제출란의 `pwnsec{...}`는 플랫폼 공통 placeholder지만, wrapped 후보 `pwnsec{T1204.004}`는 실제로 거부됐다.

## 핵심 분석

관찰된 행위는 세 부분으로 구성된다. 공격자는 서비스를 exploit하지 않았고, 첨부파일도 전송하지 않았으며, 사용자가 검증 절차라고 믿고 코드를 직접 실행했다. 따라서 첨부 파일 실행을 뜻하는 `T1204.002`는 배제된다.

MITRE ATT&CK의 `T1204.004` **User Execution: Malicious Copy and Paste**는 사용자가 사회공학에 속아 명령 인터프리터에 코드를 복사·붙여넣고 실행하는 행위다. 공식 설명은 가짜 오류나 CAPTCHA 해결 절차를 ClickFix 예시로 들며, 문제의 “routine verification step”과 직접 일치한다. 근거와 배제 과정은 [`../analysis/evidence.md`](../analysis/evidence.md)에 보존했다.

## 풀이 및 재현

현재 가장 강한 후보는 wrapper 없는 `T1204.004`다. ATT&CK 분류 자체의 근거는 강하지만 플랫폼 승인이 아직 없으므로 검증된 solver와 `flag` 파일은 두지 않는다.

```bash
python -m pip install -r ../../requirements.txt
python -m pip check
T1204.004
```

## 결과

`pwnsec{T1204.004}`는 플랫폼에서 거부됐다. 문제의 명시적 답 형식에 따른 다음 제출 후보는 다음과 같다.

```
T1204.004
```

플랫폼 승인 전이므로 상태는 `partial`이다.

## 정리 및 회고

초기 접근을 분류할 때 전달 수단과 실제 실행 행위를 분리해야 한다. 이 문제에서는 링크나 파일 자체보다 사용자가 명령을 직접 실행하도록 유도한 행위가 결정적이므로 `T1204.004`가 가장 구체적인 분류다.

## 참고 자료

- [MITRE ATT&CK: User Execution — Malicious Copy and Paste (T1204.004)](https://attack.mitre.org/techniques/T1204/004/): 사용자 복사·붙여넣기 실행과 ClickFix 검증 미끼의 공식 정의를 확인했다.
