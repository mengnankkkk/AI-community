"""
语音样本文件管理器
为IndexTTS-2 Gradio服务创建和管理默认音色样本
"""

import os
import logging
from typing import List, Dict
from pydub import AudioSegment
from pydub.generators import Sine

logger = logging.getLogger(__name__)


class VoiceSampleManager:
    """语音样本管理器"""

    def __init__(self, voice_samples_dir: str = "voice_samples"):
        self.voice_samples_dir = voice_samples_dir
        os.makedirs(voice_samples_dir, exist_ok=True)

    def create_default_samples(self):
        """创建默认的音色样本文件"""
        # 定义默认音色样本配置
        sample_configs = {
            "voice_standard.wav": {"freq": 220, "duration": 2000, "desc": "标准音色"},
            "voice_male.wav": {"freq": 180, "duration": 2000, "desc": "男声"},
            "voice_female.wav": {"freq": 280, "duration": 2000, "desc": "女声"},
            "voice_deep.wav": {"freq": 150, "duration": 2000, "desc": "浑厚"},
            "voice_crisp.wav": {"freq": 320, "duration": 2000, "desc": "清脆"},
            "voice_warm.wav": {"freq": 240, "duration": 2000, "desc": "温暖"},
            "voice_steady.wav": {"freq": 200, "duration": 2000, "desc": "沉稳"},
            "voice_energetic.wav": {"freq": 300, "duration": 2000, "desc": "有活力"},
            "voice_magnetic.wav": {"freq": 170, "duration": 2000, "desc": "有磁性"},
            "voice_intellectual.wav": {"freq": 260, "duration": 2000, "desc": "知性"},
            "voice_baritone.wav": {"freq": 160, "duration": 2000, "desc": "男中音"},
        }

        created_samples = []

        for filename, config in sample_configs.items():
            sample_path = os.path.join(self.voice_samples_dir, filename)

            # 如果文件已存在，跳过
            if os.path.exists(sample_path):
                logger.info(f"音色样本已存在，跳过: {filename}")
                continue

            try:
                # 生成简单的正弦波作为占位符音频
                # 在实际使用中，这些应该是真实的人声样本
                tone = Sine(config["freq"]).to_audio_segment(duration=config["duration"])

                # 添加淡入淡出，使音频更自然
                tone = tone.fade_in(100).fade_out(100)

                # 降低音量，避免过响
                tone = tone - 20  # 降低20dB

                # 导出音频文件
                tone.export(sample_path, format="wav")

                created_samples.append({
                    "filename": filename,
                    "description": config["desc"],
                    "path": sample_path
                })

                logger.info(f"创建音色样本: {filename} ({config['desc']})")

            except Exception as e:
                logger.error(f"创建音色样本失败 {filename}: {str(e)}")

        return created_samples

    def create_default_voice_sample(self) -> str:
        """创建默认音色样本"""
        default_path = os.path.join(self.voice_samples_dir, "default_voice.wav")

        if os.path.exists(default_path):
            return default_path

        try:
            # 生成1秒的中性音调
            tone = Sine(220).to_audio_segment(duration=1000)
            tone = tone.fade_in(50).fade_out(50) - 15  # 淡入淡出并降低音量

            tone.export(default_path, format="wav")
            logger.info(f"创建默认音色样本: {default_path}")

            return default_path

        except Exception as e:
            logger.error(f"创建默认音色样本失败: {str(e)}")
            return None

    def list_available_samples(self) -> List[Dict[str, str]]:
        """列出可用的音色样本"""
        samples = []

        if not os.path.exists(self.voice_samples_dir):
            return samples

        for filename in os.listdir(self.voice_samples_dir):
            if filename.endswith('.wav'):
                file_path = os.path.join(self.voice_samples_dir, filename)
                samples.append({
                    "filename": filename,
                    "path": file_path,
                    "size": os.path.getsize(file_path)
                })

        return samples

    def check_samples_availability(self) -> Dict[str, bool]:
        """检查音色样本的可用性"""
        required_samples = [
            "voice_standard.wav", "voice_male.wav", "voice_female.wav",
            "voice_deep.wav", "voice_crisp.wav", "voice_warm.wav"
        ]

        availability = {}
        for sample in required_samples:
            sample_path = os.path.join(self.voice_samples_dir, sample)
            availability[sample] = os.path.exists(sample_path)

        return availability

    def ensure_samples_exist(self):
        """确保音色样本存在，如果不存在则创建"""
        availability = self.check_samples_availability()

        # 如果有缺失的样本，创建所有样本
        if not all(availability.values()):
            logger.info("检测到缺失的音色样本，开始创建默认样本...")
            return self.create_default_samples()

        logger.info("所有必需的音色样本都已存在")
        return []


# 全局音色样本管理器实例
voice_sample_manager = VoiceSampleManager()


def initialize_voice_samples():
    """初始化音色样本"""
    try:
        return voice_sample_manager.ensure_samples_exist()
    except Exception as e:
        logger.error(f"音色样本初始化失败: {str(e)}")
        return []


def get_voice_sample_path(voice_description: str) -> str:
    """根据音色描述获取样本路径"""
    return voice_sample_manager.get_voice_sample_path(voice_description)


if __name__ == "__main__":
    # 直接运行时创建默认样本
    logging.basicConfig(level=logging.INFO)
    manager = VoiceSampleManager()
    samples = manager.create_default_samples()
    print(f"创建了 {len(samples)} 个音色样本")
    for sample in samples:
        print(f"  - {sample['filename']}: {sample['description']}")