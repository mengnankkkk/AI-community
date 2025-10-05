"""
NihalGazi/Text-To-Speech-Unlimited Gradio客户端服务
支持13种预设音色、情感控制和种子管理
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


class NihalTTSService:
    """NihalGazi TTS Gradio在线服务客户端"""

    def __init__(self):
        self.client = None
        self.space_name = getattr(settings, 'nihal_tts_space', "NihalGazi/Text-To-Speech-Unlimited")
        self.initialized = False

        # 13个预设音色
        self.available_voices = [
            "alloy",    # 合金 - 标准男声
            "echo",     # 回声 - 有磁性男声
            "fable",    # 寓言 - 男声
            "onyx",     # 玛瑙 - 沉稳男声
            "nova",     # 新星 - 女声
            "shimmer",  # 闪光 - 活力女声
            "coral",    # 珊瑚 - 女声
            "verse",    # 诗句 - 女声
            "ballad",   # 民谣 - 女声
            "ash",      # 灰烬 - 男声
            "sage",     # 智者 - 男声
            "amuch",    # 阿穆奇 - 特色
            "dan",      # 丹 - 特色
        ]

        # 角色音色映射配置
        self.character_voice_mapping = {
            "沉稳": "onyx",
            "浑厚": "echo",
            "男中音": "alloy",
            "清脆": "nova",
            "有活力": "shimmer",
            "女声": "nova",
            "标准": "alloy",
            "有磁性": "echo",
            "男声": "fable",
            "温暖": "coral",
            "知性": "sage",
            "活力": "shimmer",
            "优雅": "verse",
            "民谣": "ballad",
            "智慧": "sage",
            # 角色类型映射
            "主持人": "alloy",
            "嘉宾": "coral",
            "博士": "sage",
            "教授": "sage",
            "讲师": "echo",
            "专家": "onyx",
        }

        # 情感映射配置（映射到情感描述字符串）
        self.emotion_mapping = {
            "开心": "happy, joyful, cheerful",
            "悲伤": "sad, melancholic, sorrowful",
            "激动": "excited, enthusiastic, energetic",
            "平静": "calm, peaceful, serene",
            "愤怒": "angry, furious, intense",
            "惊讶": "surprised, amazed, astonished",
            "温暖": "warm, gentle, caring",
            "严肃": "serious, formal, professional",
            "幽默": "humorous, playful, funny",
            "思考": "thoughtful, contemplative, reflective",
            "自信": "confident, assertive, strong",
            "害怕": "fearful, nervous, anxious",
            "好奇": "curious, interested, inquisitive",
            "感动": "touched, emotional, moved",
            "轻松": "relaxed, casual, easygoing",
            # 补充常见情感词
            "友好": "friendly, warm, welcoming",
            "期待": "expectant, anticipating, hopeful",
            "热情": "passionate, enthusiastic, energetic",
            "失望": "disappointed, let down, discouraged",
            "紧张": "nervous, tense, anxious",
            "焦虑": "anxious, worried, uneasy",
            "沮丧": "depressed, downcast, discouraged",
            "兴奋": "excited, thrilled, elated",
            "无奈": "helpless, resigned, frustrated",
            "坚定": "determined, resolute, firm",
            "犹豫": "hesitant, uncertain, wavering",
            "欣慰": "gratified, pleased, comforted",
            "愧疚": "guilty, ashamed, remorseful",
            "感激": "grateful, thankful, appreciative",
            "怀疑": "doubtful, skeptical, suspicious",
            "渴望": "eager, longing, yearning",
            "同情": "sympathetic, compassionate, understanding",
        }

    async def initialize_client(self):
        """初始化Gradio客户端"""
        if self.initialized:
            return True

        try:
            logger.info(f"正在连接NihalGazi TTS服务: {self.space_name}")

            # 尝试禁用SSL验证以解决代理TLS问题（临时方案）
            import os
            os.environ['GRADIO_SSL_VERIFY'] = 'false'

            self.client = Client(self.space_name)
            self.initialized = True
            logger.info("NihalGazi TTS客户端初始化成功")
            return True

        except Exception as e:
            logger.error(f"NihalGazi TTS客户端初始化失败: {str(e)}")
            return False

    def get_voice_for_character(self, voice_description: str) -> str:
        """根据音色描述选择合适的语音"""
        if not voice_description:
            return "alloy"  # 默认音色

        voice_description_lower = voice_description.lower()

        # 优先检查：如果传入的已经是有效的音色ID，直接使用
        if voice_description_lower in self.available_voices:
            logger.info(f"直接使用音色ID: {voice_description_lower}")
            return voice_description_lower

        # 精确匹配关键词
        for keyword, voice in self.character_voice_mapping.items():
            if keyword.lower() in voice_description_lower:
                logger.info(f"音色映射: {voice_description} -> {voice}")
                return voice

        # 性别识别回退
        if "女" in voice_description or "female" in voice_description_lower:
            return "nova"
        elif "男" in voice_description or "male" in voice_description_lower:
            return "alloy"

        # 默认返回标准音色
        logger.warning(f"未匹配到音色关键词: {voice_description}，使用默认音色")
        return "alloy"

    def get_emotion_string(self, emotion: Optional[str]) -> str:
        """根据情感获取情感描述字符串"""
        if not emotion:
            return "neutral, natural"  # 默认中性情感

        emotion_lower = emotion.lower() if emotion else ""

        # 精确匹配
        for keyword, emotion_str in self.emotion_mapping.items():
            if keyword.lower() in emotion_lower:
                logger.info(f"情感映射: {emotion} -> {emotion_str}")
                return emotion_str

        # 如果没有匹配到，使用原始情感词
        logger.warning(f"未匹配到情感关键词: {emotion}，使用原始值")
        return emotion or "neutral"

    async def synthesize_single_audio(
        self,
        text: str,
        voice: str,
        emotion: Optional[str] = None,
        use_random_seed: bool = True,
        specific_seed: float = 12345,
        output_path: str = None,
        max_retries: int = 3
    ) -> str:
        """合成单个音频片段（带重试机制）"""
        if not await self.initialize_client():
            raise Exception("NihalGazi TTS客户端初始化失败")

        # 如果没有指定输出路径，创建临时文件
        if not output_path:
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
            output_path = temp_file.name
            temp_file.close()

        # 【重要】清理文本 - 移除舞台指示和命令提示
        cleaned_text = clean_for_tts(text, emotion)

        # 记录清理前后的差异（便于调试）
        if cleaned_text != text:
            logger.info(f"文本清理: [{text[:50]}...] -> [{cleaned_text[:50]}...]")

        # 获取情感字符串
        emotion_str = self.get_emotion_string(emotion)

        # 重试机制
        last_error = None
        for attempt in range(max_retries):
            try:
                # 调用NihalGazi TTS API
                logger.info(f"调用NihalGazi TTS API (尝试{attempt+1}/{max_retries}): text=[{cleaned_text[:30]}...], voice={voice}, emotion={emotion_str}")
                result = self.client.predict(
                    prompt=cleaned_text,  # 使用清理后的文本
                    voice=voice,
                    emotion=emotion_str,
                    use_random_seed=use_random_seed,
                    specific_seed=specific_seed,
                    api_name="/text_to_speech_app"
                )

                # result是一个元组 (音频文件路径, 状态字符串)
                audio_path, status = result
                logger.info(f"NihalGazi TTS状态: {status}")

                if audio_path and os.path.exists(audio_path):
                    # 复制到指定输出路径
                    import shutil
                    shutil.copy2(audio_path, output_path)
                    logger.info(f"音频合成成功: {output_path}")
                    return output_path
                else:
                    raise Exception("NihalGazi TTS返回无效结果")

            except Exception as e:
                last_error = e
                logger.warning(f"第{attempt+1}次尝试失败: {str(e)}")

                if attempt < max_retries - 1:
                    # 等待后重试（指数退避）
                    wait_time = 2 ** attempt  # 1s, 2s, 4s...
                    logger.info(f"等待{wait_time}秒后重试...")
                    await asyncio.sleep(wait_time)

                    # 重新初始化客户端
                    self.initialized = False
                    if not await self.initialize_client():
                        logger.error("重新初始化客户端失败")
                        continue

        # 所有重试都失败
        logger.error(f"NihalGazi TTS音频合成失败（已重试{max_retries}次）: {str(last_error)}")
        raise Exception(f"音频合成失败: {str(last_error)}")

    async def synthesize_script_audio(
        self,
        script: PodcastScript,
        characters: List[CharacterRole],
        task_id: str,
        atmosphere: str = "轻松幽默",
        enable_effects: bool = True,
        enable_bgm: bool = True
    ) -> str:
        """合成完整播客音频"""
        if not await self.initialize_client():
            raise Exception("NihalGazi TTS客户端初始化失败")

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

        # 使用固定种子确保角色音色一致性
        base_seed = 42000  # 基础种子

        for i, dialogue in enumerate(script.dialogues):
            voice = character_voices.get(dialogue.character_name, "alloy")
            output_path = os.path.join(task_dir, f"segment_{i:03d}.wav")

            # 为每个片段计算种子（同角色使用相似种子）
            character_index = list(character_voices.keys()).index(dialogue.character_name) if dialogue.character_name in character_voices else 0
            segment_seed = base_seed + character_index * 1000 + i

            try:
                result_path = await self.synthesize_single_audio(
                    text=dialogue.content,
                    voice=voice,
                    emotion=dialogue.emotion,
                    use_random_seed=False,  # 使用固定种子确保一致性
                    specific_seed=segment_seed,
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

            logger.info(f"NihalGazi TTS音频拼接完成: {final_path}")
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
                    "service": "NihalGazi-TTS",
                    "space_name": self.space_name,
                    "initialized": self.initialized,
                    "available_voices": len(self.available_voices)
                }
            else:
                return {
                    "status": "unhealthy",
                    "service": "NihalGazi-TTS",
                    "error": "客户端初始化失败"
                }
        except Exception as e:
            return {
                "status": "error",
                "service": "NihalGazi-TTS",
                "error": str(e)
            }