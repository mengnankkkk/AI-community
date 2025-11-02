# 模型调用与使用说明

本文档详细说明AI虚拟播客工作室中使用的各类模型的配置、调用方法和最佳实践。

---

## 📋 目录

1. [模型概览](#模型概览)
2. [大语言模型（LLM）](#大语言模型llm)
3. [文本转语音（TTS）](#文本转语音tts)
4. [嵌入模型（Embeddings）](#嵌入模型embeddings)
5. [模型性能对比](#模型性能对比)
6. [故障排查](#故障排查)

---

## 🎯 模型概览

系统集成了多种AI模型，实现端到端的播客生成流程：

```
输入主题
   ↓
[LLM模型] → 生成剧本
   ↓
[Embeddings] → 知识检索（可选）
   ↓
[TTS模型] → 语音合成
   ↓
[音频处理] → 后期制作
   ↓
输出音频
```

### 模型分类

| 模型类型 | 用途 | 支持的提供商 | 必需性 |
|---------|------|-------------|--------|
| LLM | 剧本生成、对话创作 | OpenAI、Claude、Qwen、Hunyuan | 必需 |
| TTS | 文本转语音 | CosyVoice、OpenAI、IndexTTS2、Qwen3、Nihal | 必需 |
| Embeddings | 知识库向量化 | OpenAI、Hunyuan | 可选（启用RAG时必需） |
| ASR | 语音识别（音色上传） | OpenAI Whisper、AliCloud | 可选 |

---

## 🧠 大语言模型（LLM）

### 支持的模型

#### 1. OpenAI GPT系列

**GPT-4o（推荐）**
```env
LLM_PROVIDER=openai
LLM_MODEL=gpt-4o
OPENAI_API_KEY=your_api_key
OPENAI_BASE_URL=https://api.openai.com/v1
```

**特点：**
- ✅ 对话质量最高，逻辑连贯性强
- ✅ 角色一致性好
- ✅ 支持长上下文（128K tokens）
- ⚠️ 成本较高（$5/1M输入tokens）

**适用场景：**
- 专业级播客生成
- 复杂主题讨论
- 多角色对话

**GPT-3.5-turbo**
```env
LLM_MODEL=gpt-3.5-turbo
```

**特点：**
- ✅ 成本低（$0.5/1M输入tokens）
- ✅ 响应速度快
- ⚠️ 质量略低于GPT-4
- ⚠️ 上下文窗口较小（16K tokens）

**适用场景：**
- 快速测试
- 简单主题播客
- 成本敏感场景

#### 2. Anthropic Claude系列

**Claude 3.5 Sonnet（推荐）**
```env
LLM_PROVIDER=anthropic
LLM_MODEL=claude-3-5-sonnet-20241022
ANTHROPIC_API_KEY=your_api_key
```

**特点：**
- ✅ 对话自然度高
- ✅ 上下文理解能力强（200K tokens）
- ✅ 安全性和伦理考量好
- ⚠️ API访问受地区限制

**适用场景：**
- 长篇播客（>10分钟）
- 深度主题讨论
- 需要大量背景知识的场景

#### 3. 阿里云通义千问（Qwen）

**Qwen-Max**
```env
LLM_PROVIDER=qwen
LLM_MODEL=qwen-max
DASHSCOPE_API_KEY=your_api_key
```

**特点：**
- ✅ 中文理解能力强
- ✅ 国内访问速度快
- ✅ 成本较低
- ⚠️ 英文能力相对较弱

**适用场景：**
- 中文播客生成
- 国内部署
- 预算受限

#### 4. 腾讯混元（Hunyuan）

**hunyuan-pro**
```env
LLM_PROVIDER=hunyuan
LLM_MODEL=hunyuan-pro
HUNYUAN_API_KEY=your_api_key
```

**特点：**
- ✅ 中文原生支持
- ✅ 响应稳定
- ✅ 价格亲民

**适用场景：**
- 中文内容创作
- 企业内部部署

### LLM配置参数

在 `config/llm_config.yaml` 或通过环境变量配置：

```yaml
llm:
  provider: openai  # openai, anthropic, qwen, hunyuan
  model: gpt-4o
  temperature: 0.8  # 0.0-2.0，越高越随机
  top_p: 0.9        # 0.0-1.0，控制多样性
  max_tokens: 4000  # 最大生成长度
  frequency_penalty: 0.3  # 减少重复
  presence_penalty: 0.3   # 鼓励新话题
```

**参数说明：**

| 参数 | 作用 | 推荐值 | 说明 |
|-----|------|-------|------|
| temperature | 控制随机性 | 0.7-0.9 | 对话生成建议较高，确保自然多样 |
| top_p | 核采样 | 0.9 | 与temperature配合使用 |
| max_tokens | 最大输出 | 3000-4000 | 根据目标时长调整 |
| frequency_penalty | 频率惩罚 | 0.2-0.4 | 避免重复词汇 |
| presence_penalty | 存在惩罚 | 0.2-0.4 | 鼓励引入新概念 |

### 调用示例

**Python代码：**

```python
from src.backend.services.llm_service import LLMService

# 初始化LLM服务
llm_service = LLMService()

# 生成对话
prompt = """
你是一个专业的播客剧本作家。请根据以下信息生成一段对话：

主题：人工智能的未来
角色1：李明，AI研究员，认为AI将深刻改变社会
角色2：王芳，科技记者，关注AI伦理问题

生成2-3轮自然的对话。
"""

response = llm_service.generate(
    prompt=prompt,
    temperature=0.8,
    max_tokens=2000
)

print(response)
```

**API调用：**

```bash
curl -X POST "http://localhost:8000/api/v1/podcast/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "custom_form": {
      "topic": "人工智能的未来",
      "characters": [
        {
          "name": "李明",
          "persona": "AI研究员",
          "core_viewpoint": "AI将深刻改变社会"
        }
      ]
    }
  }'
```

### 性能优化

**1. 使用流式输出**
```python
for chunk in llm_service.stream_generate(prompt):
    print(chunk, end='', flush=True)
```

**2. 批量处理**
```python
prompts = [prompt1, prompt2, prompt3]
responses = llm_service.batch_generate(prompts)
```

**3. 缓存常用Prompt**
```python
llm_service.cache_prompt(
    key="podcast_template",
    prompt=template
)
```

---

## 🎤 文本转语音（TTS）

### 支持的TTS引擎

#### 1. 阿里云CosyVoice（推荐）

**配置：**
```env
TTS_ENGINE=cosyvoice
ALICLOUD_DASHSCOPE_API_KEY=your_api_key
COSYVOICE_MODEL=cosyvoice-v2
COSYVOICE_DEFAULT_VOICE=longxiaochun_v2
```

**可用音色：**

| 音色ID | 类型 | 特点 | 适用角色 |
|--------|------|------|---------|
| longwan_v2 | 男声 | 沉稳、成熟 | 专家、学者、企业家 |
| longyuan_v2 | 男声 | 年轻、活力 | 主持人、记者、创业者 |
| longxiaochun_v2 | 女声 | 温柔、亲切 | 教师、医生、咨询师 |
| longxiaoyuan_v2 | 女声 | 活泼、开朗 | 娱乐主持、时尚博主 |
| longshui_v2 | 女声 | 知性、专业 | 商业分析师、科技记者 |

**调用示例：**
```python
from src.backend.services.tts_service import TTSService

tts = TTSService()
audio_data = tts.synthesize(
    text="欢迎来到AI播客",
    voice="longxiaochun_v2",
    emotion="neutral",  # neutral, happy, sad, angry
    speed=1.0,          # 0.5-2.0
    volume=1.0          # 0.0-2.0
)
```

**性能指标：**
- 响应时间：0.5-1.5秒（100字）
- 音质评分（MOS）：4.2/5.0
- 成本：¥0.3/1000字符
- 并发限制：10 QPS

#### 2. OpenAI TTS

**配置：**
```env
TTS_ENGINE=openai
OPENAI_API_KEY=your_api_key
TTS_VOICE=nova  # alloy, echo, fable, onyx, nova, shimmer
```

**可用音色：**
- **alloy**：中性，平衡
- **echo**：男声，温暖
- **fable**：英式口音
- **onyx**：男声，深沉
- **nova**：女声，友好
- **shimmer**：女声，温柔

**调用示例：**
```python
audio_data = tts.synthesize(
    text="Welcome to AI Podcast",
    voice="nova",
    model="tts-1-hd",  # tts-1 或 tts-1-hd
    speed=1.0
)
```

**性能指标：**
- 响应时间：1-2秒（100字）
- 音质评分（MOS）：4.4/5.0
- 成本：$15/1M字符
- 支持语言：多语言（50+）

#### 3. IndexTTS2 Gradio（本地）

**配置：**
```env
TTS_ENGINE=indextts2_gradio
INDEXTTS2_GRADIO_URL=http://localhost:7860
```

**特点：**
- ✅ 支持音色克隆
- ✅ 本地部署，数据安全
- ✅ 免费使用
- ⚠️ 需要GPU（推荐4GB+显存）

**音色克隆：**
```python
# 上传参考音频
tts.upload_reference_audio(
    audio_path="path/to/reference.wav",
    text="参考音频的文本内容"
)

# 使用克隆的音色
audio_data = tts.synthesize(
    text="新的文本内容",
    voice="custom_voice_id"
)
```

**性能指标：**
- 响应时间：2-5秒（100字，取决于GPU）
- 音质评分（MOS）：3.9/5.0
- 成本：免费（需GPU资源）

#### 4. Qwen3 TTS

**配置：**
```env
TTS_ENGINE=qwen3
DASHSCOPE_API_KEY=your_api_key
```

**特点：**
- ✅ 中文表现好
- ✅ 国内访问快
- ✅ 支持多种情感

**调用示例：**
```python
audio_data = tts.synthesize(
    text="这是测试文本",
    voice="qwen_female_1",
    emotion="cheerful"
)
```

#### 5. Nihal TTS（开源）

**配置：**
```env
TTS_ENGINE=nihal
NIHAL_MODEL_PATH=models/nihal_tts
```

**特点：**
- ✅ 完全开源
- ✅ 可自定义训练
- ✅ 支持多语言
- ⚠️ 音质略低

### TTS统一接口

系统提供统一的TTS接口，自动路由到配置的引擎：

```python
class TTSService:
    def synthesize(
        self,
        text: str,
        voice: str,
        emotion: str = "neutral",
        speed: float = 1.0,
        volume: float = 1.0,
        **kwargs
    ) -> bytes:
        """
        统一的TTS合成接口
        
        Args:
            text: 要合成的文本
            voice: 音色ID（自动映射到对应引擎）
            emotion: 情感（neutral, happy, sad, angry等）
            speed: 语速（0.5-2.0）
            volume: 音量（0.0-2.0）
            
        Returns:
            bytes: 音频数据（WAV格式）
        """
        pass
```

### 音色映射

系统维护一个统一的音色映射表，自动转换到不同引擎：

```python
VOICE_MAPPING = {
    "沉稳男声": {
        "cosyvoice": "longwan_v2",
        "openai": "onyx",
        "indextts2": "male_voice_1"
    },
    "活力女声": {
        "cosyvoice": "longxiaoyuan_v2",
        "openai": "nova",
        "indextts2": "female_voice_1"
    }
}
```

### 批量合成优化

**并发调用：**
```python
import asyncio

async def batch_synthesize(texts, voice):
    tasks = [
        tts.async_synthesize(text, voice)
        for text in texts
    ]
    return await asyncio.gather(*tasks)

# 使用
audio_segments = asyncio.run(
    batch_synthesize(dialogue_texts, "longxiaochun_v2")
)
```

**性能提升：**
- 串行：150秒（30段，每段5秒）
- 并发：60秒（同样30段）
- 提升：2.5倍

---

## 🔍 嵌入模型（Embeddings）

用于RAG知识库的向量化和检索。

### 支持的模型

#### 1. OpenAI Embeddings

**配置：**
```env
RAG_EMBEDDING_PROVIDER=openai
RAG_EMBEDDING_MODEL=text-embedding-3-small
OPENAI_API_KEY=your_api_key
```

**模型选择：**
- **text-embedding-3-small**：1536维，性价比高
- **text-embedding-3-large**：3072维，精度更高
- **text-embedding-ada-002**：1536维，旧版本

**性能指标：**
- 速度：1000 tokens/秒
- 成本：$0.02/1M tokens（small）
- 精度：MTEB得分62.3

#### 2. 腾讯混元Embeddings

**配置：**
```env
RAG_EMBEDDING_PROVIDER=hunyuan
RAG_EMBEDDING_MODEL=hunyuan-embedding
HUNYUAN_API_KEY=your_api_key
```

**特点：**
- ✅ 中文优化
- ✅ 国内访问快
- ✅ 成本低

**性能指标：**
- 速度：800 tokens/秒
- 成本：¥0.1/1M tokens
- 维度：1024

### 使用示例

**文档向量化：**
```python
from src.backend.services.rag_service import RAGService

rag = RAGService()

# 添加文档到知识库
rag.add_documents(
    texts=[
        "人工智能是计算机科学的一个分支...",
        "机器学习是实现人工智能的一种方法..."
    ],
    metadatas=[
        {"source": "doc1.pdf", "page": 1},
        {"source": "doc1.pdf", "page": 2}
    ]
)
```

**知识检索：**
```python
# 查询相关知识
results = rag.search(
    query="什么是机器学习",
    top_k=5,
    filter={"source": "doc1.pdf"}
)

for result in results:
    print(f"相关度: {result.score}")
    print(f"内容: {result.text}")
    print(f"来源: {result.metadata}")
```

---

## 📊 模型性能对比

### LLM对比

| 模型 | 质量评分 | 速度 | 成本（$） | 中文能力 | 推荐度 |
|-----|---------|------|----------|---------|--------|
| GPT-4o | 9.2/10 | 快 | 5.00/1M | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| GPT-3.5-turbo | 7.8/10 | 很快 | 0.50/1M | ⭐⭐⭐ | ⭐⭐⭐⭐ |
| Claude 3.5 | 9.0/10 | 快 | 3.00/1M | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| Qwen-Max | 8.3/10 | 快 | 0.30/1M | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| Hunyuan-Pro | 8.0/10 | 快 | 0.20/1M | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |

### TTS对比

| 引擎 | MOS评分 | 速度 | 成本 | 音色数 | 推荐度 |
|-----|---------|------|------|--------|--------|
| CosyVoice | 4.2/5.0 | ⭐⭐⭐⭐ | ¥0.3/1K字 | 5 | ⭐⭐⭐⭐⭐ |
| OpenAI TTS | 4.4/5.0 | ⭐⭐⭐⭐⭐ | $15/1M字 | 6 | ⭐⭐⭐⭐ |
| IndexTTS2 | 3.9/5.0 | ⭐⭐⭐ | 免费 | 无限 | ⭐⭐⭐⭐ |
| Qwen3 TTS | 4.0/5.0 | ⭐⭐⭐⭐ | ¥0.2/1K字 | 10+ | ⭐⭐⭐⭐ |
| Nihal | 3.5/5.0 | ⭐⭐ | 免费 | 自定义 | ⭐⭐⭐ |

### Embeddings对比

| 模型 | 维度 | 速度 | 成本 | 中文能力 | 推荐度 |
|-----|------|------|------|---------|--------|
| text-embedding-3-small | 1536 | ⭐⭐⭐⭐⭐ | $0.02/1M | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| text-embedding-3-large | 3072 | ⭐⭐⭐⭐ | $0.13/1M | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| hunyuan-embedding | 1024 | ⭐⭐⭐⭐ | ¥0.1/1M | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |

---

## 🔧 故障排查

### LLM问题

**问题1：API调用失败**
```
错误：401 Unauthorized
```
**解决：**
- 检查`.env`中的API密钥是否正确
- 确认API密钥有足够配额
- 检查网络连接和代理设置

**问题2：生成质量差**
```
症状：对话重复、不连贯
```
**解决：**
- 调高`temperature`（0.8-1.0）
- 增加`frequency_penalty`（0.3-0.5）
- 优化Prompt模板
- 考虑使用更高级的模型

**问题3：响应超时**
```
错误：Timeout after 60 seconds
```
**解决：**
- 减少`max_tokens`
- 简化Prompt
- 检查API服务状态
- 增加超时时间配置

### TTS问题

**问题1：音频质量差**
```
症状：机器感强、不自然
```
**解决：**
- 切换到更高质量的引擎（CosyVoice或OpenAI）
- 调整语速和音量参数
- 检查文本是否有特殊字符
- 优化文本断句

**问题2：合成速度慢**
```
症状：单段音频需要>10秒
```
**解决：**
- 启用并发合成
- 减少单次合成文本长度
- 检查网络延迟
- 考虑使用本地TTS引擎

**问题3：音色不可用**
```
错误：Voice not found
```
**解决：**
- 检查音色ID是否正确
- 查看`VOICE_LIBRARY_GUIDE.md`获取可用音色列表
- 更新音色映射配置

### Embeddings问题

**问题1：检索结果不相关**
```
症状：返回的文档与查询无关
```
**解决：**
- 增加`top_k`参数
- 调整相似度阈值
- 优化文档分块策略
- 检查嵌入模型是否适合语言

**问题2：向量化失败**
```
错误：Embedding failed
```
**解决：**
- 检查文本长度（不超过8192 tokens）
- 检查API配额
- 清理文本中的特殊字符
- 分批处理大量文档

---

## 📚 更多资源

- **API文档**：http://localhost:8000/docs
- **技术报告**：`TECHNICAL_REPORT.md`
- **配置示例**：`config/`目录
- **示例代码**：`examples/`目录

---

**模型使用愉快！** 🚀

如有更多问题，请查看FAQ或联系技术支持。
