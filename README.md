# Formaldehyde_A2

Shimadzu LabSolutions UV-Vis와 ASX-560 Controller 자동화 준비 프로젝트입니다.

이 저장소는 LabSolutions UV-Vis 관련 실행 파일의 윈도우/컨트롤 정보를 추출하고, 추출된 JSON과 운영 로그를 바탕으로 Python 좌표 자동화를 보정하기 위한 자료를 담고 있습니다.

## 구성

| 파일/폴더 | 설명 |
|---|---|
| `dump_classnn.py` | 실행 중인 Windows 프로그램의 top-level window와 자식 컨트롤 정보를 JSON으로 저장하는 도구 |
| `button1_calibration.py` | 1번 버튼 Calibration 준비 흐름을 좌표 기반으로 실행하는 자동화 스크립트 |
| `button2_sampleMeasurement.py` | 2번 버튼 Sample Measurement 준비 흐름을 좌표 기반으로 실행하는 자동화 스크립트 |
| `exe.json/` | 실제 실행 파일에서 추출한 컨트롤 dump 결과 |
| `docs/` | 운영 설계, 로그 정책, 테스트 체크리스트, 테스트 시나리오 |
| `CONTROL_ANALYSIS.md` | `exe.json`과 운영 가이드 기반 자동화 분석 문서 |
| `BUTTON1_CALIBRATION_WORKFLOW.md` | 1번 버튼 Calibration 자동화 구조와 좌표 기준 문서 |
| `BUTTON2_SAMPLE_MEASUREMENT_WORKFLOW.md` | 2번 버튼 Sample Measurement 자동화 구조와 좌표 기준 문서 |
| `requirements.txt` | Python 실행 의존성 |
| `openai_codex_example.py` | OpenAI API 호출 예제 |

## 문서

| 문서 | 용도 |
|---|---|
| `docs/architecture.md` | 자동화 레이어, 상태 모델, 실행 흐름 |
| `docs/logging-policy.md` | 로그 종류, 스크린샷 정책, 실패 원인 판독 기준 |
| `docs/manual-test-checklist.md` | 운영 PC에서 수동으로 확인할 체크리스트 |
| `docs/test-scenarios.md` | 날짜 파일명, Read/Edit/Save 실패 시나리오 |

## 설치

```powershell
pip install -r requirements.txt
```

## 컨트롤 정보 추출

대상 프로그램을 먼저 실행한 뒤 아래 명령을 실행합니다.

```powershell
python dump_classnn.py
```

특정 실행 파일만 추출하려면 `--exe` 옵션을 사용합니다.

```powershell
python dump_classnn.py --exe UVVisLauncher.exe
python dump_classnn.py --exe UVASXController.exe
```

출력 위치를 바꾸려면 `--out` 옵션을 사용합니다.

```powershell
python dump_classnn.py --exe UVVisLauncher.exe --out exe.json
```

## 현재 분석 요약

- `UVVisLauncher.exe`
  - WinForms 컨트롤이 추출됩니다.
  - 런처 버튼은 ClassNN 또는 창 기준 상대좌표로 자동화할 수 있습니다.
- `UVASXController.exe`
  - 창은 인식되지만 내부 컨트롤은 추출되지 않습니다.
  - 창 위치와 크기를 고정한 뒤 좌표 기반으로 자동화합니다.

자세한 내용은 `CONTROL_ANALYSIS.md`를 참고하세요.

## 1번 버튼 Calibration 자동화

실제 클릭 없이 생성될 파일명과 좌표를 먼저 확인합니다.

```powershell
python button1_calibration.py --dry-run
```

특정 날짜로 확인하려면 `YYYYMMDD` 형식으로 지정합니다.

```powershell
python button1_calibration.py --date 20260428 --dry-run
```

`UVVisLauncher.exe`가 실행 중이 아니면 자동으로 먼저 실행을 시도합니다.

```powershell
python button1_calibration.py --log-dir logs
```

실행 중 실패하면 `logs/` 폴더에 단계별 로그, 현재 창 목록, 스크린샷이 저장됩니다.

런처 경로를 자동으로 찾지 못하면 명시적으로 지정할 수 있습니다.

```powershell
python button1_calibration.py --log-dir logs --launcher-path "C:\Path\To\UVVisLauncher.exe"
```

## 2번 버튼 Sample Measurement 자동화

실제 클릭 없이 생성될 파일명, 랙 선택 계획, 기준 좌표를 먼저 확인합니다.

```powershell
python button2_sampleMeasurement.py --date 20260428 --sample-count 178 --dry-run
```

실행 시 입력창이 열리며 시료 수 `1`부터 `240`까지 입력할 수 있습니다. 빈값으로 확인하면 기본값 `180`을 사용합니다.

```powershell
python button2_sampleMeasurement.py --log-dir logs
```

기본 동작은 아래와 같습니다.

- `UVVisLauncher.exe`가 꺼져 있으면 먼저 실행
- `Automatic Analysis`를 통해 `ASX-560 Controller` 실행
- `C:\UVVis-Data\Parameter\20241101_YKJ_ASX_Test_Final.vasm` 열기
- `File Name`을 `YYYYMMDD H1H2H3.vqud` 형식으로 변경
- `Sample Type`을 `Sample`로 선택
- 랙 범위 선택 후 `Add to Table`
- `C:\UVVis-Data\Parameter\YYYY\MM\YYYYMMDD_YKJ_ASX_Test_Final_H1,2,3.vasm` 저장

특수 케이스:

- 시료 수 `178` 입력 시 `Rack 1 = 7A -> 12E`, `Rack 2 = 1A -> 12E`, `Rack 3 = 1A -> 10E`

버튼2도 실패 분석용 로그와 스크린샷을 `logs/` 폴더에 남깁니다.

## 권장 자동화 흐름

```text
LabSolutions UV-Vis Launcher 실행
→ Automatic Analysis 실행
→ ASX-560 Controller 창 생성 확인
→ Read로 기존 .vasm 열기
→ Edit로 Analysis Setting 진입
→ Analysis1 File Name을 Std_Test_YYYYMMDD.vqud로 치환
→ Analysis2 File Name을 Unk_Test_YYYYMMDD.vqud로 치환
→ Save As and Close
→ C:\UVVis-Data\Parameter\YYYY\MM\YYYYMMDD_YKJ_ASX_Test_Std_Final.vasm 저장
```

## 주의

- public 저장소에는 원본 제조사 매뉴얼 PDF를 포함하지 않습니다.
- `logs/`, `__pycache__/`, `.env`, `*.pdf`는 저장소에 올리지 않습니다.
- Windows GUI 자동화는 해상도, DPI 배율, 창 위치에 영향을 받을 수 있습니다.
- 실제 장비 제어 전에는 `--dry-run`과 수동 테스트 체크리스트를 먼저 확인합니다.
