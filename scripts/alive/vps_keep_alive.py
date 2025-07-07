#!/usr/bin/env python3
"""
VPS部署版本 - Render服务器防休眠监工程序
功能：定期向Render服务器发送请求，防止免费层服务器休眠
适用：可在任何VPS或本地环境运行
作者：Claude Code
版本：1.0
test url: "http://165.232.148.2:7860/ping"
部署后需改成: “https://dconaninfosearch.onrender.com/ping”
"""

import time
import random
import requests
import json
import os
import logging
import signal
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import threading


class RenderKeepAliveMonitor:
    """Render服务器防休眠监控器"""
    
    def __init__(self, config_file: str = "scripts/alive/keep_alive_config.json"):
        self.config_file = config_file
        self.config = self.load_config()
        self.running = False
        self.stats = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "start_time": None,
            "last_success": None,
            "last_failure": None
        }
        
        # 设置日志
        self.setup_logging()
        
        # 信号处理
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
        
        self.logger.info("🚀 Render防休眠监控器初始化完成")
    
    def load_config(self) -> Dict:
        """加载配置文件"""
        default_config = {
            "targets": [
                {
                    "name": "DConanInfoSearch",
                    "url": "http://165.232.148.2:7860/ping",
                    "enabled": True
                }
            ],
            "schedule": {
                "min_interval_minutes": 12,
                "max_interval_minutes": 14,
                "avoid_night_hours": True,
                "night_start": 2,
                "night_end": 6
            },
            "request": {
                "timeout": 30,
                "max_retries": 3,
                "retry_delay": 5,
                "user_agent": "VPS-KeepAlive-Monitor/1.0"
            },
            "logging": {
                "level": "INFO",
                "file": "logs/keep_alive.log",
                "max_size_mb": 10,
                "backup_count": 5
            },
            "notifications": {
                "enabled": False,
                "webhook_url": "",
                "alert_after_failures": 5
            }
        }
        
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    loaded_config = json.load(f)
                    # 合并配置，保持默认值
                    default_config.update(loaded_config)
                    return default_config
            except Exception as e:
                print(f"❌ 配置文件加载失败，使用默认配置: {e}")
        
        # 创建默认配置文件
        self.save_config(default_config)
        return default_config
    
    def save_config(self, config: Dict):
        """保存配置文件"""
        os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
    
    def setup_logging(self):
        """设置日志系统"""
        log_config = self.config.get("logging", {})
        log_file = log_config.get("file", "logs/keep_alive.log")
        log_level = getattr(logging, log_config.get("level", "INFO"))
        
        # 创建日志目录
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        
        # 配置日志格式
        formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # 文件处理器（带轮转）
        from logging.handlers import RotatingFileHandler
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=log_config.get("max_size_mb", 10) * 1024 * 1024,
            backupCount=log_config.get("backup_count", 5),
            encoding='utf-8'
        )
        file_handler.setFormatter(formatter)
        
        # 控制台处理器
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        
        # 配置logger
        self.logger = logging.getLogger("KeepAliveMonitor")
        self.logger.setLevel(log_level)
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
    
    def signal_handler(self, signum, frame):
        """优雅停止信号处理"""
        self.logger.info(f"📥 收到停止信号 {signum}，正在优雅关闭...")
        self.stop()
    
    def is_night_time(self) -> bool:
        """检查是否在深夜时段"""
        if not self.config["schedule"]["avoid_night_hours"]:
            return False
        
        now = datetime.now()
        night_start = self.config["schedule"]["night_start"]
        night_end = self.config["schedule"]["night_end"]
        
        return night_start <= now.hour < night_end
    
    def get_next_interval(self) -> int:
        """获取下次检查的间隔时间（秒）"""
        min_minutes = self.config["schedule"]["min_interval_minutes"]
        max_minutes = self.config["schedule"]["max_interval_minutes"]
        
        # 随机间隔，避免被识别为机器人
        interval_minutes = random.uniform(min_minutes, max_minutes)
        
        # 夜间延长间隔
        if self.is_night_time():
            interval_minutes *= 2  # 夜间间隔翻倍
            self.logger.debug(f"🌙 夜间模式，间隔延长至 {interval_minutes:.1f} 分钟")
        
        return int(interval_minutes * 60)
    
    def send_request(self, target: Dict) -> bool:
        """向目标服务器发送请求"""
        url = target["url"]
        name = target["name"]
        
        self.logger.debug(f"📡 正在ping {name}: {url}")
        
        # 请求配置
        req_config = self.config["request"]
        headers = {
            'User-Agent': req_config["user_agent"],
            'Accept': 'application/json,text/html,application/xhtml+xml',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive'
        }
        
        # 重试逻辑
        for attempt in range(1, req_config["max_retries"] + 1):
            try:
                start_time = time.time()
                
                response = requests.get(
                    url,
                    headers=headers,
                    timeout=req_config["timeout"],
                    allow_redirects=True
                )
                
                response_time = time.time() - start_time
                
                if response.status_code == 200:
                    # 检查响应内容
                    try:
                        data = response.json()
                        if data.get("status") == "alive":
                            self.logger.info(f"✅ {name} 响应正常 ({response.status_code}) - {response_time:.2f}s")
                            self.stats["successful_requests"] += 1
                            self.stats["last_success"] = datetime.now().isoformat()
                            return True
                    except json.JSONDecodeError:
                        # 如果不是JSON，检查HTML内容
                        if "alive" in response.text.lower():
                            self.logger.info(f"✅ {name} 响应正常 (HTML) - {response_time:.2f}s")
                            self.stats["successful_requests"] += 1
                            self.stats["last_success"] = datetime.now().isoformat()
                            return True
                
                self.logger.warning(f"⚠️  {name} 响应异常: {response.status_code} - {response_time:.2f}s")
                
            except requests.exceptions.Timeout:
                self.logger.warning(f"⏰ {name} 请求超时 (尝试 {attempt}/{req_config['max_retries']})")
            except requests.exceptions.ConnectionError:
                self.logger.warning(f"🔌 {name} 连接失败 (尝试 {attempt}/{req_config['max_retries']})")
            except Exception as e:
                self.logger.error(f"❌ {name} 请求异常: {e} (尝试 {attempt}/{req_config['max_retries']})")
            
            # 重试延迟
            if attempt < req_config["max_retries"]:
                delay = req_config["retry_delay"] * attempt
                self.logger.debug(f"⏳ 等待 {delay} 秒后重试...")
                time.sleep(delay)
        
        # 所有重试都失败
        self.logger.error(f"💔 {name} 所有重试失败")
        self.stats["failed_requests"] += 1
        self.stats["last_failure"] = datetime.now().isoformat()
        return False
    
    def send_notification(self, message: str):
        """发送通知（如果启用）"""
        if not self.config["notifications"]["enabled"]:
            return
        
        webhook_url = self.config["notifications"]["webhook_url"]
        if not webhook_url:
            return
        
        try:
            payload = {
                "text": f"🚨 Render监控告警\\n{message}",
                "timestamp": datetime.now().isoformat()
            }
            
            response = requests.post(
                webhook_url,
                json=payload,
                timeout=10
            )
            
            if response.status_code == 200:
                self.logger.info("📢 通知发送成功")
            else:
                self.logger.warning(f"📢 通知发送失败: {response.status_code}")
                
        except Exception as e:
            self.logger.error(f"📢 通知发送异常: {e}")
    
    def check_alert_condition(self):
        """检查是否需要发送告警"""
        alert_threshold = self.config["notifications"]["alert_after_failures"]
        
        if self.stats["failed_requests"] >= alert_threshold:
            if self.stats["failed_requests"] % alert_threshold == 0:  # 避免重复告警
                message = f"连续失败 {self.stats['failed_requests']} 次，请检查服务状态"
                self.send_notification(message)
    
    def print_stats(self):
        """打印统计信息"""
        uptime = ""
        if self.stats["start_time"]:
            delta = datetime.now() - self.stats["start_time"]
            uptime = f"{delta.days}天 {delta.seconds//3600}小时 {(delta.seconds%3600)//60}分钟"
        
        success_rate = 0
        if self.stats["total_requests"] > 0:
            success_rate = (self.stats["successful_requests"] / self.stats["total_requests"]) * 100
        
        print(f"""
📊 运行统计:
   运行时间: {uptime}
   总请求数: {self.stats['total_requests']}
   成功次数: {self.stats['successful_requests']}
   失败次数: {self.stats['failed_requests']}
   成功率: {success_rate:.1f}%
   最后成功: {self.stats['last_success'] or '无'}
   最后失败: {self.stats['last_failure'] or '无'}
""")
    
    def run_once(self):
        """执行一次监控检查"""
        enabled_targets = [t for t in self.config["targets"] if t.get("enabled", True)]
        
        if not enabled_targets:
            self.logger.warning("⚠️ 没有启用的监控目标")
            return
        
        self.logger.info(f"🔍 开始检查 {len(enabled_targets)} 个目标...")
        
        success_count = 0
        for target in enabled_targets:
            self.stats["total_requests"] += 1
            
            if self.send_request(target):
                success_count += 1
            else:
                self.check_alert_condition()
            
            # 多目标间隔
            if len(enabled_targets) > 1:
                time.sleep(random.uniform(2, 5))
        
        self.logger.info(f"✅ 检查完成: {success_count}/{len(enabled_targets)} 成功")
    
    def run(self, daemon: bool = False):
        """运行监控程序"""
        self.running = True
        self.stats["start_time"] = datetime.now()
        
        if daemon:
            self.logger.info("👹 后台模式启动")
        else:
            self.logger.info("🖥️  交互模式启动")
        
        self.logger.info(f"⏰ 监控间隔: {self.config['schedule']['min_interval_minutes']}-{self.config['schedule']['max_interval_minutes']} 分钟")
        
        try:
            while self.running:
                # 执行监控检查
                self.run_once()
                
                if not self.running:
                    break
                
                # 计算下次检查时间
                next_interval = self.get_next_interval()
                next_check = datetime.now() + timedelta(seconds=next_interval)
                
                self.logger.info(f"⏳ 下次检查: {next_check.strftime('%H:%M:%S')} (间隔 {next_interval//60} 分钟)")
                
                # 可中断的睡眠
                for _ in range(next_interval):
                    if not self.running:
                        break
                    time.sleep(1)
                
        except KeyboardInterrupt:
            self.logger.info("👤 用户中断")
        except Exception as e:
            self.logger.error(f"💥 监控程序异常: {e}")
        finally:
            self.stop()
    
    def stop(self):
        """停止监控"""
        if self.running:
            self.running = False
            self.logger.info("🛑 监控程序已停止")
            self.print_stats()


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Render服务器防休眠监控程序")
    parser.add_argument("-c", "--config", default="scripts/alive/keep_alive_config.json", 
                       help="配置文件路径")
    parser.add_argument("-d", "--daemon", action="store_true", 
                       help="后台模式运行")
    parser.add_argument("--test", action="store_true", 
                       help="测试模式：只执行一次检查")
    parser.add_argument("--stats", action="store_true", 
                       help="显示统计信息并退出")
    
    args = parser.parse_args()
    
    # 创建监控实例
    monitor = RenderKeepAliveMonitor(args.config)
    
    if args.stats:
        monitor.print_stats()
        return
    
    if args.test:
        print("🧪 测试模式：执行单次检查")
        monitor.run_once()
        monitor.print_stats()
        return
    
    # 正常运行
    try:
        monitor.run(daemon=args.daemon)
    except Exception as e:
        print(f"❌ 程序启动失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()