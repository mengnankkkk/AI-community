from pydantic import BaseModel, Field
from typing import List, Optional
from enum import Enum

class DiscussionAtmosphere(str, Enum):
    RELAXED_HUMOROUS = "relaxed_humorous"
    SERIOUS_DEEP = "serious_deep"
    HEATED_DEBATE = "heated_debate"
    WARM_HEALING = "warm_healing"

class LanguageStyle(str, Enum):
    COLLOQUIAL = "colloquial"
    FORMAL = "formal"
    ACADEMIC = "academic"
    INTERNET = "internet"

class CharacterRole(BaseModel):
    # === 第一层：核心身份（必填）===
    name: str = Field(..., description="角色姓名/代称")
    persona: str = Field(..., description="人设/身份描述（如：资深AI专家、企业管理者等）")
    core_viewpoint: str = Field(..., description="核心观点（该角色在讨论中持有的主要立场）")

    # 音色相关（保留原有字段）
    voice_description: str = Field(..., description="音色描述（如：沉稳、清脆、有磁性等）或音色ID（nihal_tts）")
    voice_file: Optional[str] = Field(None, description="音色样本文件路径（indextts2_gradio使用，优先级高于voice_description）")
    tone_description: str = Field(..., description="语气描述（如：平和、热情、专业、幽默等）")

    # === 第二层：深度构建（可选，高级设置）===
    # 1. 背景故事
    backstory: Optional[str] = Field(None, description="关键经历（如：大学毕业后一直留在北京，经历过几次互联网浪潮）")
    backstory_impact: Optional[str] = Field(None, description="背景如何塑造了角色（如：让他对技术趋势敏感，但缺乏安全感）")

    # 2. 沟通风格
    language_habits: Optional[str] = Field(None, description="语言习惯（如：喜欢用代码打比方，解释问题条理清晰）")
    catchphrases: Optional[str] = Field(None, description="口头禅/常用语（如：'这个逻辑是通的'、'简单来说就是'）")
    speech_pace: Optional[str] = Field(None, description="语速/音调特点（如：语速偏快，讨论技术问题时会变兴奋）")

    # 3. 内在价值观与矛盾
    core_values: Optional[str] = Field(None, description="核心价值观（如：相信技术能解决一切问题，崇尚逻辑和效率）")
    inner_contradictions: Optional[str] = Field(None, description="内在矛盾（如：是技术理想主义者，但现实中常因办公室政治感到疲惫）")

    # 4. 隐藏动机
    hidden_motivation: Optional[str] = Field(None, description="隐藏动机/秘密（如：私下里在学写小说，渴望创造有温度的东西）")

class PodcastCustomForm(BaseModel):
    # 核心主题
    topic: str = Field(..., description="播客主题")
    title: Optional[str] = Field(None, description="播客标题")

    # 风格与氛围
    atmosphere: DiscussionAtmosphere = Field(..., description="讨论氛围")
    target_duration: str = Field(..., description="目标时长")
    language_style: LanguageStyle = Field(..., description="语言风格")

    # 角色设定
    characters: List[CharacterRole] = Field(..., min_items=2, max_items=5, description="角色列表")

    # 补充素材
    background_materials: Optional[str] = Field(None, description="背景资料")

class ScriptDialogue(BaseModel):
    character_name: str = Field(..., description="角色名称")
    content: str = Field(..., description="对话内容")
    emotion: Optional[str] = Field(None, description="情感标注")

class PodcastScript(BaseModel):
    title: str = Field(..., description="播客标题")
    topic: str = Field(..., description="播客主题")
    dialogues: List[ScriptDialogue] = Field(..., description="对话列表")
    estimated_duration: Optional[int] = Field(None, description="预估时长(秒)")
    metadata: Optional[dict] = Field(None, description="元数据（RAG来源等）")

class PodcastGenerationRequest(BaseModel):
    custom_form: PodcastCustomForm = Field(..., description="播客定制单")

class PodcastGenerationResponse(BaseModel):
    task_id: str = Field(..., description="任务ID")
    status: str = Field(..., description="生成状态")
    script: Optional[PodcastScript] = Field(None, description="生成的剧本")
    audio_url: Optional[str] = Field(None, description="音频文件URL")
    message: str = Field(..., description="状态消息")