# 新的角色输入格式说明

## 概述

更新后的角色设定支持更细粒度的控制，包括音色、语气、人设和观点的独立配置。

## 角色输入字段

### CharacterRole 模型字段

| 字段 | 类型 | 说明 | 示例 |
|------|------|------|------|
| `name` | string | 角色姓名/代称 | "李博士"、"王经理"、"主持人" |
| `voice_description` | string | 音色描述（用于TTS选择声音） | "沉稳"、"清脆"、"有磁性"、"温暖" |
| `tone_description` | string | 语气风格描述（AI生成对话时参考） | "平和专业"、"热情开朗"、"严谨理性"、"幽默风趣" |
| `persona` | string | 人设/身份描述 | "资深AI专家，拥有15年研究经验"、"互联网公司CTO" |
| `core_viewpoint` | string | 核心观点/立场 | "AI将创造更多新岗位"、"需要警惕AI带来的失业风险" |

---

## 完整输入示例

### JSON格式

```json
{
  "topic": "人工智能对未来工作的影响",
  "title": "AI时代：机遇还是挑战？",
  "atmosphere": "serious_deep",
  "target_duration": "5分钟",
  "language_style": "colloquial",
  "characters": [
    {
      "name": "李博士",
      "voice_description": "沉稳有磁性",
      "tone_description": "平和专业，善于引导",
      "persona": "资深人工智能专家，AI伦理研究者，拥有15年行业经验",
      "core_viewpoint": "AI是工具而非威胁，关键在于如何引导和规范其发展"
    },
    {
      "name": "王经理",
      "voice_description": "清脆有活力",
      "tone_description": "热情开朗，善于举例",
      "persona": "互联网企业技术总监，曾参与多个AI项目落地",
      "core_viewpoint": "AI将创造更多新型工作岗位，但需要重视技能转型培训"
    },
    {
      "name": "张记者",
      "voice_description": "温暖亲切",
      "tone_description": "好奇求知，善于提问",
      "persona": "科技媒体记者，长期关注AI行业动态",
      "core_viewpoint": "需要平衡AI发展速度与社会适应能力，关注弱势群体"
    }
  ],
  "background_materials": "可选：相关研究报告、数据、案例等背景素材"
}
```

### Python代码示例

```python
from src.backend.app.models.podcast import (
    PodcastCustomForm,
    CharacterRole,
    DiscussionAtmosphere,
    LanguageStyle
)

# 定义角色
characters = [
    CharacterRole(
        name="李博士",
        voice_description="沉稳有磁性",
        tone_description="平和专业，善于引导",
        persona="资深人工智能专家，AI伦理研究者，拥有15年行业经验",
        core_viewpoint="AI是工具而非威胁，关键在于如何引导和规范其发展"
    ),
    CharacterRole(
        name="王经理",
        voice_description="清脆有活力",
        tone_description="热情开朗，善于举例",
        persona="互联网企业技术总监，曾参与多个AI项目落地",
        core_viewpoint="AI将创造更多新型工作岗位，但需要重视技能转型培训"
    )
]

# 创建播客配置
podcast_form = PodcastCustomForm(
    topic="人工智能对未来工作的影响",
    title="AI时代：机遇还是挑战？",
    atmosphere=DiscussionAtmosphere.SERIOUS_DEEP,
    target_duration="5分钟",
    language_style=LanguageStyle.COLLOQUIAL,
    characters=characters
)
```

---

## AI生成行为说明

### 1. emotion字段的作用

- **用途**：标注角色的情感状态（如：开心、好奇、思考、严肃等）
- **处理**：此字段用于后期TTS情感控制，**不会被朗读出来**
- **示例**：`"emotion": "好奇"`

### 2. content字段的规则

**✅ 正确的content格式**：
```json
{
  "character_name": "李博士",
  "content": "欢迎大家收听今天的节目！我们将探讨AI对工作的影响。",
  "emotion": "开心"
}
```

**❌ 错误的content格式**（不要这样）：
```json
{
  "character_name": "李博士",
  "content": "欢迎大家收听今天的节目！我们将探讨AI对工作的影响。 开心",
  "emotion": "开心"
}
```

