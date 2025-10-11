from fastapi import APIRouter, HTTPException, Response
from fastapi.responses import FileResponse, JSONResponse
import os
from ..models.podcast import PodcastGenerationRequest, PodcastGenerationResponse
from ..services.task_manager import task_manager

router = APIRouter(prefix="/podcast", tags=["podcast"])

@router.post("/generate", response_model=PodcastGenerationResponse)
async def generate_podcast(request: PodcastGenerationRequest):
    """
    生成AI虚拟播客
    """
    try:
        # 验证角色数量
        if len(request.custom_form.characters) < 2:
            raise HTTPException(status_code=400, detail="至少需要2个角色")

        # 创建生成任务
        task_id = await task_manager.create_task(request.custom_form)

        return PodcastGenerationResponse(
            task_id=task_id,
            status="pending",
            message="任务已创建，正在处理中..."
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"任务创建失败: {str(e)}")

@router.get("/status/{task_id}", response_model=PodcastGenerationResponse)
async def get_task_status(task_id: str):
    """
    获取播客生成任务状态
    """
    return task_manager.get_task_status(task_id)

@router.get("/download/{task_id}")
async def download_podcast_audio(task_id: str):
    """
    下载生成的播客音频文件
    """
    audio_path = task_manager.get_task_audio_path(task_id)

    if not audio_path or not os.path.exists(audio_path):
        raise HTTPException(status_code=404, detail="音频文件不存在")

    # 确保使用绝对路径
    absolute_path = os.path.abspath(audio_path)

    return FileResponse(
        path=absolute_path,
        media_type="audio/mpeg",
        filename=f"podcast_{task_id}.mp3",
        headers={
            "Cache-Control": "no-cache",
            "Access-Control-Allow-Origin": "*"
        }
    )

@router.get("/debug/{task_id}")
async def debug_task_audio(task_id: str):
    """
    调试端点：检查任务音频文件状态
    """
    audio_path = task_manager.get_task_audio_path(task_id)

    debug_info = {
        "task_id": task_id,
        "audio_path": audio_path,
        "audio_path_absolute": os.path.abspath(audio_path) if audio_path else None,
        "file_exists": os.path.exists(audio_path) if audio_path else False,
        "file_size": os.path.getsize(audio_path) if audio_path and os.path.exists(audio_path) else 0,
        "download_url": f"/api/v1/podcast/download/{task_id}",
        "task_status": task_manager.get_task_status(task_id).status
    }

    return JSONResponse(content=debug_info)