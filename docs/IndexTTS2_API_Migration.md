# IndexTTS-2 API迁移文档

## 配置变更总结

### 1. 环境配置 (.env)
**变更前：**
```env
TTS_ENGINE=indextts2  # 本地模型
INDEXTTS2_GRADIO_SPACE=https://indexteam-indextts-2-demo.ms.show  # 魔搭社区
```

**变更后：**
```env
TTS_ENGINE=indextts2_gradio  # Gradio API（关键变更！）
INDEXTTS2_GRADIO_SPACE=IndexTeam/IndexTTS-2-Demo  # 官方HuggingFace空间
```

### 2. API参数变更

#### 主要变更点
**关键参数：** `emo_control_method`
- 魔搭版本：`"与音色参考音频相同"` (中文)
- 官方版本：`"Same as the voice reference"` (英文)

#### 完整API调用参数对比

**官方HuggingFace API参数：**
```python
result = client.predict(
    emo_control_method="Same as the voice reference",  # 英文枚举
    prompt=handle_file(voice_sample_path),
    text=cleaned_text,
    emo_ref_path=handle_file(voice_sample_path),
    emo_weight=0.8,
    vec1=emotion_vectors["vec1"],  # Happy
    vec2=emotion_vectors["vec2"],  # Angry
    vec3=emotion_vectors["vec3"],  # Sad
    vec4=emotion_vectors["vec4"],  # Afraid
    vec5=emotion_vectors["vec5"],  # Disgusted
    vec6=emotion_vectors["vec6"],  # Melancholic
    vec7=emotion_vectors["vec7"],  # Surprised
    vec8=emotion_vectors["vec8"],  # Calm
    emo_text="",
    emo_random=False,
    max_text_tokens_per_segment=120,
    param_16=True,     # do_sample
    param_17=0.8,      # top_p
    param_18=30,       # top_k
    param_19=0.8,      # temperature
    param_20=0,        # length_penalty
    param_21=3,        # num_beams
    param_22=10,       # repetition_penalty
    param_23=1500,     # max_mel_tokens
    api_name="/gen_single"
)
```

### 3. 情感控制方法枚举值

| 中文 (魔搭) | 英文 (官方) | 说明 |
|------------|------------|------|
| 与音色参考音频相同 | Same as the voice reference | 使用语音参考的情感 |
| 使用情感参考音频 | Use emotion reference audio | 使用独立情感参考 |
| 使用情感向量 | Use emotion vectors | 使用vec1-vec8控制 |

### 4. 情感向量映射

| 向量 | 情感 | 说明 |
|-----|------|------|
| vec1 | Happy | 开心 |
| vec2 | Angry | 愤怒 |
| vec3 | Sad | 悲伤 |
| vec4 | Afraid | 恐惧 |
| vec5 | Disgusted | 厌恶 |
| vec6 | Melancholic | 忧郁 |
| vec7 | Surprised | 惊讶 |
| vec8 | Calm | 平静 |

### 5. 验证结果

✅ **配置验证通过**
- 空间名称：IndexTeam/IndexTTS-2-Demo
- API端点：https://indexteam-indextts-2-demo.hf.space
- API接口：/gen_single
- 参数格式：英文枚举值

⚠️ **注意事项**
1. 官方HuggingFace空间在国内可能需要代理访问
2. SSL握手可能会超时，建议增加timeout设置
3. 如需国内快速访问，可继续使用魔搭社区（需改回中文参数）

### 6. 代码变更文件

**关键变更：**
- `E:\github\AI-community\.env` (line 26, 30)
  - TTS_ENGINE: `indextts2` → `indextts2_gradio`
  - INDEXTTS2_GRADIO_SPACE: 魔搭URL → `IndexTeam/IndexTTS-2-Demo`

- `E:\github\AI-community\src\backend\app\services\indextts2_gradio_service.py`
  - line 249: API参数 `emo_control_method` 改为英文
  - line 119-132: 新增 `voice_01` ~ `voice_13` 音色ID映射

### 7. 音色ID映射表

| voice_XX ID | 映射文件 | NihalGazi音色 | 说明 |
|------------|---------|---------------|------|
| voice_01 | voice_standard.wav | alloy | 标准男声 |
| voice_02 | voice_male.wav | echo | 磁性男声 |
| voice_03 | voice_warm.wav | fable | 温和男声 |
| voice_04 | voice_deep.wav | onyx | 浑厚男声 |
| voice_05 | voice_steady.wav | ash | 沉稳男声 |
| voice_06 | voice_intellectual.wav | sage | 智者男声 |
| voice_07 | voice_female.wav | nova | 清晰女声 |
| voice_08 | voice_crisp.wav | shimmer | 活力女声 |
| voice_09 | voice_warm.wav | coral | 温暖女声 |
| voice_10 | voice_energetic.wav | verse | 优雅女声 |
| voice_11 | voice_magnetic.wav | ballad | 柔美女声 |
| voice_12 | voice_standard.wav | amuch | 特色音色 |
| voice_13 | voice_male.wav | dan | 特色音色 |

### 8. 回滚方法

如果需要回滚到魔搭社区版本：

**回滚 .env：**
```env
TTS_ENGINE=indextts2  # 改回本地模型（如果需要本地）
# 或
TTS_ENGINE=indextts2_gradio  # 保持Gradio，但换回魔搭
INDEXTTS2_GRADIO_SPACE=https://indexteam-indextts-2-demo.ms.show
```

**回滚 API参数：**
```python
emo_control_method="与音色参考音频相同",  # 改回中文
```

### 9. 使用建议

**推荐配置（国内用户）：**
```env
TTS_ENGINE=indextts2_gradio
INDEXTTS2_GRADIO_SPACE=https://indexteam-indextts-2-demo.ms.show  # 魔搭社区更快
```
并在 `indextts2_gradio_service.py:249` 使用中文参数：`"与音色参考音频相同"`

**推荐配置（国际用户）：**
```env
TTS_ENGINE=indextts2_gradio
INDEXTTS2_GRADIO_SPACE=IndexTeam/IndexTTS-2-Demo  # 官方HF空间
```
使用英文参数：`"Same as the voice reference"`（已配置）
