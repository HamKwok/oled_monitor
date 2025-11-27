import json
import os
from typing import Dict, Any

class ConfigManager:
    def __init__(self, config_file="config.json"):
        self.config_file = config_file
        self.default_config = self._get_default_config()
        self.config = self.default_config.copy()
        self.load_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        return {
            "i2c_port": 1,
            "oled_address": 60,
            "scan_interval": 1.0,
            "reconnect_interval": 2.0,
            "width": 128,
            "height": 64,
            "display_rows": 5,
            "row_spacing": 2,
            "web_port": 8080,
            "web_enabled": True,
            
            "display_settings": {
                "enabled": True,
                "start_hour": 10,
                "end_hour": 25
            },
            
            "smart_wake": {
                "enabled": True,
                "cpu_usage_threshold": 5.0,
                "network_speed_threshold": 100.0,
                "memory_usage_threshold": 30.0,
                "cpu_freq_threshold": 1000.0,
                "check_interval": 10
            },
            
            "sleep_settings": {
                "enabled": True,
                "start_hour": 23,
                "end_hour": 6
            },
            
            "temperature_paths": [
                "/sys/class/thermal/thermal_zone0/temp",
                "/sys/class/hwmon/hwmon0/temp1_input",
                "/sys/class/hwmon/hwmon1/temp1_input"
            ]
        }
    
    def load_config(self) -> bool:
        """从文件加载配置"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    loaded_config = json.load(f)
                    self._deep_update(self.config, loaded_config)
                print("配置加载成功")
                return True
            else:
                print("配置文件不存在，使用默认配置")
                self.save_config()  # 创建默认配置文件
                return True
        except Exception as e:
            print(f"配置加载错误: {e}，使用默认配置")
            return False
    
    def save_config(self) -> bool:
        """保存配置到文件"""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=4, ensure_ascii=False)
            print("配置保存成功")
            return True
        except Exception as e:
            print(f"配置保存错误: {e}")
            return False
    
    def update_config(self, new_config: Dict[str, Any]) -> bool:
        """更新配置"""
        try:
            self._deep_update(self.config, new_config)
            return self.save_config()
        except Exception as e:
            print(f"配置更新错误: {e}")
            return False
    
    def _deep_update(self, original: Dict, update: Dict):
        """深度更新字典"""
        for key, value in update.items():
            if isinstance(value, dict) and key in original and isinstance(original[key], dict):
                self._deep_update(original[key], value)
            else:
                original[key] = value
    
    def get(self, key: str, default=None):
        """获取配置值"""
        keys = key.split('.')
        value = self.config
        try:
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default
    
    def set(self, key: str, value):
        """设置配置值"""
        keys = key.split('.')
        config = self.config
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        config[keys[-1]] = value