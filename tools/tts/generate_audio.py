#!/usr/bin/env python3
"""Offline batch TTS generation for the word game corpus.

Reads data/words.json, synthesizes 4 recordings per unique word with
Kokoro-82M (MLX), converts to mono 96k mp3 via ffmpeg, writes to data/audio/.

  {key}.en.mp3   - the English word itself        (voice: VOICE_EN)
  {key}.zh.mp3   - the Chinese gloss              (voice: VOICE_ZH)
  {key}.s_en.mp3 - the English example sentence   (voice: VOICE_EN)
  {key}.s_zh.mp3 - the Chinese example sentence   (voice: VOICE_ZH)

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

VOICE_EN = "af_heart"  # American English female, clear and warm
VOICE_ZH = "zf_xiaoxiao"  # Mandarin female
SAMPLE_RATE = 24000

SEGMENTS = [
    ("en", "word", VOICE_EN),
    ("zh", "zh", VOICE_ZH),
    ("s_en", "sentenceEn", VOICE_EN),
    ("s_zh", "sentenceZh", VOICE_ZH),
]


def word_key(word: str) -> str:
    return re.sub(r"[^a-z0-9]", "_", word.lower())


def log_failure(key: str, suffix: str, text: str, err: str) -> None:
    with FAIL_LOG.open("a", encoding="utf-8") as f:
        f.write(f"{key}.{suffix}\t{text!r}\t{err}\n")


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

    from kokoro_mlx import KokoroTTS

    print(f"loading model... {len(entries)} unique words", flush=True)
    t0 = time.time()
    tts = KokoroTTS.from_pretrained()
    print(f"model loaded in {time.time() - t0:.1f}s", flush=True)

    total = len(entries) * len(SEGMENTS)
    done = skipped = failed = 0
    start = time.time()
    for i, (k, w) in enumerate(entries, 1):
        for suffix, field, voice in SEGMENTS:
            text = w[field]
            target = OUT_DIR / f"{k}.{suffix}.mp3"
            if target.exists() and target.stat().st_size > 0:
                skipped += 1
                continue
            try:
                tts.save(text, str(wav_path), voice=voice, speed=1.0, sample_rate=SAMPLE_RATE)
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
