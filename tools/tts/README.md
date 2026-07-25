# TTS 语音生成管线

用本地开源模型离线批量生成游戏全部语料的录音。游戏运行时不做实时语音合成，直接播放这里生成的 mp3；文件缺失时前端自动回退系统 TTS。

**双引擎方案**（2026-07-25 第四轮试听定稿）：

- 英文：**Kokoro-82M**（MLX 实现，Apple Silicon 原生），音色 `af_heart`——快（约 2 段/秒）、清晰
- 中文：**Qwen3-TTS-12Hz-1.7B-Base**（8bit，MLX）**ICL 声音克隆**，参考音频 `ref_heart.wav`——这段参考音频本身就是 Kokoro `af_heart` 念的 3 句英文例句（拼接，逐字转写在 `ref_heart.txt`），跨语言克隆让中文语音和英文线共享同一个明亮清晰的音色；`temperature=0.7`（默认 0.9 在孤立词条上偶尔读错字，如「关于→关羽」）；生成后用 Qwen3-ASR-0.6B 转写抽查内容正确性

选型淘汰记录：Kokoro 中文音色（机械）→ VoxCPM2 声音设计+克隆（音色不合适）→ Qwen3-TTS CustomVoice 预置音色（Serena/Vivian 等轻柔气声型，叠加"温柔"instruct 后尤甚）→ Qwen3-TTS VoiceDesign / "语文教师"instruct（仍不如英文线音色）→ **Qwen3-TTS Base ICL 克隆 af_heart**（选定）。教训：这套模型的中文预置音色偏轻柔气声，instruct 里写「温柔」会加剧；克隆英文线的参考音频是音色一致性的正解。IndexTTS-1.5 克隆叠词会吞字；Spark-TTS 孤立词太赶；GLM-TTS / MiniMax-Speech 仅 GPU；IndexTTS-2 / CosyVoice3 的 MLX 移植与 mlx-audio 0.4.5 不兼容。

## 一次性安装

```bash
tools/tts/setup.sh
```

要求：Apple Silicon Mac、Python 3.12（`brew install python@3.12`）、ffmpeg（`brew install ffmpeg`）。首次生成会从 HuggingFace 下载模型权重（Kokoro 数百 MB + Qwen3-TTS-Base-8bit 约 2GB，之后完全离线）。

## 日常使用

```bash
# 全量/增量生成（已存在的非空 mp3 自动跳过）
tools/tts/venv/bin/python tools/tts/generate_audio.py

# 只处理前 5 个词（冒烟测试）
tools/tts/venv/bin/python tools/tts/generate_audio.py --limit 5
```

- 语料来源：`public/data/words.json`（word / zh / sentenceEn / sentenceZh 四个字段）
- 产物：`public/audio/{key}.{en|zh|s_en|s_zh}.mp3`
- key 规范：单词转小写、非 `[a-z0-9]` 字符替换为 `_`（`ice cream→ice_cream`、`o'clock→o_clock`、`Mr→mr`）；与前端 `src/tts.ts` 的 `wordKey()` 保持一致，改命名规则必须两边同步
- 重复词串（如 box 同时属于 b 池和 x 池）只生成一次

## 常见场景

- **词表增删词**：直接跑增量命令即可，新词自动生成、旧文件不动
- **换英文音色**：改 `generate_audio.py` 的 `VOICE_EN`（Kokoro：如 `af_heart`、`af_bella`、`am_adam`），删掉对应 en/s_en 文件后增量重跑
- **换中文声音**：替换 `tools/tts/ref_heart.wav`（几秒干净人声即可）并同步更新 `ref_heart.txt` 的逐字转写，然后 `rm -f public/audio/*.zh.mp3 public/audio/*.s_zh.mp3` 增量重跑（1012 个文件约 1 小时）。想重新对比多个方案，用 `compare/` 下的脚本生成样音 + Qwen3-ASR 校验 + 试听页（2026-07-25 四轮对比就是这么跑的）
- **全量重新生成**：`rm -rf public/audio` 后跑全量命令（2024 个文件约 1 小时）
- **失败排查**：失败项记录在 `tmp/tts/failures.log`，不中断整体；重跑命令即可补齐
- **内容质检**：`tools/tts/venv/bin/python tools/tts/qa_fix.py`——用 Qwen3-ASR 转写全部词条（+随机 100 个句子），拼音比对词表（同音字不误报，英文字母判失败），失败项自动换温度重试修复。跨语言克隆在**孤立词条**上有约 10% 概率"滑回英文"（面包→"Manball"），所以每次全量生成后必须跑这一步。顽固词条的修法：文本后加「。」、调高温度（0.85~1.0）、重复读再裁剪、或用自产 s_zh 音频拼中文参考音频做 ICL（见 2026-07-25 的 qa_report）

## 文件说明

| 文件 | 作用 |
|------|------|
| `generate_audio.py` | 生成脚本（幂等增量，ffmpeg 转 mp3 单声道 96k） |
| `qa_fix.py` | ASR 内容质检 + 失败项自动重试修复（全量生成后必跑） |
| `ref_heart.wav` / `ref_heart.txt` | 中文 ICL 克隆参考音频（Kokoro af_heart 原声 3 句拼接）及逐字转写 |
| `compare/` | 历次音色对比试听用的样音生成脚本（gen_samples / gen_round2~4） |
| `requirements.txt` | Python 依赖（kokoro-mlx 英文 + mlx-audio/Qwen3-TTS 中文） |
| `setup.sh` | 建 venv 装依赖的一键脚本 |
| `venv/` | 本地环境，不入库（见 .gitignore） |

中间产物（wav、failures.log、qa_report.txt、试听对比样音）写在 `tmp/`，不入库。
