"""ClipForge Studio video filter and render pipeline helpers."""
from __future__ import annotations

FILTER_CATEGORIES = {
    "Basic": {
        "Original": [],
        "Bright": [
            "eq=brightness=0.08:contrast=1.05:saturation=1.08"
        ],
        "Clean": [
            "eq=contrast=1.08:saturation=1.10",
            "unsharp=3:3:0.35"
        ],
        "Soft": [
            "gblur=sigma=0.7"
        ],
        "Fade": [
            "eq=contrast=0.92:saturation=0.88",
            "colorlevels=rimin=0.04:gimin=0.04:bimin=0.04"
        ],
        "Vivid": [
            "eq=contrast=1.12:saturation=1.32"
        ],
        "Matte": [
            "eq=contrast=0.88:brightness=0.025",
            "curves=all='0/0.08 0.5/0.52 1/0.92'"
        ],
        "Crisp": [
            "eq=contrast=1.08:saturation=1.06",
            "unsharp=5:5:0.65"
        ]
    },
    "Portrait": {
        "Warm Skin": [
            "colorbalance=rs=0.07:gs=0.025:bs=-0.06",
            "eq=saturation=1.08"
        ],
        "Soft Glow": [
            "gblur=sigma=1.1",
            "eq=brightness=0.025:contrast=1.04"
        ],
        "Natural": [
            "eq=contrast=1.03:saturation=1.04"
        ],
        "Golden Skin": [
            "colorbalance=rs=0.10:gs=0.035:bs=-0.09",
            "eq=saturation=1.12"
        ],
        "Cool Portrait": [
            "colorbalance=rs=-0.035:gs=0:bs=0.075",
            "eq=contrast=1.04"
        ]
    },
    "Cinematic": {
        "Teal & Orange": [
            "colorbalance=rs=0.12:gs=0.015:bs=-0.10:rm=-0.04:gm=0.025:bm=0.08",
            "eq=contrast=1.13:saturation=1.12"
        ],
        "Moody": [
            "eq=brightness=-0.045:contrast=1.20:saturation=0.86",
            "vignette=PI/5"
        ],
        "Blockbuster": [
            "eq=contrast=1.18:saturation=1.20",
            "colorbalance=rs=0.07:bs=-0.07"
        ],
        "Film Drama": [
            "curves=medium_contrast",
            "vignette=PI/6"
        ],
        "Night Blue": [
            "colorbalance=rs=-0.06:gs=-0.015:bs=0.12",
            "eq=contrast=1.12:saturation=0.90"
        ],
        "Cinema Gold": [
            "colorbalance=rs=0.12:gs=0.04:bs=-0.12",
            "eq=contrast=1.12:saturation=1.06"
        ]
    },
    "Vintage": {
        "Vintage": [
            "curves=vintage",
            "eq=saturation=0.82"
        ],
        "Retro 70s": [
            "colorbalance=rs=0.10:gs=0.045:bs=-0.12",
            "eq=contrast=0.94:saturation=0.88"
        ],
        "Retro 90s": [
            "eq=contrast=1.10:saturation=0.92",
            "noise=alls=4:allf=t"
        ],
        "Instant Film": [
            "curves=vintage",
            "vignette=PI/5",
            "eq=saturation=0.78"
        ],
        "Sepia": [
            "colorchannelmixer=.393:.769:.189:0:.349:.686:.168:0:.272:.534:.131"
        ],
        "Dusty": [
            "eq=contrast=0.88:saturation=0.72:brightness=0.025",
            "vignette=PI/7"
        ]
    },
    "Black & White": {
        "B&W": [
            "hue=s=0"
        ],
        "Noir": [
            "hue=s=0",
            "eq=contrast=1.35:brightness=-0.025"
        ],
        "Silver Screen": [
            "hue=s=0",
            "eq=contrast=1.12:brightness=0.025"
        ],
        "Soft Mono": [
            "hue=s=0",
            "eq=contrast=0.88"
        ],
        "High Contrast Mono": [
            "hue=s=0",
            "eq=contrast=1.55"
        ]
    },
    "Color": {
        "Arctic": [
            "colorbalance=rs=-0.05:gs=0:bs=0.10",
            "eq=saturation=0.90"
        ],
        "Ocean": [
            "colorbalance=rs=-0.03:gs=0.02:bs=0.11",
            "eq=saturation=1.16"
        ],
        "Forest": [
            "colorbalance=rs=-0.025:gs=0.09:bs=-0.025",
            "eq=saturation=1.10"
        ],
        "Sunset": [
            "colorbalance=rs=0.13:gs=0.025:bs=-0.12",
            "eq=saturation=1.18"
        ],
        "Lavender": [
            "colorbalance=rs=0.035:gs=-0.025:bs=0.09",
            "eq=saturation=0.94"
        ],
        "Rose": [
            "colorbalance=rs=0.10:gs=-0.025:bs=0.025",
            "eq=saturation=1.08"
        ],
        "Emerald": [
            "colorbalance=rs=-0.06:gs=0.11:bs=-0.04",
            "eq=saturation=1.14"
        ],
        "Amber": [
            "colorbalance=rs=0.12:gs=0.055:bs=-0.13",
            "eq=saturation=1.10"
        ]
    },
    "Food": {
        "Appetizing": ["eq=saturation=1.25:contrast=1.08", "colorbalance=rs=0.035:gs=0.02:bs=-0.035"],
        "Fresh Ingredients": ["eq=saturation=1.18:brightness=0.025", "unsharp=3:3:0.35"],
        "Warm Kitchen": ["colorbalance=rs=0.10:gs=0.035:bs=-0.10", "eq=contrast=1.05"],
        "Cafe Mood": ["eq=contrast=1.12:saturation=0.88", "vignette=PI/7"]
    },
    "Nature": {
        "Green World": ["colorbalance=gs=0.12:gm=0.06", "eq=saturation=1.18"],
        "Golden Hour": ["colorbalance=rs=0.12:gs=0.035:bs=-0.12", "eq=brightness=0.025:saturation=1.12"],
        "Misty Morning": ["gblur=sigma=0.45", "eq=contrast=0.88:saturation=0.82:brightness=0.035"],
        "Deep Forest": ["colorbalance=gs=0.10:bs=-0.035", "eq=contrast=1.14:saturation=0.92"]
    },
    "Travel": {
        "Tropical": ["colorbalance=rs=0.04:gs=0.045:bs=0.08", "eq=saturation=1.28"],
        "Desert": ["colorbalance=rs=0.14:gs=0.055:bs=-0.14", "eq=saturation=0.88:contrast=1.08"],
        "Alpine": ["colorbalance=rs=-0.06:gs=0.015:bs=0.10", "eq=contrast=1.08:saturation=0.92"],
        "Coastal": ["colorbalance=rs=-0.025:gs=0.025:bs=0.11", "eq=saturation=1.10"]
    },
    "Night": {
        "Neon Night": ["eq=contrast=1.22:saturation=1.48", "colorbalance=bs=0.08:rs=0.04"],
        "Moonlight": ["colorbalance=rs=-0.07:gs=-0.025:bs=0.13", "eq=brightness=-0.035:contrast=1.10"],
        "City Lights": ["eq=contrast=1.18:saturation=1.18", "unsharp=3:3:0.3"],
        "Low Light Lift": ["eq=brightness=0.09:gamma=1.18:contrast=1.04"]
    },
    "Wedding": {
        "Soft Romance": ["gblur=sigma=0.35", "eq=brightness=0.035:contrast=0.94:saturation=0.92"],
        "Ivory": ["colorbalance=rs=0.06:gs=0.025:bs=-0.035", "eq=brightness=0.04:saturation=0.82"],
        "Blush": ["colorbalance=rs=0.09:gs=-0.015:bs=0.035", "eq=saturation=0.92"]
    },
    "Urban": {
        "Street Contrast": ["eq=contrast=1.28:saturation=0.88", "unsharp=5:5:0.45"],
        "Concrete": ["hue=s=0", "eq=contrast=1.12:brightness=-0.015"],
        "Graffiti Pop": ["eq=contrast=1.25:saturation=1.55"]
    },
    "Film": {
        "Classic Film": ["curves=medium_contrast", "eq=saturation=0.92", "noise=alls=3:allf=t"],
        "Bleach Bypass": ["eq=contrast=1.35:saturation=0.55"],
        "Film Grain": ["noise=alls=8:allf=t", "eq=contrast=1.04"],
        "Kodak Warm": ["colorbalance=rs=0.10:gs=0.035:bs=-0.10", "eq=saturation=0.96"],
        "Fuji Cool": ["colorbalance=rs=-0.035:gs=0.015:bs=0.085", "eq=saturation=1.02"]
    },
    "Lens Effects": {
        "Soft Focus": ["gblur=sigma=1.0"],
        "Dream Lens": ["gblur=sigma=1.4", "eq=brightness=0.025:saturation=1.12"],
        "Wide Lens": ["lenscorrection=k1=-0.12:k2=0.025"],
        "Fisheye": ["lenscorrection=k1=-0.28:k2=0.08"],
        "Vignette Lens": ["vignette=PI/4"],
        "Tilt Shift": ["gblur=sigma=2.2", "eq=contrast=1.08:saturation=1.08"]
    },
    "Glitch & Distortion": {
        "RGB Split": ["rgbashift=rh=5:bh=-5"],
        "Color Offset": ["rgbashift=rv=3:gv=-2:bv=2"],
        "Digital Noise": ["noise=alls=18:allf=t"],
        "Pixel Glitch": ["scale=iw/16:ih/16:flags=neighbor", "scale=iw*16:ih*16:flags=neighbor"],
        "Barrel Distortion": ["lenscorrection=k1=-0.22:k2=0.06"],
        "Edge Distortion": ["edgedetect=low=0.08:high=0.22"]
    },
    "Light & Glow": {
        "Bloom": ["gblur=sigma=1.0", "eq=brightness=0.045:contrast=1.08"],
        "Neon Glow": ["eq=contrast=1.2:saturation=1.5", "unsharp=5:5:0.8"],
        "Light Leak Warm": ["colorbalance=rs=0.16:gs=0.045:bs=-0.12", "eq=brightness=0.04"],
        "Blue Flare": ["colorbalance=rs=-0.08:gs=0.015:bs=0.15", "eq=contrast=1.08"],
        "Halation": ["gblur=sigma=0.55", "eq=brightness=0.025:saturation=1.15"],
        "Soft Highlight": ["curves=all='0/0 0.65/0.72 1/1'", "eq=brightness=0.025"]
    },
    "Motion Effects": {
        "Ghost Trail": ["tmix=frames=3:weights='1 0.65 0.35'"],
        "Motion Blur": ["tmix=frames=2:weights='1 1'"],
        "Freeze Tone": ["eq=contrast=1.15:saturation=0.78"],
        "Speed Punch": ["eq=contrast=1.18:saturation=1.16", "unsharp=5:5:0.6"],
        "Strobe Look": ["eq=contrast=1.25:saturation=1.2"],
        "Slow Shutter": ["tmix=frames=4:weights='1 0.7 0.45 0.25'"]
    },
    "Retro Effects": {
        "VHS": ["noise=alls=12:allf=t", "eq=saturation=0.85:contrast=1.08", "rgbashift=rv=2:bv=-2"],
        "Old TV": ["hue=s=0", "noise=alls=16:allf=t"],
        "Super 8": ["curves=vintage", "noise=alls=8:allf=t", "vignette=PI/6"],
        "Polaroid": ["curves=vintage", "eq=saturation=0.78:brightness=0.035"],
        "Tape Color": ["rgbashift=rh=2:bh=-2", "eq=saturation=0.9:contrast=1.08"],
        "Film Burn": ["colorbalance=rs=0.16:gs=0.04:bs=-0.12", "eq=brightness=0.055"]
    },
    "Creative": {
        "Dreamy": [
            "gblur=sigma=1.3",
            "eq=brightness=0.025:saturation=1.12"
        ],
        "Neon": [
            "eq=contrast=1.20:saturation=1.65",
            "unsharp=3:3:0.35"
        ],
        "Pop": [
            "eq=contrast=1.18:saturation=1.45"
        ],
        "Frost": [
            "colorbalance=rs=-0.06:gs=0.015:bs=0.12",
            "eq=brightness=0.025:saturation=0.88"
        ],
        "Glow": [
            "eq=brightness=0.035:contrast=1.06",
            "gblur=sigma=0.45"
        ],
        "Comic": [
            "eq=contrast=1.45:saturation=1.35",
            "unsharp=5:5:1.0"
        ],
        "Sketch": [
            "format=gray,edgedetect=low=0.08:high=0.22"
        ],
        "Pixelate": [
            "scale=iw/12:ih/12:flags=neighbor",
            "scale=iw*12:ih*12:flags=neighbor"
        ]
    }
}



