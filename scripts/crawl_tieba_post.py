#!/usr/bin/env python3
"""
百度贴吧帖子内容爬虫 + 智能过滤器
抓取指定帖子的所有楼层内容并自动过滤出高价值问答
URL: https://tieba.baidu.com/p/7223841891?pn=1-26
"""

import random
import requests
import time
import os
import re
from bs4 import BeautifulSoup
from typing import List, Dict, Optional
import json

class TiebaQAFilter:
    """贴吧问答内容智能过滤器"""
    def __init__(self):
        # 需要过滤掉的内容
        self.fold_keywords = [
            "该楼层疑似违规已被系统折叠",
            "此回复已被折叠", 
            "折叠回复",
            "隐藏此楼",
            "查看此楼"
        ]
        
        # 无意义的短回复
        self.meaningless_patterns = [
            r"^[顶支持沙发前排占楼]+$",
            r"^[0-9]+楼$",
            r"^[哈哦嗯额咦呵]+$",
            r"^[草666笑哭]+$",
            r"^[\.。！？\s]+$",
            r"^收藏了?$",
            r"^马克$",
            r"^mark$",
            r"^[+1同]+$"
        ]
        
        # 问题相关关键词（高优先级保留）
        self.question_keywords = [
            "问", "请问", "想问", "求问", "咨询", "疑问",
            "？", "吗", "呢", "吧", "求助", "help",
            "有没有", "是否", "会不会", "能不能",
            "哪里", "什么", "怎么", "为什么", "如何"
        ]
        
        # 回答相关关键词
        self.answer_keywords = [
            "答", "回答", "解释", "说明", "分析", "推理",
            "是这样", "据我所知", "应该是", "其实",
            "根据", "出处", "来源", "访谈中", "青山说"
        ]
        
        self.conan_keywords = [
            # 关键词
            "柯南", "新一", "工藤", "灰原", "哀", "小哀", "毛利", "兰", "小兰",
            "青山", "73", "Boss", "黑衣组织", "APTX",
            "剧情", "真相", "推理", "案件", "集数", "漫画",
            "动画", "访谈", "官方", "作者",
            
            # 主要角色
            "江户川", "宫野", "志保", "小五郎", "博士", "阿笠",
            
            # 少年侦探团
            "步美", "光彦", "元太", "侦探团",
            
            # 重要配角
            "服部", "平次", "和叶", "远山", "基德", "怪盗", "黑羽", "快斗",
            "园子", "铃木", "妃英理", "有希子", "优作",
            
            # FBI/CIA/公安
            "赤井", "秀一", "安室", "透", "降谷", "零", "水无", "怜奈", 
            "本堂", "瑛海", "冲矢", "昴", "世良", "真纯",
            
            # 黑衣组织成员
            "琴酒", "伏特加", "苦艾酒", "贝尔摩德", "蘭姆", "烏丸", "蓮耶",
            "波本", "基尔", "黑麦", "龙舌兰", "皮斯克",
            
            # 警察相关
            "目暮", "高木", "佐藤", "美和子", "白鸟", "松本", "茶木",
            
            # 组织代号
            "gin", "vodka", "vermouth", "rum", "bourbon", "kir", "rye",
            
            # 其他重要人物
            "小林", "澄子", "横沟", "山村", "大和", "上原"
        ]

        
        # 有用信息关键词
        self.useful_keywords = [
            "规则", "链接", "整理", "资料", "档案",
            "出处", "来源", "翻译", "确认", "否认"
        ]
    
    def is_system_folded(self, content: str) -> bool:
        """检查是否被系统折叠"""
        for keyword in self.fold_keywords:
            if keyword in content:
                return True
        return False
    
    def is_meaningless_short(self, content: str) -> bool:
        """检查是否是无意义的短回复"""
        content = content.strip()
        
        # 长度过短
        if len(content) < 5:
            return True
        
        # 匹配无意义模式
        for pattern in self.meaningless_patterns:
            if re.match(pattern, content, re.IGNORECASE):
                return True
        
        return False
    
    def calculate_content_score(self, content: str) -> float:
        """计算内容价值分数"""
        score = 0.0
        
        # 基础分数（根据长度）
        if len(content) > 50:
            score += 1.0
        elif len(content) > 20:
            score += 0.5
        
        # 问题相关加分
        for keyword in self.question_keywords:
            if keyword in content:
                score += 2.0
                break
        
        # 回答相关加分 
        for keyword in self.answer_keywords:
            if keyword in content:
                score += 1.5
                break
        
        # 柯南相关加分
        conan_matches = sum(1 for keyword in self.conan_keywords if keyword in content)
        score += conan_matches * 1.0
        
        # 有用信息加分
        useful_matches = sum(1 for keyword in self.useful_keywords if keyword in content)
        score += useful_matches * 0.8
        
        # URL链接加分
        if "http" in content or "www." in content:
            score += 1.0
        
        # 具体数字信息加分（集数、章节等）
        if re.search(r'\d+集|\d+话|\d+卷|\d+章', content):
            score += 0.8
        
        return score
    
    def should_keep_post(self, post: Dict) -> bool:
        """判断是否应该保留这个楼层"""
        content = post['content']
        
        # 检查是否被折叠
        if self.is_system_folded(content):
            return False
        
        # 检查是否无意义
        if self.is_meaningless_short(content):
            return False
        
        # 根据分数判断
        score = self.calculate_content_score(content)
        return score >= 1.5  # 保留中等价值以上的内容

