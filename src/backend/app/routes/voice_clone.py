"""
音色克隆 API 路由
支持 CosyVoice 音色克隆功能
"""
from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from typing import Optional, Dict
import os
import logging
from datetime import datetime
from pydantic import BaseModel

from ..core.config import settings
from ..services.cosyvoice_clone_service import cosyvoice_clone_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/voice-clone", tags=["voice-clone"])


class VoiceCloneRequest(BaseModel):
    """音色克隆请求"""
    audio_url: str
    voice_prefix: str
    voice_name: Optional[str] = None


class VoiceCloneResponse(BaseModel):
    """音色克隆响应"""
    success: bool
    voice_id: Optional[str] = None
    voice_prefix: Optional[str] = None
    voice_name: Optional[str] = None
    status: Optional[str] = None
    message: Optional[str] = None
    error: Optional[str] = None


@router.post("/create", summary="创建音色克隆任务", response_model=VoiceCloneResponse)
async def create_voice_clone(request: VoiceCloneRequest) -> Dict:
    """
    创建音色克隆任务

    Args:
        request: 包含音频URL和音色前缀的请求

    Returns:
        克隆结果
    """
    try:
        # 检查是否启用克隆功能
        if not getattr(settings, 'cosyvoice_enable_clone', True):
            raise HTTPException(
                status_code=403,
                detail="音色克隆功能未启用"
            )

        logger.info(f"开始音色克隆: voice_prefix={request.voice_prefix}, audio_url={request.audio_url}")

        # 调用克隆服务
        result = await cosyvoice_clone_service.clone_voice(
            audio_url=request.audio_url,
            voice_prefix=request.voice_prefix,
            voice_name=request.voice_name
        )

        if not result.get("success"):
            raise HTTPException(
                status_code=500,
                detail=result.get("error", "音色克隆失败")
            )

        logger.info(f"音色克隆成功: {result}")
        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"音色克隆失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"音色克隆失败: {str(e)}")


@router.post("/upload-and-clone", summary="上传音频并克隆音色")
async def upload_and_clone(
    file: UploadFile = File(..., description="音频文件"),
    voice_prefix: str = Form(..., description="音色前缀（不超过10个字符，只包含数字和字母）"),
    voice_name: Optional[str] = Form(None, description="音色名称")
) -> Dict:
    """
    上传音频文件并立即克隆音色

    Args:
        file: 音频文件（WAV/MP3/M4A/AAC格式，最大10MB，至少5秒）
        voice_prefix: 音色前缀
        voice_name: 音色名称（可选）

    Returns:
        克隆结果
    """
    try:
        # 检查是否启用克隆功能
        if not getattr(settings, 'cosyvoice_enable_clone', True):
            raise HTTPException(
                status_code=403,
                detail="音色克隆功能未启用"
            )

        # 验证文件类型
        if not file.filename.lower().endswith(('.wav', '.mp3', '.m4a', '.aac')):
            raise HTTPException(
                status_code=400,
                detail="仅支持音频格式: WAV, MP3, M4A, AAC"
            )

        # 验证文件大小
        file_content = await file.read()
        if len(file_content) > 10 * 1024 * 1024:
            raise HTTPException(
                status_code=400,
                detail="文件过大，最大支持10MB"
            )

        # 保存文件到临时目录
        clone_dir = os.path.join(settings.uploads_dir, "voice_clone_temp")
        os.makedirs(clone_dir, exist_ok=True)

        import uuid
        unique_id = str(uuid.uuid4())[:8]
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        from pathlib import Path
        file_ext = Path(file.filename).suffix
        temp_filename = f"clone_{voice_prefix}_{timestamp}_{unique_id}{file_ext}"
        temp_path = os.path.join(clone_dir, temp_filename)

        # 保存文件
        with open(temp_path, 'wb') as f:
            f.write(file_content)

        logger.info(f"音频文件已保存: {temp_path}")

        # 验证音频文件
        is_valid, error_msg = await cosyvoice_clone_service.validate_audio_for_cloning(temp_path)
        if not is_valid:
            os.remove(temp_path)  # 删除无效文件
            raise HTTPException(status_code=400, detail=error_msg)

        # 生成公网可访问的URL
        # TODO: 需要配置文件服务器或使用对象存储
        # 这里暂时返回本地路径，实际使用时需要上传到OSS
        audio_url = f"file://{temp_path}"

        logger.info(f"开始克隆音色: voice_prefix={voice_prefix}, file={temp_filename}")

        # 调用克隆服务
        result = await cosyvoice_clone_service.clone_voice(
            audio_url=audio_url,
            voice_prefix=voice_prefix,
            voice_name=voice_name or voice_prefix
        )

        # 如果克隆失败，删除临时文件
        if not result.get("success"):
            if os.path.exists(temp_path):
                os.remove(temp_path)
            raise HTTPException(
                status_code=500,
                detail=result.get("error", "音色克隆失败")
            )

        # 克隆成功，保留文件
        result["audio_file"] = temp_filename
        result["audio_path"] = temp_path

        logger.info(f"音色克隆成功: {result}")
        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"上传并克隆失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"上传并克隆失败: {str(e)}")


@router.get("/list/{voice_prefix}", summary="查询克隆音色列表")
async def list_cloned_voices(
    voice_prefix: str,
    page_index: int = 1,
    page_size: int = 10
) -> Dict:
    """
    查询指定前缀的克隆音色列表

    Args:
        voice_prefix: 音色前缀
        page_index: 页码（从1开始）
        page_size: 每页数量

    Returns:
        音色列表
    """
    try:
        result = await cosyvoice_clone_service.list_cloned_voices(
            voice_prefix=voice_prefix,
            page_index=page_index,
            page_size=page_size
        )

        if not result.get("success"):
            raise HTTPException(
                status_code=500,
                detail=result.get("error", "查询失败")
            )

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"查询克隆音色失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"查询失败: {str(e)}")


@router.get("/health", summary="音色克隆服务健康检查")
async def health_check() -> Dict:
    """检查音色克隆服务状态"""
    return await cosyvoice_clone_service.health_check()
