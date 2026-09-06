from __future__ import annotations

import re
import shutil
import subprocess
from pathlib import Path

WIDTH = 1080
HEIGHT = 1920
FPS = 30
SECONDS_PER_SLIDE = 4


def natural_key(path: Path):
    return [
        int(x) if x.isdigit() else x.lower()
        for x in re.split(r"(\d+)", path.name)
    ]


def find_slides(carousel_dir: Path) -> list[Path]:
    if not carousel_dir.is_dir():
        raise RuntimeError(f"Carousel directory not found: {carousel_dir}")

    allowed = {".png", ".jpg", ".jpeg", ".webp"}
    slides = sorted(
        [
            p for p in carousel_dir.iterdir()
            if p.is_file() and p.suffix.lower() in allowed
        ],
        key=natural_key,
    )

    if len(slides) != 6:
        raise RuntimeError(
            f"Expected exactly 6 slide images, found {len(slides)}"
        )

    return slides


def create_reel(slides: list[Path], output: Path) -> Path:
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        raise RuntimeError("FFmpeg is not installed in the container.")

    output.parent.mkdir(parents=True, exist_ok=True)

    cmd = [ffmpeg, "-y"]

    for slide in slides:
        cmd += [
            "-loop", "1",
            "-t", str(SECONDS_PER_SLIDE),
            "-i", str(slide),
        ]

    filters = []

    for i in range(6):
        # Blurred full-frame background.
        filters.append(
            f"[{i}:v]"
            f"scale={WIDTH}:{HEIGHT}:force_original_aspect_ratio=increase,"
            f"crop={WIDTH}:{HEIGHT},"
            f"boxblur=20:2,"
            f"setsar=1,fps={FPS}[bg{i}]"
        )

        # Sharp slide, fully visible.
        filters.append(
            f"[{i}:v]"
            f"scale={WIDTH}:{HEIGHT}:force_original_aspect_ratio=decrease,"
            f"pad={WIDTH}:{HEIGHT}:(ow-iw)/2:(oh-ih)/2:color=black@0,"
            f"setsar=1,fps={FPS}[fg{i}]"
        )

        filters.append(
            f"[bg{i}][fg{i}]overlay=(W-w)/2:(H-h)/2[slide{i}]"
        )

    joined = "".join(f"[slide{i}]" for i in range(6))
    filters.append(
        f"{joined}concat=n=6:v=1:a=0,"
        f"format=yuv420p[outv]"
    )

    cmd += [
        "-filter_complex", ";".join(filters),
        "-map", "[outv]",
        "-c:v", "libx264",
        "-preset", "medium",
        "-crf", "20",
        "-pix_fmt", "yuv420p",
        "-movflags", "+faststart",
        "-an",
        str(output),
    ]

    result = subprocess.run(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    if result.returncode != 0:
        raise RuntimeError(
            "FFmpeg failed:\n" + result.stderr[-5000:]
        )

    if not output.exists():
        raise RuntimeError(f"Video was not created: {output}")

    return output
