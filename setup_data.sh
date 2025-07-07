#!/bin/bash

echo "📦 开始拉取私有数据仓库 ConanMangaText 到 data/submodule_data"

# 如果已存在旧数据，清理一下（可选）
rm -rf data/submodule_data

# clone 私有仓库，使用 Render 环境变量注入的 GitHub 凭据
git clone https://${GIT_USERNAME}:${GIT_PASSWORD}@github.com/pingzheshenhei/ConanMangaText.git data/submodule_data

if [ $? -ne 0 ]; then
    echo "❌ clone 失败，请检查 GIT_USERNAME / GIT_PASSWORD"
    exit 1
fi

echo "✅ 数据目录列表:"
ls -l data/submodule_data/纯文本/日文 | head -n 10
