import os, re, shutil, threading, subprocess, queue, tkinter as tk
from tkinter import ttk, messagebox, filedialog
from pathlib import Path

def locate(name):
    exe=name+".exe"
    for p in [Path(__file__).parent/exe, Path(__file__).parent/"ffmpeg"/"bin"/exe, Path.home()/"Downloads"/exe]:
        if p.is_file(): return str(p)
    return shutil.which(exe) or shutil.which(name)

def clean(s):
    return re.sub(r'[<>:"/\\|?*]', "_", s).strip(" ._")[:140] or "video"

class App:
 def __init__(self,r):
    self.r=r; r.title("ClipForge Studio"); r.geometry("820x660"); r.configure(bg="#111827")
    self.q=queue.Queue(); self.jobs=[]; self.busy=False; self.out=str(Path.home()/"Downloads")
    self.ytdlp=locate("yt-dlp"); self.ffmpeg=locate("ffmpeg")
    st=ttk.Style(); st.theme_use("clam"); st.configure("TProgressbar",troughcolor="#263244",background="#22c55e")
    st.configure("Treeview",background="#1f2937",foreground="white",fieldbackground="#1f2937",rowheight=26)
    st.configure("Treeview.Heading",background="#374151",foreground="white")
    h=tk.Frame(r,bg="#111827"); h.pack(fill="x",padx=22,pady=18)
    tk.Label(h,text="ClipForge Studio",bg="#111827",fg="white",font=("Segoe UI",21,"bold")).pack(anchor="w")
    tk.Label(h,text="Download permitted videos • 5-minute parts • Landscape + Vertical 9:16",bg="#111827",fg="#94a3b8").pack(anchor="w")
    p=tk.Frame(r,bg="#1f2937"); p.pack(fill="x",padx=22,pady=7)
    tk.Label(p,text="VIDEO LINK",bg="#1f2937",fg="#cbd5e1").pack(anchor="w",padx=14,pady=(12,5))
    row=tk.Frame(p,bg="#1f2937"); row.pack(fill="x",padx=14,pady=(0,12))
    self.url=tk.StringVar(); tk.Entry(row,textvariable=self.url,bg="#0f172a",fg="white",insertbackground="white",relief="flat",font=("Segoe UI",11)).pack(side="left",fill="x",expand=True,ipady=9,padx=(0,7))
    self.btn(row,"Paste",self.paste,"#475569").pack(side="left")
    row=tk.Frame(p,bg="#1f2937"); row.pack(fill="x",padx=14,pady=(0,13))
    self.btn(row,"Add to Queue",self.add).pack(side="left"); self.btn(row,"Start",self.start,"#15803d").pack(side="left",padx=7); self.btn(row,"Clear",self.clear,"#475569").pack(side="left")
    s=tk.Frame(r,bg="#111827"); s.pack(fill="x",padx=22,pady=7)
    tk.Label(s,text="SPLIT: 5 MINUTES  |  OUTPUT:",bg="#111827",fg="#cbd5e1").pack(side="left")
    self.folder=tk.Label(s,text=self.out,bg="#111827",fg="#e2e8f0"); self.folder.pack(side="left",padx=8)
    self.btn(s,"Change",self.change,"#475569").pack(side="right")
    tk.Label(r,text="DOWNLOAD & SPLIT QUEUE",bg="#111827",fg="#cbd5e1").pack(anchor="w",padx=22,pady=(8,5))
    self.tree=ttk.Treeview(r,columns=("url","status"),show="headings",height=7); self.tree.heading("url",text="Video URL"); self.tree.heading("status",text="Status"); self.tree.column("url",width=600); self.tree.column("status",width=140); self.tree.pack(fill="both",expand=True,padx=22)
    self.pb=ttk.Progressbar(r,maximum=100); self.pb.pack(fill="x",padx=22,pady=8)
    self.status=tk.StringVar(value="Ready. Add a video you own or are permitted to download.")
    tk.Label(r,textvariable=self.status,bg="#111827",fg="#cbd5e1").pack(anchor="w",padx=22)
    self.log=tk.Text(r,height=6,bg="#0b1220",fg="#94a3b8",font=("Consolas",8),state="disabled"); self.log.pack(fill="x",padx=22,pady=10)
    if not self.ytdlp or not self.ffmpeg: self.status.set("Setup required: yt-dlp.exe and ffmpeg.exe must be beside this app. See README.txt.")
    r.after(100,self.poll)
 def btn(self,p,t,c,col="#2563eb"):
    return tk.Button(p,text=t,command=c,bg=col,fg="white",relief="flat",bd=0,padx=13,pady=9,font=("Segoe UI",9,"bold"),cursor="hand2")
 def paste(self):
    try:self.url.set(self.r.clipboard_get().strip())
    except: self.status.set("Clipboard empty.")
 def add(self):
    u=self.url.get().strip()
    if not u.startswith(("https://","http://")): messagebox.showwarning("Downloader","Paste a valid URL."); return
    if any(x[0]==u for x in self.jobs): return
    iid=self.tree.insert("","end",values=(u,"Queued")); self.jobs.append((u,iid)); self.url.set("")
 def clear(self):
    if self.busy:return
    self.jobs=[]
    for x in self.tree.get_children():self.tree.delete(x)
 def change(self):
    d=filedialog.askdirectory(initialdir=self.out)
    if d:self.out=d; self.folder.config(text=d)
 def emit(self,*x):self.q.put(x)
 def command(self,cmd):
    p=subprocess.Popen(cmd,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,encoding="utf-8",errors="replace",creationflags=getattr(subprocess,"CREATE_NO_WINDOW",0))
    for line in p.stdout:
     line=line.rstrip()
     if line:
      self.emit("log",line)
      m=re.search(r'(\d+(?:\.\d+)?)%',line)
      if m:self.emit("progress",float(m.group(1)))
    return p.wait()
 def start(self):
    if self.busy:return
    if not self.jobs:messagebox.showinfo("Downloader","Add a URL first.");return
    self.ytdlp=locate("yt-dlp"); self.ffmpeg=locate("ffmpeg")
    if not self.ytdlp or not self.ffmpeg:
     messagebox.showerror("Setup needed","Place yt-dlp.exe and ffmpeg.exe beside dailymotion_pro.py. See README.txt.");return
    self.busy=True; threading.Thread(target=self.worker,daemon=True).start()
 def worker(self):
    try:
     os.makedirs(self.out,exist_ok=True)
     for n,(url,iid) in enumerate(list(self.jobs),1):
      self.emit("row",iid,url,"Downloading"); self.emit("status",f"Downloading {n} of {len(self.jobs)}")
      work=os.path.join(self.out,"_ClipForge_Work",f"job_{n:03d}")
      os.makedirs(work,exist_ok=True)
      template=os.path.join(work,"%(title).150B [%(id)s].%(ext)s")
      code=self.command([self.ytdlp,"--no-playlist","--newline","-f","bv*+ba/b","--merge-output-format","mp4","--ffmpeg-location",os.path.dirname(self.ffmpeg),"-o",template,url])
      if code: self.emit("row",iid,url,"Download failed"); continue
      media=[os.path.join(work,f) for f in os.listdir(work) if f.lower().endswith((".mp4",".mkv",".webm",".mov"))]
      if not media:self.emit("row",iid,url,"No media file");continue
      src=max(media,key=os.path.getmtime); stem=clean(os.path.splitext(os.path.basename(src))[0]); dest=os.path.join(self.out,stem+"_Parts"); os.makedirs(dest,exist_ok=True)
      self.emit("row",iid,url,"Splitting"); self.emit("status","Creating 5-minute landscape and vertical parts...")
      land=os.path.join(dest,"Landscape_Part_%03d.mp4")
      cl=self.command([self.ffmpeg,"-y","-i",src,"-map","0:v:0","-map","0:a?","-c","copy","-f","segment","-segment_time","300","-reset_timestamps","1",land])
      vd=os.path.join(dest,"Vertical_9x16");os.makedirs(vd,exist_ok=True)
      vf="[0:v]split=2[bg][fg];[bg]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,boxblur=24:8[blur];[fg]scale=1080:1920:force_original_aspect_ratio=decrease[front];[blur][front]overlay=(W-w)/2:(H-h)/2,setsar=1[outv]"
      cv=self.command([self.ffmpeg,"-y","-i",src,"-filter_complex",vf,"-map","[outv]","-map","0:a?","-c:v","libx264","-preset","veryfast","-crf","23","-c:a","aac","-b:a","128k","-f","segment","-segment_time","300","-reset_timestamps","1",os.path.join(vd,"Vertical_Part_%03d.mp4")])
      self.emit("row",iid,url,"Done" if cl==0 and cv==0 else "Split failed")
      self.emit("status",f"Finished: {dest}")
     self.emit("status","Queue finished. Check the output folder.")
    except Exception as e:self.emit("log","ERROR: "+str(e));self.emit("status","Error; see log.")
    finally:self.emit("finished")
 def poll(self):
    try:
     while True:
      e=self.q.get_nowait()
      if e[0]=="log":
       self.log.config(state="normal");self.log.insert("end",e[1]+"\n");self.log.see("end");self.log.config(state="disabled")
      elif e[0]=="status":self.status.set(e[1])
      elif e[0]=="progress":self.pb["value"]=max(0,min(100,e[1]))
      elif e[0]=="row":self.tree.item(e[1],values=(e[2],e[3]))
      elif e[0]=="finished":self.busy=False;self.jobs=[]
    except queue.Empty:pass
    self.r.after(100,self.poll)

if __name__=="__main__":
 root=tk.Tk();App(root);root.mainloop()
