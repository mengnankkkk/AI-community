# 评委评估指南

本指南旨在帮助评委快速了解并评估AI虚拟播客工作室系统的功能和效果。

---

## 📋 目录

- [系统概述](#系统概述)
- [快速开始](#快速开始)
- [批量评估流程](#批量评估流程)
- [评估维度](#评估维度)
- [演示程序使用](#演示程序使用)
- [常见问题](#常见问题)

---

## 系统概述

### 核心功能

AI虚拟播客工作室是一个端到端的智能播客生成系统，集成了以下核心技术：

- **大语言模型 (LLM)**：自动生成多角色对话剧本
- **文本转语音 (TTS)**：将剧本转换为自然的语音
- **检索增强生成 (RAG)**：基于知识库提升内容准确性
- **音频后处理**：自动化音频优化和背景音乐配置

### 技术亮点

1. **多模态AI集成**：LLM + TTS + RAG的深度融合
2. **端到端自动化**：从文本到音频的全流程自动化
3. **高度可定制**：支持多角色、多风格、多场景
4. **生产就绪**：商业级质量，可直接应用于生产环境

---

## 快速开始

### 环境准备

确保您的环境满足以下要求：

```bash
# 检查Python版本 (需要3.11+)
python --version

# 检查FFmpeg安装
ffmpeg -version

# 克隆项目
git clone <repository_url>
cd AI-community
```

### 安装依赖

```bash
# 创建虚拟环境
python -m venv .venv

# Windows
.venv\Scripts\activate

# Linux/Mac
source .venv/bin/activate

# 安装依赖
pip install -r requirements.txt
```

### 配置环境变量

复制 `.env.example` 为 `.env` 并配置API密钥：

```env
# TTS引擎配置
TTS_ENGINE=cosyvoice
ALICLOUD_DASHSCOPE_API_KEY=your_api_key_here

# LLM配置
OPENAI_API_KEY=your_openai_key
OPENAI_BASE_URL=https://api.openai.com/v1

# RAG配置
RAG_EMBEDDING_PROVIDER=hunyuan
RAG_EMBEDDING_API_KEY=your_embedding_key
```

### 启动服务

```bash
# 方式1: 使用启动脚本 (Windows)
start.bat

# 方式2: 直接运行
python run_server.py
```

服务启动后，访问：
- **前端界面**: http://localhost:8000/static/index.html
- **API文档**: http://localhost:8000/docs

---

## 批量评估流程

我们提供了三个演示程序，方便评委进行批量评估。

### 流程概览

```
1. 启动服务
   ↓
2. 运行批量生成演示 (batch_demo.py)
   ↓
3. 运行批量评估程序 (evaluation_demo.py)
   ↓
4. 查看评估报告
```

### 详细步骤

#### 步骤1: 启动服务

```bash
python run_server.py
```

等待服务启动完成，看到以下信息：

```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
```

#### 步骤2: 批量生成播客

打开新的终端窗口，运行批量生成演示：

```bash
# 使用预设配置生成3个播客
python examples/batch_demo.py

# 或指定输出目录
python examples/batch_demo.py --output output/my_test

# 或使用自定义配置文件
python examples/batch_demo.py --config my_config.json
```

**预期输出**：

```
🚀 批量播客生成演示
=============================================================
📊 任务数量: 3
📁 输出目录: output/batch_demo
⏰ 开始时间: 2024-01-15 10:30:00
=============================================================

[1/3] 提交任务: 人工智能的未来发展趋势
  ✅ 任务创建成功: abc123...

... (等待生成完成)

✅ 成功: 3 / 3
📊 成功率: 100.0%
⏱️  平均生成时间: 165.3s
💾 总音频大小: 7.35 MB
```

#### 步骤3: 批量评估

使用生成报告中的任务ID进行批量评估：

```bash
# 从批量生成报告中提取任务ID并评估
python examples/evaluation_demo.py --report output/batch_demo/batch_report.json

# 或直接指定任务ID
python examples/evaluation_demo.py --task-ids abc123 def456 ghi789
```

**预期输出**：

```
📊 批量播客质量评估
=============================================================
🎯 评估任务数: 3
📁 输出目录: output/evaluation
=============================================================

[1/3] 评估任务: abc123...
  ✅ 评估完成 (耗时: 15.2s)
  📊 综合评分: 8.5/10
  📝 内容质量: 8.3/10
  🎵 音频质量: 8.7/10

📈 平均分数:
  • 综合评分: 8.50/10
  • 内容质量: 8.30/10
  • 音频质量: 8.70/10
```

#### 步骤4: 查看报告

批量评估完成后，查看生成的报告：

```bash
# 详细评估报告
output/evaluation/evaluation_report.json

# 汇总统计报告
output/evaluation/evaluation_summary.json

# 生成的音频文件
output/batch_demo/podcast_*.mp3

# 剧本文件
output/batch_demo/script_*.json
```

---

## 评估维度

### 1. 内容质量 (Content Quality)

评估剧本生成的质量：

| 指标 | 说明 | 权重 |
|-----|------|------|
| **主题相关性** | 对话内容与主题的契合度 | 30% |
| **逻辑连贯性** | 对话流转是否自然流畅 | 25% |
| **信息密度** | 单位时间的有效信息量 | 20% |
| **角色一致性** | 角色言行与人设的匹配度 | 25% |

**评分标准**：
- 9-10分：专业级，内容深入且连贯
- 7-8分：良好，内容有价值，逻辑清晰
- 5-6分：合格，基本符合要求
- <5分：不合格，需要重新生成

### 2. 音频质量 (Audio Quality)

评估语音合成和音频处理的质量：

| 指标 | 说明 | 权重 |
|-----|------|------|
| **音质** | 语音的清晰度和自然度 | 35% |
| **响度平衡** | 音量的一致性和舒适度 | 25% |
| **韵律自然度** | 语速、停顿、语调的自然性 | 25% |
| **背景音乐** | 背景音乐与内容的协调性 | 15% |

**评分标准**：
- 9-10分：接近真人录制，高度自然
- 7-8分：良好，偶有机器感但整体流畅
- 5-6分：合格，可识别为AI合成但可接受
- <5分：不合格，明显机器感

### 3. 系统性能 (System Performance)

评估系统的运行效率：

| 指标 | 说明 | 优秀标准 |
|-----|------|---------|
| **生成速度** | 完整播客生成耗时 | <3分钟/5分钟播客 |
| **成功率** | 批量生成的成功率 | >95% |
| **稳定性** | 连续运行的稳定性 | 无崩溃 |
| **资源占用** | CPU/内存/磁盘使用 | 合理范围 |

### 4. 创新性 (Innovation)

评估技术创新和应用价值：

- **多模态融合**：LLM + TTS + RAG的集成程度
- **自动化程度**：从输入到输出的自动化水平
- **可扩展性**：支持多场景、多引擎的灵活性
- **应用价值**：在实际业务中的应用潜力

---

## 演示程序使用

### 1. 批量生成演示 (batch_demo.py)

**功能**：批量生成多个播客，展示系统的规模化处理能力。

**使用方法**：

```bash
# 基础使用
python examples/batch_demo.py

# 自定义输出目录
python examples/batch_demo.py --output my_output

# 使用自定义配置文件
python examples/batch_demo.py --config configs/test_scenarios.json
```

**自定义配置文件格式**：

```json
[
  {
    "topic": "您的主题",
    "atmosphere": "serious_deep",
    "target_duration": "3分钟",
    "language_style": "formal",
    "characters": [
      {
        "name": "角色1",
        "persona": "角色描述",
        "core_viewpoint": "核心观点",
        "voice_description": "longwan_v2",
        "tone_description": "语气描述"
      }
    ]
  }
]
```

**输出文件**：

```
output/batch_demo/
├── batch_report.json          # 批量生成汇总报告
├── podcast_<task_id>.mp3      # 生成的音频文件
└── script_<task_id>.json      # 对话剧本
```

### 2. 批量评估演示 (evaluation_demo.py)

**功能**：对生成的播客进行质量评估，生成详细报告。

**使用方法**：

```bash
# 从批量生成报告中评估
python examples/evaluation_demo.py --report output/batch_demo/batch_report.json

# 直接指定任务ID
python examples/evaluation_demo.py --task-ids abc123 def456
```

**输出文件**：

```
output/evaluation/
├── evaluation_report.json     # 详细评估报告
└── evaluation_summary.json    # 汇总统计报告
```

### 3. 交互式演示 (interactive_demo.py)

**功能**：提供交互式命令行界面，快速测试单个播客生成。

**使用方法**：

```bash
python examples/interactive_demo.py
```

**交互流程**：

```
1. 选择预设场景 (1-5) 或自定义 (6)
2. 确认配置
3. 等待生成完成
4. 自动下载音频和剧本
5. 查看剧本预览
```

**适用场景**：
- 快速测试单个场景
- 演示系统功能
- 调试和验证

---

## 评估建议

### 推荐评估流程

1. **功能验证** (15分钟)
   - 启动服务，检查基础功能
   - 使用交互式演示生成1个播客
   - 验证音频质量和剧本内容

2. **批量测试** (30分钟)
   - 运行批量生成演示，生成3-5个播客
   - 观察生成速度和成功率
   - 检查不同场景下的表现

3. **质量评估** (20分钟)
   - 运行批量评估程序
   - 查看评估报告和统计数据
   - 对比不同场景的质量差异

4. **深度体验** (15分钟)
   - 尝试自定义配置
   - 测试边界情况
   - 评估系统稳定性

**总计时间**: 约80分钟

### 评估要点

✅ **必查项**：
- [ ] 服务能否正常启动
- [ ] 批量生成成功率是否>90%
- [ ] 音频质量是否达到可用水平
- [ ] 剧本内容是否符合主题
- [ ] 系统是否稳定运行

⭐ **加分项**：
- [ ] 内容创新性和深度
- [ ] 音频接近真人的自然度
- [ ] 生成速度是否足够快
- [ ] 支持的场景多样性
- [ ] 代码质量和文档完整性

---

## 常见问题

### Q1: 服务启动失败怎么办？

**A**: 检查以下几点：
1. Python版本是否>=3.11
2. 依赖是否完整安装：`pip install -r requirements.txt`
3. 环境变量是否正确配置 (`.env`文件)
4. 端口8000是否被占用：`lsof -i :8000` (Linux/Mac)

### Q2: 生成失败，提示API错误？

**A**: 
1. 检查API密钥是否正确配置
2. 确认API账户有足够的额度
3. 检查网络连接和代理设置
4. 查看服务端日志获取详细错误信息

### Q3: 音频质量不理想？

**A**:
1. 确认TTS引擎配置正确（推荐使用CosyVoice）
2. 检查音色选择是否合适
3. 确认FFmpeg正确安装
4. 调整音频后处理参数 (`.env`中的AUDIO_*配置)

### Q4: 批量生成速度慢？

**A**:
1. 这是正常现象，每个5分钟播客需要2-5分钟生成
2. 可以减少目标时长（如改为3分钟）加快测试
3. 确保网络连接稳定（API调用需要网络）
4. 考虑并发优化（需修改代码）

### Q5: 如何自定义评估维度？

**A**: 
1. 编辑 `evaluation_demo.py`
2. 修改评分权重和计算逻辑
3. 添加自定义评估指标
4. 参考 `src/backend/app/services/quality_assessment_service.py`

### Q6: 评估报告如何解读？

**A**: 
- **evaluation_report.json**: 包含每个任务的详细评分和分析
- **evaluation_summary.json**: 汇总统计，包括平均分、分数分布、改进建议
- **batch_report.json**: 批量生成的任务状态和基本信息

重点关注：
- `overall_score`: 综合评分（0-10）
- `content_quality`: 内容质量
- `audio_quality`: 音频质量
- `recommendations`: 系统生成的改进建议

---

## 技术支持

### 文档资源

- **README.md**: 完整的使用文档
- **TECHNICAL_REPORT.md**: 技术原理和架构说明
- **RESEARCH_METHODOLOGY.md**: 研究方法论详细说明
- **API文档**: http://localhost:8000/docs

### 联系方式

如遇到问题，请：
1. 查看项目文档和README
2. 检查服务端日志
3. 提交Issue到代码仓库

---

## 评估报告模板

评委可以参考以下模板撰写评估报告：

### 基本信息
- 评估日期：________
- 评估人员：________
- 测试环境：________

### 功能评估
| 功能项 | 是否正常 | 评分(1-10) | 备注 |
|-------|---------|-----------|------|
| 服务启动 | ☐ | ___ | |
| 单个生成 | ☐ | ___ | |
| 批量生成 | ☐ | ___ | |
| 质量评估 | ☐ | ___ | |
| Web界面 | ☐ | ___ | |

### 质量评估
| 维度 | 评分(1-10) | 说明 |
|-----|-----------|------|
| 内容质量 | ___ | |
| 音频质量 | ___ | |
| 系统性能 | ___ | |
| 技术创新 | ___ | |
| 应用价值 | ___ | |

### 综合评价
- **优点**：
  - 
  - 

- **不足**：
  - 
  - 

- **改进建议**：
  - 
  - 

- **总体评分**: ___ / 10

---

**祝评估顺利！** 🎉
