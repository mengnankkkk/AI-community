"""
Hunyuan Vision 图片分析服务
支持图片理解和描述生成功能
"""

import asyncio
import tempfile
import os
import logging
import base64
from typing import Dict, Any, Optional
import aiohttp
import aiofiles
from PIL import Image
import io

from ..core.config import settings

logger = logging.getLogger(__name__)


class HunyuanVisionService:
    """Hunyuan Vision 图片分析服务"""

    def __init__(self):
        self.api_key = settings.hunyuan_api_key
        self.base_url = settings.hunyuan_base_url
        self.model_name = settings.hunyuan_vision_model
        self.max_image_size = 10 * 1024 * 1024  # 10MB
        self.supported_formats = {'.jpg', '.jpeg', '.png', '.bmp', '.gif', '.webp'}
        self.initialized = False

    async def initialize(self):
        """初始化视觉分析服务"""
        try:
            logger.info("正在初始化Hunyuan Vision服务...")

            if not self.api_key:
                logger.warning("Hunyuan API Key未配置，使用演示模式")
                self.initialized = False
                return False

            self.initialized = True
            logger.info("Hunyuan Vision服务初始化完成")
            return True

        except Exception as e:
            logger.error(f"Vision服务初始化失败: {e}")
            return False

    async def analyze_image(
        self,
        image_path: str,
        analysis_type: str = "general",
        target_field: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        分析图片并生成描述

        Args:
            image_path: 图片文件路径
            analysis_type: 分析类型 (general, material, creative)
            target_field: 目标字段（可选）

        Returns:
            分析结果字典
        """
        if not self.initialized:
            await self.initialize()

        try:
            # 验证图片文件
            if not os.path.exists(image_path):
                raise FileNotFoundError(f"图片文件不存在: {image_path}")

            # 验证文件格式和大小
            validation_result = self._validate_image(image_path)
            if not validation_result["valid"]:
                raise ValueError(validation_result["error"])

            # 预处理图片
            processed_image_path = await self._preprocess_image(image_path)

            # 执行图片分析
            if self.api_key:
                result = await self._call_hunyuan_vision_api(
                    processed_image_path, analysis_type, target_field
                )
            else:
                # 演示模式：生成模拟分析结果
                result = self._generate_demo_analysis(processed_image_path, analysis_type)

            # 清理临时文件
            if processed_image_path != image_path:
                os.unlink(processed_image_path)

            return result

        except Exception as e:
            logger.error(f"图片分析失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "description": "",
                "target_field": target_field
            }

    def _validate_image(self, image_path: str) -> Dict[str, Any]:
        """验证图片文件"""
        try:
            # 检查文件大小
            file_size = os.path.getsize(image_path)
            if file_size > self.max_image_size:
                return {
                    "valid": False,
                    "error": f"图片文件过大，最大支持{self.max_image_size // (1024*1024)}MB"
                }

            # 检查文件格式
            file_ext = os.path.splitext(image_path)[1].lower()
            if file_ext not in self.supported_formats:
                return {
                    "valid": False,
                    "error": f"不支持的图片格式，支持格式: {', '.join(self.supported_formats)}"
                }

            # 尝试打开图片验证完整性
            with Image.open(image_path) as img:
                img.verify()

            return {"valid": True}

        except Exception as e:
            return {"valid": False, "error": f"图片文件损坏或格式错误: {str(e)}"}

    async def _preprocess_image(self, image_path: str) -> str:
        """预处理图片"""
        try:
            with Image.open(image_path) as img:
                # 转换为RGB模式
                if img.mode != 'RGB':
                    img = img.convert('RGB')

                # 调整图片大小（如果太大）
                max_dimension = 1024
                if max(img.width, img.height) > max_dimension:
                    img.thumbnail((max_dimension, max_dimension), Image.Resampling.LANCZOS)

                    # 保存处理后的图片
                    with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as tmp_file:
                        img.save(tmp_file.name, 'JPEG', quality=85)
                        return tmp_file.name

            return image_path

        except Exception as e:
            logger.error(f"图片预处理失败: {e}")
            raise

    async def _call_hunyuan_vision_api(
        self,
        image_path: str,
        analysis_type: str,
        target_field: Optional[str] = None
    ) -> Dict[str, Any]:
        """调用混元视觉API"""
        try:
            # 将图片转为base64
            with open(image_path, 'rb') as img_file:
                image_data = base64.b64encode(img_file.read()).decode('utf-8')

            # 根据分析类型和目标字段生成提示词
            prompt = self._generate_analysis_prompt(analysis_type, target_field)

            # 构造API请求
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json'
            }

            payload = {
                "model": self.model_name,
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": prompt
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{image_data}"
                                }
                            }
                        ]
                    }
                ],
                "max_tokens": 1000,
                "temperature": 0.7
            }

            # 发送API请求
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/chat/completions",
                    headers=headers,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        description = result['choices'][0]['message']['content']

                        return {
                            "success": True,
                            "description": description.strip(),
                            "target_field": target_field,
                            "analysis_type": analysis_type,
                            "model_used": self.model_name,
                            "confidence": 0.9  # 混元模型通常置信度较高
                        }
                    else:
                        error_text = await response.text()
                        raise Exception(f"API调用失败: {response.status} - {error_text}")

        except Exception as e:
            logger.error(f"混元Vision API调用失败: {e}")
            raise

    def _generate_analysis_prompt(self, analysis_type: str, target_field: Optional[str] = None) -> str:
        """生成分析提示词"""
        base_prompts = {
            "general": "请详细描述这张图片的内容，包括主要元素、场景、色彩、风格等特征。",
            "material": "请分析这张图片作为播客素材的价值，描述其中的关键信息、可讨论的话题点、以及如何与播客内容结合。",
            "creative": "请从创意角度分析这张图片，描述其艺术特色、情感表达、创作手法等，适合作为播客的灵感素材。"
        }

        prompt = base_prompts.get(analysis_type, base_prompts["general"])

        # 根据目标字段调整提示词
        if target_field:
            field_prompts = {
                "topic": "请基于图片内容，提炼出适合作为播客主题的核心议题。",
                "title": "请基于图片内容，生成一个吸引人的播客标题。",
                "background_materials": "请将图片内容整理成播客的背景资料，包括相关信息和讨论价值。",
                "character_name": "请基于图片中的人物或形象，建议合适的角色名称。",
                "persona": "请基于图片内容，描述相关的人物身份设定。",
                "viewpoint": "请基于图片传达的信息，总结可能的观点立场。"
            }

            if target_field in field_prompts:
                prompt = field_prompts[target_field]

        prompt += "\n\n请用中文回答，内容要具体生动，适合播客节目使用。"
        return prompt

    def _generate_demo_analysis(self, image_path: str, analysis_type: str) -> Dict[str, Any]:
        """生成演示分析结果（当API Key未配置时）"""
        try:
            with Image.open(image_path) as img:
                width, height = img.size
                format_name = img.format

            demo_descriptions = {
                "general": f"这是一张{format_name}格式的图片，尺寸为{width}x{height}像素。图片展现了丰富的视觉内容，包含多个值得讨论的元素，可以作为播客节目的优质素材。",
                "material": f"从播客素材角度分析，这张{width}x{height}的图片具有很好的话题价值。图片中的内容可以引发深度讨论，适合作为播客节目的背景材料。",
                "creative": f"从创意角度看，这张图片展现了独特的艺术价值。{format_name}格式保持了良好的画质，{width}x{height}的尺寸适合多媒体展示，具有很好的视觉冲击力。"
            }

            return {
                "success": True,
                "description": demo_descriptions.get(analysis_type, demo_descriptions["general"]),
                "target_field": None,
                "analysis_type": analysis_type,
                "model_used": f"{self.model_name} (演示模式)",
                "confidence": 0.7,
                "demo_mode": True
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"演示分析失败: {str(e)}",
                "description": "",
                "demo_mode": True
            }

    async def get_supported_analysis_types(self) -> Dict[str, Any]:
        """获取支持的分析类型"""
        return {
            "general": {
                "name": "通用分析",
                "description": "对图片进行全面的内容描述和分析",
                "examples": ["场景描述", "元素识别", "色彩分析"]
            },
            "material": {
                "name": "素材分析",
                "description": "从播客素材角度分析图片的话题价值",
                "examples": ["话题提取", "讨论点分析", "内容价值评估"]
            },
            "creative": {
                "name": "创意分析",
                "description": "从艺术创意角度分析图片特色",
                "examples": ["艺术特色", "情感表达", "创作手法"]
            }
        }

    async def batch_analyze_images(
        self,
        image_paths: list,
        analysis_type: str = "material"
    ) -> Dict[str, Any]:
        """批量分析图片"""
        results = []

        for image_path in image_paths[:5]:  # 限制最多5张图片
            try:
                result = await self.analyze_image(image_path, analysis_type)
                results.append({
                    "image_path": os.path.basename(image_path),
                    "result": result
                })
            except Exception as e:
                logger.error(f"批量分析图片失败 {image_path}: {e}")
                results.append({
                    "image_path": os.path.basename(image_path),
                    "result": {
                        "success": False,
                        "error": str(e)
                    }
                })

        return {
            "total_processed": len(results),
            "results": results,
            "analysis_type": analysis_type
        }


# 全局Vision服务实例
vision_service = HunyuanVisionService()


async def analyze_image_file(
    image_path: str,
    analysis_type: str = "general",
    target_field: Optional[str] = None
) -> Dict[str, Any]:
    """
    便捷的图片分析函数
    """
    return await vision_service.analyze_image(image_path, analysis_type, target_field)


async def get_analysis_capabilities() -> Dict[str, Any]:
    """
    获取分析能力信息
    """
    return await vision_service.get_supported_analysis_types()