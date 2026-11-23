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
        # ClipForge Studio v0.3 — redesigned workspace shell.
        self.root.grid_columnconfigure(1, weight=1)
        self.root.grid_rowconfigure(1, weight=1)
        self.root.configure(bg="#0b1020")

        sidebar = tk.Frame(self.root, bg="#10182b", width=210)
        sidebar.grid(row=0, column=0, rowspan=3, sticky="ns")
        sidebar.grid_propagate(False)
        brand = tk.Frame(sidebar, bg="#10182b")
        brand.pack(fill="x", padx=18, pady=(22, 28))
        tk.Label(brand, text="✦  CLIPFORGE", bg="#10182b", fg="#f8fafc",
                 font=("Segoe UI", 16, "bold")).pack(anchor="w")
        tk.Label(brand, text="STUDIO  /  CREATOR WORKSPACE", bg="#10182b", fg="#7c8ba5",
                 font=("Segoe UI", 7, "bold")).pack(anchor="w", pady=(5, 0))
        for label, active in [("▣   Home", True), ("↓   Downloads", False),
                              ("✂   Split & Cut", False), ("▤   Subtitles", False),
                              ("◈   Effects", False), ("♫   Audio", False)]:
            tk.Label(sidebar, text=label, bg="#1d2a44" if active else "#10182b",
                     fg="#e2e8f0" if active else "#8fa0bb", anchor="w",
                     padx=16, pady=12, font=("Segoe UI", 10, "bold" if active else "normal")
                     ).pack(fill="x", padx=10, pady=2)
        tk.Frame(sidebar, bg="#25324a", height=1).pack(fill="x", padx=16, pady=18)
        tk.Label(sidebar, text="WORKSPACE", bg="#10182b", fg="#60718d",
                 font=("Segoe UI", 8, "bold")).pack(anchor="w", padx=18)
        tk.Label(sidebar, text="Local projects\nSaved on this device", bg="#10182b",
                 fg="#8fa0bb", justify="left", font=("Segoe UI", 9)).pack(anchor="w", padx=18, pady=9)
        tk.Label(sidebar, text="CLIPFORGE  •  v0.3 PREVIEW", bg="#10182b", fg="#60718d",
                 font=("Segoe UI", 7, "bold")).pack(side="bottom", anchor="w", padx=16, pady=16)

        top = tk.Frame(self.root, bg="#0b1020")
        top.grid(row=0, column=1, sticky="ew", padx=26, pady=(20, 10))
        tk.Label(top, text="Creator workspace", bg="#0b1020", fg="#f8fafc",
                 font=("Segoe UI", 22, "bold")).pack(side="left")
        tk.Label(top, text="  DOWNLOAD  •  EDIT  •  EXPORT", bg="#0b1020", fg="#8292ad",
                 font=("Segoe UI", 8, "bold")).pack(side="left", padx=12, pady=(9, 0))
        tk.Label(top, text="●  READY", bg="#102d2a", fg="#5eead4",
                 font=("Segoe UI", 8, "bold"), padx=12, pady=7).pack(side="right")

        content = tk.Frame(self.root, bg="#0b1020")
        content.grid(row=1, column=1, sticky="nsew", padx=26, pady=(0, 12))
        content.grid_columnconfigure(0, weight=1)
        content.grid_rowconfigure(2, weight=1)

        hero = tk.Frame(content, bg="#17243b", highlightthickness=1, highlightbackground="#263956")
        hero.grid(row=0, column=0, sticky="ew", pady=(0, 14))
        tk.Label(hero, text="START A NEW DOWNLOAD", bg="#17243b", fg="#a5b4fc",
                 font=("Segoe UI", 8, "bold")).pack(anchor="w", padx=18, pady=(14, 4))
        tk.Label(hero, text="Bring your next video into the studio.", bg="#17243b", fg="#f8fafc",
                 font=("Segoe UI", 14, "bold")).pack(anchor="w", padx=18)
        tk.Label(hero, text="Paste a supported video link. Download first, then choose your edit workflow.",
                 bg="#17243b", fg="#9aabc4", font=("Segoe UI", 9)).pack(anchor="w", padx=18, pady=(3, 12))
        linkrow = tk.Frame(hero, bg="#17243b")
        linkrow.pack(fill="x", padx=18, pady=(0, 16))
        self.url = tk.StringVar()
        tk.Entry(linkrow, textvariable=self.url, bg="#0b1427", fg="#f8fafc",
                 insertbackground="white", relief="flat", font=("Segoe UI", 11),
                 highlightthickness=1, highlightbackground="#344765"
                 ).pack(side="left", fill="x", expand=True, ipady=11, padx=(0, 8))
        self.button(linkrow, "Paste link", self.paste, "#344765").pack(side="left", padx=(0, 7))
        self.button(linkrow, "＋  Add to Queue", self.add, "#344765").pack(side="left", padx=(0, 7))
        self.button(linkrow, "↓  Download", self.download, "#0e9f83").pack(side="left")

        tools = tk.Frame(content, bg="#0b1020")
        tools.grid(row=1, column=0, sticky="ew", pady=(0, 14))
        for col in range(4):
            tools.grid_columnconfigure(col, weight=1)
        cards = [
            ("01  SPLIT & CUT", "Choose part duration or custom ranges", "Split Selected", self.split_dialog, "#7058d8"),
            ("02  EDITOR", "Subtitles, titles and visual filters", "Open Editor", self.editor_dialog, "#087f80"),
            ("03  TIMELINE", "Create multiple clips from cut points", "Open Timeline", self.timeline_dialog, "#a052b5"),
            ("04  PREVIEW", "Open the selected downloaded video", "Preview Video", self.preview, "#344765"),
        ]
        for i, (title, desc, action, callback, color) in enumerate(cards):
            card = tk.Frame(tools, bg="#131e32", highlightthickness=1, highlightbackground="#253550")
            card.grid(row=0, column=i, sticky="nsew", padx=(0 if i == 0 else 8, 0))
            tk.Label(card, text=title, bg="#131e32", fg="#c4b5fd",
                     font=("Segoe UI", 8, "bold")).pack(anchor="w", padx=12, pady=(12, 4))
            tk.Label(card, text=desc, bg="#131e32", fg="#91a2bd", wraplength=155,
                     justify="left", font=("Segoe UI", 8)).pack(anchor="w", padx=12, pady=(0, 9))
            self.button(card, action, callback, color).pack(anchor="w", padx=12, pady=(0, 12))

        library = tk.Frame(content, bg="#131e32", highlightthickness=1, highlightbackground="#253550")
        library.grid(row=2, column=0, sticky="nsew")
        library.grid_columnconfigure(0, weight=1)
        library.grid_rowconfigure(1, weight=1)
        libhead = tk.Frame(library, bg="#131e32")
        libhead.grid(row=0, column=0, sticky="ew", padx=15, pady=(12, 8))
        tk.Label(libhead, text="YOUR DOWNLOAD LIBRARY", bg="#131e32", fg="#f1f5f9",
                 font=("Segoe UI", 10, "bold")).pack(side="left")
        tk.Label(libhead, text="Select a completed video to edit", bg="#131e32", fg="#8192ad",
                 font=("Segoe UI", 8)).pack(side="left", padx=10)
        self.button(libhead, "Clear Queue", self.clear, "#344765").pack(side="right")
        self.tree = ttk.Treeview(library, columns=("name", "status", "file"), show="headings", height=7)
        self.tree.heading("name", text="VIDEO")
        self.tree.heading("status", text="STATUS")
        self.tree.heading("file", text="LOCAL FILE")
        self.tree.column("name", width=250)
        self.tree.column("status", width=115)
        self.tree.column("file", width=430)
        self.tree.grid(row=1, column=0, sticky="nsew", padx=14, pady=(0, 12))

        bottom = tk.Frame(self.root, bg="#0b1020")
        bottom.grid(row=2, column=1, sticky="ew", padx=26, pady=(0, 16))
        fmt = tk.Frame(bottom, bg="#0b1020")
        fmt.pack(fill="x", pady=(0, 7))
        tk.Label(fmt, text="EXPORT CANVAS", bg="#0b1020", fg="#8292ad",
                 font=("Segoe UI", 8, "bold")).pack(side="left")
        self.format = tk.StringVar(value="Landscape")
        self.format_box = ttk.Combobox(fmt, textvariable=self.format,
            values=["Landscape", "Vertical 9:16", "Original", "Both"],
            state="readonly", width=17)
        self.format_box.pack(side="left", padx=10)
        self.button(fmt, "Output folder", self.change, "#344765").pack(side="right")
        self.folder_label = tk.Label(bottom, text="Output: " + self.out, bg="#0b1020",
                                      fg="#71829d", anchor="w", font=("Segoe UI", 8))
        self.folder_label.pack(fill="x")
        self.pb = ttk.Progressbar(bottom, maximum=100)
        self.pb.pack(fill="x", pady=(8, 5))
        self.status = tk.StringVar(value="Ready — download a video, then open an editing tool.")
        tk.Label(bottom, textvariable=self.status, bg="#0b1020", fg="#a5b4fc",
                 anchor="w", font=("Segoe UI", 8)).pack(fill="x")
        self.log = tk.Text(bottom, height=3, bg="#080d18", fg="#8494ad",
                           font=("Consolas", 8), state="disabled", relief="flat")
        self.log.pack(fill="x", pady=(7, 0))

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
                # Normalize downloaded media to broadly compatible H.264/AAC MP4.
                # This prevents AV1/VP9 playback failures in common Windows players.
                converted = os.path.join(work, clean(Path(source).stem) + "_H264.mp4")
                self.events.put(("status", "Converting to compatible H.264 MP4..."))
                convert_cmd = [self.ffmpeg, "-y", "-i", source, "-map", "0:v:0", "-map", "0:a?",
                               "-c:v", "libx264", "-preset", "veryfast", "-crf", "22",
                               "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "160k",
                               "-movflags", "+faststart", converted]
                if self.run_command(convert_cmd) != 0 or not os.path.isfile(converted):
                    self.events.put(("row", iid, url[:90], "Conversion failed", source))
                    continue
                source = converted
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
                folder_name = {"Landscape": "Landscape", "Vertical 9:16": "Vertical_9x16", "Original": "Original"}[fmt]
                folder = os.path.join(dest, folder_name)
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

    def video_filter(self, fmt, effect="None", text="", font_size=48, position="Bottom", subtitle=None):
        filters = []
        if fmt == "Vertical 9:16":
            base = ("[0:v]split=2[bg][fg];[bg]scale=1080:1920:force_original_aspect_ratio=increase,"
                    "crop=1080:1920,boxblur=24:8[blur];[fg]scale=1080:1920:force_original_aspect_ratio=decrease"
                    "[front];[blur][front]overlay=(W-w)/2:(H-h)/2")
            filters.append(base)
        elif fmt == "Landscape":
            filters.append("scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2")
        else:
            filters.append("setsar=1")
        if effect == "Black & White":
            filters.append("hue=s=0")
        elif effect == "Warm":
            filters.append("colorbalance=rs=0.08:gs=0.02:bs=-0.08")
        elif effect == "Vintage":
            filters.append("curves=vintage")
        elif effect == "Sharpen":
            filters.append("unsharp=5:5:0.8:3:3:0.4")
        if subtitle:
            filters.append("subtitles='" + ffpath(subtitle) + "'")
        if text.strip():
            y = "h-th-70" if position == "Bottom" else ("70" if position == "Top" else "(h-th)/2")
            safe = text.replace("\\", "\\\\").replace(":", "\\:").replace("'", "\\'").replace("%", "\\%").replace(",", "\\,")
            filters.append("drawtext=text='" + safe + "':fontcolor=white:fontsize=" + str(int(font_size)) +
                           ":borderw=3:bordercolor=black:x=(w-text_w)/2:y=" + y)
        filters.append("setsar=1")
        if fmt == "Vertical 9:16":
            return filters[0] + "," + ",".join(filters[1:]) + "[vout]"
        return ",".join(filters)

    def encode_segments(self, source, folder, duration, fmt):
        output = os.path.join(folder, "Part_%03d.mp4")
        vf = self.video_filter(fmt)
        cmd = [self.ffmpeg, "-y", "-i", source, "-filter_complex" if fmt == "Vertical 9:16" else "-vf", vf,
               "-map", "[vout]" if fmt == "Vertical 9:16" else "0:v:0", "-map", "0:a?", "-c:v", "libx264", "-preset", "veryfast", "-crf", "22",
               "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "160k", "-f", "segment",
               "-segment_time", str(duration), "-reset_timestamps", "1", "-segment_format", "mp4", output]
        code = self.run_command(cmd)
        if code:
            raise RuntimeError("FFmpeg failed while creating " + fmt + " parts.")

    def encode_clip(self, source, output, start, end, fmt, subtitle, effect, text):
        vf = self.video_filter(fmt, effect or "None", text or "", subtitle=subtitle)
        cmd = [self.ffmpeg, "-y", "-ss", start, "-to", end, "-i", source]
        if fmt == "Vertical 9:16":
            cmd += ["-filter_complex", vf, "-map", "[vout]"]
        else:
            cmd += ["-vf", vf, "-map", "0:v:0"]
        cmd += ["-map", "0:a?", "-c:v", "libx264", "-preset", "veryfast",
                "-crf", "22", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "160k",
                "-movflags", "+faststart", output]
        if self.run_command(cmd):
            raise RuntimeError("FFmpeg could not export this clip.")


    def probe_duration(self, source):
        ffprobe = locate("ffprobe")
        if not ffprobe:
            raise RuntimeError("ffprobe.exe is required. Install it beside FFmpeg or add it to PATH.")
        result = subprocess.run([ffprobe, "-v", "error", "-show_entries", "format=duration",
                                 "-of", "default=noprint_wrappers=1:nokey=1", source],
                                capture_output=True, text=True, encoding="utf-8", errors="replace",
                                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        if result.returncode:
            raise RuntimeError("Could not read video duration: " + result.stderr[-400:])
        duration = float(result.stdout.strip())
        if duration <= 0:
            raise RuntimeError("Invalid video duration.")
        return duration

    def seconds_label(self, value):
        total = int(value)
        return f"{total//3600:02d}:{(total%3600)//60:02d}:{total%60:02d}"

    def timeline_dialog(self):
        source = self.selected()
        if not source:
            return
        try:
            duration = self.probe_duration(source)
        except Exception as exc:
            messagebox.showerror(APP, str(exc))
            return
        win = tk.Toplevel(self.root)
        win.title("ClipForge Studio — Timeline / Multi-Cut")
        win.geometry("900x560")
        win.configure(bg="#111827")
        win.transient(self.root)
        win.grab_set()
        tk.Label(win, text="Timeline • Multi-Cut Editor", bg="#111827", fg="white",
                 font=("Segoe UI", 18, "bold")).pack(anchor="w", padx=18, pady=(15, 3))
        tk.Label(win, text=Path(source).name, bg="#111827", fg="#94a3b8",
                 wraplength=850).pack(anchor="w", padx=18, pady=(0, 12))
        current = tk.DoubleVar(value=0.0)
        cuts = []
        left, right = 22, 850
        canvas = tk.Canvas(win, height=105, bg="#0b1220", highlightthickness=0)
        canvas.pack(fill="x", padx=18, pady=8)
        canvas.create_text(left, 15, text="00:00:00", fill="#cbd5e1", anchor="w")
        canvas.create_text(right, 15, text=self.seconds_label(duration), fill="#cbd5e1", anchor="e")
        canvas.create_rectangle(left, 39, right, 82, fill="#334155", outline="#64748b")
        canvas.create_text((left+right)/2, 60, text="VIDEO TIMELINE — click to move playhead",
                           fill="#e2e8f0")
        playhead = canvas.create_line(left, 28, left, 94, fill="#facc15", width=3)
        markers = []
        def xpos(value):
            return left + (right-left) * max(0, min(duration, value)) / duration
        def refresh():
            for marker in markers:
                canvas.delete(marker)
            markers.clear()
            for value in cuts:
                x = xpos(value)
                markers.append(canvas.create_line(x, 32, x, 89, fill="#f87171", width=3))
            x = xpos(current.get())
            canvas.coords(playhead, x, 25, x, 96)
            label.config(text="Playhead: " + self.seconds_label(current.get()))
        def seek(event):
            current.set(max(0, min(duration, (event.x-left)/(right-left)*duration)))
            refresh()
        canvas.bind("<Button-1>", seek)
        bar = tk.Frame(win, bg="#111827")
        bar.pack(fill="x", padx=18, pady=5)
        label = tk.Label(bar, text="Playhead: 00:00:00", bg="#111827", fg="#facc15")
        label.pack(side="left")
        listing = tk.Listbox(win, height=9, bg="#1f2937", fg="white",
                             selectbackground="#1d4ed8", relief="flat", font=("Consolas", 10))
        listing.pack(fill="both", expand=True, padx=18, pady=8)
        def refresh_list():
            listing.delete(0, "end")
            for index, value in enumerate(cuts, 1):
                listing.insert("end", f"{index:02d}    {self.seconds_label(value)}")
            refresh()
        def add_cut():
            value = round(current.get(), 2)
            if value <= 0 or value >= duration:
                messagebox.showinfo(APP, "Choose a point inside the video.")
                return
            if any(abs(value-old) < 0.5 for old in cuts):
                messagebox.showinfo(APP, "A cut point already exists nearby.")
                return
            cuts.append(value)
            cuts.sort()
            refresh_list()
        def remove_cut():
            selected = listing.curselection()
            if selected:
                del cuts[selected[0]]
                refresh_list()
        self.button(bar, "Add Cut Here", add_cut, "#7c3aed").pack(side="left", padx=12)
        self.button(bar, "Remove Selected", remove_cut, "#475569").pack(side="left")
        footer = tk.Frame(win, bg="#111827")
        footer.pack(fill="x", padx=18, pady=12)
        tk.Label(footer, text="Output: " + self.format.get() + " • H.264 MP4",
                 bg="#111827", fg="#94a3b8").pack(side="left")
        def export():
            if not cuts:
                messagebox.showinfo(APP, "Add at least one cut point first.")
                return
            if self.busy:
                return
            points = [0.0] + sorted(cuts) + [duration]
            ranges = [(points[i], points[i+1]) for i in range(len(points)-1)
                      if points[i+1]-points[i] >= 0.25]
            win.destroy()
            self.busy = True
            threading.Thread(target=self.timeline_export_worker,
                             args=(source, ranges, self.format.get()), daemon=True).start()
        self.button(footer, "Export All Clips", export, "#15803d").pack(side="right")
        refresh()

    def timeline_export_worker(self, source, ranges, output_format):
        try:
            stem = clean(Path(source).stem)
            dest = os.path.join(self.out, stem + "_Timeline_Clips")
            os.makedirs(dest, exist_ok=True)
            formats = ["Landscape", "Vertical 9:16"] if output_format == "Both" else [output_format]
            for fmt in formats:
                folder_name = {"Landscape": "Landscape", "Vertical 9:16": "Vertical_9x16", "Original": "Original"}[fmt]
                folder = os.path.join(dest, folder_name)
                os.makedirs(folder, exist_ok=True)
                for index, (start, end) in enumerate(ranges, 1):
                    output = os.path.join(folder, f"Clip_{index:03d}.mp4")
                    self.events.put(("status", f"Exporting {fmt} clip {index}/{len(ranges)}"))
                    vf = self.video_filter(fmt)
                    cmd = [self.ffmpeg, "-y", "-ss", str(start), "-i", source, "-t", str(end-start),
                           "-filter_complex" if fmt == "Vertical 9:16" else "-vf", vf,
                           "-map", "[vout]" if fmt == "Vertical 9:16" else "0:v:0", "-map", "0:a?",
                           "-c:v", "libx264", "-preset", "veryfast", "-crf", "22",
                           "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "160k",
                           "-movflags", "+faststart", output]
                    if self.run_command(cmd):
                        raise RuntimeError("FFmpeg failed on clip " + str(index))
            self.events.put(("status", "Timeline export complete: " + dest))
        except Exception as exc:
            self.events.put(("log", "ERROR: " + str(exc)))
            self.events.put(("status", "Timeline export failed. Check the log."))
        finally:
            self.events.put(("finished",))

    def editor_dialog(self):
        source = self.selected()
        if not source:
            return
        ffprobe = locate("ffprobe")
        if not ffprobe:
            messagebox.showerror(APP, "ffprobe.exe is required for the timeline editor.")
            return
        probe = subprocess.run([ffprobe, "-v", "error", "-show_entries", "format=duration",
                                "-of", "default=noprint_wrappers=1:nokey=1", source],
                               capture_output=True, text=True,
                               creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        try:
            duration = float(probe.stdout.strip())
            if duration <= 0:
                raise ValueError()
        except Exception:
            messagebox.showerror(APP, "Could not read the video's duration.")
            return

        win = tk.Toplevel(self.root)
        win.title("ClipForge Studio — Timeline Editor")
        win.geometry("820x650")
        win.configure(bg="#1f2937")
        win.transient(self.root)
        tk.Label(win, text="Timeline Editor", bg="#1f2937", fg="white",
                 font=("Segoe UI", 18, "bold")).pack(anchor="w", padx=18, pady=(15, 3))
        tk.Label(win, text=Path(source).name, bg="#1f2937", fg="#94a3b8",
                 wraplength=770).pack(anchor="w", padx=18)
        tk.Label(win, text="Click on the timeline to add cut points. Each cut creates a separate exported clip.",
                 bg="#1f2937", fg="#cbd5e1").pack(anchor="w", padx=18, pady=(12, 4))
        timeline = tk.Canvas(win, height=90, bg="#0b1220", highlightthickness=0)
        timeline.pack(fill="x", padx=18, pady=5)
        cuts = []
        playhead = [0.0]
        current = tk.StringVar(value="00:00:00")
        def x_for(t):
            return 12 + (max(1, timeline.winfo_width()-24) * t / duration)
        def redraw():
            timeline.delete("all")
            width = max(1, timeline.winfo_width()-24)
            timeline.create_rectangle(12, 25, 12+width, 65, fill="#334155", outline="#64748b")
            for cut in cuts:
                x = x_for(cut)
                timeline.create_line(x, 13, x, 77, fill="#f59e0b", width=2)
            x = x_for(playhead[0])
            timeline.create_line(x, 7, x, 82, fill="#22c55e", width=3)
            timeline.create_text(12, 4, anchor="nw", text="00:00:00", fill="#cbd5e1")
            timeline.create_text(12+width, 4, anchor="ne", text=self.format_time(duration), fill="#cbd5e1")
        def click(event):
            t = max(0.0, min(duration, (event.x-12)/max(1, timeline.winfo_width()-24)*duration))
            playhead[0] = t
            current.set(self.format_time(t))
            if 0.5 < t < duration-0.5 and all(abs(t-x) > 0.5 for x in cuts):
                cuts.append(t)
                cuts.sort()
            redraw()
        timeline.bind("<Button-1>", click)
        timeline.bind("<Configure>", lambda event: redraw())
        info = tk.Frame(win, bg="#1f2937")
        info.pack(fill="x", padx=18, pady=4)
        tk.Label(info, text="Playhead:", bg="#1f2937", fg="#cbd5e1").pack(side="left")
        tk.Label(info, textvariable=current, bg="#1f2937", fg="#22c55e",
                 font=("Consolas", 11, "bold")).pack(side="left", padx=7)
        self.button(info, "Undo Last Cut", lambda: (cuts.pop() if cuts else None, redraw()), "#475569").pack(side="right")
        self.button(info, "Preview Video", lambda: os.startfile(source), "#475569").pack(side="right", padx=6)

        tk.Label(win, text="SUBTITLES", bg="#1f2937", fg="#cbd5e1",
                 font=("Segoe UI", 10, "bold")).pack(anchor="w", padx=18, pady=(12, 3))
        subrow = tk.Frame(win, bg="#1f2937")
        subrow.pack(fill="x", padx=18)
        subtitle = tk.StringVar()
        ttk.Entry(subrow, textvariable=subtitle).pack(side="left", fill="x", expand=True)
        self.button(subrow, "Import SRT", lambda: subtitle.set(
            filedialog.askopenfilename(filetypes=[("Subtitle files", "*.srt")]) or subtitle.get()),
            "#475569").pack(side="left", padx=6)

        tk.Label(win, text="EFFECTS & TITLE", bg="#1f2937", fg="#cbd5e1",
                 font=("Segoe UI", 10, "bold")).pack(anchor="w", padx=18, pady=(12, 3))
        opts = tk.Frame(win, bg="#1f2937")
        opts.pack(fill="x", padx=18)
        effect, text, size, position = tk.StringVar(value="None"), tk.StringVar(), tk.StringVar(value="48"), tk.StringVar(value="Bottom")
        tk.Label(opts, text="Filter", bg="#1f2937", fg="#cbd5e1").grid(row=0, column=0, sticky="w")
        ttk.Combobox(opts, textvariable=effect, values=["None", "Black & White", "Warm", "Vintage", "Sharpen"],
                     state="readonly", width=16).grid(row=1, column=0, padx=(0, 10), sticky="w")
        tk.Label(opts, text="Title / text overlay", bg="#1f2937", fg="#cbd5e1").grid(row=0, column=1, sticky="w")
        ttk.Entry(opts, textvariable=text, width=25).grid(row=1, column=1, padx=(0, 10), sticky="w")
        tk.Label(opts, text="Size", bg="#1f2937", fg="#cbd5e1").grid(row=0, column=2, sticky="w")
        ttk.Entry(opts, textvariable=size, width=6).grid(row=1, column=2, padx=(0, 10), sticky="w")
        tk.Label(opts, text="Position", bg="#1f2937", fg="#cbd5e1").grid(row=0, column=3, sticky="w")
        ttk.Combobox(opts, textvariable=position, values=["Top", "Center", "Bottom"],
                     state="readonly", width=10).grid(row=1, column=3, sticky="w")
        tk.Label(win, text="Output format: " + self.format.get() + "  •  H.264 MP4 export",
                 bg="#1f2937", fg="#94a3b8").pack(anchor="w", padx=18, pady=12)

        def export():
            if self.busy:
                messagebox.showinfo(APP, "Wait for the current task to finish.", parent=win)
                return
            try:
                font_size = int(size.get())
                if not 10 <= font_size <= 160:
                    raise ValueError()
                if subtitle.get() and not os.path.isfile(subtitle.get()):
                    raise ValueError()
            except Exception:
                messagebox.showerror(APP, "Check text size and subtitle file.", parent=win)
                return
            win.destroy()
            self.busy = True
            threading.Thread(target=self.editor_worker,
                             args=(source, sorted(cuts), subtitle.get() or None, effect.get(),
                                   text.get(), font_size, position.get()),
                             daemon=True).start()
        self.button(win, "Export Edited Video", export, "#0f766e").pack(anchor="e", padx=18, pady=12)
        redraw()

    @staticmethod
    def format_time(seconds):
        total = max(0, int(seconds))
        return f"{total//3600:02d}:{(total%3600)//60:02d}:{total%60:02d}"

    def editor_worker(self, source, cuts, subtitle, effect, text, size, position):
        try:
            stem = clean(Path(source).stem)
            folder = os.path.join(self.out, stem + "_Edited")
            os.makedirs(folder, exist_ok=True)
            formats = ["Landscape", "Vertical 9:16"] if self.format.get() == "Both" else [self.format.get()]
            for fmt in formats:
                vf = self.video_filter(fmt, effect, text, size, position, subtitle)
                output = os.path.join(folder, fmt.replace(" ", "_").replace(":", "") +
                                      ("_Part_%03d.mp4" if cuts else ".mp4"))
                cmd = [self.ffmpeg, "-y", "-i", source]
                if fmt == "Vertical 9:16":
                    cmd += ["-filter_complex", vf, "-map", "[vout]"]
                else:
                    cmd += ["-vf", vf, "-map", "0:v:0"]
                cmd += ["-map", "0:a?", "-c:v", "libx264", "-preset", "veryfast",
                        "-crf", "22", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "160k",
                        "-movflags", "+faststart"]
                if cuts:
                    cmd += ["-f", "segment", "-segment_times", ",".join(f"{x:.3f}" for x in cuts),
                            "-reset_timestamps", "1", "-segment_format", "mp4"]
                cmd += [output]
                if self.run_command(cmd):
                    raise RuntimeError("FFmpeg export failed for " + fmt)
            self.events.put(("status", "Edited export complete: " + folder))
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
