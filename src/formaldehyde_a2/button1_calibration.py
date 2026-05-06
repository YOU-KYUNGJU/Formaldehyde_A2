#!/usr/bin/env python3
"""
Button 1 calibration automation for ASX-560 Controller.

This script uses coordinate-based clicks for the ASX-560 Controller window,
because its internal controls are not exposed as regular Win32 child controls.
"""
import argparse
import ctypes
import os
import shutil
import subprocess
import time
import tkinter as tk
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from tkinter import messagebox


ASX_TITLE = "ASX-560 Controller for LabSolutions UV-Vis"
LAUNCHER_TITLE = "UV Launcher"
LAUNCHER_PROCESS_NAME = "UVVisLauncher.exe"
SETTING_TITLE = "Analysis Setting - ASX-560 - Quantitation"
OPEN_DIALOG_TITLES = ("Open", "열기")
SAVE_DIALOG_TITLES = ("Save", "Save As", "다른 이름으로 저장", "저장")

LAUNCHER_REFERENCE_SIZE = (498, 480)
ASX_REFERENCE_SIZE = (739, 599)
SETTING_REFERENCE_SIZE = (1280, 768)

LAUNCHER_TARGET_SIZE = (498, 480)
ASX_TARGET_SIZE = (739, 599)
SETTING_TARGET_SIZE = (1280, 768)

AUTOMATIC_ANALYSIS_BUTTON = (249, 276)
READ_BUTTON = (434, 186)
EDIT_BUTTON = (551, 186)

ANALYSIS1_TAB = (58, 459)
ANALYSIS2_TAB = (121, 459)
FILE_NAME_INPUT = (255, 497)
SAVE_AS_AND_CLOSE = (922, 738)
CLICK_RETRY_OFFSET = (20, 20)

pyautogui = None
pyperclip = None
win32con = None
win32gui = None
psutil = None


class AutomationLogger:
    def __init__(self, enabled=True, log_dir="logs", file_prefix="button1_calibration"):
        self.enabled = enabled
        self.log_path = None
        if enabled:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            Path(log_dir).mkdir(parents=True, exist_ok=True)
            self.log_path = Path(log_dir) / f"{file_prefix}_{timestamp}.log"

    def write(self, message):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        line = f"[{timestamp}] {message}"
        print(line)
        if self.log_path:
            with self.log_path.open("a", encoding="utf-8") as log_file:
                log_file.write(line + "\n")

    def dump_windows(self, label):
        if not self.enabled or not win32gui:
            return

        self.write(f"Window dump: {label}")

        def enum_callback(hwnd, _lparam):
            if not win32gui.IsWindowVisible(hwnd):
                return
            title = win32gui.GetWindowText(hwnd)
            if not title:
                return
            try:
                class_name = win32gui.GetClassName(hwnd)
                rect = win32gui.GetWindowRect(hwnd)
            except Exception:
                class_name = ""
                rect = ""
            self.write(f"  hwnd={hwnd} title={title!r} class={class_name!r} rect={rect}")

        win32gui.EnumWindows(enum_callback, None)

    def screenshot(self, label):
        if not self.enabled or not pyautogui or not self.log_path:
            return
        safe_label = "".join(ch if ch.isalnum() else "_" for ch in label).strip("_")
        image_path = self.log_path.with_name(f"{self.log_path.stem}_{safe_label}.png")
        try:
            pyautogui.screenshot(str(image_path))
            self.write(f"Screenshot saved: {image_path}")
        except Exception as exc:
            self.write(f"PyAutoGUI screenshot failed: {exc}")
            try:
                from PIL import ImageGrab

                image = ImageGrab.grab()
                image.save(str(image_path))
                self.write(f"Screenshot saved via PIL.ImageGrab: {image_path}")
            except Exception as fallback_exc:
                self.write(f"Fallback screenshot failed: {fallback_exc}")


LOGGER = AutomationLogger(enabled=False)


@dataclass
class CalibrationPaths:
    date_text: str
    standard_file_name: str
    unknown_file_name: str
    source_vasm: str
    target_vasm: str


def set_dpi_awareness():
    try:
        ctypes.windll.user32.SetProcessDPIAware()
    except Exception:
        pass


