# 音色库使用指南

## 概述

AI虚拟播客工作室现已支持统一的音色库系统，所有TTS引擎（CosyVoice、OpenAI TTS、IndexTTS2、Qwen3等）都可以使用这个统一的音色库。

## 支持的TTS引擎

| 引擎名称 | 引擎类型 | 音色支持 | 状态 |
|---------|---------|---------|-----|
| **CosyVoice** | 商业API | ✅ 5种官方音色 + 自定义 | 已完成 |
| **OpenAI TTS** | 商业API | ✅ 6种官方音色 + 映射 | 已完成 |
| **IndexTTS2 Gradio** | 本地模型 | ✅ 自定义音色文件 | 已完成 |
| **Qwen3 TTS** | 商业API | ✅ 音色映射 | 已完成 |
| **Nihal TTS** | 本地模型 | ✅ 音色映射 | 已完成 |

---

## 音色库功能

### 1. 预设音色（CosyVoice官方）

系统提供5种高质量的中文音色：

| 音色ID | 音色名称 | 特点 | 适用场景 |
|-------|---------|------|---------|
| `longwan_v2` | 龙湾（男声-标准） | 沉稳大气 | 专业播客、商务内容 |
| `longyuan_v2` | 龙渊（男声-浑厚） | 富有磁性 | 深度访谈、叙事 |
| `longxiaochun_v2` | 龙小春（女声-标准） | 清晰自然 | 通用场景、教育 |
| `longxiaoxia_v2` | 龙小夏（女声-温暖） | 亲和力强 | 情感内容、故事 |
| `longxiaoyuan_v2` | 龙小媛（女声-活力） | 朝气蓬勃 | 轻松话题、娱乐 |

### 2. 自定义音色

支持上传自定义音频样本（3-10秒）进行音色克隆：

**支持格式：** WAV, MP3, M4A, OGG
**文件大小：** 最大10MB
**推荐配置：** 16kHz采样率，单声道，3-10秒纯净人声

---

## 使用方法

### 方式1：通过Web界面使用

#### 步骤1：添加角色时选择音色

1. 访问 http://localhost:8000/static/index.html
2. 在"添加角色"部分，点击"音色"下拉菜单
3. 选择预设音色（龙湾、龙渊、龙小春等）

#### 步骤2：上传自定义音色（可选）

1. 点击"上传自定义音色"按钮
2. 选择音频文件（WAV/MP3格式）
3. 系统自动转换并添加到音色库
4. 在下拉菜单中选择刚上传的音色

#### 步骤3：试听音色

点击音色选择器旁边的播放按钮即可试听音色效果

---

### 方式2：通过API使用

#### 使用预设音色

```python
import requests

url = "http://localhost:8000/api/v1/podcast/generate"
payload = {
    "custom_form": {
        "topic": "人工智能的未来",
        "characters": [
            {
                "name": "李明",
                "persona": "资深AI研究员",
                "core_viewpoint": "AI将深刻改变社会",
                "voice_description": "longwan_v2",  # 使用CosyVoice音色ID
                "tone_description": "专业、理性"
            },
            {
                "name": "王芳",
                "persona": "科技记者",
                "core_viewpoint": "关注AI伦理",
                "voice_description": "longxiaochun_v2",  # 使用CosyVoice音色ID
                "tone_description": "好奇、客观"
            }
        ]
    }
}

response = requests.post(url, json=payload)
```

#### 使用关键词描述

```python
# 系统会自动根据关键词映射到合适的音色
payload = {
    "custom_form": {
        "characters": [
            {
                "name": "张三",
                "voice_description": "沉稳男声",  # 自动映射到 longwan_v2 (CosyVoice) 或 onyx (OpenAI)
                ...
            },
            {
                "name": "李四",
                "voice_description": "活力女声",  # 自动映射到 longxiaoyuan_v2 (CosyVoice) 或 nova (OpenAI)
                ...
            }
        ]
    }
}
```

#### 使用自定义音色

```python
# 1. 先上传音色文件
import requests

upload_url = "http://localhost:8000/api/v1/voice-samples/upload"
files = {'file': open('my_voice_sample.wav', 'rb')}
data = {
    'name': '我的自定义音色',
    'description': '温暖亲切的女声'
}

upload_response = requests.post(upload_url, files=files, data=data)
voice_id = upload_response.json()['sample']['id']

# 2. 在生成播客时使用这个音色ID
payload = {
    "custom_form": {
        "characters": [
            {
                "name": "角色A",
                "voice_description": voice_id,  # 使用上传的自定义音色ID
                ...
            }
        ]
    }
}
```

---

## 音色映射机制

系统会自动根据不同TTS引擎进行音色映射：

### CosyVoice ⇄ OpenAI 映射表

| CosyVoice | OpenAI | 特征 |
|-----------|--------|------|
| longwan_v2 | onyx | 沉稳男声 |
| longyuan_v2 | echo | 磁性男声 |
| longxiaochun_v2 | nova | 清晰女声 |
| longxiaoxia_v2 | shimmer | 温暖女声 |
| longxiaoyuan_v2 | nova | 活力女声 |

### 关键词自动映射

