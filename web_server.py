import threading
from typing import Optional

# Web服务器
try:
    from flask import Flask, jsonify, send_from_directory, request
    FLASK_AVAILABLE = True
except ImportError:
    FLASK_AVAILABLE = False
    print("Flask未安装，无法启动Web Dashboard")

class WebServer:
    def __init__(self, config_manager, system_monitor, oled_display):
        self.config = config_manager
        self.system_monitor = system_monitor
        self.oled_display = oled_display
        self.app: Optional[Flask] = None
        self.thread: Optional[threading.Thread] = None
        self.running = False
        
        if FLASK_AVAILABLE and self.config.get('web_enabled', True):
            self.setup_flask()
    
    def setup_flask(self):
        """设置Flask应用"""
        self.app = Flask(__name__, static_folder='web', static_url_path='/static')
        
        @self.app.route('/')
        def index():
            return send_from_directory('web', 'index.html')
        
        @self.app.route('/settings')
        def settings():
            return send_from_directory('web', 'settings.html')
        
        @self.app.route('/api/status')
        def api_status():
            system_info = self.system_monitor.collect_system_info()
            response = {
                'time_str': system_info['time_str'],
                'uptime': self.system_monitor.get_uptime(),
                'oled_connected': self.oled_display.is_connected if self.oled_display else False,
                'cpu_usage': system_info['cpu_usage'],
                'cpu_freq': system_info['cpu_freq'],
                'cpu_temp': system_info['cpu_temp'],
                'mem_usage': system_info['mem_usage'],
                'mem_used': system_info['mem_used'],
                'mem_total': system_info['mem_total'],
                'ip': system_info['ip'],
                'network_name': system_info['network_name'],
                'net_speed': system_info['net_speed']
            }
            return jsonify(response)
        
        @self.app.route('/api/config', methods=['GET', 'POST'])
        def api_config():
            if request.method == 'GET':
                # 返回当前配置
                return jsonify(self.config.config)
            else:
                # 更新配置
                try:
                    new_config = request.get_json()
                    if self.config.update_config(new_config):
                        return jsonify({'status': 'success'})
                    else:
                        return jsonify({'status': 'error', 'message': '配置保存失败'}), 500
                except Exception as e:
                    return jsonify({'status': 'error', 'message': str(e)}), 500
    
    def start(self):
        """启动Web服务器"""
        if self.app and self.config.get('web_enabled', True) and not self.running:
            self.running = True
            self.thread = threading.Thread(target=self.run_server, daemon=True)
            self.thread.start()
            print(f"Web服务器启动在 http://0.0.0.0:{self.config.get('web_port', 8080)}")
    
    def run_server(self):
        """运行Web服务器"""
        if self.app:
            self.app.run(
                host='0.0.0.0', 
                port=self.config.get('web_port', 8080), 
                debug=False, 
                use_reloader=False
            )
    
    def stop(self):
        """停止Web服务器"""
        self.running = False