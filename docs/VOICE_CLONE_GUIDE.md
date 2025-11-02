# CosyVoice 音色克隆功能使用指南

## 📌 功能概述

本系统已完全集成 **阿里云 CosyVoice 音色克隆功能**，支持用户上传音频文件进行自定义音色克隆，实现真正的个性化语音合成。

## ✨ 功能特性

### 1. 音色克隆支持
- ✅ 上传音频文件自动克隆音色
- ✅ 支持多种音频格式（WAV, MP3, M4A, AAC）
- ✅ 自动音频质量验证
- ✅ 克隆状态实时反馈
- ✅ 克隆失败自动回退

### 2. 音频文件要求
| 要求项 | 规格 |
|--------|------|
| **文件大小** | 最大 10 MB |
| **采样率** | 至少 16 kHz |
| **音频时长** | 至少 5 秒连续人声 |
| **支持格式** | WAV, MP3, M4A, AAC |
| **音频质量** | 低噪音，无频繁停顿 |

### 3. 音色命名要求
| 参数 | 要求 |
|------|------|
| **VoicePrefix** | 不超过10个字符 |
| **字符类型** | 仅支持字母和数字 |
| **唯一性** | 系统自动生成唯一ID |

## 🚀 使用方法

### 方式一：前端界面上传（推荐）

#### 步骤1：准备音频文件
录制或准备一段清晰的人声音频：
- 时长：5-10秒
- 内容：连续说话，避免停顿
- 质量：无背景噪音，清晰自然
- 格式：WAV或MP3

#### 步骤2：上传并克隆
1. 在播客创建界面，为角色选择音色时：
2. 点击"上传自定义音色"按钮
3. **勾选"启用音色克隆"复选框**（重要！）
4. 选择音频文件
5. 点击上传

#### 步骤3：查看结果
- ✅ **成功**: 显示"音色上传并克隆成功！音色ID: xxx"
- ⚠️ **失败**: 显示失败原因（文件质量、格式等）
- 🔄 **处理中**: 显示"正在上传音色并克隆..."

### 方式二：API调用

#### 接口1：上传音频并自动克隆
```bash
curl -X POST "http://localhost:8000/api/v1/voice-samples/upload" \
  -F "file=@your_voice.wav" \
  -F "name=我的自定义音色" \
  -F "description=我的个人音色" \
  -F "enable_clone=true"
```

**响应示例**：
```json
{
  "success": true,
  "sample": {
    "id": "custom_20250102_123456_abcd1234",
    "name": "我的自定义音色",
    "file_path": "/path/to/file.wav",
    "file_size": 524288,
    "description": "我的个人音色",
    "is_custom": true,
    "created_at": "2025-01-02T12:34:56"
  },
  "clone_status": "success",
  "clone_info": {
    "voice_id": "customabcd1234_cloned",
    "voice_prefix": "customabcd1234",
    "message": "音色克隆任务已提交"
  }
}
```

#### 接口2：查询克隆音色列表
```bash
curl -X GET "http://localhost:8000/api/v1/voice-clone/list/customabcd1234?page_index=1&page_size=10"
```

#### 接口3：独立克隆接口
```bash
curl -X POST "http://localhost:8000/api/v1/voice-clone/upload-and-clone" \
  -F "file=@your_voice.wav" \
  -F "voice_prefix=myvoice01" \
  -F "voice_name=我的专属音色"
```

## ⚙️ 配置说明

### 环境变量配置
在 `.env` 文件中添加以下配置：

```bash
# TTS引擎选择
TTS_ENGINE=cosyvoice

# 阿里云配置
ALICLOUD_DASHSCOPE_API_KEY=your_api_key_here
ALICLOUD_DASHSCOPE_API_SECRET=your_api_secret_here  # 音色克隆必需

# CosyVoice配置
COSYVOICE_MODEL=cosyvoice-v2
COSYVOICE_DEFAULT_VOICE=longxiaochun_v2
COSYVOICE_ENABLE_CLONE=true  # 启用音色克隆功能
```

