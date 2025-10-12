# AliCloud CosyVoice TTS 集成说明

## 概述

CosyVoice 是阿里云百炼平台提供的高质量中文语音合成服务，具有以下特点：

- 🎯 **专为中文优化**：发音准确、自然流畅
- 🚀 **稳定可靠**：国内服务，低延迟高可用
- 🎭 **多种音色**：支持男声、女声多种风格
- 💰 **按需计费**：根据实际使用量付费

## 配置步骤

### 1. 获取 API Key

访问阿里云百炼控制台：https://dashscope.console.aliyun.com/

1. 登录阿里云账号
2. 开通 DashScope 服务
3. 创建 API Key 并复制

### 2. 安装依赖

```bash
pip install dashscope>=1.14.0
```

### 3. 配置环境变量

在 `.env` 文件中添加以下配置：

```bash
# TTS引擎选择
TTS_ENGINE=cosyvoice

# AliCloud CosyVoice配置
ALICLOUD_DASHSCOPE_API_KEY=sk-xxxxxxxxxxxxxxxx  # 替换为你的API Key
COSYVOICE_MODEL=cosyvoice-v2
COSYVOICE_DEFAULT_VOICE=longxiaochun_v2
```

### 4. 启动服务

```bash
cd src/backend
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## 可用音色

CosyVoice 提供多种预置音色：

### 男声音色
- `longwan_v2` - 标准男声，沉稳大气
- `longyuan_v2` - 浑厚男声，富有磁性

### 女声音色
- `longxiaochun_v2` - 标准女声（默认），清晰自然
- `longxiaoxia_v2` - 温暖女声，亲和力强
- `longxiaoyuan_v2` - 活力女声，朝气蓬勃

## 音色映射

系统支持自动映射中文描述到具体音色：

| 描述关键词 | 映射音色 |
|-----------|---------|
| 沉稳、标准、男声 | longwan_v2 |
| 浑厚、有磁性 | longyuan_v2 |
| 清脆、女声、知性 | longxiaochun_v2 |
| 温暖 | longxiaoxia_v2 |
| 有活力 | longxiaoyuan_v2 |

### 角色配置示例

```python
characters = [
    {
        "name": "主持人",
        "voice_description": "沉稳"  # 自动映射到 longwan_v2
    },
    {
        "name": "嘉宾",
        "voice_description": "温暖"  # 自动映射到 longxiaoxia_v2
    }
]
```

## 音频输出

生成的播客音频将保存在：
```
data/output/audio/{task_id}/podcast_{task_id}.mp3
```

## 切换 TTS 引擎

如需切换回其他引擎，修改 `.env` 中的 `TTS_ENGINE`：

```bash
# 切换到 IndexTTS-2 Gradio
TTS_ENGINE=indextts2_gradio

# 切换到 Qwen3-TTS
TTS_ENGINE=qwen3_tts

# 切换到 OpenAI TTS
TTS_ENGINE=openai
```

## 回退机制

如果 CosyVoice 服务不可用（API Key 未配置或服务异常），系统会自动回退到其他 TTS 引擎：

```
CosyVoice → Qwen3-TTS → NihalGazi-TTS → IndexTTS-2 Gradio → OpenAI TTS
```

## 健康检查

访问以下端点检查 CosyVoice 服务状态：

```bash
curl http://localhost:8000/api/v1/tts/status
```

返回示例：
```json
{
  "current_engine": "cosyvoice",
  "service_type": "AliCloudCosyVoiceService",
  "status": "healthy",
  "service": "AliCloud CosyVoice",
  "model": "cosyvoice-v2",
  "default_voice": "longxiaochun_v2"
}
```

## 常见问题

### Q: 如何降低成本？
A: CosyVoice 按字符数计费，可以：
- 精简播客文本内容
- 使用本地 TTS 引擎（IndexTTS-2）进行测试
- 只在生产环境使用 CosyVoice

### Q: 支持自定义音色吗？
A: CosyVoice-v2 支持音色克隆功能，需要在阿里云控制台训练自定义音色。

### Q: 音频质量如何？
A: CosyVoice 提供 192kbps MP3 输出，音质清晰自然，适合专业播客制作。

### Q: 合成速度如何？
A: 国内服务，延迟低，通常几秒内即可合成完成。具体速度取决于文本长度。

## 技术支持

- 阿里云百炼文档：https://help.aliyun.com/zh/model-studio/
- DashScope API 参考：https://dashscope.aliyuncs.com/
- 项目 Issue：https://github.com/your-repo/issues

## 更新日志

### v1.0.0 (2025-01-XX)
- ✅ 集成 CosyVoice-v2 模型
- ✅ 支持多种预置音色
- ✅ 自动音色映射
- ✅ 健康检查和回退机制
- ✅ 本地音频保存
