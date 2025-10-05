@echo off
chcp 65001 >nul
title AI虚拟播客工作室

echo ===================================
echo AI虚拟播客工作室 启动脚本
echo ===================================

REM 检查Python环境
echo 检查Python环境...
python --version >nul 2>&1
if errorlevel 1 (
    echo 错误: 未找到Python，请先安装Python 3.11+
    pause
    exit /b 1
)

for /f "tokens=2" %%i in ('python --version 2^>^&1') do set python_version=%%i
echo Python版本: %python_version%

REM 激活虚拟环境
echo 激活虚拟环境...
call .venv\Scripts\activate.bat
if errorlevel 1 (
    echo 错误: 虚拟环境激活失败
    pause
    exit /b 1
)

REM 检查环境变量文件
if not exist ".env" (
    echo 创建环境配置文件...
    copy config\.env.example .env >nul
    echo ⚠️  请编辑 .env 文件，添加您的 OpenAI API 密钥
    echo    文件位置: %cd%\.env
    echo.
)

REM 创建必要目录
echo 检查输出目录...
if not exist "data\output\audio" mkdir "data\output\audio"
if not exist "data\output\logs" mkdir "data\output\logs"

REM 启动服务
echo 启动服务器...
echo 前端地址: http://localhost:8000/static/index.html
echo API文档: http://localhost:8000/docs
echo 按 Ctrl+C 停止服务
echo ===================================
echo.

python run_server.py

pause