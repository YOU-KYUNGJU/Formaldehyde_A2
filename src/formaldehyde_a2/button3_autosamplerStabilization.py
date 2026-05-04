#!/usr/bin/env python3
"""
Button 3 autosampler stabilization automation for ASX-560 Controller.

This script reuses the shared launcher/ASX helpers from button1_calibration.py
and automates the stabilization flow between the ASX controller and the
Instrument Control window.
"""
import argparse
import time
import traceback
from datetime import datetime
from pathlib import Path
from tkinter import messagebox

from . import button1_calibration as common


ASX_REFERENCE_SIZE = common.ASX_REFERENCE_SIZE
INSTRUMENT_REFERENCE_SIZE = (341, 752)
QUANTITATION_REFERENCE_SIZE = (1297, 875)
QUANTITATION_TITLE = "Quantitation - [Analysis]"
INSTRUMENT_PROCESS_NAME = "UVNavi.exe"
INSTRUMENT_CLASS_NAME = "#32770"

S1_BUTTON = (99, 260)
S2_BUTTON = (128, 260)
MOVE_BUTTON = (89, 138)
UP_DOWN_BUTTON = (202, 142)
SIP_BUTTON = (58, 471)
AUTO_ZERO_BUTTON = (69, 644)
INST_CONTROL_BUTTON = (953, 83)
MANUAL_MODE_BUTTON = (680, 22)
ANALYSIS_MODE_RIGHT_SAMPLE = (680, 22)
ANALYSIS_MODE_LEFT_SAMPLE = (596, 32)

ASX_TARGET_POSITION = (20, 20)
QUANTITATION_TARGET_POSITION = (581, 70)
INSTRUMENT_TARGET_POSITION = (853, 201)
MOVE_SETTLE_SECONDS = 5
INST_CONTROL_OPEN_SECONDS = 5
SIP_WAIT_SECONDS = 40


class StatusTooltip:
    def __init__(self, dry_run=False):
        self.dry_run = dry_run
        self.root = None
        self.label = None
        if dry_run:
            return

        import tkinter as tk

        self.root = tk.Tk()
        self.root.withdraw()
        self.root.overrideredirect(True)
        self.root.attributes("-topmost", True)
        self.label = tk.Label(
            self.root,
            text="",
            bg="#1f2937",
            fg="white",
            padx=10,
            pady=6,
            font=("Malgun Gothic", 10),
        )
        self.label.pack()

    def update(self, message):
        common.LOGGER.write(f"Status: {message}")
        if self.dry_run:
            print(f"[dry-run] status: {message}")
            return
        x_pos, y_pos = common.pyautogui.position()
        self.label.configure(text=message)
        self.root.geometry(f"+{x_pos + 18}+{y_pos + 18}")
        self.root.deiconify()
        self.root.update()

    def close(self):
        if self.root:
            self.root.destroy()


def check_abort():
    try:
        import win32api

        if win32api.GetAsyncKeyState(0x1B) & 0x8000:
            raise KeyboardInterrupt("Button 3 automation aborted by Esc.")
    except ImportError:
        return


def wait_with_status(seconds, status, tooltip, dry_run=False):
    if dry_run:
        print(f"[dry-run] wait {seconds:.1f}s: {status}")
        return

    end_time = time.time() + seconds
    while time.time() < end_time:
        check_abort()
        remaining = max(0, int(round(end_time - time.time())))
        tooltip.update(f"{status} ({remaining}s)")
        time.sleep(min(1.0, max(0.1, end_time - time.time())))


def find_window_by_process_and_class(process_name=None, class_name=None):
    matched_hwnd = None
    import win32process

    def enum_callback(hwnd, _lparam):
        nonlocal matched_hwnd
        if matched_hwnd or not common.win32gui.IsWindowVisible(hwnd):
            return
        if class_name and common.win32gui.GetClassName(hwnd) != class_name:
            return
        if process_name:
            _, pid = win32process.GetWindowThreadProcessId(hwnd)
            try:
                process = common.psutil.Process(pid)
                current_name = process.name()
            except Exception:
                return
            if current_name.lower() != process_name.lower():
                return
        matched_hwnd = hwnd

    common.win32gui.EnumWindows(enum_callback, None)
    return matched_hwnd


