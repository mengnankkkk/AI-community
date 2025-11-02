import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # 应用配置
    app_name: str = "AI Virtual Podcast Studio"
    app_version: str = "1.0.0"
    debug: bool = True

    # API配置
    api_prefix: str = "/api/v1"
    host: str = "0.0.0.0"
    port: int = 8000

    # 大模型API配置
    openai_api_key: str = ""
    openai_base_url: str = "https://api.openai.com/v1"

    # Gemini配置 - 用于素材分析
    gemini_api_key: str = ""
    gemini_base_url: str = "https://generativelanguage.googleapis.com/v1beta"
    gemini_model: str = "gemini-2.5-flash"

    # LLM配置 - 用于剧本生成（支持OpenAI兼容接口，如DeepSeek、腾讯混元等）
    deepseek_api_key: str = ""
    deepseek_base_url: str = "https://api.hunyuan.cloud.tencent.com/v1"  # 默认使用腾讯混元
    deepseek_model: str = "hunyuan-turbos-latest"  # 腾讯混元模型

    # Gradio Space配置（可选，用于自部署的DeepSeek）
    use_gradio_deepseek: bool = False
    gradio_space_name: str = "Mengnankk/deepseek-ai-DeepSeek-V3.1-test"

    # TTS配置
    tts_api_key: str = ""
    tts_model: str = "tts-1"
    tts_engine: str = "indextts2_gradio"  # 可选: "qwen3_tts", "nihal_tts", "indextts2_gradio", "indextts2", "openai"

    # Qwen3-TTS配置
    qwen3_tts_space: str = "Qwen/Qwen3-TTS-Demo"

    # NihalGazi-TTS配置
    nihal_tts_space: str = "NihalGazi/Text-To-Speech-Unlimited"

    # IndexTTS2 Gradio配置
    indextts2_gradio_space: str = "IndexTeam/IndexTTS-2-Demo"

    # AliCloud CosyVoice配置
    alicloud_dashscope_api_key: str = ""
    alicloud_dashscope_api_secret: str = ""  # 用于音色克隆功能
    cosyvoice_model: str = "cosyvoice-v2"
    cosyvoice_default_voice: str = "longxiaochun_v2"
    cosyvoice_enable_clone: bool = True  # 是否启用音色克隆功能

    # FFmpeg配置（音频处理）
    ffmpeg_path: str = ""
    ffprobe_path: str = ""

    # 代理配置（用于访问HuggingFace等国际服务）
    proxy_enabled: bool = False
    proxy_type: str = "http"
    http_proxy: str = ""
    https_proxy: str = ""

    # IndexTTS2配置（本地模型）
    indextts_model_dir: str = "checkpoints"
    indextts_voice_samples_dir: str = "voice_samples"
    indextts_emotion_samples_dir: str = "emotion_samples"
    indextts_use_fp16: bool = True
    indextts_use_cuda_kernel: bool = False

    # Hunyuan Vision配置 - 用于图片分析
    hunyuan_api_key: str = ""
    hunyuan_base_url: str = "https://hunyuan.tencentcloudapi.com"
    hunyuan_vision_model: str = "hunyuan-turbos-vision"

    # RAG知识库配置
    rag_enabled: bool = True  # 启用RAG知识库深度集成
    rag_chunk_size: int = 1000
    rag_chunk_overlap: int = 200
    rag_max_search_results: int = 5

    # 嵌入模型配置（支持腾讯混元）
    rag_embedding_provider: str = "hunyuan"  # openai 或 hunyuan
    rag_embedding_model: str = "hunyuan-embedding"
    rag_embedding_api_key: str = ""
    rag_embedding_base_url: str = "https://api.hunyuan.cloud.tencent.com/v1"
    rag_embedding_dimensions: int = 1024

    knowledge_base_dir: str = "data/knowledge_base"
    vector_store_dir: str = "data/knowledge_base/chroma_db"

    # RAG自动导入配置
    rag_auto_ingest: bool = False  # 是否自动导入知识库文件
    rag_auto_ingest_patterns: str = "**/*.txt,**/*.md,**/*.pdf"  # 自动导入文件匹配模式（逗号分隔）
    rag_max_initial_files: int = 100  # 最大自动导入文件数量（0为不限制）

    # 文件存储配置
    audio_output_dir: str = "data/output/audio"
    max_file_size: int = 50 * 1024 * 1024  # 50MB
    uploads_dir: str = "data/uploads"
    outputs_dir: str = "data/output"
    temp_dir: str = "data/temp"
    logs_dir: str = "data/output/logs"

    # Docker配置
    compose_project_name: str = "ai-podcast-studio"
    cors_origins: str = "http://localhost:3000,http://127.0.0.1:3000"

    # Redis配置
    redis_url: str = "redis://localhost:6379/0"
    redis_max_connections: int = 10

    # ChromaDB配置
    chroma_host: str = "localhost"
    chroma_port: int = 8001
    chroma_collection_name: str = "podcast_knowledge"
    anonymized_telemetry: bool = False

    # 性能配置
    worker_processes: int = 1
    worker_connections: int = 1000
    max_requests: int = 1000
    timeout: int = 30

    # 播客生成配置
    enable_audio_generation: bool = False  # 是否生成音频（设为False只生成剧本）
    task_worker_count: int = 2  # 任务工作线程数

    class Config:
        env_file = ".env"
        case_sensitive = False

settings = Settings()

# 确保必要的目录存在
def create_directories():
    # 获取项目根目录（从 src/backend/app/core/ 回到根目录）
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(current_dir))))

    directories = [
        os.path.join(project_root, settings.audio_output_dir),
        os.path.join(project_root, settings.logs_dir),
        os.path.join(project_root, settings.indextts_model_dir),
        os.path.join(project_root, settings.indextts_voice_samples_dir),
        os.path.join(project_root, settings.indextts_emotion_samples_dir),
        os.path.join(project_root, settings.knowledge_base_dir),
        os.path.join(project_root, settings.vector_store_dir),
        os.path.join(project_root, settings.uploads_dir),
        os.path.join(project_root, "assets/audio/effects"),
        os.path.join(project_root, "assets/audio/background_music"),
        os.path.join(project_root, "data/temp")
    ]

    for directory in directories:
        os.makedirs(directory, exist_ok=True)