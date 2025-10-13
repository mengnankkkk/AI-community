"""
音色样本库API路由
提供预设音色样本查询和自定义音频上传功能
"""
from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from fastapi.responses import FileResponse
from typing import List, Dict, Optional
import os
import shutil
import logging
from pathlib import Path
from pydantic import BaseModel

from ..core.config import settings
from ..services.voice_sample_manager import voice_sample_manager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/voice-samples", tags=["voice-samples"])


class VoiceSampleInfo(BaseModel):
    """音色样本信息"""
    id: str
    name: str
    file_path: str
    file_size: int
    description: Optional[str] = None
    tags: Optional[List[str]] = None
    is_custom: bool = False  # 是否为用户上传


# CosyVoice官方音色列表（阿里云百炼）
COSYVOICE_VOICES = [
    {
        "id": "longwan_v2",
        "name": "龙湾（男声-标准）",
        "description": "标准男声，沉稳大气，适合专业播客",
        "tags": ["男声", "标准", "沉稳", "专业"],
        "gender": "male",
        "provider": "cosyvoice"
    },
    {
        "id": "longyuan_v2",
        "name": "龙渊（男声-浑厚）",
        "description": "浑厚男声，富有磁性，适合深度访谈",
        "tags": ["男声", "浑厚", "磁性", "深沉"],
        "gender": "male",
        "provider": "cosyvoice"
    },
    {
        "id": "longxiaochun_v2",
        "name": "龙小春（女声-标准）",
        "description": "标准女声，清晰自然，适合通用场景",
        "tags": ["女声", "标准", "清晰", "自然"],
        "gender": "female",
        "provider": "cosyvoice"
    },
    {
        "id": "longxiaoxia_v2",
        "name": "龙小夏（女声-温暖）",
        "description": "温暖女声，亲和力强，适合情感内容",
        "tags": ["女声", "温暖", "亲切", "柔和"],
        "gender": "female",
        "provider": "cosyvoice"
    },
    {
        "id": "longxiaoyuan_v2",
        "name": "龙小媛（女声-活力）",
        "description": "活力女声，朝气蓬勃，适合轻松话题",
        "tags": ["女声", "活力", "年轻", "热情"],
        "gender": "female",
        "provider": "cosyvoice"
    }
]


@router.get("/presets", summary="获取预设音色样本列表")
async def list_preset_samples() -> Dict:
    """
    获取所有预设的音色样本

    优先返回CosyVoice官方音色，作为后备返回本地音色样本文件
    """
    try:
        # 检查是否启用CosyVoice
        tts_engine = os.getenv("TTS_ENGINE", "").lower()
        logger.info(f"TTS_ENGINE环境变量: '{tts_engine}', CosyVoice音色数量: {len(COSYVOICE_VOICES)}")

        if tts_engine == "cosyvoice":
            # 返回CosyVoice官方音色
            logger.info(f"返回CosyVoice官方音色列表，共{len(COSYVOICE_VOICES)}个音色")
            return {
                "success": True,
                "total": len(COSYVOICE_VOICES),
                "samples": COSYVOICE_VOICES,
                "provider": "cosyvoice"
            }

        # 其他引擎返回本地音色样本文件
        samples = voice_sample_manager.list_available_samples()

        # 转换为前端格式
        preset_samples = []
        for sample in samples:
            sample_info = {
                "id": Path(sample["filename"]).stem,
                "name": _get_sample_display_name(sample["filename"]),
                "file_path": sample["path"],
                "file_size": sample["size"],
                "description": _get_sample_description(sample["filename"]),
                "tags": _get_sample_tags(sample["filename"]),
                "is_custom": False,
                "provider": "local"
            }
            preset_samples.append(sample_info)

        return {
            "success": True,
            "total": len(preset_samples),
            "samples": preset_samples,
            "provider": "local"
        }

    except Exception as e:
        logger.error(f"获取预设音色样本失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取音色样本失败: {str(e)}")


