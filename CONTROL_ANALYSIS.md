# EXE Control Dump 분석

분석 대상:

- `exe.json/UVASXController.exe.json`
- `exe.json/UVVisLauncher.exe.json`

## 요약

| 프로그램 | 창 인식 | 내부 컨트롤 인식 | 권장 자동화 방식 |
|---|---:|---:|---|
| `UVASXController.exe` | 가능 | 0개 | 창 고정 + 좌표 기반 클릭 |
| `UVVisLauncher.exe` | 가능 | 45개 | WinForms 컨트롤 기반 + 필요 시 좌표 클릭 |

`OperatorsGuidUV-Vis.pdf` 기준으로 LabSolutions UV-Vis의 기본 흐름은 `Launcher → 측정 Application 선택 → Instrument Connect → Auto Zero/Baseline → 측정`입니다. 따라서 자동화도 런처 단계와 실제 측정 프로그램 단계를 분리해서 설계하는 편이 좋습니다.

`UVASXController.exe`는 top-level 창은 잡히지만 내부 버튼/입력칸이 전혀 추출되지 않았습니다. 따라서 `ControlClick`이나 ClassNN 기반 자동화보다는 창 위치와 크기를 고정한 뒤 상대좌표로 클릭하는 방식이 현실적입니다.

`UVVisLauncher.exe`는 WinForms 컨트롤이 45개 추출되었습니다. 버튼 텍스트는 대부분 비어 있지만, 주변 `STATIC` 라벨과 버튼 좌표가 규칙적으로 배치되어 있어 ClassNN 또는 창 기준 상대좌표로 자동화할 수 있습니다.

## UVASXController.exe

### 창 정보

| 항목 | 값 |
|---|---|
| 프로세스 | `UVASXController.exe` |
| 창 제목 | `ASX-560 Controller for LabSolutions UV-Vis` |
| 클래스 | `HwndWrapper[UVASXController.exe;;54182117-b1e9-4cb2-a527-c2a631b54817]` |
| 창 좌표 | `[26, 26, 826, 605]` |
| 창 크기 | `800 x 579` |
| 내부 컨트롤 | `0개` |

### 해석

- WPF 계열 `HwndWrapper` 창으로 보입니다.
- 버튼/입력칸이 Win32 자식 컨트롤로 노출되지 않습니다.
- `dump_classnn.py` 기준으로는 내부 조작 대상을 식별할 수 없습니다.
- AutoHotkey의 `ControlClick`보다는 일반 `Click` 좌표 방식이 적합합니다.

### 권장 방식

1. `UVASXController.exe` 창을 찾습니다.
2. 창 위치와 크기를 고정합니다.
3. 버튼별 창 기준 상대좌표를 수동으로 기록합니다.
4. 클릭 전후 화면 상태는 이미지 인식 또는 OCR로 확인합니다.

예시 좌표 기준:

```text
창 좌상단: (26, 26)
창 크기: 800 x 579
상대좌표 클릭 = 실제 클릭 좌표 - 창 좌상단 좌표
```

## UVVisLauncher.exe

### 창 정보

| 항목 | 값 |
|---|---|
| 프로세스 | `UVVisLauncher.exe` |
| 창 제목 | `UV Launcher` |
| 클래스 | `WindowsForms10.Window.8.app.0.34f5582_r24_ad1` |
| 창 좌표 | `[104, 104, 602, 584]` |
| 창 크기 | `498 x 480` |
| 내부 컨트롤 | `45개` |

### 컨트롤 분포

| 종류 | 개수 |
|---|---:|
| `STATIC` | 22 |
| `BUTTON` | 20 |
| `WINDOW` | 3 |

### 주요 버튼 매핑

좌표는 `UV Launcher` 창 좌상단 기준 상대좌표입니다.

