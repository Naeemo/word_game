# TTS 语音生成管线

用本地开源模型离线批量生成游戏全部语料的录音。游戏运行时不做实时语音合成，直接播放这里生成的 mp3；文件缺失时前端自动回退系统 TTS。

**双引擎方案**（2026-07 试听选定）：

- 英文：**Kokoro-82M**（MLX 实现，Apple Silicon 原生），音色 `af_heart`——快（约 2 段/秒）、清晰
- 中文：**VoxCPM2**（2B，MLX 8bit）**声音克隆模式**，参考音频 `ref_teacher.wav`——该参考音频本身是用 VoxCPM2 声音设计（instruct：「一位温柔亲切的幼儿园女老师，声音温暖、清晰、有耐心，像在给小朋友讲故事」）生成、经试听对比 25 组候选后选定的。克隆模式保证 1000+ 个文件音色完全一致

选型淘汰记录：Kokoro 中文音色（机械）→ Qwen3-TTS 预置音色（风格化人设，不适合儿童）→ VoxCPM2 声音设计 + 克隆（选定）。GLM-TTS / MiniMax-Speech 仅支持 GPU PyTorch，Mac 不可行；IndexTTS-2 的 MLX 移植与 mlx-audio 0.4.5 不兼容。

## 一次性安装

```bash
tools/tts/setup.sh
```

要求：Apple Silicon Mac、Python 3.12（`brew install python@3.12`）、ffmpeg（`brew install ffmpeg`）。首次生成会从 HuggingFace 下载模型权重（Kokoro 数百 MB + VoxCPM2-8bit 约 3.2GB，之后完全离线）。

## 日常使用

```bash
# 全量/增量生成（已存在的非空 mp3 自动跳过）
tools/tts/venv/bin/python tools/tts/generate_audio.py

# 只处理前 5 个词（冒烟测试）
tools/tts/venv/bin/python tools/tts/generate_audio.py --limit 5
```

- 语料来源：`public/data/words.json`（word / zh / sentenceEn / sentenceZh 四个字段）
- 产物：`public/audio/{key}.{en|zh|s_en|s_zh}.mp3`，跑完自动同步到 `public/audio/`
- key 规范：单词转小写、非 `[a-z0-9]` 字符替换为 `_`（`ice cream→ice_cream`、`o'clock→o_clock`、`Mr→mr`）；与前端 `src/tts.ts` 的 `wordKey()` 保持一致，改命名规则必须两边同步
- 重复词串（如 box 同时属于 b 池和 x 池）只生成一次

## 常见场景

- **词表增删词**：直接跑增量命令即可，新词自动生成、旧文件不动
- **换英文音色**：改 `generate_audio.py` 的 `VOICE_EN`（Kokoro：如 `af_heart`、`af_bella`、`am_adam`），删掉对应 en/s_en 文件后增量重跑
- **换中文声音**：替换 `tools/tts/ref_teacher.wav` 为新的参考音频（几秒干净人声即可；想重新"设计"一个音色，用 mlx-audio 的 VoxCPM2 `instruct` 声音设计模式生成样例，试听满意后拿样例当参考音频），然后 `rm -f public/audio/*.zh.mp3 public/audio/*.s_zh.mp3` 增量重跑（1012 个文件约 2 小时）
- **全量重新生成**：`rm -rf public/audio` 后跑全量命令（2024 个文件约 2 小时）
- **失败排查**：失败项记录在 `tmp/tts/failures.log`，不中断整体；重跑命令即可补齐

## 文件说明

| 文件 | 作用 |
|------|------|
| `generate_audio.py` | 生成脚本（幂等增量，ffmpeg 转 mp3 单声道 96k） |
| `ref_teacher.wav` | 中文声音克隆参考音频（"幼儿园老师"音色，已入库） |
| `requirements.txt` | Python 依赖（kokoro-mlx 英文 + mlx-audio/VoxCPM2 中文） |
| `setup.sh` | 建 venv 装依赖的一键脚本 |
| `venv/` | 本地环境，不入库（见 .gitignore） |

中间产物（wav、failures.log）写在 `tmp/tts/`，不入库。历史试听对比样例在 `tmp/tts-samples/`（含 index.html 试听页）。
