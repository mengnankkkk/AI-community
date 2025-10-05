#!/bin/bash

# AI虚拟播客工作室 - Docker部署启动脚本
set -e

echo "🎬 AI虚拟播客工作室 - Docker部署启动"
echo "========================================"

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 检查Docker和Docker Compose
check_dependencies() {
    echo -e "${BLUE}检查依赖...${NC}"

    if ! command -v docker &> /dev/null; then
        echo -e "${RED}❌ Docker未安装，请先安装Docker${NC}"
        exit 1
    fi

    if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
        echo -e "${RED}❌ Docker Compose未安装，请先安装Docker Compose${NC}"
        exit 1
    fi

    echo -e "${GREEN}✅ Docker环境检查通过${NC}"
}

# 创建必要的目录
create_directories() {
    echo -e "${BLUE}创建必要目录...${NC}"

    mkdir -p uploads
    mkdir -p outputs
    mkdir -p temp
    mkdir -p logs
    mkdir -p chroma-config

    echo -e "${GREEN}✅ 目录创建完成${NC}"
}

# 检查环境变量文件
check_env_file() {
    echo -e "${BLUE}检查环境配置...${NC}"

    if [ ! -f backend/.env ]; then
        echo -e "${YELLOW}⚠️ 未找到backend/.env文件，创建示例文件...${NC}"
        cp backend/.env.example backend/.env 2>/dev/null || {
            echo -e "${RED}❌ 请手动创建backend/.env文件并配置API密钥${NC}"
            echo "参考 .env.example 文件进行配置"
            exit 1
        }
        echo -e "${YELLOW}📝 请编辑 backend/.env 文件配置您的API密钥${NC}"
    fi

    echo -e "${GREEN}✅ 环境配置检查完成${NC}"
}

# 构建和启动服务
deploy_services() {
    echo -e "${BLUE}构建并启动服务...${NC}"

    # 停止可能正在运行的服务
    echo "停止现有服务..."
    docker-compose down --remove-orphans 2>/dev/null || true

    # 构建并启动服务
    echo "构建镜像..."
    docker-compose build --no-cache

    echo "启动服务..."
    docker-compose up -d

    echo -e "${GREEN}✅ 服务启动完成${NC}"
}

# 等待服务就绪
wait_for_services() {
    echo -e "${BLUE}等待服务就绪...${NC}"

    # 等待后端服务
    echo "等待后端API服务..."
    timeout 60 bash -c '
        while ! curl -s http://localhost:8000/health >/dev/null 2>&1; do
            sleep 2
        done
    ' || {
        echo -e "${RED}❌ 后端服务启动超时${NC}"
        docker-compose logs backend
        exit 1
    }

    # 等待前端服务
    echo "等待前端Web服务..."
    timeout 30 bash -c '
        while ! curl -s http://localhost:3000/nginx-health >/dev/null 2>&1; do
            sleep 2
        done
    ' || {
        echo -e "${RED}❌ 前端服务启动超时${NC}"
        docker-compose logs frontend
        exit 1
    }

    echo -e "${GREEN}✅ 所有服务已就绪${NC}"
}

# 显示服务状态
show_status() {
    echo -e "${BLUE}服务状态:${NC}"
    docker-compose ps

    echo ""
    echo -e "${GREEN}🎉 部署完成！${NC}"
    echo "========================================"
    echo -e "📱 前端界面: ${BLUE}http://localhost:3000${NC}"
    echo -e "🔧 API文档: ${BLUE}http://localhost:8000/docs${NC}"
    echo -e "📊 API健康检查: ${BLUE}http://localhost:8000/health${NC}"
    echo -e "🗄️ ChromaDB: ${BLUE}http://localhost:8001${NC}"
    echo -e "🔄 Redis: ${BLUE}localhost:6379${NC}"
    echo ""
    echo -e "${YELLOW}💡 使用以下命令管理服务:${NC}"
    echo "  查看日志: docker-compose logs -f"
    echo "  停止服务: docker-compose down"
    echo "  重启服务: docker-compose restart"
    echo "  查看状态: docker-compose ps"
    echo ""
}

# 主函数
main() {
    case "${1:-deploy}" in
        "deploy")
            check_dependencies
            create_directories
            check_env_file
            deploy_services
            wait_for_services
            show_status
            ;;
        "stop")
            echo -e "${YELLOW}停止所有服务...${NC}"
            docker-compose down
            echo -e "${GREEN}✅ 服务已停止${NC}"
            ;;
        "restart")
            echo -e "${YELLOW}重启所有服务...${NC}"
            docker-compose restart
            wait_for_services
            show_status
            ;;
        "logs")
            docker-compose logs -f
            ;;
        "status")
            docker-compose ps
            ;;
        "clean")
            echo -e "${YELLOW}清理Docker资源...${NC}"
            docker-compose down --volumes --remove-orphans
            docker system prune -f
            echo -e "${GREEN}✅ 清理完成${NC}"
            ;;
        *)
            echo "用法: $0 {deploy|stop|restart|logs|status|clean}"
            echo ""
            echo "命令说明:"
            echo "  deploy  - 完整部署（默认）"
            echo "  stop    - 停止所有服务"
            echo "  restart - 重启所有服务"
            echo "  logs    - 查看实时日志"
            echo "  status  - 查看服务状态"
            echo "  clean   - 清理所有资源"
            exit 1
            ;;
    esac
}

# 执行主函数
main "$@"