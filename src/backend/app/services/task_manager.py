import uuid
import asyncio
import traceback
from typing import Dict, Any
from ..models.podcast import PodcastCustomForm, PodcastScript, PodcastGenerationResponse
from .script_generator import ScriptGenerator
from .tts_service import TTSService

class PodcastTask:
    def __init__(self, task_id: str, form: PodcastCustomForm):
        self.task_id = task_id
        self.form = form
        self.status = "pending"
        self.script = None
        self.audio_path = None
        self.error_message = None

class TaskManager:
    def __init__(self):
        self.tasks: Dict[str, PodcastTask] = {}
        self.script_generator = ScriptGenerator()
        self.tts_service = TTSService()

    def create_task(self, form: PodcastCustomForm) -> str:
        """创建新的播客生成任务"""
        task_id = str(uuid.uuid4())
        task = PodcastTask(task_id, form)
        self.tasks[task_id] = task

        # 异步启动任务
        asyncio.create_task(self._execute_task(task_id))

        return task_id

    async def _execute_task(self, task_id: str):
        """执行播客生成任务"""
        task = self.tasks[task_id]

        try:
            task.status = "generating_script"
            print(f"[{task_id}] 开始生成剧本...")

            # 1. 生成剧本
            try:
                print(f"[{task_id}] 调用脚本生成器...")
                script = await self.script_generator.generate_script(task.form)
                task.script = script
                print(f"[{task_id}] 剧本生成完成，共 {len(script.dialogues)} 段对话")
            except Exception as script_error:
                print(f"[{task_id}] 剧本生成异常: {str(script_error)}")
                print(f"[{task_id}] 剧本生成异常详细: {traceback.format_exc()}")
                raise script_error

            task.status = "generating_audio"

            # 2. 生成音频（带音效和BGM）
            print(f"[{task_id}] 开始生成音频...")

            # 根据设置的氛围生成音频
            atmosphere = task.form.atmosphere.value if hasattr(task.form.atmosphere, 'value') else str(task.form.atmosphere)

            try:
                audio_path = await self.tts_service.synthesize_script_audio(
                    script=script,
                    characters=task.form.characters,
                    task_id=task_id,
                    atmosphere=atmosphere,
                    enable_effects=True,  # 启用音效
                    enable_bgm=True       # 启用背景音乐
                )
                task.audio_path = audio_path
                print(f"[{task_id}] 音频生成完成: {audio_path}")
            except Exception as audio_error:
                print(f"[{task_id}] 音频生成异常: {str(audio_error)}")
                print(f"[{task_id}] 音频生成异常详细: {traceback.format_exc()}")
                raise audio_error

            # 3. 获取音频时长
            duration = self.tts_service.get_audio_duration(audio_path) if audio_path else 0
            if task.script:
                task.script.estimated_duration = duration

            task.status = "completed"
            print(f"[{task_id}] 播客生成完成！音频时长: {duration}秒")

        except Exception as e:
            task.status = "failed"
            task.error_message = str(e)
            print(f"[{task_id}] 任务失败: {str(e)}")
            print(f"[{task_id}] 任务失败详细: {traceback.format_exc()}")

    def get_task_status(self, task_id: str) -> PodcastGenerationResponse:
        """获取任务状态"""
        if task_id not in self.tasks:
            return PodcastGenerationResponse(
                task_id=task_id,
                status="not_found",
                message="任务不存在"
            )

        task = self.tasks[task_id]

        if task.status == "completed":
            audio_url = f"/api/v1/podcast/download/{task_id}" if task.audio_path else None
            return PodcastGenerationResponse(
                task_id=task_id,
                status=task.status,
                script=task.script,
                audio_url=audio_url,
                message="播客生成完成"
            )
        elif task.status == "failed":
            return PodcastGenerationResponse(
                task_id=task_id,
                status=task.status,
                message=f"生成失败: {task.error_message}"
            )
        elif task.status == "generating_script":
            return PodcastGenerationResponse(
                task_id=task_id,
                status=task.status,
                message="正在生成剧本..."
            )
        elif task.status == "generating_audio":
            return PodcastGenerationResponse(
                task_id=task_id,
                status=task.status,
                script=task.script,
                message="正在生成音频..."
            )
        else:
            return PodcastGenerationResponse(
                task_id=task_id,
                status=task.status,
                message="任务排队中..."
            )

    def get_task_audio_path(self, task_id: str) -> str:
        """获取任务的音频文件路径"""
        if task_id in self.tasks:
            return self.tasks[task_id].audio_path
        return None

# 全局任务管理器实例
task_manager = TaskManager()