"""
统一音色解析服务
为所有TTS引擎提供统一的音色ID解析和文件路径处理
"""
import os
import logging
from pathlib import Path
from typing import Dict, Optional, Tuple
from ..core.config import settings

logger = logging.getLogger(__name__)


class VoiceResolverService:
    """统一音色解析服务"""

    def __init__(self):
        # CosyVoice官方音色映射（v1和v2通用）
        self.cosyvoice_voices = {
            # v1音色（不带后缀）
            "longwan": "龙湾（男声-标准）",
            "longyuan": "龙渊（男声-浑厚）",
            "longxiaochun": "龙小春（女声-标准）",
            "longxiaoxia": "龙小夏（女声-温暖）",
            "longxiaoyuan": "龙小媛（女声-活力）",
            "longxiaocheng": "龙小诚（男声-磁性）",
            # v2音色（带_v2后缀）
            "longwan_v2": "龙湾（男声-标准）",
            "longyuan_v2": "龙渊（男声-浑厚）",
            "longxiaochun_v2": "龙小春（女声-标准）",
            "longxiaoxia_v2": "龙小夏（女声-温暖）",
            "longxiaoyuan_v2": "龙小媛（女声-活力）"
        }

        # OpenAI TTS音色映射
        self.openai_voices = {
            "alloy": "合金（中性）",
            "echo": "回声（男声-磁性）",
            "fable": "寓言（男声-温暖）",
            "onyx": "黑玛瑙（男声-沉稳）",
            "nova": "新星（女声-活力）",
            "shimmer": "微光（女声-柔和）"
        }

        # Qwen3 TTS音色映射
        self.qwen3_voices = {
            "Cherry / 芊悦": "女声，甜美",
            "Ethan / 晨煦": "男声，标准",
            "Jennifer / 詹妮弗": "女声，英文风格",
            "Ryan / 甜茶": "男声，活力",
            "Katerina / 卡捷琳娜": "女声，知性",
            "Nofish / 不吃鱼": "特色",
            "Elias / 墨讲师": "男声，讲师风格",
            "Li / 南京-老李": "男声，南京口音",
            "Marcus / 陕西-秦川": "男声，陕西口音",
            "Roy / 闽南-阿杰": "男声，闽南口音",
            "Peter / 天津-李彼得": "男声，天津口音",
            "Eric / 四川-程川": "男声，四川口音",
            "Rocky / 粤语-阿强": "男声，粤语",
            "Kiki / 粤语-阿清": "女声，粤语",
            "Sunny / 四川-晴儿": "女声，四川口音",
            "Jada / 上海-阿珍": "女声，上海口音",
            "Dylan / 北京-晓东": "男声，北京口音",
        }

        # Nihal TTS音色映射（使用OpenAI兼容ID）
        self.nihal_voices = {
            "alloy": "标准男声",
            "echo": "磁性男声",
            "fable": "男声",
            "onyx": "沉稳男声",
            "nova": "女声",
            "shimmer": "活力女声",
            "coral": "女声",
            "verse": "女声",
            "ballad": "女声",
            "ash": "男声",
            "sage": "智者男声",
            "amuch": "特色",
            "dan": "特色",
        }

        # 音色特征关键词到各引擎的映射
        self.voice_keyword_mapping = {
            # 男声特征
            "沉稳": {
                "cosyvoice": "longwan",  # v1音色（不带_v2后缀）
                "openai": "onyx",
                "qwen3_tts": "Elias / 墨讲师",
                "nihal_tts": "onyx",
                "default": "male_steady"
            },
            "浑厚": {
                "cosyvoice": "longyuan",  # v1音色（不带_v2后缀）
                "openai": "echo",
                "qwen3_tts": "Marcus / 陕西-秦川",
                "nihal_tts": "echo",
                "default": "male_deep"
            },
            "磁性": {
                "cosyvoice": "longyuan",  # v1音色（不带_v2后缀）
                "openai": "echo",
                "qwen3_tts": "Elias / 墨讲师",
                "nihal_tts": "echo",
                "default": "male_magnetic"
            },
            "男声": {
                "cosyvoice": "longwan",  # v1音色（不带_v2后缀）
                "openai": "fable",
                "qwen3_tts": "Ethan / 晨煦",
                "nihal_tts": "fable",
                "default": "male_standard"
            },
            "男中音": {
                "cosyvoice": "longwan",  # v1音色（不带_v2后缀）
                "openai": "onyx",
                "qwen3_tts": "Ethan / 晨煦",
                "nihal_tts": "alloy",
                "default": "male_baritone"
            },

            # 女声��征
            "清脆": {
                "cosyvoice": "longxiaochun",  # v1音色（不带_v2后缀）
                "openai": "nova",
                "qwen3_tts": "Cherry / 芊悦",
                "nihal_tts": "nova",
                "default": "female_crisp"
            },
            "温暖": {
                "cosyvoice": "longxiaoxia",  # v1音色（不带_v2后缀）
                "openai": "shimmer",
                "qwen3_tts": "Jennifer / 詹妮弗",
                "nihal_tts": "coral",
                "default": "female_warm"
            },
            "活力": {
                "cosyvoice": "longxiaoyuan",  # v1音色（不带_v2后缀）
                "openai": "nova",
                "qwen3_tts": "Cherry / 芊悦",  # 女声甜美（与cosyvoice保持性别一致）
                "nihal_tts": "shimmer",
                "default": "female_energetic"
            },
            "女声": {
                "cosyvoice": "longxiaochun",  # v1音色（不带_v2后缀）
                "openai": "nova",
                "qwen3_tts": "Cherry / 芊悦",
                "nihal_tts": "nova",
                "default": "female_standard"
            },
            "柔和": {
                "cosyvoice": "longxiaoxia",  # v1音色（不带_v2后缀）
                "openai": "shimmer",
                "qwen3_tts": "Jennifer / 詹妮弗",
                "nihal_tts": "shimmer",
                "default": "female_soft"
            },
            "知性": {
                "cosyvoice": "longxiaochun",  # v1音色（不带_v2后缀）
                "openai": "nova",
                "qwen3_tts": "Katerina / 卡捷琳娜",
                "nihal_tts": "sage",
                "default": "female_intellectual"
            },

            # 通用特征
            "标准": {
                "cosyvoice": "longwan",  # v1音色（不带_v2后缀，男声标准，与qwen3保持性别一致）
                "openai": "alloy",
                "qwen3_tts": "Ethan / 晨煦",
                "nihal_tts": "alloy",
                "default": "standard"
            },
            "专业": {
                "cosyvoice": "longwan",  # v1音色（不带_v2后缀）
                "openai": "onyx",
                "qwen3_tts": "Elias / 墨讲师",
                "nihal_tts": "onyx",
                "default": "professional"
            }
        }

        # 自定义音色目录
        self.custom_voices_dir = os.path.join(settings.uploads_dir, "custom_voices")

    def resolve_voice(self, voice_description: str, tts_engine: str) -> Tuple[str, Optional[str]]:
        """
        解析音色描述，返回适合当前TTS引擎的音色ID或文件路径

        Args:
            voice_description: 音色描述（可以是ID、特征描述或文件路径）
            tts_engine: TTS引擎类型

        Returns:
            (voice_id, voice_file_path) 元组
            - voice_id: 音色ID（用于API调用）
            - voice_file_path: 音色文件路径（用于需要文件的引擎）
        """
        if not voice_description:
            return self._get_default_voice(tts_engine), None

        voice_description = voice_description.strip()
        logger.info(f"解析音色: '{voice_description}' for {tts_engine}")

        # 🔧 向后兼容：自动将v2格式的音色ID转换为v1格式
        # 移除 _v2 / _v3 后缀，统一使用v1格式（不带后缀）
        if voice_description.endswith('_v2') or voice_description.endswith('_v3'):
            original_description = voice_description
            voice_description = voice_description.replace('_v2', '').replace('_v3', '')
            logger.info(f"✅ 自动转换音色格式: '{original_description}' -> '{voice_description}' (v2/v3 -> v1)")

        # 🔧 v1模型不支持的音色替代映射
        # longxiaoyuan（龙小媛-女声活力）在v1中不存在，映射到 longxiaoxia（龙小夏-女声温暖）
        v1_voice_substitutions = {
            "longxiaoyuan": "longxiaoxia"  # 女声活力 -> 女声温暖（最接近的女声）
        }

        if tts_engine.lower() == 'cosyvoice' and voice_description in v1_voice_substitutions:
            original_voice = voice_description
            voice_description = v1_voice_substitutions[voice_description]
            logger.info(f"🔄 v1模型音色替代: '{original_voice}' -> '{voice_description}' (v1不支持原音色)")

        # 1. 检查是否是CosyVoice官方音色ID
        if voice_description in self.cosyvoice_voices:
            logger.info(f"识别为CosyVoice官方音色: {voice_description}")
            return self._map_cosyvoice_to_engine(voice_description, tts_engine)

        # 2. 检查是否是OpenAI音色ID
        if voice_description in self.openai_voices:
            logger.info(f"识别为OpenAI音色: {voice_description}")
            return self._map_openai_to_engine(voice_description, tts_engine)

        # 3. 检查是否是Qwen3音色ID
        if voice_description in self.qwen3_voices:
            logger.info(f"识别为Qwen3音色: {voice_description}")
            return self._map_qwen3_to_engine(voice_description, tts_engine)

        # 4. 检查是否是Nihal音色ID
        if voice_description.lower() in [v.lower() for v in self.nihal_voices.keys()]:
            logger.info(f"识别为Nihal音色: {voice_description}")
            return self._map_nihal_to_engine(voice_description, tts_engine)

        # 5. 检查是否是自定义音色文件路径或ID
        voice_file_path = self._find_custom_voice_file(voice_description)
        if voice_file_path:
            logger.info(f"识别为自定义音色文件: {voice_file_path}")
            return self._handle_custom_voice(voice_file_path, tts_engine)

        # 6. 根据特征关键词映射
        voice_id = self._map_by_keywords(voice_description, tts_engine)
        if voice_id:
            logger.info(f"通过关键词映射: '{voice_description}' -> {voice_id}")
            return voice_id, None

        # 7. 默认音色
        logger.warning(f"无法解析音色 '{voice_description}'，使用默认音色")
        return self._get_default_voice(tts_engine), None

    def _map_cosyvoice_to_engine(self, cosyvoice_id: str, tts_engine: str) -> Tuple[str, Optional[str]]:
        """将CosyVoice音色ID映射到其他引擎"""
        if tts_engine.lower() == 'cosyvoice':
            return cosyvoice_id, None

        # 根据CosyVoice音色特征映射到其他引擎（同时支持v1和v2格式）
        voice_mapping = {
            # v1格式（不带_v2后缀）
            "longwan": {"openai": "onyx", "default": "male_steady"},
            "longyuan": {"openai": "echo", "default": "male_deep"},
            "longxiaochun": {"openai": "nova", "default": "female_standard"},
            "longxiaoxia": {"openai": "shimmer", "default": "female_warm"},
            "longxiaoyuan": {"openai": "nova", "default": "female_energetic"},
            "longxiaocheng": {"openai": "echo", "default": "male_magnetic"},
            # v2格式（带_v2后缀，向后兼容）
            "longwan_v2": {"openai": "onyx", "default": "male_steady"},
            "longyuan_v2": {"openai": "echo", "default": "male_deep"},
            "longxiaochun_v2": {"openai": "nova", "default": "female_standard"},
            "longxiaoxia_v2": {"openai": "shimmer", "default": "female_warm"},
            "longxiaoyuan_v2": {"openai": "nova", "default": "female_energetic"}
        }

        engine_map = voice_mapping.get(cosyvoice_id, {})

        if tts_engine.lower() == 'openai':
            return engine_map.get("openai", "alloy"), None
        else:
            return engine_map.get("default", "standard"), None

    def _map_openai_to_engine(self, openai_voice: str, tts_engine: str) -> Tuple[str, Optional[str]]:
        """将OpenAI音色映射到其他引擎"""
        if tts_engine.lower() == 'openai':
            return openai_voice, None

        # 映射到CosyVoice（使用v1格式，不带_v2后缀）
        openai_to_cosyvoice = {
            "onyx": "longwan",
            "echo": "longyuan",
            "fable": "longwan",
            "nova": "longxiaoyuan",
            "shimmer": "longxiaoxia",
            "alloy": "longxiaochun"
        }

        # 映射到Qwen3
        openai_to_qwen3 = {
            "onyx": "Elias / 墨讲师",
            "echo": "Elias / 墨讲师",
            "fable": "Ethan / 晨煦",
            "nova": "Cherry / 芊悦",
            "shimmer": "Jennifer / 詹妮弗",
            "alloy": "Ethan / 晨煦"
        }

        if tts_engine.lower() == 'cosyvoice':
            return openai_to_cosyvoice.get(openai_voice, "longxiaochun"), None
        elif tts_engine.lower() == 'qwen3_tts':
            return openai_to_qwen3.get(openai_voice, "Cherry / 芊悦"), None
        elif tts_engine.lower() == 'nihal_tts':
            # Nihal使用OpenAI兼容ID，直接返回
            return openai_voice, None
        else:
            return openai_voice, None

    def _map_qwen3_to_engine(self, qwen3_voice: str, tts_engine: str) -> Tuple[str, Optional[str]]:
        """将Qwen3音色映射到其他引擎"""
        if tts_engine.lower() == 'qwen3_tts':
            return qwen3_voice, None

        # 映射到CosyVoice（使用v1格式，不带_v2后缀）
        qwen3_to_cosyvoice = {
            "Cherry / 芊悦": "longxiaochun",
            "Ethan / 晨煦": "longwan",
            "Jennifer / 詹妮弗": "longxiaoxia",
            "Ryan / 甜茶": "longxiaoyuan",
            "Katerina / 卡捷琳娜": "longxiaochun",
            "Elias / 墨讲师": "longwan",
        }

        # 映射到OpenAI
        qwen3_to_openai = {
            "Cherry / 芊悦": "nova",
            "Ethan / 晨煦": "alloy",
            "Jennifer / 詹妮弗": "shimmer",
            "Ryan / 甜茶": "fable",
            "Katerina / 卡捷琳娜": "nova",
            "Elias / 墨讲师": "onyx",
        }

        if tts_engine.lower() == 'cosyvoice':
            return qwen3_to_cosyvoice.get(qwen3_voice, "longxiaochun"), None
        elif tts_engine.lower() == 'openai':
            return qwen3_to_openai.get(qwen3_voice, "alloy"), None
        elif tts_engine.lower() == 'nihal_tts':
            # 映射到Nihal（使用OpenAI兼容ID）
            openai_voice = qwen3_to_openai.get(qwen3_voice, "alloy")
            return openai_voice, None
        else:
            return qwen3_voice, None

    def _map_nihal_to_engine(self, nihal_voice: str, tts_engine: str) -> Tuple[str, Optional[str]]:
        """将Nihal音色映射到其他引擎（Nihal使用OpenAI兼容ID）"""
        # Nihal使用OpenAI兼容的音色ID，所以可以直接调用OpenAI映射
        return self._map_openai_to_engine(nihal_voice, tts_engine)

    def _find_custom_voice_file(self, voice_id_or_path: str) -> Optional[str]:
        """查找自定义音色文件"""
        # 如果已经是完整路径且文件存在
        if os.path.isabs(voice_id_or_path) and os.path.exists(voice_id_or_path):
            return voice_id_or_path

        # 在自定义音色目录中搜索
        if not os.path.exists(self.custom_voices_dir):
            return None

        # 尝试通过ID匹配文件
        for filename in os.listdir(self.custom_voices_dir):
            file_stem = Path(filename).stem
            if file_stem == voice_id_or_path or filename == voice_id_or_path:
                return os.path.join(self.custom_voices_dir, filename)

        return None

    def _handle_custom_voice(self, voice_file_path: str, tts_engine: str) -> Tuple[str, Optional[str]]:
        """处理自定义音色文件"""
        # 对于支持文件上传的引擎（如IndexTTS2），直接返回文件路径
        if tts_engine.lower() in ['indextts2', 'indextts2_gradio']:
            return "custom_voice", voice_file_path

        # 对于不支持文件的引擎，返回默认音色
        # TODO: 未来可以考虑音色克隆或转换
        logger.warning(f"{tts_engine} 不支持自定义音色文件，使用默认音色")
        return self._get_default_voice(tts_engine), None

    def _map_by_keywords(self, description: str, tts_engine: str) -> Optional[str]:
        """通过关键词映射音色（支持性别优先级判断）"""
        description_lower = description.lower()

        # 定义性别关键词
        male_keywords = ["男声", "男", "male", "男中音"]
        female_keywords = ["女声", "女", "female"]

        # 检测性别偏好
        detected_gender = None
        for keyword in male_keywords:
            if keyword in description_lower:
                detected_gender = "male"
                break

        if not detected_gender:
            for keyword in female_keywords:
                if keyword in description_lower:
                    detected_gender = "female"
                    break

        # 定义各引擎的性别音色分类
        gender_voice_map = {
            "cosyvoice": {
                "male": ["longwan", "longyuan"],  # v1音色（不带_v2后缀）
                "female": ["longxiaochun", "longxiaoxia", "longxiaoyuan"]  # v1音色（不带_v2后缀）
            },
            "openai": {
                "male": ["onyx", "echo", "fable"],
                "female": ["nova", "shimmer", "alloy"]
            },
            "qwen3_tts": {
                "male": ["Ethan / 晨煦", "Elias / 墨讲师", "Ryan / 甜茶", "Li / 南京-老李", "Marcus / 陕西-秦川", "Roy / 闽南-阿杰", "Peter / 天津-李彼得", "Eric / 四川-程川", "Rocky / 粤语-阿强", "Dylan / 北京-晓东"],
                "female": ["Cherry / 芊悦", "Jennifer / 詹妮弗", "Katerina / 卡捷琳娜", "Kiki / 粤语-阿清", "Sunny / 四川-晴儿", "Jada / 上海-阿珍"]
            },
            "nihal_tts": {
                "male": ["onyx", "echo", "fable", "ash", "sage"],
                "female": ["nova", "shimmer", "coral", "verse", "ballad"]
            }
        }

        # 遍历关键词进行匹配
        for keyword, engine_map in self.voice_keyword_mapping.items():
            # 跳过性别关键词本身（已在上面处理）
            if keyword in male_keywords + female_keywords:
                continue

            if keyword in description_lower:
                # 获取该关键词对应的音色ID
                if tts_engine.lower() in engine_map:
                    voice_id = engine_map[tts_engine.lower()]
                elif tts_engine.lower() == 'cosyvoice' and 'cosyvoice' in engine_map:
                    voice_id = engine_map['cosyvoice']
                elif tts_engine.lower() == 'openai' and 'openai' in engine_map:
                    voice_id = engine_map['openai']
                else:
                    voice_id = engine_map.get('default')

                # 如果检测到性别偏好，验证音色是否符合性别
                if detected_gender and tts_engine.lower() in gender_voice_map:
                    gender_voices = gender_voice_map[tts_engine.lower()].get(detected_gender, [])

                    # 如果当前音色不符合性别，寻找符合性别的替代音色
                    if voice_id not in gender_voices and gender_voices:
                        logger.info(f"音色 '{voice_id}' 不符合性别 '{detected_gender}'，使用该性别的默认音色")
                        # 返回该性别的第一个音色（默认音色）
                        return gender_voices[0]

                return voice_id

        # 如果只有性别关键词，没有风格关键词，返回该性别的默认音色
        if detected_gender and tts_engine.lower() in gender_voice_map:
            gender_voices = gender_voice_map[tts_engine.lower()].get(detected_gender, [])
            if gender_voices:
                logger.info(f"仅检测到性别 '{detected_gender}'，使用默认音色: {gender_voices[0]}")
                return gender_voices[0]

        return None

    def _get_default_voice(self, tts_engine: str) -> str:
        """获取引擎的默认音色"""
        defaults = {
            "cosyvoice": "longxiaochun",  # 龙小春（女声-标准，v1格式不带_v2后缀）
            "openai": "alloy",
            "qwen3_tts": "Cherry / 芊悦",  # Qwen3默认女声
            "nihal_tts": "alloy",  # Nihal默认标准男声
            "indextts2": "default",
            "indextts2_gradio": "default",
            "chatterbox": "chatterbox_default"
        }

        return defaults.get(tts_engine.lower(), "default")

    def get_all_available_voices(self, tts_engine: str) -> Dict[str, str]:
        """获取指定引擎的所有可用音色"""
        if tts_engine.lower() == 'cosyvoice':
            return self.cosyvoice_voices.copy()
        elif tts_engine.lower() == 'openai':
            return self.openai_voices.copy()
        else:
            # 其他引擎返回默认音色列表
            return {"default": "默认音色"}

    def get_custom_voices(self) -> Dict[str, str]:
        """获取所有自定义音色"""
        custom_voices = {}

        if not os.path.exists(self.custom_voices_dir):
            return custom_voices

        for filename in os.listdir(self.custom_voices_dir):
            if filename.lower().endswith(('.wav', '.mp3', '.m4a')):
                voice_id = Path(filename).stem
                voice_path = os.path.join(self.custom_voices_dir, filename)
                custom_voices[voice_id] = voice_path

        return custom_voices


# 全局音色解析服务实例
voice_resolver = VoiceResolverService()
