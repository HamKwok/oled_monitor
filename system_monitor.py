import time
import socket
import psutil
import subprocess
from datetime import datetime
import os
from typing import Tuple, Dict

class SystemMonitor:
    def __init__(self, config_manager):
        self.config = config_manager
        self.prev_net_stats = {}
        self.current_interface = None
        self.start_time = time.time()
    
    def get_wifi_ssid(self, interface: str) -> str:
        """获取WiFi SSID"""
        try:
            result = subprocess.run(['iwgetid', '-r'], capture_output=True, text=True, timeout=2)
            if result.returncode == 0 and result.stdout.strip():
                return result.stdout.strip()[:12]
            
            result = subprocess.run(['iwconfig', interface], capture_output=True, text=True, timeout=2)
            if result.returncode == 0:
                for line in result.stdout.split('\n'):
                    if 'ESSID:' in line:
                        ssid = line.split('ESSID:')[1].split('"')[1]
                        if ssid and ssid != 'off/any':
                            return ssid[:12]
            
            return "无WiFi"
        except Exception:
            return "无WiFi"
    
    def get_network_info(self) -> Tuple[str, str, str]:
        """获取网络信息"""
        try:
            # 获取本地IP
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            
            # 查找网络接口
            interfaces = psutil.net_if_addrs()
            stats = psutil.net_if_stats()
            
            for interface, addrs in interfaces.items():
                for addr in addrs:
                    if addr.family == socket.AF_INET and addr.address == ip:
                        if interface.startswith('wlan') or interface.startswith('wlp'):
                            ssid = self.get_wifi_ssid(interface)
                            self.current_interface = interface
                            return ssid, ip[:13], interface
                        else:
                            self.current_interface = interface
                            return interface[:12], ip[:13], interface
            
            self.current_interface = None
            return "无网络", "无IP", "无接口"
        except Exception:
            self.current_interface = None
            return "无网络", "无IP", "无接口"
    
    def get_network_speed(self) -> str:
        """获取网络速度"""
        if not self.current_interface:
            return "  0K   0K"
        
        try:
            current_time = time.time()
            current_stats = psutil.net_io_counters(pernic=True).get(self.current_interface)
            
            if not current_stats:
                return "  0K   0K"
            
            # 初始化或计算速度
            if self.current_interface not in self.prev_net_stats:
                self.prev_net_stats[self.current_interface] = {
                    'bytes_sent': current_stats.bytes_sent,
                    'bytes_recv': current_stats.bytes_recv,
                    'time': current_time
                }
                return "  0K   0K"
            
            prev_stats = self.prev_net_stats[self.current_interface]
            time_diff = current_time - prev_stats['time']
            
            if time_diff <= 0:
                return "  0K   0K"
            
            # 计算速度
            bytes_sent_diff = current_stats.bytes_sent - prev_stats['bytes_sent']
            bytes_recv_diff = current_stats.bytes_recv - prev_stats['bytes_recv']
            
            upload_speed = bytes_sent_diff / time_diff / 128  # KB/s
            download_speed = bytes_recv_diff / time_diff / 128  # KB/s
            
            # 更新历史数据
            self.prev_net_stats[self.current_interface] = {
                'bytes_sent': current_stats.bytes_sent,
                'bytes_recv': current_stats.bytes_recv,
                'time': current_time
            }
            
            # 格式化显示
            def format_speed(speed):
                if speed < 1024:
                    return f"{speed:>5.1f}K"
                else:
                    return f"{speed/1024:>5.1f}M"
            
            upload_str = format_speed(upload_speed)
            download_str = format_speed(download_speed)
            
            return f"{upload_str} {download_str}"
        
        except Exception:
            return " N/A   N/A"
    
    def get_cpu_temperature(self) -> str:
        """获取CPU温度"""
        temp_paths = self.config.get('temperature_paths', [])
        
        for path in temp_paths:
            if os.path.exists(path):
                try:
                    with open(path, 'r') as f:
                        temp = float(f.read().strip()) / 1000
                        return f"{temp:.1f}°C"
                except Exception:
                    continue
        
        # 尝试vcgencmd（树莓派）
        try:
            result = subprocess.run(['vcgencmd', 'measure_temp'], capture_output=True, text=True)
            if result.returncode == 0:
                temp_str = result.stdout.split('=')[1].split("'")[0]
                return f"{float(temp_str):.1f}°C"
        except Exception:
            pass
        
        return "N/A"
    
    def collect_system_info(self) -> Dict[str, any]:
        """收集系统信息"""
        info = {}
        now = datetime.now()
        
        # 时间信息
        info['time_str'] = now.strftime("%H:%M:%S")
        info['date_str'] = now.strftime("%Y-%m-%d")
        info['weekday_str'] = now.strftime("%a")
        
        # CPU信息
        info['cpu_usage'] = psutil.cpu_percent(interval=0.1)
        try:
            cpu_freq = psutil.cpu_freq()
            info['cpu_freq'] = cpu_freq.current if cpu_freq else 0
        except Exception:
            info['cpu_freq'] = 0
        
        # 内存信息
        mem = psutil.virtual_memory()
        info['mem_usage'] = mem.percent
        info['mem_used'] = mem.used / (1024**3)  # GB
        info['mem_total'] = mem.total / (1024**3)  # GB
        
        # 温度信息
        info['cpu_temp'] = self.get_cpu_temperature()
        
        # 网络信息
        network_name, ip, interface = self.get_network_info()
        info['network_name'] = network_name
        info['ip'] = ip
        info['net_speed'] = self.get_network_speed()
        
        return info
    
    def get_uptime(self) -> str:
        """获取运行时间"""
        uptime_seconds = time.time() - self.start_time
        hours = int(uptime_seconds // 3600)
        minutes = int((uptime_seconds % 3600) // 60)
        seconds = int(uptime_seconds % 60)
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
    
    def should_wake_up(self, system_info: Dict) -> bool:
        """判断是否应该唤醒屏幕"""
        smart_wake_enabled = self.config.get('smart_wake.enabled', True)
        
        if not smart_wake_enabled:
            return True
        
        # 检查各项阈值
        cpu_usage = system_info['cpu_usage']
        cpu_freq = system_info['cpu_freq']
        mem_usage = system_info['mem_usage']
        
        # 解析网络速度
        net_speed = system_info['net_speed']
        upload_str, download_str = net_speed.split()[:2]
        
        def parse_speed(speed_str):
            if speed_str.endswith('K'):
                return float(speed_str[:-1])
            elif speed_str.endswith('M'):
                return float(speed_str[:-1]) * 1024
            else:
                return 0.0
        
        upload_speed = parse_speed(upload_str)
        download_speed = parse_speed(download_str)
        max_net_speed = max(upload_speed, download_speed)
        
        # 检查阈值
        thresholds = [
            cpu_usage > self.config.get('smart_wake.cpu_usage_threshold', 5.0),
            max_net_speed > self.config.get('smart_wake.network_speed_threshold', 100.0),
            mem_usage > self.config.get('smart_wake.memory_usage_threshold', 30.0),
            cpu_freq > self.config.get('smart_wake.cpu_freq_threshold', 1000.0)
        ]
        
        return any(thresholds)