```json
{
  "character_name": "李博士",
  "content": "（开心地）欢迎大家收听今天的节目！",
  "emotion": "开心"
}
```

### 3. 文本清理机制

系统具有**双重清理机制**确保输出纯净：

1. **第一道防线**：剧本生成阶段，AI生成后立即清理
2. **第二道防线**：TTS调用前，再次清理确保万无一失

**自动清理的内容**：
- 句末情绪词：`"...影响。 开心"` → `"...影响。"`
- 括号标注：`"(开心)大家好"` → `"大家好"`
- 语气描述：`"以平静的语气说这句话"` → `"说这句话"`
- 舞台指示：`"【微笑】你好"` → `"你好"`
- 其他40+种提示词格式

---

## 语气描述(tone_description)的使用

### 作用

`tone_description` 字段帮助AI理解角色的**说话风格**，从而生成更符合人设的对话内容。

### 推荐的描述方式

**维度组合**：性格特点 + 表达方式

| 性格特点 | 表达方式 | 完整示例 |
|---------|---------|----------|
| 平和、冷静、严谨 | 专业、逻辑清晰、善于分析 | "平和专业，逻辑清晰" |
| 热情、活泼、开朗 | 善于举例、生动形象、富有感染力 | "热情开朗，善于用例子说明" |
| 幽默、风趣、轻松 | 善于调节气氛、用比喻、接地气 | "幽默风趣，善于打比方" |
| 好奇、求知、谦虚 | 善于提问、引导讨论、倾听 | "好奇求知，善于提出关键问题" |
| 严肃、认真、权威 | 数据导向、引用研究、强调风险 | "严谨理性，注重数据支撑" |

### 常见场景示例

**学术讨论播客**：
```json
{
  "name": "教授",
  "tone_description": "严谨理性，善于引用研究成果，注重逻辑论证"
}
```

**商业访谈播客**：
```json
{
  "name": "CEO",
  "tone_description": "自信果断，善于分享实战经验，注重实效"
}
```

**轻松聊天播客**：
```json
{
  "name": "主播",
  "tone_description": "幽默风趣，善于调节气氛，接地气"
}
```

---

## 注意事项

1. **音色描述 vs 语气描述**：
   - `voice_description`：物理声音特征（沉稳、清脆、浑厚等）→ 影响TTS选择
   - `tone_description`：说话风格和态度（专业、幽默、严谨等）→ 影响AI生成内容

2. **人设身份 vs 核心观点**：
   - `persona`：角色的背景和身份
   - `core_viewpoint`：角色在本次讨论中的立场和观点

3. **保持一致性**：
   - 确保角色的音色、语气、人设、观点相互协调
   - 例如：资深专家通常配置"沉稳"音色 + "严谨专业"语气

---

## 测试方法

### 1. 重启服务器

```bash
python run_server.py
```

### 2. 使用新格式创建播客

提供包含 `tone_description` 字段的角色配置。

### 3. 检查生成的剧本

确认：
- ✅ AI正确理解了语气风格
- ✅ 对话内容符合角色人设
- ✅ content字段中无任何提示词

### 4. 验证音频输出

确认：
- ✅ TTS没有朗读情绪词
- ✅ 音频流畅自然
- ✅ 声音符合音色描述

---

## 常见问题

**Q: AI仍然在content中生成了情绪词怎么办？**

A: 系统有双重清理机制，即使AI生成了，也会被自动清理。如果仍有遗漏，请提供具体示例以便优化清理规则。

**Q: tone_description可以不填吗？**

A: 该字段为必填项，但可以填写简单的描述如"自然"、"正常"等。更详细的描述会帮助AI生成更符合预期的对话。

**Q: 如何确认音色映射是否正确？**

A: 查看 `src/backend/app/services/indextts_service.py` 中的 `character_voice_mapping` 字典，确认你的音色描述有对应的样本文件。

---

## 更新日志

**2025-01-XX**：
- ✅ 添加 `tone_description` 字段
- ✅ 优化AI生成Prompt，明确区分emotion和content
- ✅ 强化文本清理规则，支持句末独立情绪词格式
- ✅ 添加双重清理机制（剧本生成 + TTS调用）