"""
ASR语音识别API路由
提供语音转文字和智能字段分配功能
"""

from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from fastapi.responses import JSONResponse
from typing import Optional, Dict, Any
import tempfile
import os
import asyncio
from datetime import datetime

from ..services.asr_service import asr_service, transcribe_audio_file, parse_voice_command_text

router = APIRouter(prefix="/asr", tags=["asr"])


@router.on_event("startup")
async def startup_event():
    """应用启动时初始化ASR服务"""
    await asr_service.initialize()


@router.post("/transcribe")
async def transcribe_audio(
    audio_file: UploadFile = File(...),
    target_field: Optional[str] = Form(None),
    language: str = Form("zh-CN")
):
    """
    语音转文字接口

    Args:
        audio_file: 音频文件
        target_field: 目标字段（可选）
        language: 语言代码（默认中文）

    Returns:
        转换结果
    """
    try:
        # 验证文件类型
        if not audio_file.content_type.startswith('audio/'):
            raise HTTPException(status_code=400, detail="请上传音频文件")

        # 创建临时文件
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_file:
            content = await audio_file.read()
            tmp_file.write(content)
            tmp_file_path = tmp_file.name

        try:
            # 执行语音识别
            result = await transcribe_audio_file(tmp_file_path, target_field)

            # 添加元数据
            result.update({
                "filename": audio_file.filename,
                "file_size": len(content),
                "content_type": audio_file.content_type,
                "timestamp": datetime.now().isoformat(),
                "language": language
            })

            return JSONResponse(content=result)

        finally:
            # 清理临时文件
            if os.path.exists(tmp_file_path):
                os.unlink(tmp_file_path)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"语音识别失败: {str(e)}")


@router.post("/parse-command")
async def parse_voice_command(request: Dict[str, Any]):
    """
    解析语音指令

    Args:
        request: 包含text字段的请求

    Returns:
        指令解析结果
    """
    try:
        text = request.get("text", "")
        if not text:
            raise HTTPException(status_code=400, detail="缺少text参数")

        result = await parse_voice_command_text(text)

        return JSONResponse(content={
            "success": True,
            "original_text": text,
            "parsed_result": result,
            "timestamp": datetime.now().isoformat()
        })

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"指令解析失败: {str(e)}")


@router.post("/analyze-content")
async def analyze_content_for_field(request: Dict[str, Any]):
    """
    分析文本内容，推荐合适的字段

    Args:
        request: 包含text字段的请求

    Returns:
        字段推荐结果
    """
    try:
        text = request.get("text", "")
        target_field = request.get("target_field")

        if not text:
            raise HTTPException(status_code=400, detail="缺少text参数")

        # 使用ASR服务的内容分析功能
        result = await asr_service._analyze_content_for_field(text, target_field)

        return JSONResponse(content={
            "success": True,
            "text": text,
            "analysis": result,
            "timestamp": datetime.now().isoformat()
        })

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"内容分析失败: {str(e)}")


@router.get("/supported-fields")
async def get_supported_fields():
    """
    获取支持的字段列表

    Returns:
        支持的字段信息
    """
    fields = {
        "topic": {
            "name": "播客主题",
            "description": "播客的核心讨论主题",
            "examples": ["人工智能的发展", "远程工作的利弊"]
        },
        "title": {
            "name": "播客标题",
            "description": "播客的具体标题",
            "examples": ["AI时代的机遇与挑战", "在家办公新常态"]
        },
        "background_materials": {
            "name": "背景材料",
            "description": "相关的背景信息和参考资料",
            "examples": ["相关研究报告", "行业数据统计"]
        },
        "character_name": {
            "name": "角色姓名",
            "description": "参与讨论的角色名称",
            "examples": ["张教授", "李记者", "王专家"]
        },
        "persona": {
            "name": "角色人设",
            "description": "角色的身份背景和专业领域",
            "examples": ["人工智能专家", "科技记者", "企业高管"]
        },
        "viewpoint": {
            "name": "核心观点",
            "description": "角色在讨论中的主要立场和观点",
            "examples": ["支持AI发展", "注重隐私保护", "强调技术伦理"]
        }
    }

    return JSONResponse(content={
        "supported_fields": fields,
        "total_count": len(fields)
    })


@router.get("/voice-commands")
async def get_voice_commands():
    """
    获取支持的语音指令列表

    Returns:
        语音指令帮助信息
    """
    commands = {
        "topic_commands": {
            "name": "主题设置指令",
            "examples": [
                "设置主题为人工智能发展",
                "主题是远程工作讨论",
                "讨论气候变化问题"
            ]
        },
        "title_commands": {
            "name": "标题设置指令",
            "examples": [
                "标题为AI时代的机遇",
                "题目是远程办公新常态",
                "叫做未来科技探讨"
            ]
        },
        "character_commands": {
            "name": "角色添加指令",
            "examples": [
                "添加角色张教授",
                "角色是李记者",
                "嘉宾是王专家"
            ]
        },
        "viewpoint_commands": {
            "name": "观点设置指令",
            "examples": [
                "观点是支持技术发展",
                "认为需要谨慎推进",
                "立场是注重安全性"
            ]
        },
        "persona_commands": {
            "name": "身份设置指令",
            "examples": [
                "身份是AI研究专家",
                "职业是科技记者",
                "专家在机器学习领域"
            ]
        }
    }

    return JSONResponse(content={
        "voice_commands": commands,
        "usage_tips": [
            "说话清晰，语速适中",
            "使用标准普通话",
            "避免背景噪音干扰",
            "每次录音建议不超过30秒"
        ]
    })


@router.get("/health")
async def asr_health_check():
    """
    ASR服务健康检查

    Returns:
        服务状态信息
    """
    try:
        status = {
            "status": "healthy" if asr_service.initialized else "initializing",
            "model_loaded": asr_service.initialized,
            "device": asr_service.device,
            "model_name": asr_service.model_name,
            "sample_rate": asr_service.sample_rate,
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