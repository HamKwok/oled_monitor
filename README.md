# 🖥️ OLED System Monitor

[![Python](https://img.shields.io/badge/Python-3.6%2B-blue.svg)](https://www.python.org/)
[![Platform](https://img.shields.io/badge/Platform-Raspberry%20Pi%2FOrangePi-orange.svg)](https://www.raspberrypi.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

一个功能强大的系统监控工具，专为树莓派和OrangePi等嵌入式设备设计。通过SSD1306 OLED显示屏实时显示系统状态，并提供美观的Web Dashboard远程监控界面。


## ✨ 特性

### 🖥️ OLED 显示
- 实时显示CPU使用率、温度、频率
- 内存使用情况和网络状态监控
- 进度条可视化系统负载
- 自动屏幕休眠和智能唤醒

### 🌐 Web Dashboard
- 响应式Web界面，支持移动设备
- 实时数据更新，无需刷新页面
- 美观的卡片式设计，动画效果
- 完整的系统设置页面

### ⚡ 智能功能
- **智能唤醒**: 根据系统负载自动开启显示
- **时间段控制**: 可配置显示和休眠时间段
- **热插拔支持**: OLED设备热插拔自动检测
- **低功耗模式**: 非活动时段减少系统负载

### 🔧 系统集成
- Systemd服务支持，开机自启
- 完整的日志记录和故障恢复
- 资源使用限制，避免系统过载
- 安全的权限管理

## 🛠️ 硬件要求

### 必需硬件
- 树莓派 (2/3/4/Zero) 或 OrangePi
- SSD1306 OLED显示屏 (128x64, I2C接口)
- I2C连接线

## 📦 安装

### 快速安装 (一键脚本)
```bash
# 下载安装脚本
git clone https://github.com/HamKwok/oled-monitor

# 安装服务 (需要root权限)
sudo ./install-service.sh