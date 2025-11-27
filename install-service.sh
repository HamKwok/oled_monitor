#!/bin/bash

# OLED Monitor Systemd Service Installer
# 需要root权限运行

set -e

SERVICE_NAME="oled-monitor"
SERVICE_FILE="/etc/systemd/system/${SERVICE_NAME}.service"
INSTALL_DIR="/opt/oled_monitor"
CONFIG_DIR="/etc/oled_monitor"
USER="root"
GROUP="root"

echo "=== OLED Monitor Service Installer (Root Version) ==="

# 检查root权限
if [ "$EUID" -ne 0 ]; then
    echo "请使用root权限运行此脚本: sudo $0"
    exit 1
fi

# 检查Python3
if ! command -v python3 &> /dev/null; then
    echo "安装Python3..."
    apt update
    apt install -y python3
fi

# 创建安装目录
echo "创建安装目录..."
mkdir -p $INSTALL_DIR
mkdir -p $CONFIG_DIR

# 检查当前目录的文件
if [ ! -f "oled_monitor.py" ]; then
    echo "错误: 请在包含OLED监控文件的目录中运行此脚本"
    exit 1
fi

# 复制文件到安装目录
echo "复制程序文件..."
cp -f oled_monitor.py config_manager.py system_monitor.py oled_display.py web_server.py $INSTALL_DIR/
cp -f requirements-system.txt $INSTALL_DIR/

# 复制配置文件
if [ -f "config.json" ]; then
    cp -f config.json $CONFIG_DIR/
else
    echo "警告: 未找到config.json，将使用默认配置"
fi

# 复制web文件
if [ -d "web" ]; then
    cp -rf web $INSTALL_DIR/
else
    echo "警告: 未找到web目录"
fi

# 安装系统依赖包
echo "安装系统依赖包..."
apt update

# 安装Python系统包
echo "安装Python系统包..."
apt install -y \
    python3-psutil \
    python3-flask \
    python3-pil \
    python3-smbus \
    i2c-tools

# 检查是否需要安装pip
if ! command -v pip3 &> /dev/null; then
    echo "安装pip3..."
    apt install -y python3-pip
fi

# 创建服务文件
echo "创建系统服务文件..."
cat > "$SERVICE_FILE" << EOF
[Unit]
Description=OLED System Monitor with Web Dashboard
After=network.target multi-user.target
Wants=network.target
Documentation=https://github.com/your-repo/oled-monitor

[Service]
Type=simple
User=$USER
Group=$GROUP
WorkingDirectory=$INSTALL_DIR
ExecStart=/usr/bin/python3 $INSTALL_DIR/oled_monitor.py
ExecReload=/bin/kill -HUP \$MAINPID
ExecStop=/bin/kill -INT \$MAINPID
Restart=always
RestartSec=5
TimeoutStopSec=30

# 环境配置
Environment=PYTHONUNBUFFERED=1
Environment=PYTHONPATH=$INSTALL_DIR

# 安全设置
NoNewPrivileges=yes
PrivateTmp=yes
ProtectSystem=strict
ReadWritePaths=$INSTALL_DIR /tmp

# 硬件访问权限
DeviceAllow=/dev/i2c-1 rw
DeviceAllow=/dev/i2c-3 rw
DeviceAllow=/dev/mem rw
DeviceAllow=char-i2c-device rw

# 资源限制
MemoryLimit=100M
CPUQuota=50%

# 日志配置
StandardOutput=journal
StandardError=journal
SyslogIdentifier=oled-monitor

[Install]
WantedBy=multi-user.target
EOF

echo "服务文件已创建: $SERVICE_FILE"

# 设置文件权限
chmod 644 "$SERVICE_FILE"
chown -R $USER:$GROUP $INSTALL_DIR
chown -R $USER:$GROUP $CONFIG_DIR

# 设置Python脚本可执行
chmod +x $INSTALL_DIR/oled_monitor.py

# 创建符号链接（如果配置文件在/etc目录）
if [ -f "$CONFIG_DIR/config.json" ]; then
    ln -sf $CONFIG_DIR/config.json $INSTALL_DIR/config.json
fi

# 重新加载systemd
echo "重新加载systemd配置..."
systemctl daemon-reload

# 启用服务
echo "启用服务..."
systemctl enable $SERVICE_NAME

# 启用I2C接口（如果需要）
if [ -f "/boot/firmware/config.txt" ]; then
    # OrangePi等使用config.txt的系统
    if ! grep -q "dtparam=i2c_arm=on" /boot/firmware/config.txt; then
        echo "启用I2C接口..."
        echo "dtparam=i2c_arm=on" >> /boot/firmware/config.txt
    fi
elif [ -f "/boot/config.txt" ]; then
    # 树莓派等使用config.txt的系统
    if ! grep -q "dtparam=i2c_arm=on" /boot/config.txt; then
        echo "启用I2C接口..."
        echo "dtparam=i2c_arm=on" >> /boot/config.txt
    fi
fi

echo ""
echo "=== 安装完成 ==="
echo "服务名称: $SERVICE_NAME"
echo "安装目录: $INSTALL_DIR"
echo "配置目录: $CONFIG_DIR"
echo "运行用户: $USER"
echo ""
echo "常用命令:"
echo "启动服务: systemctl start $SERVICE_NAME"
echo "停止服务: systemctl stop $SERVICE_NAME"
echo "重启服务: systemctl restart $SERVICE_NAME"
echo "查看状态: systemctl status $SERVICE_NAME"
echo "查看日志: journalctl -u $SERVICE_NAME -f"
echo ""
echo "如果I2C接口被启用，可能需要重启系统"
echo "服务将在系统启动时自动运行"