def load_gui_dependencies():
    global pyautogui, pyperclip, win32con, win32gui

    if pyautogui and pyperclip and win32con and win32gui:
        return

    try:
        import pyautogui as imported_pyautogui
        import pyperclip as imported_pyperclip
        import win32con as imported_win32con
        import win32gui as imported_win32gui
    except ImportError as exc:
        raise SystemExit(
            "Missing GUI automation dependency. Run: pip install -r requirements.txt"
        ) from exc

    pyautogui = imported_pyautogui
    pyperclip = imported_pyperclip
    win32con = imported_win32con
    win32gui = imported_win32gui


def load_process_dependencies():
    global psutil

    if psutil:
        return

    try:
        import psutil as imported_psutil
    except ImportError as exc:
        raise SystemExit(
            "Missing process dependency. Run: pip install -r requirements.txt"
        ) from exc

    psutil = imported_psutil


def is_launcher_process_running():
    load_process_dependencies()
    for process in psutil.process_iter(["name"]):
        try:
            process_name = process.info.get("name")
        except Exception:
            continue
        if process_name and process_name.lower() == LAUNCHER_PROCESS_NAME.lower():
            return True
    return False


def iter_launcher_candidates(explicit_path=None):
    if explicit_path:
        yield explicit_path

    env_path = os.environ.get("UVVIS_LAUNCHER_PATH")
    if env_path:
        yield env_path

    which_path = shutil.which(LAUNCHER_PROCESS_NAME)
    if which_path:
        yield which_path

    common_roots = [
        os.environ.get("ProgramFiles"),
        os.environ.get("ProgramFiles(x86)"),
        os.environ.get("ProgramW6432"),
        r"C:\Shimadzu",
    ]
    relative_candidates = [
        Path("LabSolutions") / "UVVis" / LAUNCHER_PROCESS_NAME,
        Path("Shimadzu") / "LabSolutions" / "UVVis" / LAUNCHER_PROCESS_NAME,
        Path("LabSolutions UV-Vis") / LAUNCHER_PROCESS_NAME,
    ]
    for root in common_roots:
        if not root:
            continue
        for relative_path in relative_candidates:
            yield str(Path(root) / relative_path)


def resolve_launcher_path(explicit_path=None):
    for candidate in iter_launcher_candidates(explicit_path=explicit_path):
        normalized = os.path.expandvars(os.path.expanduser(candidate))
        if os.path.isfile(normalized):
            return normalized
    return None


def launch_uvvis_launcher(launcher_path=None, dry_run=False):
    resolved_path = resolve_launcher_path(explicit_path=launcher_path)
    if not resolved_path:
        raise FileNotFoundError(
            "UVVisLauncher.exe path not found. Pass --launcher-path or set UVVIS_LAUNCHER_PATH."
        )

    LOGGER.write(f"Launching UVVis launcher: {resolved_path}")
    if dry_run:
        print(f"[dry-run] launch UVVis launcher: {resolved_path}")
        return None

    subprocess.Popen([resolved_path], close_fds=True)
    time.sleep(2.0)
    return resolved_path


def ensure_launcher_ready(launcher_path=None, dry_run=False):
    launcher_hwnd = wait_for_window_optional(LAUNCHER_TITLE, timeout=1)
    if launcher_hwnd:
        return launcher_hwnd

    if not dry_run and is_launcher_process_running():
        LOGGER.write("UVVisLauncher.exe process is running. Waiting for UV Launcher window.")
        return wait_for_window(LAUNCHER_TITLE, timeout=15)

    LOGGER.write("UVVisLauncher.exe is not running. Launching it now.")
    launch_uvvis_launcher(launcher_path=launcher_path, dry_run=dry_run)
    if dry_run:
        return None
    return wait_for_window(LAUNCHER_TITLE, timeout=30)


def build_paths(run_date, source_vasm):
    date_text = run_date.strftime("%Y%m%d")
    year_text = run_date.strftime("%Y")
    month_text = run_date.strftime("%m")
    standard_file_name = f"Std_Test_{date_text}.vqud"
    unknown_file_name = f"Unk_Test_{date_text}.vqud"
    target_vasm = rf"C:\UVVis-Data\Parameter\{year_text}\{month_text}\{date_text}_YKJ_ASX_Test_Std_Final.vasm"
    return CalibrationPaths(
        date_text=date_text,
        standard_file_name=standard_file_name,
        unknown_file_name=unknown_file_name,
        source_vasm=source_vasm,
        target_vasm=target_vasm,
    )


