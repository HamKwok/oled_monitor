import os
import fcntl
from typing import List, Optional

# OLED显示库
try:
    from luma.core.interface.serial import i2c
    from luma.core.render import canvas
    from luma.oled.device import ssd1306
    from PIL import ImageFont, ImageDraw
    OLED_AVAILABLE = True
except ImportError:
    OLED_AVAILABLE = False
    print("OLED库未安装，将仅运行Web Dashboard模式")

class OLEDDisplay:
    def __init__(self, config_manager):
        self.config = config_manager
        self.device: Optional[ssd1306] = None
        self.serial: Optional[i2c] = None
        self.is_connected = False
        
        if OLED_AVAILABLE:
            self.fonts = {}
            self.row_positions: List[int] = []
            self.row_height = 0
            self.load_fonts()
            self.calculate_layout()
    
    def load_fonts(self):
        """加载字体"""
        if not OLED_AVAILABLE:
            return
            
        available_height = (self.config.get('height', 64) - 
                          (self.config.get('display_rows', 5) + 1) * self.config.get('row_spacing', 2))
        base_font_size = max(8, available_height // self.config.get('display_rows', 5))
        
        try:
            font_path = "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc"
            if os.path.exists(font_path):
                self.fonts = {
                    'small': ImageFont.truetype(font_path, base_font_size - 2),
                    'medium': ImageFont.truetype(font_path, base_font_size),
                    'large': ImageFont.truetype(font_path, base_font_size + 1)
                }
                print(f"字体加载成功: {font_path}, 基础大小: {base_font_size}")
            else:
                self.fonts = {
                    'small': ImageFont.load_default(),
                    'medium': ImageFont.load_default(),
                    'large': ImageFont.load_default()
                }
                print(f"字体文件不存在，使用默认字体: {font_path}")
        except Exception as e:
            self.fonts = {
                'small': ImageFont.load_default(),
                'medium': ImageFont.load_default(),
                'large': ImageFont.load_default()
            }
            print(f"字体加载失败，使用默认字体: {e}")
    
    def calculate_layout(self):
        """计算布局"""
        if not OLED_AVAILABLE:
            return
            
        self.row_height = (self.config.get('height', 64) - 
                          (self.config.get('display_rows', 5) + 1) * self.config.get('row_spacing', 2)) // self.config.get('display_rows', 5)
        self.row_positions = []
        
        for i in range(self.config.get('display_rows', 5)):
            y = self.config.get('row_spacing', 2) + i * (self.row_height + self.config.get('row_spacing', 2))
            self.row_positions.append(y)
    
    def scan_i2c_bus(self, port: int) -> List[int]:
        """扫描I2C总线"""
        devices = []
        try:
            i2c_bus = os.open(f"/dev/i2c-{port}", os.O_RDWR)
            if i2c_bus >= 0:
                for addr in range(0x03, 0x78):
                    try:
                        fcntl.ioctl(i2c_bus, 0x0703, addr)
                        devices.append(addr)
                    except OSError:
                        continue
                os.close(i2c_bus)
        except Exception as e:
            print(f"I2C总线扫描失败: {e}")
        return devices
    
    def init_oled(self) -> bool:
        """初始化OLED"""
        if not OLED_AVAILABLE:
            return False
            
        try:
            online_devices = self.scan_i2c_bus(self.config.get('i2c_port', 1))
            if self.config.get('oled_address', 60) not in online_devices:
                print(f"未在I2C-{self.config.get('i2c_port', 1)}总线上发现OLED设备")
                return False
            
            self.serial = i2c(port=self.config.get('i2c_port', 1), address=self.config.get('oled_address', 60))
            self.device = ssd1306(self.serial, rotate=0)
            print("OLED设备初始化成功")
            return True
        except Exception as e:
            print(f"OLED初始化失败: {e}")
            if self.serial:
                self.serial.cleanup()
                self.serial = None
            return False
    
    def cleanup(self):
        """清理资源（确保清屏）"""
        if not OLED_AVAILABLE:
            return
            
        try:
            if self.device:
                self.device.clear()  # 清屏
                self.device.cleanup()
                print("OLED设备资源已释放")
            if self.serial:
                self.serial.cleanup()
                self.serial = None
        except Exception as e:
            print(f"OLED设备清理失败: {e}")
        finally:
            self.device = None
            self.is_connected = False
    
    def check_connection(self) -> bool:
        """检查OLED连接"""
        if not OLED_AVAILABLE:
            return False
        online_devices = self.scan_i2c_bus(self.config.get('i2c_port', 1))
        return self.config.get('oled_address', 60) in online_devices
    
    def draw_progress_bar(self, draw: ImageDraw.ImageDraw, x: int, y: int, width: int, height: int, percent: float):
        """绘制进度条"""
        draw.rectangle([x, y, x+width, y+height], outline="white", fill="black")
        fill_width = int((width-2) * percent / 100)
        if fill_width > 0:
            draw.rectangle([x+1, y+1, x+fill_width, y+height-1], fill="white")
    
    def draw_text_line(self, draw: ImageDraw.ImageDraw, row: int, text: str, x: int = 2, font_key: str = 'medium'):
        """绘制文本行"""
        if row < len(self.row_positions):
            y = self.row_positions[row] - 1
            draw.text((x, y), text, fill="white", font=self.fonts[font_key])
    
    def draw_display(self, system_info: dict):
        """绘制显示内容"""
        if not OLED_AVAILABLE or not self.device or not self.is_connected:
            return
        
        try:
            with canvas(self.device) as draw:
                width = self.config.get('width', 128)
                height = self.config.get('height', 64)
                
                # 绘制边框
                draw.rectangle([0, 0, width-1, height-1], fill="black", outline="white")
                
                # 绘制分隔线
                for i in range(1, self.config.get('display_rows', 5)):
                    y = self.row_positions[i] - self.config.get('row_spacing', 2) // 2
                    draw.line((0, y, width, y), fill="white")
                
                # 第1行: 时间信息
                self.draw_text_line(draw, 0, f"{system_info['date_str']} {system_info['weekday_str']} {system_info['time_str']}", font_key='large')
                
                # 第2行: IP和CPU频率
                self.draw_text_line(draw, 1, f"IP:{system_info['ip']} Freq:{int(system_info['cpu_freq']):>4d}M")
                
                # 第3行: CPU使用率和温度
                cpu_text = f"CPU:{int(system_info['cpu_usage']):>2d}%"
                self.draw_text_line(draw, 2, cpu_text)
                
                # CPU进度条
                y_pos = self.row_positions[2] + self.row_height // 2 - 3
                self.draw_progress_bar(draw, 49, y_pos, 40, 6, system_info['cpu_usage'])
                self.draw_text_line(draw, 2, system_info['cpu_temp'], x=93)
                
                # 第4行: 内存使用率
                mem_text = f"MEM:{int(system_info['mem_usage']):>2d}%"
                self.draw_text_line(draw, 3, mem_text)
                
                # 内存进度条
                y_pos = self.row_positions[3] + self.row_height // 2 - 3
                self.draw_progress_bar(draw, 49, y_pos, 40, 6, system_info['mem_usage'])
                self.draw_text_line(draw, 3, f"{system_info['mem_used']:.1f}/{system_info['mem_total']:.1f}", x=93)
                
                # 第5行: 网络信息
                net_text = f"{system_info['network_name']:8}: {system_info['net_speed']}"
                self.draw_text_line(draw, 4, net_text)
                
        except Exception as e:
            print(f"屏幕绘制失败: {e}")
            self.cleanup()