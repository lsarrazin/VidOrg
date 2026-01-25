# Video Sorter

**Video Sorter** is a native Linux application built with Python and PyQt6 designed to help you quickly browse, preview, and organize your video collection.

## Features

- **Three-Panel Interface**:
  - **Source Panel**: Browse your filesystem with filters for video files.
  - **Player Panel**: High-performance video playback with seek, volume, and navigation controls.
  - **Destination Panel**: Quick-access folders for moving videos to their final locations.
- **Persistent Preferences**: Save your most-used source and destination directories.
- **Advanced Playback**:
  - Seeker bar with time indicators.
  - Double-click for fullscreen (Theater) mode.
  - One-click file moving with automatic next-file playback.
- **Native Look & Feel**: Designed for Ubuntu/GNOME environments.

## Installation

### Prerequisites

- Python 3.12+
- FFmpeg (for video decoding)
- libxcb-cursor0 (for Qt)

```bash
sudo apt install python3-venv python3-pip ffmpeg libxcb-cursor0
```

### Setup

1. Clone or download the repository.
2. Create and activate a virtual environment:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

## Running the Application

```bash
.venv/bin/python3 src/main.py
```

## How to Use

1. **Configure**: Use `File > Preferences` to add your source (e.g., Downloads) and destination (e.g., Movies) folders.
2. **Browse**: Select a source folder from the dropdown.
3. **Preview**: Click a video to watch it. Use the seeker or shortcuts to navigate.
4. **Sort**: Select a destination root or sub-folder on the right.
5. **Move**: Click "Move Video" to transfer the file. The next video in the list will automatically start playing.

## License

MIT
