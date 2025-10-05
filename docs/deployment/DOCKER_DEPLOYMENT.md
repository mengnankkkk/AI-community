# Docker 部署指南

## 系统要求

- Docker Engine 20.10+
- Docker Compose 2.0+
- 至少 4GB 内存
- 至少 10GB 存储空间

## 快速开始

### 1. 克隆项目
```bash
git clone <repository-url>
cd AI-community
```

### 2. 配置环境变量
```bash
# 复制环境变量示例文件
cp .env.example backend/.env

# 编辑配置文件，添加必要的API密钥
# vim backend/.env  # Linux/Mac
# notepad backend\.env  # Windows
```

### 3. 启动服务

**Linux/Mac:**
```bash
# 给脚本执行权限
chmod +x deploy.sh

# 部署服务
./deploy.sh deploy
```

**Windows:**
```cmd
# 直接运行批处理文件
deploy.bat deploy
```

### 4. 访问服务

服务启动后，访问以下地址：

- 📱 **前端界面**: http://localhost:3000
- 🔧 **API文档**: http://localhost:8000/docs
- 📊 **健康检查**: http://localhost:8000/health
- 🗄️ **ChromaDB**: http://localhost:8001
- 🔄 **Redis**: localhost:6379

## 服务管理

### 基本命令

```bash
# 查看服务状态
./deploy.sh status

# 查看日志
./deploy.sh logs

# 重启服务
./deploy.sh restart

# 停止服务
./deploy.sh stop

# 清理所有资源
./deploy.sh clean
```

### Docker Compose 命令

```bash
# 构建镜像
docker-compose build

# 启动服务
docker-compose up -d

# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f

# 停止服务
docker-compose down

# 重启特定服务
docker-compose restart backend
```

## 服务架构

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │    Backend      │    │     Redis       │
│   (Nginx)       │    │   (FastAPI)     │    │   (Cache)       │
│   Port: 3000    │────│   Port: 8000    │────│   Port: 6379    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │
                                │
                       ┌─────────────────┐
                       │   ChromaDB      │
                       │  (Vector DB)    │
                       │   Port: 8001    │
                       └─────────────────┘
```

## 存储卷

```
ai-podcast-studio/
├── uploads/          # 用户上传文件
├── outputs/          # 生成的音频文件
├── temp/             # 临时文件
├── logs/             # 应用日志
├── redis_data/       # Redis数据持久化
└── chromadb_data/    # ChromaDB数据持久化
```

## 环境变量配置

### 必需配置

```env
# API密钥
OPENAI_API_KEY=your_openai_api_key_here
GEMINI_API_KEY=your_gemini_api_key_here
DEEPSEEK_API_KEY=your_deepseek_api_key_here
```

### 可选配置

```env
# 应用配置
DEBUG=false
HOST=0.0.0.0
PORT=8000

# Docker配置
COMPOSE_PROJECT_NAME=ai-podcast-studio
CORS_ORIGINS=http://localhost:3000

# 性能配置
WORKER_PROCESSES=1
TIMEOUT=30
```

## 健康检查

系统提供多级健康检查：

```bash
# 整体健康检查
curl http://localhost:8000/health

# Nginx健康检查
curl http://localhost:3000/nginx-health

# Redis健康检查
docker-compose exec redis redis-cli ping

# ChromaDB健康检查
curl http://localhost:8001/api/v1/heartbeat
```

## 故障排除

### 常见问题

1. **端口冲突**
   ```bash
   # 检查端口占用
   netstat -tlnp | grep :3000
   netstat -tlnp | grep :8000

   # 修改 docker-compose.yml 中的端口映射
   ```

2. **内存不足**
   ```bash
   # 检查系统资源
   docker system df
   docker stats

   # 清理未使用资源
   docker system prune -a
   ```

3. **服务启动失败**
   ```bash
   # 查看详细日志
   docker-compose logs backend
   docker-compose logs frontend

   # 重建镜像
   docker-compose build --no-cache
   ```

4. **环境变量问题**
   ```bash
   # 检查环境变量是否正确加载
   docker-compose exec backend env | grep API_KEY
   ```

### 日志位置

- 应用日志: `./logs/`
- Docker日志: `docker-compose logs`
- Nginx日志: `docker-compose logs frontend`
- 系统日志: `/var/log/docker/`

## 生产部署建议

### 安全配置

1. **更改默认密码**
   ```bash
   # 生成新的ChromaDB密码
   htpasswd -B -C 12 -n admin > chroma-config/server.htpasswd
   ```

2. **使用HTTPS**
   ```yaml
   # 在 docker-compose.yml 中添加 SSL 配置
   nginx:
     volumes:
       - ./ssl:/etc/ssl/certs:ro
   ```

3. **限制网络访问**
   ```yaml
   # 移除不必要的端口暴露
   ports:
     - "127.0.0.1:8000:8000"  # 只绑定本地接口
   ```

### 性能优化

1. **增加资源限制**
   ```yaml
   backend:
     deploy:
       resources:
         limits:
           memory: 2G
           cpus: '1.0'
   ```

2. **使用外部数据库**
   ```yaml
   # 使用外部 Redis 和 ChromaDB 实例
   environment:
     - REDIS_URL=redis://external-redis:6379
     - CHROMA_HOST=external-chromadb
   ```

3. **启用缓存**
   ```env
   REDIS_CACHE_TTL=3600
   ENABLE_RESPONSE_CACHE=true
   ```

## 备份与恢复

### 数据备份

```bash
# 备份 Redis 数据
docker-compose exec redis redis-cli BGSAVE
docker cp ai-podcast-redis:/data/dump.rdb ./backup/

# 备份 ChromaDB 数据
docker-compose exec chromadb tar -czf /tmp/chroma-backup.tar.gz /chroma/chroma
docker cp ai-podcast-chromadb:/tmp/chroma-backup.tar.gz ./backup/

# 备份用户文件
tar -czf backup/user-files-$(date +%Y%m%d).tar.gz uploads/ outputs/
```

### 数据恢复

```bash
# 恢复 Redis 数据
docker cp ./backup/dump.rdb ai-podcast-redis:/data/
docker-compose restart redis

# 恢复 ChromaDB 数据
docker cp ./backup/chroma-backup.tar.gz ai-podcast-chromadb:/tmp/
docker-compose exec chromadb tar -xzf /tmp/chroma-backup.tar.gz -C /
docker-compose restart chromadb
```

## 监控

### 基础监控

```bash
# 服务状态监控
watch docker-compose ps

# 资源使用监控
watch docker stats

# 日志监控
docker-compose logs -f --tail=100
```

### 高级监控

可以集成 Prometheus + Grafana 进行详细监控：

```yaml
# 添加到 docker-compose.yml
prometheus:
  image: prom/prometheus
  ports:
    - "9090:9090"
  volumes:
    - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml

grafana:
  image: grafana/grafana
  ports:
    - "3001:3000"
  environment:
    - GF_SECURITY_ADMIN_PASSWORD=admin
```

---

## 联系支持

如遇到问题，请检查：

1. [GitHub Issues](https://github.com/your-repo/issues)
2. [文档](./docs/)
3. [FAQ](./docs/FAQ.md)

---

**注意**: 首次部署可能需要下载较大的Docker镜像，请确保网络连接稳定。