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
    name: str = Field(..., description="角色姓名/代称")
    voice_description: str = Field(..., description="音色描述（如：沉稳、清脆、有磁性等）或音色ID（nihal_tts）")
    voice_file: Optional[str] = Field(None, description="音色样本文件路径（indextts2_gradio使用，优先级高于voice_description）")
    tone_description: str = Field(..., description="语气描述（如：平和、热情、专业、幽默等）")
    persona: str = Field(..., description="人设/身份描述（如：资深AI专家、企业管理者等）")
    core_viewpoint: str = Field(..., description="核心观点（该角色在讨论中持有的主要立场）")

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

class PodcastGenerationRequest(BaseModel):
    custom_form: PodcastCustomForm = Field(..., description="播客定制单")

class PodcastGenerationResponse(BaseModel):
    task_id: str = Field(..., description="任务ID")
    status: str = Field(..., description="生成状态")
    script: Optional[PodcastScript] = Field(None, description="生成的剧本")
    audio_url: Optional[str] = Field(None, description="音频文件URL")
    message: str = Field(..., description="状态消息")