# 테스트 시나리오

## 1. 날짜 기반 파일명 생성

입력:

- date: `20260428`

기대:

- Standard: `Std_Test_20260428.vqud`
- Unknown: `Unk_Test_20260428.vqud`
- Target: `C:\UVVis-Data\Parameter\2026\04\20260428_YKJ_ASX_Test_Std_Final.vasm`

## 2. source vasm 열기

조건:

- `UV Launcher` 실행 상태
- ASX-560 Controller 미실행 상태

기대:

1. `UV Launcher`에서 `Automatic Analysis` 클릭
2. ASX-560 Controller 창 생성
3. `Read` 클릭
4. Open 또는 열기 창 표시
5. `C:\UVVis-Data\Parameter\20241104_YKJ_ASX_Test_Std_Final.vasm` 열기

## 3. Standard 파일명 치환

조건:

- Analysis Setting 창 표시
- `Analysis1` 탭에 기존 `Std_Test_20241206.vqud` 존재

기대:

1. `Analysis1` 탭 선택
2. `File Name` 입력칸 클릭
3. 기존 파일명 전체 선택
4. `Std_Test_YYYYMMDD.vqud`로 치환

## 4. Unknown 파일명 치환

조건:

- Analysis Setting 창 표시
- `Analysis2` 탭에 기존 `Unk_Test_20241206.vqud` 존재

기대:

1. `Analysis2` 탭 선택
2. `File Name` 입력칸 클릭
3. 기존 파일명 전체 선택
4. `Unk_Test_YYYYMMDD.vqud`로 치환

## 5. Save As 저장

조건:

- Standard/Unknown 파일명 치환 완료

기대:

1. `Save As and Close` 클릭
2. 저장 창 표시
3. target `.vasm` 경로 입력
4. 저장 완료

## 6. Read 좌표 실패

조건:

- ASX 창 크기나 DPI가 기준과 다름

기대:

- `timeout waiting for open dialog` 기록
- `timeout_open_dialog.png` 저장
- 스크린샷 기준으로 `READ_BUTTON` 좌표 보정

## 7. Edit 좌표 실패

조건:

- `Edit` 클릭 후 Analysis Setting 창이 안 뜸

기대:

- `timeout waiting for 'Analysis Setting - ASX-560 - Quantitation'` 기록
- `after_edit_click.png` 확인
- `EDIT_BUTTON` 좌표 보정

## 8. File Name 치환 실패

조건:

- Analysis Setting 창은 표시되지만 파일명이 바뀌지 않음

기대:

- `FILE_NAME_INPUT` 좌표 보정
- 치환 순서 `Ctrl+A -> Backspace -> paste -> Tab` 유지

## 9. Save As 클릭 실패

조건:

- 파일명은 바뀌었지만 저장 창이 뜨지 않음

기대:

- `timeout waiting for save dialog` 기록
- `timeout_save_dialog.png` 확인
- `SAVE_AS_AND_CLOSE` 좌표 보정
