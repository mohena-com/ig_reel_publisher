from __future__ import annotations

import re
import random
import shutil
import subprocess
from pathlib import Path


WIDTH = 1080
HEIGHT = 1920
FPS = 30
SECONDS_PER_SLIDE = 4
TOTAL_DURATION = SECONDS_PER_SLIDE * 6


def natural_key(path: Path):
    return [
        int(part) if part.isdigit() else part.lower()
        for part in re.split(r"(\d+)", path.name)
    ]


def choose_random_music(music_dir: Path) -> Path:
    if not music_dir.is_dir():
        raise RuntimeError(
            f"Music directory does not exist: {music_dir}"
        )

    tracks = sorted(
        [
            path
            for path in music_dir.iterdir()
            if path.is_file() and path.suffix.lower() == ".mp3"
        ],
        key=natural_key,
    )

    if not tracks:
        raise RuntimeError(
            f"No MP3 files found in music directory: {music_dir}"
        )

    return random.choice(tracks)


def find_slides(input_dir: Path) -> list[Path]:
    if not input_dir.is_dir():
        raise RuntimeError(
            f"Input directory does not exist: {input_dir}"
        )

    allowed = {".png", ".jpg", ".jpeg", ".webp"}

    slides = sorted(
        [
            p
            for p in input_dir.iterdir()
            if p.is_file() and p.suffix.lower() in allowed
        ],
        key=natural_key,
    )

    if len(slides) != 6:
        names = "\n".join(f"  {p.name}" for p in slides)
        raise RuntimeError(
            f"Expected exactly 6 slide images in {input_dir}, "
            f"found {len(slides)}.\n{names}"
        )

    return slides


def create_reel(
    slides: list[Path],
    output_path: Path,
    music_path: Path | None = None,
) -> Path:
    ffmpeg = shutil.which("ffmpeg")

    if not ffmpeg:
        raise RuntimeError(
            "FFmpeg was not found. Install it with:\n"
            "  brew install ffmpeg"
        )

    if len(slides) != 6:
        raise ValueError(
            f"Expected 6 slides, received {len(slides)}."
        )

    if music_path is not None and not music_path.is_file():
        raise RuntimeError(
            f"Music file does not exist: {music_path}"
        )

    output_path.parent.mkdir(parents=True, exist_ok=True)

    command = [ffmpeg, "-y"]

    for slide in slides:
        command.extend(
            [
                "-loop", "1",
                "-t", str(SECONDS_PER_SLIDE),
                "-i", str(slide),
            ]
        )

    if music_path is not None:
        command.extend(
            [
                "-stream_loop", "-1",
                "-i", str(music_path),
            ]
        )

    filters = []

    for index in range(6):
        # Full-frame blurred background prevents cropping.
        filters.append(
            f"[{index}:v]"
            f"scale={WIDTH}:{HEIGHT}:"
            f"force_original_aspect_ratio=increase,"
            f"crop={WIDTH}:{HEIGHT},"
            f"boxblur=20:2,"
            f"setsar=1,"
            f"fps={FPS}"
            f"[bg{index}]"
        )

        # Sharp foreground keeps the complete slide visible.
        filters.append(
            f"[{index}:v]"
            f"scale={WIDTH}:{HEIGHT}:"
            f"force_original_aspect_ratio=decrease,"
            f"pad={WIDTH}:{HEIGHT}:"
            f"(ow-iw)/2:(oh-ih)/2:color=black,"
            f"setsar=1,"
            f"fps={FPS}"
            f"[fg{index}]"
        )

        filters.append(
            f"[bg{index}][fg{index}]"
            f"overlay=(W-w)/2:(H-h)/2"
            f"[v{index}]"
        )

    joined = "".join(f"[v{i}]" for i in range(6))

    filters.append(
        f"{joined}"
        f"concat=n=6:v=1:a=0,"
        f"format=yuv420p"
        f"[outv]"
    )

    if music_path is not None:
        filters.append(
            f"[6:a]"
            f"atrim=duration={TOTAL_DURATION},"
            f"asetpts=N/SR/TB,"
            f"afade=t=out:st={TOTAL_DURATION - 1}:d=1"
            f"[outa]"
        )

    command.extend(
        [
            "-filter_complex",
            ";".join(filters),
            "-map",
            "[outv]",
            *(["-map", "[outa]"] if music_path is not None else []),
            "-c:v",
            "libx264",
            "-preset",
            "medium",
            "-crf",
            "20",
            "-pix_fmt",
            "yuv420p",
            "-movflags",
            "+faststart",
            *(
                [
                    "-c:a", "aac",
                    "-b:a", "192k",
                ]
                if music_path is not None
                else ["-an"]
            ),
            str(output_path),
        ]
    )

    print("Creating 24-second Reel...")
    if music_path is not None:
        print(f"  Music   → {music_path}")
    print(f"  Slide 1 → 4 seconds")
    print(f"  Slide 2 → 4 seconds")
    print(f"  Slide 3 → 4 seconds")
    print(f"  Slide 4 → 4 seconds")
    print(f"  Slide 5 → 4 seconds")
    print(f"  Slide 6 → 4 seconds")
    print(f"  Output  → {output_path}")

    result = subprocess.run(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    if result.returncode != 0:
        raise RuntimeError(
            "FFmpeg failed:\n\n"
            + result.stderr[-6000:]
        )

    if not output_path.exists():
        raise RuntimeError(
            f"FFmpeg completed but output was not created: "
            f"{output_path}"
        )

    print("Reel created successfully.")
    return output_path
