# Button 3 Autosampler Stabilization Design

## 목적

`button3_autosamplerStabilization.py`는 오토샘플러와 Instrument Control 창을 순서대로 조작해서 장비를 안정화시키는 자동화 프로세스를 담당한다.

이번 단계에서는 구현 전에 작업 순서를 명확히 고정하고, 이후 좌표 캘리브레이션과 코드 작성의 기준이 되는 설계 문서로 사용한다.

## 대상 창

### 1. ASX 컨트롤러 창

- 창 제목: `ASX-560 Controller for LabSolutions UV-Vis`
- 실행 파일: `UVASXController.exe`
- 역할:
  - `S1`, `S2` 위치 선택
  - `Move` 클릭
  - `Up/Down` 클릭으로 니들 하강

### 2. Instrument Control 창

- 클래스: `#32770`
- 실행 파일: `UVNavi.exe`
- 식별 이름: `Instrument Control` 창
- 역할:
  - `Sip` 클릭
  - `Auto Zero` 클릭
  - 중간 대기 시간 처리

### 3. Quantitation 메인 창

- 예시 창 제목: `Quantitation - [Analysis]`
- 실행 파일: `UVNavi.exe`
- 역할:
  - `Instrument Control` 창이 열려 있지 않을 때 상단의 `Inst. Control` 버튼 클릭

## 전체 작업 순서

버튼 3은 아래 순서를 그대로 따른다.

### Phase 1. S2 위치 이동 및 니들 하강

1. `UVASXController.exe` 컨트롤러 창 활성화
2. `S2` 버튼을 마우스로 1회 클릭
3. `Move` 버튼을 마우스로 클릭
4. `5초` 대기
5. `Up/Down` 버튼을 마우스로 1회 클릭해서 니들을 아래로 내림

### Phase 2. Instrument Control 에서 1차 안정화

1. `Instrument Control` 창 활성화
2. `Sip` 1회 클릭
3. `40초` 대기
4. `Auto Zero` 1회 클릭
5. `Sip` 1회 클릭
6. `40초` 대기
7. `Auto Zero` 1회 클릭

### Phase 3. S1 위치 이동 및 니들 하강

1. `UVASXController.exe` 컨트롤러 창 활성화
2. `S1` 버튼을 마우스로 1회 클릭
3. `Move` 버튼을 마우스로 클릭
4. `5초` 대기
5. `Up/Down` 버튼을 마우스로 1회 클릭해서 니들을 아래로 내림

### Phase 4. Instrument Control 에서 2차 안정화 후 종료

1. `Instrument Control` 창 활성화
2. `Sip` 1회 클릭
3. `40초` 대기
4. `Auto Zero` 1회 클릭
5. `Sip` 1회 클릭
6. 흡광도가 안정화되었는지 확인해 달라는 팝업 표시
7. 종료

## 상태 표시 계획

자동화 진행 중 현재 작업 상황을 사용자가 바로 알 수 있도록 툴팁 또는 작은 상태창을 띄운다.

- 표시 위치: 마우스 근처
- 표시 목적: 현재 단계와 다음 대기 상태를 즉시 확인

표시 예시:

- `버튼3 시작: ASX 컨트롤러 확인 중`
- `S2 선택 중`
- `S2 위치로 Move 클릭`
- `니들 하강 중`
- `Instrument Control: Sip 1/2`
- `40초 대기 중`
- `Instrument Control: Auto Zero 1/2`
- `S1 선택 중`
- `S1 위치로 Move 클릭`
- `Move 후 5초 대기 중`
- `Instrument Control: 마지막 Sip 실행`
- `흡광도 안정화 여부 확인 요청`
- `버튼3 완료`

## 구현 권장 방식

### 공용 재사용

기존 `button1_calibration.py`의 공용 헬퍼를 그대로 재사용한다.

- 런처 확인
- 창 찾기
- 창 활성화
- 좌표 기반 클릭
- 로그 기록
- 스크린샷 저장

### 버튼 3 전용 추가 요소

버튼 3 구현 시 아래 요소를 추가한다.

- `Instrument Control` 창 탐색 함수
- `Quantitation` 메인 창에서 `Inst. Control` 버튼을 눌러 보조 창을 여는 함수
- `ASX` 창 전용 좌표 세트
- `Instrument Control` 창 전용 좌표 세트
- `Quantitation` 메인 창 전용 좌표 세트
- 단계별 상태 툴팁 표시 함수
- 긴 대기 시간(`40초`) 동안 남은 시간 표시 여부 검토
- `Move` 후 `5초` 대기 처리
- 긴급 중단 처리:
  - `Esc` 중단
  - `pyautogui.FAILSAFE` 마우스 코너 중단
- 마지막 확인 팝업 표시

## 예상 코드 구조

