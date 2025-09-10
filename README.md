# Classroom Animation Script — Mindful Diabetes Inc.

This Python project generates a fun, animated classroom scene for **Mindful Diabetes Inc.’s upcoming live animated education series**. It’s designed to make science education more engaging by combining chalkboard writing, character animation, playful chaos, and branded elements into a dynamic video.

The script uses **Pygame** to render and save frames, then assembles them into a smooth video using **FFmpeg**.

---

## ✨ Features

* **Chalkboard Writing Effect**: A teacher character progressively writes a full educational message across 10 seconds.
* **Teacher Animation**:

  * While writing: alternates arm movement with a pencil.
  * After finishing: turns to the audience and waves with a smile.
* **Chaos Characters**: Colorful “animal” shapes move in the background to add playfulness.
* **MDI Branding**:

  * MDI logo on the classroom wall.
  * Animated logo expansion effect at the end.
  * Logo also placed on the teacher’s shirt.
* **Full Frame Export**: Every frame saved as `.png` to `frames/` folder.
* **Video Output**: FFmpeg stitches frames into `animation_video.mp4`.

---

## 🛠 Requirements

* **Python** 3.9+
* **Pygame**
* **FFmpeg** (must be installed and accessible in PATH)

### Install dependencies

```bash
pip install pygame
```

Install FFmpeg:

* **macOS**:

  ```bash
  brew install ffmpeg
  ```
* **Windows**:

  ```bash
  choco install ffmpeg
  ```
* **Linux**:

  ```bash
  sudo apt-get install ffmpeg
  ```

---

## 📂 Project Structure

```
.
├── animation_script.py      # Main script (this file)
├── MDI_Logo.jpg             # Logo image (required)
├── frames/                  # Frames are saved here (auto-created)
└── animation_video.mp4      # Final video output
```

---

## ▶️ Usage

Run the script directly:

```bash
python animation_script.py
```

What happens:

1. Creates a `frames/` folder if it doesn’t exist.
2. Renders each frame of the animation (1280×720, 30 fps).
3. Saves frames as `frame_0000.png`, `frame_0001.png`, … in `frames/`.
4. Calls **FFmpeg** to compile frames into `animation_video.mp4`.

---

## ⚙️ Customization

* **Whiteboard Text**: Change the `WHITEBOARD_TEXT` string near the top:

  ```python
  WHITEBOARD_TEXT = "Your educational message here!"
  ```
* **Duration**: Adjust `DURATION = 10` (in seconds).
* **Resolution**: Default is 1280×720 (16:9). Update `SCREEN_WIDTH` and `SCREEN_HEIGHT`.
* **Logo**:

  * Replace `MDI_Logo.jpg` with your preferred logo file.
  * Adjust position via `LOGO_INITIAL_POSITION`.
* **Chaos Characters**: Colors and positions are randomized for extra fun.

---

## 🎯 Purpose

This project is part of **Mindful Diabetes Inc.’s education strategy**. By blending **science, storytelling, and animation**, we aim to:

* Make complex biology concepts more accessible.
* Boost audience engagement across social platforms.
* Deliver fun, branded, professional-quality content.

---

## 📌 Notes

* Expect the frame export process to take some time (10s @ 30 fps → \~300 frames).
* Ensure `MDI_Logo.jpg` is present in the same directory.
* You can edit the `generate_video()` function to adjust FFmpeg settings (quality, codec, bitrate).

---

## 📽 Example Output

* A 10-second video with:

  * Teacher writing on a chalkboard.
  * Message fully revealed: *“The Secret to Cleaning Up Your Cells: How Exercise Recycles Proteins for Better Brain Health!”*
  * Teacher turns, waves, and logo expands dramatically.

The result is saved as `animation_video.mp4` in the project directory.
