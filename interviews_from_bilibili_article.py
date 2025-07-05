"""
用于爬取UP主大理寺少卿的名柯访谈相关专栏文章

目前存在爬取时漏爬但不报错的问题
"""

import logging
import os
import re
import json
import requests
import time
from bs4 import BeautifulSoup
from datetime import datetime

# 自动生成日志文件名（与脚本同名）
try:
    script_name = os.path.splitext(os.path.basename(__file__))[0]
except NameError:
    script_name = "interviews_from_bilibili_article"

log_path = f"./logs/{script_name}.log"

# ✅ 确保 logs 目录存在
os.makedirs(os.path.dirname(log_path), exist_ok=True)

# 设置 logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(message)s",
    handlers=[
        logging.FileHandler(log_path, mode="a", encoding="utf-8"),
        # logging.StreamHandler()  # 如果需要终端输出，取消注释
    ]
)

# ✅ 在日志文件中写入时间分隔线
logging.info("\n" + "="*20 + f" Script started at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} " + "="*20 + "\n")

logging.info("✅ 日志系统初始化成功")


# readlist_ids = [
#     725889, #大理寺少卿-日常柯南采访物料
#     780064, #大理寺少卿-柯南连载30周年 青山刚昌x东野圭吾特别对谈  
#     806967, #大理寺少卿-M27相关信息及采访
#     748494, #大理寺少卿-M26相关信息及采访
#     922184, #大理寺少卿-M28相关信息及采访     
#     432168, #柯研所翻译   
#                 ]  # ← 可持续更新
with open("./data/interviews/bilibili_article/bilibili_readlists.json", encoding="utf-8") as f:
    readlist_map = json.load(f)

readlist_ids = list(readlist_map.keys())  # ['725889', '780064', ...]

headers = {"User-Agent": "Mozilla/5.0"}

# 获取合集中的文章简略信息
def get_article_list(readlist_id):
    url = f"https://api.bilibili.com/x/article/list/web/articles?id={readlist_id}&pn=1&ps=100"
    resp = requests.get(url, headers=headers)
    return resp.json()['data']['articles']

# 获取文章正文（方式一：解析网页 HTML）
def get_article_from_web(article_id):
    url = f"https://www.bilibili.com/read/cv{article_id}"
    resp = requests.get(url, headers=headers)
    soup = BeautifulSoup(resp.text, "html.parser")

    title = soup.find("h1").text.strip()
    content_div = soup.find("div", class_="article-content")
    content = content_div.get_text(separator="\n", strip=True) if content_div else "正文获取失败"
    return title, content

# # 获取文章正文（方式二：调用 API）
def get_article_from_api(article_id):
    url = f"https://api.bilibili.com/x/article/view?id={article_id}"
    resp = requests.get(url, headers=headers)
    data = resp.json()['data']
    title = data['title']
    html = data['content']  # HTML 正文
    # 纯文本提取（也可用 html2text 等处理成 markdown）
    soup = BeautifulSoup(html, "html.parser")
    text = soup.get_text(separator="\n", strip=True)
    return title, text

# 保存

for readlist_id in readlist_ids:
    logging.info(f"\n📚 开始处理合集 rl{readlist_id} ...")
    try:
        article_list = get_article_list(readlist_id)
    except Exception as e:
        logging.info(f"❌ 合集 rl{readlist_id} 获取失败：{e}")
        continue

    logging.info(f"✅ 合集 rl{readlist_id} 共 {len(article_list)} 篇文章")

    output_dir = f"./data/interviews/bilibili_article/rl{readlist_id}/"
    os.makedirs(output_dir, exist_ok=True)

    for idx, article in enumerate(article_list, 1):
        article_id = article.get('id')
        if not article_id:
            logging.info(f"⚠️ 跳过第 {idx} 项：无有效 ID")
            continue

        try:
            title, content = get_article_from_api(article_id)

            if not title or not content:
                raise ValueError("缺失标题或正文")

            safe_title = title[:30].replace("/", "-").replace("\\", "-")
            filename = os.path.join(output_dir, f"{idx:02d}_{safe_title}.txt")

            with open(filename, "w", encoding="utf-8") as f:
                f.write(f"Title: {title}\nURL: https://www.bilibili.com/read/cv{article_id}\n\n{content}")

            logging.info(f"✅ 已保存：{filename}")
        except Exception as e:
            logging.info(f"❌ 获取失败：cv{article_id}，原因：{e}")
