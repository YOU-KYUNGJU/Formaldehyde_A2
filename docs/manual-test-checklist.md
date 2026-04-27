# 수동 테스트 체크리스트

## 1. 사전 점검

1. 운영 PC에서 LabSolutions UV-Vis가 실행 가능한지 확인한다.
2. `UV Launcher`가 정상 표시되는지 확인한다.
3. Windows 해상도와 DPI 배율이 기존 테스트 환경과 같은지 확인한다.
4. `pip install -r requirements.txt`를 실행한다.
5. `C:\UVVis-Data\Parameter` 경로 접근 권한을 확인한다.
6. 기존 `logs/` 폴더에 쓰기 권한이 있는지 확인한다.

## 2. Dry Run 확인

1. PowerShell에서 아래 명령을 실행한다.

```powershell
python button1_calibration.py --date 20260428 --dry-run
```

2. Standard 파일명이 `Std_Test_20260428.vqud`로 출력되는지 확인한다.
3. Unknown 파일명이 `Unk_Test_20260428.vqud`로 출력되는지 확인한다.
4. target `.vasm` 경로가 `C:\UVVis-Data\Parameter\2026\04\20260428_YKJ_ASX_Test_Std_Final.vasm` 형식인지 확인한다.

## 3. 런처 진입 테스트

1. ASX-560 Controller 창을 닫은 상태로 둔다.
2. `UV Launcher`만 띄운다.
3. 아래 명령을 실행한다.

```powershell
python button1_calibration.py --log-dir logs
```

4. 로그에 `ASX Controller window is not open. Trying UV Launcher > Automatic Analysis.`가 기록되는지 확인한다.
5. ASX-560 Controller 창이 뜨는지 확인한다.

## 4. Read 테스트

1. ASX-560 Controller 창에서 `Read` 버튼이 눌리는지 확인한다.
2. 파일 열기 창이 뜨는지 확인한다.
3. 기존 source `.vasm` 파일이 열리는지 확인한다.
4. 실패하면 `timeout_open_dialog` 스크린샷을 확인한다.

## 5. Edit 테스트

1. `Edit` 버튼이 눌리는지 확인한다.
2. `Analysis Setting - ASX-560 - Quantitation` 창이 뜨는지 확인한다.
3. `Analysis1` 탭의 기존 `Std_Test_20241206.vqud`가 오늘 날짜 파일명으로 바뀌는지 확인한다.
4. `Analysis2` 탭의 기존 `Unk_Test_20241206.vqud`가 오늘 날짜 파일명으로 바뀌는지 확인한다.

## 6. Save As 테스트

1. `Save As and Close` 버튼이 눌리는지 확인한다.
2. 저장 창이 뜨는지 확인한다.
3. target `.vasm` 경로가 자동 입력되는지 확인한다.
4. 저장 후 Analysis Setting 창이 닫히는지 확인한다.

## 7. 실패 분석

1. `logs/`의 최신 `.log` 파일을 연다.
2. 마지막 `timeout` 메시지를 확인한다.
3. 같은 이름의 PNG 스크린샷을 확인한다.
4. 버튼 위치가 어긋났으면 `button1_calibration.py`의 기준 좌표를 보정한다.

## 8. GitHub 업로드 전 확인

1. `python -m py_compile button1_calibration.py dump_classnn.py` 실행
2. `git status --short --ignored`로 `logs/`, `*.pdf`, `__pycache__/`가 제외되는지 확인
3. 코드와 문서만 commit/push 한다.