def format_srt_timestamp(seconds):
    millis = int(round(float(seconds) * 1000))
    hours, millis = divmod(millis, 3600000)
    minutes, millis = divmod(millis, 60000)
    secs, millis = divmod(millis, 1000)
    return "{:02d}:{:02d}:{:02d},{:03d}".format(hours, minutes, secs, millis)


def build_srt_content(captions):
    ordered = sorted(captions, key=lambda item: float(item[0]))
    blocks = []
    for index, (start, end, text) in enumerate(ordered, 1):
        start, end = float(start), float(end)
        caption = str(text).strip()
        if start < 0 or end <= start or not caption:
            raise ValueError("Each caption needs text and a valid start/end range.")
        blocks.append("{}\n{} --> {}\n{}".format(
            index, format_srt_timestamp(start), format_srt_timestamp(end), caption))
    return "\n\n".join(blocks) + ("\n" if blocks else "")

def build_audio_mix_graph(has_source_audio=True, source_volume=1.0, music_volume=0.35,
                          fade_in=0, fade_out=0, duration=0,
                          music_fade_in=0, music_fade_out=0):
    def bounded(value, low, high, default):
        try:
            return max(low, min(high, float(value)))
        except (TypeError, ValueError):
            return default
    source_volume = bounded(source_volume, 0, 2, 1)
    music_volume = bounded(music_volume, 0, 2, 0.35)
    fade_in = bounded(fade_in, 0, 3600, 0)
    fade_out = bounded(fade_out, 0, 3600, 0)
    duration = bounded(duration, 0, 86400, 0)
    music_fade_in = bounded(music_fade_in, 0, 3600, 0)
    music_fade_out = bounded(music_fade_out, 0, 3600, 0)
    music_chain = "volume={:.3f}".format(music_volume)
    if music_fade_in:
        music_chain += ",afade=t=in:st=0:d={:.3f}".format(music_fade_in)
    if music_fade_out and duration:
        music_chain += ",afade=t=out:st={:.3f}:d={:.3f}".format(
            max(0, duration-music_fade_out), min(music_fade_out, duration))
    if not has_source_audio:
        return "[1:a]{}[aout]".format(music_chain)
    source_chain = "volume={:.3f}".format(source_volume)
    if fade_in:
        source_chain += ",afade=t=in:st=0:d={:.3f}".format(fade_in)
    if fade_out and duration:
        source_chain += ",afade=t=out:st={:.3f}:d={:.3f}".format(
            max(0, duration-fade_out), min(fade_out, duration))
    return ("[0:a]{}[a0];[1:a]{}[a1];"
            "[a0][a1]amix=inputs=2:duration=longest:dropout_transition=2[aout]"
            ).format(source_chain, music_chain)

