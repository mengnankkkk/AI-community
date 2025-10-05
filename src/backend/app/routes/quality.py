"""
播客质量评估API路由
提供播客质量评估和管理的RESTful接口
"""

from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Depends
from fastapi.responses import JSONResponse
from typing import List, Dict, Any, Optional
import json
import os
import tempfile
from datetime import datetime

from ..services.quality_assessment_service import quality_assessment_service, QualityReport
from ..core.config import settings

router = APIRouter(prefix="/quality", tags=["quality"])

# 在应用启动时初始化评估服务
@router.on_event("startup")
async def startup_event():
    """应用启动时初始化质量评估服务"""
    await quality_assessment_service.initialize()

@router.post("/assess")
async def assess_podcast_quality(
    script: Dict[str, Any],
    audio_file: Optional[UploadFile] = File(None),
    metadata: Optional[Dict[str, Any]] = None
):
    """
    评估播客质量

    Args:
        script: 播客脚本数据
        audio_file: 音频文件（可选）
        metadata: 元数据（可选）

    Returns:
        QualityReport: 质量评估报告
    """
    try:
        audio_path = None

        # 如果有音频文件，保存到临时目录
        if audio_file:
            # 创建临时文件
            with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp_file:
                content = await audio_file.read()
                tmp_file.write(content)
                audio_path = tmp_file.name

        # 执行质量评估
        report = await quality_assessment_service.assess_podcast_quality(
            script=script,
            audio_path=audio_path,
            metadata=metadata
        )

        # 清理临时文件
        if audio_path and os.path.exists(audio_path):
            os.unlink(audio_path)

        # 将报告转换为字典格式
        report_dict = {
            "overall_score": report.overall_score,
            "quality_level": report.quality_level.value,
            "dimension_scores": report.dimension_scores,
            "metrics": {
                # 内容质量
                "content_logic": report.metrics.content_logic,
                "content_depth": report.metrics.content_depth,
                "content_accuracy": report.metrics.content_accuracy,
                "content_innovation": report.metrics.content_innovation,
                # 对话自然度
                "dialogue_fluency": report.metrics.dialogue_fluency,
                "dialogue_interaction": report.metrics.dialogue_interaction,
                "dialogue_consistency": report.metrics.dialogue_consistency,
                "dialogue_emotion": report.metrics.dialogue_emotion,
                # 音频质量
                "audio_clarity": report.metrics.audio_clarity,
                "audio_emotion": report.metrics.audio_emotion,
                "audio_effects": report.metrics.audio_effects,
                "audio_technical": report.metrics.audio_technical,
                # 用户体验
                "user_attraction": report.metrics.user_attraction,
                "user_comprehension": report.metrics.user_comprehension,
                "user_entertainment": report.metrics.user_entertainment,
                "user_value": report.metrics.user_value
            },
            "issues": report.issues,
            "suggestions": report.suggestions,
            "timestamp": report.timestamp.isoformat(),
            "metadata": report.metadata
        }

        return JSONResponse(content=report_dict)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"质量评估失败: {str(e)}")

