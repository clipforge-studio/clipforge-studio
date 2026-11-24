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
- Creator Editor with dedicated Filters, Effects, Adjust, Text & Overlay, and Subtitles workspaces.
- 19 original visual categories with 100+ named filter/effect presets, including Basic, Portrait, Cinematic, Vintage, Black & White, Color, Creative, Food, Nature, Travel, Night, Wedding, Urban, Film, Lens Effects, Glitch & Distortion, Light & Glow, Motion Effects, and Retro Effects. These are original ClipForge presets, not copied CapCut assets.
- Horizontally browsable category chips, searchable preset names, persistent filter favorites, and a favorites-only view.
- Dedicated Effects Library with collections for lens, glitch/distortion, light/glow, motion, and retro looks.
- Each filter tile renders a thumbnail from the selected video and displays its preset name; previews are cached per source video.
- Image and logo overlays from PNG/WebP/JPG/GIF (including animated GIF stickers) with opacity, scale, five placement positions, and start/end timing.
- Text overlays can be timed to appear only during a selected portion of the video.
- Text overlay with font family, size, color, outline/shadow, background box, and top/center/bottom placement.
- Import SRT or author multiple captions in-app with per-caption start/end times and save them as SRT; burn them in with adjustable font family (including Nirmala UI/Noto Sans Bengali options), size, color, outline, and alignment.
- Asynchronous image-frame preview that renders the selected filter, effects, adjustments, text, subtitle, and logo overlay without blocking the editor interface.
- Adjustments: brightness, exposure, contrast, saturation, gamma, hue, temperature, tint, sharpen, fade, vignette, blur, rotation, horizontal mirror, vertical flip, playback speed, video fade-in/out, and canvas fit/fill/stretch.
- Audio tools: original audio volume, fade-in/out, and optional looping background music mixed with the source audio, with independent music fade-in/fade-out controls.
- MP4 export using H.264 video and AAC audio for broad player compatibility.

### Known limitations

- The timeline is currently a simple clickable time ruler, not a full multi-track waveform editor.
- The in-app preview currently extracts still frames at selected timestamps; it is not continuous embedded playback or frame-accurate scrubbing. Full playback opens in the system media player.
- Timeline cut points are time-based; there is no drag-to-trim, clip rearrangement, transitions, or join tool yet.
- The in-app preview is a rendered still frame at the selected timestamp, not continuous embedded playback or a live GPU preview. Filter and adjustment changes trigger asynchronous preview renders.
- The timeline is still a simple time ruler with cut points; multi-track drag-and-drop clip arrangement, waveform editing, keyframes, transitions, and motion tracking are not implemented.
- The effects and filter catalog is an original starter library, not a copy of CapCut's proprietary filters, templates, or downloadable assets.
- Active downloads/conversions are not automatically resumed after reopening; the saved history and source file path remain available for retry.
- Signed installer packaging and broad Windows hardware testing remain outstanding.

## Windows portable build

The GitHub Actions workflow builds a Windows portable ZIP containing the application, Python runtime, FFmpeg, FFprobe, and yt-dlp. On a Windows 10/11 PC, extract the complete ZIP and run `ClipForgeStudio.exe` from the `ClipForgeStudio` folder. Do not separate the EXE from its `_internal` folder. No separate Python or FFmpeg installation is required for this portable build.

The portable ZIP is generated by the `windows-portable` workflow job and published as a prerelease asset from the feature branch.

## Developer run (source checkout)

For contributors running from source: Windows 10 or later, Python 3 with Tkinter, yt-dlp, FFmpeg, and FFprobe with `libx264` support are required. Keep `editor_engine.py` beside `clipforge_studio.py`, then run `SETUP_DEPENDENCIES.bat` and `START_APP.bat`.

Temporary downloads are kept in `_ClipForge_Work`.

## Important limitations

- Download availability depends on yt-dlp support and each site's rules.
- This app does not bypass DRM, private-video restrictions, logins, or access controls.
- Use it only for content you own or have permission to download and process.
- This is an early development preview. It has not been packaged as a signed Windows installer or tested across a range of PCs.

## License

MIT. See [LICENSE](LICENSE).
