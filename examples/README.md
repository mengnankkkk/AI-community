# 演示程序使用说明

本目录包含三个专业的演示程序，用于展示AI虚拟播客工作室的功能和性能。

---

## 📋 程序列表

### 1. batch_demo.py - 批量生成演示

**功能**: 批量生成多个播客，展示系统的规模化处理能力。

**适用场景**:
- 评委批量评估模型效果
- 性能压力测试
- 批量内容生产

**使用方法**:

```bash
# 基础使用 - 使用预设的3个测试场景
python examples/batch_demo.py

# 自定义输出目录
python examples/batch_demo.py --output output/my_test

# 使用自定义配置文件
python examples/batch_demo.py --config my_scenarios.json

# 指定API地址
python examples/batch_demo.py --api http://your-server:8000
```

**参数说明**:
- `--api`: API服务地址 (默认: http://localhost:8000)
- `--output`: 输出目录 (默认: output/batch_demo)
- `--config`: 自定义配置文件路径 (JSON格式)

**预设场景**:
1. 科技话题 - AI技术发展（严肃深度，正式风格）
2. 教育话题 - 在线教育未来（轻松幽默，口语化）
3. 健康话题 - 健康生活方式（温暖治愈，口语化）

**输出文件**:
```
output/batch_demo/
├── batch_report.json          # 批量生成汇总报告
│   ├── timestamp              # 生成时间
│   ├── total_tasks            # 总任务数
│   ├── successful             # 成功数量
│   ├── failed                 # 失败数量
│   └── results[]              # 详细结果列表
├── podcast_<task_id>.mp3      # 生成的音频文件
└── script_<task_id>.json      # 对话剧本
```

---

### 2. evaluation_demo.py - 批量评估程序

**功能**: 对生成的播客进行质量评估，生成详细的评估报告。

**适用场景**:
- 质量评估和打分
- 性能分析
- 对比测试

**使用方法**:

```bash
# 从批量生成报告中提取任务并评估
python examples/evaluation_demo.py --report output/batch_demo/batch_report.json

# 直接指定任务ID
python examples/evaluation_demo.py --task-ids abc123 def456 ghi789

# 自定义输出目录
python examples/evaluation_demo.py --report output/batch_demo/batch_report.json \
                                   --output output/my_evaluation

# 指定API地址
python examples/evaluation_demo.py --api http://your-server:8000 \
                                   --report output/batch_demo/batch_report.json
```

**参数说明**:
- `--api`: API服务地址 (默认: http://localhost:8000)
- `--output`: 输出目录 (默认: output/evaluation)
- `--task-ids`: 要评估的任务ID列表
- `--report`: 批量生成报告路径 (从中提取task_id)

**评估维度**:
- **内容质量** (50%): 主题相关性、逻辑连贯性、信息密度、角色一致性
- **音频质量** (30%): 音质、响度平衡、韵律自然度、背景音乐
- **系统性能** (20%): 生成速度、成功率、资源占用

**输出文件**:
```
output/evaluation/
├── evaluation_report.json     # 详细评估报告
│   └── 每个任务的完整评分和分析
└── evaluation_summary.json    # 汇总统计报告
    ├── average_scores         # 平均分数
    ├── score_distribution     # 分数分布
    └── recommendations        # 改进建议
```

---

### 3. interactive_demo.py - 交互式演示

**功能**: 提供交互式命令行界面，快速测试单个播客生成。

**适用场景**:
- 功能演示
- 快速测试
- 开发调试

**使用方法**:

```bash
python examples/interactive_demo.py

# 指定API地址
python examples/interactive_demo.py --api http://your-server:8000
```

**预设场景**:
1. 科技前沿 - AI技术发展讨论
2. 教育话题 - 在线教育的未来
3. 健康生活 - 健康饮食与运动
4. 商业洞察 - 创业与投资机遇
5. 文化艺术 - 传统文化的现代传承
6. 自定义 - 输入自己的话题

**交互流程**:
```
1. 选择预设场景 (1-5) 或自定义 (6)
   ↓
2. 确认配置信息
   ↓
3. 等待生成完成（实时进度显示）
   ↓
4. 自动下载音频和剧本
   ↓
5. 查看剧本预览（前3段对话）
   ↓
6. 选择继续生成或退出
```

**输出文件**:
```
output/interactive_demo/
├── podcast_<task_id>.mp3      # 生成的音频文件
└── script_<task_id>.json      # 对话剧本
```

---

## 🚀 快速开始

### 前置条件

1. **启动服务**:
   ```bash
   python run_server.py
   ```

2. **确认服务运行**:
   访问 http://localhost:8000/health

### 完整评估流程（推荐）

**第一步：批量生成 (15-25分钟)**

```bash
python examples/batch_demo.py
```

等待生成完成，将看到类似输出：

```
🚀 批量播客生成演示
=============================================================
📊 任务数量: 3
📁 输出目录: output/batch_demo
⏰ 开始时间: 2024-01-15 10:30:00
=============================================================

[1/3] 提交任务: 人工智能的未来发展趋势
  ✅ 任务创建成功: abc123...
  ✅ 生成成功 (耗时: 165.3s)
  💾 已保存: output/batch_demo/podcast_abc123.mp3 (2.45 MB)

✅ 成功: 3 / 3
📊 成功率: 100.0%
⏱️  平均生成时间: 165.3s
💾 总音频大小: 7.35 MB
```

**第二步：批量评估 (10-20分钟)**

```bash
python examples/evaluation_demo.py --report output/batch_demo/batch_report.json
```

等待评估完成，将看到：

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

📊 分数分布:
  • excellent (9-10分): 2 (66.7%)
  • good (7-8分): 1 (33.3%)
```

**第三步：查看结果**

```bash
# 查看评估摘要
cat output/evaluation/evaluation_summary.json

# 播放生成的音频
# Windows
start output/batch_demo/podcast_*.mp3

# Linux
vlc output/batch_demo/podcast_*.mp3

# Mac
open output/batch_demo/podcast_*.mp3
```

---

## 📝 自定义配置

### 创建自定义测试场景

创建 `my_test_scenarios.json` 文件：

```json
[
  {
    "topic": "您的测试主题",
    "title": "播客标题（可选）",
    "atmosphere": "serious_deep",
    "target_duration": "3分钟",
    "language_style": "formal",
    "characters": [
      {
        "name": "角色1",
        "persona": "角色身份描述",
        "core_viewpoint": "角色核心观点",
        "voice_description": "longwan_v2",
        "tone_description": "专业、理性、略带热情",
        "language_habits": "喜欢用类比，解释问题条理清晰",
        "backstory": "背景故事（可选）"
      },
      {
        "name": "角色2",
        "persona": "角色身份描述",
        "core_viewpoint": "角色核心观点",
        "voice_description": "longxiaochun_v2",
        "tone_description": "客观、好奇、富有同理心"
      }
    ],
    "background_materials": "可选的背景资料文本"
  }
]
```

### 配置参数说明

**atmosphere (讨论氛围)**:
- `relaxed_humorous`: 轻松幽默
- `serious_deep`: 严肃深度
- `heated_debate`: 激烈辩论
- `warm_healing`: 温暖治愈

**language_style (语言风格)**:
- `colloquial`: 口语化
- `formal`: 正式
- `academic`: 学术
- `internet`: 网络流行语

**voice_description (音色)**:
- `longwan_v2`: 龙湾（男声-标准）- 沉稳大气
- `longyuan_v2`: 龙渊（男声-浑厚）- 富有磁性
- `longxiaochun_v2`: 龙小春（女声-标准）- 清晰自然
- `longxiaoxia_v2`: 龙小夏（女声-温暖）- 亲和力强
- `longxiaoyuan_v2`: 龙小媛（女声-活力）- 朝气蓬勃

---

## 🐛 故障排查

### 问题1: 服务连接失败

**错误信息**: `❌ 服务器未响应`

**解决方案**:
1. 确认服务已启动: `python run_server.py`
2. 检查端口占用: `lsof -i :8000` (Linux/Mac)
3. 确认API地址正确: `--api http://localhost:8000`

### 问题2: 生成失败

**错误信息**: `❌ 生成失败: API Error`

**解决方案**:
1. 检查API密钥配置 (`.env`文件)
2. 确认API账户有足够额度
3. 检查网络连接
4. 查看服务端日志

### 问题3: 评估程序无法找到任务

**错误信息**: `❌ 报告中未找到已完成的任务`

**解决方案**:
1. 确认批量生成已完成
2. 检查报告文件路径是否正确
3. 确认任务状态为"completed"

### 问题4: 音频文件无法播放

**解决方案**:
1. 检查文件是否存在
2. 确认文件大小正常（>100KB）
3. 使用专业播放器（VLC、foobar2000等）
4. 检查FFmpeg是否正确安装

---

## 📊 输出文件说明

### batch_report.json 结构

```json
{
  "timestamp": "2024-01-15T10:30:00",
  "total_tasks": 3,
  "successful": 3,
  "failed": 0,
  "results": [
    {
      "task_id": "abc123...",
      "topic": "人工智能的未来发展趋势",
      "status": "completed",
      "generation_time": 165.3,
      "audio_path": "output/batch_demo/podcast_abc123.mp3",
      "audio_size": 2.45,
      "script_path": "output/batch_demo/script_abc123.json"
    }
  ]
}
```

### evaluation_summary.json 结构

```json
{
  "timestamp": "2024-01-15T11:00:00",
  "total_evaluated": 3,
  "successful_evaluations": 3,
  "failed_evaluations": 0,
  "average_scores": {
    "overall": 8.50,
    "content_quality": 8.30,
    "audio_quality": 8.70
  },
  "score_distribution": {
    "excellent (9-10分)": 2,
    "good (7-8分)": 1,
    "acceptable (5-6分)": 0,
    "poor (<5分)": 0
  },
  "recommendations": [
    "优秀：整体质量优秀，可直接用于生产环境"
  ]
}
```

---

## 💡 最佳实践

### 评估建议

1. **先小规模测试**: 使用交互式演示生成1-2个播客，验证配置
2. **再批量生成**: 使用batch_demo批量生成3-5个播客
3. **及时评估**: 生成完成后立即评估，趁热打铁
4. **记录问题**: 遇到问题及时记录，便于后续改进

### 性能优化

1. **控制并发数**: 避免同时提交过多任务
2. **选择合适时长**: 3-5分钟的播客生成速度最优
3. **使用缓存**: 相同配置会复用缓存结果
4. **网络稳定**: 确保API调用网络稳定

### 数据管理

1. **定期清理**: 删除不需要的音频文件释放空间
2. **备份重要数据**: 保存评估报告和优秀样本
3. **版本管理**: 对不同版本的测试结果分目录存储

---

## 📚 相关文档

- **[README.md](../README.md)** - 项目主文档
- **[评委评估指南](../docs/EVALUATION_GUIDE.md)** - 完整评估流程
- **[研究方法论](../docs/RESEARCH_METHODOLOGY.md)** - 技术原理详解
- **[技术报告](../TECHNICAL_REPORT.md)** - 系统架构和创新点

---

## 🤝 技术支持

遇到问题？
1. 查看 [评委评估指南](../docs/EVALUATION_GUIDE.md) 的常见问题部分
2. 查看服务端日志排查错误
3. 提交Issue到项目仓库

---

**祝评估顺利！** 🎉
