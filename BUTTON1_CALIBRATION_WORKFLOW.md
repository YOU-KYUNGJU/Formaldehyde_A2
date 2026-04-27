# 1번 버튼 자동화 구조: Calibration 시작

이 문서는 `ASX-560 Controller for LabSolutions UV-Vis` 창에서 1번 버튼으로 실행할 Calibration 준비 자동화 흐름을 정리한 것입니다.

## 목적

`Automatic Analysis` 설정 파일을 읽어온 뒤, 오늘 날짜 기준으로 표준시료/미지시료 결과 파일명과 저장할 `.vasm` 파일 경로를 갱신합니다.

## 날짜 규칙

예시는 2026년 4월 27일 기준입니다.

| 항목 | 형식 | 예시 |
|---|---|---|
| 오늘 날짜 | `YYYYMMDD` | `20260427` |
| 연도 | `YYYY` | `2026` |
| 월 | `MM` | `04` |
| Standard 결과 파일 | `Std_Test_YYYYMMDD.vqud` | `Std_Test_20260427.vqud` |
| Unknown 결과 파일 | `Unk_Test_YYYYMMDD.vqud` | `Unk_Test_20260427.vqud` |
| 저장할 설정 파일 | `C:\UVVis-Data\Parameter\YYYY\MM\YYYYMMDD_YKJ_ASX_Test_Std_Final.vasm` | `C:\UVVis-Data\Parameter\2026\04\20260427_YKJ_ASX_Test_Std_Final.vasm` |

## 자동화 흐름

1. `Calibration 시작`
2. `Automatic Analysis` 실행 또는 `ASX-560 Controller for LabSolutions UV-Vis` 창 활성화
3. `Read` 클릭
4. Open 창에서 기존 설정 파일 열기
   - 기본 파일: `C:\UVVis-Data\Parameter\20241104_YKJ_ASX_Test_Std_Final.vasm`
5. `Edit` 클릭
6. `Analysis Setting - ASX-560 - Quantitation` 창에서 `Analysis1` 탭 선택
7. `File Name` 값을 오늘 날짜의 Standard 파일명으로 변경
   - 예: `Std_Test_20260427.vqud`
8. `Analysis2` 탭 선택
9. `File Name` 값을 오늘 날짜의 Unknown 파일명으로 변경
   - 예: `Unk_Test_20260427.vqud`
10. `Save As and Close` 클릭
11. Save As 창에서 오늘 날짜 기준 `.vasm` 경로 입력
    - 예: `C:\UVVis-Data\Parameter\2026\04\20260427_YKJ_ASX_Test_Std_Final.vasm`
12. 저장 클릭

## 좌표 자동화 기준

`ASX-560 Controller for LabSolutions UV-Vis` 창은 내부 버튼이 일반 Win32 컨트롤로 잘 잡히지 않으므로 좌표 기반으로 처리합니다.

### ASX-560 Controller 창

기준 창 크기: `739 x 599`

| 동작 | 기준 상대좌표 |
|---|---:|
| `Read` 클릭 | `(434, 186)` |
| `Edit` 클릭 | `(551, 186)` |

### Open 창

Open 창은 Windows 표준 파일 선택 창이므로 좌표 클릭보다 `파일 이름` 칸에 전체 경로를 붙여넣고 `Enter`를 누르는 방식이 더 안정적입니다.

### Analysis Setting 창

기준 창 크기: `1280 x 768`

| 동작 | 기준 상대좌표 |
|---|---:|
| `Analysis1` 탭 | `(58, 459)` |
| `Analysis2` 탭 | `(121, 459)` |
| `File Name` 입력칸 | `(255, 497)` |
| `Save As and Close` | `(922, 738)` |

## 구현 파일

좌표 기반 Python 자동화 코드는 `button1_calibration.py`에 작성합니다.

## 주의사항

- 실행 전 LabSolutions UV-Vis와 ASX-560 Controller 창이 떠 있어야 합니다.
- Windows DPI 배율이 바뀌면 좌표가 어긋날 수 있습니다.
- 스크립트는 창을 지정 위치/크기로 이동한 뒤 기준 좌표를 현재 창 크기에 맞춰 보정합니다.
- 실제 장비가 연결된 자동화이므로 처음에는 `--dry-run`으로 좌표와 파일명을 확인한 뒤 실행하는 것이 좋습니다.
