"""
IndexTTS-2 Gradio客户端服务
基于IndexTeam/IndexTTS-2-Demo的在线TTS服务
"""

import asyncio
import os
import ssl
import logging
import tempfile
from typing import List, Dict, Optional
from pydub import AudioSegment

# 【关键修复】在导入gradio_client之前全局禁用SSL验证并配置WebSocket代理
# 解决代理环境下的SSL握手问题
os.environ['GRADIO_SSL_VERIFY'] = 'false'
os.environ['CURL_CA_BUNDLE'] = ''
os.environ['REQUESTS_CA_BUNDLE'] = ''

# Python SSL模块全局配置
ssl._create_default_https_context = ssl._create_unverified_context

# 禁用SSL警告
try:
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
except:
    pass

# 【关键修复2】猴子补丁httpx，禁用SSL验证并支持HTTP/SOCKS5代理
try:
    import httpx

    # 保存原始类
    _original_httpx_client = httpx.Client
    _original_httpx_async_client = httpx.AsyncClient

    # 创建补丁后的Client类
    class PatchedClient(httpx.Client):
        def __init__(self, *args, **kwargs):
            # 强制禁用SSL验证
            kwargs['verify'] = False
            # 如果环境变量中有代理配置，使用代理（支持HTTP和SOCKS5）
            if 'HTTP_PROXY' in os.environ or 'HTTPS_PROXY' in os.environ:
                proxy = os.environ.get('HTTPS_PROXY') or os.environ.get('HTTP_PROXY')
                if proxy:
                    # httpx支持统一代理字符串（http://、https://、socks5://）
                    kwargs['proxies'] = proxy
                    logger.info(f"httpx Client 使用代理: {proxy}")
            super().__init__(*args, **kwargs)

    class PatchedAsyncClient(httpx.AsyncClient):
        def __init__(self, *args, **kwargs):
            # 强制禁用SSL验证
            kwargs['verify'] = False
            # 如果环境变量中有代理配置，使用代理（支持HTTP和SOCKS5）
            if 'HTTP_PROXY' in os.environ or 'HTTPS_PROXY' in os.environ:
                proxy = os.environ.get('HTTPS_PROXY') or os.environ.get('HTTP_PROXY')
                if proxy:
                    # httpx支持统一代理字符串（http://、https://、socks5://）
                    kwargs['proxies'] = proxy
                    logger.info(f"httpx AsyncClient 使用代理: {proxy}")
            super().__init__(*args, **kwargs)

    # 替换httpx的Client类
    httpx.Client = PatchedClient
    httpx.AsyncClient = PatchedAsyncClient

except Exception as e:
    logging.warning(f"无法补丁httpx: {e}")

# 【关键修复3】猴子补丁 websockets 库以支持代理
# Gradio Client 使用 websockets 库，需要为其配置代理
try:
    import websockets
    from websockets.legacy.client import connect as _original_connect

    # 创建支持代理的 websocket 连接函数
    def patched_connect(*args, **kwargs):
        """支持代理的 websocket 连接"""
        # WebSocket 通过 HTTP CONNECT 隧道使用代理
        # 但这需要更复杂的实现，暂时禁用SSL验证来解决连接问题
        kwargs['ssl'] = ssl._create_unverified_context()
        return _original_connect(*args, **kwargs)

    # 替换默认的 connect 函数
    websockets.legacy.client.connect = patched_connect
    websockets.connect = patched_connect

except Exception as e:
    logging.warning(f"无法补丁websockets: {e}")

# 现在才导入gradio_client
from gradio_client import Client, handle_file

from ..models.podcast import PodcastScript, CharacterRole, ScriptDialogue
from ..core.config import settings
from .audio_effects_service import AudioEffectsService
from .voice_sample_manager import voice_sample_manager
from ..utils.text_cleaner import clean_for_tts
from .voice_resolver_service import voice_resolver

logger = logging.getLogger(__name__)


