# Animation Project

This repo contains two related production workflows for Mindful Diabetes Inc.:

1. `1_SeriesOpener.py`
Creates the classroom-style animated intro with the teacher, chalkboard writing, logo, and branded motion graphics.

2. `2_TalkingHeads.py`
Runs a patched local copy of SadTalker to turn still avatar images into talking-head videos from narration audio, including long-form audio chunking for Apple Silicon Macs.

## What Is In This Repo

- `1_SeriesOpener.py`
  Main intro animation generator.
- `2_TalkingHeads.py`
  Interactive runner for avatar-driven talking head videos.
- `SadTalker/`
  Local embedded SadTalker codebase with Apple Silicon / MPS compatibility fixes kept in-repo.
- `images/`
  Source avatar images and visual assets.
- `TEST/`
  Small test audio files and local validation material.
- `gfpgan/`
  Optional face enhancement support.

## SadTalker In This Repo

This project keeps a working, patched copy of SadTalker inside the repo so the exact code that works on this machine can be versioned and reused.

Key local fixes include:

- Apple Silicon MPS device selection in `SadTalker/inference.py`
- MPS-safe coordinate grid creation in `SadTalker/src/facerender/modules/util.py`
- MPS-safe tensor allocation in `SadTalker/src/facerender/modules/dense_motion.py`

The model weights are intentionally not tracked in git.

## Long-Form Talking Head Workflow

`2_TalkingHeads.py` is designed for both short clips and longer narration.

For long audio it will:

- load the selected `.mp3` or `.wav`
- detect quiet spots with `pydub`
- split near silence when possible
- keep chunk lengths between 45 and 50 seconds when feasible
- export chunk audio files
- run SadTalker once per chunk
- stitch the final chunk videos back into one MP4 with `ffmpeg`

This avoids trying to hold a full multi-minute SadTalker render in memory at once.

### Important behavior

- If the audio is under 50 seconds, it runs as one piece.
- If the audio is between 50 and 90 seconds, it may still stay as one piece because it is impossible to split that duration into chunks that are all between 45 and 50 seconds.
- If no silence is found in the allowed window, the script falls back to a hard cut at the boundary.

## Requirements

- Python 3.10 recommended
- A working local environment with PyTorch MPS support on Apple Silicon
- `ffmpeg` and `ffprobe` available
- `pygame` for the classroom intro workflow
- `pydub` for silence-aware audio chunking

If you are using the local conda environment that already works for this repo, activate it before running the talking-head workflow.

## Model Weights

The following large runtime assets are expected locally but should not be committed:

- `SadTalker/checkpoints/`
- `gfpgan/weights/`

That includes `.pth`, `.tar`, `.safetensors`, face landmark models, BFM assets, and other downloaded checkpoints.

## Usage

### 1. Classroom Intro

Run:

```bash
python 1_SeriesOpener.py
```

This generates the animated classroom opener with the chalkboard, teacher motion, branding, and FFmpeg video assembly.

### 2. Talking Head Video

Run:

```bash
python 2_TalkingHeads.py
```

The script will prompt you for:

- avatar image
- audio folder
- audio file
- output folder name
- preprocess mode
- whether to use `--still`
- optional enhancer such as `gfpgan`

### Output layout

Talking-head jobs are saved under:

```text
results/<your_folder_name>/
```

For chunked jobs, that folder will typically include:

```text
results/<your_folder_name>/
├── audio_chunks/
├── chunk_plan.tsv
├── chunk_runs/
├── concat_list.txt
└── <final_stitched_video>.mp4
```

`chunk_plan.tsv` records the chosen split points and durations for the run.

## Suggested Workflow For Long Videos

For multi-minute narration:

1. Put the narration audio in its own folder.
2. Run `python 2_TalkingHeads.py`.
3. Choose the avatar and the audio folder.
4. Give the job a clean output name like `Exercise_and_the_brain`.
5. Let the script split, render, and stitch automatically.

This is the preferred workflow for 5-10 minute content on Apple Silicon.

## Notes On Performance

- `Face Renderer` on MPS is the main GPU-heavy part and should show `Using device: mps` when the patched SadTalker path is working.
- `seamlessClone` and `gfpgan` enhancement are much slower than the initial face render and can dominate total runtime for long videos.
- The OpenCV `mp4v` fallback warning is usually noisy but not fatal.

## Repo Structure

```text
.
├── 1_SeriesOpener.py
├── 2_TalkingHeads.py
├── images/
├── TEST/
├── SadTalker/
├── gfpgan/
├── MDI_Logo.jpg
├── LICENSE.md
└── README.md
```

## Git Notes

The code for the patched SadTalker integration should stay in the repo.

The following should not be committed:

- model weights
- generated results
- chunk audio exports
- local caches
- temporary macOS files

Use the root `.gitignore` in this repo before pushing to GitHub.
