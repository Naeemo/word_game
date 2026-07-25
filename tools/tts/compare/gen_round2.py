#!/usr/bin/env python3
"""Round 2: anti-breathiness Chinese voice candidates.

Complaint: Serena + gentle instruct came out breathy/whispery ("AV dubbing").
Fix direction: bright, crisp, energetic voices + instruct that explicitly
forbids breathiness/whispering.

  python gen_round2.py cv   # CustomVoice presets × bright instruct
  python gen_round2.py vd   # VoiceDesign with explicit anti-whisper description

Output: tmp/tts-compare/audio2/<config>/<text_id>.mp3
"""

import subprocess
import sys
import time
from pathlib import Path

OUT = Path(__file__).resolve().parent / "audio2"
FFMPEG = "/opt/homebrew/bin/ffmpeg"

TEXTS = {
    "t1_gloss": "苹果",
    "t2_sentence": "兔子耳朵长长的。",
    "t3_sentence2": "这本书是关于猫的。",
}

BRIGHT = "声音明亮饱满，字正腔圆，干净利落，精神十足，像幼儿园老师带小朋友晨读，不要气声，不要耳语"
VD_BRIGHT = "明亮清脆的年轻女声，普通话标准，字正腔圆，精神饱满，是带幼儿园小朋友晨读的老师，声音洪亮干净，绝不轻柔，绝不耳语"


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
        for spk in ["Vivian", "Sohee", "Ono_anna", "Serena", "Uncle_fu"]:
            synth(m, f"cv_{spk.lower()}_bright",
                  {"voice": spk, "instruct": BRIGHT, "lang_code": "chinese"})
    elif which == "vd":
        t0 = time.time()
        m = load("mlx-community/Qwen3-TTS-12Hz-1.7B-VoiceDesign-8bit")
        print(f"loaded VoiceDesign in {time.time()-t0:.0f}s", flush=True)
        synth(m, "vd_bright", {"instruct": VD_BRIGHT, "lang_code": "chinese"})
    else:
        sys.exit(f"unknown: {which}")
    print(f"DONE {which}", flush=True)


if __name__ == "__main__":
    main()
