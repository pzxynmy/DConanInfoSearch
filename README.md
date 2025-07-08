
# DConanInfoSearch

一个为《名侦探柯南》粉丝打造的信息检索平台，支持漫画原文定位与访谈内容搜索。

---

## 🧭 项目简介

本平台旨在帮助柯南粉丝快速查找幕后访谈、角色解析、制作团队信息等内容。通过整合多个来源的数据，用户可以：

- 🔍 搜索关键词，定位其在漫画原文或访谈中的位置  
- 🌐 查找不同平台搬运的访谈资料，追溯原始出处或原文链接  

---

## 📚 数据来源（持续更新中）

我们整理了来自以下平台的访谈内容：

- [银色子弹](https://www.sbsub.com/posts/category/interviews/)
- [名侦探柯南事务所](https://bbs.aptx.cn/thread-296846-1-1.html)
- B站专栏与访谈视频
- 百度贴吧（柯南吧 / 柯哀分析文吧）
- 外网博客与平台（高山南博客、林原广播、X、fan博客等）
- 推荐合集站点：[http://ww2.kenanapp.com/lander](http://ww2.kenanapp.com/lander)

---

## 🛠 使用 & 开发指南

### 🔧 本地运行

```bash
git clone https://github.com/e9la/DConanInfoSearch.git
cd DConanInfoSearch
python app.py
```

浏览器打开 `http://10.0.0.94:7860` 查看界面。

### 📁 项目结构简览

```
DConanInfoSearch/
│
├── app.py                 # 主程序入口，Flask 后端逻辑
├── templates/             # HTML 页面模板
├── utils/                 # 支撑函数（搜索、文本处理等）
├── scripts/               # 爬虫与数据处理脚本（与网页无关）
└── data/                  # 存储结构化文本数据
```

---

## 🤝 如何贡献

1. 发现问题？欢迎创建 issue。  
2. 想参与开发？可以在 [issue 列表](https://github.com/e9la/DConanInfoSearch/issues) 中选择任务，留言认领避免重复。  
3. fork 本仓库，修改代码后提交 Pull Request。

贡献建议包括：

- 增加访谈数据源爬虫
- 优化搜索算法与关键词定位
- 改进前端样式与用户交互体验

---

## 📌 注意事项

所有内容来自公开网络，仅用于非商业学术研究与粉丝整理。如有版权问题请联系我们处理。

---

## 🌐 在线试用（开发中）

试用地址：[https://dconaninfosearch.onrender.com](https://dconaninfosearch.onrender.com)
