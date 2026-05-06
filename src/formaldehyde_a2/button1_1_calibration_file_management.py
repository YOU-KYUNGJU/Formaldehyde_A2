#!/usr/bin/env python3
"""Calibration file management automation for the Quantitation window."""

import argparse
import time
import traceback
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from . import button1_calibration as common


QUANTITATION_WINDOW_TITLES = ("Quantitation - [Analysis]", "Quantitation")
QUANTITATION_REFERENCE_SIZE = (1297, 875)
QUANTITATION_TARGET_POSITION = (267, 42)
TOOLBAR_ROW_OFFSET = 20

# Window Spy references from the user's screenshots.
TOOLBAR_OPEN_BUTTON = (209, 38 + TOOLBAR_ROW_OFFSET)
TOOLBAR_SAVE_BUTTON = (277, 38 + TOOLBAR_ROW_OFFSET)
GRID_OPEN_BUTTON = (405, 150)
GRID_SAVE_AS_BUTTON = (496, 150)
UNKNOWN_ROW1_SELECTOR = (173, 513)


@dataclass
class CalibrationFileManagementPaths:
    date_text: str
    standard_vqud: str
    unknown_vqud: str
    dated_folder: str
    qc_vqcd: str


def build_paths(run_date):
    date_text = run_date.strftime("%Y%m%d")
    year_text = run_date.strftime("%Y")
    month_folder = f"{run_date.month}\uc6d4"
    base_data_dir = Path(r"C:\UVVis-Data\Data")
    dated_folder = base_data_dir / year_text / month_folder / date_text
    qc_file_name = f"{date_text} QC.vqcd"
    return CalibrationFileManagementPaths(
        date_text=date_text,
        standard_vqud=str(base_data_dir / f"Std_Test_{date_text}.vqud"),
        unknown_vqud=str(base_data_dir / f"Unk_Test_{date_text}.vqud"),
        dated_folder=str(dated_folder),
        qc_vqcd=str(dated_folder / qc_file_name),
    )


def wait_for_quantitation_window(timeout=20):
    return common.wait_for_window_any(QUANTITATION_WINDOW_TITLES, timeout=timeout, label="quantitation window")


def activate_quantitation_window(quantitation_hwnd):
    common.activate_window(
        quantitation_hwnd,
        target_size=QUANTITATION_REFERENCE_SIZE,
        target_position=QUANTITATION_TARGET_POSITION,
    )


def _press_hotkey(keys, dry_run=False, label="hotkey"):
    if dry_run:
        print(f"[dry-run] press {label}: {'+'.join(keys)}")
        return
    common.LOGGER.write(f"Press {label}: {'+'.join(keys)}")
    common.pyautogui.hotkey(*keys)
    time.sleep(0.5)


def click_quantitation_button(quantitation_hwnd, point, label, dry_run=False):
    activate_quantitation_window(quantitation_hwnd)
    common.click_reference(
        quantitation_hwnd,
        QUANTITATION_REFERENCE_SIZE,
        point,
        dry_run=dry_run,
        label=label,
    )


def trigger_toolbar_open_dialog(quantitation_hwnd, dry_run=False):
    activate_quantitation_window(quantitation_hwnd)
    _press_hotkey(("alt", "o"), dry_run=dry_run, label="curve Open")
    if dry_run:
        return
    try:
        common.wait_for_window_any(common.OPEN_DIALOG_TITLES, timeout=2, label="open dialog")
        return
    except TimeoutError:
        common.LOGGER.write("Open dialog not found after Alt+O. Retrying with toolbar Open click.")
        click_quantitation_button(quantitation_hwnd, TOOLBAR_OPEN_BUTTON, "Quantitation toolbar Open", dry_run=False)
        common.wait_for_window_any(common.OPEN_DIALOG_TITLES, timeout=10, label="open dialog")


def trigger_grid_save_as_dialog(quantitation_hwnd, dry_run=False):
    click_quantitation_button(quantitation_hwnd, GRID_SAVE_AS_BUTTON, "Quantitation grid Save As", dry_run=dry_run)
    if dry_run:
        return
    common.wait_for_window_any(common.SAVE_DIALOG_TITLES, timeout=10, label="save dialog")


def trigger_grid_open_dialog(quantitation_hwnd, dry_run=False):
    click_quantitation_button(quantitation_hwnd, GRID_OPEN_BUTTON, "Quantitation grid Open", dry_run=dry_run)
    if dry_run:
        return
    common.wait_for_window_any(common.OPEN_DIALOG_TITLES, timeout=10, label="open dialog")


def open_file_in_dialog(file_path, dry_run=False, label="file"):
    if dry_run:
        print(f"[dry-run] open {label}: {file_path}")
        return
    common.wait_for_window_any(common.OPEN_DIALOG_TITLES, timeout=15, label="open dialog")
    common.paste_text(file_path, label=label)
    common.pyautogui.press("enter")
    common.LOGGER.write("Pressed Enter in open dialog")
    time.sleep(1.0)


