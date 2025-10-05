#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Gradio Space DeepSeek API适配器
用于将Gradio Space API适配到OpenAI兼容的接口
"""

import asyncio
from gradio_client import Client
from typing import Dict, Any, List
import json

class GradioDeepSeekAdapter:
    """Gradio Space DeepSeek API适配器"""

    def __init__(self, space_name: str = "Mengnankk/deepseek-ai-DeepSeek-V3.1-test"):
        self.space_name = space_name
        self.client = None
        self.chat_endpoint = None

    async def initialize(self):
        """初始化客户端并检测可用端点"""
        try:
            self.client = Client(self.space_name)

            # 获取API信息
            api_info = self.client.view_api(return_format='dict')

            print(f"API信息: {api_info}")  # 调试信息

            # 查找聊天相关的端点
            endpoints = []
            if 'named_endpoints' in api_info:
                endpoints = list(api_info['named_endpoints'].keys())
                print(f"所有可用端点: {endpoints}")

                # 优先查找聊天相关端点
                chat_keywords = ['chat', 'predict', 'generate', 'completion', 'inference', 'text', 'model']
                for endpoint_name in endpoints:
                    endpoint_lower = endpoint_name.lower()
                    if any(keyword in endpoint_lower for keyword in chat_keywords):
                        if not endpoint_lower.startswith('/_'):  # 避免内部端点
                            self.chat_endpoint = endpoint_name
                            break

            # 如果没有找到明确的聊天端点，尝试使用第一个非内部端点
            if not self.chat_endpoint:
                for endpoint in endpoints:
                    if not endpoint.startswith('/_'):  # 避免内部端点
                        self.chat_endpoint = endpoint
                        break

            # 如果还是没有找到，使用第一个端点
            if not self.chat_endpoint and endpoints:
                self.chat_endpoint = endpoints[0]

            print(f"已连接到Gradio Space: {self.space_name}")
            print(f"使用端点: {self.chat_endpoint}")

            if not self.chat_endpoint:
                print("警告: 未找到合适的API端点")
                return False

            return True

        except Exception as e:
            print(f"初始化Gradio适配器失败: {e}")
            return False

    async def chat_completions_create(self, messages: List[Dict], model: str, temperature: float = 0.8, **kwargs):
        """
        模拟OpenAI chat completions API
        """
        if not self.client or not self.chat_endpoint:
            raise Exception("Gradio客户端未初始化")

        try:
            # 将消息转换为适合Gradio的格式
            prompt = self._messages_to_prompt(messages)
            print(f"发送到Gradio的提示词: {prompt[:200]}...")  # 调试信息

            # 调用Gradio端点
            print(f"调用端点: {self.chat_endpoint}")
            result = self.client.predict(
                prompt,
                api_name=self.chat_endpoint
            )

            print(f"Gradio返回结果类型: {type(result)}")
            print(f"Gradio返回结果内容: {str(result)[:500]}...")

            # 检查返回结果
            if result is None or result == "":
                raise Exception("Gradio返回空结果")

            # 将结果转换为OpenAI格式
            content = str(result) if result else "生成失败，请稍后重试"

            response = {
                "choices": [{
                    "message": {
                        "content": content
                    }
                }]
            }

            return MockResponse(response)

        except Exception as e:
            print(f"Gradio API调用失败: {e}")

            # 返回包含错误信息的响应，而不是抛出异常
            error_content = f"""抱歉，AI服务暂时不可用。请稍后重试。

技术细节：{str(e)}

如果问题持续存在，请检查：
1. 网络连接是否正常
2. Gradio Space是否可访问
3. API端点配置是否正确"""

            response = {
                "choices": [{
                    "message": {
                        "content": error_content
                    }
                }]
            }
            return MockResponse(response)

    def _messages_to_prompt(self, messages: List[Dict]) -> str:
        """将OpenAI消息格式转换为简单提示词"""
        prompt_parts = []

        for message in messages:
            role = message.get("role", "")
            content = message.get("content", "")

            if role == "system":
                prompt_parts.append(f"System: {content}")
            elif role == "user":
                prompt_parts.append(f"User: {content}")
            elif role == "assistant":
                prompt_parts.append(f"Assistant: {content}")
            else:
                prompt_parts.append(content)

        return "\n".join(prompt_parts)


class MockResponse:
    """模拟OpenAI响应对象"""
    def __init__(self, data):
        self.choices = [MockChoice(choice) for choice in data.get("choices", [])]


class MockChoice:
    """模拟OpenAI选择对象"""
    def __init__(self, choice_data):
        self.message = MockMessage(choice_data.get("message", {}))


class MockMessage:
    """模拟OpenAI消息对象"""
    def __init__(self, message_data):
        self.content = message_data.get("content", "")


# 全局适配器实例
gradio_adapter = GradioDeepSeekAdapter()


class MockOpenAIClient:
    """模拟OpenAI客户端，实际调用Gradio Space"""

    def __init__(self, api_key: str, base_url: str):
        self.api_key = api_key  # 在Gradio模式下不使用
        self.base_url = base_url  # 在Gradio模式下不使用
        self.chat = self
        self.completions = self

    async def create(self, model: str, messages: List[Dict], temperature: float = 0.8, **kwargs):
        """创建聊天补全"""
        # 确保适配器已初始化
        if not gradio_adapter.client:
            success = await gradio_adapter.initialize()
            if not success:
                raise Exception("Gradio适配器初始化失败")

        return await gradio_adapter.chat_completions_create(
            messages=messages,
            model=model,
            temperature=temperature,
            **kwargs
        )