@router.post("/assess-text")
async def assess_text_quality(request: Dict[str, Any]):
    """
    仅基于文本评估播客质量

    Args:
        request: 包含script和可选metadata的请求数据

    Returns:
        评估报告
    """
    try:
        script = request.get("script")
        metadata = request.get("metadata", {})

        if not script:
            raise HTTPException(status_code=400, detail="缺少script参数")

        # 执行基于文本的质量评估
        report = await quality_assessment_service.assess_podcast_quality(
            script=script,
            audio_path=None,
            metadata=metadata
        )

        # 构建响应
        response = {
            "overall_score": report.overall_score,
            "quality_level": report.quality_level.value,
            "dimension_scores": report.dimension_scores,
            "detailed_metrics": {
                "content_quality": {
                    "logic": report.metrics.content_logic,
                    "depth": report.metrics.content_depth,
                    "accuracy": report.metrics.content_accuracy,
                    "innovation": report.metrics.content_innovation
                },
                "dialogue_naturalness": {
                    "fluency": report.metrics.dialogue_fluency,
                    "interaction": report.metrics.dialogue_interaction,
                    "consistency": report.metrics.dialogue_consistency,
                    "emotion": report.metrics.dialogue_emotion
                },
                "estimated_audio_quality": {
                    "clarity": report.metrics.audio_clarity,
                    "emotion": report.metrics.audio_emotion,
                    "effects": report.metrics.audio_effects,
                    "technical": report.metrics.audio_technical
                },
                "user_experience": {
                    "attraction": report.metrics.user_attraction,
                    "comprehension": report.metrics.user_comprehension,
                    "entertainment": report.metrics.user_entertainment,
                    "value": report.metrics.user_value
                }
            },
            "issues": report.issues,
            "suggestions": report.suggestions,
            "assessment_timestamp": report.timestamp.isoformat()
        }

        return response

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"文本质量评估失败: {str(e)}")

@router.get("/thresholds")
async def get_quality_thresholds():
    """
    获取质量阈值配置

    Returns:
        质量阈值设置
    """
    return {
        "thresholds": quality_assessment_service.quality_thresholds,
        "dimension_weights": quality_assessment_service.dimension_weights,
        "quality_levels": {
            "excellent": {"min_score": 90, "description": "优秀 - 专业水准，可直接发布"},
            "good": {"min_score": 80, "description": "良好 - 质量较高，轻微优化后可发布"},
            "acceptable": {"min_score": 70, "description": "合格 - 基本达标，需要一定优化"},
            "needs_improvement": {"min_score": 60, "description": "待改进 - 存在明显问题，需要重新生成"},
            "poor": {"min_score": 0, "description": "不合格 - 质量较差，需要检查系统配置"}
        }
    }

@router.put("/thresholds")
async def update_quality_thresholds(request: Dict[str, Any]):
    """
    更新质量阈值配置

    Args:
        request: 包含新阈值设置的请求

    Returns:
        更新结果
    """
    try:
        thresholds = request.get("thresholds")
        weights = request.get("dimension_weights")

        if thresholds:
            quality_assessment_service.quality_thresholds.update(thresholds)

        if weights:
            quality_assessment_service.dimension_weights.update(weights)

        return {
            "message": "质量阈值配置更新成功",
            "updated_thresholds": quality_assessment_service.quality_thresholds,
            "updated_weights": quality_assessment_service.dimension_weights
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"更新阈值失败: {str(e)}")

@router.post("/batch-assess")
async def batch_assess_quality(requests: List[Dict[str, Any]]):
    """
    批量评估播客质量

    Args:
        requests: 批量评估请求列表

    Returns:
        批量评估结果
    """
    try:
        results = []

        for i, req in enumerate(requests):
            try:
                script = req.get("script")
                metadata = req.get("metadata", {})
                metadata["batch_index"] = i

                report = await quality_assessment_service.assess_podcast_quality(
                    script=script,
                    audio_path=None,
                    metadata=metadata
                )

                results.append({
                    "index": i,
                    "overall_score": report.overall_score,
                    "quality_level": report.quality_level.value,
                    "dimension_scores": report.dimension_scores,
                    "issues_count": len(report.issues),
                    "suggestions_count": len(report.suggestions)
                })

            except Exception as e:
                results.append({
                    "index": i,
                    "error": str(e),
                    "overall_score": 0,
                    "quality_level": "error"
                })

        # 计算批量统计
        valid_results = [r for r in results if "error" not in r]
        if valid_results:
            avg_score = sum(r["overall_score"] for r in valid_results) / len(valid_results)
            score_distribution = {}
            for r in valid_results:
                level = r["quality_level"]
                score_distribution[level] = score_distribution.get(level, 0) + 1
        else:
            avg_score = 0
            score_distribution = {}

        return {
            "batch_summary": {
                "total_requests": len(requests),
                "successful_assessments": len(valid_results),
                "failed_assessments": len(requests) - len(valid_results),
                "average_score": round(avg_score, 2),
                "quality_distribution": score_distribution
            },
            "detailed_results": results
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"批量评估失败: {str(e)}")

