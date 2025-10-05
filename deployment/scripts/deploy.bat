@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion
title AI虚拟播客工作室 - Docker部署

echo 🎬 AI虚拟播客工作室 - Docker部署启动
echo ========================================

REM 颜色设置
set "RED=[91m"
set "GREEN=[92m"
set "YELLOW=[93m"
set "BLUE=[94m"
set "NC=[0m"

REM 获取参数
set "action=%~1"
if "%action%"=="" set "action=deploy"

goto %action% 2>nul || goto usage

:deploy
call :check_dependencies
call :create_directories
call :check_env_file
call :deploy_services
call :wait_for_services
call :show_status
goto :end

:stop
echo %YELLOW%停止所有服务...%NC%
docker-compose down
echo %GREEN%✅ 服务已停止%NC%
goto :end

:restart
echo %YELLOW%重启所有服务...%NC%
docker-compose restart
call :wait_for_services
call :show_status
goto :end

:logs
docker-compose logs -f
goto :end

:status
docker-compose ps
goto :end

:clean
echo %YELLOW%清理Docker资源...%NC%
docker-compose down --volumes --remove-orphans
docker system prune -f
echo %GREEN%✅ 清理完成%NC%
goto :end

:check_dependencies
echo %BLUE%检查依赖...%NC%

docker --version >nul 2>&1
if errorlevel 1 (
    echo %RED%❌ Docker未安装，请先安装Docker Desktop%NC%
    pause
    exit /b 1
)

docker-compose --version >nul 2>&1
if errorlevel 1 (
    docker compose version >nul 2>&1
    if errorlevel 1 (
        echo %RED%❌ Docker Compose未安装，请先安装Docker Compose%NC%
        pause
        exit /b 1
    )
)

echo %GREEN%✅ Docker环境检查通过%NC%
goto :eof

:create_directories
echo %BLUE%创建必要目录...%NC%

if not exist "uploads" mkdir uploads
if not exist "outputs" mkdir outputs
if not exist "temp" mkdir temp
if not exist "logs" mkdir logs
if not exist "chroma-config" mkdir chroma-config

echo %GREEN%✅ 目录创建完成%NC%
goto :eof

:check_env_file
echo %BLUE%检查环境配置...%NC%

if not exist "backend\.env" (
    echo %YELLOW%⚠️ 未找到backend\.env文件，创建示例文件...%NC%
    if exist "backend\.env.example" (
        copy "backend\.env.example" "backend\.env" >nul
        echo %YELLOW%📝 请编辑 backend\.env 文件配置您的API密钥%NC%
    ) else (
        echo %RED%❌ 请手动创建backend\.env文件并配置API密钥%NC%
        echo 参考 .env.example 文件进行配置
        pause
        exit /b 1
    )
)

echo %GREEN%✅ 环境配置检查完成%NC%
goto :eof

:deploy_services
echo %BLUE%构建并启动服务...%NC%

echo 停止现有服务...
docker-compose down --remove-orphans 2>nul

echo 构建镜像...
docker-compose build --no-cache
if errorlevel 1 (
    echo %RED%❌ 镜像构建失败%NC%
    pause
    exit /b 1
)

echo 启动服务...
docker-compose up -d
if errorlevel 1 (
    echo %RED%❌ 服务启动失败%NC%
    pause
    exit /b 1
)

echo %GREEN%✅ 服务启动完成%NC%
goto :eof

:wait_for_services
echo %BLUE%等待服务就绪...%NC%

echo 等待后端API服务...
set /a count=0
:wait_backend
set /a count+=1
if %count% gtr 30 (
    echo %RED%❌ 后端服务启动超时%NC%
    docker-compose logs backend
    pause
    exit /b 1
)
curl -s http://localhost:8000/health >nul 2>&1
if errorlevel 1 (
    timeout /t 2 /nobreak >nul
    goto :wait_backend
)

echo 等待前端Web服务...
set /a count=0
:wait_frontend
set /a count+=1
if %count% gtr 15 (
    echo %RED%❌ 前端服务启动超时%NC%
    docker-compose logs frontend
    pause
    exit /b 1
)
curl -s http://localhost:3000/nginx-health >nul 2>&1
if errorlevel 1 (
    timeout /t 2 /nobreak >nul
    goto :wait_frontend
)

echo %GREEN%✅ 所有服务已就绪%NC%
goto :eof

:show_status
echo %BLUE%服务状态:%NC%
docker-compose ps

echo.
echo %GREEN%🎉 部署完成！%NC%
echo ========================================
echo %BLUE%📱 前端界面: http://localhost:3000%NC%
echo %BLUE%🔧 API文档: http://localhost:8000/docs%NC%
echo %BLUE%📊 API健康检查: http://localhost:8000/health%NC%
echo %BLUE%🗄️ ChromaDB: http://localhost:8001%NC%
echo %BLUE%🔄 Redis: localhost:6379%NC%
echo.
echo %YELLOW%💡 使用以下命令管理服务:%NC%
echo   查看日志: deploy.bat logs
echo   停止服务: deploy.bat stop
echo   重启服务: deploy.bat restart
echo   查看状态: deploy.bat status
echo   清理资源: deploy.bat clean
echo.
goto :eof

:usage
echo 用法: %0 {deploy^|stop^|restart^|logs^|status^|clean}
echo.
echo 命令说明:
echo   deploy  - 完整部署（默认）
echo   stop    - 停止所有服务
echo   restart - 重启所有服务
echo   logs    - 查看实时日志
echo   status  - 查看服务状态
echo   clean   - 清理所有资源
goto :end

:end
if not "%action%"=="logs" pause