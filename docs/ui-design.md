# Automation UI Design

## Goal

Provide one desktop launcher window for the three existing automation flows:

- Button 1: Calibration
- Button 2: Sample Measurement
- Button 3: Autosampler Stabilization

## Current Structure

- `src/formaldehyde_a2/button1_calibration.py`
- `src/formaldehyde_a2/button2_sampleMeasurement.py`
- `src/formaldehyde_a2/button3_autosamplerStabilization.py`
- `src/formaldehyde_a2/ui.py`

Root-level scripts remain as compatibility entry points:

- `button1_calibration.py`
- `button2_sampleMeasurement.py`
- `button3_autosamplerStabilization.py`
- `automation_ui.py`

## UI Decisions

- Use `tkinter` so the UI can run without adding new dependencies.
- Run each automation in a separate subprocess.
- Keep only one automation active at a time.
- Show stdout and stderr in a shared log panel.
- Keep shared inputs in one place:
  - date
  - sample count
  - launcher path
  - log directory
  - dry-run flag

## Why Subprocesses

The automation scripts already manage their own windows, message boxes, and timing.
Launching them in subprocesses avoids UI freezing and reduces interference between the launcher UI and the automation flow itself.

## Important UX Considerations

- Prevent concurrent runs.
- Make the active status obvious.
- Keep a visible stop action in the UI.
- Preserve dry-run as a first-class option.
- Do not hide per-button differences:
  - Button 1 uses date
  - Button 2 uses date and sample count
  - Button 3 does not use date or sample count
- Expect that hardware automation can fail because of window position, focus, or DPI changes.
- Prefer logs and screenshots over silent failure.

## Next Good Improvements

- Add a file picker for `launcher-path`.
- Add per-button help text in the UI.
- Show the latest generated log file path after each run.
- Add a read-only "environment checklist" panel:
  - DPI scaling
  - required windows open
  - monitor arrangement
  - failsafe guidance
