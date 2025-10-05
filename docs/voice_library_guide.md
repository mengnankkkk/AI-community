# 音色库使用指南

## 概述

AI虚拟播客工作室现在集成了完整的音色库系统，提供13种精心挑选的NihalGazi TTS音色，支持智能推荐、分类浏览和场景匹配。

---

## 功能特性

### 1. 音色分类浏览

音色按性别分为三类：

#### 男声 (6种)
- **alloy (合金)** - 标准清晰的男声，适合各类播客和解说
- **echo (回声)** - 富有磁性的浑厚男声，适合深度访谈和严肃话题
- **fable (寓言)** - 温和的叙述型男声，适合讲故事和教学内容
- **onyx (玛瑙)** - 沉稳专业的男声，适合专家讲解和商业内容
- **ash (灰烬)** - 成熟低沉的男声，适合严肃话题和新闻播报
- **sage (智者)** - 充满智慧感的男声，适合学术讨论和知识分享

#### 女声 (5种)
- **nova (新星)** - 清晰明亮的女声，适合各类播客内容
- **shimmer (闪光)** - 充满活力的年轻女声，适合轻松话题和生活内容
- **coral (珊瑚)** - 温暖亲切的女声，适合情感类和治愈系内容
- **verse (诗句)** - 优雅抒情的女声，适合文艺和创意内容
- **ballad (民谣)** - 柔美带有歌唱感的女声，适合音乐和艺术内容

#### 特色 (2种)
- **amuch (阿穆奇)** - 独特的特色音色，适合创意和实验性内容
- **dan (丹)** - 多变的个性音色，适合多元化内容

---

## 前端使用

### 音色选择

1. **添加角色时自动加载**
   - 系统自动从API加载音色库数据
   - 音色按分类分组显示（男声/女声/特色）

2. **选择音色**
   - 下拉菜单中选择音色
   - 每个选项显示：中文名 (英文名) - 风格描述
   - 例如：`回声 (Echo) - 有磁性、浑厚`

3. **音色描述实时更新**
   - 选择音色后，下方自动显示详细描述
   - 包含性别标签和适用场景

4. **智能语气推荐**
   - 选择音色后，系统根据音色特点自动推荐语气风格
   - 用户可以接受建议或自定义

### 界面示例

```
┌─────────────────────────────────────┐
│ 角色姓名: [李博士            ]      │
│                                     │
│ 音色选择: [▼ 回声 (Echo) - 有磁性] │
│   🎵 回声 - 富有磁性的浑厚男声...   │
│                                     │
│ 语气风格: [沉稳专业、富有感染力]   │
│   💡 建议：沉稳专业、富有感染力     │
└─────────────────────────────────────┘
```

---

## API接口

### 基础端点

#### 1. 获取所有音色
```http
GET /api/v1/voices/
```

**响应示例：**
```json
{
  "success": true,
  "total": 13,
  "voices": [
    {
      "id": "echo",
      "name": "回声",
      "name_en": "Echo",
      "gender": "male",
      "style": "有磁性、浑厚",
      "tags": ["男声", "磁性", "浑厚", "深沉"],
      "description": "富有磁性的浑厚男声，适合深度访谈和严肃话题"
    }
    // ... 其他音色
  ]
}
```

#### 2. 按分类获取音色
```http
GET /api/v1/voices/categories
```

**响应示例：**
```json
{
  "success": true,
  "categories": {
    "male": {
      "name": "男声",
      "voices": [...]
    },
    "female": {
      "name": "女声",
      "voices": [...]
    },
    "special": {
      "name": "特色",
      "voices": [...]
    }
  }
}
```

#### 3. 获取指定音色详情
```http
GET /api/v1/voices/{voice_id}
```

#### 4. 按性别筛选
```http
GET /api/v1/voices/filter/gender/{gender}
```
参数：`male` | `female` | `neutral`

#### 5. 按标签筛选
```http
GET /api/v1/voices/filter/tag/{tag}
```
例如：`/api/v1/voices/filter/tag/磁性`

#### 6. 搜索音色
```http
GET /api/v1/voices/search?q=温暖
```

---

## 场景推荐

### 可用场景类型

#### 1. 学术讨论 (academic)
```http
GET /api/v1/voices/recommend/scene/academic?role=host
```
推荐音色：sage, onyx (主持人)

#### 2. 商业访谈 (business)
```http
GET /api/v1/voices/recommend/scene/business?role=host
```
推荐音色：onyx, echo (主持人)

#### 3. 轻松闲聊 (casual)
```http
GET /api/v1/voices/recommend/scene/casual?role=host
```
推荐音色：alloy, shimmer (主持人)

#### 4. 讲故事 (storytelling)
```http
GET /api/v1/voices/recommend/scene/storytelling?role=narrator
```
推荐音色：fable, verse (叙述者)

#### 5. 新闻播报 (news)
```http
GET /api/v1/voices/recommend/scene/news?role=anchor
```
推荐音色：ash, onyx, nova (主播)

---

## 智能推荐

### 根据人设和语气推荐音色

