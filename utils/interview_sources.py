import re

def get_interview_metadata(rel_path: str) -> dict:
    if "bbs_aptx.txt" in rel_path:
        return {
            "source": "名侦探柯南事务所论坛",
            "url": "https://bbs.aptx.cn/forum.php?mod=viewthread&tid=296846&extra=page%3D5&page=2"
        }
    
    # 检查是否是 B 站的 readlist
    match = re.search(r"bilibili_702964214/(rl\d+)", rel_path)
    if match:
        readlist_id = match.group(1)
        return {
            "source": f"B站访谈整理（by大理寺少卿）",
            "url": f"https://www.bilibili.com/read/readlist/{readlist_id}"
        }

    return {
        "source": "未知来源",
        "url": None
    }
