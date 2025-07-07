import os
from utils.config import MANGA_TEXT_DIR
from utils.cache_utils import manga_text_cache

def startup_check():
    print("🚀 启动时自动检查子模块数据是否成功加载...")
    print(f"📁 当前工作目录: {os.getcwd()}")
    print(f"📂 MANGA_TEXT_DIR: {MANGA_TEXT_DIR}")

    if not os.path.exists(MANGA_TEXT_DIR):
        print("❌ 路径不存在！可能 submodule 没被正确拉取")
    else:
        try:
            files = [f for f in os.listdir(MANGA_TEXT_DIR) if f.endswith(".txt")]
            print(f"📄 找到 {len(files)} 个文本文件: {files[:3]}...")
        except Exception as e:
            print(f"❌ 列出文件时出错: {e}")

    print(f"📦 manga_text_cache 当前大小: {len(manga_text_cache)}")
    print("✅ 检查完成")
