# ClipForge Studio

A small Windows desktop utility for processing videos you own or have permission to download.

## Current features

- Queue one or more supported video URLs through `yt-dlp`.
- Download to a local working folder.
- Split downloaded media into approximately five-minute segments.
- Export landscape segments while retaining the source aspect ratio.
- Export vertical 9:16 segments with a blurred background and the full source frame fitted in front.
- Choose an output folder.

The final segment can be shorter than five minutes. Landscape splitting uses stream copy and therefore cuts at suitable keyframes; exact cut points can vary. Vertical output is re-encoded and takes longer. Vertical framing does not automatically track faces or other subjects.

## Requirements

- Windows 10 or later
- Python 3 with Tkinter
- `yt-dlp.exe`
- `ffmpeg.exe` (FFmpeg build with `libx264`)

The app looks for `yt-dlp.exe` and `ffmpeg.exe` beside the Python script, in an `ffmpeg\bin` subfolder for FFmpeg, in the user's Downloads folder for the tools, or on `PATH`.

## Run

1. Install Python 3 if it is not already installed.
2. Download `yt-dlp.exe` from the official yt-dlp project releases.
3. Download an FFmpeg Windows build from a trusted source such as the gyan.dev builds page.
4. Put `yt-dlp.exe` and `ffmpeg.exe` beside `clipforge_studio.py` (or add them to `PATH`).
5. Double-click `START_APP.bat`.
6. Paste a permitted video URL, choose **Add to Queue**, then **Start**.

Output is saved in the selected folder. Temporary downloads are kept in `_ClipForge_Work`.

## Important limitations

- Download availability and supported sites depend on the installed `yt-dlp` version and each site's rules.
- This app does not bypass DRM, private-video restrictions, logins, or other access controls.
- Use it only for content you own or have permission to download and process.
- This is an early community starter release. It has not been packaged as a signed Windows installer and has not been tested across a range of Windows PCs.

## Project status

Version: `0.1.1` — GitHub starter package. Contributions and bug reports are welcome.

## License

MIT. See [LICENSE](LICENSE).
