import asyncio
import os
import logging
from typing import List, Dict, Optional
from pydub import AudioSegment
from ..models.podcast import PodcastScript, CharacterRole, ScriptDialogue
from ..core.config import settings
from .audio_effects_service import AudioEffectsService
from ..utils.text_cleaner import clean_for_tts

# 设置日志
logger = logging.getLogger(__name__)

class IndexTTSService:
    """IndexTTS2 语音合成服务"""

    def __init__(self):
        self.tts_model = None
        self.model_loaded = False
        self.voice_samples_dir = "voice_samples"  # 音色样本目录
        self.emotion_samples_dir = "emotion_samples"  # 情感样本目录

        # 初始化音效服务
        self.audio_effects = AudioEffectsService()

        # 创建必要目录
        os.makedirs(self.voice_samples_dir, exist_ok=True)
        os.makedirs(self.emotion_samples_dir, exist_ok=True)

        # 角色音色映射配置
        self.character_voice_mapping = {
            "沉稳": "voice_steady.wav",
            "浑厚": "voice_deep.wav",
            "男中音": "voice_baritone.wav",
            "清脆": "voice_crisp.wav",
            "有活力": "voice_energetic.wav",
            "女声": "voice_female.wav",
            "标准": "voice_standard.wav",
            "有磁性": "voice_magnetic.wav",
            "男声": "voice_male.wav",
            "温暖": "voice_warm.wav",
            "知性": "voice_intellectual.wav"
        }

        # 情感样本映射
        self.emotion_mapping = {
            "开心": "emo_happy.wav",
            "悲伤": "emo_sad.wav",
            "激动": "emo_excited.wav",
            "平静": "emo_calm.wav",
            "愤怒": "emo_angry.wav",
            "惊讶": "emo_surprised.wav",
            "温暖": "emo_warm.wav",
            "严肃": "emo_serious.wav",
            "幽默": "emo_humorous.wav",
            "思考": "emo_thoughtful.wav"
        }

    async def initialize_model(self):
        """初始化 IndexTTS2 模型（支持本地模型路径）"""
        if self.model_loaded:
            return

        try:
            # 【关键】设置HuggingFace离线模式，强制使用本地缓存
            os.environ['HF_HUB_OFFLINE'] = '1'
            os.environ['TRANSFORMERS_OFFLINE'] = '1'
            logger.info("[IndexTTS-2] 已启用HuggingFace离线模式，将使用本地缓存")

            # 动态导入，避免在没有安装时报错
            from indextts.infer_v2 import IndexTTS2

            # 从配置中读取模型目录（支持绝对路径和相对路径）
            model_dir = settings.indextts_model_dir

            # 处理路径（支持Windows和Unix风格路径）
            model_dir = os.path.normpath(model_dir)
            config_path = os.path.join(model_dir, "config.yaml")

            logger.info(f"[IndexTTS-2] 尝试加载模型: {model_dir}")
            logger.info(f"[IndexTTS-2] 配置文件路径: {config_path}")

            if not os.path.exists(config_path):
                logger.error(f"[IndexTTS-2] 配置文件未找到: {config_path}")
                logger.error(f"[IndexTTS-2] 请确保模型已下载到: {model_dir}")
                return False

            # 检查关键模型文件
            required_files = ["gpt.pth", "s2mel.pth", "bpe.model"]
            missing_files = []
            for file in required_files:
                file_path = os.path.join(model_dir, file)
                if not os.path.exists(file_path):
                    missing_files.append(file)

            if missing_files:
                logger.error(f"[IndexTTS-2] 缺少必需的模型文件: {', '.join(missing_files)}")
                return False

            logger.info(f"[IndexTTS-2] 所有必需文件已找到")
            logger.info(f"[IndexTTS-2] 初始化参数:")
            logger.info(f"  - FP16: {settings.indextts_use_fp16}")
            logger.info(f"  - CUDA Kernel: {settings.indextts_use_cuda_kernel}")

            self.tts_model = IndexTTS2(
                cfg_path=config_path,
                model_dir=model_dir,
                use_fp16=settings.indextts_use_fp16,  # 正确的参数名
                use_cuda_kernel=settings.indextts_use_cuda_kernel
            )

            self.model_loaded = True
            logger.info("[IndexTTS-2] 模型初始化成功！")
            return True

        except ImportError as e:
            logger.error(f"[IndexTTS-2] 包未安装: {str(e)}")
            logger.error("[IndexTTS-2] 请安装 indextts 包: pip install indextts")
            return False
        except Exception as e:
            logger.error(f"[IndexTTS-2] 模型初始化失败: {str(e)}")
            import traceback
            logger.error(f"[IndexTTS-2] 详细错误:\n{traceback.format_exc()}")
            return False

    def get_voice_sample_path(self, voice_description: str) -> str:
        """根据音色描述获取音色样本路径"""
        voice_description = voice_description.lower()

        # 匹配关键词
        for keyword, sample_file in self.character_voice_mapping.items():
            if keyword in voice_description:
                sample_path = os.path.join(self.voice_samples_dir, sample_file)
                if os.path.exists(sample_path):
                    return sample_path

        # 默认音色样本
        default_path = os.path.join(self.voice_samples_dir, "voice_standard.wav")
        if os.path.exists(default_path):
            return default_path

        logger.warning(f"未找到合适的音色样本: {voice_description}")
        return None

    def get_emotion_sample_path(self, emotion: str) -> Optional[str]:
        """根据情感获取情感样本路径"""
        if not emotion:
            return None

        emotion_file = self.emotion_mapping.get(emotion)
        if emotion_file:
            emotion_path = os.path.join(self.emotion_samples_dir, emotion_file)
            if os.path.exists(emotion_path):
                return emotion_path

        logger.warning(f"未找到情感样本: {emotion}")
        return None

    async def synthesize_single_audio(self, text: str, voice_sample_path: str,
                                    emotion_sample_path: Optional[str],
                                    output_path: str, target_duration: Optional[float] = None) -> bool:
        """合成单个音频片段"""
        if not await self.initialize_model():
            return False

        try:
            # 【重要】清理文本 - 移除舞台指示和命令提示
            cleaned_text = clean_for_tts(text, emotion=None)

            # 记录清理前后的差异（便于调试）
            if cleaned_text != text:
                logger.info(f"文本清理: [{text[:50]}...] -> [{cleaned_text[:50]}...]")

            # 准备合成参数
            infer_params = {
                'spk_audio_prompt': voice_sample_path,
                'text': cleaned_text,  # 使用清理后的文本
                'output_path': output_path,
                'verbose': False
            }

            # 添加情感控制
            if emotion_sample_path:
                infer_params['emo_audio_prompt'] = emotion_sample_path

            # 添加时长控制
            if target_duration:
                infer_params['use_speed'] = True
                infer_params['target_dur'] = target_duration

            # 执行合成
            self.tts_model.infer(**infer_params)

            return os.path.exists(output_path)

        except Exception as e:
            logger.error(f"音频合成失败 {output_path}: {str(e)}")
            return False

    async def synthesize_script_audio(self, script: PodcastScript, characters: List[CharacterRole], task_id: str,
                                     atmosphere: str = "轻松幽默", enable_effects: bool = True, enable_bgm: bool = True) -> str:
        """合成完整播客音频（带音效和BGM）"""
        if not await self.initialize_model():
            raise Exception("IndexTTS2模型初始化失败")

        # 创建任务专用目录
        task_dir = os.path.join(settings.audio_output_dir, task_id)
        os.makedirs(task_dir, exist_ok=True)

        # 为每个角色映射音色样本
        character_voice_samples = {}
        for char in characters:
            voice_sample_path = self.get_voice_sample_path(char.voice_description)
            if voice_sample_path:
                character_voice_samples[char.name] = voice_sample_path
            else:
                logger.warning(f"角色 {char.name} 缺少音色样本")

        # 合成每个对话片段
        audio_segments = []

        for i, dialogue in enumerate(script.dialogues):
            voice_sample_path = character_voice_samples.get(dialogue.character_name)
            if not voice_sample_path:
                logger.warning(f"跳过角色 {dialogue.character_name} - 无音色样本")
                continue

            emotion_sample_path = self.get_emotion_sample_path(dialogue.emotion)
            output_path = os.path.join(task_dir, f"segment_{i:03d}.wav")

            # 合成基础音频
            success = await self.synthesize_single_audio(
                text=dialogue.content,
                voice_sample_path=voice_sample_path,
                emotion_sample_path=emotion_sample_path,
                output_path=output_path
            )

            if success:
                # 加载生成的音频
                segment = AudioSegment.from_wav(output_path)

                # 添加音效处理
                if enable_effects:
                    # 分析对话确定位置
                    position = None
                    if i == 0:
                        position = "opening"
                    elif i == len(script.dialogues) - 1:
                        position = "closing"

                    # 分析需要的音效
                    effects = self.audio_effects.analyze_dialogue_for_effects(
                        content=dialogue.content,
                        emotion=dialogue.emotion,
                        position=position
                    )

                    # 应用音效
                    segment = self.audio_effects.add_effects_to_segment(segment, effects)

                audio_segments.append(segment)
                logger.info(f"成功合成片段 {i}: {dialogue.character_name}")

                # 清理临时文件
                try:
                    os.remove(output_path)
                except:
                    pass
            else:
                logger.error(f"片段合成失败 {i}: {dialogue.character_name}")

        if not audio_segments:
            raise Exception("所有音频片段合成失败")

        # 拼接音频并应用高级处理
        final_audio = await self.concatenate_audio_with_advanced_effects(
            audio_segments, task_dir, task_id, atmosphere, enable_bgm
        )

        return final_audio

    async def concatenate_audio_with_effects(self, audio_files: List[str], task_dir: str, task_id: str) -> str:
        """拼接音频文件并添加效果"""
        try:
            # 加载第一个音频文件
            combined = AudioSegment.from_wav(audio_files[0])

            # 依次拼接其他音频文件
            for i, audio_file in enumerate(audio_files[1:]):
                if os.path.exists(audio_file):
                    segment = AudioSegment.from_wav(audio_file)

                    # 智能停顿时长：根据上下文调整
                    pause_duration = self._calculate_pause_duration(i)
                    pause = AudioSegment.silent(duration=pause_duration)

                    combined = combined + pause + segment

            # 应用音频后处理
            combined = self._apply_audio_processing(combined)

            # 保存最终音频
            final_path = os.path.join(task_dir, f"podcast_{task_id}.mp3")
            combined.export(final_path, format="mp3", bitrate="128k")

            return final_path

        except Exception as e:
            logger.error(f"音频拼接失败: {str(e)}")
            raise Exception(f"音频拼接失败: {str(e)}")

    def _calculate_pause_duration(self, segment_index: int) -> int:
        """计算智能停顿时长"""
        # 基础停顿：500ms
        base_pause = 500

        # 每5个片段增加一个长停顿（模拟段落间隔）
        if segment_index % 5 == 0:
            return base_pause + 300

        return base_pause

    def _apply_audio_processing(self, audio: AudioSegment) -> AudioSegment:
        """应用音频后处理"""
        # 标准化音量
        audio = audio.normalize()

        # 轻微压缩动态范围
        audio = audio.compress_dynamic_range(threshold=-20.0, ratio=2.0)

        # 添加轻微的淡入淡出
        fade_duration = 100  # 100ms
        audio = audio.fade_in(fade_duration).fade_out(fade_duration)

        return audio

    def get_audio_duration(self, audio_path: str) -> int:
        """获取音频时长（秒）"""
        try:
            audio = AudioSegment.from_file(audio_path)
            return len(audio) // 1000  # 转换为秒
        except:
            return 0

    async def create_voice_sample(self, character_name: str, voice_description: str,
                                sample_text: str = "你好，我是播客角色，这是我的声音样本。") -> str:
        """为角色创建音色样本（如果有现有音频的话）"""
        # 这个方法可以用于从现有音频中提取特定角色的音色样本
        # 实际实现需要根据具体需求调整
        sample_path = os.path.join(self.voice_samples_dir, f"{character_name}_sample.wav")

        # 这里可以实现音色样本的创建逻辑
        # 比如从用户上传的音频中提取，或使用预设样本

        return sample_path

    async def concatenate_audio_with_advanced_effects(self, audio_segments: List[AudioSegment],
                                                     task_dir: str, task_id: str, atmosphere: str,
                                                     enable_bgm: bool = True) -> str:
        """拼接音频片段并应用高级音效处理"""
        try:
            # 生成开场和结尾音效
            intro_audio, outro_audio = self.audio_effects.create_intro_outro(atmosphere=atmosphere)

            # 开始拼接
            combined = AudioSegment.empty()

            # 添加开场音效（如果存在）
            if intro_audio:
                combined += intro_audio

            # 拼接主要内容
            for i, segment in enumerate(audio_segments):
                # 智能停顿时长：根据上下文调整
                if i > 0:  # 不在第一个片段前添加停顿
                    pause_duration = self._calculate_smart_pause_duration(i, len(audio_segments))
                    pause = self.audio_effects.generate_silence_with_ambience(
                        duration=pause_duration,
                        atmosphere="studio"
                    )
                    combined += pause

                combined += segment

            # 添加结尾音效（如果存在）
            if outro_audio:
                combined += outro_audio

            # 应用专业级后处理
            combined = self.audio_effects.apply_professional_mastering(combined)

            # 添加背景音乐
            if enable_bgm:
                combined = self.audio_effects.add_background_music(
                    audio=combined,
                    atmosphere=atmosphere,
                    fade_in_duration=3000,
                    fade_out_duration=3000
                )

            # 保存最终音频
            final_path = os.path.join(task_dir, f"podcast_{task_id}.mp3")
            combined.export(final_path, format="mp3", bitrate="192k")

            logger.info(f"完成高级音效处理，输出: {final_path}")
            return final_path

        except Exception as e:
            logger.error(f"高级音频处理失败: {str(e)}")
            raise Exception(f"高级音频处理失败: {str(e)}")

    def _calculate_smart_pause_duration(self, segment_index: int, total_segments: int) -> int:
        """计算智能停顿时长"""
        # 基础停顿：800ms
        base_pause = 800

        # 话题转换检测（每5个片段一个长停顿）
        if segment_index % 5 == 0:
            return base_pause + 500  # 1.3秒

        # 段落间隔（每3个片段一个中等停顿）
        if segment_index % 3 == 0:
            return base_pause + 200  # 1秒

        # 结尾前的停顿
        if segment_index == total_segments - 2:
            return base_pause + 300

        return base_pause