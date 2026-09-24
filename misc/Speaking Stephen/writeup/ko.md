# Speaking Stephen

> 스포일러: 이 문서는 문제의 분석 과정과 최종 풀이를 포함합니다.

## 개요

| 항목 | 내용 |
|---|---|
| 상태 | solved |
| 대회·플랫폼 | PwnSec CTF 2026 |
| 분야 | misc |
| 난이도 | Hard |
| Flag 형식 | `PWNSEC{...}` |

서비스는 tiny.en Whisper로 업로드 음성을 전사한 뒤 `espeak-ng -m`으로 다시 읽어 준다. 결정적인 문제는 전사 문자열을 신뢰하고 SSML 모드로 처리한다는 점이며, Whisper의 기호 억제를 BPE 결합 토큰으로 우회해 서버의 `flag.wav`를 `<audio>` 요소로 삽입할 수 있다.

## 환경 및 초기 분석

다운로드 가능한 공식 첨부물은 없었고, 문제 설명은 [challenge/README.md](../challenge/README.md)에 보존했다. 공용 환경은 [requirements.txt](../../../requirements.txt)로 복원한다. `/openapi.json`에는 `/transcribe` multipart 라우트가 있었으며, 메인 페이지는 모델이 `tiny.en`, TTS가 `espeak-ng`라고 밝혔다.

공개된 `entrypoint.sh` 조각은 `FLAG`를 `<say-as interpret-as="characters">`로 감싸 `$ICONDIR/flag.wav`에 생성했다. 또한 예제의 `<break time="1s"/>`가 실제 출력에 반영되어 전사 문자열이 `espeak-ng -m`에 그대로 들어감을 확인했다.

## 핵심 분석

직접 `<audio src="flag.wav"/>`를 말하게 하면 Whisper의 기본 `non_speech_tokens`가 `<`, `>`, `=`, 따옴표 같은 단일 기호 토큰을 억제한다. 그러나 같은 바이트열을 결합 BPE 토큰으로 만들 수 있다. 사용한 전체 문자열은 다음과 같다.

```text
 The HTML code."><audio src="flag.wav"/>
```

tiny.en tokenizer의 핵심 토큰열은 `526` (`."`), `6927` (`><`), `24051` (`audio`), `12351` (` src`), `2625` (`="`), `32109` (`flag`), `13` (`.`), `45137` (`wav`), `26700` (`"/>`)이며 모두 해당 억제 집합 밖이다.

`analysis/optimize_audio.py`는 tiny.en의 log-mel 경로를 미분해 목표 토큰에 대한 teacher-forced cross entropy를 최소화했다. 16-bit 저장 양자화를 forward pass에 포함해 실제 업로드 WAV에서도 전사가 유지되게 했다. 원격 서비스는 이 전사를 SSML로 해석해 sound icon 디렉터리의 `flag.wav`를 응답에 합성했다.

## 풀이 및 재현

[solve.py](../solve.py)는 최적화된 WAV를 gzip/base64로 내장한다. [instance.json](../instance.json)의 URL로 이를 업로드하고, 반환 음성을 `medium.en`과 `turbo`로 각각 전사한다. `medium.en`은 반복 문자 개수를 보존하는 데 사용하고, eSpeak의 `B`/`D` 발음을 더 정확히 구별한 `turbo` 결과로 문자 정체를 보정한다. 원격 응답 WAV도 [output/flag-audio.wav](../output/flag-audio.wav)에 보존한다.

단일 ASR 결과만으로는 `...663BB...`와 `...663DD...`가 충돌했다. 서버와 같은 eSpeak NG 1.51, `en-us`, 속도 110으로 두 후보를 다시 합성하고 원본 응답 안에서 최적 정렬한 결과, `DD` 후보의 코사인 유사도는 `0.999999981`(정규화 RMSE `0.000193`)이었고 `BB` 후보는 `0.185697593`이었다. 따라서 해당 두 문자는 `DD`로 확정했다. 비교 코드는 [analysis/compare_espeak.py](../analysis/compare_espeak.py)에 남겼다.

대회 공용 `.venv`를 활성화하고 challenge root에서 실행한다.

```bash
python -m pip install -r ../../requirements.txt
python -m pip check
python solve.py
```

## 결과

`python solve.py`는 exit code 0, 빈 stderr로 다음 바이트만 stdout에 출력했다.

```text
PWNSEC{2B1BA663DDAEE8A5}
```

검증된 flag는 `PWNSEC{2B1BA663DDAEE8A5}`이다.

## 정리 및 회고

생성 모델의 출력도 신뢰 경계를 넘어 다른 인터프리터로 전달되면 주입 입력이 된다. 토큰 억제는 문자열 수준의 금지가 아니므로, 동일 문자열을 만드는 결합 BPE 토큰이 남아 있는지도 확인해야 한다. 오디오 적대 예제는 파일 양자화와 실제 디코딩 경로를 손실 함수에 반영해야 원격 재현성이 생긴다.

## 참고 자료

- [OpenAI Whisper `transcribe.py`](https://github.com/openai/whisper/blob/main/whisper/transcribe.py): tiny.en 전사 옵션과 디코딩 흐름 확인.
- [eSpeak NG SSML and HTML Support](https://github.com/espeak-ng/espeak-ng/blob/master/docs/markup.md): `<audio src>`와 `-m` SSML 처리 확인.
