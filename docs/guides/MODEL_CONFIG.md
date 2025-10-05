# AI模型配置文档

## 模型架构更新

项目已更新为多模型架构，针对不同任务使用最适合的AI模型：

### 1. 素材分析模型 - Gemini 2.5 Flash

**用途：** 分析用户提供的背景素材，提取核心要点
**优势：**
- 快速响应
- 多模态支持
- 强大的理解能力

**配置变量：**
```env
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_BASE_URL=https://generativelanguage.googleapis.com/v1beta
GEMINI_MODEL=gemini-2.5-flash
```

### 2. 剧本生成模型 - DeepSeek V3.1

**用途：** 基于素材分析结果生成高质量播客剧本
**优势：**
- 中文生成能力强
- 创意表达丰富
- 长文本生成稳定

**配置变量：**
```env
DEEPSEEK_API_KEY=your_deepseek_api_key_here
DEEPSEEK_BASE_URL=https://api.deepseek.com/v1
DEEPSEEK_MODEL=deepseek-v3-chat
```

### 3. TTS（暂未确定）

**配置变量：**
```env
TTS_API_KEY=your_tts_api_key_here
TTS_MODEL=tts-1
```

## 工作流程

1. **素材分析：** Gemini 2.5 Flash 分析用户提供的背景素材
2. **剧本生成：** DeepSeek V3.1 基于分析结果生成播客剧本
3. **音频合成：** TTS服务将剧本转换为音频

## 代码更改摘要

### 1. 配置文件更新
- `.env.example` 和 `.env` 添加了新的API配置
- `backend/app/core/config.py` 增加了模型配置字段

### 2. 依赖包更新
- `requirements.txt` 添加了 `google-generativeai==0.8.0`

### 3. 代码适配
- `backend/app/services/script_generator.py` 重构为多模型架构
  - `analyze_materials()` 使用 Gemini API
  - `generate_script()` 使用 DeepSeek API

## 配置验证

所有配置已通过语法检查和加载测试，确保：
- ✅ 语法正确
- ✅ 配置变量正确加载
- ✅ 模型客户端正确初始化

## 使用建议

1. **API密钥：** 请在实际部署前替换测试密钥为真实的API密钥
2. **网络配置：** 确保服务器能访问对应的API服务
3. **错误处理：** 当前已包含基本的错误处理和降级机制