def wait_for_window_by_process_and_class(process_name, class_name, timeout=15, label="window"):
    deadline = time.time() + timeout
    while time.time() < deadline:
        hwnd = find_window_by_process_and_class(process_name=process_name, class_name=class_name)
        if hwnd:
            common.LOGGER.write(f"Found {label}: hwnd={hwnd}")
            return hwnd
        time.sleep(0.3)
    common.LOGGER.dump_windows(f"timeout waiting for {label}")
    common.LOGGER.screenshot(f"timeout_{label}")
    raise TimeoutError(f"Window not found: {label}")


def ensure_quantitation_window():
    quantitation_hwnd = common.wait_for_window_optional(QUANTITATION_TITLE, timeout=3)
    if quantitation_hwnd:
        return quantitation_hwnd
    return common.wait_for_window("Quantitation", timeout=10)


def ensure_instrument_control_open(tooltip, dry_run=False):
    if not dry_run:
        instrument_hwnd = find_window_by_process_and_class(
            process_name=INSTRUMENT_PROCESS_NAME,
            class_name=INSTRUMENT_CLASS_NAME,
        )
        if instrument_hwnd:
            return instrument_hwnd

    tooltip.update("Open Instrument Control")
    if dry_run:
        print(f"[dry-run] click Inst. Control: {INST_CONTROL_BUTTON} on {QUANTITATION_REFERENCE_SIZE}")
        print(f"[dry-run] wait {INST_CONTROL_OPEN_SECONDS:.1f}s after Inst. Control")
        return None

    quantitation_hwnd = ensure_quantitation_window()
    common.activate_window(
        quantitation_hwnd,
        target_size=QUANTITATION_REFERENCE_SIZE,
        target_position=QUANTITATION_TARGET_POSITION,
    )
    common.click_reference(
        quantitation_hwnd,
        QUANTITATION_REFERENCE_SIZE,
        INST_CONTROL_BUTTON,
        dry_run=False,
        label="Inst. Control",
    )
    common.LOGGER.screenshot("after_inst_control_click")
    wait_with_status(INST_CONTROL_OPEN_SECONDS, "Wait for Instrument Control", tooltip, dry_run=False)
    return wait_for_window_by_process_and_class(
        INSTRUMENT_PROCESS_NAME,
        INSTRUMENT_CLASS_NAME,
        timeout=15,
        label="Instrument Control",
    )


def click_asx(asx_hwnd, point, label, tooltip, dry_run=False):
    tooltip.update(label)
    if dry_run:
        print(f"[dry-run] click {label}: {point} on {ASX_REFERENCE_SIZE}")
        return
    common.click_reference(asx_hwnd, ASX_REFERENCE_SIZE, point, dry_run=False, label=label)
    common.LOGGER.screenshot(label)


def click_instrument(instrument_hwnd, point, label, tooltip, dry_run=False):
    tooltip.update(label)
    if dry_run:
        print(f"[dry-run] click {label}: {point} on {INSTRUMENT_REFERENCE_SIZE}")
        return
    common.click_reference(
        instrument_hwnd,
        INSTRUMENT_REFERENCE_SIZE,
        point,
        dry_run=False,
        label=label,
    )
    common.LOGGER.screenshot(label)


def is_blue_dominant(rgb):
    red, green, blue = rgb
    return blue > 120 and blue > red + 25 and blue > green + 10


def is_gray_like(rgb):
    red, green, blue = rgb
    spread = max(red, green, blue) - min(red, green, blue)
    brightness = (red + green + blue) / 3
    return spread < 35 and brightness > 120