| 영역 | 라벨 | 버튼 ClassNN | 버튼 중심 상대좌표 |
|---|---|---|---|
| Analysis | `Spectrum` | `34f5582r24ad137` | `(69, 156)` |
| Analysis | `Quantitation` | `34f5582r24ad136` | `(159, 156)` |
| Analysis | `Photometric` | `34f5582r24ad135` | `(249, 156)` |
| Analysis | `Time Course` | `34f5582r24ad134` | `(339, 156)` |
| Manage | `Environmental Settings` | `34f5582r24ad133` | `(69, 276)` |
| Manage | `Automatic Analysis` | `34f5582r24ad15` | `(249, 276)` |
| Manage | `UVProbe File Viewer` | `34f5582r24ad14` | `(339, 276)` |
| Application | `Help` | `34f5582r24ad117` / `34f5582r24ad127` | `(69, 400)` |
| Application | `Operation Guide` | `34f5582r24ad115` / `34f5582r24ad125` | `(159, 400)` |
| Application | 빈 라벨 | `34f5582r24ad113` / `34f5582r24ad123` | `(249, 400)` |
| Application | 빈 라벨 | `34f5582r24ad111` / `34f5582r24ad121` | `(339, 400)` |
| Application | 빈 라벨 | `34f5582r24ad19` / `34f5582r24ad119` | `(429, 400)` |

### 특이사항

- `Application` 영역 하단 컨트롤 일부가 중복으로 추출되었습니다.
  - 예: `Help`, `Operation Guide` 버튼 세트가 같은 좌표에 두 번 나타납니다.
  - 실제 클릭 좌표는 동일하므로 자동화에는 큰 문제는 없습니다.
- 버튼 컨트롤의 `text` 값은 대부분 비어 있습니다.
  - 버튼 자체 이름 대신 주변 `STATIC` 라벨과 좌표로 매핑해야 합니다.
- `ClassNN` 값은 실행 환경이나 앱 빌드에 따라 변할 수 있습니다.
  - 장기적으로는 좌표 기반 fallback을 같이 두는 편이 안전합니다.

## PDF 기반 운영 흐름

`OperatorsGuidUV-Vis.pdf`는 LabSolutions UV-Vis 기본 조작 설명서입니다. 자동화와 관련된 핵심 내용은 다음과 같습니다.

### 프로그램 구성

| 구분 | PDF상 의미 | 자동화 관점 |
|---|---|---|
| `Spectrum` | 샘플의 스펙트럼 취득 | 런처의 Analysis 영역 버튼 |
| `Quantitation` | 표준시료 검량선 기반 농도 산출 | 런처의 Analysis 영역 버튼 |
| `Photometric` | 고정 파장 흡광도 측정 | 런처의 Analysis 영역 버튼 |
| `Time Course` | 시간에 따른 흡광도 변화 측정 | 런처의 Analysis 영역 버튼 |
| `Environmental Settings` | 장비 등록, 시스템 설정, 로그 확인 | 런처의 Manage 영역 버튼 |
| `Automatic Analysis Application` | 오토샘플러 연속 측정용 옵션 앱 | 별도 라이선스 필요 가능 |
| `UVProbe File Viewer` | UVProbe 데이터 파일 보기 | 장비 제어는 불가 |

### 시작 및 연결 흐름

PDF의 시작 절차는 다음 순서입니다.

1. 장비 본체 전원을 켭니다.
2. PC를 켭니다.
3. `LabSolutions UV-Vis` 런처를 실행합니다.
4. 필요 시 `Environmental Settings`에서 장비를 등록합니다.
5. 런처에서 `Spectrum`, `Quantitation`, `Photometric`, `Time Course` 중 측정 앱을 실행합니다.
6. 측정 앱 툴바에서 `Connect`를 클릭합니다.
7. 초기화 창이 나오면 설정 확인 후 `OK`를 누릅니다.
8. Instrument Control Window가 표시되면 측정이 가능합니다.

자동화에서는 이 흐름을 그대로 상태 체크 포인트로 쓰는 것이 좋습니다.

```text
UVVisLauncher.exe
→ 측정 앱 버튼 클릭
→ 측정 앱 창 생성 확인
→ Connect 클릭
→ 초기화/OK 처리
→ Instrument Control Window 확인
→ Auto Zero 또는 Baseline
→ 측정 실행
```

### 런처 제약

- 여러 측정 앱을 동시에 실행할 수는 있지만, 장비와 통신할 수 있는 앱은 한 번에 하나입니다.
- 동일한 측정 앱은 중복 실행할 수 없습니다.
- `Environmental Settings`는 측정 앱이 실행 중일 때 열리지 않을 수 있습니다.
- 런처는 측정 앱이 떠 있어도 별도로 종료/재시작될 수 있습니다.

