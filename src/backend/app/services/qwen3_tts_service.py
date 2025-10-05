"""
Qwen3-TTS Gradio客户端服务
基于Qwen/Qwen3-TTS-Demo的在线TTS服务
支持17种预设音色和11种语言
"""

import asyncio
import os
import logging
import tempfile
from typing import List, Dict, Optional
from pydub import AudioSegment
from gradio_client import Client

from ..models.podcast import PodcastScript, CharacterRole
from ..core.config import settings
from ..utils.text_cleaner import clean_for_tts

logger = logging.getLogger(__name__)


class Qwen3TTSService:
    """Qwen3-TTS Gradio在线服务客户端"""

    def __init__(self):
        self.client = None
        self.space_name = getattr(settings, 'qwen3_tts_space', "Qwen/Qwen3-TTS-Demo")
        self.initialized = False

        # 17个预设音色（Gradio API要求完整名称）
        self.available_voices = [
            "Cherry / 芊悦",        # 女声，甜美
            "Ethan / 晨煦",         # 男声，标准
            "Jennifer / 詹妮弗",     # 女声，英文风格
            "Ryan / 甜茶",          # 男声，活力
            "Katerina / 卡捷琳娜",   # 女声，知性
            "Nofish / 不吃鱼",       # 特色
            "Elias / 墨讲师",        # 男声，讲师风格
            "Li / 南京-老李",        # 男声，南京口音
            "Marcus / 陕西-秦川",    # 男声，陕西口音
            "Roy / 闽南-阿杰",       # 男声，闽南口音
            "Peter / 天津-李彼得",   # 男声，天津口音
            "Eric / 四川-程川",      # 男声，四川口音
            "Rocky / 粤语-阿强",     # 男声，粤语
            "Kiki / 粤语-阿清",      # 女声，粤语
            "Sunny / 四川-晴儿",     # 女声，四川口音
            "Jada / 上海-阿珍",      # 女声，上海口音
            "Dylan / 北京-晓东",     # 男声，北京口音
        ]

        # 角色音色映射配置
        self.character_voice_mapping = {
            "沉稳": "Elias / 墨讲师",
            "浑厚": "Marcus / 陕西-秦川",
            "男中音": "Ethan / 晨煦",
            "清脆": "Cherry / 芊悦",
            "有活力": "Ryan / 甜茶",
            "女声": "Cherry / 芊悦",
            "标准": "Ethan / 晨煦",
            "有磁性": "Elias / 墨讲师",
            "男声": "Ethan / 晨煦",
            "温暖": "Jennifer / 詹妮弗",
            "知性": "Katerina / 卡捷琳娜",
            # 地方口音映射
            "南京": "Li / 南京-老李",
            "陕西": "Marcus / 陕西-秦川",
            "闽南": "Roy / 闽南-阿杰",
            "天津": "Peter / 天津-李彼得",
            "四川": "Eric / 四川-程川",
            "粤语": "Rocky / 粤语-阿强",
            "广东": "Rocky / 粤语-阿强",
            "上海": "Jada / 上海-阿珍",
            "北京": "Dylan / 北京-晓东",
            # 角色类型映射
            "主持人": "Ethan / 晨煦",
            "嘉宾": "Jennifer / 詹妮弗",
            "博士": "Katerina / 卡捷琳娜",
            "教授": "Elias / 墨讲师",
            "讲师": "Elias / 墨讲师",
        }

    async def initialize_client(self):
        """初始化Gradio客户端"""
        if self.initialized:
            return True

        try:
            logger.info(f"正在连接Qwen3-TTS Gradio服务: {self.space_name}")
            self.client = Client(self.space_name)
            self.initialized = True
            logger.info("Qwen3-TTS Gradio客户端初始化成功")
            return True

        except Exception as e:
            logger.error(f"Qwen3-TTS Gradio客户端初始化失败: {str(e)}")
            return False

    def get_voice_for_character(self, voice_description: str) -> str:
        """根据音色描述选择合适的语音"""
        if not voice_description:
            return "Cherry / 芊悦"  # 默认音色

        voice_description_lower = voice_description.lower()

        # 优先检查：如果传入的已经是有效的音色ID，直接使用
        # 支持完整匹配或部分匹配（如 "cherry" 匹配 "Cherry / 芊悦"）
        for available_voice in self.available_voices:
            if (voice_description == available_voice or
                voice_description_lower == available_voice.lower() or
                voice_description_lower in available_voice.lower().split('/')[0].strip().lower()):
                logger.info(f"直接使用音色ID: {available_voice}")
                return available_voice

        # 精确匹配关键词
        for keyword, voice in self.character_voice_mapping.items():
            if keyword.lower() in voice_description_lower:
                logger.info(f"音色映射: {voice_description} -> {voice}")
                return voice

        # 性别识别回退
        if "女" in voice_description or "female" in voice_description_lower:
            return "Cherry / 芊悦"
        elif "男" in voice_description or "male" in voice_description_lower:
            return "Ethan / 晨煦"

        # 默认返回标准音色
        logger.warning(f"未匹配到音色关键词: {voice_description}，使用默认音色")
        return "Cherry / 芊悦"

    async def synthesize_single_audio(self, text: str, voice: str, output_path: str = None) -> str:
        """合成单个音频片段"""
        if not await self.initialize_client():
            raise Exception("Qwen3-TTS客户端初始化失败")

        try:
            # 如果没有指定输出路径，创建临时文件
            if not output_path:
                temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
                output_path = temp_file.name
                temp_file.close()

            # 【重要】清理文本 - 移除舞台指示和命令提示
            cleaned_text = clean_for_tts(text, emotion=None)

            # 记录清理前后的差异（便于调试）
            if cleaned_text != text:
                logger.info(f"文本清理: [{text[:50]}...] -> [{cleaned_text[:50]}...]")

            # 调用Qwen3-TTS API
            logger.info(f"调用Qwen3-TTS API: text=[{cleaned_text[:30]}...], voice={voice}")
            result = self.client.predict(
                text=cleaned_text,  # 使用清理后的文本
                voice_display=voice,
                language_display="Auto / 自动",  # 自动检测语言
                api_name="/tts_interface"
            )

            # result是音频文件路径
            if result and os.path.exists(result):
                # 复制到指定输出路径
                import shutil
                shutil.copy2(result, output_path)
                logger.info(f"音频合成成功: {output_path}")
                return output_path
            else:
                raise Exception("Qwen3-TTS返回无效结果")

        except Exception as e:
            logger.error(f"Qwen3-TTS音频合成失败: {str(e)}")
            raise Exception(f"音频合成失败: {str(e)}")

    async def synthesize_script_audio(self, script: PodcastScript, characters: List[CharacterRole],
                                     task_id: str, atmosphere: str = "轻松幽默",
                                     enable_effects: bool = True, enable_bgm: bool = True) -> str:
        """合成完整播客音频"""
        if not await self.initialize_client():
            raise Exception("Qwen3-TTS客户端初始化失败")

        # 创建任务专用目录
        task_dir = os.path.join(settings.audio_output_dir, task_id)
        os.makedirs(task_dir, exist_ok=True)

        # 为每个角色映射语音
        character_voices = {}
        for char in characters:
            character_voices[char.name] = self.get_voice_for_character(char.voice_description)
            logger.info(f"角色 {char.name} 使用音色: {character_voices[char.name]}")

        # 合成每个对话片段
        audio_files = []

        for i, dialogue in enumerate(script.dialogues):
            voice = character_voices.get(dialogue.character_name, "Cherry / 芊悦")
            output_path = os.path.join(task_dir, f"segment_{i:03d}.wav")

            try:
                result_path = await self.synthesize_single_audio(
                    text=dialogue.content,
                    voice=voice,
                    output_path=output_path
                )

                if result_path and os.path.exists(result_path):
                    audio_files.append(result_path)
                    logger.info(f"成功合成片段 {i}: {dialogue.character_name}")
                else:
                    logger.error(f"音频合成失败: {output_path}")

            except Exception as e:
                logger.error(f"片段合成失败 {i}: {dialogue.character_name} - {str(e)}")
                continue

        if not audio_files:
            raise Exception("所有音频片段合成失败")

        # 拼接音频
        final_audio_path = await self.concatenate_audio(audio_files, task_dir, task_id)

        # 清理临时文件
        for audio_file in audio_files:
            try:
                os.remove(audio_file)
            except:
                pass

        return final_audio_path

    async def concatenate_audio(self, audio_files: List[str], task_dir: str, task_id: str) -> str:
        """拼接音频文件"""
        try:
            # 加载第一个音频文件
            combined = AudioSegment.from_file(audio_files[0])

            # 依次拼接其他音频文件
            for audio_file in audio_files[1:]:
                if os.path.exists(audio_file):
                    segment = AudioSegment.from_file(audio_file)
                    # 添加短暂停顿（500ms）
                    pause = AudioSegment.silent(duration=500)
                    combined = combined + pause + segment

            # 标准化音量
            combined = combined.normalize()

            # 保存最终音频
            final_path = os.path.join(task_dir, f"podcast_{task_id}.mp3")
            combined.export(final_path, format="mp3", bitrate="192k")

            logger.info(f"Qwen3-TTS音频拼接完成: {final_path}")
            return final_path

        except Exception as e:
            logger.error(f"音频拼接失败: {str(e)}")
            raise Exception(f"音频拼接失败: {str(e)}")

    def get_audio_duration(self, audio_path: str) -> int:
        """获取音频时长（秒）"""
        try:
            audio = AudioSegment.from_file(audio_path)
            return len(audio) // 1000  # 转换为秒
        except:
            return 0

    async def health_check(self) -> Dict[str, any]:
        """健康检查"""
        try:
            if await self.initialize_client():
                return {
                    "status": "healthy",
                    "service": "Qwen3-TTS",
                    "space_name": self.space_name,
                    "initialized": self.initialized,
                    "available_voices": len(self.available_voices)
                }
            else:
                return {
                    "status": "unhealthy",
                    "service": "Qwen3-TTS",
                    "error": "客户端初始化失败"
                }
        except Exception as e:
            return {
                "status": "error",
                "service": "Qwen3-TTS",
                "error": str(e)
            }