```text
button3_autosamplerStabilization.py
  - ensure_asx_controller_open()
  - ensure_quantitation_window()
  - ensure_instrument_control_open() 또는 wait_for_instrument_control()
  - open_instrument_control_if_needed()
  - show_status_tooltip(message)
  - show_completion_prompt(message)
  - click_asx_position(label, point)
  - click_instrument_control(label, point)
  - click_quantitation_position(label, point)
  - run_s2_lowering_sequence()
  - run_instrument_cycle_with_auto_zero_twice()
  - run_s1_lowering_sequence()
  - run_instrument_cycle_final()
  - run_button3_autosampler_stabilization()
```

## 좌표가 필요한 항목

아직 실제 좌표 캘리브레이션이 필요한 항목은 아래와 같다.

### ASX 컨트롤러 창

- `S1`
- `S2`
- `Move`
- `Up/Down`

### Instrument Control 창

- `Sip`
- `Auto Zero`

### Quantitation 메인 창

- `Inst. Control`

## 현재 확보된 좌표 정보

이미지와 Window Spy 기준으로 아래 정보는 확보되었거나 일부 근거가 있다.

- `Move`
  - ASX 컨트롤러 창 기준 마우스 위치 예시: `Client 89, 138`
- `S1`
  - ASX 컨트롤러 창 기준 마우스 위치 예시: `Client 99, 260`
- `S2`
  - ASX 컨트롤러 창 기준 마우스 위치 예시: `Client 128, 260`
- `Up/Down`
  - ASX 컨트롤러 창 기준 마우스 위치 예시: `Client 202, 142`
- `Sip`
  - Instrument Control 창 기준 마우스 위치 예시: `Client 58, 471`
  - 컨트롤 정보 예시: `ClassNN: Button16`, `x:17 y:440 w:102 h:65`
- `Auto Zero`
  - Instrument Control 창 기준 마우스 위치 예시: `Client 69, 644`
  - 컨트롤 정보 예시: `ClassNN: Button21`, `x:17 y:609 w:102 h:65`
- `Inst. Control`
  - Quantitation 메인 창 기준 좌표: `(953, 83)`
  - 클릭 후 `5초` 대기 후 Instrument Control 창 탐색

실제 구현 전에는 같은 방식으로 나머지 버튼 좌표도 동일 형식으로 확정한다.

## 실행 중 로그 예시

```text
[step] Activate ASX controller
[step] Click S2
[step] Click Move
[step] Wait 5 seconds after Move
[step] Click Up/Down
[step] Activate Instrument Control
[step] Click Sip
[step] Wait 40 seconds
[step] Click Auto Zero
[step] Click Sip
[step] Wait 40 seconds
[step] Click Auto Zero
[step] Activate ASX controller
[step] Click S1
[step] Click Move
[step] Wait 5 seconds after Move
[step] Click Up/Down
[step] Activate Instrument Control
[step] Click Sip
[step] Wait 40 seconds
[step] Click Auto Zero
[step] Click Sip
[step] Prompt user to confirm absorbance stabilization
[step] Button 3 completed
```

## 결정된 사항

- 버튼 3은 `ASX 컨트롤러`와 `Instrument Control` 두 창을 번갈아 사용한다.
- `Instrument Control` 창이 없으면 `Quantitation` 메인 창에서 `Inst. Control` 버튼을 눌러 연다.
- `Inst. Control` 버튼 클릭 후 `5초` 대기한다.
- 두 창의 기준 해상도와 위치는 고정한다.
- `S2` 작업을 먼저 수행한다.
- `S1` 작업은 그 다음에 수행한다.
- `Move` 클릭 후 `5초` 대기 뒤 `Up/Down`을 1회 클릭한다.
- 첫 번째 Instrument Control 구간에서는 `Sip -> 40초 대기 -> Auto Zero -> Sip -> 40초 대기 -> Auto Zero` 순서를 사용한다.
- 마지막 Instrument Control 구간에서는 `Sip -> 40초 대기 -> Auto Zero -> Sip` 후 종료한다.
- 자동화 중 현재 진행 상태를 마우스 근처 툴팁으로 보여준다.
- 마지막 `Sip` 후에는 흡광도 안정화 여부를 확인해 달라는 팝업을 띄운다.
- 중간 팝업이나 경고창 발생은 없다고 가정한다.
- 긴급 중단 수단으로 `Esc`와 마우스 코너 failsafe를 둔다.

## 다음 구현 단계

1. 실제 장비 PC에서 `--dry-run` 출력 좌표를 확인한다.
2. 실제 클릭 테스트를 진행한다.
3. `Inst. Control` 좌표가 환경에서 어긋나면 `INST_CONTROL_BUTTON` 값을 보정한다.
4. `Esc` 중단과 마우스 코너 failsafe 동작을 실제 환경에서 확인한다.