def find_window(title_contains):
    matched_hwnd = None

    def enum_callback(hwnd, _lparam):
        nonlocal matched_hwnd
        if matched_hwnd or not win32gui.IsWindowVisible(hwnd):
            return
        title = win32gui.GetWindowText(hwnd)
        if title_contains.lower() in title.lower():
            matched_hwnd = hwnd

    win32gui.EnumWindows(enum_callback, None)
    return matched_hwnd


def find_window_any(title_candidates):
    for title_contains in title_candidates:
        hwnd = find_window(title_contains)
        if hwnd:
            return hwnd, title_contains
    return None, None


def wait_for_window(title_contains, timeout=20):
    deadline = time.time() + timeout
    while time.time() < deadline:
        hwnd = find_window(title_contains)
        if hwnd:
            LOGGER.write(f"Found window: {title_contains!r}, hwnd={hwnd}")
            return hwnd
        time.sleep(0.3)
    LOGGER.dump_windows(f"timeout waiting for {title_contains!r}")
    LOGGER.screenshot(f"timeout_{title_contains}")
    raise TimeoutError(f"Window not found: {title_contains}")


def wait_for_window_optional(title_contains, timeout=5):
    deadline = time.time() + timeout
    while time.time() < deadline:
        hwnd = find_window(title_contains)
        if hwnd:
            LOGGER.write(f"Found optional window: {title_contains!r}, hwnd={hwnd}")
            return hwnd
        time.sleep(0.3)
    return None


def wait_for_window_any(title_candidates, timeout=20, label="window"):
    deadline = time.time() + timeout
    candidates = tuple(title_candidates)
    while time.time() < deadline:
        hwnd, matched_title = find_window_any(candidates)
        if hwnd:
            LOGGER.write(f"Found {label}: matched {matched_title!r}, hwnd={hwnd}")
            return hwnd
        time.sleep(0.3)
    LOGGER.dump_windows(f"timeout waiting for {label}: {candidates}")
    LOGGER.screenshot(f"timeout_{label}")
    raise TimeoutError(f"Window not found: {label} candidates={candidates}")


def activate_window(hwnd, target_size=None, target_position=(20, 20)):
    if win32gui.IsIconic(hwnd):
        win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)

    if target_size:
        win32gui.MoveWindow(
            hwnd,
            target_position[0],
            target_position[1],
            target_size[0],
            target_size[1],
            True,
        )

    win32gui.SetForegroundWindow(hwnd)
    LOGGER.write(f"Activated hwnd={hwnd}, rect={win32gui.GetWindowRect(hwnd)}")
    time.sleep(0.4)


def window_rect(hwnd):
    left, top, right, bottom = win32gui.GetWindowRect(hwnd)
    return left, top, right - left, bottom - top


def scale_point(hwnd, reference_size, reference_point):
    left, top, width, height = window_rect(hwnd)
    scale_x = width / reference_size[0]
    scale_y = height / reference_size[1]
    return (
        int(left + reference_point[0] * scale_x),
        int(top + reference_point[1] * scale_y),
    )


def click_reference(hwnd, reference_size, reference_point, dry_run=False, label=""):
    x_pos, y_pos = scale_point(hwnd, reference_size, reference_point)
    if dry_run:
        print(f"[dry-run] click {label or reference_point}: ({x_pos}, {y_pos})")
        return
    LOGGER.write(f"Click {label or reference_point}: ({x_pos}, {y_pos})")
    pyautogui.click(x_pos, y_pos)
    time.sleep(0.4)


def click_reference_with_offset(
    hwnd,
    reference_size,
    reference_point,
    offset=CLICK_RETRY_OFFSET,
    dry_run=False,
    label="",
):
    adjusted_point = (reference_point[0] + offset[0], reference_point[1] + offset[1])
    click_reference(hwnd, reference_size, adjusted_point, dry_run=dry_run, label=label)


def paste_text(text, dry_run=False, label="text"):
    if dry_run:
        print(f"[dry-run] paste {label}: {text}")
        return
    LOGGER.write(f"Paste {label}: {text}")
    pyperclip.copy(text)
    pyautogui.hotkey("ctrl", "v")
    time.sleep(0.2)


def replace_field_text(text, dry_run=False, label="field"):
    if dry_run:
        print(f"[dry-run] replace {label}: {text}")
        return
    pyautogui.hotkey("ctrl", "a")
    time.sleep(0.1)
    pyautogui.press("backspace")
    time.sleep(0.1)
    paste_text(text, label=label)
    pyautogui.press("tab")
    time.sleep(0.2)


