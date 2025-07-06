from flask import Flask, render_template, request, jsonify
import os
import re

from utils.interview_sources import get_interview_metadata


app = Flask(__name__, static_folder="static", template_folder="templates")

# 🚀 内存缓存 - 性能优化
ENABLE_CACHE = os.environ.get("ENABLE_CACHE", "true").lower() == "true"
manga_text_cache = {}  # 漫画文本缓存
interview_text_cache = {}  # 访谈文本缓存

# 🚀 缓存初始化函数
def init_manga_cache():
    """初始化漫画文本缓存"""
    if not ENABLE_CACHE or manga_text_cache:
        return
    
    base_dir = "data/japanese_text"
    if not os.path.exists(base_dir):
        return
    
    print("📥 正在预加载漫画文本到内存缓存...")
    for filename in os.listdir(base_dir):
        if filename.endswith(".txt"):
            file_path = os.path.join(base_dir, filename)
            try:
                with open(file_path, encoding="utf-8") as f:
                    manga_text_cache[filename] = f.read()
            except Exception as e:
                print(f"❌ 缓存文件失败 {filename}: {e}")
    
    print(f"✅ 已缓存 {len(manga_text_cache)} 个漫画文件")

# 功能一：漫画文本检索（优化版）
def count_word_in_documents(word):
    result = []
    base_dir = "data/japanese_text"
    
    # 🚀 使用缓存或直接读取文件
    if ENABLE_CACHE:
        init_manga_cache()  # 懒加载
        file_data = manga_text_cache
    else:
        # 原始方式：直接读取文件
        file_data = {}
        if not os.path.exists(base_dir):
            return result
        
        for filename in os.listdir(base_dir):
            if filename.endswith(".txt"):
                file_path = os.path.join(base_dir, filename)
                with open(file_path, encoding="utf-8") as f:
                    file_data[filename] = f.read()
    
    # 处理逻辑保持不变
    for filename, text in file_data.items():
        # 分页结构：===Page X===
        pages = re.split(r"===Page (\d+)===", text)
        page_nums = []
        total_count = 0

        # 结构：['', page_num1, content1, page_num2, content2, ...]
        for i in range(1, len(pages) - 1, 2):
            page_number = int(pages[i])
            content = pages[i + 1]
            count = content.count(word)
            if count > 0:
                page_nums.append(page_number)
                total_count += count

        if total_count > 0:
            volume_match = re.match(r"^(\d+)\.txt$", filename)
            volume = int(volume_match.group(1)) if volume_match else filename
            result.append({
                "volume": volume,
                "count": total_count,
                "pages": sorted(page_nums)
            })

    # ✅ 按卷号排序
    result.sort(key=lambda x: x["volume"])
    return result

# 首页：返回 HTML 页面
@app.route("/")
def home():
    return render_template("index.html")

# 漫画文本检索接口
@app.route("/search", methods=["POST"])
def search():
    word = request.form.get("word", "").strip()
    result = count_word_in_documents(word)
    return jsonify(result)

# 🚀 访谈缓存初始化函数
def init_interview_cache():
    """初始化访谈文本缓存"""
    if not ENABLE_CACHE or interview_text_cache:
        return
    
    base_dir = "data/interviews"
    if not os.path.exists(base_dir):
        return
    
    print("📥 正在预加载访谈文本到内存缓存...")
    for root, dirs, files in os.walk(base_dir):
        for filename in files:
            if filename.endswith(".txt"):
                filepath = os.path.join(root, filename)
                rel_path = os.path.relpath(filepath, base_dir)
                try:
                    with open(filepath, encoding="utf-8") as f:
                        interview_text_cache[rel_path] = f.read()
                except Exception as e:
                    print(f"❌ 缓存访谈文件失败 {rel_path}: {e}")
    
    print(f"✅ 已缓存 {len(interview_text_cache)} 个访谈文件")

# 访谈资料接口（优化版）
@app.route("/interview_search", methods=["POST"])
def interview_search():
    word = request.form.get("word", "").strip()
    base_dir = "data/interviews"
    results = []

    if not word:
        return jsonify(results)

    # 🚀 使用缓存或直接读取文件
    if ENABLE_CACHE:
        init_interview_cache()  # 懒加载
        file_data = interview_text_cache
    else:
        # 原始方式：直接读取文件
        file_data = {}
        for root, dirs, files in os.walk(base_dir):
            for filename in files:
                if filename.endswith(".txt"):
                    filepath = os.path.join(root, filename)
                    rel_path = os.path.relpath(filepath, base_dir)
                    try:
                        with open(filepath, encoding="utf-8") as f:
                            file_data[rel_path] = f.read()
                    except Exception as e:
                        print(f"❌ Error reading {filepath}: {e}")

    # 处理逻辑保持不变
    for rel_path, text in file_data.items():
        try:
            count = text.count(word)
            if count > 0:
                # 匹配句子片段（简化处理：用句号、换行、问号、叹号分句）
                sentences = re.split(r'[。！？\n]', text)
                matched_snippets = []
                for s in sentences:
                    if word in s:
                        snippet = f"...{s.strip()}..."
                        matched_snippets.append(snippet)
                matched_snippets = matched_snippets[:3]  # 最多 3 条

                # 来源信息：可以继续扩展更多规则
                meta = get_interview_metadata(rel_path)

                results.append({
                    "file": rel_path,
                    "count": count,
                    "source": meta["source"],
                    "url": meta["url"],
                    "snippets": matched_snippets
                })
        except Exception as e:
            print(f"❌ Error processing {rel_path}: {e}")

    results.sort(key=lambda x: -x["count"])
    return jsonify(results)


# 🚀 缓存状态查看接口（调试用）
@app.route("/cache_status")
def cache_status():
    """查看缓存状态"""
    status = {
        "cache_enabled": ENABLE_CACHE,
        "manga_cache_size": len(manga_text_cache),
        "interview_cache_size": len(interview_text_cache),
        "total_memory_usage_mb": sum(len(text.encode('utf-8')) for text in manga_text_cache.values()) / 1024 / 1024 +
                                sum(len(text.encode('utf-8')) for text in interview_text_cache.values()) / 1024 / 1024
    }
    return jsonify(status)

# 未来：接入 LLM 问答接口
@app.route("/ask", methods=["POST"])
def ask():
    question = request.form.get("question", "")
    return jsonify({"answer": f"暂未接入 LLM，收到问题：{question}"})

# 启动服务（适配 Render 的 PORT 环境变量）
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 7860))
    app.run(host="0.0.0.0", port=port)
