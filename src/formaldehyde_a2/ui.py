#!/usr/bin/env python3
"""Desktop launcher UI for the three automation buttons."""

import queue
import subprocess
import sys
import threading
import tkinter as tk
from pathlib import Path
from tkinter import messagebox, ttk


APP_TITLE = "Formaldehyde A2 Automation"
DEFAULT_LOG_DIR = "logs"
DEFAULT_SAMPLE_COUNT = "120"


class AutomationUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title(APP_TITLE)
        self.root.geometry("860x560")
        self.root.minsize(720, 500)

        self.process = None
        self.output_queue = queue.Queue()
        self.reader_thread = None

        self.dry_run_var = tk.BooleanVar(value=False)
        self.status_var = tk.StringVar(value="Idle")

        self._build_layout()
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)
        self.root.after(100, self._poll_output)

    def _build_layout(self):
        outer = ttk.Frame(self.root, padding=16)
        outer.pack(fill="both", expand=True)
        outer.columnconfigure(0, weight=1)
        outer.rowconfigure(2, weight=1)

        top_bar = ttk.Frame(outer)
        top_bar.grid(row=0, column=0, sticky="ew")
        top_bar.columnconfigure(1, weight=1)

        ttk.Checkbutton(top_bar, text="Dry Run", variable=self.dry_run_var).grid(
            row=0,
            column=0,
            sticky="w",
        )
        ttk.Label(
            top_bar,
            text="Button 2 uses sample count 120 by default. Logs are saved to logs/.",
            anchor="w",
        ).grid(row=0, column=1, sticky="w", padx=(14, 0))

        button_row = ttk.Frame(outer)
        button_row.grid(row=1, column=0, sticky="ew", pady=12)
        button_row.columnconfigure((0, 1, 2, 3), weight=1)

        self.button1 = ttk.Button(
            button_row,
            text="Button 1 Calibration",
            command=lambda: self._run_automation("button1_calibration.py"),
        )
        self.button1.grid(row=0, column=0, sticky="ew", padx=(0, 8))

        self.button2 = ttk.Button(
            button_row,
            text="Button 2 Sample",
            command=lambda: self._run_automation("button2_sampleMeasurement.py"),
        )
        self.button2.grid(row=0, column=1, sticky="ew", padx=8)

        self.button3 = ttk.Button(
            button_row,
            text="Button 3 Stabilize",
            command=lambda: self._run_automation("button3_autosamplerStabilization.py"),
        )
        self.button3.grid(row=0, column=2, sticky="ew", padx=8)

        ttk.Label(
            button_row,
            text="Use in Manual Mode",
            anchor="center",
        ).grid(row=1, column=2, sticky="ew", padx=8, pady=(6, 0))

        self.stop_button = ttk.Button(button_row, text="Stop", command=self._stop_process, state="disabled")
        self.stop_button.grid(row=0, column=3, sticky="ew", padx=(8, 0))

        console_frame = ttk.LabelFrame(outer, text="Run Output", padding=12)
        console_frame.grid(row=2, column=0, sticky="nsew")
        console_frame.columnconfigure(0, weight=1)
        console_frame.rowconfigure(0, weight=1)

        self.console = tk.Text(console_frame, wrap="word", height=18, state="disabled")
        self.console.grid(row=0, column=0, sticky="nsew")

        scrollbar = ttk.Scrollbar(console_frame, orient="vertical", command=self.console.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.console.configure(yscrollcommand=scrollbar.set)

        status_bar = ttk.Label(outer, textvariable=self.status_var, anchor="w")
        status_bar.grid(row=3, column=0, sticky="ew", pady=(10, 0))

    def _append_output(self, text):
        self.console.configure(state="normal")
        self.console.insert("end", text)
        self.console.see("end")
        self.console.configure(state="disabled")

    def _build_command(self, script_name):
        command = [sys.executable, script_name, "--log-dir", DEFAULT_LOG_DIR]

        if script_name == "button2_sampleMeasurement.py":
            command.extend(["--sample-count", DEFAULT_SAMPLE_COUNT])

        if self.dry_run_var.get():
            command.append("--dry-run")

        return command

    def _run_automation(self, script_name):
        if self.process and self.process.poll() is None:
            messagebox.showwarning(APP_TITLE, "Another automation is already running.")
            return

        command = self._build_command(script_name)
        self._append_output(f"\n$ {' '.join(command)}\n")
        self.status_var.set(f"Running: {Path(script_name).stem}")
        self._set_running_state(True)

        self.process = subprocess.Popen(
            command,
            cwd=Path(__file__).resolve().parents[2],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )
        self.reader_thread = threading.Thread(target=self._stream_output, daemon=True)
        self.reader_thread.start()

    def _stream_output(self):
        if not self.process or not self.process.stdout:
            return
        for line in self.process.stdout:
            self.output_queue.put(line)
        self.process.stdout.close()

    def _poll_output(self):
        while True:
            try:
                line = self.output_queue.get_nowait()
            except queue.Empty:
                break
            self._append_output(line)

        if self.process and self.process.poll() is not None:
            exit_code = self.process.returncode
            if exit_code == 0:
                self.status_var.set("Completed")
            else:
                self.status_var.set(f"Failed: exit code {exit_code}")
            self._set_running_state(False)
            self.process = None

        self.root.after(100, self._poll_output)

    def _set_running_state(self, is_running):
        button_state = "disabled" if is_running else "normal"
        stop_state = "normal" if is_running else "disabled"
        self.button1.configure(state=button_state)
        self.button2.configure(state=button_state)
        self.button3.configure(state=button_state)
        self.stop_button.configure(state=stop_state)

    def _stop_process(self):
        if not self.process or self.process.poll() is not None:
            return
        self.process.terminate()
        self._append_output("[ui] Stop requested.\n")
        self.status_var.set("Stop requested")

    def _on_close(self):
        if self.process and self.process.poll() is None:
            if not messagebox.askyesno(APP_TITLE, "An automation is still running. Close the UI anyway?"):
                return
        self.root.destroy()

    def run(self):
        self.root.mainloop()


def main():
    app = AutomationUI()
    app.run()


if __name__ == "__main__":
    main()
