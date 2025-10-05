"""
Hunyuan ASR语音识别服务
支持实时语音转文字功能
"""

import asyncio
import tempfile
import os
import logging
from typing import Dict, Any, Optional, AsyncGenerator
import aiohttp
import aiofiles
from transformers import pipeline
import torch
import librosa
import numpy as np

logger = logging.getLogger(__name__)


class HunyuanASRService:
    """Hunyuan ASR语音识别服务"""

    def __init__(self):
        self.model_name = "TencentGameMate/chinese-hunyuan-large"
        self.asr_pipeline = None
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.sample_rate = 16000
        self.initialized = False

    async def initialize(self):
        """初始化ASR模型"""
        try:
            logger.info("正在初始化Hunyuan ASR模型...")

            # 初始化ASR pipeline
            self.asr_pipeline = pipeline(
                "automatic-speech-recognition",
                model=self.model_name,
                device=0 if self.device == "cuda" else -1,
                return_timestamps=True
            )

            self.initialized = True
            logger.info("Hunyuan ASR模型初始化完成")
            return True

        except Exception as e:
            logger.error(f"ASR模型初始化失败: {e}")
            return False

    async def transcribe_audio(
        self,
        audio_file_path: str,
        target_field: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        转换音频为文字

        Args:
            audio_file_path: 音频文件路径
            target_field: 目标字段（可选）

        Returns:
            转换结果字典
        """
        if not self.initialized:
            await self.initialize()

        try:
            # 加载音频文件
            audio_data, sr = librosa.load(audio_file_path, sr=self.sample_rate)

            # 音频预处理
            audio_data = self._preprocess_audio(audio_data)

            # 执行语音识别
            result = self.asr_pipeline(audio_data)

            # 提取文本内容
            if isinstance(result, dict):
                transcribed_text = result.get("text", "")
                timestamps = result.get("chunks", [])
            else:
                transcribed_text = str(result)
                timestamps = []

            # 清理文本
            transcribed_text = self._clean_text(transcribed_text)

            # 智能字段分配
            field_assignment = await self._analyze_content_for_field(
                transcribed_text, target_field
            )

            return {
                "success": True,
                "text": transcribed_text,
                "target_field": target_field,
                "suggested_field": field_assignment["suggested_field"],
                "confidence": field_assignment["confidence"],
                "field_assignments": field_assignment["assignments"],
                "timestamps": timestamps,
                "audio_duration": len(audio_data) / self.sample_rate
            }

        except Exception as e:
            logger.error(f"语音识别失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "text": "",
                "target_field": target_field
            }

    def _preprocess_audio(self, audio_data: np.ndarray) -> np.ndarray:
        """音频预处理"""
        # 归一化音频
        audio_data = audio_data / np.max(np.abs(audio_data) + 1e-8)

        # 去除静音部分
        audio_data = librosa.effects.trim(audio_data, top_db=20)[0]

        return audio_data

    def _clean_text(self, text: str) -> str:
        """清理识别的文本"""
        # 移除多余的空格和特殊字符
        text = text.strip()
        text = ' '.join(text.split())

        # 移除常见的ASR错误
        text = text.replace("呃", "").replace("嗯", "")
        text = text.replace("那个", "").replace("就是", "")

        return text

    async def _analyze_content_for_field(
        self,
        text: str,
        target_field: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        分析文本内容，智能推荐合适的字段
        """
        if target_field:
            return {
                "suggested_field": target_field,
                "confidence": 1.0,
                "assignments": {target_field: text}
            }

        # 字段匹配规则
        field_patterns = {
            "topic": {
                "keywords": ["主题", "话题", "讨论", "关于", "题目"],
                "patterns": ["讨论.*", "主题是.*", "关于.*"],
                "weight": 1.0
            },
            "title": {
                "keywords": ["标题", "题目", "叫做", "名字"],
                "patterns": ["标题.*", "叫做.*", "名字.*"],
                "weight": 0.9
            },
            "background_materials": {
                "keywords": ["背景", "资料", "材料", "参考", "补充"],
                "patterns": ["背景.*", "参考.*", "材料.*"],
                "weight": 0.8
            },
            "character_name": {
                "keywords": ["角色", "人物", "嘉宾", "主持人"],
                "patterns": ["角色.*", "嘉宾.*", "人物.*"],
                "weight": 0.7
            },
            "persona": {
                "keywords": ["身份", "职业", "专家", "教授", "背景"],
                "patterns": ["身份.*", "职业.*", "专家.*"],
                "weight": 0.8
            },
            "viewpoint": {
                "keywords": ["观点", "看法", "认为", "立场", "态度"],
                "patterns": ["观点.*", "认为.*", "看法.*"],
                "weight": 0.9
            }
        }

        # 计算各字段的匹配分数
        field_scores = {}
        for field, rules in field_patterns.items():
            score = 0

            # 关键词匹配
            for keyword in rules["keywords"]:
                if keyword in text:
                    score += rules["weight"]

            # 模式匹配
            import re
            for pattern in rules["patterns"]:
                if re.search(pattern, text):
                    score += rules["weight"] * 1.5

            field_scores[field] = score

        # 找到最高分字段
        best_field = max(field_scores, key=field_scores.get) if field_scores else "topic"
        best_score = field_scores.get(best_field, 0)

        # 置信度计算
        confidence = min(best_score / 2.0, 1.0)

        # 如果置信度太低，默认分配到主题
        if confidence < 0.3:
            best_field = "topic"
            confidence = 0.5

        return {
            "suggested_field": best_field,
            "confidence": confidence,
            "assignments": {best_field: text},
            "all_scores": field_scores
        }

    async def parse_voice_command(self, text: str) -> Dict[str, Any]:
        """
        解析语音指令
        支持如："设置主题为人工智能"、"添加角色张教授"等
        """
        command_patterns = {
            "set_topic": {
                "patterns": [r"设置主题为(.+)", r"主题是(.+)", r"讨论(.+)"],
                "field": "topic"
            },
            "set_title": {
                "patterns": [r"标题为(.+)", r"题目是(.+)", r"叫做(.+)"],
                "field": "title"
            },
            "add_character": {
                "patterns": [r"添加角色(.+)", r"角色是(.+)", r"嘉宾是(.+)"],
                "field": "character_name"
            },
            "set_viewpoint": {
                "patterns": [r"观点是(.+)", r"认为(.+)", r"立场是(.+)"],
                "field": "viewpoint"
            },
            "set_persona": {
                "patterns": [r"身份是(.+)", r"职业是(.+)", r"专家(.+)"],
                "field": "persona"
            }
        }

        import re
        for command, rules in command_patterns.items():
            for pattern in rules["patterns"]:
                match = re.search(pattern, text)
                if match:
                    content = match.group(1).strip()
                    return {
                        "command": command,
                        "field": rules["field"],
                        "content": content,
                        "original_text": text
                    }

        # 如果没有匹配到指令，返回普通文本分析
        return await self._analyze_content_for_field(text)

    async def process_streaming_audio(self, audio_stream) -> AsyncGenerator[Dict[str, Any], None]:
        """
        处理流式音频输入（实时语音识别）
        """
        # 这里可以实现实时流式识别
        # 目前先返回基础实现
        yield {"type": "partial", "text": "实时识别功能开发中..."}


# 全局ASR服务实例
asr_service = HunyuanASRService()


async def transcribe_audio_file(
    audio_file_path: str,
    target_field: Optional[str] = None
) -> Dict[str, Any]:
    """
    便捷的音频转文字函数
    """
    return await asr_service.transcribe_audio(audio_file_path, target_field)


async def parse_voice_command_text(text: str) -> Dict[str, Any]:
    """
    便捷的语音指令解析函数
    """
    return await asr_service.parse_voice_command(text)