def is_analysis_mode(asx_hwnd):
    right_x, right_y = common.scale_point(asx_hwnd, ASX_REFERENCE_SIZE, ANALYSIS_MODE_RIGHT_SAMPLE)
    left_x, left_y = common.scale_point(asx_hwnd, ASX_REFERENCE_SIZE, ANALYSIS_MODE_LEFT_SAMPLE)
    right_pixel = common.pyautogui.pixel(right_x, right_y)
    left_pixel = common.pyautogui.pixel(left_x, left_y)

    common.LOGGER.write(f"Mode sample right pixel: {right_pixel}")
    common.LOGGER.write(f"Mode sample left pixel: {left_pixel}")

    return is_blue_dominant(right_pixel) and is_gray_like(left_pixel)


def ensure_manual_mode(asx_hwnd, tooltip, dry_run=False):
    tooltip.update("Check MANUAL mode")
    if dry_run:
        print(f"[dry-run] MANUAL button: {MANUAL_MODE_BUTTON} on {ASX_REFERENCE_SIZE}")
        return

    common.activate_window(asx_hwnd, target_size=common.ASX_TARGET_SIZE, target_position=ASX_TARGET_POSITION)
    if not is_analysis_mode(asx_hwnd):
        common.LOGGER.write("ASX controller already appears to be in manual mode.")
        return

    common.LOGGER.write("ASX controller appears to be in analysis mode. Prompting for MANUAL mode change.")
    tooltip.update("Analysis Mode detected")
    messagebox.showwarning(
        "Button 3 Notice",
        "Analysis Mode is detected.\nSwitching to Manual Mode.",
    )
    common.LOGGER.write("Switching ASX controller to manual mode.")
    common.click_reference(
        asx_hwnd,
        ASX_REFERENCE_SIZE,
        MANUAL_MODE_BUTTON,
        dry_run=False,
        label="ASX MANUAL",
    )
    common.LOGGER.screenshot("after_manual_mode_click")
    time.sleep(1.0)


def run_asx_lowering_sequence(asx_hwnd, position_label, position_point, tooltip, dry_run=False):
    if not dry_run:
        common.activate_window(asx_hwnd, target_size=common.ASX_TARGET_SIZE, target_position=ASX_TARGET_POSITION)
    click_asx(asx_hwnd, position_point, f"Select {position_label}", tooltip, dry_run)
    click_asx(asx_hwnd, MOVE_BUTTON, f"{position_label} Move", tooltip, dry_run)
    wait_with_status(MOVE_SETTLE_SECONDS, "Wait after Move", tooltip, dry_run)
    click_asx(asx_hwnd, UP_DOWN_BUTTON, f"{position_label} Up/Down", tooltip, dry_run)


def run_instrument_cycle(instrument_hwnd, tooltip, include_second_auto_zero, dry_run=False):
    if not dry_run:
        common.activate_window(
            instrument_hwnd,
            target_size=INSTRUMENT_REFERENCE_SIZE,
            target_position=INSTRUMENT_TARGET_POSITION,
        )
    click_instrument(instrument_hwnd, SIP_BUTTON, "Instrument Control Sip", tooltip, dry_run)
    wait_with_status(SIP_WAIT_SECONDS, "Wait after Sip", tooltip, dry_run)
    click_instrument(instrument_hwnd, AUTO_ZERO_BUTTON, "Instrument Control Auto Zero", tooltip, dry_run)
    click_instrument(instrument_hwnd, SIP_BUTTON, "Instrument Control Sip", tooltip, dry_run)
    if include_second_auto_zero:
        wait_with_status(SIP_WAIT_SECONDS, "Wait after Sip", tooltip, dry_run)
        click_instrument(instrument_hwnd, AUTO_ZERO_BUTTON, "Instrument Control Auto Zero", tooltip, dry_run)


def show_completion_prompt(dry_run=False):
    message = "Please confirm that the absorbance is stabilized."
    if dry_run:
        print(f"[dry-run] completion prompt: {message}")
        return
    messagebox.showinfo("Button 3 Complete", message)


