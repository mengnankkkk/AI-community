# IndexTTS2 安装与配置指南

## 概述

IndexTTS2 是由 Bilibili 开源的工业级情感语音合成模型，支持真实情感表达和多角色音色控制。本项目已集成 IndexTTS2 作为主要的 TTS 引擎。

## 系统要求

- **GPU**: 推荐 8GB+ 显存（最低 6GB）
- **内存**: 16GB+ RAM
- **Python**: 3.11 或 3.12
- **CUDA**: 支持的 NVIDIA GPU（可选，CPU 也可运行但速度较慢）

## 安装步骤

### 1. 安装 Git LFS

```bash
# Windows (使用 Git for Windows)
git lfs install

# Linux/macOS
curl -s https://packagecloud.io/install/repositories/github/git-lfs/script.deb.sh | sudo bash
sudo apt-get install git-lfs
git lfs install
```

### 2. 克隆 IndexTTS2 代码

```bash
# 在项目根目录执行
git clone https://github.com/index-tts/index-tts.git indextts2_source
cd indextts2_source
git lfs pull
```

### 3. 下载预训练模型

```bash
# 方法1: 使用 Hugging Face Hub
pip install huggingface_hub[cli]
hf download IndexTeam/IndexTTS-2 --local-dir=../checkpoints

# 方法2: 使用 ModelScope（国内用户推荐）
pip install modelscope
modelscope download --model IndexTeam/IndexTTS-2 --local_dir=../checkpoints
```

### 4. 安装 IndexTTS2 依赖

```bash
# 返回项目根目录
cd ..

# 安装项目依赖（包含 IndexTTS2 依赖）
pip install -r requirements.txt

# 安装 IndexTTS2（从源码）
cd indextts2_source
pip install -e .
cd ..
```

## 目录结构

安装完成后，您的项目目录应该如下：

```
AI-community/
├── checkpoints/                 # IndexTTS2 模型文件
│   ├── config.yaml
│   ├── gpt.pth
│   ├── decoder.pth
│   └── ...
├── voice_samples/              # 角色音色样本
│   ├── voice_standard.wav
│   ├── voice_male.wav
│   ├── voice_female.wav
│   └── ...
├── emotion_samples/            # 情感样本
│   ├── emo_happy.wav
│   ├── emo_sad.wav
│   ├── emo_excited.wav
│   └── ...
├── indextts2_source/          # IndexTTS2 源码
└── backend/
```

## 音色样本配置

### 1. 准备音色样本

为了获得最佳效果，需要为每个角色准备专用的音色样本文件（3-10秒的清晰录音）：

```
voice_samples/
├── voice_standard.wav      # 标准音色
├── voice_male.wav         # 男声
├── voice_female.wav       # 女声
├── voice_deep.wav         # 浑厚男声
├── voice_crisp.wav        # 清脆女声
├── voice_warm.wav         # 温暖音色
└── voice_magnetic.wav     # 磁性音色
```

### 2. 准备情感样本

为情感控制准备情感参考音频：

```
emotion_samples/
├── emo_happy.wav          # 开心
├── emo_sad.wav            # 悲伤
├── emo_excited.wav        # 激动
├── emo_calm.wav           # 平静
├── emo_serious.wav        # 严肃
└── emo_warm.wav           # 温暖
```

### 3. 音频样本要求

- **格式**: WAV, MP3, FLAC
- **时长**: 3-10秒
- **质量**: 清晰，无噪音
- **内容**: 自然语调，代表性内容

## 环境配置

在 `.env` 文件中配置 IndexTTS2：

```env
# TTS引擎选择
TTS_ENGINE=indextts2

# IndexTTS2配置
INDEXTTS_MODEL_DIR=checkpoints
INDEXTTS_VOICE_SAMPLES_DIR=voice_samples
INDEXTTS_EMOTION_SAMPLES_DIR=emotion_samples
INDEXTTS_USE_FP16=true
INDEXTTS_USE_CUDA_KERNEL=false
```

## 使用说明

### 1. 角色音色映射

系统会根据角色的 `voice_description` 自动匹配合适的音色样本：

- "沉稳" → `voice_steady.wav`
- "浑厚" → `voice_deep.wav`
- "清脆" → `voice_crisp.wav`
- "温暖" → `voice_warm.wav`

### 2. 情感控制

在剧本生成中，可以为对话指定情感标注：

```json
{
  "character_name": "主持人",
  "content": "欢迎大家收听今天的播客！",
  "emotion": "开心"
}
```

### 3. 引擎切换

可以通过环境变量或 API 在 IndexTTS2 和 OpenAI TTS 之间切换：

```python
# 通过 API 切换引擎
POST /api/v1/tts/switch-engine
{
  "engine": "indextts2"  # 或 "openai"
}
```

## 故障排除

### 1. 模型加载失败

```bash
# 检查模型文件完整性
ls -la checkpoints/
# 应该包含: config.yaml, gpt.pth, decoder.pth 等
```

### 2. 显存不足

```env
# 启用 FP16 减少显存占用
INDEXTTS_USE_FP16=true

# 如果仍然不足，可以回退到 OpenAI TTS
TTS_ENGINE=openai
```

### 3. 音色样本缺失

系统会自动回退到默认样本或 OpenAI TTS。建议按照上述格式准备音色样本。

## 性能优化

1. **使用 FP16**: 减少 50% 显存占用
2. **批量生成**: 一次生成多个片段
3. **样本质量**: 高质量音色样本显著提升效果
4. **GPU 加速**: 推荐使用支持 CUDA 的 GPU

## 高级功能

### 1. 自定义音色样本

```python
# 为特定角色创建专用音色样本
from backend.app.services.indextts_service import IndexTTSService

service = IndexTTSService()
sample_path = await service.create_voice_sample(
    character_name="教授",
    voice_description="学者气质，语速适中",
    sample_text="大家好，我是今天的嘉宾教授。"
)
```

### 2. 时长控制

```python
# 精确控制生成音频的时长
await service.synthesize_single_audio(
    text="这段话需要控制在5秒内",
    voice_sample_path="voice_samples/voice_standard.wav",
    emotion_sample_path=None,
    output_path="output.wav",
    target_duration=5.0  # 5秒
)
```

## 更新日志

- **v1.0.0**: 集成 IndexTTS2 基础功能
- **v1.1.0**: 添加情感控制支持
- **v1.2.0**: 优化音频后处理和拼接

## 技术支持

如遇问题，请：

1. 检查系统要求和安装步骤
2. 查看日志文件 `logs/` 目录
3. 确认音色样本文件存在且格式正确
4. 尝试切换到 OpenAI TTS 作为备选方案