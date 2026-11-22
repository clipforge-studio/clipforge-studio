import os, re, shutil, threading, subprocess, queue, tkinter as tk, tempfile
from tkinter import ttk, messagebox, filedialog
from pathlib import Path

APP = "ClipForge Studio"

def locate(name):
    exe = name + ".exe"
    for p in [Path(__file__).parent / exe, Path(__file__).parent / "ffmpeg" / "bin" / exe, Path.home() / "Downloads" / exe]:
        if p.is_file():
            return str(p)
    return shutil.which(exe) or shutil.which(name)

def clean(s):
    return re.sub(r'[<>:"/\\\\|?*]', "_", s).strip(" ._")[:140] or "video"

def ffpath(path):
    return str(path).replace("\\", "/").replace(":", r"\:").replace("'", r"\'")

class App:
    def __init__(self, root):
        self.root = root
        root.title(APP)
        root.geometry("1060x760")
        root.minsize(900, 650)
        root.configure(bg="#111827")
        self.events = queue.Queue()
        self.jobs = []
        self.files = {}
        self.busy = False
        self.out = str(Path.home() / "Downloads")
        self.ytdlp = locate("yt-dlp")
        self.ffmpeg = locate("ffmpeg")
        self.format = tk.StringVar(value="Landscape")
        self.status = tk.StringVar(value="Ready — download first, then choose how to split or edit.")
        self._style()
        self._build()
        root.after(100, self.poll)

    def _style(self):
        st = ttk.Style()
        st.theme_use("clam")
        st.configure("TProgressbar", troughcolor="#263244", background="#22c55e")
        st.configure("Treeview", background="#1f2937", foreground="white", fieldbackground="#1f2937", rowheight=29)
        st.configure("Treeview.Heading", background="#374151", foreground="white")
        st.map("Treeview", background=[("selected", "#1d4ed8")])

    def button(self, parent, text, command, color="#2563eb"):
        return tk.Button(parent, text=text, command=command, bg=color, fg="white", activebackground=color,
                         activeforeground="white", relief="flat", bd=0, padx=14, pady=9,
                         font=("Segoe UI", 9, "bold"), cursor="hand2")

    def _build(self):
        head = tk.Frame(self.root, bg="#111827")
        head.pack(fill="x", padx=22, pady=(18, 10))
        tk.Label(head, text=APP, bg="#111827", fg="white", font=("Segoe UI", 23, "bold")).pack(anchor="w")
        tk.Label(head, text="Download first • Split when you choose • Subtitle and editing tools",
                 bg="#111827", fg="#94a3b8", font=("Segoe UI", 10)).pack(anchor="w")

        panel = tk.Frame(self.root, bg="#1f2937")
        panel.pack(fill="x", padx=22, pady=7)
        tk.Label(panel, text="VIDEO LINK", bg="#1f2937", fg="#cbd5e1").pack(anchor="w", padx=14, pady=(12, 5))
        row = tk.Frame(panel, bg="#1f2937")
        row.pack(fill="x", padx=14, pady=(0, 12))
        self.url = tk.StringVar()
        tk.Entry(row, textvariable=self.url, bg="#0f172a", fg="white", insertbackground="white",
                 relief="flat", font=("Segoe UI", 11)).pack(side="left", fill="x", expand=True, ipady=9, padx=(0, 7))
        self.button(row, "Paste", self.paste, "#475569").pack(side="left")
        row = tk.Frame(panel, bg="#1f2937")
        row.pack(fill="x", padx=14, pady=(0, 13))
        self.button(row, "Add to Queue", self.add).pack(side="left")
        self.button(row, "Download", self.download, "#15803d").pack(side="left", padx=7)
        self.button(row, "Clear Queue", self.clear, "#475569").pack(side="left")

        bar = tk.Frame(self.root, bg="#111827")
        bar.pack(fill="x", padx=22, pady=9)
        tk.Label(bar, text="OUTPUT FORMAT", bg="#111827", fg="#cbd5e1").pack(side="left")
        self.format_box = ttk.Combobox(bar, textvariable=self.format, values=["Landscape", "Vertical 9:16", "Both"], state="readonly", width=18)
        self.format_box.pack(side="left", padx=9)
        self.button(bar, "Change Output Folder", self.change, "#475569").pack(side="right")
        self.folder_label = tk.Label(self.root, text="Output: " + self.out, bg="#111827", fg="#94a3b8", anchor="w")
        self.folder_label.pack(fill="x", padx=22)

        tk.Label(self.root, text="DOWNLOAD LIBRARY — select a completed video to split or edit",
                 bg="#111827", fg="#cbd5e1").pack(anchor="w", padx=22, pady=(14, 5))
        self.tree = ttk.Treeview(self.root, columns=("name", "status", "file"), show="headings", height=9)
        self.tree.heading("name", text="Video")
        self.tree.heading("status", text="Status")
        self.tree.heading("file", text="Saved file")
        self.tree.column("name", width=340)
        self.tree.column("status", width=130)
        self.tree.column("file", width=500)
        self.tree.pack(fill="both", expand=True, padx=22)
        actions = tk.Frame(self.root, bg="#111827")
        actions.pack(fill="x", padx=22, pady=10)
        self.button(actions, "Split Selected", self.split_dialog, "#7c3aed").pack(side="left")
        self.button(actions, "Open Full Editor", self.editor_dialog, "#0f766e").pack(side="left", padx=7)
        self.button(actions, "Preview Video", self.preview, "#475569").pack(side="left")
        self.pb = ttk.Progressbar(self.root, maximum=100)
        self.pb.pack(fill="x", padx=22, pady=(3, 7))
        tk.Label(self.root, textvariable=self.status, bg="#111827", fg="#cbd5e1", anchor="w").pack(fill="x", padx=22)
        self.log = tk.Text(self.root, height=6, bg="#0b1220", fg="#94a3b8", font=("Consolas", 8), state="disabled")
        self.log.pack(fill="x", padx=22, pady=(8, 14))

    def paste(self):
        try:
            self.url.set(self.root.clipboard_get().strip())
        except tk.TclError:
            self.status.set("Clipboard is empty.")

    def add(self):
        url = self.url.get().strip()
        if not url.startswith(("https://", "http://")):
            messagebox.showwarning(APP, "Paste a valid video URL.")
            return
        if any(item[0] == url for item in self.jobs):
            return
        iid = self.tree.insert("", "end", values=(url[:90], "Queued", ""))
        self.jobs.append((url, iid))
        self.url.set("")

    def clear(self):
        if self.busy:
            return
        self.jobs.clear()
        for iid in self.tree.get_children():
            self.tree.delete(iid)

    def change(self):
        folder = filedialog.askdirectory(initialdir=self.out)
        if folder:
            self.out = folder
            self.folder_label.config(text="Output: " + folder)

    def selected(self):
        chosen = self.tree.selection()
        if not chosen:
            messagebox.showinfo(APP, "Select a downloaded video first.")
            return None
        iid = chosen[0]
        path = self.files.get(iid)
        if not path or not os.path.isfile(path):
            messagebox.showinfo(APP, "This item is not downloaded yet. Click Download first.")
            return None
        return path

    def download(self):
        if self.busy:
            return
        if not self.jobs:
            messagebox.showinfo(APP, "Add one or more URLs first.")
            return
        self.ytdlp, self.ffmpeg = locate("yt-dlp"), locate("ffmpeg")
        if not self.ytdlp or not self.ffmpeg:
            messagebox.showerror(APP, "Setup required: yt-dlp.exe and ffmpeg.exe must be available. See README.md.")
            return
        self.busy = True
        threading.Thread(target=self.download_worker, daemon=True).start()

    def run_command(self, cmd):
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
                                encoding="utf-8", errors="replace",
                                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        for line in proc.stdout:
            line = line.rstrip()
            if line:
                self.events.put(("log", line))
                match = re.search(r"(\d+(?:\.\d+)?)%", line)
                if match:
                    self.events.put(("progress", float(match.group(1))))
        return proc.wait()

    def download_worker(self):
        try:
            os.makedirs(self.out, exist_ok=True)
            for index, (url, iid) in enumerate(list(self.jobs), 1):
                self.events.put(("row", iid, url[:90], "Downloading", ""))
                self.events.put(("status", "Downloading video " + str(index)))
                work = os.path.join(self.out, "_ClipForge_Work", "job_" + str(index).zfill(3))
                os.makedirs(work, exist_ok=True)
                template = os.path.join(work, "%(title).150B [%(id)s].%(ext)s")
                code = self.run_command([self.ytdlp, "--no-playlist", "--newline", "-f", "bv*+ba/b",
                                         "--merge-output-format", "mp4", "--ffmpeg-location",
                                         os.path.dirname(self.ffmpeg), "-o", template, url])
                if code:
                    self.events.put(("row", iid, url[:90], "Download failed", ""))
                    continue
                media = [os.path.join(work, name) for name in os.listdir(work)
                         if name.lower().endswith((".mp4", ".mkv", ".webm", ".mov"))]
                if not media:
                    self.events.put(("row", iid, url[:90], "No media found", ""))
                    continue
                source = max(media, key=os.path.getmtime)
                self.events.put(("downloaded", iid, source, os.path.basename(source)))
            self.events.put(("status", "Downloads finished. Select a video, then choose Split or Open Full Editor."))
        except Exception as exc:
            self.events.put(("log", "ERROR: " + str(exc)))
            self.events.put(("status", "An error occurred. Check the log."))
        finally:
            self.events.put(("finished",))

    def split_dialog(self):
        source = self.selected()
        if not source:
            return
        win = tk.Toplevel(self.root)
        win.title("Split Video")
        win.configure(bg="#1f2937")
        win.resizable(False, False)
        win.transient(self.root)
        win.grab_set()
        tk.Label(win, text="Choose how to split", bg="#1f2937", fg="white",
                 font=("Segoe UI", 15, "bold")).pack(anchor="w", padx=18, pady=(16, 10))
        mode = tk.StringVar(value="auto")
        tk.Radiobutton(win, text="Automatic split — choose segment duration", variable=mode, value="auto",
                       bg="#1f2937", fg="white", selectcolor="#111827", activebackground="#1f2937").pack(anchor="w", padx=18)
        row = tk.Frame(win, bg="#1f2937")
        row.pack(anchor="w", padx=38, pady=7)
        minutes = tk.StringVar(value="5")
        tk.Label(row, text="Part duration (minutes):", bg="#1f2937", fg="#cbd5e1").pack(side="left")
        ttk.Entry(row, textvariable=minutes, width=8).pack(side="left", padx=8)
        tk.Radiobutton(win, text="Manual split — export one selected time range", variable=mode, value="manual",
                       bg="#1f2937", fg="white", selectcolor="#111827", activebackground="#1f2937").pack(anchor="w", padx=18, pady=(8, 3))
        times = tk.Frame(win, bg="#1f2937")
        times.pack(anchor="w", padx=38, pady=7)
        start = tk.StringVar(value="00:00:00")
        end = tk.StringVar(value="00:01:00")
        tk.Label(times, text="Start (HH:MM:SS)", bg="#1f2937", fg="#cbd5e1").grid(row=0, column=0, sticky="w")
        tk.Label(times, text="End (HH:MM:SS)", bg="#1f2937", fg="#cbd5e1").grid(row=0, column=1, sticky="w", padx=10)
        ttk.Entry(times, textvariable=start, width=14).grid(row=1, column=0, sticky="w")
        ttk.Entry(times, textvariable=end, width=14).grid(row=1, column=1, sticky="w", padx=10)
        tk.Label(win, text="Output format: " + self.format.get(), bg="#1f2937", fg="#94a3b8").pack(anchor="w", padx=18, pady=8)
        def go():
            try:
                if mode.get() == "auto":
                    duration = float(minutes.get()) * 60
                    if duration <= 0 or duration > 86400:
                        raise ValueError()
                    args = ("auto", duration, "", "")
                else:
                    a, b = self.to_seconds(start.get()), self.to_seconds(end.get())
                    if b <= a:
                        raise ValueError()
                    args = ("manual", 0, start.get(), end.get())
            except Exception:
                messagebox.showerror(APP, "Enter a valid positive duration and valid time values.", parent=win)
                return
            win.destroy()
            self.process_video(source, *args)
        self.button(win, "Create Parts", go, "#7c3aed").pack(anchor="e", padx=18, pady=16)

    def to_seconds(self, value):
        parts = value.strip().split(":")
        if len(parts) != 3:
            raise ValueError()
        h, m, s = [float(x) for x in parts]
        if min(h, m, s) < 0 or m >= 60 or s >= 60:
            raise ValueError()
        return h * 3600 + m * 60 + s

    def process_video(self, source, mode, duration, start, end):
        if self.busy:
            messagebox.showinfo(APP, "Wait for the current task to finish.")
            return
        self.busy = True
        threading.Thread(target=self.split_worker, args=(source, mode, duration, start, end), daemon=True).start()

    def split_worker(self, source, mode, duration, start, end):
        try:
            stem = clean(Path(source).stem)
            dest = os.path.join(self.out, stem + "_Clips")
            os.makedirs(dest, exist_ok=True)
            formats = ["Landscape", "Vertical 9:16"] if self.format.get() == "Both" else [self.format.get()]
            for fmt in formats:
                folder = os.path.join(dest, "Landscape" if fmt == "Landscape" else "Vertical_9x16")
                os.makedirs(folder, exist_ok=True)
                if mode == "manual":
                    output = os.path.join(folder, stem + "_Manual.mp4")
                    self.events.put(("status", "Exporting manual clip: " + fmt))
                    self.encode_clip(source, output, start, end, fmt, None, None, "None")
                else:
                    self.events.put(("status", "Splitting " + fmt + " into " + str(round(duration / 60, 2)) + " minute parts"))
                    self.encode_segments(source, folder, duration, fmt)
            self.events.put(("status", "Split complete: " + dest))
        except Exception as exc:
            self.events.put(("log", "ERROR: " + str(exc)))
            self.events.put(("status", "Split failed. Check the log."))
        finally:
            self.events.put(("finished",))

    def video_filter(self, fmt, effect="None", text="", font_size=48, position="Bottom"):
        filters = []
        if fmt == "Vertical 9:16":
            filters.append("split=2[bg][fg];[bg]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,boxblur=24:8[blur];[fg]scale=1080:1920:force_original_aspect_ratio=decrease[front];[blur][front]overlay=(W-w)/2:(H-h)/2,setsar=1")
        else:
            filters.append("scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2,setsar=1")
        if effect == "Black & White":
            filters.append("hue=s=0")
        elif effect == "Warm":
            filters.append("colorbalance=rs=0.08:gs=0.02:bs=-0.08")
        elif effect == "Vintage":
            filters.append("curves=vintage")
        elif effect == "Sharpen":
            filters.append("unsharp=5:5:0.8:3:3:0.4")
        if text.strip():
            y = "h-th-70" if position == "Bottom" else ("70" if position == "Top" else "(h-th)/2")
            safe = text.replace("\\", "\\\\\\\\").replace(":", "\\\\:").replace("'", "\\\\'").replace("%", "\\\\%").replace(",", "\\\\,")
            filters.append("drawtext=text='" + safe + "':fontcolor=white:fontsize=" + str(int(font_size)) +
                           ":borderw=3:bordercolor=black:x=(w-text_w)/2:y=" + y)
        return ",".join(filters)

    def encode_segments(self, source, folder, duration, fmt):
        output = os.path.join(folder, "Part_%03d.mp4")
        vf = self.video_filter(fmt)
        cmd = [self.ffmpeg, "-y", "-i", source, "-vf" if fmt == "Landscape" else "-filter_complex", vf,
               "-map", "0:v:0", "-map", "0:a?", "-c:v", "libx264", "-preset", "veryfast", "-crf", "22",
               "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "160k", "-f", "segment",
               "-segment_time", str(duration), "-reset_timestamps", "1", "-segment_format", "mp4", output]
        code = self.run_command(cmd)
        if code:
            raise RuntimeError("FFmpeg failed while creating " + fmt + " parts.")

    def encode_clip(self, source, output, start, end, fmt, subtitle, effect, text):
        vf = self.video_filter(fmt, effect or "None", text or "")
        cmd = [self.ffmpeg, "-y", "-ss", start, "-to", end, "-i", source]
        if subtitle:
            vf += ",subtitles='" + ffpath(subtitle) + "'"
        cmd += ["-vf" if fmt == "Landscape" else "-filter_complex", vf,
                "-map", "0:v:0", "-map", "0:a?", "-c:v", "libx264", "-preset", "veryfast",
                "-crf", "22", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "160k",
                "-movflags", "+faststart", output]
        if self.run_command(cmd):
            raise RuntimeError("FFmpeg could not export this clip.")

    def editor_dialog(self):
        source = self.selected()
        if not source:
            return
        win = tk.Toplevel(self.root)
        win.title("ClipForge Studio — Full Editor")
        win.geometry("560x570")
        win.configure(bg="#1f2937")
        win.transient(self.root)
        win.grab_set()
        tk.Label(win, text="Clip Editor", bg="#1f2937", fg="white", font=("Segoe UI", 18, "bold")).pack(anchor="w", padx=18, pady=(16, 3))
        tk.Label(win, text=Path(source).name, bg="#1f2937", fg="#94a3b8", wraplength=510).pack(anchor="w", padx=18, pady=(0, 12))
        form = tk.Frame(win, bg="#1f2937")
        form.pack(fill="x", padx=18)
        start, end = tk.StringVar(value="00:00:00"), tk.StringVar(value="00:00:30")
        subtitle = tk.StringVar()
        text = tk.StringVar()
        effect = tk.StringVar(value="None")
        position = tk.StringVar(value="Bottom")
        size = tk.StringVar(value="48")
        def field(label, var, row, width=34):
            tk.Label(form, text=label, bg="#1f2937", fg="#cbd5e1").grid(row=row, column=0, sticky="w", pady=6)
            ttk.Entry(form, textvariable=var, width=width).grid(row=row, column=1, sticky="ew", pady=6)
        field("Start time (HH:MM:SS)", start, 0)
        field("End time (HH:MM:SS)", end, 1)
        tk.Label(form, text="Effect preset", bg="#1f2937", fg="#cbd5e1").grid(row=2, column=0, sticky="w", pady=6)
        ttk.Combobox(form, textvariable=effect, values=["None", "Black & White", "Warm", "Vintage", "Sharpen"], state="readonly").grid(row=2, column=1, sticky="ew")
        field("Text / subtitle overlay", text, 3)
        tk.Label(form, text="Text position", bg="#1f2937", fg="#cbd5e1").grid(row=4, column=0, sticky="w", pady=6)
        ttk.Combobox(form, textvariable=position, values=["Top", "Center", "Bottom"], state="readonly").grid(row=4, column=1, sticky="ew")
        field("Text size", size, 5)
        tk.Label(form, text="Subtitle file (.srt)", bg="#1f2937", fg="#cbd5e1").grid(row=6, column=0, sticky="w", pady=6)
        subrow = tk.Frame(form, bg="#1f2937")
        subrow.grid(row=6, column=1, sticky="ew")
        ttk.Entry(subrow, textvariable=subtitle).pack(side="left", fill="x", expand=True)
        self.button(subrow, "Browse", lambda: subtitle.set(filedialog.askopenfilename(filetypes=[("Subtitle files", "*.srt")]) or subtitle.get()), "#475569").pack(side="left", padx=5)
        form.columnconfigure(1, weight=1)
        tk.Label(win, text="Exports one edited MP4 clip. Subtitle files are burned into the video.",
                 bg="#1f2937", fg="#94a3b8", wraplength=510).pack(anchor="w", padx=18, pady=12)
        def export():
            try:
                a, b = self.to_seconds(start.get()), self.to_seconds(end.get())
                if b <= a or not 8 <= int(size.get()) <= 160:
                    raise ValueError()
                if subtitle.get() and not os.path.isfile(subtitle.get()):
                    raise ValueError()
            except Exception:
                messagebox.showerror(APP, "Check start/end time, text size, and subtitle file.", parent=win)
                return
            win.destroy()
            if self.busy:
                messagebox.showinfo(APP, "Wait for the current task to finish.")
                return
            output = os.path.join(self.out, clean(Path(source).stem) + "_Edited.mp4")
            self.busy = True
            threading.Thread(target=self.editor_worker, args=(source, output, start.get(), end.get(),
                            subtitle.get() or None, effect.get(), text.get(), int(size.get()), position.get()), daemon=True).start()
        self.button(win, "Export Edited Video", export, "#0f766e").pack(anchor="e", padx=18, pady=14)

    def editor_worker(self, source, output, start, end, subtitle, effect, text, size, position):
        try:
            fmt = self.format.get()
            if fmt == "Both":
                fmt = "Landscape"
            vf = self.video_filter(fmt, effect, text, size, position)
            cmd = [self.ffmpeg, "-y", "-ss", start, "-to", end, "-i", source]
            if subtitle:
                vf += ",subtitles='" + ffpath(subtitle) + "'"
            cmd += ["-vf" if fmt == "Landscape" else "-filter_complex", vf,
                    "-map", "0:v:0", "-map", "0:a?", "-c:v", "libx264", "-preset", "veryfast",
                    "-crf", "22", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "160k",
                    "-movflags", "+faststart", output]
            if self.run_command(cmd):
                raise RuntimeError("FFmpeg export failed.")
            self.events.put(("status", "Edited video saved: " + output))
        except Exception as exc:
            self.events.put(("log", "ERROR: " + str(exc)))
            self.events.put(("status", "Editor export failed. Check the log."))
        finally:
            self.events.put(("finished",))

    def preview(self):
        source = self.selected()
        if source:
            try:
                os.startfile(source)
            except Exception as exc:
                messagebox.showerror(APP, str(exc))

    def poll(self):
        try:
            while True:
                event = self.events.get_nowait()
                kind = event[0]
                if kind == "log":
                    self.log.config(state="normal")
                    self.log.insert("end", event[1] + "\n")
                    self.log.see("end")
                    self.log.config(state="disabled")
                elif kind == "status":
                    self.status.set(event[1])
                elif kind == "progress":
                    self.pb["value"] = max(0, min(100, event[1]))
                elif kind == "row":
                    _, iid, name, status, path = event
                    self.tree.item(iid, values=(name, status, path))
                elif kind == "downloaded":
                    _, iid, path, name = event
                    self.files[iid] = path
                    self.tree.item(iid, values=(name[:90], "Downloaded", path))
                elif kind == "finished":
                    self.busy = False
                    self.pb["value"] = 0
        except queue.Empty:
            pass
        self.root.after(100, self.poll)

if __name__ == "__main__":
    root = tk.Tk()
    App(root)
    root.mainloop()
