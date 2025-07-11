import os
import re
import json

# 加载 sbsub 访谈标题-链接映射表
try:
    with open("./data/interviews/sbsub/sbsub_title_url_map.json", encoding="utf-8") as f:
        sbsub_title_url_map = json.load(f)

    with open("./data/interviews/bilibili_article/bilibili_readlists.json", encoding="utf-8") as f:
        bilibili_source_map = json.load(f)

except FileNotFoundError:
    sbsub_title_url_map = {}
    bilibili_source_map = {}

def get_interview_metadata(rel_path: str) -> dict:
    # 1. 名侦探柯南事务所论坛
    if "bbs_aptx.txt" in rel_path:
        return {
            "source": "名侦探柯南事务所论坛",
            "url": "https://bbs.aptx.cn/forum.php?mod=viewthread&tid=296846&extra=page%3D5&page=2"
        }

    # 2. B站 readlist
    match = re.search(r"bilibili_article/(rl\d+)", rel_path)
    if match:
        full_rl_id = match.group(1)        # rl725889
        numeric_id = full_rl_id[2:]        # 725889
        source = bilibili_source_map.get(numeric_id, "B站访谈整理（by未知）")
        return {
            "source": source,
            "url": f"https://www.bilibili.com/read/readlist/{full_rl_id}"
        }

    # 3. 银色子弹 sbsub
    if "sbsub/" in rel_path:
        filename = os.path.basename(rel_path).replace(".txt", "")
        url = sbsub_title_url_map.get(filename)
        return {
            "source": "银色子弹访谈整理",
            "url": url
        }

    # 4. fallback
    return {
        "source": "未知来源",
        "url": None
    }
