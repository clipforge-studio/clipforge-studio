# ClipForge Studio

A Windows desktop video utility for content you own or have permission to download and process.

## Version 0.2 development branch

This branch introduces a download-first workflow and early editing tools. It is a development preview, not a finished CapCut replacement.

### Implemented in this branch

- Queue supported video URLs and download with `yt-dlp`.
- Keep downloaded videos in a selectable output folder.
- Select Landscape, Vertical 9:16, Original, or Both for processing.
- Choose when to split after download.
- Automatic split using a user-entered segment duration.
- Manual time-range export using start and end timestamps.
- Timeline ruler: click to position a playhead, add/remove multiple cut points, and export the resulting clips.
- Subtitle & Effects Editor: import an existing SRT file and burn it into the video, add a title/text overlay with size and position controls, and apply Black & White, Warm, Vintage, or Sharpen presets.
- MP4 export using H.264 video and AAC audio for broad player compatibility.

### Known limitations

- The timeline is currently a simple clickable time ruler, not a full multi-track waveform editor.
- It does not provide embedded video playback or frame-accurate visual scrubbing; use Preview Video to open the source in the system's media player.
- Timeline cut points are time-based; there is no drag-to-trim, clip rearrangement, transitions, or join tool yet.
- Subtitle authoring and per-caption timing inside the app are not implemented; subtitles are imported from an existing SRT file and burned into the export.
- Live preview of text, subtitles, and effects before export is not available.
- Full audio track editing, keyframes, and advanced effects are not implemented.
- Installer packaging and broad Windows hardware testing remain outstanding.

## Requirements

- Windows 10 or later
- Python 3 with Tkinter
- `yt-dlp.exe`
- `ffmpeg.exe` and `ffprobe.exe` with `libx264` support

The app searches beside the Python script, in an `ffmpeg\bin` subfolder, in the user's Downloads folder, and on `PATH` for the required executables.

## Run

1. Install Python 3 if it is not already installed.
2. Download `yt-dlp.exe` from the official yt-dlp project releases.
3. Download a trusted FFmpeg Windows build containing FFmpeg, FFprobe, and `libx264` support.
4. Put `yt-dlp.exe`, `ffmpeg.exe`, and `ffprobe.exe` beside `clipforge_studio.py` (or add them to `PATH`).
5. Double-click `START_APP.bat`.
6. Add a permitted video URL and click **Download**.
7. Select the downloaded item and choose **Split Selected**, **Timeline / Multi-Cut**, or **Open Full Editor**.

Temporary downloads are kept in `_ClipForge_Work`.

## Important limitations

- Download availability depends on yt-dlp support and each site's rules.
- This app does not bypass DRM, private-video restrictions, logins, or access controls.
- Use it only for content you own or have permission to download and process.
- This is an early development preview. It has not been packaged as a signed Windows installer or tested across a range of PCs.

## License

MIT. See [LICENSE](LICENSE).
