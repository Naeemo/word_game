# 小小键盘单词机（Word Keys）

给 4 岁+ 孩子的本地单词游戏：敲字母键出单词卡（图 + 文 + 四段式朗读录音）+ 积分 + 曝光调度。需求与设计见 [PRD.md](PRD.md)。

- 在线玩（GitHub Pages，push 到 main 自动部署）：https://naeemo.github.io/word_game/
- 本地玩：`npm install && npm run dev`

## 目录结构

| 目录 | 性质 | 说明 |
|------|------|------|
| `data/` | **数据源（唯一）** | `words.json` 词表 + `audio/` 全部录音 |
| `images/` | **数据源（唯一）** | 全部单词配图 |
| `public/` | 生成物，**不入库** | Vite 静态目录，是 `data/` + `images/` 的镜像，由 `npm run sync:assets` 生成（`predev`/`prebuild` 钩子自动执行） |
| `dist/` | 生成物，**不入库** | 构建产物 |
| `src/` | 源码 | React 应用本体 |
| `tools/` | 工具管线 | `tts/`：语音生成管线（见 [tools/tts/README.md](tools/tts/README.md)）；`sync-assets.sh`：镜像同步 |
| `tmp/` | 溯源材料 | 词表构建脚本与语料来源、TTS 试听对比样例；一次性用途，可随时清空 |

改词表/图片/音频只动 `data/` 和 `images/`，不要动 `public/`（会被覆盖）。

## 常用命令

```bash
npm run dev        # 本地开发（自动先同步 public/ 镜像）
npm run build      # 构建到 dist/（含 tsc 检查）
npm test           # 调度算法单元测试
tools/tts/venv/bin/python tools/tts/generate_audio.py   # 词表变更后增量补语音
```
