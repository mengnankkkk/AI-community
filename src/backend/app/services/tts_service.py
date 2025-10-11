import openai
import asyncio
from typing import List, Dict, Optional
import os
import shutil
from pydub import AudioSegment
from ..models.podcast import PodcastScript, CharacterRole
from ..core.config import settings
from ..utils.text_cleaner import clean_for_tts
import logging

logger = logging.getLogger(__name__)

class OpenAITTSService:
    """OpenAI TTS服务（作为备选方案）"""

    def __init__(self):
        self.client = openai.OpenAI(
            api_key=settings.openai_api_key,
            base_url=settings.openai_base_url
        )
        # OpenAI TTS支持的音色列表
        self.available_voices = ["alloy", "echo", "fable", "onyx", "nova", "shimmer"]

        self.voice_mapping = {
            "沉稳": "onyx",
            "浑厚": "onyx",
            "男中音": "onyx",
            "清脆": "nova",
            "有活力": "shimmer",
            "女声": "nova",
            "标准": "alloy",
            "有磁性": "echo",
            "男声": "fable",
            "温暖": "alloy"
        }

    def get_voice_for_character(self, voice_description: str) -> str:
        """根据音色描述选择合适的语音"""
        if not voice_description:
            return "alloy"  # 默认音色

        voice_description = voice_description.lower()

        # 优先检查：如果传入的已经是有效的音色ID，直接使用
        if voice_description in self.available_voices:
            logger.info(f"直接使用音色ID: {voice_description}")
            return voice_description

        # 关键词映射
        for keyword, voice in self.voice_mapping.items():
            if keyword in voice_description:
                logger.info(f"音色映射: {voice_description} -> {voice}")
                return voice

        # 默认返回标准音色
        logger.warning(f"未匹配到音色关键词: {voice_description}，使用默认音色")
        return "alloy"  # 默认音色

    async def synthesize_single_audio(self, text: str, voice: str, output_path: str) -> bool:
        """合成单个音频片段"""
        try:
            # 检查API密钥是否有效
            if not settings.openai_api_key or settings.openai_api_key == "your_openai_api_key_here":
                logger.warning("OpenAI API密钥未配置，生成静音文件")
                return self._create_placeholder_audio(output_path, text)

            # 【重要】清理文本 - 移除舞台指示和命令提示
            cleaned_text = clean_for_tts(text, emotion=None)

            # 记录清理前后的差异（便于调试）
            if cleaned_text != text:
                logger.info(f"文本清理: [{text[:50]}...] -> [{cleaned_text[:50]}...]")

            response = self.client.audio.speech.create(
                model=settings.tts_model,
                voice=voice,
                input=cleaned_text,  # 使用清理后的文本
                response_format="mp3"
            )

            with open(output_path, 'wb') as f:
                f.write(response.content)

            return True
        except Exception as e:
            logger.error(f"OpenAI TTS合成失败 {output_path}: {str(e)}")
            logger.warning("尝试生成占位符音频")
            return self._create_placeholder_audio(output_path, text)

    def _create_placeholder_audio(self, output_path: str, text: str) -> bool:
        """创建占位符音频（静音 + 提示音）"""
        try:
            from pydub import AudioSegment
            from pydub.generators import Sine

            # 根据文本长度估算音频时长（每个字0.3秒）
            duration_ms = max(len(text) * 300, 1000)  # 最少1秒

            # 生成低频提示音
            tone = Sine(440).to_audio_segment(duration=500)  # 0.5秒的A4音调
            silence = AudioSegment.silent(duration=duration_ms - 500)

            # 组合音频：提示音 + 静音
            placeholder_audio = tone + silence
            placeholder_audio = placeholder_audio.fade_in(100).fade_out(100) - 10  # 降低音量

            # 导出为MP3
            placeholder_audio.export(output_path, format="mp3", bitrate="128k")
            logger.info(f"生成占位符音频: {output_path} (时长: {duration_ms}ms)")
            return True

        except Exception as e:
            logger.error(f"生成占位符音频失败: {str(e)}")
            return False

    async def synthesize_script_audio(self, script: PodcastScript, characters: List[CharacterRole],
                                     task_id: str, atmosphere: str = "轻松幽默",
                                     enable_effects: bool = True, enable_bgm: bool = True) -> str:
        """合成完整播客音频（OpenAI TTS不支持高级音效，忽略相关参数）"""
        logger.info(f"OpenAI TTS开始合成播客音频，忽略高级参数: atmosphere={atmosphere}, effects={enable_effects}, bgm={enable_bgm}")

        # 创建任务专用目录
        task_dir = os.path.join(settings.audio_output_dir, task_id)
        os.makedirs(task_dir, exist_ok=True)

        # 为每个角色映射语音
        character_voices = {}
        for char in characters:
            character_voices[char.name] = self.get_voice_for_character(char.voice_description)

        # 合成每个对话片段（并发 + 缓存复用）
        max_concurrency = max(1, getattr(settings, 'tts_max_concurrency', 3))
        semaphore = asyncio.Semaphore(max_concurrency)
        segment_cache: Dict[tuple, str] = {}
        segment_results = []

        async def process_segment(index: int, dialogue):
            voice = character_voices.get(dialogue.character_name, "alloy")
            output_path = os.path.join(task_dir, f"segment_{index:03d}.mp3")
            cleaned_text = clean_for_tts(dialogue.content, None)
            cache_key = (voice, cleaned_text)

            if cache_key in segment_cache and os.path.exists(segment_cache[cache_key]):
                try:
                    shutil.copyfile(segment_cache[cache_key], output_path)
                    logger.debug(f"复用缓存音频: segment_{index:03d}")
                    return index, output_path, True
                except Exception as copy_error:
                    logger.warning(f"缓存复制失败，重新合成: {copy_error}")

            async with semaphore:
                success = await self.synthesize_single_audio(dialogue.content, voice, output_path)

            if success:
                segment_cache[cache_key] = output_path
            else:
                logger.error(f"音频合成失败: {output_path}")

            return index, output_path, success

        tasks = [asyncio.create_task(process_segment(i, dialogue)) for i, dialogue in enumerate(script.dialogues)]

        for result in await asyncio.gather(*tasks, return_exceptions=True):
            if isinstance(result, Exception):
                logger.error(f"音频片段合成任务异常: {result}")
                continue
            segment_results.append(result)

        successful_segments = [path for _, path, ok in sorted(segment_results, key=lambda item: item[0]) if ok]

        if not successful_segments:
            raise Exception("所有音频片段合成失败")

        # 拼接音频
        final_audio_path = await self.concatenate_audio(successful_segments, task_dir, task_id)

        # 清理临时文件
        for audio_file in successful_segments:
            try:
                os.remove(audio_file)
            except:
                pass

        return final_audio_path

    async def concatenate_audio(self, audio_files: List[str], task_dir: str, task_id: str) -> str:
        """拼接音频文件"""
        try:
            # 加载第一个音频文件
            combined = AudioSegment.from_mp3(audio_files[0])

            # 依次拼接其他音频文件
            for audio_file in audio_files[1:]:
                if os.path.exists(audio_file):
                    segment = AudioSegment.from_mp3(audio_file)
                    # 添加短暂停顿（500ms）
                    pause = AudioSegment.silent(duration=500)
                    combined = combined + pause + segment

            # 保存最终音频
            final_path = os.path.join(task_dir, f"podcast_{task_id}.mp3")
            combined.export(final_path, format="mp3")

            return final_path

        except Exception as e:
            logger.error(f"音频拼接失败: {str(e)}")
            raise Exception(f"音频拼接失败: {str(e)}")


