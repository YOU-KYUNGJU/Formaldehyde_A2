#!/usr/bin/env python3
"""
dump_classnn.py

Enumerate visible top-level windows for target executable names, then dump
each child control's class name, ClassNN-like identifier, text, and rectangle to
controls/<exe_name>.json.

Usage:
  python dump_classnn.py --exe UVVisLauncher.exe UVNavi.exe UVASXController.exe

Requires: pywin32, psutil
"""
import argparse
import json
import os
import re
from collections import defaultdict

try:
    import win32gui
    import win32process
except Exception:
    print("pywin32 is required: pip install pywin32")
    raise

try:
    import psutil
except Exception:
    print("psutil is required: pip install psutil")
    raise


def get_process_name(pid):
    try:
        process = psutil.Process(pid)
        return os.path.basename(process.exe())
    except Exception:
        try:
            return process.name()
        except Exception:
            return ""


def enum_children_recursive(parent_hwnd, parent_path, results, class_counter):
    children = []

    def callback(hwnd, _lparam):
        children.append(hwnd)

    win32gui.EnumChildWindows(parent_hwnd, callback, None)

    for hwnd in children:
        try:
            class_name = win32gui.GetClassName(hwnd)
        except Exception:
            class_name = ""
        try:
            text = win32gui.GetWindowText(hwnd)
        except Exception:
            text = ""
        try:
            rect = win32gui.GetWindowRect(hwnd)
        except Exception:
            rect = (0, 0, 0, 0)

        base = re.split(r"[.\s]+", class_name)[-1] if class_name else class_name
        base_clean = re.sub(r"[^A-Za-z0-9]", "", base) if base else "Class"
        index = class_counter[base_clean] + 1
        class_counter[base_clean] = index
        classnn = f"{base_clean}{index}"

        entry = {
            "hwnd": int(hwnd),
            "class_name": class_name,
            "classnn": classnn,
            "text": text,
            "rect": rect,
            "path": parent_path + [classnn],
        }
        results.append(entry)

        enum_children_recursive(hwnd, parent_path + [classnn], results, class_counter)


def find_top_windows_for_exe(target_exe_names):
    windows = []

    def enum_callback(hwnd, _lparam):
        if not win32gui.IsWindowVisible(hwnd):
            return
        try:
            _, pid = win32process.GetWindowThreadProcessId(hwnd)
        except Exception:
            return

        process_name = get_process_name(pid)
        if process_name in target_exe_names:
            windows.append((hwnd, pid, process_name, win32gui.GetWindowText(hwnd)))

    win32gui.EnumWindows(enum_callback, None)
    return windows


def dump_for_exes(exe_list, out_dir="controls"):
    os.makedirs(out_dir, exist_ok=True)
    targets = [os.path.basename(exe) for exe in exe_list]

    top_windows = find_top_windows_for_exe(targets)
    if not top_windows:
        print("No top-level windows were found for the target process names.")

    grouped = defaultdict(list)
    for hwnd, pid, process_name, title in top_windows:
        grouped[process_name].append((hwnd, pid, title))

    for process_name, window_list in grouped.items():
        output = {
            "process": process_name,
            "windows": [],
        }

        for hwnd, pid, title in window_list:
            controls = []
            class_counter = defaultdict(int)
            try:
                top_class = win32gui.GetClassName(hwnd)
            except Exception:
                top_class = ""
            try:
                top_rect = win32gui.GetWindowRect(hwnd)
            except Exception:
                top_rect = (0, 0, 0, 0)

            enum_children_recursive(hwnd, [f"HWND_{hwnd}"], controls, class_counter)

            output["windows"].append(
                {
                    "hwnd": int(hwnd),
                    "pid": int(pid),
                    "title": title,
                    "class_name": top_class,
                    "rect": top_rect,
                    "controls": controls,
                }
            )

        out_path = os.path.join(out_dir, f"{process_name}.json")
        with open(out_path, "w", encoding="utf-8") as output_file:
            json.dump(output, output_file, ensure_ascii=False, indent=2)

        control_count = sum(len(window["controls"]) for window in output["windows"])
        print(f"Saved: {out_path} ({len(output['windows'])} windows, {control_count} controls)")


def main():
    parser = argparse.ArgumentParser(description="Dump ClassNN-like info for target exe windows")
    parser.add_argument(
        "--exe",
        "-e",
        nargs="+",
        required=False,
        default=["UVVisLauncher.exe", "UVNavi.exe", "UVASXController.exe"],
        help="Target executable names (e.g. UVVisLauncher.exe)",
    )
    parser.add_argument("--out", "-o", default="controls", help="Output directory")
    args = parser.parse_args()

    dump_for_exes(args.exe, args.out)


if __name__ == "__main__":
    main()
