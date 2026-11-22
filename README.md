# ClipForge Studio

A Windows desktop video utility for content you own or have permission to download and process.

## Version 0.2 development branch

This branch begins the download-first workflow and early editing tools. It is a development preview, not a finished CapCut replacement.

### Available in this development build

- Queue supported video URLs and download with `yt-dlp`.
- Keep downloaded videos in a selectable output folder.
- Select Landscape, Vertical 9:16, Original, or Both for processing.
- Choose when to split after download.
- Automatic split using a user-entered segment duration.
- Manual time-range export using start and end timestamps.\n- A basic visual timeline where clicking adds manual cut points; undo the last cut and export segments.
- Edit export with an optional SRT subtitle file (burned into the video), text overlay with position/size controls, and video filter presets (Black & White, Warm, Vintage, Sharpen).\n- H.264/AAC re-encoding for the generated MP4 clips, avoiding the previous stream-copy/AV1 playback issue in exported clips.
- MP4 export using H.264 video and AAC audio for broad player compatibility.

### Not implemented yet

- A visual, draggable multi-track timeline with playhead-based cut points.
- Multiple manual cut points and clip rearrangement/joining.
- Subtitle authoring and per-caption timing inside the app.
- Live preview of text, subtitles, and effects before export.
- Full audio track editing, transitions, keyframes, and advanced effects.
- Installer packaging and broad Windows hardware testing.

These are planned features; do not treat them as available until implemented and tested.

## Requirements

- Windows 10 or later
- Python 3 with Tkinter\n- `ffprobe.exe` (for reading the timeline duration)
- `yt-dlp.exe`
- `ffmpeg.exe` with `libx264` and subtitle filter support

The app searches beside the Python script, in an `ffmpeg\bin` subfolder, in the user's Downloads folder, and on `PATH` for the required executables.

## Run

1. Install Python 3 if it is not already installed.
2. Download `yt-dlp.exe` from the official yt-dlp project releases.
3. Download an FFmpeg Windows build from a trusted source.
4. Put `yt-dlp.exe` and `ffmpeg.exe` beside `clipforge_studio.py` (or add them to `PATH`).
5. Double-click `START_APP.bat`.
6. Add a permitted video URL and click **Download**.
7. Select the downloaded item and choose **Split Selected** or **Open Full Editor**.

Temporary downloads are kept in `_ClipForge_Work`.

## Important limitations

- Download availability depends on yt-dlp support and each site's rules.
- This app does not bypass DRM, private-video restrictions, logins, or access controls.
- Use it only for content you own or have permission to download and process.
- This is an early development preview. It has not been packaged as a signed Windows installer or tested across a range of PCs.

## License

MIT. See [LICENSE](LICENSE).
