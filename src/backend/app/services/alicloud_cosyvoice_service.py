"""
阿里云百炼 CosyVoice 语音合成服务
支持流式输入输出，高质量语音生成
"""

import asyncio
import os
import logging
import tempfile
import io
from typing import List, Dict, Optional, Tuple
from pydub import AudioSegment

try:
    import dashscope
    from dashscope.audio.tts_v2 import SpeechSynthesizer
    DASHSCOPE_AVAILABLE = True
except ImportError:
    DASHSCOPE_AVAILABLE = False
    logging.warning("dashscope SDK未安装，CosyVoice服务不可用。请运行: pip install dashscope")

from ..models.podcast import PodcastScript, CharacterRole, ScriptDialogue
from ..core.config import settings
from ..utils.text_cleaner import clean_for_tts
from .voice_resolver_service import voice_resolver

logger = logging.getLogger(__name__)


class AliCloudCosyVoiceService:
    """阿里云百炼 CosyVoice 语音合成服务"""

    def __init__(self):
        if not DASHSCOPE_AVAILABLE:
            raise ImportError("dashscope SDK未安装")

        # 配置API Key
        api_key = getattr(settings, 'alicloud_dashscope_api_key', '')
        if api_key and api_key != 'your_alicloud_api_key_here':
            dashscope.api_key = api_key
        else:
            logger.warning("阿里云API Key未配置，CosyVoice服务不可用")

        # 配置FFmpeg路径（pydub需要）
        self._configure_ffmpeg()

        # 模型配置
        self.model = getattr(settings, 'cosyvoice_model', 'cosyvoice-v1')  # 默认使用v1（更稳定）
        self.default_voice = getattr(settings, 'cosyvoice_default_voice', 'longxiaochun')  # v1音色

        # 根据模型版本确定可用音色
        if 'v2' in self.model or 'v3' in self.model:
            # v2/v3模型：音色ID带_v2/_v3后缀
            self.available_voices = [
                "longwan_v2", "longyuan_v2",
                "longxiaochun_v2", "longxiaoxia_v2", "longxiaoyuan_v2"
            ]
            self.voice_suffix = "_v2"
        else:
            # v1模型：音色ID不带后缀
            # 注意：v1模型支持 longxiaocheng（男声磁性），不支持 longxiaoyuan（女声活力）
            self.available_voices = [
                "longwan", "longyuan",
                "longxiaochun", "longxiaoxia", "longxiaocheng"
            ]
            self.voice_suffix = ""

        logger.info(f"CosyVoice配置: model={self.model}, default_voice={self.default_voice}")
        logger.info(f"可用音色: {self.available_voices}")

    def _configure_ffmpeg(self):
        """配置FFmpeg路径供pydub使用"""
        ffmpeg_path = getattr(settings, 'ffmpeg_path', '')
        ffprobe_path = getattr(settings, 'ffprobe_path', '')

        # 如果配置了路径,设置给pydub
        if ffmpeg_path and os.path.exists(ffmpeg_path):
            # 如果是目录,添加可执行文件名
            if os.path.isdir(ffmpeg_path):
                ffmpeg_exe = os.path.join(ffmpeg_path, 'ffmpeg.exe')
                ffprobe_exe = os.path.join(ffmpeg_path, 'ffprobe.exe')
            else:
                ffmpeg_exe = ffmpeg_path
                ffprobe_exe = ffprobe_path if ffprobe_path else ffmpeg_path.replace('ffmpeg', 'ffprobe')

            # 检查文件是否存在
            if os.path.isfile(ffmpeg_exe):
                AudioSegment.converter = ffmpeg_exe
                logger.info(f"✅ FFmpeg配置: {ffmpeg_exe}")
            else:
                logger.warning(f"⚠️ FFmpeg文件不存在: {ffmpeg_exe}")

            if os.path.isfile(ffprobe_exe):
                AudioSegment.ffprobe = ffprobe_exe
                logger.info(f"✅ FFprobe配置: {ffprobe_exe}")
            else:
                logger.warning(f"⚠️ FFprobe文件不存在: {ffprobe_exe}")
        else:
            logger.warning("⚠️ FFmpeg路径未配置或不存在,将使用系统PATH中的FFmpeg")
            logger.info("提示: 在.env中配置 FFMPEG_PATH 和 FFPROBE_PATH 以使用自定义FFmpeg")

    def get_voice_for_character(self, voice_description: str) -> str:
        """根据音色描述选择合适的CosyVoice音色（使用统一音色解析服务）"""
        if not voice_description:
            logger.warning(f"音色描述为空，使用默认音色: {self.default_voice}")
            return self.default_voice

        # 记录原始输入
        logger.info(f"[音色解析] 原始描述: '{voice_description}'")

        # 使用统一的音色解析服务
        voice_id, voice_file = voice_resolver.resolve_voice(voice_description, "cosyvoice")

        # 记录解析结果
        logger.info(f"[音色解析] 解析结果: voice_id='{voice_id}', voice_file='{voice_file}'")
        logger.info(f"[音色解析] 可用音色列表: {self.available_voices}")

        # CosyVoice只使用音色ID
        if voice_id in self.available_voices:
            logger.info(f"✅ 使用CosyVoice音色: {voice_id}")
            return voice_id

        # 如果解析的音色ID不在可用列表中，使用默认
        logger.error(f"❌ 音色 '{voice_id}' 不是有效的CosyVoice音色！")
        logger.error(f"   原始描述: '{voice_description}'")
        logger.error(f"   解析结果: '{voice_id}'")
        logger.error(f"   可用音色: {self.available_voices}")
        logger.error(f"   → 使用默认音色: {self.default_voice}")
        return self.default_voice

    async def synthesize_single_audio(self, text: str, voice: str) -> Tuple[bool, Optional[bytes]]:
        """合成单个音频片段，返回音频数据"""
        # 清理文本
        cleaned_text = clean_for_tts(text, emotion=None)

        if cleaned_text != text:
            logger.info(f"文本清理: [{text[:50]}...] -> [{cleaned_text[:50]}...]")

        max_retries = 3
        last_error: Optional[Exception] = None

        for attempt in range(1, max_retries + 1):
            try:
                # 记录请求参数，方便排查问题
                logger.info(f"[CosyVoice] 请求参数: model={self.model}, voice={voice}, text_length={len(cleaned_text)}")

                synthesizer = SpeechSynthesizer(
                    model=self.model,
                    voice=voice
                )

                # call为同步阻塞，放入线程池避免阻塞事件循环
                audio_data = await asyncio.to_thread(synthesizer.call, cleaned_text)

                # 检查返回的音频数据是否有效
                if audio_data is None:
                    error_msg = f"CosyVoice返回了None（可能是API错误或参数无效）"
                    logger.error(f"❌ {error_msg}")
                    logger.error(f"   音色: {voice}, 文本: {cleaned_text[:100]}")
                    raise ValueError(error_msg)

                if not isinstance(audio_data, bytes) or len(audio_data) == 0:
                    error_msg = f"CosyVoice返回了无效数据: type={type(audio_data)}, length={len(audio_data) if audio_data else 0}"
                    logger.error(f"❌ {error_msg}")
                    raise ValueError(error_msg)

                logger.info(
                    f'[Metric] requestId: {synthesizer.get_last_request_id()}, '
                    f'首包延迟: {synthesizer.get_first_package_delay()}ms'
                )
                logger.info(f"✅ CosyVoice音频���成成功，数据大小: {len(audio_data)} bytes")
                return True, audio_data

            except Exception as error:  # noqa: BLE001 - 需捕捉SDK内部异常
                last_error = error
                message = str(error)

                # 检查是否是418错误（参数无效）
                if "418" in message or "InvalidParameter" in message:
                    logger.error(f"❌ CosyVoice参数错误 (418): {message}")
                    logger.error(f"   可能的原因:")
                    logger.error(f"   1. 音色ID '{voice}' 不正确或不支持")
                    logger.error(f"   2. 文本内容有问题: {cleaned_text[:100]}")
                    logger.error(f"   3. 模型 '{self.model}' 配置错误")
                    logger.error(f"   建议检查 .env 中的 COSYVOICE_MODEL 和音色配置")
                    # 418错误不重试，直接失败
                    break

                connection_issue = any(
                    keyword in message.lower()
                    for keyword in [
                        "websocket closed",
                        "connection to remote host was lost",
                        "connection reset",
                        "timeout"
                    ]
                )

                if attempt < max_retries and connection_issue:
                    logger.warning(
                        f"⚠️ CosyVoice连接异常，准备重试 {attempt}/{max_retries}: {message}"
                    )
                    await asyncio.sleep(1 * attempt)
                    continue

                logger.error(f"❌ CosyVoice音频合成失败: {message}")
                logger.error(f"错误详情: {repr(error)}")
                import traceback
                logger.error(traceback.format_exc())
                break

        return False, None

    async def synthesize_script_audio(self, script: PodcastScript, characters: List[CharacterRole],
                                     task_id: str, atmosphere: str = "轻松幽默",
                                     enable_effects: bool = True, enable_bgm: bool = True) -> str:
        """合成完整播客音频"""
        logger.info(f"开始使用CosyVoice合成播客音频，共 {len(script.dialogues)} 段对话")

        # 创建任务目录
        task_dir = os.path.join(settings.audio_output_dir, task_id)
        os.makedirs(task_dir, exist_ok=True)

        # 为每个角色映射音色
        character_voices = {}
        for char in characters:
            character_voices[char.name] = self.get_voice_for_character(char.voice_description)
            logger.info(f"角色 {char.name} 使用音色: {character_voices[char.name]}")

        # 合成每个对话片段
        audio_segments = []

        for i, dialogue in enumerate(script.dialogues):
            voice = character_voices.get(dialogue.character_name, self.default_voice)

            try:
                # 合成音频，直接获取音频数据
                success, audio_data = await self.synthesize_single_audio(
                    text=dialogue.content,
                    voice=voice
                )

                if success and audio_data:
                    segment = AudioSegment.from_file(io.BytesIO(audio_data), format="mp3")
                    audio_segments.append(segment)
                    logger.info(f"成功合成片段 {i+1}/{len(script.dialogues)}")
                else:
                    logger.error(f"片段 {i} 合成失败")

            except Exception as e:
                logger.error(f"片段 {i} 合成异常: {str(e)}")
                logger.error(f"错误详情: {repr(e)}")
                import traceback
                logger.error(traceback.format_exc())
                continue

        if not audio_segments:
            raise Exception("所有音频片段合成失败")

        # 拼接音频
        combined = AudioSegment.empty()

        for i, segment in enumerate(audio_segments):
            if i > 0:
                # 添加800ms停顿
                pause = AudioSegment.silent(duration=800)
                combined += pause

            combined += segment

        # 保存最终音频
        final_path = os.path.join(task_dir, f"podcast_{task_id}.mp3")

        try:
            # 尝试导出为MP3（需要FFmpeg）
            combined.export(final_path, format="mp3", bitrate="192k")
            logger.info(f"✅ 音频导出为MP3格式")
        except Exception as e:
            # 如果FFmpeg不可用，回退到WAV格式
            logger.warning(f"MP3导出失败（可能缺少FFmpeg）: {e}")
            logger.info("回退到WAV格式")
            final_path = os.path.join(task_dir, f"podcast_{task_id}.wav")
            combined.export(final_path, format="wav")

        total_duration = len(combined) // 1000
        logger.info(f"✅ CosyVoice播客音频生成完成: {final_path} (时长: {total_duration}秒)")

        return final_path

    def get_audio_duration(self, audio_path: str) -> int:
        """获取音频时长（秒）"""
        try:
            audio = AudioSegment.from_file(audio_path)
            return len(audio) // 1000
        except:
            return 0

    async def health_check(self) -> Dict[str, any]:
        """健康检查"""
        try:
            if not DASHSCOPE_AVAILABLE:
                return {
                    "status": "unavailable",
                    "service": "AliCloud CosyVoice",
                    "error": "dashscope SDK未安装"
                }

            if not dashscope.api_key:
                return {
                    "status": "unconfigured",
                    "service": "AliCloud CosyVoice",
                    "error": "API Key未配置"
                }

            # 测试合成一小段音频
            test_text = "测试"
            synthesizer = SpeechSynthesizer(
                model=self.model,
                voice=self.default_voice
            )

            # 尝试合成
            audio_data = synthesizer.call(test_text)

            if audio_data:
                return {
                    "status": "healthy",
                    "service": "AliCloud CosyVoice",
                    "model": self.model,
                    "default_voice": self.default_voice,
                    "test_audio_size": len(audio_data)
                }
            else:
                return {
                    "status": "error",
                    "service": "AliCloud CosyVoice",
                    "error": "测试合成失败"
                }

        except Exception as e:
            return {
                "status": "error",
                "service": "AliCloud CosyVoice",
                "error": str(e)
            }
