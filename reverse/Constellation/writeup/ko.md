# Constellation

> 스포일러: 이 문서는 문제의 분석 과정과 최종 풀이를 포함합니다.

## 개요

| 항목 | 내용 |
|---|---|
| 상태 | solved |
| 대회·플랫폼 | PwnSec CTF 2026 |
| 분야 | reverse |
| 난이도 | Hard |
| Flag 형식 | `pwnsec{...}` |

`main.exe`가 사용하는 컨테이너는 224개 data shard와 32개 parity shard로 구성된 systematic Reed–Solomon 계열 형식이다. `flag.flag`에는 블록마다 32개 shard가 지워져 있지만, GF(256) 선형 연립방정식과 별도의 shard 순열을 역으로 적용하면 내부 materialization archive를 복원할 수 있다. 그 안의 레코드를 재정렬·복호화해 파일 시스템 이미지를 얻고, 포함된 `flag.py`와 같은 해시를 계산하는 것이 목표다.

## 환경 및 초기 분석

공식 입력은 [`main.exe`](../challenge/main.exe)와 [`flag.flag`](../challenge/flag.flag)이다. `main.exe`의 크기는 497,097,807바이트이고 SHA-256은 `50f9c357eef50db9af6ac3df48af617595274c1b7794b73cc256dee5cad547c7`이다. `flag.flag`는 196,776바이트이고 SHA-256은 `8cd10a5e403850465568f79a01c8d49450c26e511e0dfca2e47f2012cf478a1b`이다.

Windows x64에서 Python 3과 IDA Professional 9.4를 사용했다. 공용 환경은 [`../../../requirements.txt`](../../../requirements.txt)로 복원한다. 프로그램은 GUI에서 입력 경로와 출력 경로를 받은 뒤 입력을 새로운 컨테이너로 pack했다. PE 본체 뒤에는 약 496 MB의 고엔트로피 overlay가 있었고, 일반 문자열 검색만으로는 변환 로직을 확인할 수 없었다.

## 핵심 분석

IDA에서 `sub_1400383A0`이 컨테이너 생성기이고 `sub_140032020`이 shard ID를 plan의 32비트 키로 정렬하는 비교 함수임을 확인했다. 컨테이너 헤더는 `<9I`이며 실제 값은 magic `0xe70b1591`, width `192`, data shard `224`, parity shard `32`, seed `0xc1028a4d`, block count `4`였다. 헤더 뒤에는 블록마다 `count || erased_indices[32]` 형식의 33바이트 메타데이터가 있고, 이어서 순열된 256개 shard가 온다.

GF(256)는 primitive polynomial `0x11d`를 사용한다. parity 행 `p`, data 열 `d`의 계수는 다음과 일치했다.

```text
M[p,d] = (p + 1)^d in GF(256)
```

실행 중 materialization plan을 읽어 각 블록의 256개 정렬 키를 확보했고, [`solve.py`](../solve.py)에 압축해 포함했다. 물리 위치 `j`의 논리 shard ID는 `sorted(range(256), key=(order_key[id], id))[j]`이다. 처음에 순열을 항등으로 가정했을 때 내부 magic이 나오지 않았지만, 이 순열을 역적용한 결과 첫 4바이트가 `11 50 9d 02`가 되어 `sub_1400352C0`에서 확인한 archive magic `0x029d5011`과 일치했다. 삭제된 data shard는 남은 parity 식에서 알려진 data 항을 제거한 뒤 GF(256) 가우스 소거로 복구했다.

복원된 stream은 entry magic `0xf12c04a7`을 쓰며 각 항목은 `path_len`, `record_len`, path, record 순서다. 모든 record는 `8 + 128 + 5 = 141`바이트였다. record 두 번째 dword의 하위 16비트와 원래 chunk 번호의 관계는 다음과 같다.

```text
chunk_index = (record_word_1 & 0xffff) XOR 0x06d0
```

471개 chunk가 정확히 `0..470`을 한 번씩 덮었다. payload를 이 순서로 합친 뒤, `mix32` 기반 keystream을 XOR했다. 기본 seed 변환은 `mix32(0x5e17e11d XOR 0x50524144)`이고, 각 dword 상태는 `mix32(output_offset + state + 0x6d2b79f5)`로 갱신된다. 결과는 60,288바이트 파일 시스템 archive였고 SHA-256은 `e9cbf4038148531e1d0b2acb0071b868d1fa41427b2420fbaf55dab89a0d7456`이다.

파일 시스템 archive에는 139개 항목(디렉터리 42개, 파일 97개)이 있었다. 포함된 `flag.py`는 자기 자신을 제외하고 경로순으로 각 디렉터리에 `D || u32(name_len) || name`, 각 파일에 `F || u32(name_len) || name || u64(body_len) || body`를 SHA3-512에 넣는다.

## 풀이 및 재현

[`solve.py`](../solve.py)는 컨테이너 파싱, shard 역순열, GF(256) erasure 복구, 내부 레코드 재정렬, XOR stream 복호화, 파일 시스템 해시를 모두 한 번에 수행한다. Competition의 `.venv`를 활성화하고 challenge root에서 실행한다.

```bash
python -m pip install -r ../../requirements.txt
python -m pip check
python solve.py
```

솔버는 복원된 파일 시스템 archive를 [`../output/recovered.bin`](../output/recovered.bin)에 기록하고, stdout에는 flag 바이트만 개행 없이 출력한다.

## 결과

`python solve.py`는 exit code `0`, stderr 0바이트, stdout 136바이트로 종료했다. stdout은 [`../flag`](../flag)와 byte-for-byte로 일치했다.

```text
pwnsec{c0d3ebc92d57e1db301dbf8a6a9595b3e003078fc977c204ab6ff6372353a6da60a423b3d9b57fd1c7618b976df1500f2d3b137d9b5e57e92909a140ae6ee99f}
```

## 정리 및 회고

Reed–Solomon 복구만 맞아도 shard 저장 순열이 틀리면 내부 형식 검증에 실패한다. 이 문제에서는 알려진 archive magic이 순열과 GF 연산을 독립적으로 검증하는 강한 기준이었다. 또한 알려진 입력을 프로그램으로 다시 pack한 결과와 비교해 record index 관계와 XOR keystream을 검증하면, 거대한 VM 전체를 해석하지 않고도 최종 데이터 경로를 재현할 수 있었다.

## 참고 자료

외부 자료는 사용하지 않았다. 알고리즘과 상수는 제공된 바이너리의 정적 분석, 로컬 실행 관찰, 생성된 컨테이너와 공식 입력의 비교에서 얻었다.
