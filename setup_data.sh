#!/bin/bash

echo "📦 自动 clone 私有数据仓库 ConanMangaText 到 ./data/submodule_data"

# 清理旧目录（可选）
rm -rf data/submodule_data

# 使用 GitHub token clone 数据仓库
git clone https://${GIT_USERNAME}:${GIT_PASSWORD}@github.com/pingzheshenhei/ConanMangaText.git data/submodule_data

# 打印确认
ls -l data/submodule_data/纯文本/日文 | head -n 10
