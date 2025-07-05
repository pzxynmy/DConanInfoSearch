## This script is used to fetch interview info from bbs.aptx

import os
import re
import requests
from bs4 import BeautifulSoup

SAVE_PATH = "./data/interviews/bbs_aptx.txt"
BASE_URL = "https://bbs.aptx.cn/thread-296846-{}-1.html"
headers = {
    "User-Agent": "Mozilla/5.0"
}

# 请求第一页，先解析总页数
print("Detecting total number of pages...")
resp = requests.get(BASE_URL.format(1), headers=headers)
resp.encoding = 'utf-8'
soup = BeautifulSoup(resp.text, 'html.parser')

# 找到最大页数
page_links = soup.select("div.pg a")
page_nums = [int(a.text) for a in page_links if a.text.isdigit()]
max_page = max(page_nums) if page_nums else 1
print(f"Total pages detected: {max_page}")

# 开始逐页抓取
all_posts = []

for page in range(1, max_page + 1):
    url = BASE_URL.format(page)
    print(f"Fetching page {page}: {url}")
    resp = requests.get(url, headers=headers)
    resp.encoding = 'utf-8'
    soup = BeautifulSoup(resp.text, "html.parser")
    post_cells = soup.find_all("td", class_="t_f")

    if not post_cells:
        print(f"No posts found on page {page}, skipping.")
        continue

    for cell in post_cells:
        post_text = cell.get_text(separator="\n", strip=True)
        post_text = re.sub(r'\[[^\]]+\]', '', post_text)  # Remove BBCode like [b], [img]
        all_posts.append(post_text)

# 合并保存为一个大文件
full_text = "\n\n=== PAGE BREAK ===\n\n".join(all_posts)
os.makedirs(os.path.dirname(SAVE_PATH), exist_ok=True)
with open(SAVE_PATH, "w", encoding="utf-8") as f:
    f.write(full_text)

print(f"\nDone! Saved all {len(all_posts)} posts to {SAVE_PATH}")
