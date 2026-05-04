# Button 2 Sample Measurement Workflow

## Summary

`button2_sampleMeasurement.py` automates the Button 2 sample-measurement setup flow for the ASX-560 controller.

It now:

- starts `UVVisLauncher.exe` if `UV Launcher` is not already open
- clicks `Automatic Analysis` when the ASX controller is not open
- uses sample count `178` by default when `--sample-count` is omitted
- opens `C:\UVVis-Data\Parameter\20241101_YKJ_ASX_Test_Final.vasm`
- changes the result file name to `YYYYMMDD H1H2H3.vqud`
- switches `Sample Type` to `Sample`
- selects rack ranges and clicks `Add to Table` for rack `1` and rack `2`
- saves to `C:\UVVis-Data\Parameter\YYYY\MM\YYYYMMDD_YKJ_ASX_Test_Final_H1,2,3.vasm`
- reopens `Edit` after saving and moves the `Setting` window to rack `3`

## Commands

Dry run:

```powershell
python button2_sampleMeasurement.py --date 20260428 --dry-run
```

Normal run:

```powershell
python button2_sampleMeasurement.py --log-dir logs
```

Optional explicit launcher path:

```powershell
python button2_sampleMeasurement.py --launcher-path "C:\Path\To\UVVisLauncher.exe"
```

## Current rack plan

Default calibrated plan:

1. Rack `1`: drag from `7A` to `12E`, then `Add to Table`
2. Rack `2`: drag from `1A` to `12E`, then `Add to Table`
3. Rack `3`: after `Save As and Close`, reopen `Edit` and move to rack `3`

Special calibrated case:

1. Sample count `178`
2. Rack `1`: `7A -> 12E`
3. Rack `2`: `1A -> 12E`
4. Rack `3`: reopen `Edit` and move to rack `3` only

Counts other than the explicit `178` case follow the same rack segmentation in code.

## Output naming

- Result file name: `YYYYMMDD H1H2H3.vqud`
- Saved parameter file: `C:\UVVis-Data\Parameter\YYYY\MM\YYYYMMDD_YKJ_ASX_Test_Final_H1,2,3.vasm`
