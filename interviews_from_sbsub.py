import requests
import os
import json
import re
from bs4 import BeautifulSoup
from tqdm import tqdm

def get_all_interview_links():
    base_url = "https://www.sbsub.com/posts/category/interviews/page/{}/"
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/114.0.0.0 Safari/537.36"
        )
    }

    page = 1
    all_links = []

    while True:
        url = base_url.format(page)
        print(f"📄 抓取第 {page} 页：{url}")
        res = requests.get(url, headers=headers)
        if res.status_code != 200:
            print(f"⚠️ 第 {page} 页返回 {res.status_code}，停止抓取")
            break

        soup = BeautifulSoup(res.text, "html.parser")
        posts = soup.select("a.post-title")
        if not posts:
            print(f"✅ 第 {page} 页没有找到帖子，抓取完毕")
            break

        for a in posts:
            href = a.get("href")
            if href:
                all_links.append(href)

        page += 1

    return list(set(all_links))  # 去重

def clean_filename(name):
    """Sanitize filename: remove slashes, colons, etc."""
    name = re.sub(r'[\\/*?:"<>|]', "", name)
    return name.strip()

def extract_article_text(url):
    headers = {
        "User-Agent": "Mozilla/5.0"
    }
    res = requests.get(url, headers=headers, timeout=10)
    res.raise_for_status()

    soup = BeautifulSoup(res.text, "html.parser")

    # Get title (used as filename)
    title_tag = soup.select_one("h1.entry-title, title")
    title = title_tag.get_text(strip=True) if title_tag else "untitled"

    # Extract article body (may vary depending on template)
    article = soup.select_one("div.entry-content") or soup.select_one("div.post-content-container")
    if not article:
        article = soup.find("main") or soup.find("article") or soup.find("body")

    paragraphs = article.find_all("p")
    text = "\n\n".join(p.get_text(strip=True) for p in paragraphs)

    return clean_filename(title), text

# Where to save the files
output_dir = "./data/interviews/sbsub"
os.makedirs(output_dir, exist_ok=True)

# Step 1: Get all interview post links
interview_links = get_all_interview_links()
print(f"🔗 共抓取到 {len(interview_links)} 篇访谈文章")

title_to_url = {}  # 新增这个字典
# Step 2: Loop through and save each
for url in tqdm(interview_links):
    try:
        filename, content = extract_article_text(url)
        filepath = os.path.join(output_dir, f"{filename}.txt")

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content.strip())
            
        # 保存映射
        title_to_url[filename] = url

    except Exception as e:
        print(f"❌ 处理失败 {url}: {e}")

# 保存为 JSON 文件
with open("./data/interviews/sbsub/sbsub_title_url_map.json", "w", encoding="utf-8") as f:
    json.dump(title_to_url, f, ensure_ascii=False, indent=2)
