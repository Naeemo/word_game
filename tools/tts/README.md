# TTS 语音生成管线

用本地开源模型 **Kokoro-82M**（MLX 实现，Apple Silicon 原生）离线批量生成游戏全部语料的录音。游戏运行时不做实时语音合成，直接播放这里生成的 mp3；文件缺失时前端自动回退系统 TTS。

## 一次性安装

```bash
tools/tts/setup.sh
```

要求：Apple Silicon Mac、Python 3.12（`brew install python@3.12`）、ffmpeg（`brew install ffmpeg`）。首次生成会从 HuggingFace 下载模型权重（之后完全离线）。

## 日常使用

```bash
# 全量/增量生成（已存在的非空 mp3 自动跳过）
tools/tts/venv/bin/python tools/tts/generate_audio.py

# 只处理前 5 个词（冒烟测试）
tools/tts/venv/bin/python tools/tts/generate_audio.py --limit 5
```

- 语料来源：`data/words.json`（word / zh / sentenceEn / sentenceZh 四个字段）
- 产物：`data/audio/{key}.{en|zh|s_en|s_zh}.mp3`，跑完自动同步到 `public/audio/`
- key 规范：单词转小写、非 `[a-z0-9]` 字符替换为 `_`（`ice cream→ice_cream`、`o'clock→o_clock`、`Mr→mr`）；与前端 `src/tts.ts` 的 `wordKey()` 保持一致，改命名规则必须两边同步
- 重复词串（如 box 同时属于 b 池和 x 池）只生成一次

## 常见场景

- **词表增删词**：直接跑增量命令即可，新词自动生成、旧文件不动
- **换音色/重新生成某些词**：删掉对应 mp3 再跑增量命令；换音色改 `generate_audio.py` 顶部的 `VOICE_EN` / `VOICE_ZH`（英文如 `af_heart`、`af_bella`、`am_adam`；中文如 `zf_xiaoxiao`、`zf_xiaobei`）
- **全量重新生成**：`rm -rf data/audio public/audio` 后跑全量命令（2024 个文件约 18 分钟）
- **失败排查**：失败项记录在 `tmp/tts/failures.log`，不中断整体；重跑命令即可补齐

## 文件说明

| 文件 | 作用 |
|------|------|
| `generate_audio.py` | 生成脚本（幂等增量，ffmpeg 转 mp3 单声道 96k） |
| `requirements.txt` | Python 依赖（kokoro-mlx + 中文 G2P） |
| `setup.sh` | 建 venv 装依赖的一键脚本 |
| `venv/` | 本地环境，不入库（见 .gitignore） |

中间产物（wav、failures.log）写在 `tmp/tts/`，可随时清空。
