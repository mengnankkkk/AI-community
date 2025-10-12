"""
阿里云百炼 CosyVoice 语音合成服务
支持流式输入输出，高质量语音生成
"""

import asyncio
import os
import logging
import tempfile
from typing import List, Dict, Optional
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

        # 模型配置
        self.model = getattr(settings, 'cosyvoice_model', 'cosyvoice-v2')
        self.default_voice = getattr(settings, 'cosyvoice_default_voice', 'longxiaochun_v2')

        # 角色音色映射（CosyVoice音色）
        self.character_voice_mapping = {
            # 中文描述关键词映射
            "沉稳": "longwan_v2",
            "浑厚": "longyuan_v2",
            "男中音": "longwan_v2",
            "清脆": "longxiaochun_v2",
            "有活力": "longxiaoyuan_v2",
            "女声": "longxiaochun_v2",
            "标准": "longwan_v2",
            "有磁性": "longyuan_v2",
            "男声": "longwan_v2",
            "温暖": "longxiaoxia_v2",
            "知性": "longxiaochun_v2",

            # 角色名映射
            "主持人": "longwan_v2",
            "嘉宾": "longxiaoxia_v2",
            "博士": "longyuan_v2",
            "教授": "longwan_v2",
            "经理": "longxiaochun_v2",
            "专家": "longyuan_v2",

            # NihalGazi TTS 完整音色映射（13种预设音色）
            # 男声系列
            "alloy": "longwan_v2",              # 合金 - 标准中性男声
            "echo": "longyuan_v2",              # 回声 - 磁性浑厚男声
            "fable": "longwan_v2",              # 寓言 - 叙述温和男声
            "onyx": "longyuan_v2",              # 玛瑙 - 沉稳专业男声
            "ash": "longyuan_v2",               # 灰烬 - 成熟低沉男声
            "sage": "longwan_v2",               # 智者 - 智慧知性男声

            # 女声系列
            "nova": "longxiaochun_v2",          # 新星 - 清晰明亮女声
            "shimmer": "longxiaoyuan_v2",       # 闪光 - 活力年轻女声
            "coral": "longxiaoxia_v2",          # 珊瑚 - 温暖亲切女声
            "verse": "longxiaoyuan_v2",         # 诗句 - 优雅抒情女声
            "ballad": "longxiaoxia_v2",         # 民谣 - 柔美歌唱女声

            # 特色系列
            "amuch": "longwan_v2",              # 阿穆奇 - 独特特色
            "dan": "longyuan_v2",               # 丹 - 多变个性

            # voice_XX 数字ID映射（与上述音色对应）
            "voice_01": "longwan_v2",           # alloy - 标准男声
            "voice_02": "longyuan_v2",          # echo - 磁性男声
            "voice_03": "longwan_v2",           # fable - 温和男声
            "voice_04": "longyuan_v2",          # onyx - 浑厚男声
            "voice_05": "longyuan_v2",          # ash - 沉稳男声
            "voice_06": "longwan_v2",           # sage - 智者男声
            "voice_07": "longxiaochun_v2",      # nova - 清晰女声
            "voice_08": "longxiaoyuan_v2",      # shimmer - 活力女声
            "voice_09": "longxiaoxia_v2",       # coral - 温暖女声
            "voice_10": "longxiaoyuan_v2",      # verse - 优雅女声
            "voice_11": "longxiaoxia_v2",       # ballad - 柔美女声
            "voice_12": "longwan_v2",           # amuch - 特色
            "voice_13": "longyuan_v2",          # dan - 特色
        }

        # 常用CosyVoice音色列表
        self.available_voices = [
            "longwan_v2",           # 男声-标准
            "longyuan_v2",          # 男声-浑厚
            "longxiaochun_v2",      # 女声-标准
            "longxiaoxia_v2",       # 女声-温暖
            "longxiaoyuan_v2",      # 女声-活力
        ]

    def get_voice_for_character(self, voice_description: str) -> str:
        """根据音色描述选择合适的CosyVoice音色"""
        if not voice_description:
            return self.default_voice

        voice_description_lower = voice_description.lower()

        # 检查是否已经是有效的音色ID
        if voice_description in self.available_voices:
            logger.info(f"直接使用音色ID: {voice_description}")
            return voice_description

        # 关键词映射
        for keyword, voice in self.character_voice_mapping.items():
            if keyword.lower() in voice_description_lower:
                logger.info(f"音色映射: {voice_description} -> {voice}")
                return voice

        # 默认返回标准音色
        logger.warning(f"未匹配到音色关键词: {voice_description}，使用默认音色")
        return self.default_voice

    async def synthesize_single_audio(self, text: str, voice: str, output_path: str) -> bool:
        """合成单个音频片段"""
        try:
            # 清理文本
            cleaned_text = clean_for_tts(text, emotion=None)

            if cleaned_text != text:
                logger.info(f"文本清理: [{text[:50]}...] -> [{cleaned_text[:50]}...]")

            # 使用SpeechSynthesizer合成语音
            synthesizer = SpeechSynthesizer(
                model=self.model,
                voice=voice
            )

            # 调用合成
            audio_data = synthesizer.call(cleaned_text)

            # 记录首包延迟（用于性能监控）
            logger.info(f'[Metric] requestId: {synthesizer.get_last_request_id()}, '
                       f'首包延迟: {synthesizer.get_first_package_delay()}ms')

            # 保存音频（直接保存为二进制数据，不需要ffmpeg）
            with open(output_path, 'wb') as f:
                f.write(audio_data)

            logger.info(f"✅ CosyVoice音频合成成功: {output_path}")
            return True

        except Exception as e:
            logger.error(f"❌ CosyVoice音频合成失败: {str(e)}")
            logger.error(f"错误详情: {repr(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return False

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
            # CosyVoice 返回 WAV 格式，先保存为 WAV
            output_path = os.path.join(task_dir, f"segment_{i:03d}.wav")

            try:
                success = await self.synthesize_single_audio(
                    text=dialogue.content,
                    voice=voice,
                    output_path=output_path
                )

                if success and os.path.exists(output_path):
                    # 加载音频片段（WAV格式不需要ffmpeg）
                    segment = AudioSegment.from_wav(output_path)
                    audio_segments.append(segment)
                    logger.info(f"成功合成片段 {i+1}/{len(script.dialogues)}")

                    # 清理临时文件
                    try:
                        os.remove(output_path)
                    except:
                        pass
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
        combined.export(final_path, format="mp3", bitrate="192k")

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
