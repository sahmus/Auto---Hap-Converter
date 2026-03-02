import os
import shutil
import subprocess
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk


VIDEO_EXTENSIONS = {
    ".mp4",
    ".mov",
    ".mkv",
    ".avi",
    ".m4v",
    ".wmv",
    ".webm",
    ".mpg",
    ".mpeg",
    ".flv",
    ".mts",
    ".m2ts",
}


class HapBatchConverterApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("HAP Batch Converter")
        self.root.geometry("860x600")

        self.source_dir = tk.StringVar()
        self.output_dir = tk.StringVar()
        self.high_quality = tk.BooleanVar(value=True)
        self.include_audio = tk.BooleanVar(value=False)
        self.overwrite_existing = tk.BooleanVar(value=True)
        self.status_text = tk.StringVar(value="Ready.")

        self._configure_style()
        self._build_ui()

    def _configure_style(self) -> None:
        style = ttk.Style(self.root)
        if "clam" in style.theme_names():
            style.theme_use("clam")

        style.configure("Root.TFrame", background="#171A21")
        style.configure("Card.TFrame", background="#212734")
        style.configure("Title.TLabel", background="#171A21", foreground="#E6EDF3", font=("Segoe UI", 16, "bold"))
        style.configure("Body.TLabel", background="#212734", foreground="#E6EDF3", font=("Segoe UI", 10))
        style.configure("Status.TLabel", background="#171A21", foreground="#8B949E", font=("Segoe UI", 10, "italic"))
        style.configure("Action.TButton", font=("Segoe UI", 10, "bold"), padding=8)
        style.configure("Option.TCheckbutton", background="#212734", foreground="#E6EDF3", font=("Segoe UI", 10))

    def _build_ui(self) -> None:
        root_frame = ttk.Frame(self.root, style="Root.TFrame", padding=16)
        root_frame.pack(fill="both", expand=True)

        ttk.Label(root_frame, text="HAP Batch Converter", style="Title.TLabel").pack(anchor="w", pady=(0, 12))

        card = ttk.Frame(root_frame, style="Card.TFrame", padding=16)
        card.pack(fill="both", expand=False)

        self._directory_row(card, "Source folder", self.source_dir, self._pick_source)
        self._directory_row(card, "Output folder", self.output_dir, self._pick_output)

        options = ttk.Frame(card, style="Card.TFrame")
        options.pack(fill="x", pady=(10, 8))

        ttk.Checkbutton(
            options,
            text="Use high quality HAP (hap_q)",
            variable=self.high_quality,
            style="Option.TCheckbutton",
        ).pack(anchor="w", pady=4)

        ttk.Checkbutton(
            options,
            text="Include audio (PCM, slower)",
            variable=self.include_audio,
            style="Option.TCheckbutton",
        ).pack(anchor="w", pady=4)

        ttk.Checkbutton(
            options,
            text="Overwrite existing output files",
            variable=self.overwrite_existing,
            style="Option.TCheckbutton",
        ).pack(anchor="w", pady=4)

        actions = ttk.Frame(card, style="Card.TFrame")
        actions.pack(fill="x", pady=(8, 12))

        self.convert_button = ttk.Button(actions, text="Convert Folder", style="Action.TButton", command=self._start_conversion)
        self.convert_button.pack(side="left")

        ttk.Button(actions, text="Quit", command=self.root.destroy).pack(side="right")

        self.progress = ttk.Progressbar(card, orient="horizontal", mode="determinate", maximum=100)
        self.progress.pack(fill="x", pady=(6, 6))

        log_label = ttk.Label(card, text="Conversion log", style="Body.TLabel")
        log_label.pack(anchor="w", pady=(8, 4))

        self.log_box = tk.Text(card, height=18, bg="#0D1117", fg="#E6EDF3", insertbackground="#E6EDF3", relief="flat")
        self.log_box.pack(fill="both", expand=True)

        ttk.Label(root_frame, textvariable=self.status_text, style="Status.TLabel").pack(anchor="w", pady=(10, 0))

    def _directory_row(self, parent: ttk.Frame, label: str, variable: tk.StringVar, callback) -> None:
        row = ttk.Frame(parent, style="Card.TFrame")
        row.pack(fill="x", pady=6)

        ttk.Label(row, text=label, style="Body.TLabel", width=14).pack(side="left")
        entry = ttk.Entry(row, textvariable=variable)
        entry.pack(side="left", fill="x", expand=True, padx=(8, 8))
        ttk.Button(row, text="Browse", command=callback).pack(side="right")

    def _pick_source(self) -> None:
        selected = filedialog.askdirectory(title="Select source folder")
        if selected:
            self.source_dir.set(selected)

    def _pick_output(self) -> None:
        selected = filedialog.askdirectory(title="Select output folder")
        if selected:
            self.output_dir.set(selected)

    def _log(self, message: str) -> None:
        self.log_box.insert("end", f"{message}\n")
        self.log_box.see("end")
        self.root.update_idletasks()

    def _set_status(self, message: str) -> None:
        self.status_text.set(message)
        self.root.update_idletasks()

    def _start_conversion(self) -> None:
        if not self.source_dir.get().strip() or not self.output_dir.get().strip():
            messagebox.showwarning("Missing folder", "Please choose both source and output folders.")
            return

        if shutil.which("ffmpeg") is None:
            messagebox.showerror("ffmpeg not found", "ffmpeg was not found in PATH. Install ffmpeg first.")
            return

        self.convert_button.config(state="disabled")
        self.progress["value"] = 0
        self.log_box.delete("1.0", "end")

        worker = threading.Thread(target=self._convert_folder, daemon=True)
        worker.start()

    def _convert_folder(self) -> None:
        source = Path(self.source_dir.get()).expanduser().resolve()
        output = Path(self.output_dir.get()).expanduser().resolve()

        if not source.exists():
            self._set_status("Source folder not found.")
            self._log(f"ERROR: Source folder does not exist: {source}")
            self.convert_button.config(state="normal")
            return

        output.mkdir(parents=True, exist_ok=True)

        videos = [
            path
            for path in sorted(source.iterdir())
            if path.is_file() and path.suffix.lower() in VIDEO_EXTENSIONS
        ]

        if not videos:
            self._set_status("No videos found in source folder.")
            self._log("No supported video files were found in the selected source folder.")
            self.convert_button.config(state="normal")
            return

        total = len(videos)
        hap_format = "hap_q" if self.high_quality.get() else "hap"

        self._set_status(f"Converting {total} file(s)...")
        self._log(f"Using HAP format: {hap_format}")
        self._log("Video settings: pix_fmt=rgba, chunks=4, compressor=snappy")
        self._log("Resolution handling: pad to nearest multiple of 4 for HAP compatibility")
        self._log(f"Include audio (PCM): {'yes' if self.include_audio.get() else 'no'}")
        self._log(f"Existing output handling: {'overwrite' if self.overwrite_existing.get() else 'skip'}")

        succeeded = 0
        skipped = 0
        for index, video_path in enumerate(videos, start=1):
            out_path = output / f"{video_path.stem}_hap.mov"
            cmd = [
                "ffmpeg",
                "-y" if self.overwrite_existing.get() else "-n",
                "-hide_banner",
                "-loglevel",
                "error",
                "-i",
                str(video_path),
                "-c:v",
                "hap",
                "-format",
                hap_format,
                "-chunks",
                "4",
                "-compressor",
                "snappy",
                "-pix_fmt",
                "rgba",
                "-vf",
                "pad=ceil(iw/4)*4:ceil(ih/4)*4",
            ]
            if self.include_audio.get():
                cmd.extend(["-c:a", "pcm_s16le"])
            else:
                cmd.append("-an")

            cmd.append(str(out_path))

            if out_path.exists() and not self.overwrite_existing.get():
                skipped += 1
                self._log(f"[{index}/{total}] Skipping existing file: {out_path.name}")
                self.progress["value"] = int((index / total) * 100)
                self.root.update_idletasks()
                continue

            self._log(f"[{index}/{total}] Converting: {video_path.name}")
            result = subprocess.run(cmd, capture_output=True, text=True)

            if result.returncode == 0:
                succeeded += 1
                self._log(f"  ✓ Saved: {out_path.name}")
            else:
                self._log(f"  ✗ Failed: {video_path.name}")
                if result.stderr:
                    self._log(result.stderr.strip())

            self.progress["value"] = int((index / total) * 100)
            self.root.update_idletasks()

        self._set_status(
            f"Done. {succeeded}/{total} file(s) converted, {skipped} skipped."
        )
        self._log(f"Conversion finished. Converted: {succeeded}, skipped: {skipped}.")
        self.convert_button.config(state="normal")


def main() -> None:
    root = tk.Tk()
    app = HapBatchConverterApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
