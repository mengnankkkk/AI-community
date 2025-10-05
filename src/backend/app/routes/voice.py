"""
音色库API路由
提供音色查询、分类、推荐等功能
"""
from fastapi import APIRouter, HTTPException, Query
from typing import List, Dict, Optional
from ..config.voice_library import (
    get_voice_by_id,
    get_voices_by_gender,
    get_voices_by_tag,
    search_voices,
    get_recommended_voices_for_scene,
    get_all_voices_list,
    get_voice_categories,
    VOICE_STYLES,
    SCENE_RECOMMENDATIONS,
    VoiceInfo
)

router = APIRouter(prefix="/voices", tags=["voices"])


@router.get("/", summary="获取所有音色")
async def list_all_voices():
    """
    获取所有可用音色列表

    返回所有音色的详细信息，包括ID、名称、性别、风格等
    """
    try:
        voices = get_all_voices_list()
        return {
            "success": True,
            "total": len(voices),
            "voices": voices
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取音色列表失败: {str(e)}")


@router.get("/categories", summary="按分类获取音色")
async def get_voices_by_categories():
    """
    按性别分类获取音色

    返回按男声、女声、特色分组的音色列表
    """
    try:
        categories = get_voice_categories()
        return {
            "success": True,
            "categories": categories
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取音色分类失败: {str(e)}")


@router.get("/styles", summary="获取音色风格分类")
async def get_voice_styles():
    """
    获取音色风格分类

    返回按风格（专业权威、亲切温暖等）分组的音色推荐
    """
    try:
        return {
            "success": True,
            "styles": VOICE_STYLES
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取音色风格失败: {str(e)}")


@router.get("/{voice_id}", summary="获取指定音色详情")
async def get_voice_detail(voice_id: str):
    """
    根据ID获取音色详细信息

    Args:
        voice_id: 音色ID（如：alloy, echo, nova等）

    Returns:
        音色的完整信息
    """
    try:
        voice = get_voice_by_id(voice_id)
        if not voice:
            raise HTTPException(status_code=404, detail=f"音色不存在: {voice_id}")

        return {
            "success": True,
            "voice": voice.model_dump()
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取音色详情失败: {str(e)}")


@router.get("/filter/gender/{gender}", summary="按性别筛选音色")
async def filter_voices_by_gender(gender: str):
    """
    按性别筛选音色

    Args:
        gender: 性别类型（male/female/neutral）

    Returns:
        符合条件的音色列表
    """
    try:
        if gender not in ["male", "female", "neutral"]:
            raise HTTPException(status_code=400, detail="性别参数必须是 male, female 或 neutral")

        voices = get_voices_by_gender(gender)
        return {
            "success": True,
            "gender": gender,
            "total": len(voices),
            "voices": [voice.model_dump() for voice in voices]
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"筛选音色失败: {str(e)}")


@router.get("/filter/tag/{tag}", summary="按标签筛选音色")
async def filter_voices_by_tag(tag: str):
    """
    按标签筛选音色

    Args:
        tag: 标签（如：磁性、清晰、温暖等）

    Returns:
        符合条件的音色列表
    """
    try:
        voices = get_voices_by_tag(tag)
        return {
            "success": True,
            "tag": tag,
            "total": len(voices),
            "voices": [voice.model_dump() for voice in voices]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"筛选音色失败: {str(e)}")


@router.get("/search", summary="搜索音色")
async def search_voice(
    q: str = Query(..., description="搜索关键词", min_length=1)
):
    """
    搜索音色

    根据关键词搜索音色名称、风格、标签、描述等

    Args:
        q: 搜索关键词

    Returns:
        匹配的音色列表
    """
    try:
        voices = search_voices(q)
        return {
            "success": True,
            "query": q,
            "total": len(voices),
            "voices": [voice.model_dump() for voice in voices]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"搜索音色失败: {str(e)}")


@router.get("/recommend/scene/{scene}", summary="场景推荐音色")
async def recommend_voices_for_scene(
    scene: str,
    role: str = Query("host", description="角色类型（host/guest/narrator等）")
):
    """
    根据播客场景推荐合适的音色

    Args:
        scene: 场景类型（academic/business/casual/storytelling/news）
        role: 角色类型（默认为host）

    Returns:
        推荐的音色ID列表及场景信息
    """
    try:
        if scene not in SCENE_RECOMMENDATIONS:
            available_scenes = ", ".join(SCENE_RECOMMENDATIONS.keys())
            raise HTTPException(
                status_code=400,
                detail=f"场景类型无效。可用场景: {available_scenes}"
            )

        recommended_voice_ids = get_recommended_voices_for_scene(scene, role)

        # 获取推荐音色的详细信息
        recommended_voices = []
        for voice_id in recommended_voice_ids:
            voice = get_voice_by_id(voice_id)
            if voice:
                recommended_voices.append(voice.model_dump())

        scene_info = SCENE_RECOMMENDATIONS[scene]

        return {
            "success": True,
            "scene": scene_info["name"],
            "role": role,
            "total": len(recommended_voices),
            "voices": recommended_voices
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取推荐音色失败: {str(e)}")


@router.get("/recommend/auto", summary="智能推荐音色")
async def auto_recommend_voices(
    persona: Optional[str] = Query(None, description="角色人设描述"),
    tone: Optional[str] = Query(None, description="语气风格描述"),
    gender_preference: Optional[str] = Query(None, description="性别偏好（male/female）")
):
    """
    根据角色人设和语气风格智能推荐音色

    Args:
        persona: 角色人设（如：资深AI专家、企业管理者）
        tone: 语气风格（如：平和专业、热情开朗）
        gender_preference: 性别偏好

    Returns:
        智能推荐的音色列表
    """
    try:
        # 简单的关键词匹配推荐逻辑
        recommended_voices = []

        # 根据关键词推荐
        if persona or tone:
            search_text = f"{persona or ''} {tone or ''}".lower()

            # 专业、权威、严肃 -> 推荐沉稳男声
            if any(keyword in search_text for keyword in ["专家", "博士", "教授", "权威", "专业", "严谨"]):
                recommended_voices.extend(["onyx", "sage", "echo", "ash"])

            # 热情、活力、年轻 -> 推荐活力女声
            elif any(keyword in search_text for keyword in ["热情", "活力", "年轻", "开朗"]):
                recommended_voices.extend(["shimmer", "nova", "alloy"])

            # 温暖、亲切、治愈 -> 推荐温暖女声
            elif any(keyword in search_text for keyword in ["温暖", "亲切", "温柔", "治愈"]):
                recommended_voices.extend(["coral", "nova", "verse"])

            # 故事、叙述、文艺 -> 推荐叙述型音色
            elif any(keyword in search_text for keyword in ["故事", "叙述", "文艺", "诗意"]):
                recommended_voices.extend(["fable", "verse", "ballad"])

            # 默认推荐
            else:
                recommended_voices.extend(["alloy", "nova", "echo", "shimmer"])

        # 性别偏好筛选
        if gender_preference:
            gender_voices = get_voices_by_gender(gender_preference)
            gender_voice_ids = [v.id for v in gender_voices]
            recommended_voices = [v for v in recommended_voices if v in gender_voice_ids]

        # 去重并获取详细信息
        unique_voice_ids = list(dict.fromkeys(recommended_voices))[:5]  # 最多返回5个

        voices_detail = []
        for voice_id in unique_voice_ids:
            voice = get_voice_by_id(voice_id)
            if voice:
                voices_detail.append(voice.model_dump())

        return {
            "success": True,
            "criteria": {
                "persona": persona,
                "tone": tone,
                "gender_preference": gender_preference
            },
            "total": len(voices_detail),
            "voices": voices_detail
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"智能推荐失败: {str(e)}")


@router.get("/scenes", summary="获取所有场景类型")
async def list_scenes():
    """
    获取所有可用的播客场景类型

    Returns:
        场景列表及每个场景的推荐角色类型
    """
    try:
        return {
            "success": True,
            "scenes": SCENE_RECOMMENDATIONS
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取场景列表失败: {str(e)}")