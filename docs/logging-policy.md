# 로그 정책

## 1. 로그 종류

### button1_calibration_YYYYMMDD_HHMMSS.log

1번 버튼 Calibration 자동화 실행 단위 로그입니다.

저장 위치:

- `logs\button1_calibration_YYYYMMDD_HHMMSS.log`

기록 내용:

- 실행 날짜
- Standard 결과 파일명
- Unknown 결과 파일명
- source `.vasm` 경로
- target `.vasm` 경로
- 단계별 창 탐색 결과
- 클릭 좌표
- 붙여넣은 값
- timeout 시점의 창 목록

### diagnostic screenshot

원인 분석용 스크린샷입니다.

저장 위치:

- `logs\button1_calibration_YYYYMMDD_HHMMSS_<label>.png`

현재 저장 지점:

- `after_read_click`
- `after_edit_click`
- `timeout_open_dialog`
- `timeout_save_dialog`
- 기타 timeout 지점

## 2. 로그 예시

```text
[2026-04-28 00:18:17] Click ASX Read: (454, 206)
[2026-04-28 00:18:18] Found open dialog: matched 'Open', hwnd=1574740
[2026-04-28 00:18:23] Paste standard file name: Std_Test_20260428.vqud
```

## 3. 상태 확인 기준

| 로그 내용 | 의미 | 조치 |
|---|---|---|
| `ASX Controller window is not open` | ASX 창이 없어 런처에서 실행 시도 | `UV Launcher`가 떠 있는지 확인 |
| `timeout waiting for open dialog` | `Read` 클릭 후 파일 열기 창이 안 뜸 | `Read` 좌표 보정 |
| `timeout waiting for save dialog` | `Save As and Close` 후 저장 창이 안 뜸 | 버튼 좌표 또는 파일명 치환 상태 확인 |
| `Screenshot failed` | 스크린샷 의존성 부족 | `pip install -r requirements.txt` 재실행 |

## 4. 보관 정책

- `logs/`는 로컬 진단 자료로만 사용한다.
- public GitHub 저장소에는 업로드하지 않는다.
- 오류 분석이 끝난 zip 파일은 필요 시 별도 보관하고 저장소에는 포함하지 않는다.

## 5. 민감정보 정책

- 장비 경로와 파일명은 로그에 남긴다.
- API 키, 계정, 비밀번호는 로그에 남기지 않는다.
- `.env` 파일은 `.gitignore`로 제외한다.
