"""
Vision图片分析API路由
提供图片上传和智能分析功能，替换原有的ASR语音识别功能
"""

from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from fastapi.responses import JSONResponse
from typing import Optional, Dict, Any
import tempfile
import os
import asyncio
from datetime import datetime

from ..services.vision_service import vision_service, analyze_image_file, get_analysis_capabilities

router = APIRouter(prefix="/vision", tags=["vision"])


@router.on_event("startup")
async def startup_event():
    """应用启动时初始化Vision服务"""
    await vision_service.initialize()


@router.post("/analyze")
async def analyze_image(
    image_file: UploadFile = File(...),
    analysis_type: str = Form("material"),
    target_field: Optional[str] = Form(None)
):
    """
    图片分析接口

    Args:
        image_file: 图片文件
        analysis_type: 分析类型 (general, material, creative)
        target_field: 目标字段（可选）

    Returns:
        分析结果
    """
    try:
        # 验证文件类型
        if not image_file.content_type.startswith('image/'):
            raise HTTPException(status_code=400, detail="请上传图片文件")

        # 创建临时文件
        with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp_file:
            content = await image_file.read()
            tmp_file.write(content)
            tmp_file_path = tmp_file.name

        try:
            # 执行图片分析
            result = await analyze_image_file(tmp_file_path, analysis_type, target_field)

            # 添加元数据
            result.update({
                "filename": image_file.filename,
                "file_size": len(content),
                "content_type": image_file.content_type,
                "timestamp": datetime.now().isoformat(),
                "analysis_type": analysis_type
            })

            return JSONResponse(content=result)

        finally:
            # 清理临时文件
            if os.path.exists(tmp_file_path):
                os.unlink(tmp_file_path)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"图片分析失败: {str(e)}")


@router.post("/batch-analyze")
async def batch_analyze_images(
    image_files: list[UploadFile] = File(...),
    analysis_type: str = Form("material")
):
    """
    批量图片分析接口

    Args:
        image_files: 图片文件列表（最多5张）
        analysis_type: 分析类型

    Returns:
        批量分析结果
    """
    try:
        if len(image_files) > 5:
            raise HTTPException(status_code=400, detail="最多支持上传5张图片")

        # 验证所有文件类型
        for image_file in image_files:
            if not image_file.content_type.startswith('image/'):
                raise HTTPException(status_code=400, detail=f"文件{image_file.filename}不是图片文件")

        # 保存临时文件
        temp_files = []
        try:
            for image_file in image_files:
                with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp_file:
                    content = await image_file.read()
                    tmp_file.write(content)
                    temp_files.append(tmp_file.name)

            # 批量分析
            result = await vision_service.batch_analyze_images(temp_files, analysis_type)

            # 添加元数据
            result.update({
                "upload_count": len(image_files),
                "filenames": [f.filename for f in image_files],
                "timestamp": datetime.now().isoformat()
            })

            return JSONResponse(content=result)

        finally:
            # 清理临时文件
            for temp_file in temp_files:
                if os.path.exists(temp_file):
                    os.unlink(temp_file)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"批量图片分析失败: {str(e)}")


@router.post("/analyze-for-field")
async def analyze_image_for_field(request: Dict[str, Any]):
    """
    为特定字段分析图片内容

    Args:
        request: 包含image_url和target_field的请求

    Returns:
        字段导向的分析结果
    """
    try:
        image_url = request.get("image_url", "")
        target_field = request.get("target_field")

        if not image_url:
            raise HTTPException(status_code=400, detail="缺少image_url参数")

        # 这里可以实现从URL下载图片并分析的逻辑
        # 目前返回示例结果
        analysis_result = {
            "success": True,
            "target_field": target_field,
            "suggested_content": "基于图片内容生成的字段建议",
            "confidence": 0.8,
            "description": "这是根据上传图片为特定字段生成的内容建议"
        }

        return JSONResponse(content={
            "success": True,
            "image_url": image_url,
            "analysis": analysis_result,
            "timestamp": datetime.now().isoformat()
        })

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"字段分析失败: {str(e)}")


@router.get("/supported-types")
async def get_supported_analysis_types():
    """
    获取支持的分析类型列表

    Returns:
        分析类型信息
    """
    try:
        types = await get_analysis_capabilities()
        return JSONResponse(content={
            "analysis_types": types,
            "total_count": len(types)
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取分析类型失败: {str(e)}")


@router.get("/supported-fields")
async def get_supported_fields():
    """
    获取支持的字段列表（兼容原ASR接口）

    Returns:
        支持的字段信息
    """
    fields = {
        "topic": {
            "name": "播客主题",
            "description": "基于图片内容提炼播客讨论主题",
            "examples": ["科技发展趋势", "社会现象分析"]
        },
        "title": {
            "name": "播客标题",
            "description": "根据图片内容生成吸引人的播客标题",
            "examples": ["图说科技未来", "视觉中的社会观察"]
        },
        "background_materials": {
            "name": "背景材料",
            "description": "将图片内容转化为播客的背景资料",
            "examples": ["相关背景介绍", "话题延伸资料"]
        },
        "character_name": {
            "name": "角色姓名",
            "description": "基于图片中的人物形象建议角色名称",
            "examples": ["专家形象", "代表性人物"]
        },
        "persona": {
            "name": "角色人设",
            "description": "根据图片内容描述角色身份背景",
            "examples": ["专业背景描述", "身份特征设定"]
        },
        "viewpoint": {
            "name": "核心观点",
            "description": "从图片传达的信息中提炼观点立场",
            "examples": ["支持某种趋势", "关注特定议题"]
        }
    }

    return JSONResponse(content={
        "supported_fields": fields,
        "total_count": len(fields)
    })


@router.get("/image-guidelines")
async def get_image_upload_guidelines():
    """
    获取图片上传指南

    Returns:
        上传指南信息
    """
    guidelines = {
        "supported_formats": [
            ".jpg", ".jpeg", ".png", ".bmp", ".gif", ".webp"
        ],
        "max_file_size": "10MB",
        "recommended_resolution": "1024x1024以下",
        "best_practices": [
            "确保图片清晰可见",
            "避免过于模糊或暗淡的图片",
            "选择内容丰富、有讨论价值的图片",
            "支持多种场景：人物、风景、物品、抽象概念等"
        ],
        "analysis_capabilities": [
            "内容识别与描述",
            "场景理解与分析",
            "情感色彩判断",
            "话题价值评估",
            "创意灵感提取"
        ]
    }

    return JSONResponse(content={
        "upload_guidelines": guidelines,
        "service_status": "active" if vision_service.initialized else "initializing"
    })


@router.get("/health")
async def vision_health_check():
    """
    Vision服务健康检查

    Returns:
        服务状态信息
    """
    try:
        status = {
            "status": "healthy" if vision_service.initialized else "initializing",
            "service_loaded": vision_service.initialized,
            "model_name": vision_service.model_name,
            "api_configured": bool(vision_service.api_key),
            "max_image_size": f"{vision_service.max_image_size // (1024*1024)}MB",
            "supported_formats": list(vision_service.supported_formats),
            "timestamp": datetime.now().isoformat()
        }

        return JSONResponse(content=status)

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
        )