class TiebaPostCrawler:
    def __init__(self, post_id: str, max_pages: int = 2):
        self.post_id = post_id
        self.max_pages = max_pages
        self.base_url = f"https://tieba.baidu.com/p/{post_id}"
        self.session = requests.Session()
        
        # 更强的反反爬虫请求头池
        self.headers_pool = [
            {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'none',
                'Cache-Control': 'max-age=0'
            },
            {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Safari/605.1.15',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'zh-CN,zh-Hans;q=0.9',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1'
            },
            {
                'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
                'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1'
            }
        ]
        
        self.posts = []  # 存储所有楼层数据
        self.filtered_posts = []  # 存储过滤后的高价值数据
        self.post_title = ""
        self.filter = TiebaQAFilter()
        self.captcha_count = 0  # 验证码遇到次数
        
    def get_random_headers(self):
        """获取随机请求头"""
        return random.choice(self.headers_pool)
        
    def fetch_page(self, page_num: int, max_retries: int = 3) -> Optional[BeautifulSoup]:
        """获取指定页面的HTML内容，带反反爬虫策略"""
        url = f"{self.base_url}?pn={page_num}"
        
        for attempt in range(max_retries):
            try:
                # 随机延迟
                delay = random.uniform(5, 12)  # 5-12秒随机延迟
                if attempt > 0:
                    print(f"⏳ 等待 {delay:.1f} 秒后重试...")
                    time.sleep(delay)
                
                # 使用随机请求头
                headers = self.get_random_headers()
                
                print(f"📥 正在抓取第 {page_num} 页 (尝试 {attempt + 1}/{max_retries}): {url}")
                print(f"🔧 使用UA: {headers['User-Agent'][:50]}...")
                
                response = self.session.get(url, headers=headers, timeout=20)
                response.raise_for_status()
                
                print(f"✅ 请求成功，状态码: {response.status_code}")
                print(f"📄 响应长度: {len(response.text)} 字符")
                
                # 检查是否被重定向或需要验证
                if "验证" in response.text or "captcha" in response.url.lower() or "verify" in response.text.lower():
                    self.captcha_count += 1
                    print(f"🚫 第 {page_num} 页遇到验证码 (第{self.captcha_count}次)")
                    
                    if self.captcha_count >= 3:
                        print("❌ 验证码次数过多，建议使用手动方案")
                        print("💡 请运行: python scripts/anti_captcha_guide.py")
                        return None
                    
                    # 增加更长延迟再重试
                    longer_delay = random.uniform(15, 25)
                    print(f"⏳ 遇到验证码，等待 {longer_delay:.1f} 秒后重试...")
                    time.sleep(longer_delay)
                    continue
                
                # 检查页面内容是否正常
                if len(response.text) < 1000:
                    print(f"⚠️  第 {page_num} 页内容过短，可能被限制")
                    continue
                
                response.encoding = 'utf-8'
                soup = BeautifulSoup(response.text, 'html.parser')
                return soup
                
            except requests.Timeout as e:
                print(f"⏰ 第 {page_num} 页请求超时 (尝试 {attempt + 1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    wait_time = random.uniform(10, 20)
                    print(f"⏳ 等待 {wait_time:.1f} 秒后重试...")
                    time.sleep(wait_time)
                
            except requests.RequestException as e:
                print(f"❌ 第 {page_num} 页请求失败 (尝试 {attempt + 1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    time.sleep(random.uniform(5, 10))
        
        print(f"💔 第 {page_num} 页经过 {max_retries} 次尝试仍然失败")
        return None
    
    def extract_title(self, soup: BeautifulSoup) -> str:
        """提取帖子标题"""
        # 尝试多种可能的标题选择器
        title_selectors = [
            'h3.core_title_txt',
            '.core_title_txt',
            'h1',
            'h2', 
            '.thread_title',
            'title'
        ]
        
        for selector in title_selectors:
            title_elem = soup.select_one(selector)
            if title_elem:
                title = title_elem.get_text(strip=True)
                if title and "百度贴吧" not in title:
                    return title
        
        return "未知标题"
    
    def extract_posts_from_page(self, soup: BeautifulSoup, page_num: int) -> List[Dict]:
        """从页面中提取所有楼层内容"""
        posts = []
        
        # 尝试多种可能的楼层容器选择器
        post_selectors = [
            '.l_post',
            '.j_l_post', 
            '.core_reply',
            '.p_postlist .l_post',
            'div[data-field]'  # 贴吧楼层通常有data-field属性
        ]
        
        post_elements = []
        for selector in post_selectors:
            post_elements = soup.select(selector)
            if post_elements:
                print(f"✅ 使用选择器 '{selector}' 找到 {len(post_elements)} 个楼层")
                break
        
        if not post_elements:
            print(f"⚠️  第 {page_num} 页未找到楼层内容，尝试备用方案")
            # 备用方案：查找包含用户发言的div
            post_elements = soup.find_all('div', class_=re.compile(r'post|reply'))
        
        for i, post_elem in enumerate(post_elements):
            try:
                post_data = self.extract_single_post(post_elem, page_num, i)
                if post_data and post_data['content'].strip():
                    posts.append(post_data)
            except Exception as e:
                print(f"⚠️  解析第 {page_num} 页第 {i+1} 个楼层时出错: {e}")
                continue
        
        return posts
    
    def extract_single_post(self, post_elem, page_num: int, index: int) -> Optional[Dict]:
        """提取单个楼层的详细信息"""
        try:
            # 提取楼层号
            floor_num = None
            floor_selectors = [
                '.tail-info .tail-info-num',
                '.floor',
                '.post-tail-wrap .tail-info',
                '[data-field]'  # 有时楼层号在data-field中
            ]
            
            for selector in floor_selectors:
                floor_elem = post_elem.select_one(selector)
                if floor_elem:
                    floor_text = floor_elem.get_text(strip=True)
                    floor_match = re.search(r'(\d+)楼', floor_text)
                    if floor_match:
                        floor_num = int(floor_match.group(1))
                        break
            
            # 如果没找到楼层号，使用页面内索引估算
            if floor_num is None:
                # 每页大约30楼，根据页码和索引估算
                floor_num = (page_num - 1) * 30 + index + 1
            
            # 提取用户名
            username = "匿名用户"
            username_selectors = [
                '.j_user_card',
                '.p_author_name',
                '.username',
                '.author'
            ]
            
            for selector in username_selectors:
                username_elem = post_elem.select_one(selector)
                if username_elem:
                    username = username_elem.get_text(strip=True)
                    break
            
            # 提取发帖时间
            post_time = ""
            time_selectors = [
                '.tail-info:last-child',
                '.post-tail-wrap .tail-info:last-child',
                '.j_reply_data',
                '.post-time'
            ]
            
            for selector in time_selectors:
                time_elem = post_elem.select_one(selector)
                if time_elem:
                    post_time = time_elem.get_text(strip=True)
                    break
            
            # 提取帖子内容
            content = ""
            content_selectors = [
                '.d_post_content',
                '.j_d_post_content',
                '.post-content',
                '.content',
                '.cc .j_d_post_content'
            ]
            
            for selector in content_selectors:
                content_elem = post_elem.select_one(selector)
                if content_elem:
                    # 移除广告和无关元素
                    for ad in content_elem.select('.j_sponsor, .at, .emotion'):
                        ad.decompose()
                    
                    content = content_elem.get_text(separator='\n', strip=True)
                    break
            
            # 如果还是没找到内容，尝试更宽泛的搜索
            if not content:
                content = post_elem.get_text(separator='\n', strip=True)
                # 清理掉明显的导航和广告文本
                content = re.sub(r'(回复|删除|举报|分享|收藏|签到|等级|经验)', '', content)
                content = re.sub(r'\s+', ' ', content).strip()
            
            return {
                'floor': floor_num,
                'username': username,
                'post_time': post_time,
                'content': content,
                'page': page_num
            }
            
        except Exception as e:
            print(f"❌ 解析楼层出错: {e}")
            return None
    
    def crawl_all_pages(self):
        """爬取所有页面"""
        print(f"🚀 开始抓取帖子 {self.post_id}，共 {self.max_pages} 页")
        
        for page_num in range(1, self.max_pages + 1):
            soup = self.fetch_page(page_num)
            if soup is None:
                print(f"⚠️  跳过第 {page_num} 页")
                continue
            
            # 第一页时提取标题
            if page_num == 1 and not self.post_title:
                self.post_title = self.extract_title(soup)
                print(f"📋 帖子标题: {self.post_title}")
            
            # 提取楼层内容
            page_posts = self.extract_posts_from_page(soup, page_num)
            self.posts.extend(page_posts)
            
            print(f"✅ 第 {page_num} 页抓取完成，获得 {len(page_posts)} 个楼层")
            
            # 延迟避免被ban
            time.sleep(2)
        
        print(f"🎉 抓取完成！总共获得 {len(self.posts)} 个楼层")
        
        # 执行智能过滤
        self.apply_filter()
    
    def apply_filter(self):
        """应用智能过滤器"""
        print(f"\n🧹 开始智能过滤...")
        
        filtered_count = 0
        for post in self.posts:
            if self.filter.should_keep_post(post):
                # 添加评分信息
                post['score'] = self.filter.calculate_content_score(post['content'])
                self.filtered_posts.append(post)
                filtered_count += 1
        
        removed_count = len(self.posts) - filtered_count
        print(f"✅ 过滤完成：保留 {filtered_count} 个高价值楼层，过滤掉 {removed_count} 个低质量内容")
        
        if removed_count > 0:
            print(f"📊 保留率: {filtered_count/len(self.posts)*100:.1f}%")
    
    def save_to_file(self, save_json: bool = False):
        """保存抓取结果到文件"""
        # 确保输出目录存在
        output_dir = "data/interviews"
        os.makedirs(output_dir, exist_ok=True)
        
        # 清理标题用作文件名
        safe_title = re.sub(r'[<>:"/\\|?*]', '_', self.post_title)
        safe_title = safe_title[:50]  # 限制长度
        
        # 保存过滤后的高价值内容为文本文件（纯文本格式）
        txt_filename = f"{output_dir}/tieba_{self.post_id}_{safe_title}.txt"
        with open(txt_filename, 'w', encoding='utf-8') as f:
            f.write(f"{self.post_title}\n\n")
            f.write(f"帖子ID: {self.post_id}\n")
            f.write(f"抓取时间: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"原始楼层数: {len(self.posts)}\n")
            f.write(f"高价值楼层数: {len(self.filtered_posts)}\n")
            f.write("=" * 50 + "\n\n")
            
            for post in self.filtered_posts:
                f.write(f"【{post['floor']}楼】{post['username']}\n")
                if post['post_time']:
                    f.write(f"时间: {post['post_time']}\n")
                f.write(f"\n{post['content']}\n\n")
        
        print(f"💾 过滤后内容已保存到: {txt_filename}")
        
        # 可选保存JSON文件（完整数据）
        if save_json:
            json_filename = f"{output_dir}/tieba_{self.post_id}_{safe_title}.json"
            with open(json_filename, 'w', encoding='utf-8') as f:
                json.dump({
                    'title': self.post_title,
                    'post_id': self.post_id,
                    'crawl_time': time.strftime('%Y-%m-%d %H:%M:%S'),
                    'total_posts': len(self.posts),
                    'filtered_posts': len(self.filtered_posts),
                    'raw_posts': self.posts,
                    'filtered_posts_data': self.filtered_posts
                }, f, ensure_ascii=False, indent=2)
            print(f"💾 完整数据已保存到: {json_filename}")
        
        return txt_filename
    
    def run(self, save_json: bool = False):
        """运行完整的爬取流程"""
        self.crawl_all_pages()
        result_file = self.save_to_file(save_json)
        
        # 输出统计信息
        print(f"\n📊 抓取统计:")
        print(f"   标题: {self.post_title}")
        print(f"   原始楼层: {len(self.posts)}")
        print(f"   高价值楼层: {len(self.filtered_posts)}")
        if self.filtered_posts:
            print(f"   楼层范围: {min(p['floor'] for p in self.filtered_posts)} - {max(p['floor'] for p in self.filtered_posts)}")
            avg_score = sum(p['score'] for p in self.filtered_posts) / len(self.filtered_posts)
            print(f"   平均评分: {avg_score:.1f}")
        
        return result_file

def main():
    """主函数"""
    print("🕷️  百度贴吧智能爬虫 v2.0")
    print("=" * 50)
    
    # 配置参数
    POST_ID = "7223841891"
    MAX_PAGES = 10  # 测试阶段只抓取前2页
    
    print(f"📋 测试模式：只抓取前 {MAX_PAGES} 页，自动过滤低质量内容")
    
    # 创建爬虫实例并运行
    crawler = TiebaPostCrawler(POST_ID, MAX_PAGES)
    
    # 先测试网络连接
    print("\n🔍 测试网络连接...")
    try:
        test_response = requests.get("https://www.baidu.com", timeout=5)
        print(f"✅ 百度首页访问正常: {test_response.status_code}")
    except Exception as e:
        print(f"❌ 网络连接异常: {e}")
        return
    
    # 运行爬虫（默认不生成JSON）
    result_file = crawler.run(save_json=False)
    print(f"\n🎉 任务完成！结果保存在: {result_file}")

def test_single_page():
    """测试单页抓取功能"""
    print("🧪 单页测试模式")
    crawler = TiebaPostCrawler("7223841891", 1)
    soup = crawler.fetch_page(1)
    
    if soup:
        print("✅ 成功获取页面内容")
        print(f"📄 页面标题: {soup.title.string if soup.title else '无标题'}")
        
        # 尝试提取基本信息
        title = crawler.extract_title(soup)
        print(f"📋 提取的标题: {title}")
        
    else:
        print("❌ 无法获取页面内容")

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        test_single_page()
    else:
        main()