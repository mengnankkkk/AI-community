"""
Chatterbox Multilingual TTS 服务
支持23种语言的零样本语音合成
"""

import asyncio
import os
import tempfile
import logging
from typing import List, Dict, Optional
from pydub import AudioSegment

from ..models.podcast import PodcastScript, CharacterRole, ScriptDialogue
from ..core.config import settings
from .audio_effects_service import AudioEffectsService
from .voice_resolver_service import voice_resolver

logger = logging.getLogger(__name__)


class ChatterboxTTSService:
    """Chatterbox Multilingual TTS 服务"""

    def __init__(self):
        self.model = None
        self.multilingual_model = None
        self.initialized = False
        self.audio_effects = AudioEffectsService()

        # 语言映射
        self.language_map = {
            '中文': 'zh',
            '英文': 'en',
            '英语': 'en',
            '法语': 'fr',
            '日语': 'ja',
            '韩语': 'ko',
            '西班牙语': 'es',
            '德语': 'de',
            '意大利语': 'it',
            '葡萄牙语': 'pt',
            '俄语': 'ru',
            '阿拉伯语': 'ar',
            '印地语': 'hi',
        }

    async def initialize(self):
        """初始化 Chatterbox 模型"""
        if self.initialized:
            return True

        try:
            logger.info("正在初始化 Chatterbox TTS 模型...")

            # 检查是否安装
            try:
                from chatterbox.tts import ChatterboxTTS
                from chatterbox.mtl_tts import ChatterboxMultilingualTTS
            except ImportError:
                logger.error("Chatterbox TTS 未安装，请运行: pip install chatterbox-tts")
                return False

            # 加载英文模型
            self.model = ChatterboxTTS.from_pretrained(device="cpu")
            logger.info("✅ 英文模型加载成功")

            # 加载多语言模型
            self.multilingual_model = ChatterboxMultilingualTTS.from_pretrained(device="cpu")
            logger.info("✅ 多语言模型加载成功")

            self.initialized = True
            logger.info("Chatterbox TTS 初始化完成")
            return True

        except Exception as e:
            logger.error(f"Chatterbox TTS 初始化失败: {str(e)}")
            return False

    def detect_language(self, text: str) -> str:
        """
        检测文本语言

        Args:
            text: 输入文本

        Returns:
            语言代码 (en, zh, fr, etc.)
        """
        # 简单的语言检测
        # 检查是否包含中文字符
        if any('\u4e00' <= char <= '\u9fff' for char in text):
            return 'zh'

        # 检查是否包含日文字符
        if any('\u3040' <= char <= '\u309f' or '\u30a0' <= char <= '\u30ff' for char in text):
            return 'ja'

        # 检查是否包含韩文字符
        if any('\uac00' <= char <= '\ud7af' for char in text):
            return 'ko'

        # 检查是否包含阿拉伯字符
        if any('\u0600' <= char <= '\u06ff' for char in text):
            return 'ar'

        # 默认英文
        return 'en'

    async def synthesize_single_audio(
        self,
        text: str,
        voice_sample_path: Optional[str] = None,
        language: str = 'auto',
        emotion: Optional[str] = None,
        output_path: Optional[str] = None,
        exaggeration: float = 0.5,
        cfg_weight: float = 0.5
    ) -> str:
        """
        合成单个音频片段

        Args:
            text: 要合成的文本
            voice_sample_path: 音色参考文件（可选）
            language: 语言代码（auto自动检测）
            emotion: 情感标签（可选）
            output_path: 输出路径
            exaggeration: 情绪夸张度 (0.0-1.0)
            cfg_weight: 风格权重 (0.0-1.0)

        Returns:
            生成的音频文件路径
        """
        if not await self.initialize():
            raise Exception("Chatterbox TTS 初始化失败")

        # 创建临时输出文件
        if not output_path:
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
            output_path = temp_file.name
            temp_file.close()

        try:
            import torchaudio as ta

            # 自动检测语言
            if language == 'auto':
                language = self.detect_language(text)
                logger.info(f"自动检测语言: {language}")

            # 根据情感调整参数
            if emotion:
                exaggeration, cfg_weight = self._adjust_params_for_emotion(emotion)

            # 选择模型
            if language == 'en':
                # 英文使用专用模型
                if voice_sample_path and os.path.exists(voice_sample_path):
                    wav = self.model.generate(
                        text,
                        audio_prompt_path=voice_sample_path
                    )
                else:
                    wav = self.model.generate(text)
            else:
                # 其他语言使用多语言模型
                if voice_sample_path and os.path.exists(voice_sample_path):
                    wav = self.multilingual_model.generate(
                        text,
                        language_id=language,
                        audio_prompt_path=voice_sample_path,
                        exaggeration=exaggeration,
                        cfg_weight=cfg_weight
                    )
                else:
                    wav = self.multilingual_model.generate(
                        text,
                        language_id=language,
                        exaggeration=exaggeration,
                        cfg_weight=cfg_weight
                    )

            # 保存音频
            sample_rate = self.model.sr if language == 'en' else self.multilingual_model.sr
            ta.save(output_path, wav, sample_rate)

            logger.info(f"✅ 音频合成成功: {output_path}")
            return output_path

        except Exception as e:
            logger.error(f"音频合成失败: {str(e)}")
            raise Exception(f"Chatterbox TTS 合成失败: {str(e)}")

    def _adjust_params_for_emotion(self, emotion: str) -> tuple:
        """
        根据情感调整生成参数

        Returns:
            (exaggeration, cfg_weight)
        """
        emotion_params = {
            "激动": (0.8, 0.3),
            "开心": (0.7, 0.4),
            "悲伤": (0.6, 0.5),
            "愤怒": (0.9, 0.2),
            "平静": (0.3, 0.6),
            "温暖": (0.5, 0.5),
            "严肃": (0.4, 0.6),
            "幽默": (0.7, 0.4),
        }

        return emotion_params.get(emotion, (0.5, 0.5))

    async def synthesize_script_audio(
        self,
        script: PodcastScript,
        characters: List[CharacterRole],
        task_id: str,
        atmosphere: str = "轻松幽默",
        enable_effects: bool = True,
        enable_bgm: bool = True
    ) -> str:
        """
        合成完整播客音频

        Args:
            script: 播客脚本
            characters: 角色列表
            task_id: 任务ID
            atmosphere: 氛围
            enable_effects: 是否启用音效
            enable_bgm: 是否启用背景音乐

        Returns:
            生成的音频文件路径
        """
        if not await self.initialize():
            raise Exception("Chatterbox TTS 初始化失败")

        # 创建任务目录
        task_dir = os.path.join(settings.audio_output_dir, task_id)
        os.makedirs(task_dir, exist_ok=True)

        # 为每个角色准备音色样本（使用统一音色解析服务）
        character_voice_samples = {}
        for char in characters:
            voice_sample_path = None

            # 优先使用角色自带的voice_file
            if hasattr(char, 'voice_file') and char.voice_file:
                if os.path.exists(char.voice_file):
                    voice_sample_path = char.voice_file
                    logger.info(f"角色 {char.name} 使用指定音色文件: {char.voice_file}")

            # 如果没有voice_file，使用voice_resolver解析voice_description
            if not voice_sample_path and hasattr(char, 'voice_description') and char.voice_description:
                _, resolved_voice_file = voice_resolver.resolve_voice(
                    char.voice_description,
                    "chatterbox"
                )
                if resolved_voice_file and os.path.exists(resolved_voice_file):
                    voice_sample_path = resolved_voice_file
                    logger.info(f"角色 {char.name} 使用解析的音色文件: {resolved_voice_file}")

            if voice_sample_path:
                character_voice_samples[char.name] = voice_sample_path
            else:
                logger.warning(f"角色 {char.name} 没有可用的音色样本，将使用默认音色")

        # 检测主要语言
        all_text = ' '.join([d.content for d in script.dialogues])
        main_language = self.detect_language(all_text)
        logger.info(f"播客主要语言: {main_language}")

        # 合成每个对话片段
        audio_segments = []

        for i, dialogue in enumerate(script.dialogues):
            voice_sample_path = character_voice_samples.get(dialogue.character_name)
            output_path = os.path.join(task_dir, f"segment_{i:03d}.wav")

            try:
                # 合成音频
                result_path = await self.synthesize_single_audio(
                    text=dialogue.content,
                    voice_sample_path=voice_sample_path,
                    language=main_language,
                    emotion=dialogue.emotion,
                    output_path=output_path
                )

                if result_path and os.path.exists(result_path):
                    # 加载音频
                    segment = AudioSegment.from_wav(result_path)

                    # 添加音效
                    if enable_effects:
                        position = None
                        if i == 0:
                            position = "opening"
                        elif i == len(script.dialogues) - 1:
                            position = "closing"

                        effects = self.audio_effects.analyze_dialogue_for_effects(
                            content=dialogue.content,
                            emotion=dialogue.emotion,
                            position=position
                        )
                        segment = self.audio_effects.add_effects_to_segment(segment, effects)

                    audio_segments.append(segment)
                    logger.info(f"成功合成片段 {i}: {dialogue.character_name}")

                    # 清理临时文件
                    try:
                        os.remove(result_path)
                    except:
                        pass

            except Exception as e:
                logger.error(f"片段合成失败 {i}: {dialogue.character_name} - {str(e)}")
                continue

        if not audio_segments:
            raise Exception("所有音频片段合成失败")

        # 拼接音频
        final_audio = await self._concatenate_audio_with_effects(
            audio_segments, task_dir, task_id, atmosphere, enable_bgm
        )

        return final_audio

    async def _concatenate_audio_with_effects(
        self,
        audio_segments: List[AudioSegment],
        task_dir: str,
        task_id: str,
        atmosphere: str,
        enable_bgm: bool
    ) -> str:
        """拼接音频并应用效果"""
        try:
            # 生成开场和结尾
            intro_audio, outro_audio = self.audio_effects.create_intro_outro(atmosphere=atmosphere)

            # 拼接
            combined = AudioSegment.empty()

            if intro_audio:
                combined += intro_audio

            # 添加对话片段
            for i, segment in enumerate(audio_segments):
                if i > 0:
                    pause_duration = 800 if i % 3 != 0 else 1200
                    pause = self.audio_effects.generate_silence_with_ambience(
                        duration=pause_duration,
                        atmosphere="studio"
                    )
                    combined += pause
                combined += segment

            if outro_audio:
                combined += outro_audio

            # 专业后处理
            combined = self.audio_effects.apply_professional_mastering(combined)

            # 添加BGM
            if enable_bgm:
                combined = self.audio_effects.add_background_music(
                    audio=combined,
                    atmosphere=atmosphere,
                    fade_in_duration=3000,
                    fade_out_duration=3000
                )

            # 保存
            final_path = os.path.join(task_dir, f"podcast_{task_id}.mp3")
            combined.export(final_path, format="mp3", bitrate="192k")

            logger.info(f"完成 Chatterbox TTS 音频处理: {final_path}")
            return final_path

        except Exception as e:
            logger.error(f"音频处理失败: {str(e)}")
            raise Exception(f"音频处理失败: {str(e)}")

    async def health_check(self) -> Dict[str, any]:
        """健康检查"""
        try:
            if await self.initialize():
                return {
                    "status": "healthy",
                    "service": "Chatterbox TTS",
                    "models": {
                        "english": "loaded" if self.model else "not loaded",
                        "multilingual": "loaded" if self.multilingual_model else "not loaded"
                    }
                }
            else:
                return {
                    "status": "unhealthy",
                    "service": "Chatterbox TTS",
                    "error": "模型初始化失败"
                }
        except Exception as e:
            return {
                "status": "error",
                "service": "Chatterbox TTS",
                "error": str(e)
            }