def open_vasm_from_read_dialog(paths, dry_run=False):
    if dry_run:
        print(f"[dry-run] open source vasm: {paths.source_vasm}")
        return

    wait_for_window_any(OPEN_DIALOG_TITLES, timeout=15, label="open dialog")
    paste_text(paths.source_vasm, label="source vasm")
    pyautogui.press("enter")
    LOGGER.write("Pressed Enter in open dialog")
    time.sleep(1.5)


def open_vasm_from_read_dialog_with_retry(asx_hwnd, paths, dry_run=False):
    if dry_run:
        open_vasm_from_read_dialog(paths, dry_run=True)
        return

    try:
        open_vasm_from_read_dialog(paths, dry_run=False)
    except TimeoutError:
        LOGGER.write("Open dialog not found after ASX Read. Retrying with +20 offset.")
        activate_window(asx_hwnd, target_size=ASX_TARGET_SIZE)
        click_reference_with_offset(
            asx_hwnd,
            ASX_REFERENCE_SIZE,
            READ_BUTTON,
            dry_run=False,
            label="ASX Read retry +20",
        )
        LOGGER.screenshot("after_read_retry_click")
        open_vasm_from_read_dialog(paths, dry_run=False)


def open_setting_window_from_edit(asx_hwnd, dry_run=False, label="ASX Edit"):
    activate_window(asx_hwnd, target_size=ASX_TARGET_SIZE)
    click_reference(asx_hwnd, ASX_REFERENCE_SIZE, EDIT_BUTTON, dry_run, label)
    LOGGER.screenshot("after_edit_click")
    if dry_run:
        return None
    return wait_for_window(SETTING_TITLE, timeout=20)


def open_setting_window_from_edit_with_retry(asx_hwnd, dry_run=False, label="ASX Edit"):
    if dry_run:
        return open_setting_window_from_edit(asx_hwnd, dry_run=True, label=label)

    try:
        return open_setting_window_from_edit(asx_hwnd, dry_run=False, label=label)
    except TimeoutError:
        LOGGER.write("Analysis Setting window not found after ASX Edit. Retrying with +20 offset.")
        activate_window(asx_hwnd, target_size=ASX_TARGET_SIZE)
        click_reference_with_offset(
            asx_hwnd,
            ASX_REFERENCE_SIZE,
            EDIT_BUTTON,
            dry_run=False,
            label=f"{label} retry +20",
        )
        LOGGER.screenshot("after_edit_retry_click")
        return wait_for_window(SETTING_TITLE, timeout=20)


def ensure_asx_controller_open(dry_run=False, launcher_path=None):
    asx_hwnd = wait_for_window_optional(ASX_TITLE, timeout=3)
    if asx_hwnd:
        return asx_hwnd

    LOGGER.write("ASX Controller window is not open. Trying UV Launcher > Automatic Analysis.")
    launcher_hwnd = ensure_launcher_ready(launcher_path=launcher_path, dry_run=dry_run)
    activate_window(launcher_hwnd, target_size=LAUNCHER_TARGET_SIZE, target_position=(20, 20))
    click_reference(
        launcher_hwnd,
        LAUNCHER_REFERENCE_SIZE,
        AUTOMATIC_ANALYSIS_BUTTON,
        dry_run,
        "UV Launcher Automatic Analysis",
    )

    if dry_run:
        return launcher_hwnd

    return wait_for_window(ASX_TITLE, timeout=30)


def save_vasm_from_save_dialog(paths, dry_run=False):
    target_dir = os.path.dirname(paths.target_vasm)

    if dry_run:
        print(f"[dry-run] ensure directory: {target_dir}")
        print(f"[dry-run] save target vasm: {paths.target_vasm}")
        return

    os.makedirs(target_dir, exist_ok=True)
    wait_for_window_any(SAVE_DIALOG_TITLES, timeout=15, label="save dialog")
    paste_text(paths.target_vasm, label="target vasm")
    pyautogui.press("enter")
    LOGGER.write("Pressed Enter in save dialog")
    time.sleep(0.8)


def show_completion_popup(title, message, dry_run=False):
    if dry_run:
        print(f"[dry-run] popup {title}: {message}")
        return

    popup_root = tk.Tk()
    popup_root.withdraw()
    popup_root.attributes("-topmost", True)
    try:
        messagebox.showinfo(title, message, parent=popup_root)
    finally:
        popup_root.destroy()


