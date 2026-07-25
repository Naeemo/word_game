#!/usr/bin/env python3
"""Round 3: "高级语文教师" instruct — serious, bright, stable tone for teaching.

  python gen_round3.py cv
  python gen_round3.py vd

Output: tmp/tts-compare/audio3/<config>/<text_id>.mp3
"""

import subprocess
import sys
import time
from pathlib import Path

OUT = Path(__file__).resolve().parent / "audio3"
FFMPEG = "/opt/homebrew/bin/ffmpeg"

TEXTS = {
    "t1_gloss": "苹果",
    "t2_sentence": "兔子耳朵长长的。",
    "t3_sentence2": "这本书是关于猫的。",
}

TEACHER = "像一位高级语文教师在给中学生上课，语气严肃认真，声音明亮稳定，字正腔圆，节奏不疾不徐"
VD_TEACHER = "一位资深高级语文教师的声音，给中学生授课，音色明亮沉稳，吐字清晰有力，语气严肃认真但不失亲和力，节奏不疾不徐，普通话标准"


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

    if which == "cv":
        t0 = time.time()
        m = load("mlx-community/Qwen3-TTS-12Hz-1.7B-CustomVoice-bf16")
        print(f"loaded CustomVoice in {time.time()-t0:.0f}s", flush=True)
        for spk in ["Serena", "Vivian", "Sohee", "Uncle_fu"]:
            synth(m, f"cv_{spk.lower()}_teacher",
                  {"voice": spk, "instruct": TEACHER, "lang_code": "chinese"})
    elif which == "vd":
        t0 = time.time()
        m = load("mlx-community/Qwen3-TTS-12Hz-1.7B-VoiceDesign-8bit")
        print(f"loaded VoiceDesign in {time.time()-t0:.0f}s", flush=True)
        synth(m, "vd_teacher", {"instruct": VD_TEACHER, "lang_code": "chinese"})
    else:
        sys.exit(f"unknown: {which}")
    print(f"DONE {which}", flush=True)


if __name__ == "__main__":
    main()
