#!/usr/bin/env python3
"""Legal Document Converter — Tkinter GUI."""

import threading
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext, ttk
from pathlib import Path

from config import validate_config
from processing.llm_client import LLMClient
from processing.quality_checker import reset_warnings, write_quality_report
from main import discover_files, process_file
from utils.logger import get_logger

logger = get_logger(__name__)


class ConverterApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Legal Document Converter")
        self.geometry("680x520")
        self.resizable(False, False)

        self._build_ui()
        self._running = False

    def _build_ui(self):
        pad = {"padx": 12, "pady": 4}

        # --- Input ---
        frame_input = ttk.LabelFrame(self, text="Input")
        frame_input.pack(fill="x", **pad)

        self.input_var = tk.StringVar()
        ttk.Entry(frame_input, textvariable=self.input_var, width=60).pack(
            side="left", padx=(8, 4), pady=6, fill="x", expand=True,
        )
        ttk.Button(frame_input, text="Browse File", command=self._browse_file).pack(
            side="left", padx=2, pady=6,
        )
        ttk.Button(frame_input, text="Browse Folder", command=self._browse_folder).pack(
            side="left", padx=(2, 8), pady=6,
        )

        # --- Output ---
        frame_output = ttk.LabelFrame(self, text="Output Folder")
        frame_output.pack(fill="x", **pad)

        self.output_var = tk.StringVar(value=str(Path.cwd() / "output"))
        ttk.Entry(frame_output, textvariable=self.output_var, width=60).pack(
            side="left", padx=(8, 4), pady=6, fill="x", expand=True,
        )
        ttk.Button(frame_output, text="Browse", command=self._browse_output).pack(
            side="left", padx=(2, 8), pady=6,
        )

        # --- Options ---
        frame_opts = ttk.LabelFrame(self, text="Options")
        frame_opts.pack(fill="x", **pad)

        ttk.Label(frame_opts, text="Format:").pack(side="left", padx=(8, 4), pady=6)
        self.format_var = tk.StringVar(value="docx")
        fmt_combo = ttk.Combobox(
            frame_opts, textvariable=self.format_var,
            values=["txt", "docx", "pdf", "both", "all"],
            state="readonly", width=8,
        )
        fmt_combo.pack(side="left", padx=4, pady=6)

        ttk.Label(frame_opts, text="Workers:").pack(side="left", padx=(16, 4), pady=6)
        self.workers_var = tk.IntVar(value=1)
        ttk.Spinbox(frame_opts, from_=1, to=8, textvariable=self.workers_var, width=4).pack(
            side="left", padx=(4, 8), pady=6,
        )

        # --- Convert button ---
        self.convert_btn = ttk.Button(self, text="Convert", command=self._start_conversion)
        self.convert_btn.pack(pady=8)

        # --- Progress ---
        self.progress = ttk.Progressbar(self, mode="indeterminate", length=640)
        self.progress.pack(padx=12, pady=(0, 4))

        # --- Log output ---
        self.log_area = scrolledtext.ScrolledText(self, height=12, state="disabled", font=("Courier", 10))
        self.log_area.pack(fill="both", expand=True, padx=12, pady=(0, 12))

    def _browse_file(self):
        path = filedialog.askopenfilename(
            filetypes=[("Legal Documents", "*.pdf *.docx *.txt"), ("All Files", "*.*")],
        )
        if path:
            self.input_var.set(path)

    def _browse_folder(self):
        path = filedialog.askdirectory()
        if path:
            self.input_var.set(path)

    def _browse_output(self):
        path = filedialog.askdirectory()
        if path:
            self.output_var.set(path)

    def _log(self, msg: str):
        self.log_area.configure(state="normal")
        self.log_area.insert("end", msg + "\n")
        self.log_area.see("end")
        self.log_area.configure(state="disabled")

    def _start_conversion(self):
        if self._running:
            return

        input_path = self.input_var.get().strip()
        output_path = self.output_var.get().strip()

        if not input_path:
            messagebox.showwarning("Missing Input", "Please select an input file or folder.")
            return

        self._running = True
        self.convert_btn.configure(state="disabled")
        self.progress.start(10)
        self.log_area.configure(state="normal")
        self.log_area.delete("1.0", "end")
        self.log_area.configure(state="disabled")

        thread = threading.Thread(
            target=self._run_conversion,
            args=(input_path, output_path),
            daemon=True,
        )
        thread.start()

    def _run_conversion(self, input_path: str, output_path: str):
        try:
            validate_config()
        except RuntimeError as exc:
            self.after(0, lambda: self._finish(str(exc), error=True))
            return

        fmt = self.format_var.get()
        output_dir = Path(output_path)

        try:
            files = discover_files(input_path)
        except (ValueError, FileNotFoundError) as exc:
            self.after(0, lambda: self._finish(str(exc), error=True))
            return

        client = LLMClient()
        total = len(files)
        succeeded = 0
        failed = 0
        reset_warnings()

        for idx, filepath in enumerate(files, 1):
            self.after(0, lambda i=idx, n=filepath.name: self._log(f"[{i}/{total}] Processing: {n}"))
            try:
                process_file(filepath, output_dir, fmt, client)
                succeeded += 1
            except Exception as exc:
                failed += 1
                self.after(0, lambda n=filepath.name, e=exc: self._log(f"  FAILED: {n} — {e}"))

        report = write_quality_report(output_dir)
        if report:
            self.after(0, lambda p=report: self._log(f"Quality report: {p}"))

        summary = f"Done. {succeeded}/{total} succeeded, {failed} failed."
        self.after(0, lambda: self._finish(summary, error=failed > 0))

    def _finish(self, msg: str, error: bool = False):
        self.progress.stop()
        self._running = False
        self.convert_btn.configure(state="normal")
        self._log(msg)
        if error:
            messagebox.showerror("Error", msg)
        else:
            messagebox.showinfo("Complete", msg)


def main():
    app = ConverterApp()
    app.mainloop()


if __name__ == "__main__":
    main()
