import shutil
import subprocess
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from editor_engine import FILTER_CATEGORIES, build_filter_chain

ffmpeg = shutil.which("ffmpeg")
if not ffmpeg:
    print("FFmpeg not installed; smoke tests cannot run.", file=sys.stderr)
    raise SystemExit(2)

source = ["-f", "lavfi", "-i", "testsrc2=size=320x240:rate=10:duration=0.3"]
total = 0
failures = []

for category, presets in FILTER_CATEGORIES.items():
    for preset in presets:
        graph = build_filter_chain("Landscape", preset)
        command = [ffmpeg, "-hide_banner", "-loglevel", "error", "-y",
                   *source, "-vf", graph, "-frames:v", "1", "-f", "null", "-"]
        result = subprocess.run(command, capture_output=True, text=True)
        total += 1
        if result.returncode:
            failures.append((category, preset, result.stderr[-1200:]))

vertical = build_filter_chain("Vertical 9:16", "Teal & Orange")
command = [ffmpeg, "-hide_banner", "-loglevel", "error", "-y",
           *source, "-filter_complex", vertical, "-map", "[vout]",
           "-frames:v", "1", "-f", "null", "-"]
result = subprocess.run(command, capture_output=True, text=True)
total += 1
if result.returncode:
    failures.append(("Canvas", "Vertical 9:16", result.stderr[-1200:]))

overlay = build_filter_chain("Landscape", "Original",
    {"brightness": 0.12, "contrast": 1.2, "saturation": 1.15,
     "gamma": 1.05, "temperature": 0.2, "tint": -0.1,
     "sharpen": 0.7, "fade": 0.2, "vignette": 0.4, "blur": 0.2},
    {"text": "ClipForge Studio", "text_size": 42, "position": "Bottom",
     "color": "white", "background": True, "font": "Sans"})
command = [ffmpeg, "-hide_banner", "-loglevel", "error", "-y",
           *source, "-vf", overlay, "-frames:v", "1", "-f", "null", "-"]
result = subprocess.run(command, capture_output=True, text=True)
total += 1
if result.returncode:
    failures.append(("Overlay", "Text and all adjustments", result.stderr[-1200:]))

print("FFmpeg filter smoke tests: {}/{} passed".format(total-len(failures), total))
if failures:
    for category, preset, error in failures:
        print("\nFAILED [{} / {}]\n{}".format(category, preset, error))
    raise SystemExit(1)