def run_button1_calibration(paths, dry_run=False, launcher_path=None):
    LOGGER.write("Calibration automation values:")
    LOGGER.write(f"- date: {paths.date_text}")
    LOGGER.write(f"- standard: {paths.standard_file_name}")
    LOGGER.write(f"- unknown: {paths.unknown_file_name}")
    LOGGER.write(f"- source: {paths.source_vasm}")
    LOGGER.write(f"- target: {paths.target_vasm}")

    if dry_run:
        print("[dry-run] reference coordinates:")
        print(f"- ASX Read: {READ_BUTTON} on {ASX_REFERENCE_SIZE}")
        print(f"- ASX Edit: {EDIT_BUTTON} on {ASX_REFERENCE_SIZE}")
        print(f"- Launcher Automatic Analysis: {AUTOMATIC_ANALYSIS_BUTTON} on {LAUNCHER_REFERENCE_SIZE}")
        print(f"- Analysis1 tab: {ANALYSIS1_TAB} on {SETTING_REFERENCE_SIZE}")
        print(f"- Analysis2 tab: {ANALYSIS2_TAB} on {SETTING_REFERENCE_SIZE}")
        print(f"- File Name input: {FILE_NAME_INPUT} on {SETTING_REFERENCE_SIZE}")
        print(f"- Save As and Close: {SAVE_AS_AND_CLOSE} on {SETTING_REFERENCE_SIZE}")
        print("Done.")
        return

    load_gui_dependencies()
    LOGGER.dump_windows("before automation")

    ensure_launcher_ready(launcher_path=launcher_path, dry_run=dry_run)

    asx_hwnd = ensure_asx_controller_open(dry_run, launcher_path=launcher_path)
    activate_window(asx_hwnd, target_size=ASX_TARGET_SIZE)
    click_reference(asx_hwnd, ASX_REFERENCE_SIZE, READ_BUTTON, dry_run, "ASX Read")
    LOGGER.screenshot("after_read_click")
    open_vasm_from_read_dialog_with_retry(asx_hwnd, paths, dry_run)

    asx_hwnd = wait_for_window(ASX_TITLE, timeout=20)
    setting_hwnd = open_setting_window_from_edit_with_retry(asx_hwnd, dry_run, "ASX Edit")
    activate_window(setting_hwnd, target_size=SETTING_TARGET_SIZE, target_position=(30, 30))

    click_reference(setting_hwnd, SETTING_REFERENCE_SIZE, ANALYSIS1_TAB, dry_run, "Analysis1 tab")
    click_reference(setting_hwnd, SETTING_REFERENCE_SIZE, FILE_NAME_INPUT, dry_run, "Analysis1 File Name")
    replace_field_text(paths.standard_file_name, dry_run, "standard file name")

    click_reference(setting_hwnd, SETTING_REFERENCE_SIZE, ANALYSIS2_TAB, dry_run, "Analysis2 tab")
    click_reference(setting_hwnd, SETTING_REFERENCE_SIZE, FILE_NAME_INPUT, dry_run, "Analysis2 File Name")
    replace_field_text(paths.unknown_file_name, dry_run, "unknown file name")

    click_reference(
        setting_hwnd,
        SETTING_REFERENCE_SIZE,
        SAVE_AS_AND_CLOSE,
        dry_run,
        "Save As and Close",
    )
    save_vasm_from_save_dialog(paths, dry_run)
    show_completion_popup("Button 1 Complete", "Calibration setup is ready.", dry_run=dry_run)

    print("Done.")


def parse_args():
    parser = argparse.ArgumentParser(description="Run button 1 calibration automation.")
    parser.add_argument(
        "--date",
        help="Run date in YYYYMMDD format. Default: today.",
    )
    parser.add_argument(
        "--source-vasm",
        default=r"C:\UVVis-Data\Parameter\20241104_YKJ_ASX_Test_Std_Final.vasm",
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


def main():
    global LOGGER
    set_dpi_awareness()

    args = parse_args()
    LOGGER = AutomationLogger(enabled=not args.no_log, log_dir=args.log_dir)
    if LOGGER.log_path:
        LOGGER.write(f"Log file: {LOGGER.log_path}")

    run_date = datetime.strptime(args.date, "%Y%m%d") if args.date else datetime.today()
    paths = build_paths(run_date, args.source_vasm)

    if not args.dry_run:
        load_gui_dependencies()
        pyautogui.PAUSE = 0.15
        pyautogui.FAILSAFE = True

    run_button1_calibration(paths, dry_run=args.dry_run, launcher_path=args.launcher_path)


if __name__ == "__main__":
    main()
