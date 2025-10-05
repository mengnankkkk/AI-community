# IndexTTS2音色选择快速参考

## 🎯 总览

为 `indextts2_gradio` TTS引擎实现了**双模式音色选择**功能：
1. **预设音色库**：从11个预设音色中选择
2. **自定义上传**：上传用户自己的音频文件进行克隆

---

## 📦 后端实现清单

### ✅ 已完成的修改

1. **新增API路由** (`src/backend/app/routes/voice_samples.py`)
   - `GET /api/v1/voice-samples/presets` - 获取预设音色
   - `POST /api/v1/voice-samples/upload` - 上传自定义音色
   - `GET /api/v1/voice-samples/custom` - 获取用户音色
   - `DELETE /api/v1/voice-samples/{id}` - 删除自定义音色

2. **扩展数据模型** (`src/backend/app/models/podcast.py`)
   ```python
   class CharacterRole:
       voice_description: str  # 保留（向后兼容）
       voice_file: Optional[str]  # 新增（音色文件路径）
   ```

3. **更新TTS服务** (`src/backend/app/services/indextts2_gradio_service.py`)
   - `get_voice_sample_path()` 方法支持 `voice_file` 参数
   - 优先使用 `voice_file`，回退到 `voice_description` 映射

4. **注册路由** (`src/backend/app/main.py`)
   - 添加 `voice_samples` 路由到FastAPI应用

---

## 📋 预设音色列表

| ID | 名称 | 描述 | 适用场景 |
|----|------|------|---------|
| voice_standard | 标准音色 | 中性标准 | 通用 |
| voice_male | 男声 | 标准男声 | 主持人 |
| voice_female | 女声 | 标准女声 | 主持人 |
| voice_deep | 浑厚男声 | 深沉有力 | 严肃内容 |
| voice_crisp | 清脆女声 | 明亮活泼 | 活泼内容 |
| voice_warm | 温暖音色 | 亲切温和 | 情感内容 |
| voice_steady | 沉稳音色 | 专业稳重 | 专业内容 |
| voice_energetic | 活力音色 | 年轻有活力 | 年轻化 |
| voice_magnetic | 磁性音色 | 富有魅力 | 深度访谈 |
| voice_intellectual | 知性音色 | 学术气质 | 学术讨论 |
| voice_baritone | 男中音 | 播音风格 | 播报 |

---

## 🔌 前端集成要点

### 1. 获取预设音色

```javascript
const response = await fetch('/api/v1/voice-samples/presets');
const { samples } = await response.json();

// 渲染选择界面
samples.forEach(sample => {
  // sample.id, sample.name, sample.file_path, sample.description
});
```

### 2. 上传自定义音色

```javascript
const formData = new FormData();
formData.append('file', audioFile);
formData.append('name', '我的音色');

const response = await fetch('/api/v1/voice-samples/upload', {
  method: 'POST',
  body: formData
});

const { sample } = await response.json();
// 使用 sample.file_path
```

### 3. 配置角色音色

```javascript
// 方式1：使用预设音色
const character = {
  name: "李博士",
  voice_description: "男中音",
  voice_file: "voice_samples/voice_baritone.wav",  // 选择的预设
  // ...其他字段
};

// 方式2：使用自定义音色
const character = {
  name: "王经理",
  voice_description: "自定义音色",
  voice_file: "uploads/custom_voices/custom_xxx.wav",  // 上传的文件
  // ...其他字段
};
```

---

## 🎵 音频文件要求

- **格式**：WAV（推荐）/ MP3 / M4A / OGG
- **时长**：3-10秒
- **内容**：纯净人声，无背景音乐/噪音
- **大小**：≤10MB
- **采样率**：16kHz+（系统会自动转换）
- **声道**：单声道/立体声均可（自动转单声道）

---

## 🚀 快速测试

### 1. 测试预设音色接口

```bash
curl http://localhost:8000/api/v1/voice-samples/presets
```

### 2. 测试上传接口

```bash
curl -X POST http://localhost:8000/api/v1/voice-samples/upload \
  -F "file=@test_voice.wav" \
  -F "name=测试音色"
```

### 3. 生成播客（使用音色文件）

```bash
curl -X POST http://localhost:8000/api/v1/podcast/generate \
  -H "Content-Type: application/json" \
  -d '{
    "custom_form": {
      "topic": "测试主题",
      "characters": [{
        "name": "测试角色",
        "voice_description": "标准音色",
        "voice_file": "voice_samples/voice_standard.wav",
        "tone_description": "平和",
        "persona": "测试人设",
        "core_viewpoint": "测试观点"
      }]
    }
  }'
```

---

## 🔍 故障排查

### 问题1：音色文件找不到

**症状**：日志显示 "无法获取音色样本"

**解决**：
1. 检查 `voice_samples/` 目录是否存在
2. 运行 `voice_sample_manager.ensure_samples_exist()` 创建默认样本
3. 检查文件路径是否正确

### 问题2：上传的音频无法使用

**症状**：上传成功但生成时报错

**解决**：
1. 确认音频格式是否支持
2. 检查文件是否损坏（使用音频播放器测试）
3. 查看日志中的具体错误信息

### 问题3：音色克隆效果不佳

**原因**：音频质量问题

**改进**：
- 使用更清晰的人声样本
- 确保样本时长在5-10秒
- 避免背景噪音
- 语速适中、语调自然

---

## 📚 相关文档

- **完整前端集成指南**：`docs/VOICE_SELECTION_GUIDE.md`
- **API文档**：http://localhost:8000/docs#/voice-samples
- **TTS引擎配置**：`.env` 文件中的 `TTS_ENGINE` 设置

---

## 💡 最佳实践

1. **优先使用预设**：预设音色经过优化，效果更稳定
2. **自定义需精选**：选择高质量的音频样本
3. **测试后使用**：上传后先测试生成效果
4. **统一风格**：同一播客使用风格相似的音色
5. **备份音色**：重要的自定义音色应该备份

---

**创建时间：** 2025-10-02
**适用引擎：** indextts2_gradio
**最低版本：** v1.0.0
