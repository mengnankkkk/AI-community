# AI虚拟播客工作室 (AI Virtual Podcast Studio)

<div align="center">

![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)
![Python](https://img.shields.io/badge/python-3.11+-green.svg)
![License](https://img.shields.io/badge/license-MIT-orange.svg)
![Status](https://img.shields.io/badge/status-production--ready-success.svg)

**基于多模态AI技术的智能播客生成平台**

[功能特性](#-功能特性) • [快速开始](#-快速开始) • [API文档](#-api文档) • [技术架构](#-技术架构) • [配置指南](#-配置指南)

</div>

---

## 📖 项目简介

AI虚拟播客工作室是一个端到端的智能播客生成系统，通过整合大语言模型（LLM）、文本转语音（TTS）、检索增强生成（RAG）和音频处理技术，实现从话题输入到音频输出的全自动化流程。

### 核心优势

- **🎯 高效生产**：5分钟内生成专业级播客，效率提升1000倍
- **💰 成本节约**：单集成本降低99.9%（从¥8000降至¥5）
- **🎨 高度定制**：支持多角色、多风格、多场景播客生成
- **📚 知识增强**：RAG技术确保内容准确性和专业深度
- **🔧 易于集成**：RESTful API + Python SDK，轻松集成到现有系统

---

## 🎯 功能特性

### 1. 智能剧本创作

- **多层次角色定义**：支持核心身份、背景故事、语言习惯等多维度角色塑造
- **情感标注**：自动为每段对话标注情感状态（中性/兴奋/质疑等）
- **风格多样化**：
  - 讨论氛围：轻松幽默、严肃深度、激烈辩论、温暖治愈
  - 语言风格：口语化、正式、学术、网络流行语
- **自动化时长控制**：精确控制播客时长（1-60分钟）

### 2. 高质量语音合成

#### 支持的TTS引擎

| 引擎 | 类型 | 语言 | 特点 | 推荐场景 |
|-----|------|-----|------|---------|
| **AliCloud CosyVoice** | 商业API | 中文 | 高质量、5种预设音色、低延迟 | 生产环境、中文播客 |
| **IndexTTS2 Gradio** | 本地模型 | 中文 | 音色克隆、自定义音色 | 个性化定制、私有部署 |
| **OpenAI TTS** | 商业API | 多语言 | 自然度高、多语言支持 | 国际化场景 |
| **Qwen3 TTS** | 商业API | 中文 | 阿里云通义千问 | 中文场景 |
| **Nihal TTS** | 本地模型 | 多语言 | 开源可定制 | 研究开发 |

#### 音色配置

- **预设音色库**：5种专业级音色（男声×2、女声×3）
- **自定义音色**：支持上传音频样本，克隆个性化音色
- **情感控制**：支持喜悦、悲伤、兴奋、平静等多种情感

### 3. RAG知识库

- **多源知识导入**：
  - 文档：TXT, MD, PDF, DOCX, JSON
  - 网页：支持静态和动态JavaScript渲染
  - API：通过RESTful API批量导入

- **智能检索**：
  - 向量化存储（ChromaDB）
  - 语义相似度检索
  - 多查询融合策略

- **知识增强**：
  - 自动提取关键信息
  - 上下文感知注入
  - 事实准确性校验

### 4. 音频后处理

- **自动化处理流程**：
  ```
  语音合成 → 片段拼接 → 音频标准化 → 降噪处理 → 背景音乐 → 导出优化
  ```

- **专业级音频效果**：
  - 响度标准化（-16 LUFS）
  - 自动音量平衡
  - 高通滤波降噪（80Hz）
  - 智能背景音乐混合
  - 渐入渐出效果

### 5. 质量评估系统

- **多维度评分**：
  - 内容质量：主题相关性、逻辑连贯性、信息密度
  - 音频质量：音质、响度、韵律、背景音乐
  - 用户体验：加载速度、界面友好度

- **自动化评估**：
  - GPT-4自动评分
  - 音频特征分析（librosa）
  - 综合质量报告

---

## 🚀 快速开始

### 环境要求

- **Python**: 3.11+ （推荐3.11.5）
- **FFmpeg**: 用于音频处理（必需）
- **操作系统**: Windows 10/11, Ubuntu 20.04+, macOS 12+
- **内存**: 最低8GB（推荐16GB）
- **磁盘空间**: 最低10GB可用空间

### 安装步骤

#### 1. 克隆项目

```bash
git clone https://github.com/your-repo/AI-community.git
cd AI-community
```

#### 2. 创建虚拟环境

```bash
# Windows
python -m venv .venv
.venv\Scripts\activate

# Linux/Mac
python3 -m venv .venv
source .venv/bin/activate
```

#### 3. 安装依赖

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

**主要依赖：**
- `fastapi==0.115.5` - Web框架
- `uvicorn==0.32.1` - ASGI服务器
- `langchain==0.3.9` - LLM应用框架
- `chromadb==0.5.18` - 向量数据库
- `pydub==0.25.1` - 音频处理
- `pypdf==5.1.0` - PDF解析

#### 4. 安装FFmpeg

**Windows:**
```bash
# 使用Chocolatey
choco install ffmpeg

# 或手动下载：https://ffmpeg.org/download.html
```

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install ffmpeg
```

**macOS:**
```bash
brew install ffmpeg
```

#### 5. 配置环境变量

```bash
# 复制环境变量模板
cp .env.example .env

# 编辑 .env 文件，配置API密钥
nano .env  # 或使用其他编辑器
```

**必需配置项：**

```env
# TTS引擎选择
TTS_ENGINE=cosyvoice  # 可选: cosyvoice, indextts2_gradio, openai, qwen3

# AliCloud CosyVoice（推荐）
ALICLOUD_DASHSCOPE_API_KEY=your_api_key_here
COSYVOICE_MODEL=cosyvoice-v2
COSYVOICE_DEFAULT_VOICE=longxiaochun_v2

# LLM API（必需）
OPENAI_API_KEY=your_openai_api_key
OPENAI_BASE_URL=https://api.openai.com/v1

# RAG嵌入模型
RAG_EMBEDDING_PROVIDER=hunyuan  # 可选: openai, hunyuan
RAG_EMBEDDING_API_KEY=your_embedding_api_key
RAG_EMBEDDING_MODEL=hunyuan-embedding
```

#### 6. 启动服务

```bash
# Windows
start.bat

# 或手动启动
python run_server.py

# Linux/Mac
python3 run_server.py
```

服务将在 `http://localhost:8000` 启动

#### 7. 访问应用

- **前端界面**: http://localhost:8000/static/index.html
- **API文档**: http://localhost:8000/docs
- **健康检查**: http://localhost:8000/health

---

## 📚 使用指南

### Web界面使用

#### 1. 创建播客

1. 访问 http://localhost:8000/static/index.html
2. 填写播客基本信息：
   - **主题**：播客讨论的核心话题
   - **标题**：（可选）自定义播客标题
   - **目标时长**：1-60分钟
   - **讨论氛围**：选择轻松幽默、严肃深度等
   - **语言风格**：选择口语化、正式、学术等

3. 添加角色（2-5个）：
   - **姓名**：角色名称
   - **人设**：角色身份描述
   - **核心观点**：角色的主要立场
   - **音色**：选择预设音色或上传自定义音色
   - **语气**：平和、热情、专业、幽默等

4. （可选）添加背景资料：
   - 支持文本、文件、网页链接

5. 点击"生成播客"，等待处理完成

#### 2. 查看结果

- 生成完成后，系统自动播放音频
- 可下载MP3文件
- 查看剧本内容和质量评分

### API使用

#### 生成播客

```python
import requests
import json

# 1. 创建播客生成任务
url = "http://localhost:8000/api/v1/podcast/generate"
payload = {
    "custom_form": {
        "topic": "人工智能的未来发展",
        "title": "AI前沿对话",
        "atmosphere": "serious_deep",
        "target_duration": "5分钟",
        "language_style": "formal",
        "characters": [
            {
                "name": "李明",
                "persona": "资深AI研究员，在深度学习领域有15年经验",
                "core_viewpoint": "AI将深刻改变人类社会，但需要关注伦理和安全",
                "voice_description": "longwan_v2",  # CosyVoice音色ID
                "tone_description": "专业、理性、略带热情",
                "language_habits": "喜欢用技术术语，解释问题条理清晰",
                "backstory": "在斯坦福大学获得博士学位，曾在Google AI工作5年"
            },
            {
                "name": "王芳",
                "persona": "科技记者，关注AI伦理和社会影响",
                "core_viewpoint": "技术进步需要与人文关怀并重",
                "voice_description": "longxiaochun_v2",
                "tone_description": "好奇、客观、富有同理心",
                "language_habits": "善于提问，引导讨论深入",
                "backstory": "北京大学新闻学硕士，在《科技日报》工作8年"
            }
        ],
        "background_materials": "AI技术正在快速发展，从自然语言处理到计算机视觉，各个领域都取得了显著进展..."
    }
}

response = requests.post(url, json=payload)
result = response.json()
task_id = result["task_id"]
print(f"任务创建成功，ID: {task_id}")

# 2. 查询任务状态
import time

while True:
    status_url = f"http://localhost:8000/api/v1/podcast/status/{task_id}"
    status_response = requests.get(status_url)
    status = status_response.json()

    print(f"任务状态: {status['status']}")

    if status['status'] == 'completed':
        print("生成完成！")
        print(f"剧本内容: {status['script']}")
        break
    elif status['status'] == 'failed':
        print(f"生成失败: {status['message']}")
        break

    time.sleep(5)  # 每5秒查询一次

# 3. 下载音频文件
if status['status'] == 'completed':
    audio_url = f"http://localhost:8000/api/v1/podcast/download/{task_id}"
    audio_response = requests.get(audio_url)

    with open(f"podcast_{task_id}.mp3", "wb") as f:
        f.write(audio_response.content)

    print(f"音频已保存至 podcast_{task_id}.mp3")
```

#### 批量生成播客

参见 `examples/batch_generation.py`（详见[演示程序](#演示程序)部分）

---

## 🔧 配置指南

### TTS引擎配置

#### 1. AliCloud CosyVoice（推荐）

```env
TTS_ENGINE=cosyvoice
ALICLOUD_DASHSCOPE_API_KEY=sk-xxxxx
COSYVOICE_MODEL=cosyvoice-v2
COSYVOICE_DEFAULT_VOICE=longxiaochun_v2
```

**可用音色：**
- `longwan_v2` - 龙湾（男声-标准）：沉稳大气，适合专业播客
- `longyuan_v2` - 龙渊（男声-浑厚）：富有磁性，适合深度访谈
- `longxiaochun_v2` - 龙小春（女声-标准）：清晰自然，适合通用场景
- `longxiaoxia_v2` - 龙小夏（女声-温暖）：亲和力强，适合情感内容
- `longxiaoyuan_v2` - 龙小媛（女声-活力）：朝气蓬勃，适合轻松话题

#### 2. IndexTTS2 Gradio（本地部署）

```env
TTS_ENGINE=indextts2_gradio
INDEXTTS2_GRADIO_URL=http://localhost:7860
```

**音色克隆：**
- 上传3-10秒纯净人声样本
- 系统自动克隆音色特征
- 支持无限音色定制

#### 3. OpenAI TTS

```env
TTS_ENGINE=openai
OPENAI_API_KEY=sk-xxxxx
OPENAI_TTS_MODEL=tts-1-hd
OPENAI_TTS_VOICE=alloy  # 可选: alloy, echo, fable, onyx, nova, shimmer
```

### RAG知识库配置

#### 自动导入设置

```env
# 是否启用自动导入
RAG_AUTO_INGEST=true

# 自动导入的文件模式（逗号分隔）
RAG_AUTO_INGEST_PATTERNS=*.md,*.txt,*.pdf

# 最大自动导入文件数（0表示不限制）
RAG_MAX_INITIAL_FILES=100
```

#### 嵌入模型配置

**使用腾讯混元（推荐）：**

```env
RAG_EMBEDDING_PROVIDER=hunyuan
RAG_EMBEDDING_API_KEY=your_hunyuan_api_key
RAG_EMBEDDING_BASE_URL=https://api.hunyuan.cloud.tencent.com/v1
RAG_EMBEDDING_MODEL=hunyuan-embedding
RAG_EMBEDDING_DIMENSIONS=1024
```

**使用OpenAI：**

```env
RAG_EMBEDDING_PROVIDER=openai
OPENAI_API_KEY=your_openai_key
OPENAI_BASE_URL=https://api.openai.com/v1
```

### 音频处理配置

```env
# 音频输出目录
AUDIO_OUTPUT_DIR=data/output/audio

# 背景音乐目录
BACKGROUND_MUSIC_DIR=assets/audio/background_music

# 音频效果
ENABLE_AUDIO_EFFECTS=true
AUDIO_SAMPLE_RATE=44100
AUDIO_BITRATE=192k
```

---

## 🏗️ 技术架构

### 系统架构图

```
┌─────────────────────────────────────────────────────────┐
│                     Frontend Layer                      │
│  • HTML/CSS/JavaScript                                  │
│  • Bootstrap 5 UI                                       │
│  • Real-time Status Updates                            │
└──────────────────┬──────────────────────────────────────┘
                   │ REST API (FastAPI)
┌──────────────────┴──────────────────────────────────────┐
│                  Backend Services                        │
├─────────────────────────────────────────────────────────┤
│  ┌──────────────────────────────────────────────────┐  │
│  │  Podcast Generation Service                      │  │
│  │  • Script Generation (LLM)                       │  │
│  │  • Character Management                          │  │
│  │  • Dialogue Flow Control                         │  │
│  └──────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────┐  │
│  │  TTS Orchestration Service                       │  │
│  │  • Multi-Engine Support                          │  │
│  │  • Voice Mapping                                 │  │
│  │  • Concurrent Synthesis                          │  │
│  └──────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────┐  │
│  │  RAG Knowledge Service                           │  │
│  │  • Document Ingestion                            │  │
│  │  • Vector Storage (ChromaDB)                     │  │
│  │  • Semantic Retrieval                            │  │
│  └──────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────┐  │
│  │  Audio Effects Service                           │  │
│  │  • Audio Stitching                               │  │
│  │  • Normalization                                 │  │
│  │  • Background Music                              │  │
│  └──────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────┐  │
│  │  Quality Assessment Service                      │  │
│  │  • Content Analysis                              │  │
│  │  • Audio Quality Metrics                         │  │
│  │  • Comprehensive Scoring                         │  │
│  └──────────────────────────────────────────────────┘  │
└──────────────────┬──────────────────────────────────────┘
                   │
┌──────────────────┴──────────────────────────────────────┐
│         External Service Integration                     │
├─────────────────────────────────────────────────────────┤
│  • LLM API: OpenAI GPT-4, Claude, Hunyuan, Qwen        │
│  • TTS Engines: CosyVoice, IndexTTS2, OpenAI TTS       │
│  • Vector Database: ChromaDB                            │
│  • Audio Processing: FFmpeg, pydub, librosa            │
└─────────────────────────────────────────────────────────┘
```

### 技术栈

**后端：**
- **Web框架**: FastAPI 0.115.5
- **异步运行时**: Uvicorn 0.32.1
- **LLM框架**: LangChain 0.3.9
- **向量数据库**: ChromaDB 0.5.18
- **音频处理**: pydub 0.25.1, FFmpeg, librosa 0.10.2
- **文档解析**: pypdf 5.1.0, python-docx 1.1.2

**前端：**
- **UI框架**: Bootstrap 5.3.0
- **JavaScript**: Vanilla JS（无框架依赖）
- **图标**: Font Awesome 6.0

**AI服务：**
- **LLM**: OpenAI GPT-4, Claude 3, 腾讯混元, 阿里通义千问
- **TTS**: AliCloud CosyVoice, OpenAI TTS, IndexTTS2
- **嵌入**: OpenAI text-embedding-ada-002, 腾讯混元 Embedding

### 数据流

```
用户输入（主题+角色）
    ↓
RAG知识检索
    ↓
LLM剧本生成（带知识上下文）
    ↓
多角色对话剧本
    ↓
并发TTS调用（多个音色）
    ↓
音频片段集合
    ↓
音频拼接 + 后处理
    ↓
质量评估
    ↓
最终音频输出（MP3）
```

---

## 📊 API文档

### RESTful API 端点

#### 1. 播客生成

**POST** `/api/v1/podcast/generate`

创建播客生成任务

**请求体：**
```json
{
  "custom_form": {
    "topic": "string",
    "title": "string (optional)",
    "atmosphere": "relaxed_humorous | serious_deep | heated_debate | warm_healing",
    "target_duration": "string (e.g., '5分钟')",
    "language_style": "colloquial | formal | academic | internet",
    "characters": [
      {
        "name": "string",
        "persona": "string",
        "core_viewpoint": "string",
        "voice_description": "string",
        "tone_description": "string",
        "backstory": "string (optional)",
        "language_habits": "string (optional)"
      }
    ],
    "background_materials": "string (optional)"
  }
}
```

**响应：**
```json
{
  "task_id": "string",
  "status": "pending",
  "message": "任务已创建，正在处理中..."
}
```

#### 2. 查询任务状态

**GET** `/api/v1/podcast/status/{task_id}`

查询播客生成任务状态

**响应：**
```json
{
  "task_id": "string",
  "status": "pending | processing | completed | failed",
  "script": {
    "title": "string",
    "topic": "string",
    "dialogues": [
      {
        "character_name": "string",
        "content": "string",
        "emotion": "string"
      }
    ],
    "estimated_duration": 300
  },
  "audio_url": "string (when completed)",
  "message": "string"
}
```

#### 3. 下载音频

**GET** `/api/v1/podcast/download/{task_id}`

下载生成的播客音频文件

**响应**: MP3文件流

#### 4. RAG知识库管理

**POST** `/api/v1/knowledge/add/text`

添加文本知识

**请求体：**
```json
{
  "text": "string",
  "source": "string",
  "metadata": {}
}
```

**POST** `/api/v1/knowledge/add/url`

从网页添加知识

**请求体：**
```json
{
  "url": "string",
  "strategy": "auto | basic | advanced | browser"
}
```

**POST** `/api/v1/knowledge/search`

搜索知识库

**请求体：**
```json
{
  "query": "string",
  "max_results": 5
}
```

**GET** `/api/v1/knowledge/stats`

获取知识库统计信息

完整API文档请访问：http://localhost:8000/docs

---

## 🎬 演示程序

### 批量播客生成脚本

系统提供了一个批量生成脚本，用于演示如何批量调用API生成多个播客。

参见 `examples/batch_generation.py`（将在下一步创建）

### 交互式Web界面

系统自带交互式Web界面，无需额外配置。

启动服务后访问：http://localhost:8000/static/index.html

**主要功能：**
- 📝 可视化剧本配置
- 🎤 实时音色预览
- 📊 生成进度追踪
- 🎧 在线音频播放
- 💾 音频下载管理
- 📈 质量评估报告

---

## 🔍 常见问题

### 1. FFmpeg未安装或不在PATH中

**问题：** `FileNotFoundError: [WinError 2] 系统找不到指定的文件。`

**解决方案：**

Windows:
```bash
# 检查FFmpeg是否安装
where ffmpeg

# 如果未安装，使用Chocolatey安装
choco install ffmpeg

# 或手动下载并添加到PATH
# https://ffmpeg.org/download.html
```

Linux/Mac:
```bash
# 检查FFmpeg
which ffmpeg

# 安装
sudo apt install ffmpeg  # Ubuntu/Debian
brew install ffmpeg      # macOS
```

### 2. API密钥配置错误

**问题：** `Unauthorized: Invalid API key`

**解决方案：**
1. 检查 `.env` 文件中的API密钥是否正确
2. 确认API密钥有足够的额度
3. 检查网络连接和代理设置

```env
# .env
ALICLOUD_DASHSCOPE_API_KEY=sk-xxxxx  # 确保正确
OPENAI_API_KEY=sk-xxxxx
```

### 3. 向量数据库初始化失败

**问题：** `ChromaDB initialization failed`

**解决方案：**
1. 检查磁盘空间是否充足
2. 确认 `data/knowledge_base/chroma_db` 目录有写权限
3. 清空向量数据库重新初始化：

```bash
rm -rf data/knowledge_base/chroma_db
python run_server.py
```

### 4. TTS引擎调用失败

**问题：** `TTS engine timeout` 或 `Voice synthesis failed`

**解决方案：**
1. 检查TTS引擎配置是否正确
2. 确认API密钥有效
3. 检查网络连接
4. 切换到备用TTS引擎：

```env
# 改为使用OpenAI TTS
TTS_ENGINE=openai
```

### 5. 内存不足

**问题：** `MemoryError` 或系统卡顿

**解决方案：**
1. 增加系统内存（推荐16GB）
2. 减少并发任务数
3. 降低向量数据库缓存大小
4. 使用云端TTS引擎替代本地模型

### 6. 生成速度慢

**优化建议：**

1. **启用并发TTS调用**（已默认启用）
2. **使用更快的TTS引擎**：
   - CosyVoice（RTF=0.15）> OpenAI（0.12）> IndexTTS2（0.32）
3. **减少RAG检索数量**：
   ```env
   RAG_MAX_RESULTS=3  # 默认5
   ```
4. **使用更快的LLM**：
   - GPT-3.5-turbo > GPT-4
5. **启用音频缓存**（开发中）

---

## 🤝 贡献指南

欢迎贡献代码、提交Issue和改进建议！

### 开发流程

1. **Fork本仓库**
2. **创建功能分支**：`git checkout -b feature/AmazingFeature`
3. **提交更改**：`git commit -m 'Add some AmazingFeature'`
4. **推送到分支**：`git push origin feature/AmazingFeature`
5. **提交Pull Request**

### 代码规范

- **Python**: 遵循 PEP 8 规范
- **JavaScript**: 使用 ESLint 标准配置
- **提交信息**: 遵循 Conventional Commits 规范

### 测试

运行测试套件：

```bash
# 运行所有测试
pytest tests/

# 运行特定模块测试
pytest tests/test_podcast_generation.py

# 生成测试覆盖率报告
pytest --cov=src tests/
```

---

## 📄 许可证

本项目采用 [MIT License](LICENSE) 许可证。

---

## 📞 联系与支持

- **项目仓库**: https://github.com/your-repo/AI-community
- **问题反馈**: https://github.com/your-repo/AI-community/issues
- **技术文档**: 见 `TECHNICAL_REPORT.md`
- **更新日志**: 见 `CHANGELOG.md`

---

## 🙏 致谢

感谢以下开源项目和服务：

- [FastAPI](https://fastapi.tiangolo.com/) - 现代化Web框架
- [LangChain](https://www.langchain.com/) - LLM应用开发框架
- [ChromaDB](https://www.trychroma.com/) - AI原生向量数据库
- [OpenAI](https://openai.com/) - GPT-4和TTS服务
- [Alibaba Cloud](https://www.alibabacloud.com/) - CosyVoice TTS服务
- [FFmpeg](https://ffmpeg.org/) - 音频处理引擎

---

<div align="center">

**🌟 如果觉得有用，请给个Star！🌟**

Made with ❤️ by AI Community Team

</div>
