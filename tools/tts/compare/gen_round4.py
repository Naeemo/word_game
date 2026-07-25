#!/usr/bin/env python3
"""Round 4: cross-lingual voice cloning of the English Kokoro af_heart timbre
into Chinese. ref_heart.wav is a 7.5s af_heart clip (transcript in ref_heart.txt).

  python gen_round4.py qwen3_base   # Qwen3-TTS Base ICL clone (~2GB download)
  python gen_round4.py voxcpm2      # VoxCPM2-8bit clone (cached)
  python gen_round4.py indextts     # IndexTTS-1.5 clone (cached)
  python gen_round4.py spark        # Spark-TTS clone (cached)

Output: tmp/tts-compare/audio4/<config>/<text_id>.mp3
"""

import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE / "audio4"
REF = HERE / "ref_heart.wav"
REF_TEXT = (HERE / "ref_heart.txt").read_text(encoding="utf-8").strip()
FFMPEG = "/opt/homebrew/bin/ffmpeg"

TEXTS = {
    "t1_gloss": "苹果",
    "t2_sentence": "兔子耳朵长长的。",
    "t3_sentence2": "这本书是关于猫的。",
}


def to_mp3(wav_path: Path, target: Path) -> None:
    subprocess.run(
        [FFMPEG, "-y", "-hide_banner", "-loglevel", "error",
         "-i", str(wav_path), "-ac", "1", "-codec:a", "libmp3lame", "-b:a", "96k",
         str(target)],
        check=True,
    )


def synth(model, name: str, kwargs: dict) -> None:
    import numpy as np
    import soundfile as sf

    cfg_dir = OUT / name
    cfg_dir.mkdir(parents=True, exist_ok=True)
    tmp = cfg_dir / "_tmp.wav"
    for tid, text in TEXTS.items():
        target = cfg_dir / f"{tid}.mp3"
        if target.exists() and target.stat().st_size > 0:
            continue
        t0 = time.time()
        result = next(model.generate(text=text, **kwargs))
        sr = getattr(result, "sample_rate", None) or model.sample_rate
        sf.write(str(tmp), np.array(result.audio), sr)
        to_mp3(tmp, target)
        print(f"  {name}/{tid}: {time.time()-t0:.1f}s  {text}", flush=True)
    tmp.unlink(missing_ok=True)


def main() -> None:
    which = sys.argv[1]
    from mlx_audio.tts.utils import load

    if which == "qwen3_base":
        t0 = time.time()
        m = load("mlx-community/Qwen3-TTS-12Hz-1.7B-Base-8bit")
        print(f"loaded Base in {time.time()-t0:.0f}s", flush=True)
        synth(m, "qwen3base_heart", {
            "ref_audio": str(REF), "ref_text": REF_TEXT, "lang_code": "chinese"})
    elif which == "voxcpm2":
        t0 = time.time()
        m = load("mlx-community/VoxCPM2-8bit")
        print(f"loaded VoxCPM2 in {time.time()-t0:.0f}s", flush=True)
        synth(m, "voxcpm2_heart", {"ref_audio": str(REF), "max_tokens": 800})
    elif which == "indextts":
        t0 = time.time()
        m = load("mlx-community/IndexTTS-1.5", tokenizer_name="mlx-community/IndexTTS-1.5")
        print(f"loaded IndexTTS in {time.time()-t0:.0f}s", flush=True)
        synth(m, "indextts_heart", {"ref_audio": str(REF)})
    elif which == "spark":
        t0 = time.time()
        m = load("mlx-community/Spark-TTS-0.5B-8bit")
        print(f"loaded Spark in {time.time()-t0:.0f}s", flush=True)
        synth(m, "spark_heart", {"ref_audio": REF, "ref_text": REF_TEXT})
    else:
        sys.exit(f"unknown: {which}")
    print(f"DONE {which}", flush=True)


if __name__ == "__main__":
    main()
