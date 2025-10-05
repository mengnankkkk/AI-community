#!/bin/bash

# AI虚拟播客工作室启动脚本

echo "==================================="
echo "AI虚拟播客工作室 启动脚本"
echo "==================================="

# 检查Python环境
echo "检查Python环境..."
if ! command -v python &> /dev/null; then
    echo "错误: 未找到Python，请先安装Python 3.11+"
    exit 1
fi

python_version=$(python --version 2>&1 | cut -d' ' -f2)
echo "Python版本: $python_version"

# 检查虚拟环境
if [[ "$VIRTUAL_ENV" != "" ]]; then
    echo "当前虚拟环境: $VIRTUAL_ENV"
else
    echo "提示: 建议使用虚拟环境运行项目"
fi

# 安装依赖
echo "安装/更新依赖包..."
pip install -r requirements.txt

# 检查环境变量文件
if [ ! -f ".env" ]; then
    echo "创建环境配置文件..."
    cp .env.example .env
    echo "⚠️  请编辑 .env 文件，添加您的 OpenAI API 密钥"
    echo "   文件位置: $(pwd)/.env"
fi

# 创建必要目录
echo "创建输出目录..."
mkdir -p audio_output
mkdir -p logs

# 启动服务
echo "启动服务器..."
echo "前端地址: http://localhost:8000/static/index.html"
echo "API文档: http://localhost:8000/docs"
echo "按 Ctrl+C 停止服务"
echo "==================================="

python run_server.py