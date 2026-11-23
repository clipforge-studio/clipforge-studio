# ClipForge Studio

A Windows desktop video utility for content you own or have permission to download and process.

## Version 0.3 development preview

This branch introduces a download-first workflow and early editing tools. It is a development preview, not a finished CapCut replacement.

### Implemented in this branch

- Queue supported video URLs and download with `yt-dlp`.
- Save the finished H.264 MP4 directly inside the selected output folder (not buried in the temporary work directory), then automatically select it in the Video Library.
- Convert downloaded AV1/VP9 videos to H.264 + AAC MP4 for improved Windows playback compatibility.
- Import existing local video files from your computer, as well as download supported URLs.
- Scan a selected folder (including subfolders) to add existing videos to the library, while skipping the temporary download-work directory.
- Open the selected output folder directly from the main workspace.
- Automatically add Split, Timeline, Editor, and Audio exports to the Video Library when processing finishes.
- Avoid silently overwriting a previously downloaded H.264 file when another video has the same title.
- Save newly queued URLs and output-folder changes immediately so they survive an unexpected app close.
- Restore the video library, output folder, last status, and last progress stage after closing and reopening the app.
- Show a simple percentage and current stage in the main window; technical output is hidden unless **Advanced Log** is opened.
- Show separate Downloading and H.264 conversion stages. FFmpeg conversion progress is read from its machine-readable progress output.
- Stop the active FFmpeg/yt-dlp process when the app is closed and mark an in-progress task as interrupted.
- Restore queued, failed, and interrupted download URLs so they can be retried with the **Download** button after reopening.
- Open an in-app frame preview window with a seek slider, frame refresh, and a button to play the full video in the system media player.
- Select Landscape, Vertical 9:16, Original, or Both for processing.
- Export settings: 720p, 1080p, or 1440p; Draft, Standard, High, or Best quality; Original, 24, 30, or 60 FPS. Settings are saved between sessions.
- Canvas fit modes for Landscape and Vertical: Fit, Fill, and Stretch.
- Choose when to split after download.
- Automatic split using a user-entered segment duration.
- Manual time-range export using start and end timestamps.
- Timeline ruler: click to position a playhead, add/remove multiple cut points, and export the resulting clips.
- Creator Editor with Filter, Adjust, Text & Overlay, and Subtitles tabs.
- 14 filter categories with 70+ named presets: Basic, Portrait, Cinematic, Vintage, Black & White, Color, Creative, Food, Nature, Travel, Night, Wedding, Urban, and Film. These are original ClipForge presets, not copied CapCut assets.
- Image and logo overlays from PNG/WebP/JPG/GIF (including animated GIF stickers) with opacity, scale, five placement positions, and start/end timing.
- Text overlays can be timed to appear only during a selected portion of the video.
- Text overlay with font family, size, color, outline/shadow, background box, and top/center/bottom placement.
- SRT subtitle burn-in with adjustable font size, color, outline, and alignment.
- Image-frame preview that renders the selected filter, adjustments, text, subtitle, and logo overlay before export.
- Adjustments: brightness, contrast, saturation, gamma, temperature, tint, sharpen, fade, vignette, blur, rotation, horizontal mirror, vertical flip, playback speed, video fade-in/out, and canvas fit/fill/stretch.
- Audio tools: original audio volume, fade-in/out, and optional looping background music mixed with the source audio.
- MP4 export using H.264 video and AAC audio for broad player compatibility.

### Known limitations

- The timeline is currently a simple clickable time ruler, not a full multi-track waveform editor.
- The in-app preview currently extracts still frames at selected timestamps; it is not continuous embedded playback or frame-accurate scrubbing. Full playback opens in the system media player.
- Timeline cut points are time-based; there is no drag-to-trim, clip rearrangement, transitions, or join tool yet.
- Subtitle authoring and per-caption timing inside the app are not implemented; subtitles are imported from an existing SRT file and burned into the export.
- Editor preview is a rendered still frame, not continuous real-time playback or a live GPU preview.
- Multi-track audio mixing, keyframes, transitions, drag-and-drop clip arrangement, and professional color grading are not implemented.
- Active downloads/conversions are not automatically resumed after reopening; the saved history and source file path remain available for retry.
- Installer packaging and broad Windows hardware testing remain outstanding.

## Requirements

- Windows 10 or later
- Python 3 with Tkinter
- `yt-dlp.exe`
- `ffmpeg.exe` and `ffprobe.exe` with `libx264` support

The app searches beside the Python script, in an `ffmpeg\bin` subfolder, in the user's Downloads folder, and on `PATH` for the required executables.

## Run

1. Install Python 3 if it is not already installed.
2. Install a trusted FFmpeg Windows build containing `ffmpeg.exe`, `ffprobe.exe`, and `libx264` support.
3. Keep `editor_engine.py` in the same folder as `clipforge_studio.py`.
4. Double-click `SETUP_DEPENDENCIES.bat` once to install/update yt-dlp. FFmpeg and FFprobe must be installed and available on `PATH`, or placed beside the app.
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