def save_file_in_dialog(file_path, dry_run=False, label="file"):
    target_dir = str(Path(file_path).parent)
    if dry_run:
        print(f"[dry-run] ensure directory: {target_dir}")
        print(f"[dry-run] save {label}: {file_path}")
        return
    Path(target_dir).mkdir(parents=True, exist_ok=True)
    common.wait_for_window_any(common.SAVE_DIALOG_TITLES, timeout=15, label="save dialog")
    common.paste_text(file_path, label=label)
    common.pyautogui.press("enter")
    common.LOGGER.write("Pressed Enter in save dialog")
    time.sleep(1.0)


def dismiss_optional_confirmation(timeout=4, dry_run=False):
    if dry_run:
        print("[dry-run] confirm optional message with Enter")
        return

    deadline = time.time() + timeout
    while time.time() < deadline:
        foreground = common.win32gui.GetForegroundWindow()
        if foreground:
            title = common.win32gui.GetWindowText(foreground)
            class_name = common.win32gui.GetClassName(foreground)
            if class_name == "#32770" and title not in common.OPEN_DIALOG_TITLES + common.SAVE_DIALOG_TITLES:
                common.LOGGER.write(f"Confirming dialog: title={title!r}, class={class_name!r}")
                common.pyautogui.press("enter")
                time.sleep(0.8)
                return True
        time.sleep(0.2)
    common.LOGGER.write("No confirmation dialog detected.")
    return False


def dismiss_optional_no_prompt(timeout=4, dry_run=False):
    if dry_run:
        print("[dry-run] dismiss optional prompt with Alt+N")
        return

    deadline = time.time() + timeout
    while time.time() < deadline:
        foreground = common.win32gui.GetForegroundWindow()
        if foreground:
            title = common.win32gui.GetWindowText(foreground)
            class_name = common.win32gui.GetClassName(foreground)
            if class_name == "#32770" and title not in common.OPEN_DIALOG_TITLES + common.SAVE_DIALOG_TITLES:
                common.LOGGER.write(f"Choosing No on dialog: title={title!r}, class={class_name!r}")
                common.pyautogui.hotkey("alt", "n")
                time.sleep(0.8)
                return True
        time.sleep(0.2)
    common.LOGGER.write("No Yes/No dialog detected.")
    return False


def replace_filename_with_qc_path(qc_path, dry_run=False):
    if dry_run:
        print(f"[dry-run] replace filename with: {qc_path}")
        return
    common.LOGGER.write(f"Replace Filename with QC path: {qc_path}")
    common.pyautogui.hotkey("ctrl", "a")
    time.sleep(0.1)
    common.pyautogui.press("backspace")
    time.sleep(0.1)
    common.paste_text(qc_path, label="qc filename override")
    common.pyautogui.press("enter")
    common.LOGGER.write("Pressed Enter after Filename override")
    time.sleep(0.8)


def delete_first_unknown_row(quantitation_hwnd, dry_run=False):
    activate_quantitation_window(quantitation_hwnd)
    if dry_run:
        print(f"[dry-run] right-click unknown row selector: {UNKNOWN_ROW1_SELECTOR} on {QUANTITATION_REFERENCE_SIZE}")
        print("[dry-run] press D to delete selected row")
        return
    common.click_reference(
        quantitation_hwnd,
        QUANTITATION_REFERENCE_SIZE,
        UNKNOWN_ROW1_SELECTOR,
        dry_run=False,
        label="Unknown row 1 selector",
    )
    time.sleep(0.3)
    x_pos, y_pos = common.scale_point(quantitation_hwnd, QUANTITATION_REFERENCE_SIZE, UNKNOWN_ROW1_SELECTOR)
    common.LOGGER.write(f"Right click Unknown row 1 selector: ({x_pos}, {y_pos})")
    common.pyautogui.click(x_pos, y_pos, button="right")
    time.sleep(0.4)
    common.LOGGER.write("Press D to delete selected row")
    common.pyautogui.press("d")
    time.sleep(0.8)


def save_quantitation(quantitation_hwnd, dry_run=False):
    click_quantitation_button(quantitation_hwnd, TOOLBAR_SAVE_BUTTON, "Quantitation toolbar Save", dry_run=dry_run)
    if dry_run:
        return
    time.sleep(1.0)


