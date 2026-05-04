#!/usr/bin/env python3
"""
Button 2 sample measurement automation for ASX-560 Controller.

This script reuses the shared coordinate-based helpers from button1_calibration.py.
"""
import argparse
import math
import os
import time
import traceback
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from . import button1_calibration as common


RACK_SETTING_REFERENCE_SIZE = common.SETTING_REFERENCE_SIZE
ASX_REFERENCE_SIZE = common.ASX_REFERENCE_SIZE

SAMPLE_RADIO = (530, 150)
RACK_NO_RIGHT_ARROW = (1170, 116)
ADD_TO_TABLE_BUTTON = (670, 402)
PLATE_ORIGIN = (897, 108)
PLATE_STEP_X = 31
PLATE_STEP_Y = 23
DRAG_START_OFFSET = (-8, -8)
DRAG_END_OFFSET = (16, 12)
WELL_POINT_OVERRIDES = {
    "7A": (897, 269),
    "10E": (1005, 355),
    "12E": (1005, 405),
}

ROW_LABELS = tuple(range(1, 13))
COLUMN_LABELS = ("A", "B", "C", "D", "E")
DEFAULT_SOURCE_VASM = r"C:\UVVis-Data\Parameter\20241101_YKJ_ASX_Test_Final.vasm"
DEFAULT_SAMPLE_COUNT = 178


@dataclass
class MeasurementPaths:
    date_text: str
    result_file_name: str
    source_vasm: str
    target_vasm: str


@dataclass
class RackSelection:
    rack_number: int
    start_well: str
    end_well: str


SPECIAL_SELECTIONS = {
    178: [
        RackSelection(1, "7A", "12E"),
        RackSelection(2, "1A", "12E"),
        RackSelection(3, "1A", "10E"),
    ],
}


def build_paths(run_date, source_vasm):
    date_text = run_date.strftime("%Y%m%d")
    year_text = run_date.strftime("%Y")
    month_text = run_date.strftime("%m")
    result_file_name = f"{date_text} H1H2H3.vqud"
    target_vasm = rf"C:\UVVis-Data\Parameter\{year_text}\{month_text}\{date_text}_YKJ_ASX_Test_Final_H1,2,3.vasm"
    return MeasurementPaths(
        date_text=date_text,
        result_file_name=result_file_name,
        source_vasm=source_vasm,
        target_vasm=target_vasm,
    )


def parse_well_label(well_label):
    row_text = well_label[:-1]
    column_text = well_label[-1].upper()
    row_number = int(row_text)
    column_index = COLUMN_LABELS.index(column_text)
    return row_number, column_index


def build_well_sequence(start_well, end_well):
    start_row, start_column = parse_well_label(start_well)
    end_row, end_column = parse_well_label(end_well)
    wells = []
    for row_number in ROW_LABELS:
        for column_index, column_name in enumerate(COLUMN_LABELS):
            if row_number < start_row or row_number > end_row:
                continue
            if row_number == start_row and column_index < start_column:
                continue
            if row_number == end_row and column_index > end_column:
                continue
            wells.append(f"{row_number}{column_name}")
    return wells


def calculate_end_well(start_well, segment_count, virtual_capacity):
    wells = build_well_sequence(start_well, "12E")
    if virtual_capacity > len(wells):
        ratio = virtual_capacity / len(wells)
        target_index = max(0, min(len(wells) - 1, math.ceil(segment_count / ratio) - 1))
    else:
        target_index = max(0, min(len(wells) - 1, segment_count - 1))
    return wells[target_index]


def build_selection_plan(sample_count):
    if sample_count in SPECIAL_SELECTIONS:
        return SPECIAL_SELECTIONS[sample_count]

    plan = []
    remaining = sample_count
    segments = [
        (1, "7A", 60),
        (2, "1A", 60),
        (3, "1A", 60),
        (4, "1A", 60),
    ]
    for rack_number, start_well, capacity in segments:
        if remaining <= 0:
            break
        segment_count = min(remaining, capacity)
        end_well = "12E" if segment_count == capacity else calculate_end_well(start_well, segment_count, capacity)
        plan.append(RackSelection(rack_number, start_well, end_well))
        remaining -= segment_count
    if remaining > 0:
        raise ValueError("Sample count exceeds configured rack capacity.")
    return plan

