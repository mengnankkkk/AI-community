"""
阿里云 CosyVoice 音色克隆服务
支持上传音频文件进行音色克隆
"""

import os
import base64
import hashlib
import hmac
import time
import uuid
import logging
import asyncio
from typing import Dict, Optional, Tuple
from urllib import parse
import aiohttp

from ..core.config import settings

logger = logging.getLogger(__name__)


class CosyVoiceCloneService:
    """阿里云 CosyVoice 音色克隆服务"""

    def __init__(self):
        self.access_key_id = getattr(settings, 'alicloud_dashscope_api_key', '')
        self.access_key_secret = getattr(settings, 'alicloud_dashscope_api_secret', '')
        self.api_endpoint = "https://nls-slp.cn-shanghai.aliyuncs.com/"
        self.region_id = "cn-shanghai"

        if not self.access_key_id or self.access_key_id == 'your_alicloud_api_key_here':
            logger.warning("阿里云 API Key 未配置，音色克隆服务不可用")

        if not self.access_key_secret:
            logger.warning("阿里云 API Secret 未配置，音色克隆服务不可用")

    @staticmethod
    def _encode_text(text: str) -> str:
        """URL编码文本"""
        encoded_text = parse.quote_plus(str(text))
        return encoded_text.replace('+', '%20').replace('*', '%2A').replace('%7E', '~')

    @staticmethod
    def _encode_dict(dic: Dict) -> str:
        """URL编码字典"""
        keys = dic.keys()
        dic_sorted = [(key, dic[key]) for key in sorted(keys)]
        encoded_text = parse.urlencode(dic_sorted)
        return encoded_text.replace('+', '%20').replace('*', '%2A').replace('%7E', '~')

    def _generate_signature(self, query_string: str) -> str:
        """生成API签名"""
        string_to_sign = 'POST' + '&' + self._encode_text('/') + '&' + self._encode_text(query_string)
        secreted_string = hmac.new(
            bytes(self.access_key_secret + '&', encoding='utf-8'),
            bytes(string_to_sign, encoding='utf-8'),
            hashlib.sha1
        ).digest()
        signature = base64.b64encode(secreted_string)
        return self._encode_text(signature)

    def _validate_voice_prefix(self, voice_prefix: str) -> Tuple[bool, Optional[str]]:
        """
        验证音色前缀

        规则：
        - 不能为空
        - 不超过10个字符
        - 只包含数字和字母
        """
        if not voice_prefix:
            return False, "音色前缀不能为空"

        if len(voice_prefix) > 10:
            return False, "音色前缀不能超过10个字符"

        if not voice_prefix.isalnum():
            return False, "音色前缀只能包含数字和字母"

        return True, None

    async def clone_voice(
        self,
        audio_url: str,
        voice_prefix: str,
        voice_name: Optional[str] = None
    ) -> Dict:
        """
        克隆音色

        Args:
            audio_url: 音频文件URL（公网可访问）
            voice_prefix: 音色前缀（不超过10个字符，只包含数字和字母）
            voice_name: 音色名称（可选）

        Returns:
            克隆结果字典
        """
        # 验证配置
        if not self.access_key_id or not self.access_key_secret:
            return {
                "success": False,
                "error": "阿里云 API Key 或 Secret 未配置"
            }

        # 验证音色前缀
        valid, error_msg = self._validate_voice_prefix(voice_prefix)
        if not valid:
            return {
                "success": False,
                "error": error_msg
            }

        try:
            # 构建请求参数
            parameters = {
                'AccessKeyId': self.access_key_id,
                'Action': 'CosyVoiceClone',
                'Format': 'JSON',
                'RegionId': self.region_id,
                'SignatureMethod': 'HMAC-SHA1',
                'SignatureNonce': str(uuid.uuid4()),
                'SignatureVersion': '1.0',
                'Timestamp': time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                'Version': '2019-08-19',
                'VoicePrefix': voice_prefix,
                'Url': audio_url,
            }

            # 生成签名
            query_string = self._encode_dict(parameters)
            signature = self._generate_signature(query_string)

            # 构建完整URL
            full_url = f"{self.api_endpoint}?Signature={signature}&{query_string}"

            # 发送请求
            async with aiohttp.ClientSession() as session:
                async with session.post(full_url, timeout=aiohttp.ClientTimeout(total=30)) as response:
                    response_text = await response.text()
                    logger.info(f"CosyVoice 克隆 API 响应: {response_text}")

                    try:
                        result = await response.json()
                    except:
                        result = {"raw_response": response_text}

                    if response.status == 200:
                        return {
                            "success": True,
                            "voice_id": f"{voice_prefix}_cloned",
                            "voice_prefix": voice_prefix,
                            "voice_name": voice_name or voice_prefix,
                            "status": "cloning",
                            "message": "音色克隆任务已提交",
                            "response": result
                        }
                    else:
                        return {
                            "success": False,
                            "error": f"API 调用失败: HTTP {response.status}",
                            "response": result
                        }

        except asyncio.TimeoutError:
            logger.error("CosyVoice 克隆 API 超时")
            return {
                "success": False,
                "error": "API 调用超时，请稍后重试"
            }
        except Exception as e:
            logger.error(f"CosyVoice 音色克隆失败: {str(e)}", exc_info=True)
            return {
                "success": False,
                "error": f"音色克隆失败: {str(e)}"
            }

    async def list_cloned_voices(
        self,
        voice_prefix: str,
        page_index: int = 1,
        page_size: int = 10
    ) -> Dict:
        """
        查询克隆音色列表

        Args:
            voice_prefix: 音色前缀
            page_index: 页码（从1开始）
            page_size: 每页数量

        Returns:
            音色列表
        """
        # 验证配置
        if not self.access_key_id or not self.access_key_secret:
            return {
                "success": False,
                "error": "阿里云 API Key 或 Secret 未配置"
            }

        try:
            # 构建请求参数
            parameters = {
                'AccessKeyId': self.access_key_id,
                'Action': 'ListCosyVoice',
                'Format': 'JSON',
                'RegionId': self.region_id,
                'SignatureMethod': 'HMAC-SHA1',
                'SignatureNonce': str(uuid.uuid4()),
                'SignatureVersion': '1.0',
                'Timestamp': time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                'Version': '2019-08-19',
                'VoicePrefix': voice_prefix,
                'PageIndex': str(page_index),
                'PageSize': str(page_size),
            }

            # 生成签名
            query_string = self._encode_dict(parameters)
            signature = self._generate_signature(query_string)

            # 构建完整URL
            full_url = f"{self.api_endpoint}?Signature={signature}&{query_string}"

            # 发送请求
            async with aiohttp.ClientSession() as session:
                async with session.post(full_url, timeout=aiohttp.ClientTimeout(total=10)) as response:
                    response_text = await response.text()
                    logger.info(f"CosyVoice 列表 API 响应: {response_text}")

                    try:
                        result = await response.json()
                    except:
                        result = {"raw_response": response_text}

                    if response.status == 200:
                        return {
                            "success": True,
                            "voices": result.get("Data", {}).get("Voices", []),
                            "total": result.get("Data", {}).get("TotalCount", 0),
                            "page_index": page_index,
                            "page_size": page_size,
                            "response": result
                        }
                    else:
                        return {
                            "success": False,
                            "error": f"API 调用失败: HTTP {response.status}",
                            "response": result
                        }

        except asyncio.TimeoutError:
            logger.error("CosyVoice 列表 API 超时")
            return {
                "success": False,
                "error": "API 调用超时，请稍后重试"
            }
        except Exception as e:
            logger.error(f"查询克隆音色列表失败: {str(e)}", exc_info=True)
            return {
                "success": False,
                "error": f"查询失败: {str(e)}"
            }

    async def validate_audio_for_cloning(self, audio_path: str) -> Tuple[bool, Optional[str]]:
        """
        验证音频文件是否符合克隆要求

        Args:
            audio_path: 音频文件路径

        Returns:
            (是否有效, 错误信息)
        """
        try:
            # 检查文件是否存在
            if not os.path.exists(audio_path):
                return False, "音频文件不存在"

            # 检查文件大小
            file_size = os.path.getsize(audio_path)
            max_size = 10 * 1024 * 1024  # 10MB
            if file_size > max_size:
                return False, f"文件过大（{file_size / 1024 / 1024:.2f}MB），最大支持10MB"

            # 检查文件格式
            file_ext = os.path.splitext(audio_path)[1].lower()
            if file_ext not in ['.wav', '.mp3', '.m4a', '.aac']:
                return False, f"不支持的文件格式：{file_ext}，仅支持 WAV, MP3, M4A, AAC"

            # 使用 pydub 检查音频属性
            try:
                from pydub import AudioSegment
                audio = AudioSegment.from_file(audio_path)

                # 检查采样率
                if audio.frame_rate < 16000:
                    return False, f"采样率过低（{audio.frame_rate}Hz），需要至少16kHz"

                # 检查时长（至少5秒）
                duration_seconds = len(audio) / 1000
                if duration_seconds < 5:
                    return False, f"音频时长过短（{duration_seconds:.1f}秒），需要至少5秒连续语音"

                logger.info(f"音频验证通过: {audio_path}, 采样率={audio.frame_rate}Hz, 时长={duration_seconds:.1f}s")
                return True, None

            except Exception as e:
                logger.warning(f"无法解析音频文件: {str(e)}")
                # 如果无法解析，返回通过（让服务器端验证）
                return True, None

        except Exception as e:
            logger.error(f"音频验证失败: {str(e)}")
            return False, f"音频验证失败: {str(e)}"

    async def health_check(self) -> Dict:
        """健康检查"""
        if not self.access_key_id or not self.access_key_secret:
            return {
                "status": "unconfigured",
                "service": "CosyVoice Clone",
                "error": "API Key 或 Secret 未配置"
            }

        return {
            "status": "configured",
            "service": "CosyVoice Clone",
            "message": "音色克隆服务已配置"
        }


# 全局音色克隆服务实例
cosyvoice_clone_service = CosyVoiceCloneService()