@router.get("/metrics/definitions")
async def get_metrics_definitions():
    """
    获取评估指标定义

    Returns:
        详细的指标定义和说明
    """
    return {
        "dimensions": {
            "content_quality": {
                "name": "内容质量",
                "weight": quality_assessment_service.dimension_weights["content"],
                "description": "评估播客内容的专业性、深度和准确性",
                "metrics": {
                    "logic": {
                        "name": "逻辑性",
                        "weight": 0.30,
                        "description": "论证清晰、结构合理、前后呼应"
                    },
                    "depth": {
                        "name": "深度性",
                        "weight": 0.25,
                        "description": "观点深入、分析透彻、有见地"
                    },
                    "accuracy": {
                        "name": "准确性",
                        "weight": 0.25,
                        "description": "信息正确、引用可靠、无误导"
                    },
                    "innovation": {
                        "name": "创新性",
                        "weight": 0.20,
                        "description": "观点新颖、角度独特、有启发"
                    }
                }
            },
            "dialogue_naturalness": {
                "name": "对话自然度",
                "weight": quality_assessment_service.dimension_weights["dialogue"],
                "description": "评估对话的流畅性和真实感",
                "metrics": {
                    "fluency": {
                        "name": "流畅性",
                        "weight": 0.35,
                        "description": "语言顺畅、过渡自然、无突兀感"
                    },
                    "interaction": {
                        "name": "交互性",
                        "weight": 0.30,
                        "description": "角色互动、回应合理、有来有往"
                    },
                    "consistency": {
                        "name": "一致性",
                        "weight": 0.25,
                        "description": "角色性格稳定、语言风格统一"
                    },
                    "emotion": {
                        "name": "情感表达",
                        "weight": 0.10,
                        "description": "情感真实、表达恰当、有感染力"
                    }
                }
            },
            "audio_quality": {
                "name": "音频质量",
                "weight": quality_assessment_service.dimension_weights["audio"],
                "description": "评估音频制作的技术质量和艺术效果",
                "metrics": {
                    "clarity": {
                        "name": "语音清晰度",
                        "weight": 0.40,
                        "description": "发音准确、咬字清楚、音质清晰"
                    },
                    "emotion": {
                        "name": "情感表达",
                        "weight": 0.30,
                        "description": "情感丰富、抑扬顿挫、有感染力"
                    },
                    "effects": {
                        "name": "背景音效",
                        "weight": 0.20,
                        "description": "音效恰当、音量平衡、增强氛围"
                    },
                    "technical": {
                        "name": "技术质量",
                        "weight": 0.10,
                        "description": "无杂音、无断层、音频平稳"
                    }
                }
            },
            "user_experience": {
                "name": "用户体验",
                "weight": quality_assessment_service.dimension_weights["user_experience"],
                "description": "评估用户收听体验和价值感受",
                "metrics": {
                    "attraction": {
                        "name": "吸引力",
                        "weight": 0.35,
                        "description": "开头抓人、保持兴趣、有听下去的欲望"
                    },
                    "comprehension": {
                        "name": "易懂性",
                        "weight": 0.30,
                        "description": "表达清楚、逻辑清晰、易于理解"
                    },
                    "entertainment": {
                        "name": "娱乐性",
                        "weight": 0.25,
                        "description": "有趣味性、不枯燥、有亮点"
                    },
                    "value": {
                        "name": "价值性",
                        "weight": 0.10,
                        "description": "有收获、有启发、值得分享"
                    }
                }
            }
        }
    }