class IndexTTS2GradioService:
    """IndexTTS-2 Gradio在线服务客户端"""

    def __init__(self):
        self.client = None
        self.space_name = getattr(settings, 'indextts2_gradio_space', "IndexTeam/IndexTTS-2-Demo")
        self.initialized = False
        self.voice_samples_dir = "voice_samples"

        # 初始化音效服务
        self.audio_effects = AudioEffectsService()

        # 确保音色样本存在
        voice_sample_manager.ensure_samples_exist()

        # 角色音色映射配置 - 映射到具体的音色样本文件
        self.character_voice_mapping = {
            # 中文描述关键词
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
            "知性": "voice_intellectual.wav",
            # 角色名映射
            "主持人": "voice_standard.wav",
            "嘉宾": "voice_warm.wav",
            "博士": "voice_intellectual.wav",
            "教授": "voice_steady.wav",
            "经理": "voice_male.wav",
            "专家": "voice_magnetic.wav",
            # 【新增】NihalGazi音色ID兼容映射（向后兼容）
            "alloy": "voice_standard.wav",      # 通用标准
            "echo": "voice_male.wav",           # 男声
            "fable": "voice_warm.wav",          # 温暖
            "onyx": "voice_deep.wav",           # 浑厚男声
            "nova": "voice_female.wav",         # 女声
            "shimmer": "voice_crisp.wav",       # 清脆女声
            "coral": "voice_warm.wav",          # 温暖
            "sage": "voice_intellectual.wav",   # 知性
            "ash": "voice_steady.wav",          # 沉稳
            "ballad": "voice_magnetic.wav",     # 磁性
            "verse": "voice_energetic.wav",     # 活力
            # 【新增】voice_XX 数字ID映射（NihalGazi顺序）
            "voice_01": "voice_standard.wav",      # alloy - 标准男声
            "voice_02": "voice_male.wav",          # echo - 磁性男声
            "voice_03": "voice_warm.wav",          # fable - 温和男声
            "voice_04": "voice_deep.wav",          # onyx - 浑厚男声
            "voice_05": "voice_steady.wav",        # ash - 沉稳男声
            "voice_06": "voice_intellectual.wav",  # sage - 智者男声
            "voice_07": "voice_female.wav",        # nova - 清晰女声
            "voice_08": "voice_crisp.wav",         # shimmer - 活力女声
            "voice_09": "voice_warm.wav",          # coral - 温暖女声
            "voice_10": "voice_energetic.wav",     # verse - 优雅女声
            "voice_11": "voice_magnetic.wav",      # ballad - 柔美女声
            "voice_12": "voice_standard.wav",      # amuch - 特色
            "voice_13": "voice_male.wav",          # dan - 特色
        }

        # 情感映射到向量权重
        self.emotion_vectors = {
            "开心": {"vec1": 0.8, "vec2": 0.2, "vec3": 0.0, "vec4": 0.0, "vec5": 0.0, "vec6": 0.0, "vec7": 0.5, "vec8": 0.0},
            "悲伤": {"vec1": 0.0, "vec2": 0.0, "vec3": 0.0, "vec4": 0.0, "vec5": 0.0, "vec6": 0.8, "vec7": 0.0, "vec8": 0.0},
            "激动": {"vec1": 0.9, "vec2": 0.0, "vec3": 0.7, "vec4": 0.0, "vec5": 0.0, "vec6": 0.0, "vec7": 0.8, "vec8": 0.0},
            "平静": {"vec1": 0.0, "vec2": 0.7, "vec3": 0.0, "vec4": 0.0, "vec5": 0.0, "vec6": 0.0, "vec7": 0.0, "vec8": 0.0},
            "愤怒": {"vec1": 0.0, "vec2": 0.0, "vec3": 0.9, "vec4": 0.0, "vec5": 0.0, "vec6": 0.0, "vec7": 0.0, "vec8": 0.0},
            "惊讶": {"vec1": 0.3, "vec2": 0.0, "vec3": 0.0, "vec4": 0.0, "vec5": 0.0, "vec6": 0.0, "vec7": 0.9, "vec8": 0.0},
            "温暖": {"vec1": 0.4, "vec2": 0.6, "vec3": 0.0, "vec4": 0.0, "vec5": 0.0, "vec6": 0.0, "vec7": 0.2, "vec8": 0.0},
            "严肃": {"vec1": 0.0, "vec2": 0.8, "vec3": 0.0, "vec4": 0.0, "vec5": 0.0, "vec6": 0.2, "vec7": 0.0, "vec8": 0.0},
            "幽默": {"vec1": 0.6, "vec2": 0.0, "vec3": 0.0, "vec4": 0.0, "vec5": 0.0, "vec6": 0.0, "vec7": 0.4, "vec8": 0.0},
            "思考": {"vec1": 0.0, "vec2": 0.5, "vec3": 0.0, "vec4": 0.0, "vec5": 0.0, "vec6": 0.3, "vec7": 0.0, "vec8": 0.0},
        }

    async def initialize_client(self, max_retries: int = 3):
        """初始化Gradio客户端（带重试机制和代理支持）"""
        if self.initialized:
            return True

        # 【修复】强制设置代理环境变量，确保在多进程/异步环境下生效
        # 优先使用环境变量，再使用 settings
        proxy_enabled = os.getenv('PROXY_ENABLED', '').lower() == 'true' or getattr(settings, 'proxy_enabled', False)

        # 准备 httpx 配置（不包含 verify，因为通过 ssl_verify 参数单独传递）
        httpx_config = {
            'timeout': 120.0,  # 增加超时到120秒
        }

        if proxy_enabled:
            # 从环境变量或settings获取代理地址
            http_proxy = os.getenv('HTTP_PROXY') or getattr(settings, 'http_proxy', '')
            https_proxy = os.getenv('HTTPS_PROXY') or getattr(settings, 'https_proxy', '')

            if http_proxy:
                os.environ['HTTP_PROXY'] = http_proxy
                os.environ['http_proxy'] = http_proxy  # 小写版本，某些库需要
                logger.info(f"✓ 设置HTTP代理: {http_proxy}")
            if https_proxy:
                os.environ['HTTPS_PROXY'] = https_proxy
                os.environ['https_proxy'] = https_proxy  # 小写版本
                logger.info(f"✓ 设置HTTPS代理: {https_proxy}")

            # 设置NO_PROXY避免本地回环使用代理
            if 'NO_PROXY' not in os.environ:
                os.environ['NO_PROXY'] = 'localhost,127.0.0.1'
                os.environ['no_proxy'] = 'localhost,127.0.0.1'

            # 为 httpx 配置代理
            if https_proxy or http_proxy:
                httpx_config['proxies'] = https_proxy or http_proxy
                logger.info(f"✓ httpx_kwargs 代理: {httpx_config['proxies']}")
        else:
            logger.warning("⚠️ 代理未启用，直接连接可能会超时")

        last_error = None
        for attempt in range(max_retries):
            try:
                logger.info(f"正在连接IndexTTS-2 Gradio服务: {self.space_name} (尝试 {attempt + 1}/{max_retries})")
                logger.info(f"httpx配置: timeout={httpx_config['timeout']}s, proxy={httpx_config.get('proxies', 'None')}, ssl_verify=False")

                # 【关键修复】创建客户端时传递 httpx_kwargs 和 ssl_verify
                # Gradio Client会使用这些参数配置所有HTTP请求
                self.client = Client(
                    self.space_name,
                    httpx_kwargs=httpx_config,
                    ssl_verify=False,  # 禁用SSL证书验证
                    verbose=True
                )
                self.initialized = True

                logger.info("✅ IndexTTS-2 Gradio客户端初始化成功")
                return True

            except Exception as e:
                last_error = e
                error_msg = str(e)[:300]
                logger.warning(f"❌ 第{attempt + 1}次尝试失败: {error_msg}")

                # 如果是SSL超时错误，提供额外提示
                if 'handshake' in error_msg.lower() or 'timeout' in error_msg.lower():
                    logger.error("💡 检测到连接超时，请确认：")
                    logger.error(f"  1. 代理服务运行正常（{os.getenv('HTTP_PROXY', 'None')}）")
                    logger.error("  2. 代理可以访问 https://huggingface.co")
                    logger.error("  3. 防火墙未阻止连接")
                    logger.error(f"  4. 超时时间: {httpx_config['timeout']}秒")

                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt  # 指数退避: 1s, 2s, 4s
                    logger.info(f"⏳ 等待{wait_time}秒后重试...")
                    await asyncio.sleep(wait_time)
                    self.initialized = False

        logger.error(f"❌ IndexTTS-2 Gradio客户端初始化最终失败 (共{max_retries}次尝试)")
        logger.error(f"最后错误: {str(last_error)[:300]}")
        return False

    def get_voice_sample_path(self, voice_description: str, voice_file: Optional[str] = None) -> str:
        """
        根据音色描述或文件路径获取音色样本路径（使用统一音色解析服务）

        Args:
            voice_description: 音色描述关键词或ID（支持CosyVoice、OpenAI等音色ID）
            voice_file: 音色文件路径（优先使用）

        Returns:
            音色样本文件路径
        """
        # 优先使用voice_file（用户上传或选择的音色）
        if voice_file and os.path.exists(voice_file):
            logger.info(f"使用指定的音色文件: {voice_file}")
            return voice_file

        # 使用统一的音色解析服务
        voice_id, resolved_voice_file = voice_resolver.resolve_voice(
            voice_description or "",
            "indextts2_gradio"
        )

        # 如果解析器返回了音色文件路径（自定义音色），直接使用
        if resolved_voice_file and os.path.exists(resolved_voice_file):
            logger.info(f"使用解析器返回的音色文件: {resolved_voice_file}")
            return resolved_voice_file

        # 如果解析器返回了音色ID，映射到本地WAV文件
        if voice_id:
            # 尝试在本地映射表中查找
            sample_file = self.character_voice_mapping.get(voice_id)
            if sample_file:
                sample_path = os.path.join(self.voice_samples_dir, sample_file)
                if os.path.exists(sample_path):
                    logger.info(f"音色ID映射: {voice_id} -> {sample_path}")
                    return sample_path

        # 使用语音样本管理器创建默认样本
        default_path = voice_sample_manager.create_default_voice_sample()
        if default_path and os.path.exists(default_path):
            logger.warning(f"使用默认音色样本: {default_path}")
            return default_path

        logger.warning(f"无法获取音色样本: {voice_description}")
        return None

    def get_emotion_vectors(self, emotion: str) -> Dict[str, float]:
        """根据情感获取情感向量"""
        if not emotion:
            # 返回中性情感向量
            return {"vec1": 0, "vec2": 0, "vec3": 0, "vec4": 0, "vec5": 0, "vec6": 0, "vec7": 0, "vec8": 0}

        return self.emotion_vectors.get(emotion, {
            "vec1": 0, "vec2": 0, "vec3": 0, "vec4": 0,
            "vec5": 0, "vec6": 0, "vec7": 0, "vec8": 0
        })

    async def synthesize_single_audio(self, text: str, voice_sample_path: str,
                                    emotion: Optional[str] = None,
                                    output_path: Optional[str] = None,
                                    max_retries: int = 3) -> str:
        """合成单个音频片段（带重试机制）"""
        if not await self.initialize_client():
            raise Exception("IndexTTS-2客户端初始化失败")

        if not self.client:
            raise Exception("IndexTTS-2客户端未初始化")

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

        # 获取情感向量
        emotion_vectors = self.get_emotion_vectors(emotion or "")

        # 重试机制
        last_error = None
        for attempt in range(max_retries):
            try:
                # 【关键修复】使用 asyncio.wait_for 增加超时控制
                logger.info(f"开始音频合成... (超时设置: 180秒)")
                
                # 调用IndexTTS-2 API（使用异步超时包装）
                result = await asyncio.wait_for(
                    asyncio.get_event_loop().run_in_executor(
                        None,
                        lambda: self.client.predict(
                            emo_control_method="Same as the voice reference",  # HuggingFace官方：英文枚举值
                            prompt=handle_file(voice_sample_path),  # 语音参考文件
                            text=cleaned_text,  # 使用清理后的文本
                            emo_ref_path=handle_file(voice_sample_path),  # 情绪参考（使用同样的语音文件）
                            emo_weight=0.8,  # 情绪权重
                            vec1=emotion_vectors["vec1"],
                            vec2=emotion_vectors["vec2"],
                            vec3=emotion_vectors["vec3"],
                            vec4=emotion_vectors["vec4"],
                            vec5=emotion_vectors["vec5"],
                            vec6=emotion_vectors["vec6"],
                            vec7=emotion_vectors["vec7"],
                            vec8=emotion_vectors["vec8"],
                            emo_text="",  # 情绪文本描述
                            emo_random=False,  # 不使用随机情绪
                            max_text_tokens_per_segment=120,  # 每段最大token数
                            param_16=True,  # do_sample
                            param_17=0.8,   # top_p
                            param_18=30,    # top_k
                            param_19=0.8,   # temperature
                            param_20=0,     # length_penalty
                            param_21=3,     # num_beams
                            param_22=10,    # repetition_penalty
                            param_23=1500,  # max_mel_tokens
                            api_name="/gen_single"
                        )
                    ),
                    timeout=180  # 180秒超时
                )

                # 结果是音频文件路径，需要下载到本地
                logger.info(f"IndexTTS-2 API调用完成，结果类型: {type(result)}")
                logger.info(f"结果内容: {result}")
                
                if result:
                    # 检查result的属性和方法
                    logger.info(f"Result属性: {dir(result) if hasattr(result, '__dict__') else 'No attributes'}")
                    
                    # 尝试多种方式获取文件路径
                    file_path = None
                    if hasattr(result, 'path'):
                        file_path = result.path
                        logger.info(f"使用result.path: {file_path}")
                    elif hasattr(result, 'file'):
                        file_path = result.file
                        logger.info(f"使用result.file: {file_path}")
                    elif isinstance(result, str):
                        file_path = result
                        logger.info(f"result是字符串路径: {file_path}")
                    elif isinstance(result, (list, tuple)) and len(result) > 0:
                        file_path = result[0]
                        logger.info(f"result是列表，取第一个: {file_path}")
                    
                    if file_path and os.path.exists(file_path):
                        # 复制文件到指定输出路径
                        import shutil
                        shutil.copy2(file_path, output_path)
                        
                        # 验证复制的文件
                        if os.path.exists(output_path):
                            file_size = os.path.getsize(output_path)
                            logger.info(f"✅ 音频合成成功: {output_path} (大小: {file_size} bytes)")
                            return output_path
                        else:
                            raise Exception(f"文件复制失败: {output_path}")
                    else:
                        raise Exception(f"无法找到有效的音频文件路径: {file_path}")
                else:
                    raise Exception("IndexTTS-2返回空结果")

            except Exception as e:
                last_error = e
                logger.warning(f"❌ 音频合成第{attempt + 1}次尝试失败: {str(e)}")

                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt  # 指数退避: 1s, 2s, 4s
                    logger.info(f"⏳ 等待{wait_time}秒后重试...")
                    await asyncio.sleep(wait_time)

                    # 重新初始化客户端
                    self.initialized = False
                    if not await self.initialize_client():
                        logger.error("❌ 重新初始化客户端失败")
                        continue

        # 所有重试都失败
        error_msg = f"音频合成最终失败 (共{max_retries}次尝试): {str(last_error)}"
        logger.error(f"❌ {error_msg}")
        raise Exception(error_msg)

    async def synthesize_script_audio(self, script: PodcastScript, characters: List[CharacterRole],
                                     task_id: str, atmosphere: str = "轻松幽默",
                                     enable_effects: bool = True, enable_bgm: bool = True) -> str:
        """合成完整播客音频（带音效和BGM）"""
        if not await self.initialize_client():
            raise Exception("IndexTTS-2客户端初始化失败")

        # 创建任务专用目录
        task_dir = os.path.join(settings.audio_output_dir, task_id)
        os.makedirs(task_dir, exist_ok=True)

        # 为每个角色映射音色样本
        character_voice_samples = {}
        for char in characters:
            # 优先使用voice_file，否则使用voice_description映射
            voice_sample_path = self.get_voice_sample_path(
                voice_description=char.voice_description,
                voice_file=char.voice_file if hasattr(char, 'voice_file') else None
            )
            if voice_sample_path:
                character_voice_samples[char.name] = voice_sample_path
                logger.info(f"角色 {char.name} 使用音色: {voice_sample_path}")
            else:
                logger.warning(f"角色 {char.name} 缺少音色样本")

        # 合成每个对话片段
        audio_segments = []

        for i, dialogue in enumerate(script.dialogues):
            voice_sample_path = character_voice_samples.get(dialogue.character_name)
            if not voice_sample_path:
                logger.warning(f"跳过角色 {dialogue.character_name} - 无音色样本")
                continue

            output_path = os.path.join(task_dir, f"segment_{i:03d}.wav")

            try:
                # 合成基础音频
                result_path = await self.synthesize_single_audio(
                    text=dialogue.content,
                    voice_sample_path=voice_sample_path,
                    emotion=dialogue.emotion,
                    output_path=output_path
                )

                if result_path and os.path.exists(result_path):
                    # 加载生成的音频
                    segment = AudioSegment.from_wav(result_path)

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
                        os.remove(result_path)
                    except:
                        pass

            except Exception as e:
                logger.error(f"片段合成失败 {i}: {dialogue.character_name} - {str(e)}")
                continue

        if not audio_segments:
            raise Exception("所有音频片段合成失败")

        # 拼接音频并应用高级处理
        final_audio = await self.concatenate_audio_with_advanced_effects(
            audio_segments, task_dir, task_id, atmosphere, enable_bgm
        )

        return final_audio

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

            logger.info(f"完成IndexTTS-2高级音效处理，输出: {final_path}")
            return final_path

        except Exception as e:
            logger.error(f"IndexTTS-2高级音频处理失败: {str(e)}")
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
                    "service": "IndexTTS-2 Gradio",
                    "space_name": self.space_name,
                    "initialized": self.initialized
                }
            else:
                return {
                    "status": "unhealthy",
                    "service": "IndexTTS-2 Gradio",
                    "error": "客户端初始化失败"
                }
        except Exception as e:
            return {
                "status": "error",
                "service": "IndexTTS-2 Gradio",
                "error": str(e)
            }