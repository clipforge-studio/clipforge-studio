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
    if fmt == "Vertical 9:16":
        chain.append(
            "[0:v]split=2[bg][fg];[bg]scale=1080:1920:force_original_aspect_ratio=increase,"
            "crop=1080:1920,boxblur=24:8[blur];[fg]scale=1080:1920:"
            "force_original_aspect_ratio=decrease[front];[blur][front]overlay=(W-w)/2:(H-h)/2"
        )
    elif fmt == "Landscape":
        chain.append("scale=1920:1080:force_original_aspect_ratio=decrease,"
                     "pad=1920:1080:(ow-iw)/2:(oh-ih)/2")
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

    def number(key, default, low, high):
        try:
            value = float(adjustments.get(key, default))
        except (TypeError, ValueError):
            value = default
        return max(low, min(high, value))

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
        style = ("FontName=Arial,FontSize={},PrimaryColour={},OutlineColour=&H00000000,"
                 "BorderStyle=1,Outline={},Shadow=1,Alignment={}").format(
                     subtitle_size, primary, subtitle_outline, alignment)
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
        chain.append("drawtext=font='{font}':text='{text}':fontcolor={color}:fontsize={size}:"
                     "borderw={border}:bordercolor=black:shadowx={shadow}:shadowy={shadow}:"
                     "box={box}:boxcolor=black@0.45:boxborderw=12:x=(w-text_w)/2:y={y}".format(
                         font=safe_font, text=safe_text, color=color, size=size,
                         border=border, shadow=shadow, box=box, y=y))
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
        base = chain[0] + "," + ",".join(chain[1:]) if fmt == "Vertical 9:16" else "[0:v]," + ",".join(chain)
        return (base + "[vbase];[1:v]format=rgba,colorchannelmixer=aa={:.3f},"
                "scale=iw*{:.3f}:ih*{:.3f}[ov];[vbase][ov]overlay=x={}:y={}:shortest=1[vout]"
                ).format(opacity, scale, scale, x, y)
    if fmt == "Vertical 9:16":
        return chain[0] + "," + ",".join(chain[1:]) + "[vout]"
    return ",".join(chain)
