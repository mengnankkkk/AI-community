"""
音色库配置和管理
支持阿里云 CosyVoice 的5种预设音色
"""

from typing import Dict, List, Optional
from pydantic import BaseModel


class VoiceInfo(BaseModel):
    """音色信息"""
    id: str  # 音色ID（用于API调用）
    name: str  # 显示名称
    name_en: str  # 英文名称
    gender: str  # 性别：male/female/neutral
    style: str  # 风格描述
    tags: List[str]  # 标签
    description: str  # 详细描述
    sample_url: Optional[str] = None  # 音色样本URL


# 阿里云 CosyVoice 音色库配置（v1格式，不带_v2后缀）
COSYVOICE_VOICE_LIBRARY = {
    # 男声 - 标准
    "longwan": VoiceInfo(
        id="longwan",
        name="龙湾",
        name_en="Longwan",
        gender="male",
        style="标准、沉稳",
        tags=["男声", "标准", "沉稳", "专业"],
        description="标准沉稳的男声，适合专业播客和商业内容",
        sample_url=None
    ),

    # 男声 - 浑厚
    "longyuan": VoiceInfo(
        id="longyuan",
        name="龙渊",
        name_en="Longyuan",
        gender="male",
        style="浑厚、磁性",
        tags=["男声", "浑厚", "磁性", "深沉"],
        description="浑厚富有磁性的男声，适合深度访谈和严肃话题",
        sample_url=None
    ),

    # 女声 - 标准
    "longxiaochun": VoiceInfo(
        id="longxiaochun",
        name="龙小春",
        name_en="Longxiaochun",
        gender="female",
        style="标准、清晰",
        tags=["女声", "标准", "清晰", "自然"],
        description="标准清晰的女声，适合通用场景和各类播客",
        sample_url=None
    ),

    # 女声 - 温暖
    "longxiaoxia": VoiceInfo(
        id="longxiaoxia",
        name="龙小夏",
        name_en="Longxiaoxia",
        gender="female",
        style="温暖、亲切",
        tags=["女声", "温暖", "亲切", "柔和"],
        description="温暖亲切的女声，适合情感内容和治愈系话题",
        sample_url=None
    ),

    # 女声 - 活力
    "longxiaoyuan": VoiceInfo(
        id="longxiaoyuan",
        name="龙小媛",
        name_en="Longxiaoyuan",
        gender="female",
        style="活力、年轻",
        tags=["女声", "活力", "年轻", "热情"],
        description="充满活力的年轻女声，适合轻松话题和生活内容",
        sample_url=None
    ),
}


# 音色标签分类
VOICE_CATEGORIES = {
    "male": {
        "name": "男声",
        "voices": ["longwan", "longyuan"]  # v1格式（不带_v2后缀）
    },
    "female": {
        "name": "女声",
        "voices": ["longxiaochun", "longxiaoxia", "longxiaoyuan"]  # v1格式（不带_v2后缀）
    }
}


# 音色风格分类
VOICE_STYLES = {
    "professional": {
        "name": "专业权威",
        "voices": ["longwan", "longyuan"],  # v1格式（不带_v2后缀）
        "description": "适合专业讨论、商业内容、学术分享"
    },
    "friendly": {
        "name": "亲切温暖",
        "voices": ["longxiaochun", "longxiaoxia"],  # v1格式（不带_v2后缀）
        "description": "适合日常对话、生活分享、情感内容"
    },
    "energetic": {
        "name": "活力青春",
        "voices": ["longxiaoyuan"],  # v1格式（不带_v2后缀）
        "description": "适合轻松话题、娱乐内容、年轻群体"
    }
}


# 场景推荐配置
SCENE_RECOMMENDATIONS = {
    "academic": {
        "name": "学术讨论",
        "recommended_voices": {
            "host": ["longwan", "longyuan"],  # v1格式（不带_v2后缀）
            "guest": ["longxiaochun"]  # v1格式（不带_v2后缀）
        }
    },
    "business": {
        "name": "商业访谈",
        "recommended_voices": {
            "host": ["longwan", "longyuan"],  # v1格式（不带_v2后缀）
            "guest": ["longxiaochun", "longxiaoxia"]  # v1格式（不带_v2后缀）
        }
    },
    "casual": {
        "name": "轻松闲聊",
        "recommended_voices": {
            "host": ["longxiaoyuan", "longxiaoxia"],  # v1格式（不带_v2后缀）
            "guest": ["longwan", "longxiaochun"]  # v1格式（不带_v2后缀）
        }
    },
    "news": {
        "name": "新闻播报",
        "recommended_voices": {
            "anchor": ["longwan", "longxiaochun"]  # v1格式（不带_v2后缀）
        }
    }
}


def get_voice_by_id(voice_id: str) -> Optional[VoiceInfo]:
    """根据ID获取音色信息"""
    return COSYVOICE_VOICE_LIBRARY.get(voice_id)


def get_voices_by_gender(gender: str) -> List[VoiceInfo]:
    """根据性别筛选音色"""
    return [
        voice for voice in COSYVOICE_VOICE_LIBRARY.values()
        if voice.gender == gender
    ]


def get_voices_by_tag(tag: str) -> List[VoiceInfo]:
    """根据标签筛选音色"""
    return [
        voice for voice in COSYVOICE_VOICE_LIBRARY.values()
        if tag in voice.tags
    ]


def search_voices(keyword: str) -> List[VoiceInfo]:
    """搜索音色"""
    keyword = keyword.lower()
    results = []

    for voice in COSYVOICE_VOICE_LIBRARY.values():
        if (keyword in voice.name.lower() or
            keyword in voice.name_en.lower() or
            keyword in voice.style.lower() or
            keyword in voice.description.lower() or
            any(keyword in tag for tag in voice.tags)):
            results.append(voice)

    return results


def get_recommended_voices_for_scene(scene: str, role: str = "host") -> List[str]:
    """获取场景推荐音色"""
    scene_config = SCENE_RECOMMENDATIONS.get(scene)
    if not scene_config:
        return []

    return scene_config["recommended_voices"].get(role, [])


def get_all_voices_list() -> List[Dict]:
    """获取所有音色列表（用于前端展示）"""
    return [
        {
            "id": voice.id,
            "name": voice.name,
            "name_en": voice.name_en,
            "gender": voice.gender,
            "style": voice.style,
            "tags": voice.tags,
            "description": voice.description
        }
        for voice in COSYVOICE_VOICE_LIBRARY.values()
    ]


def get_voice_categories() -> Dict:
    """获取音色分类（用于前端分组展示）"""
    result = {}
    for category_id, category_info in VOICE_CATEGORIES.items():
        result[category_id] = {
            "name": category_info["name"],
            "voices": [
                COSYVOICE_VOICE_LIBRARY[voice_id].model_dump()
                for voice_id in category_info["voices"]
                if voice_id in COSYVOICE_VOICE_LIBRARY
            ]
        }
    return result