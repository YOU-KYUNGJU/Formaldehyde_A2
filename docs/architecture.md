# 아키텍처

## 1. 목표 구조

`런처 진입 + ASX 좌표 자동화 + 설정 파일 갱신 + 실행 로그` 구조로 운영한다.

LabSolutions UV-Vis와 ASX-560 Controller는 일반 Win32 컨트롤이 완전히 노출되지 않으므로, 컨트롤 dump 결과와 좌표 기반 자동화를 함께 사용한다.

## 2. 레이어

### 2.1 Control Dump

- 실행 중인 대상 프로세스 탐색
- top-level window 정보 수집
- 자식 컨트롤의 class name, ClassNN-like 값, text, rect 저장
- 결과를 `controls/` 또는 `exe.json/`에 JSON으로 저장

### 2.2 Launcher Automation

- `UV Launcher` 창 탐색
- 창 위치와 크기 고정
- `Automatic Analysis` 버튼 좌표 클릭
- ASX-560 Controller 창 생성 대기

### 2.3 ASX Controller Automation

- `ASX-560 Controller for LabSolutions UV-Vis` 창 탐색
- 창 위치와 크기 고정
- `Read` 클릭
- 설정 파일 열기 창 처리
- `Edit` 클릭

### 2.4 Analysis Setting Automation

- `Analysis Setting - ASX-560 - Quantitation` 창 탐색
- 창 위치와 크기 고정
- `Analysis1` 탭 진입
- Standard 결과 파일명 치환
- `Analysis2` 탭 진입
- Unknown 결과 파일명 치환
- `Save As and Close` 실행
- 날짜 기반 `.vasm` 저장 경로 입력

### 2.5 Path Builder

- 실행 날짜 계산
- `Std_Test_YYYYMMDD.vqud` 생성
- `Unk_Test_YYYYMMDD.vqud` 생성
- `C:\UVVis-Data\Parameter\YYYY\MM\YYYYMMDD_YKJ_ASX_Test_Std_Final.vasm` 생성

### 2.6 Logger

- 실행 시작 값 기록
- 단계별 클릭 좌표 기록
- 현재 창 목록 기록
- 실패 시 스크린샷 저장
- 로그와 스크린샷을 `logs/`에 저장

## 3. 처리 상태 모델

실행 단위 상태:

- initialized
- launcher_found
- asx_opened
- source_vasm_loaded
- analysis_setting_opened
- standard_filename_replaced
- unknown_filename_replaced
- save_as_clicked
- target_vasm_saved
- success
- failed

실패 원인:

- launcher_not_found
- asx_window_not_found
- open_dialog_not_found
- setting_window_not_found
- filename_field_not_focused
- save_dialog_not_found
- coordinate_mismatch
- dependency_missing

## 4. 실행 흐름

1. 날짜 기반 파일명과 저장 경로 계산
2. GUI 자동화 의존성 로드
3. 현재 창 목록 로그 저장
4. ASX 창이 없으면 `UV Launcher`에서 `Automatic Analysis` 클릭
5. ASX 창 위치와 크기 고정
6. `Read` 클릭 후 기존 `.vasm` 열기
7. `Edit` 클릭 후 Analysis Setting 창 대기
8. `Analysis1` 파일명을 Standard 파일명으로 치환
9. `Analysis2` 파일명을 Unknown 파일명으로 치환
10. `Save As and Close` 클릭
11. 오늘 날짜 기준 target `.vasm` 저장
12. 실패 시 창 목록과 스크린샷 저장

## 5. 설계 원칙

1. 내부 컨트롤이 잡히지 않는 창은 창 기준 상대좌표로 처리한다.
2. 좌표는 반드시 기준 창 크기와 함께 관리한다.
3. 실패 원인을 다음 실행에서 바로 보정할 수 있도록 로그와 스크린샷을 남긴다.
4. 원본 제조사 매뉴얼 PDF와 실행 로그는 public 저장소에 올리지 않는다.
5. 실제 장비 제어 전에는 `--dry-run`으로 파일명과 좌표를 먼저 확인한다.
