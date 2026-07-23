#!/usr/bin/env python3
"""Offline batch TTS generation for the word game corpus.

Reads data/words.json, synthesizes 4 recordings per unique word, converts to
mono 96k mp3 via ffmpeg, writes to data/audio/.

  {key}.en.mp3   - the English word itself        (Kokoro-82M, VOICE_EN)
  {key}.zh.mp3   - the Chinese gloss              (Qwen3-TTS, VOICE_ZH + INSTRUCT_ZH)
  {key}.s_en.mp3 - the English example sentence   (Kokoro-82M, VOICE_EN)
  {key}.s_zh.mp3 - the Chinese example sentence   (Qwen3-TTS, VOICE_ZH + INSTRUCT_ZH)

English uses Kokoro-82M (fast, clear); Chinese uses Qwen3-TTS-1.7B CustomVoice
(natural, relaxed — picked by ear over all Kokoro zh voices).

key = word.lower() with every non [a-z0-9] char replaced by "_"
(ice cream -> ice_cream, o'clock -> o_clock, Mr -> mr).

Idempotent: existing non-empty mp3 files are skipped. Failures are logged to
tmp/tts/failures.log and do not abort the run. At the end data/audio/ is
mirrored to public/audio/ for the frontend.

Usage:
  tools/tts/venv/bin/python tools/tts/generate_audio.py            # full run
  tools/tts/venv/bin/python tools/tts/generate_audio.py --limit 5  # first 5 unique words only
"""

import argparse
import json
import re
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
WORDS_JSON = ROOT / "data" / "words.json"
OUT_DIR = ROOT / "data" / "audio"
PUBLIC_DIR = ROOT / "public" / "audio"
TMP_DIR = ROOT / "tmp" / "tts"
FAIL_LOG = TMP_DIR / "failures.log"
FFMPEG = "/opt/homebrew/bin/ffmpeg"

VOICE_EN = "af_heart"  # Kokoro-82M: American English female, clear and warm
VOICE_ZH = "Serena"  # Qwen3-TTS CustomVoice speaker (Mandarin female)
INSTRUCT_ZH = "用自然、松弛、亲切的语气朗读，语速偏慢，像给小朋友讲故事一样"
QWEN_MODEL = "mlx-community/Qwen3-TTS-12Hz-1.7B-CustomVoice-bf16"
SAMPLE_RATE = 24000

# (suffix, words.json field, engine)
SEGMENTS = [
    ("en", "word", "en"),
    ("zh", "zh", "zh"),
    ("s_en", "sentenceEn", "en"),
    ("s_zh", "sentenceZh", "zh"),
]


def word_key(word: str) -> str:
    return re.sub(r"[^a-z0-9]", "_", word.lower())


def log_failure(key: str, suffix: str, text: str, err: str) -> None:
    with FAIL_LOG.open("a", encoding="utf-8") as f:
        f.write(f"{key}.{suffix}\t{text!r}\t{err}\n")


class Engines:
    """Lazy-loaded TTS engines: Kokoro-82M for English, Qwen3-TTS for Chinese."""

    def __init__(self) -> None:
        self._kokoro = None
        self._qwen = None

    def synth_en(self, text: str, wav_path: Path) -> None:
        if self._kokoro is None:
            from kokoro_mlx import KokoroTTS

            t0 = time.time()
            self._kokoro = KokoroTTS.from_pretrained()
            print(f"kokoro loaded in {time.time() - t0:.1f}s", flush=True)
        self._kokoro.save(text, str(wav_path), voice=VOICE_EN, speed=1.0, sample_rate=SAMPLE_RATE)

    def synth_zh(self, text: str, wav_path: Path) -> None:
        if self._qwen is None:
            from huggingface_hub import snapshot_download
            from mlx_audio.tts.generate import load_model

            t0 = time.time()
            local = snapshot_download(QWEN_MODEL)  # cached after first download
            self._qwen = load_model(Path(local))
            print(f"qwen3-tts loaded in {time.time() - t0:.1f}s", flush=True)
        from mlx_audio.tts.generate import generate_audio

        generate_audio(
            text=text,
            model=self._qwen,
            voice=VOICE_ZH,
            instruct=INSTRUCT_ZH,
            lang_code="zh",
            output_path=str(TMP_DIR),
            file_prefix="qwen_seg",
            save=True,
            play=False,
            verbose=False,
        )
        (TMP_DIR / "qwen_seg_000.wav").replace(wav_path)


def to_mp3(wav_path: Path, target: Path) -> None:
    subprocess.run(
        [
            FFMPEG, "-y", "-hide_banner", "-loglevel", "error",
            "-i", str(wav_path),
            "-ac", "1", "-codec:a", "libmp3lame", "-b:a", "96k",
            str(target),
        ],
        check=True,
        capture_output=True,
        text=True,
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=0, help="only process first N unique words")
    args = parser.parse_args()

    data = json.loads(WORDS_JSON.read_text(encoding="utf-8"))
    seen: set[str] = set()
    entries = []
    for w in data["words"]:
        k = word_key(w["word"])
        if k in seen:
            continue
        seen.add(k)
        entries.append((k, w))
    if args.limit:
        entries = entries[: args.limit]

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    TMP_DIR.mkdir(parents=True, exist_ok=True)
    wav_path = TMP_DIR / "segment.wav"

    engines = Engines()
    total = len(entries) * len(SEGMENTS)
    done = skipped = failed = 0
    start = time.time()
    for i, (k, w) in enumerate(entries, 1):
        for suffix, field, engine in SEGMENTS:
            text = w[field]
            target = OUT_DIR / f"{k}.{suffix}.mp3"
            if target.exists() and target.stat().st_size > 0:
                skipped += 1
                continue
            try:
                if engine == "zh":
                    engines.synth_zh(text, wav_path)
                else:
                    engines.synth_en(text, wav_path)
                to_mp3(wav_path, target)
                done += 1
            except Exception as e:  # noqa: BLE001 - log and continue
                failed += 1
                log_failure(k, suffix, text, str(e).strip().splitlines()[-1][:300])
                print(f"FAILED {k}.{suffix}: {e}", flush=True)
        elapsed = time.time() - start
        rate = (done + failed) / elapsed if elapsed > 0 else 0
        remaining = (total - done - failed - skipped) / rate if rate > 0 else 0
        print(
            f"[{i}/{len(entries)}] {k} | done={done} skip={skipped} fail={failed} "
            f"| {rate:.2f} seg/s, eta {remaining / 60:.1f} min",
            flush=True,
        )

    wav_path.unlink(missing_ok=True)
    (TMP_DIR / "qwen_seg_000.wav").unlink(missing_ok=True)

    # Mirror data/audio/ into public/audio/ for the frontend.
    PUBLIC_DIR.mkdir(parents=True, exist_ok=True)
    subprocess.run(["rsync", "-a", f"{OUT_DIR}/", f"{PUBLIC_DIR}/"], check=True)

    print(
        f"FINISHED in {(time.time() - start) / 60:.1f} min: "
        f"done={done} skipped={skipped} failed={failed} (see {FAIL_LOG})",
        flush=True,
    )
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
