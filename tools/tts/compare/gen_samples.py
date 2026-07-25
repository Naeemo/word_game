#!/usr/bin/env python3
"""Generate Chinese TTS comparison samples across candidate engines.

One engine per invocation (keeps memory bounded on 16GB):
  gen_samples.py qwen3_vd     # VoiceDesign-8bit, 2 instruct variants
  gen_samples.py qwen3_cv     # CustomVoice-bf16, Serena + Vivian + kid instruct
  gen_samples.py spark        # Spark-TTS-0.5B-8bit, voice creation
  gen_samples.py indextts     # IndexTTS-1.5, clone ref_teacher.wav
  gen_samples.py baseline     # copy current production mp3s (VoxCPM2-8bit clone)

Output: tmp/tts-compare/audio/<config>/<text_id>.mp3  +  samples.json manifest
"""

import json
import shutil
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent / "audio"
REF = ROOT / "tools" / "tts" / "ref_teacher.wav"
FFMPEG = "/opt/homebrew/bin/ffmpeg"

TEXTS = {
    "t1_gloss": "苹果",
    "t2_sentence": "兔子耳朵长长的。",
    "t3_sentence2": "这本书是关于猫的。",
}

INSTRUCT_WARM = "温柔亲切的年轻女老师，声音温暖柔和，语速稍慢，吐字非常清晰，像在给幼儿园小朋友讲故事，充满耐心和爱心"
INSTRUCT_LIVELY = "活泼可爱的年轻女声，语气轻快亲切，发音标准清晰，像儿童节目主持人在给小朋友读故事"
INSTRUCT_CV = "温柔耐心地给幼儿园小朋友朗读，语速稍慢，吐字清晰，语气亲切"


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

    if which == "baseline":
        srcs = {"t1_gloss": "apple.zh.mp3", "t2_sentence": "rabbit.s_zh.mp3",
                "t3_sentence2": "about.s_zh.mp3"}
        d = OUT / "baseline"
        d.mkdir(parents=True, exist_ok=True)
        for tid, f in srcs.items():
            shutil.copy(ROOT / "public" / "audio" / f, d / f"{tid}.mp3")
        print("baseline copied", flush=True)
        return

    if which == "qwen3_vd":
        t0 = time.time()
        m = load("mlx-community/Qwen3-TTS-12Hz-1.7B-VoiceDesign-8bit")
        print(f"loaded VoiceDesign in {time.time()-t0:.0f}s", flush=True)
        synth(m, "qwen3_vd_warm", {"instruct": INSTRUCT_WARM, "lang_code": "chinese"})
        synth(m, "qwen3_vd_lively", {"instruct": INSTRUCT_LIVELY, "lang_code": "chinese"})
    elif which == "qwen3_cv":
        t0 = time.time()
        m = load("mlx-community/Qwen3-TTS-12Hz-1.7B-CustomVoice-bf16")
        print(f"loaded CustomVoice in {time.time()-t0:.0f}s", flush=True)
        for spk in ["Serena", "Vivian"]:
            synth(m, f"qwen3_cv_{spk.lower()}",
                  {"voice": spk, "instruct": INSTRUCT_CV, "lang_code": "chinese"})
    elif which == "spark":
        t0 = time.time()
        m = load("mlx-community/Spark-TTS-0.5B-8bit")
        print(f"loaded Spark in {time.time()-t0:.0f}s", flush=True)
        # pitch/speed use LEVELS_MAP floats: 0.0=very_low 0.5=low 1.0=moderate 1.5=high 2.0=very_high
        synth(m, "spark_female_slow", {"gender": "female", "pitch": 1.5, "speed": 0.5})
    elif which == "indextts":
        t0 = time.time()
        m = load("mlx-community/IndexTTS-1.5", tokenizer_name="mlx-community/IndexTTS-1.5")
        print(f"loaded IndexTTS in {time.time()-t0:.0f}s", flush=True)
        synth(m, "indextts15_clone", {"ref_audio": str(REF)})
    else:
        sys.exit(f"unknown engine: {which}")
    print(f"DONE {which}", flush=True)


if __name__ == "__main__":
    main()
