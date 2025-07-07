import os
from utils.config import MANGA_TEXT_DIR, INTERVIEW_DATA_DIR, ENABLE_CACHE

manga_text_cache = {}
interview_text_cache = {}

def init_manga_cache():
    if not ENABLE_CACHE or manga_text_cache:
        return
    _init_cache_from_directory(manga_text_cache, MANGA_TEXT_DIR)

def init_interview_cache():
    if not ENABLE_CACHE or interview_text_cache:
        return
    _init_cache_from_directory(interview_text_cache, INTERVIEW_DATA_DIR, use_walk=True)

def _init_cache_from_directory(cache_dict, base_dir, use_walk=False):
    if not os.path.exists(base_dir):
        return

    for root, _, files in os.walk(base_dir) if use_walk else [(base_dir, [], os.listdir(base_dir))]:
        for filename in files:
            if filename.endswith(".txt"):
                filepath = os.path.join(root, filename)
                rel_path = os.path.relpath(filepath, base_dir)
                try:
                    with open(filepath, encoding="utf-8") as f:
                        cache_dict[rel_path] = f.read()
                except Exception as e:
                    print(f"❌ 缓存失败: {rel_path}: {e}")