def drag_reference(hwnd, reference_size, start_point, end_point, duration=0.3, dry_run=False, label="drag"):
    start_x, start_y = common.scale_point(hwnd, reference_size, start_point)
    end_x, end_y = common.scale_point(hwnd, reference_size, end_point)
    if dry_run:
        print(f"[dry-run] drag {label}: ({start_x}, {start_y}) -> ({end_x}, {end_y})")
        return
    common.LOGGER.write(f"Drag {label}: ({start_x}, {start_y}) -> ({end_x}, {end_y})")
    common.pyautogui.moveTo(start_x, start_y)
    time.sleep(0.1)
    common.pyautogui.mouseDown()
    time.sleep(0.1)
    common.pyautogui.moveTo(end_x, end_y, duration=duration)
    time.sleep(0.1)
    common.pyautogui.mouseUp()
    time.sleep(0.4)


def well_to_reference_point(well_label, offset=(0, 0), apply_offset_to_override=False):
    if well_label in WELL_POINT_OVERRIDES:
        base_x, base_y = WELL_POINT_OVERRIDES[well_label]
        if apply_offset_to_override:
            return base_x + offset[0], base_y + offset[1]
        return base_x, base_y
    row_number, column_index = parse_well_label(well_label)
    return (
        PLATE_ORIGIN[0] + column_index * PLATE_STEP_X + offset[0],
        PLATE_ORIGIN[1] + (row_number - 1) * PLATE_STEP_Y + offset[1],
    )


def set_rack_number(setting_hwnd, current_rack, target_rack, dry_run=False):
    if target_rack < current_rack:
        raise ValueError("Rack number can only move to the right with the current automation flow.")
    for step_index in range(target_rack - current_rack):
        common.click_reference(
            setting_hwnd,
            RACK_SETTING_REFERENCE_SIZE,
            RACK_NO_RIGHT_ARROW,
            dry_run,
            f"Rack No. right arrow step {step_index + 1}",
        )
        common.LOGGER.screenshot(f"after_rack_arrow_{current_rack + step_index + 1}")
        time.sleep(0.5)
    return target_rack


def select_rack_range(setting_hwnd, selection, current_rack, dry_run=False):
    current_rack = set_rack_number(
        setting_hwnd,
        current_rack=current_rack,
        target_rack=selection.rack_number,
        dry_run=dry_run,
    )
    start_point = well_to_reference_point(selection.start_well, offset=DRAG_START_OFFSET)
    end_point = well_to_reference_point(selection.end_well, offset=DRAG_END_OFFSET, apply_offset_to_override=False)
    drag_reference(
        setting_hwnd,
        RACK_SETTING_REFERENCE_SIZE,
        start_point,
        end_point,
        dry_run=dry_run,
        label=f"Rack {selection.rack_number} {selection.start_well}->{selection.end_well}",
    )
    common.LOGGER.screenshot(f"after_rack_{selection.rack_number}_drag")
    time.sleep(0.6)
    common.click_reference(
        setting_hwnd,
        RACK_SETTING_REFERENCE_SIZE,
        ADD_TO_TABLE_BUTTON,
        dry_run,
        f"Add to Table rack {selection.rack_number}",
    )
    return current_rack


def save_measurement_vasm(paths, dry_run=False):
    target_dir = os.path.dirname(paths.target_vasm)
    if dry_run:
        print(f"[dry-run] ensure directory: {target_dir}")
        print(f"[dry-run] save target vasm: {paths.target_vasm}")
        return

    os.makedirs(target_dir, exist_ok=True)
    common.wait_for_window_any(common.SAVE_DIALOG_TITLES, timeout=15, label="save dialog")
    common.paste_text(paths.target_vasm, label="target vasm")
    common.pyautogui.press("enter")
    common.LOGGER.write("Pressed Enter in save dialog")
    time.sleep(0.8)


def reopen_setting_and_move_to_rack(asx_hwnd, target_rack, dry_run=False):
    setting_hwnd = common.open_setting_window_from_edit_with_retry(asx_hwnd, dry_run, "ASX Edit reopen")
    common.activate_window(setting_hwnd, target_size=common.SETTING_TARGET_SIZE, target_position=(30, 30))
    common.click_reference(
        setting_hwnd,
        RACK_SETTING_REFERENCE_SIZE,
        SAMPLE_RADIO,
        dry_run,
        "Sample Type Sample reopen",
    )
    common.LOGGER.screenshot("reopened_after_sample_type_click")
    current_rack = 1
    current_rack = set_rack_number(
        setting_hwnd,
        current_rack=current_rack,
        target_rack=target_rack,
        dry_run=dry_run,
    )
    common.LOGGER.screenshot(f"reopened_setting_rack_{current_rack}")
    return setting_hwnd


