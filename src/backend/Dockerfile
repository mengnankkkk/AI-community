# AI虚拟播客工作室 - 后端Docker镜像
FROM python:3.9-slim

# 设置工作目录
WORKDIR /app

# 设置环境变量
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DEBIAN_FRONTEND=noninteractive

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    ffmpeg \
    portaudio19-dev \
    libsndfile1 \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 升级pip
RUN pip install --upgrade pip

# 复制requirements文件
COPY ../requirements.txt .

# 安装Python依赖
RUN pip install -r requirements.txt --no-cache-dir

# 复制应用代码
COPY . .

# 创建必要的目录
RUN mkdir -p /app/uploads /app/outputs /app/temp /app/logs

# 设置权限
RUN chmod +x /app/run_server.py

# 健康检查
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# 暴露端口
EXPOSE 8000

# 启动命令
CMD ["python", "run_server.py"]