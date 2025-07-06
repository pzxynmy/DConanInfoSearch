"""This script scrapes the blog entries from Megumi Hayashibara's blogs on Ameblo.

使用:
    0. 解压 `blogs.zip` 到 `data/hayashibara_blogs/blogs` 目录下:
        ```
        data/hayashibara_blogs
        ├── blogs
        │   ├── ENTRY_ID.txt
        │   └── ...
        └── blog_meta.json
        ```
    1. 更新已缓存的博客元数据列表（blog_meta.json）：
        ```python get_hayashibara_blogs.py --update_meta```

    2. 根据元数据列表保存博客内容（blogs目录下）：
        ```python get_hayashibara_blogs.py --save_data```
"""
import os
import json
from tqdm import tqdm
from typing import List, Optional
import requests
from bs4 import BeautifulSoup

base_url = "https://ameblo.jp/megumi--hayashibara/entrylist.html"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

def get_up_to_date_pages_urls(base_url:str):
    response = requests.get(base_url, headers=headers)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")
    # get the end pagination link
    end_page_link = soup.find("a", class_="skin-paginationEnd")
    end_url = end_page_link["href"]
    page_num = end_url.split("-")[-1].split(".")[0]
    print(f"Total pages: {page_num}")
    page_urls = [base_url]
    for i in range(2, int(page_num) + 1):
        # add '-{num}' to the base URL to get the specific page
        page_url = f"{base_url[:-5]}-{i}.html"
        page_urls.append(page_url)
    return page_urls


def get_up_to_date_blog_entries(page_urls:List[str]):
    # Each blog url is in <a> under <h2> tags with attr `data-uranus-component="entryItemTitle"`
    blog_entries_map = {}
    for page_url in tqdm(page_urls, desc="Fetching blog entries"):
        response = requests.get(page_url, headers=headers)
        response.raise_for_status()
        page_soup = BeautifulSoup(response.text, "html.parser")
        entries = page_soup.find_all("h2", {"data-uranus-component": "entryItemTitle"})
        if not entries:
            print(f"No entries found on page: {page_url}")
            continue
        for entry in entries:
            a_tag = entry.find("a")
            if a_tag and a_tag.has_attr("href"):
                entry_id =  a_tag["href"][-16:-5]
                title = a_tag.get_text(strip=True)
                try:
                    test_id = int(entry_id)
                except ValueError:
                    print(f"Invalid entry ID: {entry_id} in {page_url}")
                    continue
                blog_entries_map[entry_id] = title
    return blog_entries_map


def count_cached_blog_entries(meta_path:str) -> Optional[dict]:
    # read the blog entries mapping from json
    import json
    if not os.path.exists(meta_path):
        print(f"File not found: {meta_path}")
        return None
    with open(meta_path, "r", encoding="utf-8") as f:
        meta = json.load(f)
    if "entries" not in meta:
        print(f"No entries found in the meta data: {meta_path}")
        return None
    return len(meta["entries"]) 


def update_blog_meta(meta_path:str, up_to_date_entries:dict):
    with open(meta_path, "r", encoding="utf-8") as f:
        meta_data = json.load(f)
    entries = meta_data["entries"]
    old_meta_ids = set([entry["id"] for entry in entries])
    up_to_date_ids = set(up_to_date_entries.keys())
    missing_entries = up_to_date_ids - old_meta_ids
    if not missing_entries:
        print("No new entries to update.")
        return
    print(f"Updating {len(missing_entries)} new entries to the meta data.")
    for entry_id in missing_entries:
        entry_title = up_to_date_entries[entry_id]
        entries.append({"id": entry_id, "title": entry_title})
    meta_data["entries"] = entries
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(meta_data, f, ensure_ascii=False, indent=4) 


def save_blogs_text(meta_path:str):
    dirname = os.path.dirname(meta_path)
    save_path = os.path.join(dirname, "blogs")
    os.makedirs(save_path, exist_ok=True)
    with open(meta_path, "r", encoding="utf-8") as f:
        meta_data = json.load(f)
    base_url = meta_data["base_url"]
    entries = meta_data["entries"]
    all_entry_ids = [entry["id"] for entry in entries]
    existing_entry_ids = [os.path.splitext(f)[0] for f in os.listdir(save_path) if f.endswith(".txt")]
    missing_entry_ids = set(all_entry_ids) - set(existing_entry_ids)
    if not missing_entry_ids:
        print("All blog entries are already saved.")
        return
    print(f"Missing entries: {len(missing_entry_ids)}")
    input("Press Enter to save missing entries...")
    for entry in tqdm(missing_entry_ids, desc="Saving blog entries"):
        entry_url = base_url.replace("ENTRYID", entry)
        response = requests.get(entry_url, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        content_div = soup.find("div", class_="skin-entryBody")
        if content_div:
            text_content = content_div.get_text(strip=True)
            with open(os.path.join(save_path, f"{entry}.txt"), "w", encoding="utf-8") as f:
                f.write(text_content)
        else:
            print(f"Content not found for entry {entry}")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Scrape Megumi Hayashibara's blog entries from Ameblo.")
    parser.add_argument("--update_meta", "-u", action="store_true",
                        help="Update the blog meta list.")
    parser.add_argument("--save_data", "-s", action="store_true",
                        help="Save the blog entries to text files.")
    args = parser.parse_args()
    
    # 更新 blog_meta.json，与林原博客的最新状态保持一致
    if args.update_meta:
        page_urls = get_up_to_date_pages_urls(base_url)
        blog_entries_map = get_up_to_date_blog_entries(page_urls)
        update_blog_meta("./data/hayashibara_blogs/blog_meta.json", blog_entries_map)
        
    # 保存博客内容到文本文件 
    if args.save_data:
        count = count_cached_blog_entries("./data/hayashibara_blogs/blog_meta.json")
        print(f"Cached blog entries count: {count}")
        if count:
            save_blogs_text("./data/hayashibara_blogs/blog_meta.json")
        else:
            print("No blog meta data found. Please update the meta list first.")