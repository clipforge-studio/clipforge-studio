import shutil
import subprocess
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from editor_engine import FILTER_CATEGORIES, build_filter_chain, build_audio_mix_graph

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

image_graph = build_filter_chain("Landscape", "Original",
    {"overlay_opacity": 0.7, "overlay_scale": 0.3},
    {"image_position": "Bottom Right"}, overlay_image="logo.png")
command = [ffmpeg, "-hide_banner", "-loglevel", "error", "-y",
           *source, "-f", "lavfi", "-i", "color=c=red@0.5:s=64x64:d=0.3",
           "-filter_complex", image_graph, "-map", "[vout]",
           "-frames:v", "1", "-f", "null", "-"]
result = subprocess.run(command, capture_output=True, text=True)
total += 1
if result.returncode:
    failures.append(("Overlay", "PNG logo compositing", result.stderr[-1200:]))

for fmt in ("Landscape", "Vertical 9:16"):
    for mode in ("Fit", "Fill", "Stretch"):
        graph = build_filter_chain(fmt, "Original", {"canvas_mode": mode})
        if fmt == "Vertical 9:16":
            command = [ffmpeg, "-hide_banner", "-loglevel", "error", "-y",
                *source, "-filter_complex", graph, "-map", "[vout]",
                "-frames:v", "1", "-f", "null", "-"]
        else:
            command = [ffmpeg, "-hide_banner", "-loglevel", "error", "-y",
                *source, "-vf", graph, "-frames:v", "1", "-f", "null", "-"]
        result = subprocess.run(command, capture_output=True, text=True)
        total += 1
        if result.returncode:
            failures.append(("Canvas", fmt + " / " + mode, result.stderr[-1200:]))

fade_graph = build_filter_chain("Landscape", "Original",
    {"video_fade_in": 0.1, "video_fade_out": 0.1, "duration": 0.3})
command = [ffmpeg, "-hide_banner", "-loglevel", "error", "-y",
           *source, "-vf", fade_graph, "-frames:v", "1", "-f", "null", "-"]
result = subprocess.run(command, capture_output=True, text=True)
total += 1
if result.returncode:
    failures.append(("Adjust", "Video fade in/out", result.stderr[-1200:]))

transform_graph = build_filter_chain("Landscape", "Original",
    {"rotation": "90° CW", "flip_h": True, "flip_v": False})
command = [ffmpeg, "-hide_banner", "-loglevel", "error", "-y",
           *source, "-vf", transform_graph, "-frames:v", "1", "-f", "null", "-"]
result = subprocess.run(command, capture_output=True, text=True)
total += 1
if result.returncode:
    failures.append(("Adjust", "Rotate and mirror", result.stderr[-1200:]))

import tempfile
from pathlib import Path
subtitle_file = Path(tempfile.gettempdir()) / "clipforge_smoke.srt"
subtitle_file.write_text("1\n00:00:00,000 --> 00:00:01,000\nClipForge subtitle test\n", encoding="utf-8")
subtitle_graph = build_filter_chain("Landscape", "Original",
    {"subtitle_size": 26, "subtitle_outline": 2},
    {"subtitle_color": "yellow", "subtitle_position": "Bottom"},
    subtitle=str(subtitle_file))
command = [ffmpeg, "-hide_banner", "-loglevel", "error", "-y",
           *source, "-vf", subtitle_graph, "-frames:v", "1", "-f", "null", "-"]
result = subprocess.run(command, capture_output=True, text=True)
total += 1
if result.returncode:
    failures.append(("Subtitles", "SRT burn-in and styling", result.stderr[-1200:]))

import tempfile
from pathlib import Path
tmp = Path(tempfile.gettempdir())
source_mp4 = tmp / "clipforge_audio_source.mp4"
mixed_mp4 = tmp / "clipforge_audio_mixed.mp4"
create_source = [ffmpeg, "-hide_banner", "-loglevel", "error", "-y",
    "-f", "lavfi", "-i", "testsrc2=size=320x240:rate=10:duration=0.5",
    "-f", "lavfi", "-i", "sine=frequency=440:duration=0.5",
    "-shortest", "-c:v", "libx264", "-preset", "ultrafast", "-c:a", "aac", str(source_mp4)]
created = subprocess.run(create_source, capture_output=True, text=True)
if created.returncode == 0:
    video_graph = "[0:v]scale=320:240[vout]"
    audio_graph = build_audio_mix_graph(True, 0.8, 0.25, 0.05, 0.05, 0.5)
    command = [ffmpeg, "-hide_banner", "-loglevel", "error", "-y",
        "-i", str(source_mp4), "-f", "lavfi", "-i", "sine=frequency=880:duration=0.5",
        "-filter_complex", video_graph + ";" + audio_graph,
        "-map", "[vout]", "-map", "[aout]", "-shortest",
        "-c:v", "libx264", "-preset", "ultrafast", "-c:a", "aac", str(mixed_mp4)]
    result = subprocess.run(command, capture_output=True, text=True)
    total += 1
    if result.returncode or not mixed_mp4.is_file():
        failures.append(("Audio", "Background music mix export", result.stderr[-1200:]))
else:
    total += 1
    failures.append(("Audio", "Create audio test source", created.stderr[-1200:]))

print("FFmpeg filter smoke tests: {}/{} passed".format(total-len(failures), total))
if failures:
    for category, preset, error in failures:
        print("\nFAILED [{} / {}]\n{}".format(category, preset, error))
    raise SystemExit(1)
