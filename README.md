# 小小键盘单词机（Word Keys）

给 4 岁+ 孩子的本地单词游戏：敲字母键出单词卡（图 + 文 + 四段式朗读录音）+ 积分 + 曝光调度。需求与设计见 [PRD.md](PRD.md)。

- 在线玩（GitHub Pages，push 到 main 自动部署）：https://naeemo.github.io/word_game/
- 本地玩：`npm install && npm run dev`

## 目录结构

| 目录 | 说明 |
|------|------|
| `public/` | 静态资源（Vite 标准目录）：`data/words.json` 词表、`images/` 配图、`audio/` 全部录音 |
| `src/` | React 应用源码 |
| `tools/` | 工具管线：`tts/` 语音生成管线（见 [tools/tts/README.md](tools/tts/README.md)） |
| `dist/` | 构建产物（生成，不入库） |

改词表/图片/音频直接动 `public/` 下对应文件。

## 常用命令

```bash
npm run dev        # 本地开发
npm run build      # 构建到 dist/（含 tsc 检查）
npm test           # 调度算法单元测试
tools/tts/venv/bin/python tools/tts/generate_audio.py   # 词表变更后增量补语音
```
