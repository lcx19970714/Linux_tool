#!/bin/bash

# Linux工具启动脚本

# 获取脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# 进入项目目录
cd "$SCRIPT_DIR"

# 激活虚拟环境
if [ -f ".venv/bin/activate" ]; then
    source .venv/bin/activate
else
    echo "错误：虚拟环境不存在"
    echo "请先运行: python3 -m venv .venv"
    exit 1
fi

# 检查依赖
echo "检查依赖..."
pip install -q -r requirements.txt 2>/dev/null

# 启动应用
echo "启动Linux工具..."
python main.py

# 退出虚拟环境
deactivate