def run_button3_autosampler_stabilization(dry_run=False, launcher_path=None):
    common.LOGGER.write("Autosampler stabilization automation started.")

    if dry_run:
        print("[dry-run] autosampler stabilization")
        print(f"- ASX S2: {S2_BUTTON} on {ASX_REFERENCE_SIZE}")
        print(f"- ASX S1: {S1_BUTTON} on {ASX_REFERENCE_SIZE}")
        print(f"- ASX Move: {MOVE_BUTTON} on {ASX_REFERENCE_SIZE}")
        print(f"- ASX Up/Down: {UP_DOWN_BUTTON} on {ASX_REFERENCE_SIZE}")
        print(f"- ASX Manual: {MANUAL_MODE_BUTTON} on {ASX_REFERENCE_SIZE}")
        print(f"- Quantitation Inst. Control: {INST_CONTROL_BUTTON} on {QUANTITATION_REFERENCE_SIZE}")
        print(f"- Instrument Sip: {SIP_BUTTON} on {INSTRUMENT_REFERENCE_SIZE}")
        print(f"- Instrument Auto Zero: {AUTO_ZERO_BUTTON} on {INSTRUMENT_REFERENCE_SIZE}")

    if not dry_run:
        common.load_gui_dependencies()
        common.load_process_dependencies()
        common.LOGGER.dump_windows("before button3 automation")

    tooltip = StatusTooltip(dry_run=dry_run)
    try:
        tooltip.update("Start Button 3")
        asx_hwnd = None if dry_run else common.ensure_asx_controller_open(dry_run=False, launcher_path=launcher_path)
        ensure_manual_mode(asx_hwnd, tooltip, dry_run=dry_run)
        instrument_hwnd = ensure_instrument_control_open(tooltip, dry_run=dry_run)
        run_asx_lowering_sequence(asx_hwnd, "S2", S2_BUTTON, tooltip, dry_run=dry_run)
        run_instrument_cycle(instrument_hwnd, tooltip, include_second_auto_zero=True, dry_run=dry_run)
        run_asx_lowering_sequence(asx_hwnd, "S1", S1_BUTTON, tooltip, dry_run=dry_run)
        run_instrument_cycle(instrument_hwnd, tooltip, include_second_auto_zero=False, dry_run=dry_run)
        tooltip.update("Request absorbance check")
        show_completion_prompt(dry_run=dry_run)
        tooltip.update("Button 3 complete")
        print("Done.")
    finally:
        tooltip.close()


def parse_args():
    parser = argparse.ArgumentParser(description="Run button 3 autosampler stabilization automation.")
    parser.add_argument(
        "--launcher-path",
        help="Explicit path to UVVisLauncher.exe. Falls back to UVVIS_LAUNCHER_PATH or common install locations.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print configured autosampler stabilization steps without clicking.",
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


def build_fallback_log_path(log_dir, file_prefix="button3_autosampler_stabilization"):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    Path(log_dir).mkdir(parents=True, exist_ok=True)
    return Path(log_dir) / f"{file_prefix}_{timestamp}_startup_error.log"


def write_startup_error_log(log_dir, message, file_prefix="button3_autosampler_stabilization"):
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
            file_prefix="button3_autosampler_stabilization",
        )
        if common.LOGGER.log_path:
            common.LOGGER.write(f"Log file: {common.LOGGER.log_path}")

        if not args.dry_run:
            common.load_gui_dependencies()
            common.pyautogui.PAUSE = 0.15
            common.pyautogui.FAILSAFE = True

        run_button3_autosampler_stabilization(
            dry_run=args.dry_run,
            launcher_path=args.launcher_path,
        )
    except Exception:
        error_text = traceback.format_exc()
        logger = getattr(common, "LOGGER", None)
        if logger and getattr(logger, "write", None):
            logger.write("Unhandled error during button3 autosampler stabilization automation:")
            for line in error_text.rstrip().splitlines():
                logger.write(line)
        elif not args.no_log:
            write_startup_error_log(
                args.log_dir,
                "Unhandled error during button3 autosampler stabilization automation:\n" + error_text.rstrip(),
            )
        raise


if __name__ == "__main__":
    main()
