#!/usr/bin/env python3
"""Full ASR QA + auto-repair pass for the Chinese gloss files (*.zh.mp3).

Cross-lingual ICL cloning occasionally fails to code-switch into Chinese on
very short glosses (e.g. 面包 -> "Manball."). This script:
  1. ASR-transcribes every {key}.zh.mp3 and compares pinyin (homophone-tolerant)
     against the expected gloss; Latin letters in the transcript = auto-fail.
  2. Regenerates failures with temperature jitter until ASR-verified (max 5 tries).
  3. Also scans a random sample of 100 sentence files (s_zh) and repairs the same way.

Writes a report to tmp/tts/qa_report.txt. Idempotent: re-run to re-check.
"""

import json
import random
import re
import subprocess
import sys
from pathlib import Path

import numpy as np
import soundfile as sf
from pypinyin import lazy_pinyin

ROOT = Path(__file__).resolve().parents[2]
REF = ROOT / "tools" / "tts" / "ref_heart.wav"
REF_TEXT = (ROOT / "tools" / "tts" / "ref_heart.txt").read_text(encoding="utf-8").strip()
FFMPEG = "/opt/homebrew/bin/ffmpeg"
REPORT = ROOT / "tmp" / "tts" / "qa_report.txt"
MODEL = "mlx-community/Qwen3-TTS-12Hz-1.7B-Base-8bit"
TEMPS = [0.7, 0.6, 0.8, 0.5, 0.9]


def key(w: str) -> str:
    return re.sub(r"[^a-z0-9]", "_", w.lower())


def norm(s: str) -> str:
    return re.sub(r"[，。！？、\s（）()；……·]", "", s)


def py(s: str):
    return lazy_pinyin(norm(s))


def main() -> None:
    from mlx_audio.stt.utils import load_model as load_asr
    from mlx_audio.tts.utils import load as load_tts

    data = json.loads((ROOT / "public" / "data" / "words.json").read_text(encoding="utf-8"))
    seen, entries = set(), []
    for w in data["words"]:
        k = key(w["word"])
        if k not in seen:
            seen.add(k)
            entries.append((k, w))

    random.seed(7)
    s_zh_sample = set(k for k, _ in random.sample(entries, 100))

    asr = load_asr("Qwen/Qwen3-ASR-0.6B")

    def transcribe(path: Path) -> str:
        r = asr.generate(str(path))
        return r.text if hasattr(r, "text") else str(r)

    def ok(expected: str, heard: str) -> bool:
        if re.search(r"[A-Za-z]", heard):  # slipped into English-ish gibberish
            return False
        return py(expected) == py(heard)

    # ---- scan ----
    failures = []  # (key, suffix, field, expected, heard)
    for i, (k, w) in enumerate(entries, 1):
        checks = [("zh", "zh")]
        if k in s_zh_sample:
            checks.append(("s_zh", "sentenceZh"))
        for suffix, field in checks:
            p = ROOT / "public" / "audio" / f"{k}.{suffix}.mp3"
            heard = transcribe(p)
            if not ok(w[field], heard):
                failures.append((k, suffix, field, w[field], heard.strip()))
        if i % 50 == 0:
            print(f"scanned {i}/{len(entries)}, failures so far: {len(failures)}", flush=True)

    print(f"\nSCAN DONE: {len(failures)} failures", flush=True)
    for k, suffix, field, exp, heard in failures:
        print(f"  ✗ {k}.{suffix}: 期望「{exp}」识别「{heard}」", flush=True)

    if not failures:
        REPORT.write_text("all clear\n", encoding="utf-8")
        return

    # ---- repair ----
    tts = load_tts(MODEL)
    wav_path = ROOT / "tmp" / "tts" / "qa_fix.wav"
    stubborn = []
    for k, suffix, field, exp, heard in failures:
        target = ROOT / "public" / "audio" / f"{k}.{suffix}.mp3"
        fixed = False
        for attempt, temp in enumerate(TEMPS, 1):
            r = next(tts.generate(text=exp, ref_audio=str(REF), ref_text=REF_TEXT,
                                  lang_code="chinese", max_tokens=800, temperature=temp))
            sr = getattr(r, "sample_rate", None) or tts.sample_rate
            sf.write(str(wav_path), np.array(r.audio), sr)
            heard2 = transcribe(wav_path)
            if ok(exp, heard2):
                subprocess.run([FFMPEG, "-y", "-hide_banner", "-loglevel", "error",
                                "-i", str(wav_path), "-ac", "1", "-codec:a", "libmp3lame",
                                "-b:a", "96k", str(target)], check=True)
                print(f"  ✓ fixed {k}.{suffix} (attempt {attempt}, temp={temp})", flush=True)
                fixed = True
                break
        if not fixed:
            stubborn.append((k, suffix, exp))
            print(f"  ✗ STUBBORN {k}.{suffix} 「{exp}」 after {len(TEMPS)} tries", flush=True)
    wav_path.unlink(missing_ok=True)

    lines = [f"failures found: {len(failures)}, fixed: {len(failures) - len(stubborn)}, stubborn: {len(stubborn)}"]
    lines += [f"STUBBORN {k}.{suffix} {exp}" for k, suffix, exp in stubborn]
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n" + lines[0], flush=True)
    sys.exit(1 if stubborn else 0)


if __name__ == "__main__":
    main()
