import os
import random
from typing import List, Dict, Optional, Tuple
from pydub import AudioSegment
from pydub.effects import normalize, compress_dynamic_range
import logging

logger = logging.getLogger(__name__)

class AudioEffectsService:
    """音效和BGM处理服务"""

    def __init__(self):
        self.effects_dir = "audio_effects"
        self.bgm_dir = "background_music"

        # 创建音效目录
        os.makedirs(self.effects_dir, exist_ok=True)
        os.makedirs(self.bgm_dir, exist_ok=True)

        # 音效库映射
        self.effect_mapping = {
            # 基础音效
            "笑声": ["laugh_light.wav", "laugh_warm.wav", "chuckle.wav"],
            "思考": ["hmm_thinking.wav", "um_pause.wav", "thoughtful_pause.wav"],
            "惊讶": ["oh_surprised.wav", "wow_amazed.wav"],
            "赞同": ["yes_agree.wav", "mhm_agree.wav"],
            "停顿": ["natural_pause.wav", "breath_pause.wav"],

            # 情感音效
            "温暖": ["warm_ambient.wav"],
            "激动": ["excited_energy.wav"],
            "严肃": ["serious_tone.wav"],
            "轻松": ["relaxed_ambient.wav"],

            # 转场音效
            "话题转换": ["topic_transition.wav", "smooth_transition.wav"],
            "段落间隔": ["section_break.wav"],
            "开场": ["intro_flourish.wav"],
            "结尾": ["outro_fade.wav"]
        }

        # BGM氛围映射
        self.bgm_mapping = {
            "轻松幽默": ["upbeat_casual.mp3", "light_comedy.mp3"],
            "严肃深入": ["contemplative.mp3", "deep_discussion.mp3"],
            "激烈辩论": ["tension_debate.mp3", "energetic_discussion.mp3"],
            "温暖治愈": ["warm_ambient.mp3", "peaceful_background.mp3"],
            "学术讨论": ["intellectual_bg.mp3", "scholarly_ambient.mp3"],
            "商业讨论": ["professional_bg.mp3", "corporate_ambient.mp3"]
        }

        # 音效插入规则
        self.effect_rules = {
            # 基于内容关键词的音效
            "content_triggers": {
                "哈哈": "笑声",
                "呵呵": "笑声",
                "(笑)": "笑声",
                "(笑声)": "笑声",
                "嗯": "思考",
                "这个": "思考",
                "让我想想": "思考",
                "哇": "惊讶",
                "天哪": "惊讶",
                "是的": "赞同",
                "没错": "赞同",
                "确实": "赞同"
            },

            # 基于位置的音效
            "position_triggers": {
                "opening": "开场",
                "closing": "结尾",
                "topic_change": "话题转换"
            }
        }

    def get_effect_file(self, effect_type: str) -> Optional[str]:
        """获取音效文件路径"""
        if effect_type not in self.effect_mapping:
            return None

        effect_files = self.effect_mapping[effect_type]
        for effect_file in effect_files:
            effect_path = os.path.join(self.effects_dir, effect_file)
            if os.path.exists(effect_path):
                return effect_path

        logger.warning(f"音效文件不存在: {effect_type}")
        return None

    def get_bgm_file(self, atmosphere: str) -> Optional[str]:
        """获取BGM文件路径"""
        atmosphere_key = atmosphere.replace("_", "")

        if atmosphere_key not in self.bgm_mapping:
            # 尝试模糊匹配
            for key in self.bgm_mapping.keys():
                if any(word in atmosphere for word in key.split()):
                    atmosphere_key = key
                    break

        if atmosphere_key in self.bgm_mapping:
            bgm_files = self.bgm_mapping[atmosphere_key]
            for bgm_file in bgm_files:
                bgm_path = os.path.join(self.bgm_dir, bgm_file)
                if os.path.exists(bgm_path):
                    return bgm_path

        logger.warning(f"BGM文件不存在: {atmosphere}")
        return None

    def analyze_dialogue_for_effects(self, content: str, emotion: str = None, position: str = None) -> List[str]:
        """分析对话内容，确定需要的音效"""
        effects = []

        # 基于内容的音效检测
        content_lower = content.lower()
        for trigger, effect_type in self.effect_rules["content_triggers"].items():
            if trigger in content_lower or trigger in content:
                effects.append(effect_type)

        # 基于情感的音效
        if emotion:
            if emotion in ["开心", "愉快"]:
                if random.random() < 0.3:  # 30%概率添加轻松音效
                    effects.append("笑声")
            elif emotion in ["思考", "沉思"]:
                if random.random() < 0.4:
                    effects.append("思考")
            elif emotion in ["惊讶"]:
                effects.append("惊讶")

        # 基于位置的音效
        if position in self.effect_rules["position_triggers"]:
            effects.append(self.effect_rules["position_triggers"][position])

        return list(set(effects))  # 去重

    def add_effects_to_segment(self, audio_segment: AudioSegment, effects: List[str]) -> AudioSegment:
        """为音频片段添加音效"""
        if not effects:
            return audio_segment

        result = audio_segment

        for effect_type in effects:
            effect_path = self.get_effect_file(effect_type)
            if not effect_path:
                continue

            try:
                effect_audio = AudioSegment.from_file(effect_path)

                # 根据音效类型选择混合方式
                if effect_type in ["笑声", "思考", "惊讶", "赞同"]:
                    # 在语音结束后添加
                    result = result + AudioSegment.silent(duration=200) + effect_audio.apply_gain(-10)

                elif effect_type in ["温暖", "激动", "严肃", "轻松"]:
                    # 作为背景混合
                    if len(effect_audio) < len(result):
                        effect_audio = effect_audio * (len(result) // len(effect_audio) + 1)
                    effect_audio = effect_audio[:len(result)].apply_gain(-20)  # 降低音量
                    result = result.overlay(effect_audio)

                elif effect_type in ["开场", "结尾", "话题转换"]:
                    # 作为转场音效，在前面添加
                    transition_effect = effect_audio.apply_gain(-8)
                    result = transition_effect + AudioSegment.silent(duration=300) + result

            except Exception as e:
                logger.error(f"添加音效失败 {effect_type}: {str(e)}")
                continue

        return result

    def add_background_music(self, audio: AudioSegment, atmosphere: str,
                           fade_in_duration: int = 2000, fade_out_duration: int = 2000) -> AudioSegment:
        """为音频添加背景音乐"""
        bgm_path = self.get_bgm_file(atmosphere)
        if not bgm_path:
            logger.warning(f"未找到合适的BGM: {atmosphere}")
            return audio

        try:
            bgm = AudioSegment.from_file(bgm_path)

            # 调整BGM长度以匹配音频
            audio_duration = len(audio)
            if len(bgm) < audio_duration:
                # BGM太短，循环播放
                loops_needed = (audio_duration // len(bgm)) + 1
                bgm = bgm * loops_needed

            # 裁剪BGM到合适长度
            bgm = bgm[:audio_duration]

            # 应用淡入淡出效果
            bgm = bgm.fade_in(fade_in_duration).fade_out(fade_out_duration)

            # 降低BGM音量，确保不影响语音
            bgm_volume = self._calculate_bgm_volume(atmosphere)
            bgm = bgm.apply_gain(bgm_volume)

            # 混合音频和BGM
            result = audio.overlay(bgm)

            logger.info(f"成功添加BGM: {atmosphere}")
            return result

        except Exception as e:
            logger.error(f"添加BGM失败: {str(e)}")
            return audio

    def _calculate_bgm_volume(self, atmosphere: str) -> float:
        """根据氛围计算BGM音量（dB）"""
        volume_mapping = {
            "轻松幽默": -18,    # 相对较响，营造轻松氛围
            "严肃深入": -25,    # 较轻，不干扰思考
            "激烈辩论": -22,    # 中等，保持能量感
            "温暖治愈": -20,    # 温和舒适
            "学术讨论": -28,    # 很轻，突出对话
            "商业讨论": -24     # 专业但不过分
        }

        return volume_mapping.get(atmosphere, -22)  # 默认-22dB

    def create_intro_outro(self, intro_text: str = None, outro_text: str = None,
                          atmosphere: str = "轻松幽默") -> Tuple[Optional[AudioSegment], Optional[AudioSegment]]:
        """创建开场和结尾音效"""
        intro_audio = None
        outro_audio = None

        # 创建开场音效
        intro_effect_path = self.get_effect_file("开场")
        if intro_effect_path:
            intro_audio = AudioSegment.from_file(intro_effect_path)
            # 添加适当的静音间隔
            intro_audio = intro_audio + AudioSegment.silent(duration=1000)

        # 创建结尾音效
        outro_effect_path = self.get_effect_file("结尾")
        if outro_effect_path:
            outro_audio = AudioSegment.silent(duration=500) + AudioSegment.from_file(outro_effect_path)

        return intro_audio, outro_audio

    def apply_professional_mastering(self, audio: AudioSegment) -> AudioSegment:
        """应用专业级母带处理"""
        try:
            # 1. 标准化音量
            audio = normalize(audio)

            # 2. 动态范围压缩
            audio = compress_dynamic_range(audio, threshold=-20.0, ratio=3.0, attack=5.0, release=50.0)

            # 3. 轻微EQ调整（模拟）
            # 注意：pydub的EQ功能有限，这里用音量调整模拟

            # 4. 最终限制器（防止过载）
            audio = audio.apply_gain(-1.0)  # 轻微降低整体音量

            # 5. 添加轻微的混响效果（如果需要）
            # 这里可以添加更复杂的音频处理

            logger.info("完成专业级母带处理")
            return audio

        except Exception as e:
            logger.error(f"母带处理失败: {str(e)}")
            return audio

    def generate_silence_with_ambience(self, duration: int, atmosphere: str = "neutral") -> AudioSegment:
        """生成带有环境音的静音"""
        base_silence = AudioSegment.silent(duration=duration)

        # 可以添加轻微的环境音
        # 比如办公室环境音、咖啡厅氛围等
        ambience_files = {
            "office": "office_ambient.wav",
            "cafe": "cafe_ambient.wav",
            "studio": "studio_ambient.wav"
        }

        if atmosphere in ambience_files:
            ambience_path = os.path.join(self.effects_dir, ambience_files[atmosphere])
            if os.path.exists(ambience_path):
                try:
                    ambience = AudioSegment.from_file(ambience_path)
                    if len(ambience) > duration:
                        ambience = ambience[:duration]
                    else:
                        ambience = ambience * (duration // len(ambience) + 1)
                        ambience = ambience[:duration]

                    ambience = ambience.apply_gain(-30)  # 非常轻的环境音
                    return base_silence.overlay(ambience)
                except:
                    pass

        return base_silence