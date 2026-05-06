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
STOP_SHORTCUT_LABEL = "Esc"
BUTTON1_MODULE = "src.formaldehyde_a2.button1_calibration"
BUTTON1_1_MODULE = "src.formaldehyde_a2.button1_1_calibration_file_management"
BUTTON2_MODULE = "src.formaldehyde_a2.button2_sampleMeasurement"
BUTTON3_MODULE = "src.formaldehyde_a2.button3_autosamplerStabilization"
BACKGROUND = "#f4efe7"
SURFACE = "#fffdf8"
SURFACE_ALT = "#ebe3d8"
TEXT = "#2e2a26"
MUTED = "#6f655d"
ACCENT = "#0f766e"
ACCENT_SOFT = "#d9f3ef"
STOP = "#b42318"
STOP_ACTIVE = "#8f1d14"
CONSOLE_BG = "#1f2430"
CONSOLE_FG = "#f7f7f2"
WINDOW_SIZE = (980, 700)
WINDOW_MIN_SIZE = (900, 640)
WINDOW_MARGIN = 24
WINDOW_LIFT = 20

class AutomationUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title(APP_TITLE)
        self.root.geometry(f"{WINDOW_SIZE[0]}x{WINDOW_SIZE[1]}")
        self.root.minsize(*WINDOW_MIN_SIZE)
        self.root.configure(bg=BACKGROUND)

        self.process = None
        self.output_queue = queue.Queue()
        self.reader_thread = None

        self.dry_run_var = tk.BooleanVar(value=False)
        self.status_var = tk.StringVar(value="Idle")
        self.status_detail_var = tk.StringVar(value="Choose an automation to begin.")

        self._configure_styles()
        self._build_layout()
        self._position_window_bottom_right()
        self._bind_shortcuts()
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)
        self.root.after(100, self._poll_output)

    def _configure_styles(self):
        style = ttk.Style(self.root)
        style.theme_use("clam")

        style.configure(".", background=BACKGROUND, foreground=TEXT)
        style.configure("App.TFrame", background=BACKGROUND)
        style.configure("Surface.TFrame", background=SURFACE)
        style.configure("Header.TFrame", background=TEXT)
        style.configure("Card.TLabelframe", background=SURFACE, borderwidth=0, relief="flat")
        style.configure("Card.TLabelframe.Label", background=SURFACE, foreground=TEXT, font=("Segoe UI Semibold", 11))
        style.configure("Title.TLabel", background=TEXT, foreground=SURFACE, font=("Segoe UI Semibold", 17))
        style.configure("Subtitle.TLabel", background=TEXT, foreground="#ddd6ce", font=("Segoe UI", 9))
        style.configure("SectionTitle.TLabel", background=SURFACE, foreground=TEXT, font=("Segoe UI Semibold", 11))
        style.configure("Body.TLabel", background=SURFACE, foreground=MUTED, font=("Segoe UI", 9))
        style.configure("Muted.TLabel", background=BACKGROUND, foreground=MUTED, font=("Segoe UI", 9))
        style.configure("HeaderMuted.TLabel", background=TEXT, foreground="#cfc4b9", font=("Segoe UI", 9))
        style.configure("Pill.TLabel", background=ACCENT_SOFT, foreground=ACCENT, font=("Segoe UI Semibold", 9), padding=(8, 4))
        style.configure("StatusValue.TLabel", background=SURFACE_ALT, foreground=TEXT, font=("Segoe UI Semibold", 10), padding=(10, 5))
        style.configure("HeaderStatusValue.TLabel", background="#4b433d", foreground=SURFACE, font=("Segoe UI Semibold", 10), padding=(10, 5))
        style.configure(
            "Action.TButton",
            font=("Segoe UI Semibold", 10),
            padding=(10, 10),
            background=SURFACE,
            foreground=TEXT,
            borderwidth=0,
            focusthickness=0,
        )
        style.map(
            "Action.TButton",
            background=[("active", SURFACE_ALT), ("disabled", "#f3eee8")],
            foreground=[("disabled", "#a69b92")],
        )
        style.configure(
            "Stop.TButton",
            font=("Segoe UI Semibold", 10),
            padding=(10, 10),
            background=STOP,
            foreground=SURFACE,
            borderwidth=0,
            focusthickness=0,
        )
        style.map(
            "Stop.TButton",
            background=[("active", STOP_ACTIVE), ("disabled", "#d9b0ab")],
            foreground=[("disabled", SURFACE)],
        )
        style.configure(
            "Switch.TCheckbutton",
            background=SURFACE,
            foreground=TEXT,
            font=("Segoe UI", 9),
            focuscolor=SURFACE,
        )

    def _build_layout(self):
        outer = ttk.Frame(self.root, padding=12, style="App.TFrame")
        outer.pack(fill="both", expand=True)
        outer.columnconfigure(0, weight=1)
        outer.rowconfigure(1, weight=1)

        header = ttk.Frame(outer, padding=14, style="Header.TFrame")
        header.grid(row=0, column=0, sticky="ew")
        header.columnconfigure(0, weight=1)
        header.columnconfigure(1, weight=0)

        header_copy = ttk.Frame(header, style="Header.TFrame")
        header_copy.grid(row=0, column=0, sticky="nw")
        header_copy.columnconfigure(0, weight=1)

        ttk.Label(header_copy, text=APP_TITLE, style="Title.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Label(
            header_copy,
            text="Run calibration, sample measurement, and autosampler workflows from one clean launcher.",
            style="Subtitle.TLabel",
        ).grid(row=1, column=0, sticky="w", pady=(3, 0))

        status_panel = ttk.Frame(header, padding=(16, 2, 0, 2), style="Header.TFrame")
        status_panel.grid(row=0, column=1, sticky="ne")
        status_panel.columnconfigure(0, weight=1)
        ttk.Label(status_panel, text="Live Status", style="HeaderMuted.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Label(status_panel, textvariable=self.status_var, style="HeaderStatusValue.TLabel").grid(row=1, column=0, sticky="ew", pady=(6, 6))
        ttk.Label(status_panel, textvariable=self.status_detail_var, style="HeaderMuted.TLabel", wraplength=250).grid(row=2, column=0, sticky="w")

        console_section = ttk.Frame(outer, style="App.TFrame")
        console_section.grid(row=1, column=0, sticky="nsew", pady=(10, 0))
        console_section.columnconfigure(0, weight=1)
        console_section.rowconfigure(1, weight=1)

        console_header = ttk.Frame(console_section, style="App.TFrame")
        console_header.grid(row=0, column=0, sticky="ew", pady=(0, 5))
        console_header.columnconfigure(0, weight=1)
        console_header.columnconfigure(1, weight=0)

        ttk.Label(console_header, text="Run Output", style="SectionTitle.TLabel").grid(row=0, column=0, sticky="w", padx=(6, 0))
        ttk.Label(console_header, text="Logs are saved to logs/.", style="Muted.TLabel").grid(row=0, column=1, sticky="e")

        console_frame = ttk.Frame(console_section, padding=12, style="Surface.TFrame")
        console_frame.grid(row=1, column=0, sticky="nsew")
        console_frame.columnconfigure(0, weight=1)
        console_frame.rowconfigure(0, weight=1)

        self.console = tk.Text(
            console_frame,
            wrap="word",
            height=12,
            state="disabled",
            bg=CONSOLE_BG,
            fg=CONSOLE_FG,
            insertbackground=CONSOLE_FG,
            relief="flat",
            borderwidth=0,
            padx=12,
            pady=12,
            font=("Consolas", 10),
        )
        self.console.grid(row=0, column=0, sticky="nsew")

        scrollbar = ttk.Scrollbar(console_frame, orient="vertical", command=self.console.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.console.configure(yscrollcommand=scrollbar.set)

        button_row = ttk.Frame(outer, style="App.TFrame")
        button_row.grid(row=2, column=0, sticky="nsew", pady=(10, 0))
        button_row.columnconfigure((0, 1, 2, 3), weight=1)
        button_row.rowconfigure((0, 1), weight=1)

        button1_card = ttk.Frame(button_row, padding=12, style="Surface.TFrame")
        button1_card.grid(row=0, column=0, sticky="nsew", padx=(0, 6), pady=(0, 6))
        button1_card.columnconfigure(0, weight=1)
        ttk.Label(button1_card, text="Prepare calibration workflow and verify baseline setup.", style="Body.TLabel", wraplength=200).grid(
            row=0, column=0, sticky="w"
        )
        ttk.Label(button1_card, text="Analysis Mode Required", style="Pill.TLabel").grid(row=1, column=0, sticky="w", pady=(8, 0))
        self.button1 = ttk.Button(
            button1_card,
            text="Button 1 Calibration",
            style="Action.TButton",
            command=lambda: self._run_automation(BUTTON1_MODULE),
        )
        self.button1.grid(row=2, column=0, sticky="ew", pady=(10, 0))

        button1_1_card = ttk.Frame(button_row, padding=12, style="Surface.TFrame")
        button1_1_card.grid(row=1, column=0, sticky="nsew", padx=(0, 6))
        button1_1_card.columnconfigure(0, weight=1)
        ttk.Label(
            button1_1_card,
            text="Work inside Quantitation to open Std/Unk files, create today's QC file, and reconnect the saved QC.vqcd path.",
            style="Body.TLabel",
            wraplength=200,
        ).grid(row=0, column=0, sticky="w")
        ttk.Label(button1_1_card, text="Quantitation Required", style="Pill.TLabel").grid(row=1, column=0, sticky="w", pady=(8, 0))
        self.button1_1 = ttk.Button(
            button1_1_card,
            text="Button 1-1 File Mgmt",
            style="Action.TButton",
            command=lambda: self._run_automation(BUTTON1_1_MODULE),
        )
        self.button1_1.grid(row=2, column=0, sticky="ew", pady=(10, 0))

        button2_card = ttk.Frame(button_row, padding=12, style="Surface.TFrame")
        button2_card.grid(row=0, column=1, rowspan=2, sticky="nsew", padx=3)
        button2_card.columnconfigure(0, weight=1)
        ttk.Label(button2_card, text="Run the sample measurement flow with the default count of 120.", style="Body.TLabel", wraplength=200).grid(
            row=0, column=0, sticky="w"
        )
        ttk.Label(button2_card, text="Analysis Mode Required", style="Pill.TLabel").grid(row=1, column=0, sticky="w", pady=(8, 0))
        self.button2 = ttk.Button(
            button2_card,
            text="Button 2 Sample",
            style="Action.TButton",
            command=lambda: self._run_automation(BUTTON2_MODULE),
        )
        self.button2.grid(row=2, column=0, sticky="ew", pady=(10, 0))

        button3_card = ttk.Frame(button_row, padding=12, style="Surface.TFrame")
        button3_card.grid(row=0, column=2, rowspan=2, sticky="nsew", padx=3)
        button3_card.columnconfigure(0, weight=1)
        ttk.Label(button3_card, text="Use when the instrument is already in Manual Mode and Quantitation is open.", style="Body.TLabel", wraplength=200).grid(
            row=0, column=0, sticky="w"
        )
        ttk.Label(button3_card, text="Manual Mode Required", style="Pill.TLabel").grid(row=1, column=0, sticky="w", pady=(8, 0))
        ttk.Label(button3_card, text="Quantitation Required", style="Pill.TLabel").grid(row=2, column=0, sticky="w", pady=(6, 0))
        self.button3 = ttk.Button(
            button3_card,
            text="Button 3 Stabilize",
            style="Action.TButton",
            command=lambda: self._run_automation(BUTTON3_MODULE),
        )
        self.button3.grid(row=3, column=0, sticky="ew", pady=(10, 0))

        stop_card = ttk.Frame(button_row, padding=12, style="Surface.TFrame")
        stop_card.grid(row=0, column=3, rowspan=2, sticky="nsew", padx=(6, 0))
        stop_card.columnconfigure(0, weight=1)
        ttk.Label(
            stop_card,
            text=f"Press {STOP_SHORTCUT_LABEL} to stop the current subprocess gracefully.",
            style="Body.TLabel",
            wraplength=200,
        ).grid(row=0, column=0, sticky="w")
        self.stop_button = ttk.Button(
            stop_card,
            text=f"Stop Active Run ({STOP_SHORTCUT_LABEL})",
            style="Stop.TButton",
            command=self._stop_process,
            state="disabled",
        )
        self.stop_button.grid(row=1, column=0, sticky="ew", pady=(10, 0))

    def _bind_shortcuts(self):
        self.root.bind("<Escape>", self._handle_stop_shortcut)

    def _position_window_bottom_right(self):
        self.root.update_idletasks()
        window_width = self.root.winfo_width()
        window_height = self.root.winfo_height()
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x_pos = max(WINDOW_MARGIN, screen_width - window_width - WINDOW_MARGIN)
        y_pos = max(WINDOW_MARGIN, screen_height - window_height - WINDOW_MARGIN - WINDOW_LIFT)
        self.root.geometry(f"{window_width}x{window_height}+{x_pos}+{y_pos}")

    def _append_output(self, text):
        self.console.configure(state="normal")
        self.console.insert("end", text)
        self.console.see("end")
        self.console.configure(state="disabled")

    def _build_command(self, module_name):
        command = [sys.executable, "-m", module_name, "--log-dir", DEFAULT_LOG_DIR]

        if module_name == BUTTON2_MODULE:
            command.extend(["--sample-count", DEFAULT_SAMPLE_COUNT])

        if self.dry_run_var.get():
            command.append("--dry-run")

        return command

    def _run_automation(self, module_name):
        if self.process and self.process.poll() is None:
            messagebox.showwarning(APP_TITLE, "Another automation is already running.")
            return

        command = self._build_command(module_name)
        self._append_output(f"\n$ {' '.join(command)}\n")
        self.status_var.set(f"Running: {module_name.split('.')[-1]}")
        self.status_detail_var.set("Streaming live subprocess output below.")
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
                self.status_detail_var.set("The automation finished successfully.")
            else:
                self.status_var.set(f"Failed: exit code {exit_code}")
                self.status_detail_var.set("Check the log output for the failure point.")
            self._set_running_state(False)
            self.process = None

        self.root.after(100, self._poll_output)

    def _set_running_state(self, is_running):
        button_state = "disabled" if is_running else "normal"
        stop_state = "normal" if is_running else "disabled"
        self.button1.configure(state=button_state)
        self.button1_1.configure(state=button_state)
        self.button2.configure(state=button_state)
        self.button3.configure(state=button_state)
        self.stop_button.configure(state=stop_state)

    def _handle_stop_shortcut(self, _event=None):
        if not self.process or self.process.poll() is not None:
            return "break"
        self._stop_process()
        return "break"

    def _stop_process(self):
        if not self.process or self.process.poll() is not None:
            return
        self.process.terminate()
        self._append_output("[ui] Stop requested.\n")
        self.status_var.set("Stop requested")
        self.status_detail_var.set("Waiting for the running process to terminate.")

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
