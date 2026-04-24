# SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0
# Copyright (c) 2026 Bruno Muller
# https://polyformproject.org/licenses/noncommercial/1.0.0

import tkinter as tk
from tkinter import filedialog, messagebox
import os
import threading

try:
    from tkinterdnd2 import DND_FILES, TkinterDnD
    _DND_AVAILABLE = True
except ImportError:
    _DND_AVAILABLE = False

from shape_extractor import ShapeExtractor
from texture_extractor import TextureExtractor


class MainWindow:

    def __init__(self, root: tk.Tk, input_file: str = "", output_dir: str = ""):
        self._root = root
        root.title("kuju2gltf")
        root.resizable(True, False)

        pad = {"padx": 6, "pady": 4}

        # --- Input file row ---
        frame_in = tk.Frame(root)
        frame_in.pack(fill=tk.X, **pad)

        tk.Label(frame_in, text="Input file:", width=12, anchor="w").pack(side=tk.LEFT)

        text_frame = tk.Frame(frame_in)
        text_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 4))

        yscroll = tk.Scrollbar(text_frame, orient=tk.VERTICAL)
        yscroll.pack(side=tk.RIGHT, fill=tk.Y)

        entry_in = tk.Text(text_frame, height=4, wrap=tk.NONE, yscrollcommand=yscroll.set)
        entry_in.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        yscroll.config(command=entry_in.yview)

        if input_file:
            entry_in.insert("1.0", input_file)

        if _DND_AVAILABLE:
            entry_in.drop_target_register(DND_FILES)
            entry_in.dnd_bind("<<Drop>>", lambda e: self._on_drop_file(e))

        tk.Button(frame_in, text="Browse…", command=self._browse_input).pack(side=tk.LEFT)

        # --- Output directory row ---
        frame_out = tk.Frame(root)
        frame_out.pack(fill=tk.X, **pad)

        tk.Label(frame_out, text="Output dir:", width=12, anchor="w").pack(side=tk.LEFT)

        self._output_var = tk.StringVar(value=output_dir)
        entry_out = tk.Entry(frame_out, textvariable=self._output_var)
        entry_out.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 4))

        if _DND_AVAILABLE:
            entry_out.drop_target_register(DND_FILES)
            entry_out.dnd_bind("<<Drop>>", lambda e: self._on_drop_dir(e, self._output_var))

        tk.Button(frame_out, text="Browse…", command=self._browse_output).pack(side=tk.LEFT)

        # --- Convert button ---
        tk.Button(root, text="Convert", command=self._convert, height=2).pack(
            fill=tk.X, **pad
        )

        # --- Status label ---
        self._status_var = tk.StringVar(value="Ready.")
        tk.Label(root, textvariable=self._status_var, anchor="w", fg="gray").pack(
            fill=tk.X, padx=6, pady=(0, 6)
        )

        # Keep references to lockable widgets
        self._btn_browse_in = frame_in.winfo_children()[-1]
        self._btn_browse_out = frame_out.winfo_children()[-1]
        self._btn_convert = root.winfo_children()[-2]  # button before status label
        self._entry_in = entry_in
        self._entry_out = entry_out
        self._loading_after_id = None
        self._loading_frames = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
        self._loading_idx = 0

    # ------------------------------------------------------------------
    # Drag & drop helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _parse_dnd_paths(raw: str) -> list:
        """Parse space-separated file paths from tkinterdnd2; handles brace-quoted paths."""
        paths = []
        raw = raw.strip()
        i = 0
        while i < len(raw):
            if raw[i] == '{':
                end = raw.find('}', i + 1)
                if end == -1:
                    paths.append(raw[i + 1:])
                    break
                paths.append(raw[i + 1:end])
                i = end + 1
            else:
                end = raw.find(' ', i)
                if end == -1:
                    paths.append(raw[i:])
                    break
                paths.append(raw[i:end])
                i = end
            while i < len(raw) and raw[i] == ' ':
                i += 1
        return [p for p in paths if p]

    def _on_drop_file(self, event):
        paths = self._parse_dnd_paths(event.data)
        self._entry_in.delete("1.0", "end")
        self._entry_in.insert("1.0", "\n".join(paths))

    def _on_drop_dir(self, event, var: tk.StringVar):
        paths = self._parse_dnd_paths(event.data)
        path = paths[0] if paths else ""
        if os.path.isfile(path):
            path = os.path.dirname(path)
        var.set(path)

    # ------------------------------------------------------------------
    # Browse dialogs
    # ------------------------------------------------------------------

    def _browse_input(self):
        paths = filedialog.askopenfilenames(
            title="Select input file(s)",
            filetypes=[("Shape / ACE files", "*.s *.ace *.dds"), ("All files", "*.*")],
        )
        if paths:
            self._entry_in.delete("1.0", "end")
            self._entry_in.insert("1.0", "\n".join(paths))

    def _browse_output(self):
        path = filedialog.askdirectory(title="Select output directory")
        if path:
            self._output_var.set(path)

    # ------------------------------------------------------------------
    # Convert
    # ------------------------------------------------------------------

    def _set_ui_locked(self, locked: bool):
        state = tk.DISABLED if locked else tk.NORMAL
        for widget in (self._btn_browse_in, self._btn_browse_out,
                       self._btn_convert, self._entry_in, self._entry_out):
            widget.config(state=state)

    def _start_loading(self):
        self._loading_idx = 0
        self._tick_loading()

    def _tick_loading(self):
        frame = self._loading_frames[self._loading_idx % len(self._loading_frames)]
        self._status_var.set(f"{frame}  Converting…")
        self._loading_idx += 1
        self._loading_after_id = self._root.after(100, self._tick_loading)

    def _stop_loading(self):
        if self._loading_after_id is not None:
            self._root.after_cancel(self._loading_after_id)
            self._loading_after_id = None

    def _convert(self):
        content = self._entry_in.get("1.0", "end-1c").strip()
        input_files = [f.strip() for f in content.splitlines() if f.strip()]
        output_dir = self._output_var.get().strip()

        if not input_files:
            messagebox.showwarning("Missing input", "Please select at least one input file.")
            return
        missing = [f for f in input_files if not os.path.isfile(f)]
        if missing:
            messagebox.showerror("File not found", "File(s) not found:\n" + "\n".join(missing))
            return
        if not output_dir:
            messagebox.showwarning("Missing output", "Please select an output directory.")
            return
        if not os.path.isdir(output_dir):
            try:
                os.makedirs(output_dir)
            except OSError as e:
                messagebox.showerror("Cannot create directory", f"Failed to create output directory:\n{e}")
                return

        self._set_ui_locked(True)
        self._start_loading()

        def _run():
            errors = []
            for input_file in input_files:
                try:
                    ext = os.path.splitext(input_file)[1].lower()
                    if ext == ".s":
                        extractor = ShapeExtractor(input_file, output_dir, "orts")
                        extractor.run()
                    elif ext == ".dds":
                        tex = TextureExtractor(output_dir)
                        tex.save_png(input_file, overwrite=True)
                    elif ext == ".ace":
                        tex = TextureExtractor(output_dir)
                        tex.save_png(input_file, overwrite=True)
                        tex.save_dds(input_file, overwrite=True)
                    else:
                        errors.append(f"{os.path.basename(input_file)}: unsupported type '{ext}'")
                except Exception as e:
                    errors.append(f"{os.path.basename(input_file)}: {e}")
            self._root.after(0, lambda: self._on_convert_done(errors))

        threading.Thread(target=_run, daemon=True).start()

    def _on_convert_done(self, errors):
        self._stop_loading()
        self._set_ui_locked(False)
        if not errors:
            self._status_var.set("Done.")
        else:
            self._status_var.set(f"{len(errors)} error(s).")
            messagebox.showerror("Conversion error(s)", "\n".join(errors))


def main(input_file: str = "", output_dir: str = ""):
    if _DND_AVAILABLE:
        root = TkinterDnD.Tk()
    else:
        root = tk.Tk()
    app = MainWindow(root, input_file=input_file, output_dir=output_dir)
    root.mainloop()


if __name__ == "__main__":
    main()
