import os
import re
import json

# 加载 sbsub 访谈标题-链接映射表
try:
    with open("./data/interviews/sbsub/sbsub_title_url_map.json", encoding="utf-8") as f:
        sbsub_title_url_map = json.load(f)
except FileNotFoundError:
    sbsub_title_url_map = {}

def get_interview_metadata(rel_path: str) -> dict:
    # 1. 名侦探柯南事务所论坛
    if "bbs_aptx.txt" in rel_path:
        return {
            "source": "名侦探柯南事务所论坛",
            "url": "https://bbs.aptx.cn/forum.php?mod=viewthread&tid=296846&extra=page%3D5&page=2"
        }

    # 2. B站 readlist
    match = re.search(r"bilibili_702964214/(rl\d+)", rel_path)
    if match:
        readlist_id = match.group(1)
        return {
            "source": "B站访谈整理（by大理寺少卿）",
            "url": f"https://www.bilibili.com/read/readlist/{readlist_id}"
        }

    # 3. 银色子弹（sbsub）访谈
    if "sbsub/" in rel_path:
        filename = os.path.basename(rel_path).replace(".txt", "")
        url = sbsub_title_url_map.get(filename)
        return {
            "source": "银色子弹访谈整理",
            "url": url
        }

    # 4. 其他情况
    return {
        "source": "未知来源",
        "url": None
    }
