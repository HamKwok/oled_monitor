#!/bin/bash

SERVICE_NAME="oled-monitor"

show_usage() {
    echo "OLED Monitor 服务管理脚本"
    echo "用法: $0 {start|stop|restart|status|enable|disable|logs|install|uninstall}"
    echo ""
    echo "命令说明:"
    echo "  start     - 启动服务"
    echo "  stop      - 停止服务"
    echo "  restart   - 重启服务"
    echo "  status    - 查看服务状态"
    echo "  enable    - 启用开机自启"
    echo "  disable   - 禁用开机自启"
    echo "  logs      - 查看服务日志"
    echo "  install   - 安装服务"
    echo "  uninstall - 卸载服务"
}

check_root() {
    if [ "$EUID" -ne 0 ]; then
        echo "此操作需要root权限，请使用: sudo $0 $1"
        exit 1
    fi
}

case "$1" in
    start)
        check_root "start"
        echo "启动 $SERVICE_NAME 服务..."
        systemctl start $SERVICE_NAME
        systemctl status $SERVICE_NAME
        ;;
    stop)
        check_root "stop"
        echo "停止 $SERVICE_NAME 服务..."
        systemctl stop $SERVICE_NAME
        systemctl status $SERVICE_NAME
        ;;
    restart)
        check_root "restart"
        echo "重启 $SERVICE_NAME 服务..."
        systemctl restart $SERVICE_NAME
        systemctl status $SERVICE_NAME
        ;;
    status)
        systemctl status $SERVICE_NAME
        ;;
    enable)
        check_root "enable"
        echo "启用 $SERVICE_NAME 开机自启..."
        systemctl enable $SERVICE_NAME
        ;;
    disable)
        check_root "disable"
        echo "禁用 $SERVICE_NAME 开机自启..."
        systemctl disable $SERVICE_NAME
        ;;
    logs)
        echo "显示 $SERVICE_NAME 服务日志..."
        journalctl -u $SERVICE_NAME -f
        ;;
    install)
        # 运行安装脚本
        if [ -f "install-service.sh" ]; then
            ./install-service.sh
        else
            echo "错误: 未找到 install-service.sh"
            exit 1
        fi
        ;;
    uninstall)
        check_root "uninstall"
        echo "卸载 $SERVICE_NAME 服务..."
        
        # 停止服务
        systemctl stop $SERVICE_NAME 2>/dev/null || true
        
        # 禁用服务
        systemctl disable $SERVICE_NAME 2>/dev/null || true
        
        # 删除服务文件
        if [ -f "/etc/systemd/system/$SERVICE_NAME.service" ]; then
            rm -f "/etc/systemd/system/$SERVICE_NAME.service"
            echo "服务文件已删除"
        fi
        
        # 重新加载systemd
        systemctl daemon-reload
        systemctl reset-failed
        
        echo "服务卸载完成"
        ;;
    *)
        show_usage
        exit 1
        ;;
esac