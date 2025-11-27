#!/usr/bin/env python3
import time
import signal
import sys
from datetime import datetime
from pathlib import Path

from config_manager import ConfigManager
from system_monitor import SystemMonitor
from oled_display import OLEDDisplay
from web_server import WebServer

class OLEDMonitor:
    def __init__(self, config_file="config.json"):
        self.config = ConfigManager(config_file)
        self.system_monitor = SystemMonitor(self.config)
        self.oled_display = OLEDDisplay(self.config)
        self.web_server = WebServer(self.config, self.system_monitor, self.oled_display)
        self.running = False
        self.sleep_mode = False
        
        # 注册信号处理
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
    
    def signal_handler(self, signum, frame):
        """信号处理函数"""
        print(f"\n收到信号 {signum}，程序退出中...")
        self.running = False
    
    def is_display_time(self) -> bool:
        """检查是否在显示时间段内"""
        display_enabled = self.config.get('display_settings.enabled', True)
        if not display_enabled:
            return True
        
        now = datetime.now()
        current_hour = now.hour
        start_hour = self.config.get('display_settings.start_hour', 10)
        end_hour = self.config.get('display_settings.end_hour', 25)
        
        # 处理跨天情况
        if end_hour >= 24:
            return (current_hour >= start_hour) or (current_hour < end_hour - 24)
        else:
            return start_hour <= current_hour < end_hour
    
    def is_sleep_time(self) -> bool:
        """检查是否在睡眠时间段内"""
        sleep_enabled = self.config.get('sleep_settings.enabled', True)
        if not sleep_enabled:
            return False
        
        now = datetime.now()
        current_hour = now.hour
        start_hour = self.config.get('sleep_settings.start_hour', 23)
        end_hour = self.config.get('sleep_settings.end_hour', 6)
        
        # 处理跨天情况
        if start_hour > end_hour:
            return current_hour >= start_hour or current_hour < end_hour
        else:
            return start_hour <= current_hour < end_hour
    
    def calculate_wait_time(self) -> int:
        """计算等待时间"""
        now = datetime.now()
        current_hour = now.hour
        
        # 计算到下一个显示时间段开始的时间
        start_hour = self.config.get('display_settings.start_hour', 10)
        
        if current_hour < start_hour:
            wait_hours = start_hour - current_hour - 1
            wait_minutes = 60 - now.minute
        else:
            wait_hours = 24 - current_hour + start_hour - 1
            wait_minutes = 60 - now.minute
        
        wait_seconds = wait_hours * 3600 + wait_minutes * 60 - now.second
        return max(60, min(wait_seconds, 3600))
    
    def handle_oled_connection(self):
        """处理OLED连接状态"""
        if not self.oled_display:
            return
        
        current_connected = self.oled_display.check_connection()
        
        # 设备连接状态变化处理
        if current_connected and not self.oled_display.is_connected:
            if self.oled_display.init_oled():
                self.oled_display.is_connected = True
                print("OLED设备已连接")
        elif not current_connected and self.oled_display.is_connected:
            print("OLED设备已断开")
            self.oled_display.cleanup()
    
    def run_display_mode(self):
        """运行显示模式"""
        system_info = self.system_monitor.collect_system_info()
        
        # 智能唤醒检查
        if self.sleep_mode:
            if self.system_monitor.should_wake_up(system_info):
                print("系统活动，唤醒屏幕")
                self.sleep_mode = False
            else:
                # 保持在睡眠模式
                time.sleep(self.config.get('smart_wake.check_interval', 10))
                return
        
        # 处理OLED连接
        self.handle_oled_connection()
        
        # 绘制显示内容
        if self.oled_display and self.oled_display.is_connected and self.oled_display.device:
            self.oled_display.draw_display(system_info)
        
        time.sleep(self.config.get('scan_interval', 1.0))
    
    def run_sleep_mode(self):
        """运行睡眠模式"""
        if not self.sleep_mode:
            print("进入睡眠模式")
            self.sleep_mode = True
            
            # 关闭OLED显示
            if self.oled_display:
                self.oled_display.cleanup()
        
        # 检查是否应该唤醒
        system_info = self.system_monitor.collect_system_info()
        if self.system_monitor.should_wake_up(system_info):
            print("系统活动，唤醒屏幕")
            self.sleep_mode = False
            return
        
        # 睡眠模式下减少系统负载
        wait_seconds = self.config.get('smart_wake.check_interval', 10)
        print(f"睡眠中，{wait_seconds}秒后重新检查...")
        
        # 分段等待，便于响应退出信号
        for i in range(wait_seconds):
            if not self.running:
                break
            time.sleep(1)
    
    def run(self):
        """主运行循环"""
        self.running = True
        print("OLED监控系统启动，按Ctrl+C退出")
        
        # 显示配置信息
        print(f"显示时间段: {self.config.get('display_settings.start_hour', 10):02d}:00 ~ {self.config.get('display_settings.end_hour', 25):02d}:00")
        if self.config.get('sleep_settings.enabled', True):
            print(f"睡眠时间段: {self.config.get('sleep_settings.start_hour', 23):02d}:00 ~ {self.config.get('sleep_settings.end_hour', 6):02d}:00")
        if self.config.get('smart_wake.enabled', True):
            print("智能唤醒已启用")
        
        # 启动Web服务器
        self.web_server.start()
        
        try:
            while self.running:
                # 检查睡眠时间段
                if self.is_sleep_time():
                    self.run_sleep_mode()
                    continue
                
                # 检查显示时间段
                if self.is_display_time():
                    self.run_display_mode()
                else:
                    # 不在显示时间段，进入等待
                    if self.oled_display and self.oled_display.is_connected and self.oled_display.device:
                        print("不在显示时间段，关闭屏幕")
                        self.oled_display.cleanup()
                    
                    wait_seconds = self.calculate_wait_time()
                    print(f"不在显示时间段，等待 {wait_seconds//60} 分钟")
                    
                    # 分段等待，便于响应退出信号
                    for i in range(wait_seconds):
                        if not self.running:
                            break
                        time.sleep(1)
        
        except KeyboardInterrupt:
            print("\n程序被用户中断")
        except Exception as e:
            print(f"程序运行错误: {e}")
        finally:
            self.shutdown()
    
    def shutdown(self):
        """关闭程序"""
        print("程序关闭中...")
        self.running = False
        
        # 确保清理OLED资源
        if self.oled_display:
            self.oled_display.cleanup()
        
        self.web_server.stop()
        print("程序已退出")

def main():
    # 创建web目录
    Path("web").mkdir(exist_ok=True)
    
    # 创建监控实例并运行
    monitor = OLEDMonitor()
    monitor.run()

if __name__ == "__main__":
    main()