def filter_names():
    return {category: list(filters.keys()) for category, filters in FILTER_CATEGORIES.items()}

def escape_drawtext(value):
    return (str(value).replace("\\", "\\\\").replace(":", "\\:")
            .replace("'", "\\'").replace("%", "\\%").replace(",", "\\,")
            .replace("[", "\\[").replace("]", "\\]"))

def build_filter_chain(fmt="Original", preset="Original", adjustments=None, overlay=None, subtitle=None, overlay_image=None):
    adjustments = adjustments or {}
    if preset in (None, "", "None"):
        preset = "Original"
    overlay = overlay or {}
    chain = []
    canvas_mode = adjustments.get("canvas_mode", "Fit")
    resolution = adjustments.get("resolution", "1080p")
    dimensions = {"720p": (1280, 720), "1080p": (1920, 1080),
                  "1440p": (2560, 1440)}
    width, height = dimensions.get(resolution, dimensions["1080p"])
    if fmt == "Vertical 9:16":
        vwidth, vheight = height, width
        if canvas_mode == "Fill":
            foreground = "scale={}:{}:force_original_aspect_ratio=increase,crop={}:{}".format(
                vwidth, vheight, vwidth, vheight)
        elif canvas_mode == "Stretch":
            foreground = "scale={}:{}".format(vwidth, vheight)
        else:
            foreground = "scale={}:{}:force_original_aspect_ratio=decrease".format(vwidth, vheight)
        chain.append(
            "[0:v]split=2[bg][fg];[bg]scale={}:{}:force_original_aspect_ratio=increase,"
            "crop={}:{},boxblur=24:8[blur];[fg]".format(vwidth, vheight, vwidth, vheight) +
            foreground + "[front];[blur][front]overlay=(W-w)/2:(H-h)/2"
        )
    elif fmt == "Landscape":
        if canvas_mode == "Fill":
            chain.append("scale={}:{}:force_original_aspect_ratio=increase,crop={}:{}".format(
                width, height, width, height))
        elif canvas_mode == "Stretch":
            chain.append("scale={}:{}".format(width, height))
        else:
            chain.append("scale={}:{}:force_original_aspect_ratio=decrease,"
                         "pad={}:{}:(ow-iw)/2:(oh-ih)/2".format(width, height, width, height))
    else:
        chain.append("setsar=1")

    selected = None
    for category in FILTER_CATEGORIES.values():
        if preset in category:
            selected = category[preset]
            break
    if selected is None:
        raise ValueError("Unknown filter preset: " + str(preset))
    chain.extend(selected)

    rotation = adjustments.get("rotation", "None")
    transforms = []
    if rotation == "90° CW":
        transforms.append("transpose=clock")
    elif rotation == "180°":
        transforms.extend(["hflip", "vflip"])
    elif rotation == "90° CCW":
        transforms.append("transpose=cclock")
    if adjustments.get("flip_h", False):
        transforms.append("hflip")
    if adjustments.get("flip_v", False):
        transforms.append("vflip")
    if transforms:
        transform_chain = ",".join(transforms)
        if fmt == "Vertical 9:16":
            chain[0] = chain[0].replace("[0:v]", "[0:v]" + transform_chain + ",", 1)
        else:
            chain[0] = transform_chain + "," + chain[0]

    def number(key, default, low, high):
        try:
            value = float(adjustments.get(key, default))
        except (TypeError, ValueError):
            value = default
        return max(low, min(high, value))

    speed = number("speed", 1, 0.5, 2)
    if abs(speed - 1) > 0.0001:
        chain.append("setpts=PTS/{:.4f}".format(speed))
    brightness = number("brightness", 0, -1, 1)
    contrast = number("contrast", 1, 0, 3)
    saturation = number("saturation", 1, 0, 3)
    gamma = number("gamma", 1, 0.1, 3)
    if (brightness, contrast, saturation, gamma) != (0, 1, 1, 1):
        chain.append("eq=brightness={:.4f}:contrast={:.4f}:saturation={:.4f}:gamma={:.4f}".format(
            brightness, contrast, saturation, gamma))
    temperature = number("temperature", 0, -1, 1)
    tint = number("tint", 0, -1, 1)
    if temperature or tint:
        chain.append("colorbalance=rs={:.4f}:bs={:.4f}:gs={:.4f}:gm={:.4f}".format(
            temperature * 0.12, -temperature * 0.12, tint * 0.08, tint * 0.08))
    sharpen = number("sharpen", 0, 0, 2)
    if sharpen:
        chain.append("unsharp=5:5:{:.3f}:3:3:{:.3f}".format(sharpen, sharpen / 2))
    fade = number("fade", 0, 0, 1)
    if fade:
        chain.append("eq=contrast={:.4f}:saturation={:.4f}".format(1 - fade * 0.18, 1 - fade * 0.22))
    fade_in = number("video_fade_in", 0, 0, 10)
    fade_out = number("video_fade_out", 0, 0, 10)
    total_duration = number("duration", 0, 0, 86400)
    if speed > 0:
        total_duration = total_duration / speed
    if fade_in:
        chain.append("fade=t=in:st=0:d={:.3f}".format(fade_in))
    if fade_out and total_duration > 0:
        chain.append("fade=t=out:st={:.3f}:d={:.3f}".format(
            max(0, total_duration - fade_out), min(fade_out, total_duration)))
    vignette = number("vignette", 0, 0, 1)
    if vignette:
        chain.append("vignette=angle={:.4f}".format(0.25 + vignette * 0.55))
    blur = number("blur", 0, 0, 10)
    if blur:
        chain.append("gblur=sigma={:.3f}".format(blur))

    if subtitle:
        subtitle_path = str(subtitle).replace("\\", "/").replace(":", "\\:").replace("'", "\\'")
        subtitle_size = int(number("subtitle_size", 28, 10, 72))
        subtitle_outline = int(number("subtitle_outline", 2, 0, 8))
        subtitle_color = str(overlay.get("subtitle_color", "white"))
        subtitle_colors = {
            "white": "&H00FFFFFF", "yellow": "&H0000FFFF", "cyan": "&H00FFFF00",
            "red": "&H000000FF", "green": "&H0000FF00"
        }
        primary = subtitle_colors.get(subtitle_color, "&H00FFFFFF")
        alignment = {"Bottom": 2, "Top": 8, "Center": 5}.get(
            overlay.get("subtitle_position", "Bottom"), 2)
        subtitle_font = str(overlay.get("subtitle_font", "Arial")).replace(",", "").replace("'", "")
        style = ("FontName={},FontSize={},PrimaryColour={},OutlineColour=&H00000000,"
                 "BorderStyle=1,Outline={},Shadow=1,Alignment={}").format(
                     subtitle_font, subtitle_size, primary, subtitle_outline, alignment)
        chain.append("subtitles='{}':force_style='{}'".format(subtitle_path, style))

    text = str(overlay.get("text", "")).strip()
    if text:
        size = int(number("text_size", 48, 10, 180))
        color = str(overlay.get("color", "white"))
        allowed = {"white", "black", "yellow", "red", "blue", "lime", "cyan", "magenta"}
        if color not in allowed:
            color = "white"
        pos = overlay.get("position", "Bottom")
        y = "h-th-70" if pos == "Bottom" else ("70" if pos == "Top" else "(h-th)/2")
        font = overlay.get("font", "Sans")
        safe_font = escape_drawtext(font)
        safe_text = escape_drawtext(text)
        border = int(number("outline", 3, 0, 12))
        shadow = int(number("shadow", 2, 0, 12))
        box = "1" if overlay.get("background", False) else "0"
        text_start = number("overlay_start", 0, 0, 86400)
        text_end = number("overlay_end", 86400, text_start, 86400)
        enable = ":enable='between(t,{:.3f},{:.3f})'".format(text_start, text_end)
        chain.append("drawtext=font='{font}':text='{text}':fontcolor={color}:fontsize={size}:"
                     "borderw={border}:bordercolor=black:shadowx={shadow}:shadowy={shadow}:"
                     "box={box}:boxcolor=black@0.45:boxborderw=12:x=(w-text_w)/2:y={y}".format(
                         font=safe_font, text=safe_text, color=color, size=size,
                         border=border, shadow=shadow, box=box, y=y) + enable)
    chain.append("setsar=1")
    if overlay_image:
        opacity = number("overlay_opacity", 0.85, 0.05, 1)
        scale = number("overlay_scale", 0.25, 0.05, 1)
        placement = overlay.get("image_position", "Bottom Right")
        positions = {
            "Top Left": ("30", "30"), "Top Right": ("W-w-30", "30"),
            "Center": ("(W-w)/2", "(H-h)/2"),
            "Bottom Left": ("30", "H-h-30"),
            "Bottom Right": ("W-w-30", "H-h-30")
        }
        x, y = positions.get(placement, positions["Bottom Right"])
        base = chain[0] + "," + ",".join(chain[1:]) if fmt == "Vertical 9:16" else "[0:v]" + ",".join(chain)
        image_start = number("overlay_start", 0, 0, 86400)
        image_end = number("overlay_end", 86400, image_start, 86400)
        enable = ":enable='between(t,{:.3f},{:.3f})'".format(image_start, image_end)
        return (base + "[vbase];[1:v]format=rgba,colorchannelmixer=aa={:.3f},"
                "scale=iw*{:.3f}:ih*{:.3f}[ov];[vbase][ov]overlay=x={}:y={}:shortest=1{}[vout]"
                ).format(opacity, scale, scale, x, y, enable)
    if fmt == "Vertical 9:16":
        return chain[0] + "," + ",".join(chain[1:]) + "[vout]"
    return ",".join(chain)
