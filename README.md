# Formaldehyde_A2

Shimadzu LabSolutions UV-Vis 자동화 준비 프로젝트입니다.

이 저장소는 LabSolutions UV-Vis 관련 실행 파일의 윈도우/컨트롤 정보를 추출하고, 추출된 JSON과 운영 가이드를 바탕으로 AutoHotkey 또는 Python 기반 자동화 스크립트를 설계하기 위한 자료를 담고 있습니다.

## 구성

| 파일/폴더 | 설명 |
|---|---|
| `dump_classnn.py` | 실행 중인 Windows 프로그램의 top-level window와 자식 컨트롤 정보를 JSON으로 저장하는 도구 |
| `button1_calibration.py` | 1번 버튼 Calibration 준비 흐름을 좌표 기반으로 실행하는 자동화 스크립트 |
| `exe.json/` | 실제 실행 파일에서 추출한 컨트롤 dump 결과 |
| `CONTROL_ANALYSIS.md` | `exe.json`과 운영 가이드 기반 자동화 분석 문서 |
| `BUTTON1_CALIBRATION_WORKFLOW.md` | 1번 버튼 Calibration 자동화 구조와 좌표 기준 문서 |
| `requirements.txt` | Python 실행 의존성 |
| `openai_codex_example.py` | OpenAI API 호출 예제 |

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
  - 창 위치/크기 고정 후 좌표 기반 자동화가 적합합니다.

자세한 내용은 `CONTROL_ANALYSIS.md`를 참고하세요.

## 1번 버튼 Calibration 자동화

실제 클릭 없이 생성될 파일명과 좌표를 먼저 확인합니다.

```powershell
python button1_calibration.py --dry-run
```

특정 날짜로 확인하려면 `YYYYMMDD` 형식으로 지정합니다.

```powershell
python button1_calibration.py --date 20260427 --dry-run
```

실행 전 `ASX-560 Controller for LabSolutions UV-Vis` 창이 열려 있어야 합니다.

```powershell
python button1_calibration.py
```

실행 중 실패하면 `logs/` 폴더에 단계별 로그, 현재 창 목록, 스크린샷이 저장됩니다.

```powershell
python button1_calibration.py --log-dir logs
```

## 권장 자동화 흐름

```text
LabSolutions UV-Vis Launcher 실행
→ 측정 앱 선택
→ 측정 앱 창 생성 확인
→ Connect
→ 초기화 OK 처리
→ Auto Zero 또는 Baseline
→ 샘플 측정
→ 필요한 경우 ASX-560 Controller 좌표 기반 조작
```

## 주의

- public 저장소에는 원본 제조사 매뉴얼 PDF를 포함하지 않습니다.
- `.env` 파일과 API 키는 저장소에 올리지 않습니다.
- Windows GUI 자동화는 해상도, DPI 배율, 창 위치에 영향을 받을 수 있습니다.
