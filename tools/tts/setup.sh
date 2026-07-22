#!/usr/bin/env bash
# Set up the TTS generation environment (Apple Silicon Mac only).
# Creates tools/tts/venv with Python 3.12 and installs Kokoro-82M (MLX).
# Model weights download from HuggingFace on first generation run (~hundreds of MB),
# afterwards everything works fully offline.
set -euo pipefail
cd "$(dirname "$0")"

PY=$(command -v python3.12 || command -v /opt/homebrew/bin/python3.12 || true)
if [ -z "$PY" ]; then
  echo "需要 Python 3.12（kokoro-mlx 不支持 3.13+）。安装：brew install python@3.12" >&2
  exit 1
fi

"$PY" -m venv venv
venv/bin/pip install --upgrade pip
venv/bin/pip install -r requirements.txt

command -v ffmpeg >/dev/null || { echo "需要 ffmpeg：brew install ffmpeg" >&2; exit 1; }

echo "OK。运行：tools/tts/venv/bin/python tools/tts/generate_audio.py"