@router.post("/upload", summary="上传自定义音色样本")
async def upload_custom_sample(
    file: UploadFile = File(..., description="音频文件（WAV格式，建议3-10秒）"),
    name: Optional[str] = Form(None, description="音色名称"),
    description: Optional[str] = Form(None, description="音色描述")
) -> Dict:
    """
    上传自定义音色样本文件

    Args:
        file: 音频文件（建议WAV格式，3-10秒纯净人声）
        name: 音色名称（可选）
        description: 音色描述（可选）

    Returns:
        上传成功的音色信息
    """
    try:
        # 验证文件类型
        if not file.filename.lower().endswith(('.wav', '.mp3', '.m4a', '.ogg')):
            raise HTTPException(
                status_code=400,
                detail="仅支持音频格式: WAV, MP3, M4A, OGG"
            )

        # 验证文件大小（最大10MB）
        MAX_SIZE = 10 * 1024 * 1024  # 10MB
        file_content = await file.read()
        if len(file_content) > MAX_SIZE:
            raise HTTPException(
                status_code=400,
                detail="文件过大，最大支持10MB"
            )

        # 创建自定义音色目录
        custom_dir = os.path.join(settings.uploads_dir, "custom_voices")
        os.makedirs(custom_dir, exist_ok=True)

        # 生成唯一文件名
        import uuid
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_id = str(uuid.uuid4())[:8]
        file_ext = Path(file.filename).suffix
        safe_filename = f"custom_{timestamp}_{unique_id}{file_ext}"

        # 保存文件
        file_path = os.path.join(custom_dir, safe_filename)
        with open(file_path, 'wb') as f:
            f.write(file_content)

        logger.info(f"上传自定义音色样本: {file_path}")

        # 如果是非WAV格式，转换为WAV
        if not file_path.endswith('.wav'):
            wav_path = _convert_to_wav(file_path)
            if wav_path:
                # 删除原文件，使用WAV
                os.remove(file_path)
                file_path = wav_path
                safe_filename = Path(wav_path).name

        return {
            "success": True,
            "sample": {
                "id": Path(safe_filename).stem,
                "name": name or f"自定义音色_{unique_id}",
                "file_path": file_path,
                "file_size": os.path.getsize(file_path),
                "description": description or "用户上传的自定义音色",
                "is_custom": True,
                "created_at": datetime.now().isoformat()
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"上传音色样本失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"上传失败: {str(e)}")


@router.get("/custom", summary="获取用户上传的音色列表")
async def list_custom_samples() -> Dict:
    """
    获取所有用户上传的自定义音色样本
    """
    try:
        custom_dir = os.path.join(settings.uploads_dir, "custom_voices")

        if not os.path.exists(custom_dir):
            return {
                "success": True,
                "total": 0,
                "samples": []
            }

        custom_samples = []
        for filename in os.listdir(custom_dir):
            if filename.lower().endswith(('.wav', '.mp3', '.m4a')):
                file_path = os.path.join(custom_dir, filename)
                stat = os.stat(file_path)

                custom_samples.append({
                    "id": Path(filename).stem,
                    "name": Path(filename).stem.replace("custom_", "自定义_"),
                    "file_path": file_path,
                    "file_size": stat.st_size,
                    "description": "用户上传的音色",
                    "is_custom": True,
                    "created_at": stat.st_ctime
                })

        # 按创建时间倒序排序
        custom_samples.sort(key=lambda x: x["created_at"], reverse=True)

        return {
            "success": True,
            "total": len(custom_samples),
            "samples": custom_samples
        }

    except Exception as e:
        logger.error(f"获取自定义音色列表失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取失败: {str(e)}")


@router.delete("/{sample_id}", summary="删除自定义音色")
async def delete_custom_sample(sample_id: str) -> Dict:
    """
    删除用户上传的自定义音色

    Args:
        sample_id: 音色ID
    """
    try:
        custom_dir = os.path.join(settings.uploads_dir, "custom_voices")

        # 查找匹配的文件
        deleted = False
        for filename in os.listdir(custom_dir):
            if Path(filename).stem == sample_id:
                file_path = os.path.join(custom_dir, filename)
                os.remove(file_path)
                logger.info(f"删除自定义音色: {file_path}")
                deleted = True
                break

        if not deleted:
            raise HTTPException(status_code=404, detail="音色不存在")

        return {
            "success": True,
            "message": "删除成功"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除音色失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"删除失败: {str(e)}")


# 辅助函数

def _get_sample_display_name(filename: str) -> str:
    """获取音色样本的显示名称"""
    name_mapping = {
        "voice_standard.wav": "标准音色",
        "voice_male.wav": "男声",
        "voice_female.wav": "女声",
        "voice_deep.wav": "浑厚男声",
        "voice_crisp.wav": "清脆女声",
        "voice_warm.wav": "温暖音色",
        "voice_steady.wav": "沉稳音色",
        "voice_energetic.wav": "活力音色",
        "voice_magnetic.wav": "磁性音色",
        "voice_intellectual.wav": "知性音色",
        "voice_baritone.wav": "男中音",
        "default_voice.wav": "默认音色"
    }
    return name_mapping.get(filename, Path(filename).stem)


def _get_sample_description(filename: str) -> str:
    """获取音色样本的描述"""
    desc_mapping = {
        "voice_standard.wav": "中性标准音色，适合通用场景",
        "voice_male.wav": "标准男声，清晰自然",
        "voice_female.wav": "标准女声，亲切温和",
        "voice_deep.wav": "浑厚的男声，适合严肃内容",
        "voice_crisp.wav": "清脆的女声，适合活泼内容",
        "voice_warm.wav": "温暖的音色，适合情感内容",
        "voice_steady.wav": "沉稳的音色，适合专业内容",
        "voice_energetic.wav": "有活力的音色，适合年轻化内容",
        "voice_magnetic.wav": "有磁性的音色，适合深度访谈",
        "voice_intellectual.wav": "知性的音色，适合学术讨论",
        "voice_baritone.wav": "男中音，适合播音主持"
    }
    return desc_mapping.get(filename, "预设音色样本")


def _get_sample_tags(filename: str) -> List[str]:
    """获取音色样本的标签"""
    tags_mapping = {
        "voice_standard.wav": ["通用", "标准", "中性"],
        "voice_male.wav": ["男声", "标准"],
        "voice_female.wav": ["女声", "标准"],
        "voice_deep.wav": ["男声", "浑厚", "深沉"],
        "voice_crisp.wav": ["女声", "清脆", "活泼"],
        "voice_warm.wav": ["温暖", "亲切"],
        "voice_steady.wav": ["沉稳", "专业"],
        "voice_energetic.wav": ["活力", "年轻"],
        "voice_magnetic.wav": ["磁性", "深度"],
        "voice_intellectual.wav": ["知性", "学术"],
        "voice_baritone.wav": ["男中音", "播音"]
    }
    return tags_mapping.get(filename, ["预设"])


def _convert_to_wav(input_path: str) -> Optional[str]:
    """
    将音频文件转换为WAV格式

    Args:
        input_path: 输入文件路径

    Returns:
        转换后的WAV文件路径，失败返回None
    """
    try:
        from pydub import AudioSegment

        # 加载音频
        audio = AudioSegment.from_file(input_path)

        # 转换为WAV（16kHz, 单声道）
        audio = audio.set_frame_rate(16000).set_channels(1)

        # 生成输出路径
        output_path = str(Path(input_path).with_suffix('.wav'))

        # 导出WAV
        audio.export(output_path, format='wav')

        logger.info(f"音频格式转换: {input_path} -> {output_path}")
        return output_path

    except Exception as e:
        logger.error(f"音频格式转换失败: {str(e)}")
        return None


@router.get("/preview/{sample_id}", summary="预览音色样本")
async def preview_sample(sample_id: str):
    """
    预览音色样本音频

    Args:
        sample_id: 音色ID或文件名（不含扩展名）

    Returns:
        音频文件流
    """
    try:
        # 首先在预设音色中查找
        voice_samples_dir = "voice_samples"

        # 尝试多种可能的文件名
        possible_files = [
            f"{sample_id}.wav",
            f"{sample_id}.mp3",
            sample_id if sample_id.endswith(('.wav', '.mp3')) else None
        ]

        # 在预设目录中查找
        for filename in possible_files:
            if filename:
                preset_path = os.path.join(voice_samples_dir, filename)
                if os.path.exists(preset_path):
                    return FileResponse(
                        path=preset_path,
                        media_type="audio/wav" if filename.endswith('.wav') else "audio/mpeg",
                        filename=filename
                    )

        # 在自定义音色中查找
        custom_dir = os.path.join(settings.uploads_dir, "custom_voices")
        if os.path.exists(custom_dir):
            for filename in os.listdir(custom_dir):
                if Path(filename).stem == sample_id:
                    custom_path = os.path.join(custom_dir, filename)
                    return FileResponse(
                        path=custom_path,
                        media_type="audio/wav" if filename.endswith('.wav') else "audio/mpeg",
                        filename=filename
                    )

        raise HTTPException(status_code=404, detail=f"音色样本不存在: {sample_id}")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"预览音色样本失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"预览失败: {str(e)}")