@router.post("/feedback")
async def submit_quality_feedback(
    script_id: str,
    user_rating: float,
    feedback_data: Dict[str, Any]
):
    """
    提交用户质量反馈

    Args:
        script_id: 脚本ID
        user_rating: 用户评分(1-5)
        feedback_data: 详细反馈数据

    Returns:
        反馈提交结果
    """
    try:
        # 验证评分范围
        if not 1 <= user_rating <= 5:
            raise HTTPException(status_code=400, detail="用户评分必须在1-5之间")

        # 保存反馈数据（这里可以集成到数据库）
        feedback_record = {
            "script_id": script_id,
            "user_rating": user_rating,
            "feedback_timestamp": datetime.now().isoformat(),
            "dimension_ratings": feedback_data.get("dimension_ratings", {}),
            "specific_issues": feedback_data.get("specific_issues", []),
            "text_feedback": feedback_data.get("text_feedback", ""),
            "user_metadata": feedback_data.get("user_metadata", {})
        }

        # TODO: 将反馈数据保存到数据库

        return {
            "message": "质量反馈提交成功",
            "feedback_id": f"feedback_{script_id}_{int(datetime.now().timestamp())}",
            "received_rating": user_rating,
            "processed_timestamp": datetime.now().isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"反馈提交失败: {str(e)}")

@router.get("/statistics")
async def get_quality_statistics(
    days: int = 7,
    include_details: bool = False
):
    """
    获取质量统计信息

    Args:
        days: 统计天数
        include_details: 是否包含详细信息

    Returns:
        质量统计数据
    """
    try:
        # TODO: 从数据库获取实际统计数据
        # 这里返回模拟数据

        statistics = {
            "summary": {
                "period_days": days,
                "total_assessments": 156,
                "average_score": 82.3,
                "quality_distribution": {
                    "excellent": 23,
                    "good": 87,
                    "acceptable": 34,
                    "needs_improvement": 9,
                    "poor": 3
                }
            },
            "trends": {
                "score_trend": [78.2, 79.1, 81.3, 82.1, 82.8, 82.3, 83.1],
                "volume_trend": [18, 22, 25, 28, 24, 19, 20]
            },
            "dimension_averages": {
                "content": 84.2,
                "dialogue": 81.7,
                "audio": 79.8,
                "user_experience": 83.5
            }
        }

        if include_details:
            statistics["detailed_metrics"] = {
                "common_issues": [
                    {"issue": "对话交互性不足", "frequency": 34, "avg_impact": -8.2},
                    {"issue": "内容深度偏浅", "frequency": 28, "avg_impact": -6.5},
                    {"issue": "音频清晰度问题", "frequency": 19, "avg_impact": -9.1}
                ],
                "improvement_suggestions": [
                    {"suggestion": "增强角色互动", "effectiveness": 85},
                    {"suggestion": "优化音频处理", "effectiveness": 78},
                    {"suggestion": "加深内容分析", "effectiveness": 72}
                ]
            }

        return statistics

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取统计信息失败: {str(e)}")

@router.get("/health")
async def quality_service_health():
    """
    检查质量评估服务健康状态

    Returns:
        服务健康状态
    """
    try:
        # 检查评估服务是否正常
        test_script = {
            "title": "测试标题",
            "dialogues": [
                {"character_name": "测试角色", "content": "这是一个测试对话。"}
            ]
        }

        # 执行简单的评估测试
        report = await quality_assessment_service.assess_podcast_quality(
            script=test_script,
            audio_path=None,
            metadata={"test": True}
        )

        return {
            "status": "healthy",
            "service_version": "1.0.0",
            "models_loaded": bool(quality_assessment_service.sentiment_analyzer),
            "test_assessment_score": report.overall_score,
            "last_check": datetime.now().isoformat()
        }

    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "last_check": datetime.now().isoformat()
        }