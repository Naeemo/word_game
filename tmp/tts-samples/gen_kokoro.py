import subprocess, time
from pathlib import Path
from kokoro_mlx import KokoroTTS

OUT = Path("/Users/naeemo/Workspace/word_game/tmp/tts-samples")
FFMPEG = "/opt/homebrew/bin/ffmpeg"
VOICES = ["zf_xiaobei","zf_xiaoni","zf_xiaoxiao","zf_xiaoyi","zm_yunjian","zm_yunxi","zm_yunxia","zm_yunyang"]
SPEEDS = [1.0, 0.9]
TEXTS = [("word","苹果"),("gloss","一只可爱的熊猫"),("sentence","我吃苹果。"),("long","大熊猫喜欢在竹林里睡觉。")]

tts = KokoroTTS.from_pretrained()
wav = OUT / "tmp.wav"
t0 = time.time(); n = 0
for v in VOICES:
    for s in SPEEDS:
        for tag, text in TEXTS:
            mp3 = OUT / f"kokoro_{v}_s{s}.{tag}.mp3"
            tts.save(text, str(wav), voice=v, speed=s, sample_rate=24000)
            subprocess.run([FFMPEG,"-y","-hide_banner","-loglevel","error","-i",str(wav),
                            "-ac","1","-codec:a","libmp3lame","-b:a","96k",str(mp3)], check=True)
            n += 1
    print(f"{v} done ({n} files, {time.time()-t0:.0f}s)", flush=True)
wav.unlink()
print("ALL DONE", n)
