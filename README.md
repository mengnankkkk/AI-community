# AI虚拟播客工作室

> 基于AI技术的专业播客生成平台，支持多角色对话、情感语音合成、智能背景音乐和RAG知识库

## 🎯 项目特性

- **🎙️ 智能播客生成**：AI驱动的多角色对话剧本创作
- **🗣️ 情感语音合成**：支持IndexTTS2和OpenAI TTS的高质量语音生成
- **🎵 智能背景音乐**：自动音频后处理和背景音乐搭配
- **📚 RAG知识库**：基于ChromaDB的智能知识检索
- **📊 质量评估**：多维度音频和内容质量分析

## 📁 项目结构

```
AI-community/
├── 📁 src/                     # 源代码
│   ├── backend/                # 后端FastAPI应用
│   ├── frontend/               # 前端Web界面
│   └── run_server.py           # 开发服务器启动脚本
├── 📁 docs/                    # 文档
│   ├── guides/                 # 使用指南
│   └── deployment/             # 部署文档
├── 📁 assets/                  # 静态资源
│   ├── audio/                  # 音频资源
│   │   ├── effects/            # 音效
│   │   ├── samples/            # 语音样本
│   │   └── background_music/   # 背景音乐
│   └── models/                 # AI模型文件
├── 📁 data/                    # 数据目录
│   ├── knowledge_base/         # RAG知识库
│   ├── uploads/                # 用户上传
│   └── output/                 # 生成输出
├── 📁 config/                  # 配置文件
│   ├── .env.example           # 环境变量模板
│   ├── docker-compose.yml     # Docker配置
│   └── nginx.conf             # Nginx配置
├── 📁 deployment/             # 部署脚本
├── 📄 requirements.txt        # Python依赖
├── 📄 run_server.py          # 根级启动脚本
└── 📄 start.bat              # Windows启动脚本
```

## 🚀 快速开始

### 环境要求

- Python 3.11+
- Node.js 16+ (可选，如需前端开发)
- FFmpeg (音频处理)

### 安装步骤

1. **克隆项目**
   ```bash
   git clone https://github.com/your-repo/AI-community.git
   cd AI-community
   ```

2. **创建虚拟环境**
   ```bash
   python -m venv .venv
   # Windows
   .venv\Scripts\activate
   # Linux/Mac
   source .venv/bin/activate
   ```

3. **安装依赖**
   ```bash
   pip install -r requirements.txt
   ```

4. **配置环境变量**
   ```bash
   cp config/.env.example .env
   # 编辑 .env 文件，添加你的API密钥
   ```

5. **启动服务**
   ```bash
   # Windows
   start.bat

   # 或手动启动
   python run_server.py
   ```

6. **访问应用**
   - 前端界面：http://localhost:8000/static/index.html
   - API文档：http://localhost:8000/docs

## 📚 文档

- [音频效果指南](docs/guides/AUDIO_EFFECTS_GUIDE.md)
- [IndexTTS2使用指南](docs/guides/IndexTTS2_GUIDE.md)
- [RAG知识库指南](docs/guides/RAG_KNOWLEDGE_GUIDE.md)
- [质量评估系统](docs/guides/QUALITY_ASSESSMENT_SYSTEM.md)
- [Docker部署指南](docs/deployment/DOCKER_DEPLOYMENT.md)

## 🔧 配置说明

主要配置文件：
- `.env`：环境变量和API密钥
- `config/docker-compose.yml`：Docker服务配置
- `src/backend/app/core/config.py`：应用配置

## 🚢 部署

### Docker部署
```bash
cd config
docker-compose up -d
```

### 生产部署
参考 [Docker部署指南](docs/deployment/DOCKER_DEPLOYMENT.md)

## 🤝 贡献

欢迎提交Issue和Pull Request！

## 📄 许可证

[MIT License](LICENSE)

## 📞 联系

如有问题，请提交Issue或联系维护者。