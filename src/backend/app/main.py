import os
import sys

# ===== 【关键】在所有导入之前设置代理环境变量 =====
# 从环境文件加载代理配置
from dotenv import load_dotenv
load_dotenv()

# 如果启用代理，立即设置到环境变量（在任何网络请求库加载前）
if os.getenv('PROXY_ENABLED', 'false').lower() == 'true':
    http_proxy = os.getenv('HTTP_PROXY', '')
    https_proxy = os.getenv('HTTPS_PROXY', '')

    if http_proxy:
        os.environ['HTTP_PROXY'] = http_proxy
        print(f"[启动] 设置HTTP代理: {http_proxy}", file=sys.stderr)
    if https_proxy:
        os.environ['HTTPS_PROXY'] = https_proxy
        print(f"[启动] 设置HTTPS代理: {https_proxy}", file=sys.stderr)

    # 禁用SSL验证（代理环境下）
    os.environ['GRADIO_SSL_VERIFY'] = 'false'
    os.environ['CURL_CA_BUNDLE'] = ''
    os.environ['REQUESTS_CA_BUNDLE'] = ''
    print(f"[启动] 代理配置已应用", file=sys.stderr)
# ===== 代理配置结束 =====

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from .core.config import settings, create_directories
from .routes import podcast, knowledge, quality, vision, voice, voice_samples

# 创建必要的目录
create_directories()

# 创建FastAPI应用
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    debug=settings.debug
)

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 在生产环境中应该设置具体的域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(podcast.router, prefix=settings.api_prefix)
app.include_router(knowledge.router, prefix=settings.api_prefix)
app.include_router(quality.router, prefix=settings.api_prefix)
app.include_router(vision.router, prefix=settings.api_prefix)
app.include_router(voice.router, prefix=settings.api_prefix)
app.include_router(voice_samples.router, prefix=settings.api_prefix)

# 挂载静态文件服务 - 需要获取正确的项目根目录路径
import os
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
frontend_path = os.path.join(project_root, "src", "frontend")
audio_output_path = os.path.join(project_root, settings.audio_output_dir)

# 挂载前端静态文件
app.mount("/static", StaticFiles(directory=frontend_path), name="static")

# 挂载音频输出目录（用于直接访问音频文件）
if os.path.exists(audio_output_path):
    app.mount("/audio", StaticFiles(directory=audio_output_path), name="audio")

@app.get("/")
async def root():
    return {
        "message": f"欢迎使用 {settings.app_name}",
        "version": settings.app_version,
        "docs": "/docs"
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "backend.app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug
    )