#!/bin/bash

echo "=== OLED Monitor 环境检查 ==="
echo ""

# 检查Python3
echo "1. 检查Python3..."
if command -v python3 &> /dev/null; then
    python3_version=$(python3 --version)
    echo "   ✓ $python3_version"
else
    echo "   ✗ 未安装Python3"
    echo "   请运行: sudo apt install python3"
    exit 1
fi

# 检查pip3
echo "2. 检查pip3..."
if command -v pip3 &> /dev/null; then
    pip3_version=$(pip3 --version | cut -d' ' -f2)
    echo "   ✓ pip $pip3_version"
else
    echo "   ✗ 未安装pip3"
    echo "   请运行: sudo apt install python3-pip"
    exit 1
fi

# 检查依赖包
echo "3. 检查Python依赖包..."
required_packages=("psutil" "Flask" "luma.oled" "Pillow")

for package in "${required_packages[@]}"; do
    if python3 -c "import ${package%%.*}" 2>/dev/null; then
        echo "   ✓ $package"
    else
        echo "   ✗ $package 未安装"
        echo "   请运行: pip3 install $package"
    fi
done

# 检查I2C设备
echo "4. 检查I2C设备..."
if [ -e "/dev/i2c-1" ]; then
    echo "   ✓ I2C设备 /dev/i2c-1 存在"
    
    # 检查I2C工具
    if command -v i2cdetect &> /dev/null; then
        echo "   ✓ i2c-tools 已安装"
    else
        echo "   ! i2c-tools 未安装"
        echo "   请运行: sudo apt install i2c-tools"
    fi
else
    echo "   ✗ I2C设备 /dev/i2c-1 不存在"
    echo "   请启用I2C接口: sudo raspi-config"
fi

# 检查用户权限
echo "5. 检查用户权限..."
current_user=$(whoami)
if groups $current_user | grep -q "i2c"; then
    echo "   ✓ 用户 $current_user 在 i2c 组中"
else
    echo "   ! 用户 $current_user 不在 i2c 组中"
    echo "   请运行: sudo usermod -a -G i2c $current_user"
    echo "   然后重新登录"
fi

# 检查安装目录
echo "6. 检查安装目录..."
install_dir="/home/pi/oled_monitor"
if [ -d "$install_dir" ]; then
    echo "   ✓ 安装目录存在: $install_dir"
    
    # 检查必要文件
    required_files=("oled_monitor.py" "config.json" "requirements.txt")
    for file in "${required_files[@]}"; do
        if [ -f "$install_dir/$file" ]; then
            echo "   ✓ $file 存在"
        else
            echo "   ✗ $file 不存在"
        fi
    done
else
    echo "   ✗ 安装目录不存在: $install_dir"
fi

# 检查服务状态
echo "7. 检查服务状态..."
if systemctl is-active oled-monitor &>/dev/null; then
    echo "   ✓ oled-monitor 服务正在运行"
elif systemctl is-enabled oled-monitor &>/dev/null; then
    echo "   ○ oled-monitor 服务已启用但未运行"
else
    echo "   ○ oled-monitor 服务未安装"
fi

echo ""
echo "=== 环境检查完成 ==="