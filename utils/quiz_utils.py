# 文件: utils/quiz_utils.py
import os
import json

def load_quiz_bank():
    """优先从本地 quiz_bank.json 加载题库，否则从环境变量 QUIZ_BANK_JSON 加载"""

    local_path = "quiz_bank.json"

    # 1. 尝试从本地文件加载
    if os.path.exists(local_path):
        try:
            with open(local_path, encoding="utf-8") as f:
                data = json.load(f)
                print(f"✅ 本地题库加载成功，共 {len(data)} 道题")
                return data
        except Exception as e:
            print(f"⚠️ 本地题库加载失败: {e}")

    # 2. 备用：尝试从环境变量加载
    try:
        raw = os.environ.get("QUIZ_BANK_JSON", "")
        if raw.strip() == "":
            print("⚠️ 未设置环境变量 QUIZ_BANK_JSON，跳过题库加载")
            return []
        data = json.loads(raw)
        print(f"✅ 从环境变量加载题库成功，共 {len(data)} 道题")
        return data
    except Exception as e:
        print(f"❌ 从环境变量加载题库失败: {e}")

    # 3. 两者都失败
    print("⚠️ 无可用题库，问答功能将禁用")
    return []




