#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
run_avatar_talker.py

Run from inside your animation-project directory.

What it does:
- Finds avatar files in ./images that look like avatar images
- Lets you choose one
- Lets you choose an audio folder in the current working directory
- If the chosen folder has one MP3, it uses it automatically
- If the chosen folder has multiple MP3s, it asks which one to use
- For long audio, splits on nearby silence into chunk lengths that target 45-50s
- Runs SadTalker inference for each chunk
- Concatenates the chunk videos back into one final MP4
- Saves output into ./results/<job_name>/

Assumptions:
- This script is placed in the animation-project root
- SadTalker lives at ./SadTalker
- Avatar images live at ./images
- Audio folders are subfolders in the current working directory
"""

from __future__ import annotations

import os
import re
import sys
import math
import shutil
import subprocess
from pathlib import Path
from datetime import datetime

PYTHON_BIN_DIR = Path(sys.executable).resolve().parent
os.environ["PATH"] = f"{PYTHON_BIN_DIR}{os.pathsep}{os.environ.get('PATH', '')}"

from pydub import AudioSegment
from pydub.silence import detect_silence


# -----------------------------
# Config
# -----------------------------
PROJECT_ROOT = Path.cwd()
IMAGES_DIR = PROJECT_ROOT / "images"
SADTALKER_DIR = PROJECT_ROOT / "SadTalker"
RESULTS_ROOT = PROJECT_ROOT / "results"

# Only treat files that look like actual avatars as selectable avatars.
# This avoids things like strips.png, dropdown-icon.png, etc.
AVATAR_PATTERN = re.compile(r"^avatar.*\.(png|jpg|jpeg|webp)$", re.IGNORECASE)

# Allowed audio file types. User asked for mp3, but wav support is handy too.
AUDIO_EXTENSIONS = {".mp3", ".wav"}

# Known non-audio / non-folder project directories we do not want shown as audio choices
EXCLUDED_DIR_NAMES = {
    "SadTalker",
    "images",
    "results",
    ".git",
    "__pycache__",
    ".venv",
    "venv",
    "env",
}

# Long-form chunking settings.
MIN_CHUNK_MS = 45_000
MAX_CHUNK_MS = 50_000
TARGET_CHUNK_MS = 48_000
MIN_SILENCE_LEN_MS = 350
SILENCE_SEEK_STEP_MS = 10


# -----------------------------
# Helpers
# -----------------------------
def die(msg: str, code: int = 1) -> None:
    print(f"❌ {msg}")
    sys.exit(code)


def info(msg: str) -> None:
    print(f"ℹ️  {msg}")


def ok(msg: str) -> None:
    print(f"✅ {msg}")


def ask_index(items: list[Path], title: str) -> Path:
    if not items:
        die(f"No options found for: {title}")

    print(f"\n{title}")
    for i, item in enumerate(items, start=1):
        print(f"  {i}. {item.name}")

    while True:
        raw = input("\nEnter number: ").strip()
        if not raw.isdigit():
            print("Please enter a valid number.")
            continue

        idx = int(raw)
        if 1 <= idx <= len(items):
            return items[idx - 1]

        print("Selection out of range.")


def sanitize_name(text: str) -> str:
    text = re.sub(r"\.[^.]+$", "", text)  # strip extension
    text = re.sub(r"[^A-Za-z0-9._-]+", "_", text)
    text = re.sub(r"_+", "_", text).strip("_")
    return text or "job"


def format_seconds(ms: int) -> str:
    return f"{ms / 1000:.2f}s"


def find_avatars(images_dir: Path) -> list[Path]:
    if not images_dir.exists():
        die(f"Images directory not found: {images_dir}")

    avatars = [
        p for p in images_dir.iterdir()
        if p.is_file() and AVATAR_PATTERN.match(p.name)
    ]
    return sorted(avatars, key=lambda p: p.name.lower())


def find_audio_directories(project_root: Path) -> list[Path]:
    dirs = []
    for p in project_root.iterdir():
        if not p.is_dir():
            continue
        if p.name in EXCLUDED_DIR_NAMES:
            continue

        has_audio = any(
            child.is_file() and child.suffix.lower() in AUDIO_EXTENSIONS
            for child in p.iterdir()
        )
        if has_audio:
            dirs.append(p)

    return sorted(dirs, key=lambda p: p.name.lower())


def choose_audio_file(audio_dir: Path) -> Path:
    audio_files = sorted(
        [
            p for p in audio_dir.iterdir()
            if p.is_file() and p.suffix.lower() in AUDIO_EXTENSIONS
        ],
        key=lambda p: p.name.lower()
    )

    if not audio_files:
        die(f"No audio files found in: {audio_dir}")

    mp3_files = [p for p in audio_files if p.suffix.lower() == ".mp3"]
    wav_files = [p for p in audio_files if p.suffix.lower() == ".wav"]

    preferred = mp3_files if mp3_files else wav_files

    if len(preferred) == 1:
        info(f"Using audio automatically: {preferred[0].name}")
        return preferred[0]

    return ask_index(preferred, f"Choose audio from '{audio_dir.name}':")


def find_python_executable() -> str:
    return sys.executable or "python"


def validate_environment() -> None:
    if not SADTALKER_DIR.exists():
        die(f"SadTalker directory not found: {SADTALKER_DIR}")

    inference_script = SADTALKER_DIR / "inference.py"
    if not inference_script.exists():
        die(f"SadTalker inference.py not found: {inference_script}")

    checkpoints_dir = SADTALKER_DIR / "checkpoints"
    if not checkpoints_dir.exists():
        info("Warning: ./SadTalker/checkpoints was not found.")
        info("If models are not already downloaded, SadTalker will fail.")

    if shutil.which("ffmpeg") is None:
        info("Warning: ffmpeg is not in PATH. SadTalker may fail without it.")


def build_default_job_name(audio_file: Path, avatar_file: Path) -> str:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"{sanitize_name(audio_file.stem)}__{sanitize_name(avatar_file.stem)}__{timestamp}"


def build_output_dir(job_name: str) -> Path:
    outdir = RESULTS_ROOT / job_name
    outdir.mkdir(parents=True, exist_ok=True)
    return outdir


def build_sadtalker_env() -> dict[str, str]:
    env = os.environ.copy()
    env.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")
    env.setdefault("OMP_NUM_THREADS", "1")
    env.setdefault("MKL_NUM_THREADS", "1")
    env.setdefault("VECLIB_MAXIMUM_THREADS", "1")
    env.setdefault("NUMEXPR_NUM_THREADS", "1")
    env.setdefault("PYTORCH_ENABLE_MPS_FALLBACK", "1")
    env.setdefault("NUMBA_CACHE_DIR", "/tmp/numba-cache")
    env.setdefault("MPLCONFIGDIR", "/tmp/matplotlib-cache")
    return env


def run_sadtalker(
    source_image: Path,
    driven_audio: Path,
    result_dir: Path,
    preprocess: str = "full",
    still: bool = True,
    enhancer: str | None = None,
) -> int:
    python_exe = find_python_executable()
    inference_py = SADTALKER_DIR / "inference.py"

    cmd = [
        python_exe,
        str(inference_py),
        "--driven_audio", str(driven_audio),
        "--source_image", str(source_image),
        "--result_dir", str(result_dir),
        "--preprocess", preprocess,
    ]

    if still:
        cmd.append("--still")

    if enhancer:
        cmd.extend(["--enhancer", enhancer])

    print("\n🚀 Running SadTalker...\n")
    print("Command:")
    print(" ".join(f'"{c}"' if " " in c else c for c in cmd))
    print()

    proc = subprocess.run(cmd, cwd=SADTALKER_DIR, env=build_sadtalker_env())
    return proc.returncode


def find_generated_videos(result_dir: Path) -> list[Path]:
    videos = [
        p for p in result_dir.rglob("*.mp4")
        if p.is_file() and not p.name.startswith("temp_")
    ]
    return sorted(videos)


def choose_best_generated_video(result_dir: Path) -> Path | None:
    videos = find_generated_videos(result_dir)
    if not videos:
        return None

    root = result_dir.resolve()
    top_level = [video for video in videos if video.parent.resolve() == root]
    if top_level:
        return sorted(top_level)[-1]

    full_videos = [video for video in videos if video.stem.endswith("_full")]
    if full_videos:
        return sorted(full_videos)[-1]

    return videos[-1]


def detect_silence_midpoints(audio: AudioSegment) -> list[int]:
    silence_thresh = audio.dBFS - 16
    silences = detect_silence(
        audio,
        min_silence_len=MIN_SILENCE_LEN_MS,
        silence_thresh=silence_thresh,
        seek_step=SILENCE_SEEK_STEP_MS,
    )
    return [(start + end) // 2 for start, end in silences]


def choose_split_point(
    silence_midpoints: list[int],
    min_end: int,
    max_end: int,
    target_end: int,
) -> int:
    candidates = [
        midpoint for midpoint in silence_midpoints
        if min_end <= midpoint <= max_end
    ]
    if not candidates:
        return max_end

    return min(candidates, key=lambda point: (abs(point - target_end), point))


def rebalance_tail_chunk(
    chunks: list[tuple[int, int]],
    silence_midpoints: list[int],
) -> list[tuple[int, int]]:
    if len(chunks) < 2:
        return chunks

    prev_start, _ = chunks[-2]
    last_start, last_end = chunks[-1]
    last_duration = last_end - last_start
    if last_duration >= MIN_CHUNK_MS:
        return chunks

    min_end = prev_start + MIN_CHUNK_MS
    max_end = min(prev_start + MAX_CHUNK_MS, last_end - MIN_CHUNK_MS)
    if max_end < min_end:
        return chunks

    target_end = min(prev_start + TARGET_CHUNK_MS, max_end)
    new_split = choose_split_point(silence_midpoints, min_end, max_end, target_end)
    chunks[-2] = (prev_start, new_split)
    chunks[-1] = (new_split, last_end)
    return chunks


def plan_audio_chunks(audio: AudioSegment) -> list[tuple[int, int]]:
    total_ms = len(audio)
    if total_ms <= MAX_CHUNK_MS:
        return [(0, total_ms)]

    if total_ms < MIN_CHUNK_MS * 2:
        info(
            "Audio is longer than 50s but shorter than 90s, so it cannot be split into "
            "all-45-50s chunks cleanly. Running it as one piece."
        )
        return [(0, total_ms)]

    silence_midpoints = detect_silence_midpoints(audio)
    min_chunk_count = math.ceil(total_ms / MAX_CHUNK_MS)
    max_chunk_count = total_ms // MIN_CHUNK_MS
    target_chunk_count = round(total_ms / TARGET_CHUNK_MS)
    chunk_count = min(max(target_chunk_count, min_chunk_count), max_chunk_count)

    chunks: list[tuple[int, int]] = []
    start = 0

    for chunk_index in range(1, chunk_count):
        remaining_chunks_after = chunk_count - chunk_index
        remaining_ms = total_ms - start
        ideal_duration = round(remaining_ms / (remaining_chunks_after + 1))

        min_end = max(
            start + MIN_CHUNK_MS,
            total_ms - (remaining_chunks_after * MAX_CHUNK_MS),
        )
        max_end = min(
            start + MAX_CHUNK_MS,
            total_ms - (remaining_chunks_after * MIN_CHUNK_MS),
        )

        if max_end < min_end:
            break

        target_end = min(max(start + ideal_duration, min_end), max_end)
        cut = choose_split_point(silence_midpoints, min_end, max_end, target_end)
        chunks.append((start, cut))
        start = cut

    chunks.append((start, total_ms))
    return chunks


def write_chunk_plan(chunk_ranges: list[tuple[int, int]], plan_path: Path) -> None:
    lines = ["chunk\tstart_s\tend_s\tduration_s\n"]
    for index, (start_ms, end_ms) in enumerate(chunk_ranges, start=1):
        duration_ms = end_ms - start_ms
        lines.append(
            f"{index}\t{start_ms / 1000:.3f}\t{end_ms / 1000:.3f}\t{duration_ms / 1000:.3f}\n"
        )
    plan_path.write_text("".join(lines), encoding="utf-8")


def export_audio_chunks(
    audio: AudioSegment,
    audio_file: Path,
    chunk_ranges: list[tuple[int, int]],
    chunks_dir: Path,
) -> list[Path]:
    chunks_dir.mkdir(parents=True, exist_ok=True)
    chunk_paths: list[Path] = []

    for index, (start_ms, end_ms) in enumerate(chunk_ranges, start=1):
        chunk = audio[start_ms:end_ms]
        chunk_name = (
            f"chunk_{index:03d}_"
            f"{start_ms // 1000:05d}s_"
            f"{end_ms // 1000:05d}s.wav"
        )
        chunk_path = chunks_dir / chunk_name
        chunk.export(chunk_path, format="wav")
        chunk_paths.append(chunk_path)

    info(f"Exported {len(chunk_paths)} audio chunks for {audio_file.name}.")
    return chunk_paths


def concat_videos(video_paths: list[Path], output_path: Path) -> Path:
    ffmpeg_path = shutil.which("ffmpeg")
    if ffmpeg_path is None:
        die("ffmpeg is required to concatenate chunk videos, but it is not on PATH.")

    concat_list = output_path.parent / "concat_list.txt"
    lines = []
    for video_path in video_paths:
        escaped = str(video_path.resolve()).replace("'", r"'\''")
        lines.append(f"file '{escaped}'\n")
    concat_list.write_text("".join(lines), encoding="utf-8")

    copy_cmd = [
        ffmpeg_path,
        "-y",
        "-hide_banner",
        "-loglevel",
        "error",
        "-f",
        "concat",
        "-safe",
        "0",
        "-i",
        str(concat_list),
        "-c",
        "copy",
        str(output_path),
    ]

    copy_proc = subprocess.run(copy_cmd, capture_output=True, text=True)
    if copy_proc.returncode == 0:
        ok(f"Concatenated {len(video_paths)} chunk videos into {output_path.name}")
        return output_path

    output_path.unlink(missing_ok=True)
    reencode_cmd = [
        ffmpeg_path,
        "-y",
        "-hide_banner",
        "-loglevel",
        "error",
        "-f",
        "concat",
        "-safe",
        "0",
        "-i",
        str(concat_list),
        "-c:v",
        "libx264",
        "-pix_fmt",
        "yuv420p",
        "-c:a",
        "aac",
        "-movflags",
        "+faststart",
        str(output_path),
    ]
    reencode_proc = subprocess.run(reencode_cmd, capture_output=True, text=True)
    if reencode_proc.returncode != 0:
        die(
            "ffmpeg failed while concatenating chunk videos.\n"
            f"Copy stderr: {copy_proc.stderr.strip()}\n"
            f"Re-encode stderr: {reencode_proc.stderr.strip()}"
        )

    ok(f"Concatenated {len(video_paths)} chunk videos into {output_path.name}")
    return output_path


def run_chunked_job(
    source_image: Path,
    audio_file: Path,
    result_dir: Path,
    preprocess: str,
    still: bool,
    enhancer: str | None,
) -> list[Path]:
    audio = AudioSegment.from_file(audio_file)
    duration_ms = len(audio)
    info(f"Audio duration: {format_seconds(duration_ms)}")

    chunk_ranges = plan_audio_chunks(audio)
    if len(chunk_ranges) == 1 and chunk_ranges[0] == (0, duration_ms):
        info("Using a single SadTalker run for this audio file.")
        rc = run_sadtalker(
            source_image=source_image,
            driven_audio=audio_file,
            result_dir=result_dir,
            preprocess=preprocess,
            still=still,
            enhancer=enhancer,
        )
        if rc != 0:
            die("SadTalker failed. Check the terminal output above.")

        video = choose_best_generated_video(result_dir)
        if video is None:
            die(f"SadTalker finished, but no MP4 was found under {result_dir}")
        return [video]

    info(f"Splitting long audio into {len(chunk_ranges)} silence-aware chunks.")
    for index, (start_ms, end_ms) in enumerate(chunk_ranges, start=1):
        info(
            f"Chunk {index:02d}: {format_seconds(start_ms)} -> "
            f"{format_seconds(end_ms)} ({format_seconds(end_ms - start_ms)})"
        )

    write_chunk_plan(chunk_ranges, result_dir / "chunk_plan.tsv")
    chunk_audio_dir = result_dir / "audio_chunks"
    chunk_paths = export_audio_chunks(audio, audio_file, chunk_ranges, chunk_audio_dir)

    chunk_video_paths: list[Path] = []
    chunk_runs_dir = result_dir / "chunk_runs"
    chunk_runs_dir.mkdir(parents=True, exist_ok=True)

    for index, chunk_path in enumerate(chunk_paths, start=1):
        chunk_result_dir = chunk_runs_dir / f"chunk_{index:03d}"
        chunk_result_dir.mkdir(parents=True, exist_ok=True)
        info(f"Starting chunk {index}/{len(chunk_paths)}: {chunk_path.name}")

        rc = run_sadtalker(
            source_image=source_image,
            driven_audio=chunk_path,
            result_dir=chunk_result_dir,
            preprocess=preprocess,
            still=still,
            enhancer=enhancer,
        )
        if rc != 0:
            die(
                f"SadTalker failed on chunk {index} "
                f"({chunk_path.name}). Check the terminal output above."
            )

        chunk_video = choose_best_generated_video(chunk_result_dir)
        if chunk_video is None:
            die(f"No MP4 was found for chunk {index} under {chunk_result_dir}")
        chunk_video_paths.append(chunk_video)

    final_output = result_dir / (
        f"{sanitize_name(audio_file.stem)}__{sanitize_name(source_image.stem)}__stitched.mp4"
    )
    concat_videos(chunk_video_paths, final_output)
    return [final_output]


# -----------------------------
# Main
# -----------------------------
def main() -> None:
    print("\n🎭 SadTalker Avatar Runner\n")
    print(f"Project root : {PROJECT_ROOT}")
    print(f"Images dir   : {IMAGES_DIR}")
    print(f"SadTalker dir: {SADTALKER_DIR}")

    validate_environment()

    avatars = find_avatars(IMAGES_DIR)
    if not avatars:
        die(
            "No avatar images found in ./images matching names like avatar1.png, avatar2.png, etc."
        )

    avatar = ask_index(avatars, "Choose an avatar image:")

    audio_dirs = find_audio_directories(PROJECT_ROOT)
    if not audio_dirs:
        die("No audio directories with .mp3 or .wav files were found in the current directory.")

    audio_dir = ask_index(audio_dirs, "Choose an audio folder:")
    audio_file = choose_audio_file(audio_dir)

    print("\nSelected:")
    print(f"  Avatar : {avatar}")
    print(f"  Audio  : {audio_file}")

    default_job_name = build_default_job_name(audio_file, avatar)
    custom_job_name = input(
        f"\nOutput folder name [default: {default_job_name}]: "
    ).strip()
    job_name = sanitize_name(custom_job_name) if custom_job_name else default_job_name

    preprocess = input("\nPreprocess mode [full  / crop / resize / extcrop / extfull]: ").strip().lower()
    if not preprocess:
        preprocess = "full"

    still_raw = input("Use --still mode? [Y/n]: ").strip().lower()
    still = still_raw not in {"n", "no"}

    enhancer_raw = input("Enhancer [blank = none, or type gfpgan]: ").strip().lower()
    enhancer = enhancer_raw if enhancer_raw else None

    result_dir = build_output_dir(job_name)
    videos = run_chunked_job(
        source_image=avatar,
        audio_file=audio_file,
        result_dir=result_dir,
        preprocess=preprocess,
        still=still,
        enhancer=enhancer,
    )

    if videos:
        ok("Video created successfully.")
        for video in videos:
            print(f"   -> {video}")
        chunk_plan = result_dir / "chunk_plan.tsv"
        if chunk_plan.exists():
            print(f"   -> chunk plan: {chunk_plan}")
    else:
        info("SadTalker finished, but no MP4 was found in the result directory.")
        info(f"Check manually: {result_dir}")


if __name__ == "__main__":
    main()