자동화 스크립트는 실행 전 기존 측정 앱이 떠 있는지 확인하고, 필요하면 사용자에게 닫도록 안내하거나 해당 창을 재사용해야 합니다.

### 측정 전 보정 흐름

PDF상 측정 전 보정은 앱별로 공통 패턴이 있습니다.

| 측정 | 권장 보정 |
|---|---|
| `Spectrum` | Baseline Correction 후 샘플 측정 |
| `Quantitation` | 단일 파장은 Auto Zero, 복수 파장은 Baseline Correction |
| `Photometric` | 단일 파장은 Auto Zero, 복수 파장은 Baseline Correction |
| `Time Course` | 단일 파장은 Auto Zero, 복수 파장은 Baseline Correction |

자동화에 넣을 체크 포인트:

- 빈 시료 또는 blank sample 세팅 확인
- `Auto Zero` 또는 `Baseline` 버튼 클릭
- 보정 완료 대기
- 실제 시료 장착 확인
- 측정 실행

### 파일과 로그

PDF에서 확인되는 주요 파일 확장자는 다음과 같습니다.

| 구분 | 확장자 | 의미 |
|---|---|---|
| Spectrum data | `.vspd` | 스펙트럼 데이터 |
| Quantitation calibration | `.vqcd` | 검량선 데이터 |
| Quantitation result | `.vqud` | 정량 결과 |
| Time course data | `.vtmd` | 시간 변화 데이터 |
| Spectrum parameter | `.vspm` | Spectrum 측정 파라미터 |
| Quantitation parameter | `.vqum` | Quantitation 측정 파라미터 |
| Photometric parameter | `.vphm` | Photometric 측정 파라미터 |
| Time course parameter | `.vtmm` | Time Course 측정 파라미터 |
| Log | `.log` | 조작 이력 |

로그는 측정 앱 하단 로그 뷰에 표시되고, 과거 로그는 `Environmental Settings`의 `Log Confirmation`에서 확인할 수 있습니다.

## 자동화 전략

### UVASXController.exe

권장:

- AutoHotkey: `WinMove` + `Click x y`
- Python: `pywin32`로 창 찾기/이동 + `pyautogui.click`

주의:

- 해상도, DPI 배율, 창 크기가 바뀌면 좌표가 틀어질 수 있습니다.
- 실행 전에 창 위치/크기를 강제로 맞추는 단계가 필요합니다.

### UVVisLauncher.exe

권장 우선순위:

1. `ClassNN` 기반 클릭
2. 실패 시 창 기준 상대좌표 클릭
3. 실행 결과 확인은 창 제목 변화, 프로세스 생성, 이미지 인식 중 하나로 처리

예시:

```text
UV Launcher 창 고정
→ Analysis > Spectrum 버튼 클릭
→ 실행된 프로그램/창 확인
→ Connect 버튼 클릭
→ 필요 시 초기화 OK 처리
→ Auto Zero 또는 Baseline 수행
→ 필요한 다음 자동화로 진입
```

### 권장 스크립트 분리

| 스크립트 | 역할 |
|---|---|
| `launch_uvvis` | 런처 실행, 측정 앱 선택 |
| `connect_instrument` | 측정 앱에서 장비 연결 및 초기화 처리 |
| `calibrate_measurement` | Auto Zero 또는 Baseline 처리 |
| `run_measurement` | 샘플 측정 실행 |
| `control_asx560` | `UVASXController.exe` 좌표 기반 조작 |

이렇게 나누면 버튼 좌표가 바뀌어도 전체 스크립트를 고치지 않고 해당 단계만 수정할 수 있습니다.

## 다음 작업 제안

1. `UVASXController.exe`의 실제 버튼 위치를 스크린샷 기준으로 찍어 좌표표를 만듭니다.
2. `UVVisLauncher.exe`용 런처 자동화 스크립트를 먼저 만듭니다.
3. PDF 흐름에 맞춰 `Connect → 초기화 OK → Auto Zero/Baseline` 공통 루틴을 만듭니다.
4. `UVASXController.exe`는 창 고정 후 상대좌표 클릭 방식으로 별도 스크립트를 만듭니다.
5. 두 스크립트를 하나의 실행 흐름으로 묶어 `Launcher → 측정 앱 → Controller 조작` 순서로 자동화합니다.