def run_button2_sample_measurement(paths, sample_count, dry_run=False, launcher_path=None):
    plan = build_selection_plan(sample_count)
    common.LOGGER.write("Sample measurement automation values:")
    common.LOGGER.write(f"- date: {paths.date_text}")
    common.LOGGER.write(f"- sample_count: {sample_count}")
    common.LOGGER.write(f"- result file name: {paths.result_file_name}")
    common.LOGGER.write(f"- source: {paths.source_vasm}")
    common.LOGGER.write(f"- target: {paths.target_vasm}")
    for selection in plan:
        common.LOGGER.write(
            f"- rack {selection.rack_number}: {selection.start_well} -> {selection.end_well}"
        )

    if dry_run:
        print("[dry-run] reference coordinates:")
        print(f"- Sample radio: {SAMPLE_RADIO} on {RACK_SETTING_REFERENCE_SIZE}")
        print(f"- Rack No. right arrow: {RACK_NO_RIGHT_ARROW} on {RACK_SETTING_REFERENCE_SIZE}")
        print(f"- Add to Table: {ADD_TO_TABLE_BUTTON} on {RACK_SETTING_REFERENCE_SIZE}")
        print(f"- Plate origin (1A): {PLATE_ORIGIN}")
        print(f"- Well overrides: {WELL_POINT_OVERRIDES}")
        print("Done.")
        return

    common.load_gui_dependencies()
    common.LOGGER.dump_windows("before button2 automation")

    if not common.wait_for_window_optional(common.LAUNCHER_TITLE, timeout=1):
        common.launch_uvvis_launcher(launcher_path=launcher_path, dry_run=dry_run)

    asx_hwnd = common.ensure_asx_controller_open(dry_run=dry_run, launcher_path=launcher_path)
    common.activate_window(asx_hwnd, target_size=common.ASX_TARGET_SIZE)
    common.click_reference(asx_hwnd, ASX_REFERENCE_SIZE, common.READ_BUTTON, dry_run, "ASX Read")
    common.LOGGER.screenshot("after_read_click")
    common.open_vasm_from_read_dialog_with_retry(asx_hwnd, paths, dry_run)

    asx_hwnd = common.wait_for_window(common.ASX_TITLE, timeout=20)
    setting_hwnd = common.open_setting_window_from_edit_with_retry(asx_hwnd, dry_run, "ASX Edit")
    common.activate_window(setting_hwnd, target_size=common.SETTING_TARGET_SIZE, target_position=(30, 30))

    common.click_reference(
        setting_hwnd,
        RACK_SETTING_REFERENCE_SIZE,
        common.ANALYSIS1_TAB,
        dry_run,
        "Analysis1 tab",
    )
    common.click_reference(
        setting_hwnd,
        RACK_SETTING_REFERENCE_SIZE,
        common.FILE_NAME_INPUT,
        dry_run,
        "Analysis1 File Name",
    )
    common.replace_field_text(paths.result_file_name, dry_run, "sample file name")
    common.LOGGER.screenshot("before_sample_type_click")
    common.click_reference(
        setting_hwnd,
        RACK_SETTING_REFERENCE_SIZE,
        SAMPLE_RADIO,
        dry_run,
        "Sample Type Sample",
    )
    common.LOGGER.screenshot("after_sample_type_click")

    reopening_target_rack = None
    current_rack = 1
    for selection in plan:
        if selection.rack_number >= 3:
            reopening_target_rack = selection.rack_number
            common.LOGGER.write(
                f"- deferred rack {selection.rack_number}: reopen Setting after save and move only"
            )
            continue
        current_rack = select_rack_range(
            setting_hwnd,
            selection=selection,
            current_rack=current_rack,
            dry_run=dry_run,
        )
        common.LOGGER.screenshot(f"after_rack_{selection.rack_number}_add")

    common.click_reference(
        setting_hwnd,
        RACK_SETTING_REFERENCE_SIZE,
        common.SAVE_AS_AND_CLOSE,
        dry_run,
        "Save As and Close",
    )
    save_measurement_vasm(paths, dry_run)

    if reopening_target_rack is not None:
        reopen_setting_and_move_to_rack(
            asx_hwnd,
            target_rack=reopening_target_rack,
            dry_run=dry_run,
        )

    print("Done.")


