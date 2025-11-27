function updateDashboard(data) {
    // 系统概览
    document.getElementById('current-time').textContent = data.time_str;
    document.getElementById('uptime').textContent = data.uptime;
    
    // OLED状态
    const oledStatus = document.getElementById('oled-status');
    const oledText = document.getElementById('oled-text');
    if (data.oled_connected) {
        oledStatus.className = 'status-indicator status-online';
        oledText.textContent = '在线';
    } else {
        oledStatus.className = 'status-indicator status-offline';
        oledText.textContent = '离线';
    }

    // CPU信息
    document.getElementById('cpu-usage').textContent = data.cpu_usage.toFixed(1) + '%';
    document.getElementById('cpu-freq').textContent = data.cpu_freq.toFixed(0) + ' MHz';
    document.getElementById('cpu-temp').textContent = data.cpu_temp;
    document.getElementById('cpu-progress').style.width = data.cpu_usage + '%';

    // 内存信息
    document.getElementById('mem-usage').textContent = data.mem_usage.toFixed(1) + '%';
    document.getElementById('mem-usage-detail').textContent = 
        data.mem_used.toFixed(1) + ' GB / ' + data.mem_total.toFixed(1) + ' GB';
    document.getElementById('mem-progress').style.width = data.mem_usage + '%';

    // 网络信息
    document.getElementById('ip-address').textContent = data.ip;
    document.getElementById('network-name').textContent = data.network_name;
    
    const speeds = data.net_speed.split(' ');
    if (speeds.length >= 2) {
        document.getElementById('upload-speed').textContent = speeds[0].trim();
        document.getElementById('download-speed').textContent = speeds[1].trim();
    }

    // 更新时间
    document.getElementById('last-update-time').textContent = new Date().toLocaleString();
}

function fetchData() {
    fetch('/api/status')
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(data => updateDashboard(data))
        .catch(error => {
            console.error('获取数据失败:', error);
            // 显示错误状态
            document.getElementById('oled-text').textContent = '连接失败';
            document.getElementById('oled-status').className = 'status-indicator status-offline';
        });
}

// 初始加载
fetchData();

// 每3秒更新一次
let updateInterval = setInterval(fetchData, 3000);

// 页面可见性变化时调整更新频率
document.addEventListener('visibilitychange', function() {
    if (document.hidden) {
        clearInterval(updateInterval);
    } else {
        fetchData();
        updateInterval = setInterval(fetchData, 3000);
    }
});