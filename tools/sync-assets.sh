#!/usr/bin/env bash
# public/ 是【生成的镜像】，不是数据源。唯一数据源：
#   data/words.json -> public/data/words.json
#   images/         -> public/images/
#   data/audio/     -> public/audio/
# Vite 只能从 public/ 提供静态文件，所以构建/开发前用这个脚本同步镜像。
# 由 npm 的 predev / prebuild 钩子自动执行，无需手动调用。
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p public/data
rsync -a --delete data/words.json public/data/words.json
rsync -a --delete images/ public/images/
rsync -a --delete data/audio/ public/audio/