def parse_args():
    parser = argparse.ArgumentParser(description="Run button 2 sample measurement automation.")
    parser.add_argument(
        "--date",
        help="Run date in YYYYMMDD format. Default: today.",
    )
    parser.add_argument(
        "--sample-count",
        type=int,
        help=f"Measurement sample count. Default: {DEFAULT_SAMPLE_COUNT}.",
    )
    parser.add_argument(
        "--source-vasm",
        default=DEFAULT_SOURCE_VASM,
        help="Existing .vasm file to open from the Read dialog.",
    )
    parser.add_argument(
        "--launcher-path",
        help="Explicit path to UVVisLauncher.exe. Falls back to UVVIS_LAUNCHER_PATH or common install locations.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print generated values and coordinates without clicking.",
    )
    parser.add_argument(
        "--log-dir",
        default="logs",
        help="Directory for step logs and screenshots. Default: logs.",
    )
    parser.add_argument(
        "--no-log",
        action="store_true",
        help="Disable file logging.",
    )
    return parser.parse_args()


def build_fallback_log_path(log_dir, file_prefix="button2_sample_measurement"):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    Path(log_dir).mkdir(parents=True, exist_ok=True)
    return Path(log_dir) / f"{file_prefix}_{timestamp}_startup_error.log"


def write_startup_error_log(log_dir, message, file_prefix="button2_sample_measurement"):
    log_path = build_fallback_log_path(log_dir, file_prefix=file_prefix)
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with log_path.open("a", encoding="utf-8") as log_file:
        log_file.write(f"[{timestamp}] {message}\n")
    print(f"[{timestamp}] Startup error log: {log_path}")
    print(f"[{timestamp}] {message}")
    return log_path


def create_compatible_logger(enabled, log_dir, file_prefix):
    try:
        return common.AutomationLogger(
            enabled=enabled,
            log_dir=log_dir,
            file_prefix=file_prefix,
        )
    except TypeError as exc:
        if "file_prefix" not in str(exc):
            raise
        logger = common.AutomationLogger(enabled=enabled, log_dir=log_dir)
        if enabled and getattr(logger, "log_path", None):
            desired_log_path = logger.log_path.with_name(
                logger.log_path.name.replace("button1_calibration", file_prefix, 1)
            )
            logger.log_path = desired_log_path
        return logger


def main():
    common.set_dpi_awareness()
    args = parse_args()
    try:
        common.LOGGER = create_compatible_logger(
            enabled=not args.no_log,
            log_dir=args.log_dir,
            file_prefix="button2_sample_measurement",
        )
        if common.LOGGER.log_path:
            common.LOGGER.write(f"Log file: {common.LOGGER.log_path}")

        run_date = datetime.strptime(args.date, "%Y%m%d") if args.date else datetime.today()
        paths = build_paths(run_date, args.source_vasm)
        sample_count = args.sample_count if args.sample_count is not None else DEFAULT_SAMPLE_COUNT
        if not 1 <= sample_count <= 240:
            raise SystemExit("--sample-count must be between 1 and 240.")

        if not args.dry_run:
            common.load_gui_dependencies()
            common.pyautogui.PAUSE = 0.15
            common.pyautogui.FAILSAFE = True

        run_button2_sample_measurement(
            paths,
            sample_count=sample_count,
            dry_run=args.dry_run,
            launcher_path=args.launcher_path,
        )
    except Exception:
        error_text = traceback.format_exc()
        logger = getattr(common, "LOGGER", None)
        if logger and getattr(logger, "write", None):
            logger.write("Unhandled error during button2 sample measurement automation:")
            for line in error_text.rstrip().splitlines():
                logger.write(line)
        elif not args.no_log:
            write_startup_error_log(
                args.log_dir,
                "Unhandled error during button2 sample measurement automation:\n" + error_text.rstrip(),
            )
        raise


if __name__ == "__main__":
    main()
