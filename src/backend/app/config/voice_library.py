"""
音色库配置和管理
支持NihalGazi TTS的13种预设音色
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


# NihalGazi TTS 音色库配置
NIHAL_VOICE_LIBRARY = {
    # 男声 - 标准
    "alloy": VoiceInfo(
        id="alloy",
        name="合金",
        name_en="Alloy",
        gender="male",
        style="标准、中性",
        tags=["男声", "标准", "通用", "清晰"],
        description="标准清晰的男声，适合各类播客和解说",
        sample_url=None
    ),

    # 男声 - 磁性
    "echo": VoiceInfo(
        id="echo",
        name="回声",
        name_en="Echo",
        gender="male",
        style="有磁性、浑厚",
        tags=["男声", "磁性", "浑厚", "深沉"],
        description="富有磁性的浑厚男声，适合深度访谈和严肃话题",
        sample_url=None
    ),

    # 男声 - 寓言
    "fable": VoiceInfo(
        id="fable",
        name="寓言",
        name_en="Fable",
        gender="male",
        style="叙述、故事感",
        tags=["男声", "叙述", "故事", "温和"],
        description="温和的叙述型男声，适合讲故事和教学内容",
        sample_url=None
    ),

    # 男声 - 沉稳
    "onyx": VoiceInfo(
        id="onyx",
        name="玛瑙",
        name_en="Onyx",
        gender="male",
        style="沉稳、专业",
        tags=["男声", "沉稳", "专业", "权威"],
        description="沉稳专业的男声，适合专家讲解和商业内容",
        sample_url=None
    ),

    # 男声 - 灰烬
    "ash": VoiceInfo(
        id="ash",
        name="灰烬",
        name_en="Ash",
        gender="male",
        style="成熟、低沉",
        tags=["男声", "成熟", "低沉", "稳重"],
        description="成熟低沉的男声，适合严肃话题和新闻播报",
        sample_url=None
    ),

    # 男声 - 智者
    "sage": VoiceInfo(
        id="sage",
        name="智者",
        name_en="Sage",
        gender="male",
        style="智慧、知性",
        tags=["男声", "智慧", "知性", "博学"],
        description="充满智慧感的男声，适合学术讨论和知识分享",
        sample_url=None
    ),

    # 女声 - 标准
    "nova": VoiceInfo(
        id="nova",
        name="新星",
        name_en="Nova",
        gender="female",
        style="清晰、明亮",
        tags=["女声", "清晰", "明亮", "通用"],
        description="清晰明亮的女声，适合各类播客内容",
        sample_url=None
    ),

    # 女声 - 活力
    "shimmer": VoiceInfo(
        id="shimmer",
        name="闪光",
        name_en="Shimmer",
        gender="female",
        style="活力、年轻",
        tags=["女声", "活力", "年轻", "热情"],
        description="充满活力的年轻女声，适合轻松话题和生活内容",
        sample_url=None
    ),

    # 女声 - 珊瑚
    "coral": VoiceInfo(
        id="coral",
        name="珊瑚",
        name_en="Coral",
        gender="female",
        style="温暖、亲切",
        tags=["女声", "温暖", "亲切", "柔和"],
        description="温暖亲切的女声，适合情感类和治愈系内容",
        sample_url=None
    ),

    # 女声 - 诗句
    "verse": VoiceInfo(
        id="verse",
        name="诗句",
        name_en="Verse",
        gender="female",
        style="优雅、抒情",
        tags=["女声", "优雅", "抒情", "艺术"],
        description="优雅抒情的女声，适合文艺和创意内容",
        sample_url=None
    ),

    # 女声 - 民谣
    "ballad": VoiceInfo(
        id="ballad",
        name="民谣",
        name_en="Ballad",
        gender="female",
        style="柔美、歌唱感",
        tags=["女声", "柔美", "歌唱", "音乐"],
        description="柔美带有歌唱感的女声，适合音乐和艺术内容",
        sample_url=None
    ),

    # 特色 - Amuch
    "amuch": VoiceInfo(
        id="amuch",
        name="阿穆奇",
        name_en="Amuch",
        gender="neutral",
        style="特色、独特",
        tags=["特色", "独特", "实验"],
        description="独特的特色音色，适合创意和实验性内容",
        sample_url=None
    ),

    # 特色 - Dan
    "dan": VoiceInfo(
        id="dan",
        name="丹",
        name_en="Dan",
        gender="neutral",
        style="特色、多变",
        tags=["特色", "多变", "个性"],
        description="多变的个性音色，适合多元化内容",
        sample_url=None
    ),
}


# 音色标签分类
VOICE_CATEGORIES = {
    "male": {
        "name": "男声",
        "voices": ["alloy", "echo", "fable", "onyx", "ash", "sage"]
    },
    "female": {
        "name": "女声",
        "voices": ["nova", "shimmer", "coral", "verse", "ballad"]
    },
    "special": {
        "name": "特色",
        "voices": ["amuch", "dan"]
    }
}


# 音色风格分类
VOICE_STYLES = {
    "professional": {
        "name": "专业权威",
        "voices": ["onyx", "echo", "sage", "ash"],
        "description": "适合专业讨论、商业内容、学术分享"
    },
    "friendly": {
        "name": "亲切温暖",
        "voices": ["coral", "nova", "alloy"],
        "description": "适合日常对话、生活分享、情感内容"
    },
    "energetic": {
        "name": "活力青春",
        "voices": ["shimmer", "alloy"],
        "description": "适合轻松话题、娱乐内容、年轻群体"
    },
    "narrative": {
        "name": "叙述故事",
        "voices": ["fable", "verse", "ballad"],
        "description": "适合讲故事、文艺创作、有声读物"
    },
    "special": {
        "name": "创意实验",
        "voices": ["amuch", "dan"],
        "description": "适合创意内容、实验性项目"
    }
}


# 场景推荐配置
SCENE_RECOMMENDATIONS = {
    "academic": {
        "name": "学术讨论",
        "recommended_voices": {
            "host": ["sage", "onyx"],
            "guest": ["echo", "ash", "nova"]
        }
    },
    "business": {
        "name": "商业访谈",
        "recommended_voices": {
            "host": ["onyx", "echo"],
            "guest": ["alloy", "nova", "coral"]
        }
    },
    "casual": {
        "name": "轻松闲聊",
        "recommended_voices": {
            "host": ["alloy", "shimmer"],
            "guest": ["nova", "coral", "fable"]
        }
    },
    "storytelling": {
        "name": "讲故事",
        "recommended_voices": {
            "narrator": ["fable", "verse"],
            "character": ["ballad", "coral", "alloy"]
        }
    },
    "news": {
        "name": "新闻播报",
        "recommended_voices": {
            "anchor": ["ash", "onyx", "nova"]
        }
    }
}


def get_voice_by_id(voice_id: str) -> Optional[VoiceInfo]:
    """根据ID获取音色信息"""
    return NIHAL_VOICE_LIBRARY.get(voice_id)


def get_voices_by_gender(gender: str) -> List[VoiceInfo]:
    """根据性别筛选音色"""
    return [
        voice for voice in NIHAL_VOICE_LIBRARY.values()
        if voice.gender == gender
    ]


def get_voices_by_tag(tag: str) -> List[VoiceInfo]:
    """根据标签筛选音色"""
    return [
        voice for voice in NIHAL_VOICE_LIBRARY.values()
        if tag in voice.tags
    ]


def search_voices(keyword: str) -> List[VoiceInfo]:
    """搜索音色"""
    keyword = keyword.lower()
    results = []

    for voice in NIHAL_VOICE_LIBRARY.values():
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
        for voice in NIHAL_VOICE_LIBRARY.values()
    ]


def get_voice_categories() -> Dict:
    """获取音色分类（用于前端分组展示）"""
    result = {}
    for category_id, category_info in VOICE_CATEGORIES.items():
        result[category_id] = {
            "name": category_info["name"],
            "voices": [
                NIHAL_VOICE_LIBRARY[voice_id].model_dump()
                for voice_id in category_info["voices"]
                if voice_id in NIHAL_VOICE_LIBRARY
            ]
        }
    return result