```http
GET /api/v1/voices/recommend/auto?persona=AI专家&tone=专业严谨&gender_preference=male
```

**参数说明：**
- `persona`: 角色人设描述（可选）
- `tone`: 语气风格描述（可选）
- `gender_preference`: 性别偏好（可选）

**推荐逻辑：**
- 专家、博士、教授、权威 → onyx, sage, echo, ash
- 热情、活力、年轻、开朗 → shimmer, nova, alloy
- 温暖、亲切、温柔、治愈 → coral, nova, verse
- 故事、叙述、文艺、诗意 → fable, verse, ballad

---

## 风格分类

### 1. 专业权威
**音色：** onyx, echo, sage, ash
**适用：** 专业讨论、商业内容、学术分享

### 2. 亲切温暖
**音色：** coral, nova, alloy
**适用：** 日常对话、生活分享、情感内容

### 3. 活力青春
**音色：** shimmer, alloy
**适用：** 轻松话题、娱乐内容、年轻群体

### 4. 叙述故事
**音色：** fable, verse, ballad
**适用：** 讲故事、文艺创作、有声读物

### 5. 创意实验
**音色：** amuch, dan
**适用：** 创意内容、实验性项目

---

## 数据结构

### VoiceInfo 模型

```python
class VoiceInfo(BaseModel):
    id: str                      # 音色ID（用于API调用）
    name: str                    # 显示名称（中文）
    name_en: str                 # 英文名称
    gender: str                  # 性别：male/female/neutral
    style: str                   # 风格描述
    tags: List[str]              # 标签列表
    description: str             # 详细描述
    sample_url: Optional[str]    # 音色样本URL（未来支持）
```

---

## 配置文件

### 位置
`src/backend/app/config/voice_library.py`

### 主要内容
- `NIHAL_VOICE_LIBRARY`: 13种音色的完整配置
- `VOICE_CATEGORIES`: 性别分类
- `VOICE_STYLES`: 风格分类
- `SCENE_RECOMMENDATIONS`: 场景推荐配置

---

## 使用示例

### 示例1：标准播客（两人对话）

**场景：** 科技访谈
**主持人：** onyx (玛瑙) - 沉稳专业
**嘉宾：** echo (回声) - 有磁性

### 示例2：轻松播客（多人闲聊）

**场景：** 生活话题
**主持人：** shimmer (闪光) - 活力女声
**嘉宾1：** coral (珊瑚) - 温暖女声
**嘉宾2：** alloy (合金) - 标准男声

### 示例3：故事播客

**场景：** 有声读物
**叙述者：** fable (寓言) - 温和叙述
**角色1：** verse (诗句) - 优雅女声
**角色2：** ballad (民谣) - 柔美女声

---

## 最佳实践

### 1. 音色搭配
- **对比原则：** 男女声搭配，风格互补
- **场景匹配：** 根据播客主题选择合适风格
- **个性差异：** 确保每个角色有独特的音色特点

### 2. 智能推荐使用
- 填写完整的人设和语气描述
- 参考系统推荐，但可自由调整
- 优先使用场景推荐功能

### 3. 语气风格配合
- 音色选择后，查看系统推荐的语气
- 根据角色特点微调语气描述
- 保持音色风格与语气风格的一致性

---

## 未来功能

### 即将推出
- ✅ 音色预览功能（播放示例音频）
- ⏳ 自定义音色上传
- ⏳ 音色收藏夹
- ⏳ 批量音色应用
- ⏳ 音色效果对比

---

## 技术实现

### 前端
- **文件：** `src/frontend/script.js`
- **功能：**
  - `loadVoiceLibrary()` - 加载音色库
  - `populateVoiceSelector()` - 填充选择框
  - `updateVoiceDescription()` - 更新描述
  - `suggestToneFromVoice()` - 智能推荐语气

### 后端
- **配置：** `src/backend/app/config/voice_library.py`
- **路由：** `src/backend/app/routes/voice.py`
- **集成：** `src/backend/app/main.py`

---

## 常见问题

**Q: 音色库加载失败怎么办？**
A: 系统会自动降级使用默认音色选项，不影响播客生成。

**Q: 如何添加新的音色？**
A: 编辑 `voice_library.py` 中的 `NIHAL_VOICE_LIBRARY` 字典，添加新的 `VoiceInfo` 配置。

**Q: 音色描述如何影响TTS？**
A: 音色ID直接传递给NihalGazi TTS服务，确保使用正确的预设音色。

**Q: 可以自定义音色分类吗？**
A: 可以，修改 `VOICE_CATEGORIES` 和 `VOICE_STYLES` 配置。

---

## 版本历史

**v3.0** (2025-01)
- ✅ 完整音色库系统上线
- ✅ 13种NihalGazi TTS音色支持
- ✅ 智能推荐和场景匹配
- ✅ 前端下拉选择界面

---

## 相关文档

- [前端修改总结](frontend_modifications_summary.md)
- [角色输入格式](new_character_input_format.md)
- [TTS集成指南](../src/backend/app/services/nihal_tts_service.py)

---

**最后更新：** 2025-01
**维护者：** AI虚拟播客工作室团队