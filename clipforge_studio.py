import os, hashlib, re, json, shutil, threading, subprocess, queue, tkinter as tk, tempfile, sys, importlib.util, sysconfig
from tkinter import ttk, messagebox, filedialog
from pathlib import Path
from editor_engine import FILTER_CATEGORIES, build_filter_chain, build_audio_mix_graph, format_srt_timestamp, build_srt_content

APP = "ClipForge Studio"

def locate(name):
    exe = name + ".exe"
    candidates = [Path(__file__).parent / exe,
                  Path(__file__).parent / "ffmpeg" / "bin" / exe,
                  Path.home() / "Downloads" / exe]
    if name == "yt-dlp":
        try:
            candidates.append(Path(sysconfig.get_path("scripts")) / exe)
        except Exception:
            pass
    for p in candidates:
        if p.is_file():
            return str(p)
    found = shutil.which(exe) or shutil.which(name)
    if found:
        return found
    if name == "yt-dlp" and importlib.util.find_spec("yt_dlp"):
        return sys.executable
    return None

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
        self.active_process = None
        self.closing = False
        self.out = str(Path.home() / "Downloads")
        self.export_quality = "High"
        self.export_fps = "Original"
        self.export_resolution = "1080p"
        self.state_dir = Path(os.environ.get("APPDATA", str(Path.home()))) / "ClipForgeStudio"
        self.state_file = self.state_dir / "session.json"
        self.current_stage = "Ready"
        self.show_logs = False
        self.ytdlp = locate("yt-dlp")
        self.ffmpeg = locate("ffmpeg")
        self.format = tk.StringVar(value="Landscape")
        self.status = tk.StringVar(value="Ready — download first, then choose how to split or edit.")
        self._style()
        self._build()
        self.load_state()
        root.protocol("WM_DELETE_WINDOW", self.on_close)
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
        nav_items = [
            ("▣   Home", self.go_home),
            ("↓   Downloads", self.go_downloads),
            ("✂   Split & Cut", self.split_dialog),
            ("▤   Subtitles", self.editor_dialog),
            ("◈   Effects", self.editor_dialog),
            ("♫   Audio", self.audio_dialog),
        ]
        self.nav_buttons = {}
        for label, command in nav_items:
            btn = tk.Button(sidebar, text=label, command=command, bg="#1d2a44" if label.startswith("▣") else "#10182b",
                            fg="#e2e8f0" if label.startswith("▣") else "#8fa0bb",
                            activebackground="#253653", activeforeground="#ffffff",
                            anchor="w", padx=16, pady=12, relief="flat", bd=0,
                            font=("Segoe UI", 10, "bold" if label.startswith("▣") else "normal"),
                            cursor="hand2")
            btn.pack(fill="x", padx=10, pady=2)
            self.nav_buttons[label] = btn
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
        self.url_entry = tk.Entry(linkrow, textvariable=self.url, bg="#0b1427", fg="#f8fafc",
                                  insertbackground="white", relief="flat", font=("Segoe UI", 11),
                                  highlightthickness=1, highlightbackground="#344765")
        self.url_entry.pack(side="left", fill="x", expand=True, ipady=11, padx=(0, 8))
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
        self.button(libhead, "Import Video", self.import_video, "#0e9f83").pack(side="right", padx=6)
        self.button(libhead, "Scan Folder", self.scan_output_folder, "#344765").pack(side="right", padx=6)
        self.button(libhead, "Open Folder", self.open_output_folder, "#344765").pack(side="right", padx=6)
        self.button(libhead, "Advanced Log", self.toggle_logs, "#344765").pack(side="right", padx=6)
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
        tk.Label(fmt, text="RESOLUTION", bg="#0b1020", fg="#8292ad",
                 font=("Segoe UI", 8, "bold")).pack(side="left", padx=(12, 4))
        self.resolution_box = ttk.Combobox(fmt, values=["720p", "1080p", "1440p"],
            state="readonly", width=8)
        self.resolution_box.set(self.export_resolution)
        self.resolution_box.pack(side="left", padx=4)
        self.resolution_box.bind("<<ComboboxSelected>>",
            lambda _e: setattr(self, "export_resolution", self.resolution_box.get()))
        tk.Label(fmt, text="QUALITY", bg="#0b1020", fg="#8292ad",
                 font=("Segoe UI", 8, "bold")).pack(side="left", padx=(10, 4))
        self.quality_box = ttk.Combobox(fmt, values=["Draft", "Standard", "High", "Best"],
            state="readonly", width=10)
        self.quality_box.set(self.export_quality)
        self.quality_box.pack(side="left", padx=4)
        self.quality_box.bind("<<ComboboxSelected>>",
            lambda _e: setattr(self, "export_quality", self.quality_box.get()))
        tk.Label(fmt, text="FPS", bg="#0b1020", fg="#8292ad",
                 font=("Segoe UI", 8, "bold")).pack(side="left", padx=(10, 4))
        self.fps_box = ttk.Combobox(fmt, values=["Original", "24", "30", "60"],
            state="readonly", width=9)
        self.fps_box.set(self.export_fps)
        self.fps_box.pack(side="left", padx=4)
        self.fps_box.bind("<<ComboboxSelected>>",
            lambda _e: setattr(self, "export_fps", self.fps_box.get()))
        self.button(fmt, "Output folder", self.change, "#344765").pack(side="right")
        self.folder_label = tk.Label(bottom, text="Output: " + self.out, bg="#0b1020",
                                      fg="#71829d", anchor="w", font=("Segoe UI", 8))
        self.folder_label.pack(fill="x")
        self.pb = ttk.Progressbar(bottom, maximum=100)
        self.pb.pack(fill="x", pady=(8, 5))
        self.status = tk.StringVar(value="Ready — download a video, then open an editing tool.")
        tk.Label(bottom, textvariable=self.status, bg="#0b1020", fg="#a5b4fc",
                 anchor="w", font=("Segoe UI", 8)).pack(fill="x")
        self.progress_label = tk.Label(bottom, text="0%  •  Ready", bg="#0b1020",
                                         fg="#a5b4fc", anchor="e", font=("Segoe UI", 8, "bold"))
        self.progress_label.pack(fill="x")
        self.log = tk.Text(bottom, height=4, bg="#080d18", fg="#8494ad",
                           font=("Consolas", 8), state="disabled", relief="flat")
        self.log.pack(fill="x", pady=(7, 0))
        self.log.pack_forget()

    def set_export_controls(self, enabled=True):
        state = "readonly" if enabled else "disabled"
        for control in (self.format_box, self.resolution_box, self.quality_box, self.fps_box):
            control.configure(state=state)

    def encoding_args(self):
        crf = {"Draft": "28", "Standard": "23", "High": "20", "Best": "17"}.get(
            self.export_quality, "20")
        args = ["-preset", "veryfast", "-crf", crf, "-pix_fmt", "yuv420p"]
        if self.export_fps in ("24", "30", "60"):
            args += ["-r", self.export_fps]
        return args

    def go_home(self):
        self.url_entry_focus()

    def url_entry_focus(self):
        try:
            self.root.focus_force()
            self.url_entry.focus_set()
        except Exception:
            pass
        self.status.set("Home — paste a video link to get started.")

    def go_downloads(self):
        self.tree.focus_set()
        children = self.tree.get_children()
        if children:
            self.tree.selection_set(children[-1])
            self.tree.see(children[-1])
        self.status.set("Downloads — select a completed video from your library.")

    def audio_dialog(self):
        source = self.selected()
        if not source:
            return
        try:
            duration = self.probe_duration(source)
        except Exception as exc:
            messagebox.showerror(APP, "Could not read video duration: " + str(exc))
            return
        win = tk.Toplevel(self.root)
        win.title("ClipForge Studio — Audio")
        win.configure(bg="#1f2937")
        win.resizable(False, False)
        win.transient(self.root)
        win.grab_set()
        tk.Label(win, text="Audio controls", bg="#1f2937", fg="white",
                 font=("Segoe UI", 16, "bold")).pack(anchor="w", padx=20, pady=(18, 4))
        tk.Label(win, text=Path(source).name, bg="#1f2937", fg="#94a3b8",
                 wraplength=480).pack(anchor="w", padx=20, pady=(0, 14))
        volume = tk.DoubleVar(value=100)
        music_volume = tk.DoubleVar(value=35)
        music_path = tk.StringVar()
        fade_in = tk.StringVar(value="0")
        fade_out = tk.StringVar(value="0")
        music_fade_in = tk.StringVar(value="0")
        music_fade_out = tk.StringVar(value="0")
        tk.Label(win, text="Original audio volume (%)", bg="#1f2937", fg="#cbd5e1").pack(anchor="w", padx=20)
        ttk.Scale(win, from_=0, to=200, variable=volume, orient="horizontal", length=420).pack(padx=20, pady=8)
        vol_label = tk.Label(win, text="100%", bg="#1f2937", fg="#a5b4fc")
        vol_label.pack(anchor="e", padx=22)
        volume.trace_add("write", lambda *_: vol_label.config(text=f"{int(volume.get())}%"))
        fields = tk.Frame(win, bg="#1f2937")
        fields.pack(fill="x", padx=20, pady=12)
        tk.Label(fields, text="Fade in (seconds)", bg="#1f2937", fg="#cbd5e1").grid(row=0, column=0, sticky="w")
        tk.Label(fields, text="Fade out (seconds)", bg="#1f2937", fg="#cbd5e1").grid(row=0, column=1, sticky="w", padx=12)
        ttk.Entry(fields, textvariable=fade_in, width=12).grid(row=1, column=0, sticky="w")
        ttk.Entry(fields, textvariable=fade_out, width=12).grid(row=1, column=1, sticky="w", padx=12)
        tk.Label(fields, text="Music fade in (seconds)", bg="#1f2937", fg="#cbd5e1").grid(
            row=2, column=0, sticky="w", pady=(10, 0))
        tk.Label(fields, text="Music fade out (seconds)", bg="#1f2937", fg="#cbd5e1").grid(
            row=2, column=1, sticky="w", padx=12, pady=(10, 0))
        ttk.Entry(fields, textvariable=music_fade_in, width=12).grid(row=3, column=0, sticky="w")
        ttk.Entry(fields, textvariable=music_fade_out, width=12).grid(
            row=3, column=1, sticky="w", padx=12)
        tk.Label(win, text="Background music (optional)", bg="#1f2937", fg="#cbd5e1").pack(
            anchor="w", padx=20, pady=(10, 4))
        music_row = tk.Frame(win, bg="#1f2937")
        music_row.pack(fill="x", padx=20)
        ttk.Entry(music_row, textvariable=music_path).pack(side="left", fill="x", expand=True)
        self.button(music_row, "Choose Music", lambda: music_path.set(
            filedialog.askopenfilename(filetypes=[("Audio files", "*.mp3 *.wav *.m4a *.aac *.ogg *.flac")])
            or music_path.get()), "#475569").pack(side="left", padx=6)
        tk.Label(win, text="Music volume (%)", bg="#1f2937", fg="#cbd5e1").pack(
            anchor="w", padx=20, pady=(8, 0))
        ttk.Scale(win, from_=0, to=150, variable=music_volume,
            orient="horizontal", length=420).pack(padx=20, pady=6)
        tk.Label(win, text="Exports a new H.264 MP4; the source file stays unchanged.",
                 bg="#1f2937", fg="#94a3b8").pack(anchor="w", padx=20, pady=6)
        def export_audio():
            try:
                fi, fo = float(fade_in.get()), float(fade_out.get())
                mfi, mfo = float(music_fade_in.get()), float(music_fade_out.get())
                if min(fi, fo, mfi, mfo) < 0 or fi + fo > duration or mfi + mfo > duration:
                    raise ValueError()
                if music_path.get() and not os.path.isfile(music_path.get()):
                    raise ValueError()
            except Exception:
                messagebox.showerror(APP, "Enter valid fade durations within the video length.", parent=win)
                return
            if self.busy:
                messagebox.showinfo(APP, "Wait for the current task to finish.", parent=win)
                return
            selected_format = self.format.get()
            selected_volume = volume.get()/100.0
            selected_music = music_path.get() or None
            selected_music_volume = music_volume.get()/100.0
            win.destroy()
            self.busy = True
            self.set_export_controls(False)
            threading.Thread(target=self.audio_worker,
                             args=(source, selected_volume, fi, fo, duration,
                                   selected_music, selected_music_volume, selected_format,
                                   mfi, mfo),
                             daemon=True).start()
        self.button(win, "Export Audio Adjustments", export_audio, "#0f766e").pack(anchor="e", padx=20, pady=18)

    def audio_worker(self, source, volume, fade_in, fade_out, duration,
                     music_path=None, music_volume=0.35, selected_format="Landscape",
                     music_fade_in=0, music_fade_out=0):
        try:
            filters = [f"volume={volume:.3f}"]
            if fade_in > 0:
                filters.append(f"afade=t=in:st=0:d={fade_in:.3f}")
            if fade_out > 0:
                filters.append(f"afade=t=out:st={max(0, duration-fade_out):.3f}:d={fade_out:.3f}")
            stem = clean(Path(source).stem)
            folder = os.path.join(self.out, stem + "_Audio")
            os.makedirs(folder, exist_ok=True)
            formats = ["Landscape", "Vertical 9:16"] if selected_format == "Both" else [selected_format]
            for fmt in formats:
                output = os.path.join(folder, stem + "_Audio_" +
                                      fmt.replace(" ", "_").replace(":", "") + ".mp4")
                vf = self.video_filter(fmt)
                cmd = [self.ffmpeg, "-y", "-i", source]
                if music_path:
                    cmd += ["-stream_loop", "-1", "-i", music_path]
                    if fmt == "Vertical 9:16":
                        video_graph = vf
                    else:
                        video_graph = "[0:v]" + vf + "[vout]"
                    ffprobe = locate("ffprobe")
                    if not ffprobe:
                        raise RuntimeError("ffprobe is required to mix background music.")
                    probe = subprocess.run([ffprobe, "-v", "error",
                        "-select_streams", "a:0", "-show_entries", "stream=index",
                        "-of", "csv=p=0", source], capture_output=True, text=True,
                        creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
                    has_audio = bool(probe.stdout.strip())
                    graph_parts = [video_graph,
                        build_audio_mix_graph(has_audio, volume, music_volume,
                                              fade_in, fade_out, duration,
                                              music_fade_in, music_fade_out)]
                    cmd += ["-filter_complex", ";".join(graph_parts),
                            "-map", "[vout]", "-map", "[aout]", "-shortest"]
                else:
                    if fmt == "Vertical 9:16":
                        cmd += ["-filter_complex", vf, "-map", "[vout]"]
                    else:
                        cmd += ["-vf", vf, "-map", "0:v:0"]
                    cmd += ["-map", "0:a?", "-af", ",".join(filters)]
                cmd += ["-c:v", "libx264", *self.encoding_args(),
                        "-c:a", "aac", "-b:a", "160k",
                        "-movflags", "+faststart", output]
                if self.run_command(cmd):
                    raise RuntimeError("FFmpeg audio export failed for " + fmt)
            self.register_output_folder(folder)
            self.events.put(("status", "Audio export complete: " + folder))
        except Exception as exc:
            self.events.put(("log", "ERROR: " + str(exc)))
            self.events.put(("status", "Audio export failed. Check the log."))
        finally:
            self.events.put(("finished",))

    def toggle_logs(self):
        self.show_logs = not self.show_logs
        if self.show_logs:
            self.log.pack(fill="x", pady=(7, 0))
        else:
            self.log.pack_forget()

    def import_video(self):
        paths = filedialog.askopenfilenames(
            title="Import videos from this computer",
            filetypes=[("Video files", "*.mp4 *.mkv *.mov *.avi *.webm *.m4v *.wmv"),
                       ("All files", "*.*")])
        for path in paths:
            if not os.path.isfile(path):
                continue
            if any(existing == path for existing in self.files.values()):
                continue
            iid = self.tree.insert("", "end", values=(Path(path).name, "Imported", path))
            self.files[iid] = path
        if paths:
            self.status.set(f"Imported {len(paths)} video file(s). Select one to edit.")
            self.save_state()

    def open_output_folder(self):
        try:
            os.makedirs(self.out, exist_ok=True)
            os.startfile(self.out)
        except Exception as exc:
            messagebox.showerror(APP, "Could not open output folder: " + str(exc))

    def scan_output_folder(self):
        if self.busy:
            messagebox.showinfo(APP, "Wait until the current task finishes.")
            return
        folder = filedialog.askdirectory(title="Scan a folder for videos", initialdir=self.out)
        if not folder:
            return
        self.out = folder
        self.folder_label.config(text="Output: " + folder)
        known = {os.path.normcase(os.path.abspath(path)) for path in self.files.values()}
        found = 0
        extensions = {".mp4", ".mkv", ".mov", ".avi", ".webm", ".m4v", ".wmv"}
        for root, dirs, files in os.walk(folder):
            dirs[:] = [name for name in dirs if name.lower() != "_clipforge_work"]
            for name in files:
                path = os.path.join(root, name)
                if Path(name).suffix.lower() not in extensions:
                    continue
                key = os.path.normcase(os.path.abspath(path))
                if key in known:
                    continue
                iid = self.tree.insert("", "end", values=(name, "Imported", path))
                self.files[iid] = path
                known.add(key)
                found += 1
        self.status.set("Folder scan complete — added {} video(s) to your library.".format(found))
        self.save_state()

    def register_output_folder(self, folder):
        try:
            paths = sorted(Path(folder).rglob("*.mp4"), key=lambda p: p.stat().st_mtime)
            for path in paths:
                if path.is_file():
                    self.events.put(("output", str(path)))
        except Exception as exc:
            self.events.put(("log", "Could not register exported files: " + str(exc)))

    def unique_output_path(self, folder, filename):
        candidate = os.path.join(folder, filename)
        if not os.path.exists(candidate):
            return candidate
        stem, ext = os.path.splitext(filename)
        index = 2
        while os.path.exists(os.path.join(folder, "{}_{}{}".format(stem, index, ext))):
            index += 1
        return os.path.join(folder, "{}_{}{}".format(stem, index, ext))

    def save_state(self):
        try:
            self.state_dir.mkdir(parents=True, exist_ok=True)
            rows = []
            for iid in self.tree.get_children():
                name, status, path = self.tree.item(iid, "values")
                queued_url = next((url for url, job_iid in self.jobs if job_iid == iid), "")
                rows.append({"name": name, "status": status, "path": path, "url": queued_url})
            data = {"output_folder": self.out, "rows": rows,
                    "status": self.status.get(), "progress": float(self.pb["value"]),
                    "stage": self.current_stage, "export_quality": self.export_quality,
                    "export_fps": self.export_fps, "export_resolution": self.export_resolution,
                    "export_format": self.format.get()}
            temp = self.state_file.with_suffix(".tmp")
            temp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
            temp.replace(self.state_file)
        except Exception:
            pass

    def load_state(self):
        try:
            if not self.state_file.is_file():
                return
            data = json.loads(self.state_file.read_text(encoding="utf-8"))
            self.out = data.get("output_folder", self.out)
            self.export_quality = data.get("export_quality", self.export_quality)
            self.export_fps = data.get("export_fps", self.export_fps)
            self.export_resolution = data.get("export_resolution", self.export_resolution)
            self.quality_box.set(self.export_quality)
            self.fps_box.set(self.export_fps)
            self.resolution_box.set(self.export_resolution)
            self.format.set(data.get("export_format", self.format.get()))
            self.folder_label.config(text="Output: " + self.out)
            for row in data.get("rows", []):
                path = row.get("path", "")
                status = row.get("status", "Imported")
                if status in ("Downloading", "Converting to H.264"):
                    status = "Interrupted — reopen to retry"
                iid = self.tree.insert("", "end", values=(row.get("name", "Video"), status, path))
                if path and os.path.isfile(path) and status not in ("Queued", "Download failed"):
                    self.files[iid] = path
                saved_url = row.get("url", "")
                if saved_url and status in ("Queued", "Download failed", "Interrupted — reopen to retry"):
                    self.jobs.append((saved_url, iid))
            saved_status = data.get("status", "Previous session restored.")
            self.status.set("Previous session restored — " + saved_status)
            self.current_stage = "Previous session"
            self.progress_label.config(text=f"{int(data.get('progress', 0))}%  •  Previous session")
        except Exception:
            self.status.set("Previous session could not be fully restored.")

    def on_close(self):
        self.closing = True
        if self.active_process and self.active_process.poll() is None:
            try:
                self.active_process.terminate()
                try:
                    self.active_process.wait(timeout=2)
                except subprocess.TimeoutExpired:
                    self.active_process.kill()
            except Exception:
                pass
        if self.busy:
            self.current_stage = "Interrupted — task stopped when app closed"
            self.status.set("App closed during a task. Reopen to see saved history.")
            for iid in self.tree.get_children():
                vals = list(self.tree.item(iid, "values"))
                if len(vals) > 1 and vals[1] in ("Downloading", "Converting to H.264"):
                    vals[1] = "Interrupted — reopen to retry"
                    self.tree.item(iid, values=vals)
        self.save_state()
        self.root.destroy()

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
        self.save_state()

    def clear(self):
        if self.busy:
            return
        self.jobs.clear()
        for iid in self.tree.get_children():
            self.tree.delete(iid)
        self.files.clear()
        self.save_state()

    def change(self):
        if self.busy:
            messagebox.showinfo(APP, "Wait until the current export or download finishes.")
            return
        folder = filedialog.askdirectory(initialdir=self.out)
        if folder:
            self.out = folder
            self.folder_label.config(text="Output: " + folder)
            self.save_state()

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
        self.set_export_controls(False)
        threading.Thread(target=self.download_worker, daemon=True).start()

    def run_command(self, cmd, duration=None):
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
                                encoding="utf-8", errors="replace", bufsize=1,
                                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        self.active_process = proc
        try:
            if self.closing:
                proc.terminate()
            for line in proc.stdout:
                line = line.strip()
                if not line:
                    continue
                self.events.put(("log", line))
                # yt-dlp reports percentages; FFmpeg -progress reports elapsed time in microseconds.
                match = re.search(r"(\d+(?:\.\d+)?)%", line)
                if match:
                    self.events.put(("progress", float(match.group(1))))
                elif duration and duration > 0:
                    out_time = re.search(r"out_time_ms=(\d+)", line)
                    stamp = re.search(r"(?:out_time|time)=(\d+):(\d+):(\d+(?:\.\d+)?)", line)
                    if out_time:
                        seconds = int(out_time.group(1)) / 1000000.0
                        self.events.put(("progress", min(99.0, seconds / duration * 100)))
                    elif stamp:
                        seconds = int(stamp.group(1))*3600 + int(stamp.group(2))*60 + float(stamp.group(3))
                        self.events.put(("progress", min(99.0, seconds / duration * 100)))
            return proc.wait()
        finally:
            if self.active_process is proc:
                self.active_process = None

    def download_worker(self):
        try:
            os.makedirs(self.out, exist_ok=True)
            for index, (url, iid) in enumerate(list(self.jobs), 1):
                self.events.put(("stage", "Downloading"))
                self.events.put(("progress", 0))
                self.events.put(("row", iid, url[:90], "Downloading", ""))
                self.events.put(("status", "Downloading video " + str(index)))
                work = os.path.join(self.out, "_ClipForge_Work", "job_" + str(index).zfill(3))
                os.makedirs(work, exist_ok=True)
                template = os.path.join(work, "%(title).150B [%(id)s].%(ext)s")
                ytdlp_command = ([self.ytdlp, "-m", "yt_dlp"] if
                    os.path.normcase(os.path.abspath(self.ytdlp)) ==
                    os.path.normcase(os.path.abspath(sys.executable)) else [self.ytdlp])
                code = self.run_command(ytdlp_command + ["--no-playlist", "--newline", "-f", "bv*+ba/b",
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
                # Keep temporary source files in the work folder, but place the finished video
                # directly in the selected output folder so users can find it easily.
                converted_name = clean(Path(source).stem) + "_H264.mp4"
                converted = self.unique_output_path(self.out, converted_name)
                if os.path.abspath(converted) == os.path.abspath(source):
                    converted = os.path.join(self.out, clean(Path(source).stem) + "_H264_Export.mp4")
                self.events.put(("stage", "Converting to H.264"))
                try:
                    source_duration = self.probe_duration(source)
                except Exception:
                    source_duration = None
                self.events.put(("progress", 0))
                self.events.put(("row", iid, url[:90], "Converting to H.264", source))
                self.events.put(("status", "Converting to H.264 MP4..."))
                convert_cmd = [self.ffmpeg, "-y", "-i", source, "-map", "0:v:0", "-map", "0:a?",
                               "-c:v", "libx264", *self.encoding_args(),
                               "-c:a", "aac", "-b:a", "160k",
                               "-movflags", "+faststart", "-progress", "pipe:1", "-nostats", converted]
                if self.run_command(convert_cmd, duration=source_duration) != 0 or not os.path.isfile(converted):
                    self.events.put(("row", iid, url[:90], "Conversion failed", source))
                    continue
                source = converted
                try:
                    self.jobs.remove((url, iid))
                except ValueError:
                    pass
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
            output_format = self.format.get()
            win.destroy()
            self.process_video(source, *args, output_format)
        self.button(win, "Create Parts", go, "#7c3aed").pack(anchor="e", padx=18, pady=16)

    def to_seconds(self, value):
        parts = value.strip().split(":")
        if len(parts) != 3:
            raise ValueError()
        h, m, s = [float(x) for x in parts]
        if min(h, m, s) < 0 or m >= 60 or s >= 60:
            raise ValueError()
        return h * 3600 + m * 60 + s

    def process_video(self, source, mode, duration, start, end, output_format):
        if self.busy:
            messagebox.showinfo(APP, "Wait for the current task to finish.")
            return
        self.busy = True
        self.set_export_controls(False)
        threading.Thread(target=self.split_worker,
                         args=(source, mode, duration, start, end, output_format), daemon=True).start()

    def split_worker(self, source, mode, duration, start, end, output_format):
        try:
            stem = clean(Path(source).stem)
            dest = os.path.join(self.out, stem + "_Clips")
            os.makedirs(dest, exist_ok=True)
            formats = ["Landscape", "Vertical 9:16"] if output_format == "Both" else [output_format]
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
            self.register_output_folder(dest)
            self.events.put(("status", "Split complete: " + dest))
        except Exception as exc:
            self.events.put(("log", "ERROR: " + str(exc)))
            self.events.put(("status", "Split failed. Check the log."))
        finally:
            self.events.put(("finished",))

    def video_filter(self, fmt, effect="Original", text="", font_size=48, position="Bottom",
                     subtitle=None, adjustments=None, overlay=None, overlay_image=None):
        if overlay is None:
            overlay = {"text": text, "text_size": font_size, "position": position}
        settings = dict(adjustments or {})
        settings.setdefault("resolution", self.export_resolution)
        return build_filter_chain(fmt, effect or "Original", settings, overlay, subtitle, overlay_image)

    def encode_segments(self, source, folder, duration, fmt):
        output = os.path.join(folder, "Part_%03d.mp4")
        vf = self.video_filter(fmt)
        cmd = [self.ffmpeg, "-y", "-i", source, "-filter_complex" if fmt == "Vertical 9:16" else "-vf", vf,
               "-map", "[vout]" if fmt == "Vertical 9:16" else "0:v:0", "-map", "0:a?",
               "-c:v", "libx264", *self.encoding_args(), "-c:a", "aac", "-b:a", "160k", "-f", "segment",
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
        cmd += ["-map", "0:a?", "-c:v", "libx264", *self.encoding_args(),
                "-c:a", "aac", "-b:a", "160k",
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
            self.set_export_controls(False)
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
                           "-c:v", "libx264", *self.encoding_args(),
                           "-c:a", "aac", "-b:a", "160k",
                           "-movflags", "+faststart", output]
                    if self.run_command(cmd):
                        raise RuntimeError("FFmpeg failed on clip " + str(index))
            self.register_output_folder(dest)
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
        win.geometry("1040x880")
        win.minsize(920, 760)
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
        self.button(info, "Preview Current Look", lambda: preview_current_look(), "#0f766e").pack(side="right", padx=6)
        preview_frame = tk.Frame(win, bg="#0b1220", height=150)
        preview_frame.pack(fill="x", padx=18, pady=(4, 8))
        preview_frame.pack_propagate(False)
        preview_image_label = tk.Label(preview_frame, text="Choose a filter or adjustment, then preview your look.",
                                       bg="#0b1220", fg="#94a3b8")
        preview_image_label.pack(expand=True)
        preview_png = os.path.join(tempfile.gettempdir(), "clipforge_editor_preview.png")
        def preview_current_look():
            if not self.ffmpeg:
                self.ffmpeg = locate("ffmpeg")
            if not self.ffmpeg:
                messagebox.showerror(APP, "FFmpeg is required for preview.", parent=win)
                return
            try:
                chosen_overlay = {"text": overlay_text.get(), "text_size": int(overlay_size.get()),
                    "position": overlay_position.get(), "color": overlay_color.get(),
                    "background": overlay_background.get(), "font": overlay_font.get(),
                    "image_position": image_position.get(),
                    "text_start": float(overlay_start.get()), "text_end": float(overlay_end.get())}
                chosen_adjustments = {key: value.get() for key, value in adjustment_vars.items()}
                chosen_adjustments.update({"rotation": rotation_var.get(),
                    "flip_h": flip_h_var.get(), "flip_v": flip_v_var.get(),
                    "video_fade_in": video_fade_in.get(),
                    "video_fade_out": video_fade_out.get(), "duration": duration,
                    "speed": speed_var.get(), "canvas_mode": canvas_mode_var.get()})
                chosen_adjustments["subtitle_size"] = subtitle_size.get()
                chosen_adjustments["outline"] = text_outline.get()
                chosen_adjustments["shadow"] = text_shadow.get()
                chosen_adjustments["overlay_start"] = float(overlay_start.get())
                chosen_adjustments["overlay_end"] = float(overlay_end.get())
                chosen_adjustments["subtitle_outline"] = subtitle_outline.get()
                chosen_overlay.update({"subtitle_color": subtitle_color.get(),
                                        "subtitle_position": subtitle_position.get()})
                subtitle_path = resolve_subtitle_path()
                graph = self.video_filter(self.format.get() if self.format.get() != "Both" else "Landscape",
                    effect.get(), overlay_text.get(), int(overlay_size.get()), overlay_position.get(),
                    subtitle_path, chosen_adjustments, chosen_overlay, overlay_image.get() or None)
                if graph.endswith("[vout]"):
                    graph = graph[:-6] + ",scale=800:450:force_original_aspect_ratio=decrease[vpreview]"
                    cmd = [self.ffmpeg, "-hide_banner", "-loglevel", "error", "-y", "-ss",
                           str(playhead[0]), "-i", source]
                    if overlay_image.get():
                        loop_args = ["-stream_loop", "-1"] if Path(overlay_image.get()).suffix.lower() == ".gif" else ["-loop", "1"]
                        cmd += loop_args + ["-i", overlay_image.get()]
                    cmd += ["-filter_complex", graph, "-map", "[vpreview]", "-frames:v", "1", preview_png]
                else:
                    graph += ",scale=800:450:force_original_aspect_ratio=decrease"
                    cmd = [self.ffmpeg, "-hide_banner", "-loglevel", "error", "-y", "-ss",
                           str(playhead[0]), "-i", source, "-vf", graph, "-frames:v", "1", preview_png]
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=45,
                    creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
                if result.returncode or not os.path.isfile(preview_png):
                    raise RuntimeError(result.stderr[-1200:] or "Preview frame could not be created.")
                photo = tk.PhotoImage(file=preview_png)
                preview_image_label.config(image=photo, text="")
                preview_image_label.image = photo
            except Exception as exc:
                preview_image_label.config(image="", text="Preview failed: " + str(exc))
                preview_image_label.image = None

        tk.Label(win, text="CREATOR TOOLS", bg="#1f2937", fg="#cbd5e1",
                 font=("Segoe UI", 10, "bold")).pack(anchor="w", padx=18, pady=(12, 5))
        notebook = ttk.Notebook(win)
        notebook.pack(fill="both", expand=True, padx=18, pady=5)
        filter_tab = tk.Frame(notebook, bg="#172235")
        adjust_tab = tk.Frame(notebook, bg="#172235")
        overlay_tab = tk.Frame(notebook, bg="#172235")
        subtitle_tab = tk.Frame(notebook, bg="#172235")
        notebook.add(filter_tab, text="  Filters  ")
        notebook.add(adjust_tab, text="  Adjust  ")
        notebook.add(overlay_tab, text="  Text & Overlay  ")
        notebook.add(subtitle_tab, text="  Subtitles  ")

        category = tk.StringVar(value="Basic")
        effect = tk.StringVar(value="Original")
        tk.Label(filter_tab, text="Filter category", bg="#172235", fg="#cbd5e1").grid(
            row=0, column=0, sticky="w", padx=14, pady=(14, 4))
        category_box = ttk.Combobox(filter_tab, textvariable=category,
            values=list(FILTER_CATEGORIES.keys()), state="readonly", width=24)
        category_box.grid(row=1, column=0, sticky="w", padx=14)
        tk.Label(filter_tab, text="Filter preset", bg="#172235", fg="#cbd5e1").grid(
            row=0, column=1, sticky="w", padx=14, pady=(14, 4))
        filter_box = ttk.Combobox(filter_tab, textvariable=effect,
            values=list(FILTER_CATEGORIES["Basic"].keys()), state="readonly", width=30)
        filter_box.grid(row=1, column=1, sticky="w", padx=14)
        preset_count = sum(len(items) for items in FILTER_CATEGORIES.values())
        preview_filter_name = tk.Label(filter_tab, text=f"{preset_count} named presets across {len(FILTER_CATEGORIES)} categories",
            bg="#172235", fg="#94a3b8", font=("Segoe UI", 9))
        preview_filter_name.grid(row=2, column=0, columnspan=2, sticky="w", padx=14, pady=12)
        filter_cards = tk.Frame(filter_tab, bg="#172235")
        filter_cards.grid(row=3, column=0, columnspan=2, sticky="ew", padx=10, pady=5)
        filter_tile_buttons = {}
        thumbnail_state = {"token": 0}
        def choose_filter(name):
            effect.set(name)
            preview_filter_name.config(text="Selected filter: " + name)
            for child in filter_cards.winfo_children():
                if getattr(child, "_filter_name", None) == name:
                    child.configure(bg="#2563eb")
                else:
                    child.configure(bg="#344765")
        def apply_filter_thumbnail(name, path, token):
            if token != thumbnail_state["token"] or not win.winfo_exists():
                return
            tile = filter_tile_buttons.get(name)
            if tile and os.path.isfile(path):
                try:
                    photo = tk.PhotoImage(file=path)
                    tile.configure(image=photo, text=name, compound="top")
                    tile.image = photo
                except Exception:
                    pass
        source_key = hashlib.sha1((os.path.abspath(source) +
            str(os.path.getmtime(source))).encode("utf-8", errors="ignore")).hexdigest()[:10]
        def create_filter_thumbnails(category_name, choices, token):
            if not self.ffmpeg:
                return
            for name in choices:
                if token != thumbnail_state["token"]:
                    return
                path = os.path.join(tempfile.gettempdir(),
                    "clipforge_filter_" + clean(category_name) + "_" + clean(name) +
                    "_" + source_key + ".png")
                try:
                    if os.path.isfile(path):
                        self.root.after(0, lambda n=name, p=path, t=token:
                                        apply_filter_thumbnail(n, p, t))
                        continue
                    graph = self.video_filter("Original", name)
                    graph += ",scale=170:78:force_original_aspect_ratio=decrease,pad=170:78:(ow-iw)/2:(oh-ih)/2"
                    command = [self.ffmpeg, "-hide_banner", "-loglevel", "error", "-y",
                        "-ss", str(playhead[0]), "-i", source, "-vf", graph,
                        "-frames:v", "1", path]
                    result = subprocess.run(command, capture_output=True, text=True, timeout=25,
                        creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
                    if result.returncode == 0 and os.path.isfile(path):
                        self.root.after(0, lambda n=name, p=path, t=token:
                                        apply_filter_thumbnail(n, p, t))
                except Exception:
                    continue
        def render_filter_cards():
            for child in filter_cards.winfo_children():
                child.destroy()
            filter_tile_buttons.clear()
            choices = list(FILTER_CATEGORIES.get(category.get(), {}).keys())
            filter_box.configure(values=choices)
            if effect.get() not in choices:
                effect.set("Original" if "Original" in choices else choices[0])
            thumbnail_state["token"] += 1
            token = thumbnail_state["token"]
            for index, name in enumerate(choices):
                tile = tk.Button(filter_cards, text=name + "\nPreview loading…",
                    command=lambda item=name: choose_filter(item), bg="#2563eb" if name == effect.get() else "#344765",
                    fg="white", activebackground="#3b82f6", activeforeground="white",
                    relief="flat", bd=0, font=("Segoe UI", 9, "bold"),
                    width=19, height=7, wraplength=145, compound="top", cursor="hand2")
                tile._filter_name = name
                tile.grid(row=index // 4, column=index % 4, sticky="nsew", padx=4, pady=4)
                filter_cards.grid_columnconfigure(index % 4, weight=1)
                filter_tile_buttons[name] = tile
            threading.Thread(target=create_filter_thumbnails,
                args=(category.get(), choices, token), daemon=True).start()

        category_box.bind("<<ComboboxSelected>>", lambda _event: render_filter_cards())
        filter_box.bind("<<ComboboxSelected>>", lambda _event: choose_filter(effect.get()))
        render_filter_cards()

        adjustment_vars = {
            "brightness": tk.DoubleVar(value=0), "contrast": tk.DoubleVar(value=1),
            "saturation": tk.DoubleVar(value=1), "gamma": tk.DoubleVar(value=1),
            "temperature": tk.DoubleVar(value=0), "tint": tk.DoubleVar(value=0),
            "sharpen": tk.DoubleVar(value=0), "fade": tk.DoubleVar(value=0),
            "vignette": tk.DoubleVar(value=0), "blur": tk.DoubleVar(value=0)
        }
        rotation_var = tk.StringVar(value="None")
        flip_h_var = tk.BooleanVar(value=False)
        flip_v_var = tk.BooleanVar(value=False)
        video_fade_in = tk.DoubleVar(value=0)
        video_fade_out = tk.DoubleVar(value=0)
        speed_var = tk.DoubleVar(value=1)
        canvas_mode_var = tk.StringVar(value="Fit")
        slider_specs = [
            ("brightness", "Brightness", -1, 1), ("contrast", "Contrast", 0, 2),
            ("saturation", "Saturation", 0, 2), ("gamma", "Gamma", 0.1, 2),
            ("temperature", "Temperature", -1, 1), ("tint", "Tint", -1, 1),
            ("sharpen", "Sharpen", 0, 2), ("fade", "Fade", 0, 1),
            ("vignette", "Vignette", 0, 1), ("blur", "Blur", 0, 10)
        ]
        for index, (key, label, low, high) in enumerate(slider_specs):
            row, col = divmod(index, 2)
            cell = tk.Frame(adjust_tab, bg="#172235")
            cell.grid(row=row, column=col, sticky="ew", padx=12, pady=5)
            adjust_tab.grid_columnconfigure(col, weight=1)
            tk.Label(cell, text=label, bg="#172235", fg="#dbeafe").pack(anchor="w")
            ttk.Scale(cell, from_=low, to=high, variable=adjustment_vars[key],
                      orient="horizontal").pack(fill="x", pady=2)
        tk.Label(adjust_tab, text="Rotate", bg="#172235", fg="#dbeafe").grid(
            row=6, column=0, sticky="w", padx=12, pady=5)
        ttk.Combobox(adjust_tab, textvariable=rotation_var,
            values=["None", "90° CW", "180°", "90° CCW"],
            state="readonly", width=18).grid(row=6, column=1, sticky="w", padx=12)
        tk.Checkbutton(adjust_tab, text="Mirror horizontally", variable=flip_h_var,
            bg="#172235", fg="#dbeafe", selectcolor="#0b1220",
            activebackground="#172235").grid(row=7, column=0, sticky="w", padx=12, pady=5)
        tk.Checkbutton(adjust_tab, text="Flip vertically", variable=flip_v_var,
            bg="#172235", fg="#dbeafe", selectcolor="#0b1220",
            activebackground="#172235").grid(row=7, column=1, sticky="w", padx=12, pady=5)
        tk.Label(adjust_tab, text="Video fade in (seconds)", bg="#172235", fg="#dbeafe").grid(
            row=9, column=0, sticky="w", padx=12, pady=5)
        ttk.Scale(adjust_tab, from_=0, to=min(5, duration/2), variable=video_fade_in,
            orient="horizontal").grid(row=9, column=1, sticky="ew", padx=12)
        tk.Label(adjust_tab, text="Video fade out (seconds)", bg="#172235", fg="#dbeafe").grid(
            row=10, column=0, sticky="w", padx=12, pady=5)
        ttk.Scale(adjust_tab, from_=0, to=min(5, duration/2), variable=video_fade_out,
            orient="horizontal").grid(row=10, column=1, sticky="ew", padx=12)
        tk.Label(adjust_tab, text="Playback speed", bg="#172235", fg="#dbeafe").grid(
            row=11, column=0, sticky="w", padx=12, pady=5)
        ttk.Scale(adjust_tab, from_=0.5, to=2, variable=speed_var,
            orient="horizontal").grid(row=11, column=1, sticky="ew", padx=12)
        tk.Label(adjust_tab, text="Canvas fit", bg="#172235", fg="#dbeafe").grid(
            row=12, column=0, sticky="w", padx=12, pady=5)
        ttk.Combobox(adjust_tab, textvariable=canvas_mode_var,
            values=["Fit", "Fill", "Stretch"], state="readonly", width=18).grid(
            row=12, column=1, sticky="w", padx=12)
        self.button(adjust_tab, "Reset Adjustments",
            lambda: ([v.set({"brightness":0,"contrast":1,"saturation":1,"gamma":1,
                            "temperature":0,"tint":0,"sharpen":0,"fade":0,"vignette":0,"blur":0}[k])
                     for k,v in adjustment_vars.items()], rotation_var.set("None"),
                     flip_h_var.set(False), flip_v_var.set(False),
                     video_fade_in.set(0), video_fade_out.set(0),
                     speed_var.set(1), canvas_mode_var.set("Fit")), "#475569").grid(
                         row=13, column=0, sticky="w", padx=12, pady=8)

        overlay_text = tk.StringVar()
        overlay_size = tk.StringVar(value="48")
        overlay_position = tk.StringVar(value="Bottom")
        overlay_color = tk.StringVar(value="white")
        overlay_background = tk.BooleanVar(value=False)
        overlay_font = tk.StringVar(value="Sans")
        text_outline = tk.DoubleVar(value=3)
        text_shadow = tk.DoubleVar(value=2)
        for row, (label, variable) in enumerate([("Text", overlay_text), ("Font size", overlay_size)]):
            tk.Label(overlay_tab, text=label, bg="#172235", fg="#cbd5e1").grid(
                row=row, column=0, sticky="w", padx=14, pady=7)
            ttk.Entry(overlay_tab, textvariable=variable, width=36).grid(
                row=row, column=1, sticky="w", padx=14, pady=7)
        tk.Label(overlay_tab, text="Font", bg="#172235", fg="#cbd5e1").grid(
            row=2, column=0, sticky="w", padx=14, pady=7)
        ttk.Combobox(overlay_tab, textvariable=overlay_font,
            values=["Sans", "Serif", "Monospace"], state="readonly", width=18).grid(
                row=2, column=1, sticky="w", padx=14)
        tk.Label(overlay_tab, text="Position", bg="#172235", fg="#cbd5e1").grid(
            row=3, column=0, sticky="w", padx=14, pady=7)
        ttk.Combobox(overlay_tab, textvariable=overlay_position,
            values=["Top", "Center", "Bottom"], state="readonly", width=18).grid(
            row=3, column=1, sticky="w", padx=14)
        tk.Label(overlay_tab, text="Text color", bg="#172235", fg="#cbd5e1").grid(
            row=4, column=0, sticky="w", padx=14, pady=7)
        ttk.Combobox(overlay_tab, textvariable=overlay_color,
            values=["white", "black", "yellow", "red", "blue", "lime", "cyan", "magenta"],
            state="readonly", width=18).grid(row=4, column=1, sticky="w", padx=14)
        tk.Checkbutton(overlay_tab, text="Background box behind text",
            variable=overlay_background, bg="#172235", fg="#cbd5e1",
            selectcolor="#0b1220", activebackground="#172235").grid(
                row=5, column=1, sticky="w", padx=14, pady=7)
        tk.Label(overlay_tab, text="Outline width", bg="#172235", fg="#cbd5e1").grid(
            row=6, column=0, sticky="w", padx=14, pady=5)
        ttk.Scale(overlay_tab, from_=0, to=12, variable=text_outline,
            orient="horizontal").grid(row=6, column=1, sticky="ew", padx=14)
        tk.Label(overlay_tab, text="Shadow depth", bg="#172235", fg="#cbd5e1").grid(
            row=7, column=0, sticky="w", padx=14, pady=5)
        ttk.Scale(overlay_tab, from_=0, to=12, variable=text_shadow,
            orient="horizontal").grid(row=7, column=1, sticky="ew", padx=14)
        tk.Label(overlay_tab, text="Text is rendered into the exported video.",
            bg="#172235", fg="#94a3b8").grid(row=8, column=0, columnspan=2,
                                             sticky="w", padx=14, pady=8)

        overlay_image = tk.StringVar()
        image_opacity = tk.DoubleVar(value=0.85)
        image_scale = tk.DoubleVar(value=0.25)
        image_position = tk.StringVar(value="Bottom Right")
        overlay_start = tk.StringVar(value="0")
        overlay_end = tk.StringVar(value=f"{duration:.2f}")
        image_row = tk.Frame(overlay_tab, bg="#172235")
        image_row.grid(row=9, column=0, columnspan=2, sticky="ew", padx=14, pady=(10, 4))
        ttk.Entry(image_row, textvariable=overlay_image).pack(side="left", fill="x", expand=True)
        self.button(image_row, "Add PNG / Logo", lambda: overlay_image.set(
            filedialog.askopenfilename(filetypes=[("Overlay images", "*.png *.webp *.jpg *.jpeg *.gif")])
            or overlay_image.get()), "#475569").pack(side="left", padx=6)
        tk.Label(overlay_tab, text="Image position", bg="#172235", fg="#cbd5e1").grid(
            row=10, column=0, sticky="w", padx=14, pady=6)
        ttk.Combobox(overlay_tab, textvariable=image_position,
            values=["Top Left", "Top Right", "Center", "Bottom Left", "Bottom Right"],
            state="readonly", width=18).grid(row=10, column=1, sticky="w", padx=14)
        tk.Label(overlay_tab, text="Image opacity", bg="#172235", fg="#cbd5e1").grid(
            row=11, column=0, sticky="w", padx=14, pady=6)
        ttk.Scale(overlay_tab, from_=0.05, to=1, variable=image_opacity,
            orient="horizontal").grid(row=11, column=1, sticky="ew", padx=14)
        tk.Label(overlay_tab, text="Image size", bg="#172235", fg="#cbd5e1").grid(
            row=12, column=0, sticky="w", padx=14, pady=6)
        ttk.Scale(overlay_tab, from_=0.05, to=1, variable=image_scale,
            orient="horizontal").grid(row=12, column=1, sticky="ew", padx=14)
        tk.Label(overlay_tab, text="Overlay start (seconds)", bg="#172235", fg="#cbd5e1").grid(
            row=13, column=0, sticky="w", padx=14, pady=6)
        ttk.Entry(overlay_tab, textvariable=overlay_start, width=18).grid(
            row=13, column=1, sticky="w", padx=14)
        tk.Label(overlay_tab, text="Overlay end (seconds)", bg="#172235", fg="#cbd5e1").grid(
            row=14, column=0, sticky="w", padx=14, pady=6)
        ttk.Entry(overlay_tab, textvariable=overlay_end, width=18).grid(
            row=14, column=1, sticky="w", padx=14)

        subtitle = tk.StringVar()
        tk.Label(subtitle_tab, text="Import SRT subtitle file", bg="#172235",
                 fg="#cbd5e1").pack(anchor="w", padx=14, pady=(16, 6))
        subrow = tk.Frame(subtitle_tab, bg="#172235")
        subrow.pack(fill="x", padx=14)
        ttk.Entry(subrow, textvariable=subtitle).pack(side="left", fill="x", expand=True)
        self.button(subrow, "Browse SRT", lambda: subtitle.set(
            filedialog.askopenfilename(filetypes=[("Subtitle files", "*.srt")]) or subtitle.get()),
            "#475569").pack(side="left", padx=6)
        caption_items = []
        caption_text = tk.StringVar()
        caption_start = tk.StringVar(value="0")
        caption_end = tk.StringVar(value=str(min(2, duration)))
        caption_form = tk.Frame(subtitle_tab, bg="#172235")
        caption_form.pack(fill="x", padx=14, pady=(12, 4))
        tk.Label(caption_form, text="New caption", bg="#172235", fg="#cbd5e1").grid(
            row=0, column=0, sticky="w", padx=4)
        ttk.Entry(caption_form, textvariable=caption_text, width=34).grid(
            row=0, column=1, sticky="ew", padx=4)
        tk.Label(caption_form, text="Start sec", bg="#172235", fg="#cbd5e1").grid(
            row=1, column=0, sticky="w", padx=4, pady=4)
        ttk.Entry(caption_form, textvariable=caption_start, width=12).grid(
            row=1, column=1, sticky="w", padx=4)
        tk.Label(caption_form, text="End sec", bg="#172235", fg="#cbd5e1").grid(
            row=1, column=2, sticky="w", padx=4)
        ttk.Entry(caption_form, textvariable=caption_end, width=12).grid(
            row=1, column=3, sticky="w", padx=4)
        caption_form.grid_columnconfigure(1, weight=1)
        caption_list = tk.Listbox(subtitle_tab, height=4, bg="#0b1220", fg="#e2e8f0",
                                  selectbackground="#1d4ed8", relief="flat")
        caption_list.pack(fill="x", padx=14, pady=5)
        def srt_timestamp(seconds):
            return format_srt_timestamp(seconds)
        def add_caption():
            try:
                start_value, end_value = float(caption_start.get()), float(caption_end.get())
                caption = caption_text.get().strip()
                if not caption or start_value < 0 or end_value <= start_value or end_value > duration:
                    raise ValueError()
                caption_items.append((start_value, end_value, caption))
                caption_items.sort(key=lambda item: item[0])
                caption_list.delete(0, "end")
                for index, (start_value, end_value, caption) in enumerate(caption_items, 1):
                    caption_list.insert("end", "{:02d}  {} → {}  {}".format(
                        index, srt_timestamp(start_value), srt_timestamp(end_value), caption))
                caption_text.set("")
            except Exception:
                messagebox.showerror(APP, "Enter caption text and a valid start/end range.", parent=win)
        def remove_caption():
            selected = caption_list.curselection()
            if selected:
                del caption_items[selected[0]]
                caption_list.delete(selected[0])
                caption_list.delete(0, "end")
                for index, (start_value, end_value, caption) in enumerate(caption_items, 1):
                    caption_list.insert("end", "{:02d}  {} → {}  {}".format(
                        index, srt_timestamp(start_value), srt_timestamp(end_value), caption))
        tk.Label(subtitle_tab, text="Adding custom captions uses your caption list instead of the imported SRT for this export.",
            bg="#172235", fg="#94a3b8", wraplength=760, justify="left").pack(
                anchor="w", padx=14, pady=(0, 4))
        caption_buttons = tk.Frame(subtitle_tab, bg="#172235")
        caption_buttons.pack(fill="x", padx=14, pady=4)
        self.button(caption_buttons, "＋ Add Caption", add_caption, "#0f766e").pack(side="left")
        self.button(caption_buttons, "Remove Caption", remove_caption, "#475569").pack(side="left", padx=6)
        def resolve_subtitle_path():
            if not caption_items:
                return subtitle.get() or None
            custom_path = os.path.join(tempfile.gettempdir(), "clipforge_custom_captions.srt")
            Path(custom_path).write_text(build_srt_content(caption_items), encoding="utf-8")
            return custom_path
        subtitle_size = tk.DoubleVar(value=28)
        subtitle_outline = tk.DoubleVar(value=2)
        subtitle_color = tk.StringVar(value="white")
        subtitle_position = tk.StringVar(value="Bottom")
        subtitle_options = tk.Frame(subtitle_tab, bg="#172235")
        subtitle_options.pack(fill="x", padx=14, pady=10)
        tk.Label(subtitle_options, text="Font size", bg="#172235", fg="#cbd5e1").grid(
            row=0, column=0, sticky="w", padx=6, pady=5)
        ttk.Scale(subtitle_options, from_=10, to=72, variable=subtitle_size,
            orient="horizontal").grid(row=0, column=1, sticky="ew", padx=6)
        tk.Label(subtitle_options, text="Outline", bg="#172235", fg="#cbd5e1").grid(
            row=1, column=0, sticky="w", padx=6, pady=5)
        ttk.Scale(subtitle_options, from_=0, to=8, variable=subtitle_outline,
            orient="horizontal").grid(row=1, column=1, sticky="ew", padx=6)
        tk.Label(subtitle_options, text="Color", bg="#172235", fg="#cbd5e1").grid(
            row=2, column=0, sticky="w", padx=6, pady=5)
        ttk.Combobox(subtitle_options, textvariable=subtitle_color,
            values=["white", "yellow", "cyan", "red", "green"],
            state="readonly", width=14).grid(row=2, column=1, sticky="w", padx=6)
        tk.Label(subtitle_options, text="Position", bg="#172235", fg="#cbd5e1").grid(
            row=3, column=0, sticky="w", padx=6, pady=5)
        ttk.Combobox(subtitle_options, textvariable=subtitle_position,
            values=["Bottom", "Top", "Center"], state="readonly", width=14).grid(
            row=3, column=1, sticky="w", padx=6)
        subtitle_options.grid_columnconfigure(1, weight=1)
        tk.Label(subtitle_tab, text="SRT subtitles are burned into the exported video.",
            bg="#172235", fg="#94a3b8").pack(anchor="w", padx=14, pady=8)

        tk.Label(win, text="Output format: " + self.format.get() + "  •  H.264 MP4 export",
                 bg="#1f2937", fg="#94a3b8").pack(anchor="w", padx=18, pady=12)

        def export():
            if self.busy:
                messagebox.showinfo(APP, "Wait for the current task to finish.", parent=win)
                return
            try:
                font_size = int(overlay_size.get())
                if not 10 <= font_size <= 180:
                    raise ValueError()
                subtitle_path = resolve_subtitle_path()
                if subtitle_path and not os.path.isfile(subtitle_path):
                    raise ValueError()
                adjustments = {key: value.get() for key, value in adjustment_vars.items()}
                adjustments.update({"rotation": rotation_var.get(),
                    "flip_h": flip_h_var.get(), "flip_v": flip_v_var.get(),
                    "video_fade_in": video_fade_in.get(),
                    "video_fade_out": video_fade_out.get(), "duration": duration,
                    "speed": speed_var.get(), "canvas_mode": canvas_mode_var.get()})
                adjustments["subtitle_size"] = subtitle_size.get()
                adjustments["outline"] = text_outline.get()
                adjustments["shadow"] = text_shadow.get()
                adjustments["subtitle_outline"] = subtitle_outline.get()
                if overlay_image.get() and not os.path.isfile(overlay_image.get()):
                    raise ValueError()
                overlay_start_value = float(overlay_start.get())
                overlay_end_value = float(overlay_end.get())
                if overlay_start_value < 0 or overlay_end_value <= overlay_start_value or overlay_end_value > duration:
                    raise ValueError()
                adjustments["overlay_start"] = overlay_start_value
                adjustments["overlay_end"] = overlay_end_value
                adjustments["overlay_opacity"] = image_opacity.get()
                adjustments["overlay_scale"] = image_scale.get()
                overlay = {"text": overlay_text.get(), "text_size": font_size,
                           "position": overlay_position.get(), "color": overlay_color.get(),
                           "background": overlay_background.get(), "font": overlay_font.get(),
                           "image_position": image_position.get(), "image": overlay_image.get() or None,
                           "text_start": overlay_start_value, "text_end": overlay_end_value,
                           "subtitle_color": subtitle_color.get(),
                           "subtitle_position": subtitle_position.get()}
            except Exception:
                messagebox.showerror(APP, "Check text size and subtitle file.", parent=win)
                return
            win.destroy()
            self.busy = True
            self.set_export_controls(False)
            threading.Thread(target=self.editor_worker,
                             args=(source, sorted(cuts), subtitle_path, effect.get(),
                                   overlay_text.get(), font_size, overlay_position.get(),
                                   adjustments, overlay, self.format.get()),
                             daemon=True).start()
        self.button(win, "Export Edited Video", export, "#0f766e").pack(anchor="e", padx=18, pady=12)
        redraw()

    @staticmethod
    def format_time(seconds):
        total = max(0, int(seconds))
        return f"{total//3600:02d}:{(total%3600)//60:02d}:{total%60:02d}"

    def editor_worker(self, source, cuts, subtitle, effect, text, size, position,
                      adjustments=None, overlay=None, output_format="Landscape"):
        try:
            stem = clean(Path(source).stem)
            folder = os.path.join(self.out, stem + "_Edited")
            os.makedirs(folder, exist_ok=True)
            formats = ["Landscape", "Vertical 9:16"] if output_format == "Both" else [output_format]
            for fmt in formats:
                overlay_image_path = (overlay or {}).get("image")
                vf = self.video_filter(fmt, effect, text, size, position, subtitle,
                                       adjustments, overlay, overlay_image_path)
                output = os.path.join(folder, fmt.replace(" ", "_").replace(":", "") +
                                      ("_Part_%03d.mp4" if cuts else ".mp4"))
                cmd = [self.ffmpeg, "-y", "-i", source]
                if overlay_image_path:
                    loop_args = ["-stream_loop", "-1"] if Path(overlay_image_path).suffix.lower() == ".gif" else ["-loop", "1"]
                    cmd += loop_args + ["-i", overlay_image_path,
                            "-filter_complex", vf, "-map", "[vout]"]
                elif fmt == "Vertical 9:16":
                    cmd += ["-filter_complex", vf, "-map", "[vout]"]
                else:
                    cmd += ["-vf", vf, "-map", "0:v:0"]
                cmd += ["-map", "0:a?"]
                speed = float((adjustments or {}).get("speed", 1))
                if abs(speed - 1) > 0.0001:
                    cmd += ["-af", "atempo={:.4f}".format(speed)]
                cmd += ["-c:v", "libx264", *self.encoding_args(),
                        "-c:a", "aac", "-b:a", "160k",
                        "-movflags", "+faststart"]
                if overlay_image_path:
                    cmd += ["-shortest"]
                if cuts:
                    cmd += ["-f", "segment", "-segment_times", ",".join(
                                f"{x / max(0.5, speed):.3f}" for x in cuts),
                            "-reset_timestamps", "1", "-segment_format", "mp4"]
                cmd += [output]
                if self.run_command(cmd):
                    raise RuntimeError("FFmpeg export failed for " + fmt)
            self.register_output_folder(folder)
            self.events.put(("status", "Edited export complete: " + folder))
        except Exception as exc:
            self.events.put(("log", "ERROR: " + str(exc)))
            self.events.put(("status", "Editor export failed. Check the log."))
        finally:
            self.events.put(("finished",))

    def preview(self):
        source = self.selected()
        if not source:
            return
        try:
            duration = self.probe_duration(source)
        except Exception as exc:
            messagebox.showerror(APP, "Could not read video: " + str(exc))
            return
        win = tk.Toplevel(self.root)
        win.title("ClipForge Studio — Video Preview")
        win.geometry("900x650")
        win.configure(bg="#0b1020")
        win.transient(self.root)
        win.grid_columnconfigure(0, weight=1)
        win.grid_rowconfigure(1, weight=1)
        tk.Label(win, text="VIDEO PREVIEW", bg="#0b1020", fg="#a5b4fc",
                 font=("Segoe UI", 11, "bold")).grid(row=0, column=0, sticky="w", padx=20, pady=(16, 4))
        tk.Label(win, text=Path(source).name, bg="#0b1020", fg="#94a3b8",
                 wraplength=850).grid(row=0, column=0, sticky="e", padx=20, pady=(16, 4))
        stage = tk.Frame(win, bg="#050914", highlightthickness=1, highlightbackground="#263956")
        stage.grid(row=1, column=0, sticky="nsew", padx=20, pady=12)
        stage.grid_columnconfigure(0, weight=1)
        stage.grid_rowconfigure(0, weight=1)
        image_label = tk.Label(stage, text="Generating preview frame…", bg="#050914", fg="#94a3b8")
        image_label.grid(row=0, column=0, sticky="nsew")
        controls = tk.Frame(win, bg="#0b1020")
        controls.grid(row=2, column=0, sticky="ew", padx=20, pady=(0, 16))
        position = tk.DoubleVar(value=0.0)
        time_label = tk.Label(controls, text="00:00:00", bg="#0b1020", fg="#c4b5fd",
                              font=("Consolas", 10, "bold"))
        time_label.pack(side="left", padx=(0, 12))
        seek = ttk.Scale(controls, from_=0, to=max(0.1, duration), variable=position)
        seek.pack(side="left", fill="x", expand=True, padx=8)
        self.button(controls, "Refresh Frame", lambda: render_frame(), "#344765").pack(side="left", padx=6)
        self.button(controls, "▶  Play Full Video", lambda: os.startfile(source), "#0e9f83").pack(side="left")
        frame_path = os.path.join(tempfile.gettempdir(), "clipforge_preview_frame.png")
        def render_frame():
            if not os.path.isfile(self.ffmpeg or ""):
                self.ffmpeg = locate("ffmpeg")
            if not self.ffmpeg:
                image_label.config(text="FFmpeg not found — install ffmpeg.exe to preview frames.")
                return
            seconds = max(0.0, min(duration, position.get()))
            time_label.config(text=self.seconds_label(seconds))
            try:
                result = subprocess.run([self.ffmpeg, "-y", "-ss", str(seconds), "-i", source,
                                         "-frames:v", "1", "-vf", "scale=820:460:force_original_aspect_ratio=decrease",
                                         frame_path], capture_output=True, text=True,
                                        creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
                if result.returncode != 0 or not os.path.isfile(frame_path):
                    image_label.config(text="Could not generate this preview frame.")
                    return
                photo = tk.PhotoImage(file=frame_path)
                image_label.config(image=photo, text="")
                image_label.image = photo
            except Exception as exc:
                image_label.config(text="Preview error: " + str(exc))
        seek.bind("<ButtonRelease-1>", lambda event: render_frame())
        render_frame()

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
                    self.save_state()
                elif kind == "stage":
                    self.current_stage = event[1]
                    self.progress_label.config(text=f"{int(self.pb['value'])}%  •  {self.current_stage}")
                    self.save_state()
                elif kind == "progress":
                    self.pb["value"] = max(0, min(100, event[1]))
                    self.progress_label.config(text=f"{int(self.pb['value'])}%  •  {self.current_stage}")
                    self.save_state()
                elif kind == "row":
                    _, iid, name, status, path = event
                    self.tree.item(iid, values=(name, status, path))
                    if path and os.path.isfile(path):
                        self.files[iid] = path
                    self.save_state()
                elif kind == "output":
                    path = event[1]
                    normalized = os.path.normcase(os.path.abspath(path))
                    if os.path.isfile(path) and not any(
                            os.path.normcase(os.path.abspath(existing)) == normalized
                            for existing in self.files.values()):
                        iid = self.tree.insert("", "end",
                            values=(os.path.basename(path), "Ready to Edit", path))
                        self.files[iid] = path
                        self.tree.selection_set(iid)
                        self.tree.focus(iid)
                        self.tree.see(iid)
                        self.save_state()
                elif kind == "downloaded":
                    _, iid, path, name = event
                    self.files[iid] = path
                    self.tree.item(iid, values=(name[:90], "Downloaded", path))
                    self.tree.selection_set(iid)
                    self.tree.focus(iid)
                    self.tree.see(iid)
                    self.status.set("Download complete — video is ready in your library and saved to: " + path)
                    self.current_stage = "Completed"
                    self.pb["value"] = 100
                    self.progress_label.config(text="100%  •  Completed")
                    self.save_state()
                elif kind == "finished":
                    self.busy = False
                    self.set_export_controls(True)
                    self.save_state()
        except queue.Empty:
            pass
        self.root.after(100, self.poll)

if __name__ == "__main__":
    root = tk.Tk()
    App(root)
    root.mainloop()
