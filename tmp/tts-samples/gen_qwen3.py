import subprocess, time
import numpy as np
from pathlib import Path
from scipy.io import wavfile
from mlx_audio.tts.utils import load_model

OUT = Path("/Users/naeemo/Workspace/word_game/tmp/tts-samples")
FFMPEG = "/opt/homebrew/bin/ffmpeg"
TEXTS = [("word","苹果"),("gloss","一只可爱的熊猫"),("sentence","我吃苹果。"),("long","大熊猫喜欢在竹林里睡觉。")]
RELAXED = "语速稍慢，自然松弛，亲切温柔，像给小朋友讲故事。"
CASES = [
    ("serena", "Serena", None),
    ("serena_relaxed", "Serena", RELAXED),
    ("vivian", "Vivian", None),
    ("vivian_relaxed", "Vivian", RELAXED),
]

t0 = time.time()
model = load_model("mlx-community/Qwen3-TTS-12Hz-1.7B-CustomVoice-bf16")
print(f"model loaded in {time.time()-t0:.0f}s", flush=True)

wav = OUT / "tmp_qwen.wav"
for name, speaker, instruct in CASES:
    for tag, text in TEXTS:
        kw = dict(text=text, speaker=speaker, language="Chinese")
        if instruct:
            kw["instruct"] = instruct
        try:
            results = list(model.generate_custom_voice(**kw))
            r = results[0]
            audio = np.array(r.audio, dtype=np.float32).flatten()
            sr = int(getattr(r, "sample_rate", 24000))
            pcm = np.clip(audio, -1, 1)
            wavfile.write(str(wav), sr, (pcm * 32767).astype(np.int16))
            mp3 = OUT / f"qwen3_{name}.{tag}.mp3"
            subprocess.run([FFMPEG,"-y","-hide_banner","-loglevel","error","-i",str(wav),
                            "-ac","1","-codec:a","libmp3lame","-b:a","96k",str(mp3)], check=True)
            print(f"OK qwen3_{name}.{tag}.mp3 ({len(audio)/sr:.2f}s)", flush=True)
        except Exception as e:
            print(f"FAIL qwen3_{name}.{tag}: {e}", flush=True)
wav.unlink(missing_ok=True)
print("ALL DONE", flush=True)
