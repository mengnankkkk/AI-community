# AI虚拟播客工作室 - MVP版本

## 项目概述

AI虚拟播客工作室是一个创新的AI驱动平台，可以根据用户输入的主题和角色设定，自动生成完整的播客剧本并合成高质量的音频内容。

## 功能特性

### ✅ 已实现功能（第一阶段 MVP）

1. **智能剧本生成**
   - 基于大语言模型的多角色对话生成
   - 支持不同氛围和语言风格设定
   - 自动角色人设保持和互动逻辑

2. **高质量语音合成**
   - 集成OpenAI TTS引擎
   - 支持多种音色选择和描述
   - 智能角色音色匹配

3. **音频后期处理**
   - 自动音频片段拼接
   - 角色间对话停顿优化
   - 完整音频文件输出

4. **用户友好界面**
   - 响应式Web界面设计
   - 直观的播客定制单填写
   - 实时生成状态显示

5. **RESTful API架构**
   - FastAPI后端框架
   - 异步任务处理
   - 完整的API文档

## 技术架构

### 后端技术栈
- **框架**: FastAPI 0.104.1
- **语言**: Python 3.11+
- **AI服务**: OpenAI GPT + TTS
- **音频处理**: PyDub
- **数据验证**: Pydantic v2

### 前端技术栈
- **框架**: 原生HTML5 + JavaScript ES6
- **样式**: Bootstrap 5.1.3 + 自定义CSS
- **图标**: Font Awesome 6.0

### 核心模块架构

```
backend/
├── app/
│   ├── core/           # 核心配置
│   ├── models/         # 数据模型
│   ├── services/       # 业务逻辑
│   │   ├── script_generator.py    # 剧本生成引擎
│   │   ├── tts_service.py         # TTS语音合成
│   │   └── task_manager.py        # 任务管理器
│   └── routes/         # API路由
frontend/               # 前端界面
audio_output/          # 音频输出目录
```

## 快速开始

### 环境要求
- Python 3.11+
- pip包管理器
- FFmpeg（可选，用于高级音频处理）

### 安装步骤

1. **克隆项目**
```bash
git clone <your-repo-url>
cd AI-community
```

2. **安装依赖**
```bash
pip install -r requirements.txt
```

3. **配置环境变量**
```bash
cp .env.example .env
# 编辑 .env 文件，添加您的 OpenAI API 密钥
```

4. **启动服务**
```bash
python run_server.py
```

5. **访问应用**
- 前端界面: http://localhost:8000/static/index.html
- API文档: http://localhost:8000/docs
- 健康检查: http://localhost:8000/health

## API使用说明

### 核心接口

#### 1. 生成播客
```http
POST /api/v1/podcast/generate
Content-Type: application/json

{
  "custom_form": {
    "topic": "远程工作的未来",
    "atmosphere": "serious_deep",
    "target_duration": "3分钟",
    "language_style": "colloquial",
    "characters": [
      {
        "name": "张教授",
        "persona": "资深管理学专家",
        "core_viewpoint": "支持混合办公模式",
        "voice_description": "沉稳男声"
      }
    ]
  }
}
```

#### 2. 查询任务状态
```http
GET /api/v1/podcast/status/{task_id}
```

#### 3. 下载音频文件
```http
GET /api/v1/podcast/download/{task_id}
```

## 使用流程

1. **填写播客定制单**
   - 输入核心主题和标题
   - 选择讨论氛围和语言风格
   - 设定目标时长

2. **配置角色信息**
   - 添加2-5个讨论角色
   - 定义角色人设和观点
   - 描述期望的音色特点

3. **提交生成任务**
   - 系统自动分析和生成剧本
   - 并发进行TTS语音合成
   - 完成音频拼接和优化

4. **获取结果**
   - 查看生成的播客剧本
   - 在线播放或下载音频
   - 支持重新生成和调优

## 项目特色

### 🎯 核心优势
- **智能化**: 基于先进的大语言模型，生成高质量对话内容
- **个性化**: 支持自定义角色设定和音色选择
- **高效性**: 异步任务处理，快速生成播客内容
- **易用性**: 简洁直观的用户界面，零技术门槛

### 🚀 创新亮点
- **多角色互动**: 自然的角色间对话和观点碰撞
- **氛围控制**: 支持多种讨论氛围和语言风格
- **音色匹配**: 智能的角色音色映射系统
- **实时反馈**: 完整的任务状态追踪和进度显示

## 开发计划

### 第二阶段功能（Week 2-3）
- [ ] 状态化循环生成机制
- [ ] SSML精细音色控制
- [ ] RAG知识库集成
- [ ] 模型微调优化

### 第三阶段功能（Week 4）
- [ ] 音效和背景音乐
- [ ] 批量处理能力
- [ ] 用户管理系统
- [ ] 云端部署优化

## 技术支持

如需技术支持或反馈问题，请：
1. 查看项目文档
2. 检查服务状态 `/health`
3. 查看API文档 `/docs`
4. 提交Issue或联系开发团队

---

*本项目为AI驱动的播客生成工具，致力于为内容创作者提供高效、智能的播客制作解决方案。*