### 获取阿里云密钥
1. 登录 [阿里云控制台](https://ram.console.aliyun.com/)
2. 进入访问控制 > 用户 > 创建用户
3. 勾选"OpenAPI调用访问"
4. 保存 AccessKey ID 和 AccessKey Secret
5. 授予用户 **AliyunNLSFullAccess** 权限

## 📊 系统架构

### 完整流程
```
用户上传音频
    ↓
前端验证（格式、大小）
    ↓
提交到后端 API
    ↓
保存到本地 (data/uploads/custom_voices/)
    ↓
音频质量验证（采样率、时长、噪音）
    ↓
调用 CosyVoice 克隆 API
    ↓
获取克隆音色 ID
    ↓
返回结果给前端
    ↓
可用于TTS合成
```

### 文件结构
```
src/backend/app/
├── services/
│   ├── cosyvoice_clone_service.py      # 音色克隆核心服务
│   ├── alicloud_cosyvoice_service.py   # TTS合成服务
│   └── voice_resolver_service.py       # 音色解析服务
├── routes/
│   ├── voice_clone.py                  # 音色克隆API路由
│   └── voice_samples.py                # 音色样本API路由
└── core/
    └── config.py                        # 配置管理

src/frontend/
└── voice_samples.js                     # 前端音色管理

data/uploads/
├── custom_voices/                       # 用户上传的音色文件
└── voice_clone_temp/                    # 克隆临时文件
```

## 🔧 API 接口文档

### 1. POST /api/v1/voice-samples/upload
**上传自定义音色样本（支持克隆）**

**请求参数**：
- `file`: 音频文件（FormData）
- `name`: 音色名称（可选）
- `description`: 音色描述（可选）
- `enable_clone`: 是否启用克隆（布尔值，默认false）

**响应字段**：
- `success`: 是否成功
- `sample`: 音色样本信息
- `clone_status`: 克隆状态（success/failed/error）
- `clone_info`: 克隆信息（成功时）
- `clone_error`: 克隆错误信息（失败时）

### 2. POST /api/v1/voice-clone/upload-and-clone
**上传音频并立即克隆**

**请求参数**：
- `file`: 音频文件（FormData）
- `voice_prefix`: 音色前缀（必需，不超过10个字符）
- `voice_name`: 音色名称（可选）

**响应字段**：
- `success`: 是否成功
- `voice_id`: 克隆音色ID
- `voice_prefix`: 音色前缀
- `status`: 克隆状态
- `message`: 状态消息
- `error`: 错误信息（失败时）

### 3. GET /api/v1/voice-clone/list/{voice_prefix}
**查询克隆音色列表**

**请求参数**：
- `voice_prefix`: 音色前缀（路径参数）
- `page_index`: 页码（查询参数，默认1）
- `page_size`: 每页数量（查询参数，默认10）

**响应字段**：
- `success`: 是否成功
- `voices`: 音色列表
- `total`: 总数量
- `page_index`: 当前页码
- `page_size`: 每页数量

### 4. GET /api/v1/voice-clone/health
**音色克隆服务健康检查**

**响应字段**：
- `status`: 服务状态（configured/unconfigured）
- `service`: 服务名称
- `message`: 状态消息

## ⚠️ 常见问题

### Q1: 为什么克隆失败？
**可能原因**：
1. **音频质量不佳**：噪音过大、信噪比低
2. **时长不足**：少于5秒连续人声
3. **采样率过低**：低于16kHz
4. **文件过大**：超过10MB
5. **API配置错误**：API Key或Secret未配置

**解决方法**：
```bash
# 检查音频质量
ffprobe your_voice.wav

# 转换音频格式
ffmpeg -i input.mp3 -ar 16000 -ac 1 output.wav

# 检查配置
curl -X GET "http://localhost:8000/api/v1/voice-clone/health"
```

### Q2: 如何提高克隆质量？
**建议**：
1. 使用高质量麦克风录音
2. 在安静环境录制
3. 保持连续说话，避免停顿
4. 录制5-10秒自然语音
5. 使用WAV或无损格式

### Q3: 克隆的音色如何使用？
克隆成功后，音色ID会自动添加到可用音色列表：
```python
# 在TTS合成时使用
voice_id = "customabcd1234_cloned"
result = cosyvoice_service.synthesize_audio(text, voice_id)
```

### Q4: TODO - 文件需要公网访问？
**当前状态**：使用本地文件路径（`file://`）
**计划**：集成阿里云 OSS 对象存储

**临时解决方案**：
```python
# 在 cosyvoice_clone_service.py 中
# TODO: 上传到 OSS
# audio_url = upload_to_oss(file_path)
audio_url = f"file://{file_path}"  # 当前使用本地路径
```

## 🔒 安全说明

1. **API密钥保护**：
   - 不要将密钥提交到代码仓库
   - 使用环境变量存储
   - 定期轮换密钥

2. **文件验证**：
   - 自动验证文件类型
   - 检查文件大小
   - 验证音频质量

3. **权限控制**：
   - 用户只能访问自己的音色
   - 克隆音色数量限制（默认1000个）

## 📈 性能优化

1. **异步处理**：所有API调用都是异步的
2. **错误重试**：网络错误自动重试
3. **文件缓存**：上传的文件保留用于后续使用
4. **批量处理**：支持批量查询和管理

## 🎯 下一步计划

- [ ] 集成阿里云 OSS 文件存储
- [ ] 添加音色预览功能
- [ ] 支持批量克隆
- [ ] 音色质量评分
- [ ] 音色推荐系统

---

**文档生成时间**: 2025-11-02
**版本**: 1.0.0
**维护者**: AI-community 团队