def run_calibration_file_management(paths, dry_run=False):
    common.LOGGER.write("Calibration file management values:")
    common.LOGGER.write(f"- date: {paths.date_text}")
    common.LOGGER.write(f"- standard: {paths.standard_vqud}")
    common.LOGGER.write(f"- unknown: {paths.unknown_vqud}")
    common.LOGGER.write(f"- folder: {paths.dated_folder}")
    common.LOGGER.write(f"- qc: {paths.qc_vqcd}")

    if dry_run:
        print("[dry-run] reference coordinates:")
        print(f"- Quantitation toolbar Open: {TOOLBAR_OPEN_BUTTON} on {QUANTITATION_REFERENCE_SIZE}")
        print(f"- Quantitation toolbar Save: {TOOLBAR_SAVE_BUTTON} on {QUANTITATION_REFERENCE_SIZE}")
        print(f"- Quantitation grid Open: {GRID_OPEN_BUTTON} on {QUANTITATION_REFERENCE_SIZE}")
        print(f"- Quantitation grid Save As: {GRID_SAVE_AS_BUTTON} on {QUANTITATION_REFERENCE_SIZE}")
        print(f"- Unknown row 1 selector: {UNKNOWN_ROW1_SELECTOR} on {QUANTITATION_REFERENCE_SIZE}")
        print("Done.")
        return

    common.load_gui_dependencies()
    common.LOGGER.dump_windows("before calibration file management")

    quantitation_hwnd = wait_for_quantitation_window(timeout=20)

    trigger_toolbar_open_dialog(quantitation_hwnd, dry_run=False)
    open_file_in_dialog(paths.standard_vqud, dry_run=False, label="standard vqud")
    time.sleep(2.0)

    quantitation_hwnd = wait_for_quantitation_window(timeout=20)
    trigger_grid_save_as_dialog(quantitation_hwnd, dry_run=False)
    save_file_in_dialog(paths.qc_vqcd, dry_run=False, label="qc vqcd")

    quantitation_hwnd = wait_for_quantitation_window(timeout=20)
    trigger_toolbar_open_dialog(quantitation_hwnd, dry_run=False)
    open_file_in_dialog(paths.unknown_vqud, dry_run=False, label="unknown vqud")
    dismiss_optional_confirmation(timeout=4, dry_run=False)

    quantitation_hwnd = wait_for_quantitation_window(timeout=20)
    trigger_grid_open_dialog(quantitation_hwnd, dry_run=False)
    open_file_in_dialog(paths.qc_vqcd, dry_run=False, label="saved qc vqcd")
    dismiss_optional_no_prompt(timeout=4, dry_run=False)
    replace_filename_with_qc_path(paths.qc_vqcd, dry_run=False)
    quantitation_hwnd = wait_for_quantitation_window(timeout=20)
    delete_first_unknown_row(quantitation_hwnd, dry_run=False)
    quantitation_hwnd = wait_for_quantitation_window(timeout=20)
    save_quantitation(quantitation_hwnd, dry_run=False)
    common.show_completion_popup(
        "Button 1-1 Complete",
        "QC saving is complete.",
        dry_run=dry_run,
    )

    print("Done.")


def parse_args():
    parser = argparse.ArgumentParser(description="Run calibration file management automation.")
    parser.add_argument(
        "--date",
        help="Run date in YYYYMMDD format. Default: today.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print generated values and actions without clicking.",
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


def parse_run_date(date_text):
    if not date_text:
        return datetime.now()
    return datetime.strptime(date_text, "%Y%m%d")


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


def build_fallback_log_path(log_dir, file_prefix="button1_1_calibration_file_management"):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    Path(log_dir).mkdir(parents=True, exist_ok=True)
    return Path(log_dir) / f"{file_prefix}_{timestamp}_startup_error.log"


def write_startup_error_log(log_dir, message, file_prefix="button1_1_calibration_file_management"):
    log_path = build_fallback_log_path(log_dir, file_prefix=file_prefix)
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with log_path.open("a", encoding="utf-8") as log_file:
        log_file.write(f"[{timestamp}] {message}\n")
    print(f"[{timestamp}] Startup error log: {log_path}")
    print(f"[{timestamp}] {message}")
    return log_path


def main():
    common.set_dpi_awareness()
    args = parse_args()
    try:
        common.LOGGER = create_compatible_logger(
            enabled=not args.no_log,
            log_dir=args.log_dir,
            file_prefix="button1_1_calibration_file_management",
        )
        if common.LOGGER.log_path:
            common.LOGGER.write(f"Log file: {common.LOGGER.log_path}")

        if not args.dry_run:
            common.load_gui_dependencies()
            common.pyautogui.PAUSE = 0.15
            common.pyautogui.FAILSAFE = True

        run_date = parse_run_date(args.date)
        paths = build_paths(run_date)
        run_calibration_file_management(paths, dry_run=args.dry_run)
    except Exception:
        error_text = traceback.format_exc()
        logger = getattr(common, "LOGGER", None)
        if logger and getattr(logger, "write", None):
            logger.write("Unhandled error during calibration file management automation:")
            for line in error_text.rstrip().splitlines():
                logger.write(line)
        elif not args.no_log:
            write_startup_error_log(
                args.log_dir,
                "Unhandled error during calibration file management automation:\n" + error_text.rstrip(),
            )
        raise


if __name__ == "__main__":
    main()