class TTSService:
    """统一的TTS服务管理器"""

    def __init__(self):
        self.tts_engine = getattr(settings, 'tts_engine', 'qwen3_tts')  # 默认使用Qwen3-TTS
        self.openai_service = None
        self.indextts_service = None
        self.indextts2_gradio_service = None
        self.qwen3_tts_service = None
        self.nihal_tts_service = None
        self.chatterbox_service = None  # Chatterbox Multilingual TTS

    async def get_tts_service(self):
        """获取当前配置的TTS服务"""
        if self.tts_engine.lower() == 'qwen3_tts':
            if not self.qwen3_tts_service:
                try:
                    from .qwen3_tts_service import Qwen3TTSService
                    self.qwen3_tts_service = Qwen3TTSService()

                    # 检查服务是否可用
                    health = await self.qwen3_tts_service.health_check()
                    if health["status"] == "healthy":
                        logger.info("使用Qwen3-TTS引擎")
                        return self.qwen3_tts_service
                    else:
                        logger.warning(f"Qwen3-TTS不可用: {health.get('error', '未知错误')}，回退到IndexTTS-2 Gradio")
                        self.tts_engine = 'indextts2_gradio'
                except ImportError as e:
                    logger.warning(f"Qwen3-TTS服务导入失败: {str(e)}，使用IndexTTS-2 Gradio")
                    self.tts_engine = 'indextts2_gradio'
                except Exception as e:
                    logger.warning(f"Qwen3-TTS服务初始化失败: {str(e)}，使用Chatterbox TTS")
                    self.tts_engine = 'chatterbox'

        if self.tts_engine.lower() == 'chatterbox':
            if not self.chatterbox_service:
                try:
                    from .chatterbox_tts_service import ChatterboxTTSService
                    self.chatterbox_service = ChatterboxTTSService()

                    # 检查服务是否可用
                    health = await self.chatterbox_service.health_check()
                    if health["status"] == "healthy":
                        logger.info("使用Chatterbox Multilingual TTS引擎（支持23种语言）")
                        return self.chatterbox_service
                    else:
                        logger.warning(f"Chatterbox TTS不可用: {health.get('error', '未知错误')}，回退到NihalGazi TTS")
                        self.tts_engine = 'nihal_tts'
                except ImportError as e:
                    logger.warning(f"Chatterbox TTS未安装（pip install chatterbox-tts），使用NihalGazi TTS")
                    self.tts_engine = 'nihal_tts'
                except Exception as e:
                    logger.warning(f"Chatterbox TTS初始化失败: {str(e)}，使用NihalGazi TTS")
                    self.tts_engine = 'nihal_tts'

        if self.tts_engine.lower() == 'nihal_tts':
            if not self.nihal_tts_service:
                try:
                    from .nihal_tts_service import NihalTTSService
                    self.nihal_tts_service = NihalTTSService()

                    # 检查服务是否可用
                    health = await self.nihal_tts_service.health_check()
                    if health["status"] == "healthy":
                        logger.info("使用NihalGazi-TTS引擎")
                        return self.nihal_tts_service
                    else:
                        logger.warning(f"NihalGazi-TTS不可用: {health.get('error', '未知错误')}，回退到IndexTTS-2 Gradio")
                        self.tts_engine = 'indextts2_gradio'
                except ImportError as e:
                    logger.warning(f"NihalGazi-TTS服务导入失败: {str(e)}，使用IndexTTS-2 Gradio")
                    self.tts_engine = 'indextts2_gradio'
                except Exception as e:
                    logger.warning(f"NihalGazi-TTS服务初始化失败: {str(e)}，使用IndexTTS-2 Gradio")
                    self.tts_engine = 'indextts2_gradio'

        if self.tts_engine.lower() == 'indextts2_gradio':
            if not self.indextts2_gradio_service:
                try:
                    from .indextts2_gradio_service import IndexTTS2GradioService
                    self.indextts2_gradio_service = IndexTTS2GradioService()

                    # 检查服务是否可用
                    health = await self.indextts2_gradio_service.health_check()
                    if health["status"] == "healthy":
                        logger.info("使用IndexTTS-2 Gradio引擎")
                        return self.indextts2_gradio_service
                    else:
                        logger.warning(f"IndexTTS-2 Gradio不可用: {health.get('error', '未知错误')}，回退到OpenAI TTS")
                        self.tts_engine = 'openai'
                except ImportError as e:
                    logger.warning(f"IndexTTS-2 Gradio服务导入失败: {str(e)}，使用OpenAI TTS")
                    self.tts_engine = 'openai'
                except Exception as e:
                    logger.warning(f"IndexTTS-2 Gradio服务初始化失败: {str(e)}，使用OpenAI TTS")
                    self.tts_engine = 'openai'

        elif self.tts_engine.lower() == 'indextts2':
            if not self.indextts_service:
                try:
                    from .indextts_service import IndexTTSService
                    self.indextts_service = IndexTTSService()

                    # 检查模型是否可用
                    if await self.indextts_service.initialize_model():
                        logger.info("使用IndexTTS2本地引擎")
                        return self.indextts_service
                    else:
                        logger.warning("IndexTTS2本地引擎不可用，回退到OpenAI TTS")
                        self.tts_engine = 'openai'
                except ImportError:
                    logger.warning("IndexTTS2未安装，使用OpenAI TTS")
                    self.tts_engine = 'openai'

        # 默认使用OpenAI TTS
        if not self.openai_service:
            self.openai_service = OpenAITTSService()
            logger.info("使用OpenAI TTS引擎")

        return self.openai_service

    async def synthesize_script_audio(self, script: PodcastScript, characters: List[CharacterRole], task_id: str,
                                     atmosphere: str = "轻松幽默", enable_effects: bool = True, enable_bgm: bool = True) -> str:
        """合成完整播客音频（带自动回退机制）"""

        # 尝试获取TTS服务
        service = await self.get_tts_service()
        service_name = service.__class__.__name__

        try:
            logger.info(f"尝试使用 {service_name} 合成播客音频")

            # 检查服务是否支持高级音效
            if hasattr(service, 'synthesize_script_audio') and len(service.synthesize_script_audio.__code__.co_varnames) > 4:
                # 支持高级参数的服务（IndexTTS系列）
                return await service.synthesize_script_audio(script, characters, task_id, atmosphere, enable_effects, enable_bgm)
            else:
                # OpenAI TTS服务，使用基础功能
                return await service.synthesize_script_audio(script, characters, task_id, atmosphere, enable_effects, enable_bgm)

        except Exception as e:
            logger.error(f"{service_name} 音频合成失败: {str(e)}")

            # 如果不是OpenAI TTS，尝试回退到OpenAI TTS
            if service_name != "OpenAITTSService":
                logger.info("回退到 OpenAI TTS 服务")
                try:
                    self.openai_service = OpenAITTSService()
                    return await self.openai_service.synthesize_script_audio(script, characters, task_id, atmosphere, enable_effects, enable_bgm)
                except Exception as openai_error:
                    logger.error(f"OpenAI TTS 也失败了: {str(openai_error)}")
                    # 最后回退：生成占位符音频
                    return await self._create_fallback_audio(script, task_id)
            else:
                # 如果OpenAI TTS也失败，生成占位符音频
                logger.info("回退到占位符音频生成")
                return await self._create_fallback_audio(script, task_id)

    async def _create_fallback_audio(self, script: PodcastScript, task_id: str) -> str:
        """创建回退音频（占位符）"""
        try:
            from pydub import AudioSegment
            from pydub.generators import Sine

            logger.info(f"开始生成回退音频，对话数量: {len(script.dialogues)}")

            # 创建任务目录
            task_dir = os.path.join(settings.audio_output_dir, task_id)
            os.makedirs(task_dir, exist_ok=True)

            # 为每段对话生成占位符音频
            audio_segments = []

            for i, dialogue in enumerate(script.dialogues):
                # 根据内容长度计算音频时长
                text_length = len(dialogue.content)
                duration_ms = max(text_length * 200, 1000)  # 每个字200ms，最少1秒

                # 生成提示音 + 静音
                tone = Sine(440).to_audio_segment(duration=300)  # 300ms提示音
                silence = AudioSegment.silent(duration=duration_ms - 300)
                segment_audio = tone + silence

                # 添加淡入淡出
                segment_audio = segment_audio.fade_in(50).fade_out(50) - 15

                # 添加片段间的停顿
                if i > 0:
                    pause = AudioSegment.silent(duration=800)
                    audio_segments.append(pause)

                audio_segments.append(segment_audio)
                logger.info(f"生成第 {i+1} 段占位符音频 (时长: {duration_ms}ms)")

            # 合并所有音频片段
            combined_audio = audio_segments[0]
            for segment in audio_segments[1:]:
                combined_audio += segment

            # 导出最终音频
            final_path = os.path.join(task_dir, f"podcast_{task_id}.mp3")
            combined_audio.export(final_path, format="mp3", bitrate="128k")

            total_duration = len(combined_audio) // 1000
            logger.info(f"回退音频生成完成: {final_path} (总时长: {total_duration}秒)")

            return final_path

        except Exception as e:
            logger.error(f"生成回退音频失败: {str(e)}")
            raise Exception(f"所有TTS方案都失败了: {str(e)}")

    def get_audio_duration(self, audio_path: str) -> int:
        """获取音频时长（秒）"""
        try:
            audio = AudioSegment.from_file(audio_path)
            return len(audio) // 1000  # 转换为秒
        except:
            return 0

    async def switch_engine(self, engine: str) -> bool:
        """切换TTS引擎"""
        if engine.lower() in ['qwen3_tts', 'chatterbox', 'nihal_tts', 'indextts2', 'indextts2_gradio', 'openai']:
            self.tts_engine = engine.lower()
            logger.info(f"TTS引擎切换为: {engine}")
            return True
        return False

    async def get_engine_status(self) -> Dict[str, any]:
        """获取当前引擎状态"""
        service = await self.get_tts_service()

        status_info = {
            "current_engine": self.tts_engine,
            "service_type": service.__class__.__name__
        }

        # 如果是IndexTTS-2 Gradio服务，获取详细状态
        if hasattr(service, 'health_check'):
            health = await service.health_check()
            status_info.update(health)

        return status_info