| 关键词 | CosyVoice | OpenAI | 通用 |
|-------|-----------|--------|-----|
| 沉稳 | longwan_v2 | onyx | male_steady |
| 浑厚 | longyuan_v2 | echo | male_deep |
| 磁性 | longyuan_v2 | echo | male_magnetic |
| 清脆 | longxiaochun_v2 | nova | female_crisp |
| 温暖 | longxiaoxia_v2 | shimmer | female_warm |
| 活力 | longxiaoyuan_v2 | nova | female_energetic |
| 男声 | longwan_v2 | fable | male_standard |
| 女声 | longxiaochun_v2 | nova | female_standard |

---

## API接口文档

### 获取预设音色列表

**GET** `/api/v1/voice-samples/presets`

**响应示例：**
```json
{
    "success": true,
    "total": 5,
    "samples": [
        {
            "id": "longwan_v2",
            "name": "龙湾（男声-标准）",
            "description": "标准男声，沉稳大气，适合专业播客",
            "tags": ["男声", "标准", "沉稳", "专业"],
            "gender": "male",
            "provider": "cosyvoice"
        },
        ...
    ],
    "provider": "cosyvoice"
}
```

### 上传自定义音色

**POST** `/api/v1/voice-samples/upload`

**请求参数：**
- `file`: 音频文件（form-data）
- `name`: 音色名称（可选）
- `description`: 音色描述（可选）

**响应示例：**
```json
{
    "success": true,
    "sample": {
        "id": "custom_20250613_abc123",
        "name": "自定义音色_abc123",
        "file_path": "/path/to/custom_voice.wav",
        "file_size": 245678,
        "description": "用户上传的自定义音色",
        "is_custom": true
    }
}
```

### 获取自定义音色列表

**GET** `/api/v1/voice-samples/custom`

**响应示例：**
```json
{
    "success": true,
    "total": 2,
    "samples": [
        {
            "id": "custom_20250613_abc123",
            "name": "自定义_20250613_abc123",
            "file_path": "/path/to/file.wav",
            "file_size": 245678,
            "description": "用户上传的音色",
            "is_custom": true,
            "created_at": 1686644123.456
        },
        ...
    ]
}
```

### 预览音色

**GET** `/api/v1/voice-samples/preview/{sample_id}`

返回音频文件流，可直接在浏览器播放

### 删除自定义音色

**DELETE** `/api/v1/voice-samples/{sample_id}`

**响应示例：**
```json
{
    "success": true,
    "message": "删除成功"
}
```

---

## 最佳实践

### 1. 音色选择建议

**专业内容：**
- 男声：使用龙湾（longwan_v2）或龙渊（longyuan_v2）
- 女声：使用龙小春（longxiaochun_v2）

**情感内容：**
- 温暖风格：使用龙小夏（longxiaoxia_v2）
- 活力风格：使用龙小媛（longxiaoyuan_v2）

**访谈节目：**
- 主持人：龙湾（沉稳）
- 嘉宾：根据嘉宾特点选择不同音色

### 2. 自定义音色上传建议

**录音要求：**
- 环境安静，无背景噪音
- 说话自然，避免过度表演
- 时长3-10秒最佳
- 内容：一段完整的句子

**音频处理：**
- 推荐采样率：16kHz或44.1kHz
- 推荐格式：WAV（无损）
- 单声道优于双声道
- 避免使用音效处理

### 3. 性能优化

**并发调用：**
系统支持并发TTS合成，多角色播客会自动并行处理，显著提升生成速度。

**缓存机制：**
相同文本和音色的音频会自动缓存复用，减少重复合成。

---

## 故障排除

### 问题1：音色列表为空

**症状：** 前端音色选择器显示"正在加载..."但无音色

**解决方案：**
1. 检查后端服务是否正常运行
2. 检查 `.env` 文件中 `TTS_ENGINE` 配置
3. 查看浏览器控制台日志
4. 重启后端服务

### 问题2：自定义音色上传失败

**症状：** 上传时提示错误

**可能原因：**
- 文件格式不支持 → 使用WAV/MP3格式
- 文件过大 → 压缩至10MB以下
- 目录权限问题 → 检查 `data/uploads/custom_voices` 目录权限

### 问题3：音色效果不理想

**解决方案：**
1. 尝试不同的预设音色
2. 调整语气描述（tone_description）
3. 上传更高质量的自定义音色样本
4. 切换TTS引擎（如从OpenAI切换到CosyVoice）

---

## 技术架构

### 统一音色解析服务

系统使用 `VoiceResolverService` 统一处理所有TTS引擎的音色解析：

```python
from ..services.voice_resolver_service import voice_resolver

# 解析音色描述
voice_id, voice_file = voice_resolver.resolve_voice(
    voice_description="沉稳男声",
    tts_engine="cosyvoice"
)
```

**解析优先级：**
1. CosyVoice官方音色ID（如 longwan_v2）
2. OpenAI音色ID（如 onyx）
3. 自定义音色文件路径
4. 关键词映射
5. 默认音色

---

## 更新日志

### v1.0.0 (2025-06-13)
- ✅ 支持5种CosyVoice官方音色
- ✅ 支持自定义音色上传和克隆
- ✅ 统一所有TTS引擎的音色解析
- ✅ 前端音色选择器增强
- ✅ 音色试听功能
- ✅ 音色管理API完善

---

## 联系支持

如有问题或建议，请：
- 提交Issue: https://github.com/your-repo/AI-community/issues
- 查看技术文档: `TECHNICAL_REPORT.md`
- 查看README: `README.md`
