import openai
import google.generativeai as genai
import json
import re
from typing import Dict, Any, List, Optional
from ..models.podcast import PodcastCustomForm, PodcastScript, ScriptDialogue
from ..core.config import settings
from .rag_knowledge_service import RAGKnowledgeService
from ..utils.text_cleaner import clean_for_tts


class FallbackResponse:
    """回退响应对象"""
    def __init__(self, content: str):
        self.choices = [FallbackChoice(content)]


class FallbackChoice:
    """回退选择对象"""
    def __init__(self, content: str):
        self.message = FallbackMessage(content)


class FallbackMessage:
    """回退消息对象"""
    def __init__(self, content: str):
        self.content = content


class FallbackCompletions:
    """回退聊天完成服务"""
    async def create(self, model: str, messages: List[Dict], temperature: float = 0.8, **kwargs):
        """生成回退内容"""
        # 获取用户的输入
        user_input = ""
        for message in messages:
            if message.get("role") == "user":
                user_input = message.get("content", "")
                break

        # 从输入中提取角色信息
        characters = self._extract_characters(user_input)
        topic = self._extract_topic(user_input)

        if not characters:
            characters = ["主持人", "嘉宾"]

        # 简单的模板生成逻辑
        if "开场白" in user_input or "第一轮对话" in user_input:
            content = self._generate_opening(characters, topic)
        elif "继续对话" in user_input:
            content = self._generate_continuation(characters, topic)
        elif "结束语" in user_input:
            content = self._generate_ending(characters[0])
        else:
            # 通用回复
            content = self._generate_opening(characters, topic)

        return FallbackResponse(content)

    def _extract_characters(self, user_input: str) -> List[str]:
        """从输入中提取角色名称"""
        characters = []
        lines = user_input.split('\n')

        for line in lines:
            if '**角色：**' in line:
                # 提取角色名称，例如："* **角色：** 李博士"
                parts = line.split('**角色：**')
                if len(parts) > 1:
                    char_name = parts[1].strip().split('\n')[0].strip()
                    if char_name:
                        characters.append(char_name)

        return characters[:3]  # 最多3个角色

    def _extract_topic(self, user_input: str) -> str:
        """从输入中提取主题"""
        lines = user_input.split('\n')

        for line in lines:
            if '**主题：**' in line:
                parts = line.split('**主题：**')
                if len(parts) > 1:
                    return parts[1].strip()

        return "有趣的话题"

    def _generate_opening(self, characters: List[str], topic: str) -> str:
        """生成开场白"""
        host = characters[0] if characters else "主持人"
        guest = characters[1] if len(characters) > 1 else "嘉宾"

        return f"""{{
  "dialogues": [
    {{
      "character_name": "{host}",
      "content": "欢迎大家收听今天的播客节目！今天我们要深入探讨一个非常重要的话题：{topic}。",
      "emotion": "开心"
    }},
    {{
      "character_name": "{guest}",
      "content": "谢谢邀请！{topic}确实是一个值得我们认真讨论的议题，我很高兴能在这里与大家分享我的观点。",
      "emotion": "友好"
    }},
    {{
      "character_name": "{host}",
      "content": "那么让我们先从基本概念开始聊起，您认为这个话题的核心是什么？",
      "emotion": "好奇"
    }}
  ]
}}"""

    def _generate_continuation(self, characters: List[str], topic: str) -> str:
        """生成继续对话"""
        speaker1 = characters[0] if characters else "主持人"
        speaker2 = characters[1] if len(characters) > 1 else "嘉宾"

        return f"""{{
  "dialogues": [
    {{
      "character_name": "{speaker2}",
      "content": "这个观点确实很有意思。我认为在讨论{topic}时，我们还需要考虑更多的实际因素和潜在影响。",
      "emotion": "思考"
    }},
    {{
      "character_name": "{speaker1}",
      "content": "您说得非常对！能否详细展开一下您的看法？我想听众朋友们也很感兴趣。",
      "emotion": "好奇"
    }}
  ]
}}"""

    def _generate_ending(self, host_name: str) -> str:
        """生成结束语"""
        return f"""{{
  "dialogues": [
    {{
      "character_name": "{host_name}",
      "content": "今天的讨论非常精彩，感谢各位嘉宾的深入分析，也感谢听众朋友们的收听！我们下期节目再见！",
      "emotion": "温暖"
    }}
  ]
}}"""


class FallbackClient:
    """回退客户端（用于演示和测试）"""
    def __init__(self):
        self.chat = self
        self.completions = FallbackCompletions()


class ScriptGenerator:
    def __init__(self):
        # 配置Gemini用于素材分析
        if settings.gemini_api_key:
            genai.configure(api_key=settings.gemini_api_key)

        # 配置DeepSeek用于剧本生成
        # 临时强制使用回退模式，避免Gradio Space问题
        use_gradio = False  # 强制禁用

        if use_gradio and getattr(settings, 'use_gradio_deepseek', False):
            # 使用Gradio Space模式
            try:
                from .gradio_adapter import MockOpenAIClient
                self.deepseek_client = MockOpenAIClient(
                    api_key="gradio_mode",
                    base_url="gradio_mode"
                )
                print("使用Gradio Space模式")
            except ImportError:
                print("Gradio适配器导入失败，回退到标准API模式")
                # 如果没有配置有效的DeepSeek密钥，使用一个默认的错误处理客户端
                self.deepseek_client = self._create_fallback_client()
        else:
            # 使用标准OpenAI兼容API模式或回退模式
            if settings.deepseek_api_key and settings.deepseek_api_key != "your_actual_deepseek_api_key_here":
                self.deepseek_client = openai.OpenAI(
                    api_key=settings.deepseek_api_key,
                    base_url=settings.deepseek_base_url
                )
                print("使用DeepSeek API模式")
            else:
                print("使用回退模板模式（演示用）")
                self.deepseek_client = self._create_fallback_client()

        # 初始化RAG知识库服务
        self.rag_service = RAGKnowledgeService()

        # 状态化循环生成相关属性
        self.conversation_history: List[ScriptDialogue] = []
        self.characters_list: List[str] = []
        self.current_speaker_index: int = 0
        self.target_word_count: int = 0
        self.current_word_count: int = 0

    def generate_analysis_prompt(self, materials: str) -> str:
        """生成素材分析提示词 - 针对 Gemini 2.5 Flash 优化"""
        return f"""# 任务：深度分析文本素材，为播客创作提供结构化见解

你是一位顶尖的内容分析专家和播客顾问。你将深入分析以下文本材料，提炼出适合播客讨论的核心要点、争议话题和深度问题。

## 分析方法论
采用"三层分析法"：
1. **表层分析**：提取明确陈述的事实、观点和数据
2. **深层分析**：挖掘隐含的假设、逻辑链条和潜在矛盾
3. **应用分析**：转化为引人入胜的播客讨论点

## 待分析的原始材料
---
{materials}
---

## 分析步骤（内部思考，不要输出）
1. 快速阅读全文，把握整体框架
2. 识别核心论点和支撑论据
3. 发现潜在的争议点和未解决问题
4. 构思引导深度讨论的问题
5. 提炼可供播客使用的关键信息

## 输出格式要求
**必须严格按照以下 JSON 格式输出，不要添加任何代码块标记（如 ```json）：**

{{
  "main_thesis": "用一句话（30-50字）概括文本的核心主张或结论",
  "key_arguments": [
    "支撑核心主张的关键论点1（具体、清晰、可辩论）",
    "支撑核心主张的关键论点2",
    "支撑核心主张的关键论点3",
    "如有必要，可添加第4、5个论点"
  ],
  "supporting_data_or_examples": [
    "关键数据或案例1：具体数字、引人注目的事实或生动的例子",
    "关键数据或案例2：注重可验证性和说服力",
    "关键数据或案例3"
  ],
  "potential_counterarguments": [
    "反驳观点1：从不同视角质疑核心主张",
    "逻辑漏洞1：文本中可能存在的推理问题",
    "潜在争议1：容易引发分歧的观点或假设"
  ],
  "discussion_questions": [
    "深度问题1：为什么【核心概念】会导致【某种结果】？",
    "应用问题1：这个观点如何影响【具体场景/行业/群体】？",
    "批判问题1：作者的假设【具体假设】是否成立？有哪些例外情况？",
    "展望问题1：如果【核心主张】继续发展，5年后会发生什么？"
  ],
  "podcast_hooks": [
    "开场钩子：能立即吸引听众的惊人事实或争议观点",
    "情感共鸣点：与听众日常经历相关的具体场景",
    "知识盲区：大多数人不知道但应该了解的信息"
  ]
}}

## 质量标准
- 每个要点都要具体、可操作、有洞察力
- 避免空洞的总结性语言
- 优先选择有争议性、能引发思考的内容
- 确保所有字段都有实质性内容（不少于3个条目）

现在开始分析，直接输出 JSON 结果："""

    async def analyze_materials(self, materials: str) -> Dict[str, Any]:
        """使用 Gemini 2.5 Flash 分析素材内容 - 增强版

        特性：
        - 自动重试机制（最多3次）
        - 优化的生成参数配置
        - JSON 提取和验证
        - 详细的错误日志
        - 回退机制
        """
        if not materials or not materials.strip():
            print("[分析] 素材为空，跳过分析")
            return {}

        prompt = self.generate_analysis_prompt(materials)
        max_retries = 3

        for attempt in range(max_retries):
            try:
                print(f"[分析] 第 {attempt + 1}/{max_retries} 次尝试使用 Gemini 2.5 Flash 分析素材...")

                # 配置 Gemini 2.5 Flash 的生成参数
                generation_config = {
                    "temperature": 0.4,  # 降低温度以获得更稳定的分析结果
                    "top_p": 0.95,
                    "top_k": 40,
                    "max_output_tokens": 4096,  # 允许详细的分析输出
                    "response_mime_type": "application/json",  # 强制 JSON 输出
                }

                # 使用 Gemini 进行分析
                model = genai.GenerativeModel(
                    model_name=settings.gemini_model,
                    generation_config=generation_config
                )

                response = model.generate_content(prompt)
                result_text = response.text.strip()

                print(f"[分析] Gemini 响应长度: {len(result_text)} 字符")

                # 提取 JSON（处理可能的代码块包裹）
                result_text = self._extract_json_from_response(result_text)

                # 解析 JSON
                analysis_result = json.loads(result_text)

                # 验证结果结构
                if self._validate_analysis_result(analysis_result):
                    print(f"[分析] 成功完成素材分析")
                    print(f"  - 核心主张: {analysis_result.get('main_thesis', '')[:50]}...")
                    print(f"  - 关键论点: {len(analysis_result.get('key_arguments', []))} 个")
                    print(f"  - 讨论问题: {len(analysis_result.get('discussion_questions', []))} 个")
                    if 'podcast_hooks' in analysis_result:
                        print(f"  - 播客钩子: {len(analysis_result.get('podcast_hooks', []))} 个")
                    return analysis_result
                else:
                    print(f"[分析] 第 {attempt + 1} 次结果验证失败，结构不完整")
                    if attempt < max_retries - 1:
                        print(f"[分析] 将进行重试...")
                        continue

            except json.JSONDecodeError as e:
                print(f"[分析] JSON 解析失败 (尝试 {attempt + 1}/{max_retries}): {str(e)}")
                print(f"[分析] 响应内容前500字符: {result_text[:500] if 'result_text' in locals() else 'N/A'}")
                if attempt < max_retries - 1:
                    print(f"[分析] 将进行重试...")
                    continue

            except Exception as e:
                print(f"[分析] Gemini 素材分析失败 (尝试 {attempt + 1}/{max_retries}): {str(e)}")
                print(f"[分析] 错误类型: {type(e).__name__}")
                if attempt < max_retries - 1:
                    print(f"[分析] 将进行重试...")
                    import asyncio
                    await asyncio.sleep(1)  # 等待1秒后重试
                    continue

        # 所有重试都失败，返回基础分析结果
        print(f"[分析] 所有重试均失败，返回基础分析模板")
        return self._get_fallback_analysis(materials)

    def _extract_json_from_response(self, text: str) -> str:
        """从响应中提取 JSON 内容

        处理以下情况：
        - 纯 JSON
        - ```json ... ``` 包裹的 JSON
        - ```... ``` 包裹的 JSON
        """
        text = text.strip()

        # 如果被代码块包裹，提取内容
        if text.startswith("```"):
            # 移除开头的 ```json 或 ```
            text = re.sub(r'^```(?:json)?\s*\n?', '', text)
            # 移除结尾的 ```
            text = re.sub(r'\n?```\s*$', '', text)
            text = text.strip()

        return text

    def _validate_analysis_result(self, result: Dict[str, Any]) -> bool:
        """验证分析结果的结构完整性"""
        required_fields = [
            "main_thesis",
            "key_arguments",
            "supporting_data_or_examples",
            "potential_counterarguments",
            "discussion_questions"
        ]

        for field in required_fields:
            if field not in result:
                print(f"[验证] 缺少必需字段: {field}")
                return False

            # 检查列表字段至少有一个元素
            if isinstance(result[field], list) and len(result[field]) == 0:
                print(f"[验证] 字段 {field} 为空列表")
                return False

        return True

    def _get_fallback_analysis(self, materials: str) -> Dict[str, Any]:
        """生成回退分析结果（当 Gemini 分析失败时）"""
        # 简单的关键词提取
        words = materials.split()[:100]  # 取前100个词
        preview = " ".join(words)

        return {
            "main_thesis": "基于提供的素材内容进行深入讨论",
            "key_arguments": [
                "素材中提到的核心观点和论据",
                "相关领域的专业见解",
                "实践案例和数据支撑"
            ],
            "supporting_data_or_examples": [
                f"素材摘要: {preview[:200]}...",
                "相关背景信息和上下文"
            ],
            "potential_counterarguments": [
                "不同视角的观点和质疑",
                "需要进一步验证的假设"
            ],
            "discussion_questions": [
                "这个观点的核心价值是什么？",
                "在实际应用中会遇到哪些挑战？",
                "如何评估这个观点的长期影响？"
            ],
            "podcast_hooks": [
                "引发思考的核心议题",
                "与听众相关的实际场景",
                "值得深入探讨的问题"
            ],
            "_fallback": True  # 标记这是回退结果
        }

    def _create_fallback_client(self):
        """创建回退客户端（用于演示和测试）"""
        return FallbackClient()

    def estimate_target_word_count(self, duration_str: str) -> int:
        """根据目标时长估算目标字数"""
        # 提取数字
        numbers = re.findall(r'\d+', duration_str)
        if not numbers:
            return 800  # 默认字数

        minutes = int(numbers[0])
        # 一般播客语速约为每分钟150-200字
        return minutes * 175

    def initialize_generation_state(self, form: PodcastCustomForm):
        """初始化生成状态"""
        self.conversation_history = []
        self.characters_list = [char.name for char in form.characters]
        self.current_speaker_index = 0
        self.target_word_count = self.estimate_target_word_count(form.target_duration)
        self.current_word_count = 0

    def get_next_speaker(self) -> str:
        """智能决定下一位发言者"""
        # 简单轮流策略，后续可以改为AI决定
        speaker = self.characters_list[self.current_speaker_index]
        self.current_speaker_index = (self.current_speaker_index + 1) % len(self.characters_list)
        return speaker

    def should_terminate(self) -> bool:
        """判断是否应该终止生成"""
        # 检查字数是否达到目标
        if self.current_word_count >= self.target_word_count:
            return True

        # 检查是否有明确的结束标志
        if self.conversation_history:
            last_content = self.conversation_history[-1].content
            end_keywords = ["感谢大家收听", "今天的播客", "我们下期再见", "谢谢收听"]
            if any(keyword in last_content for keyword in end_keywords):
                return True

        return False

    def count_words_in_history(self) -> int:
        """统计对话历史中的字数"""
        return sum(len(dialogue.content) for dialogue in self.conversation_history)

    def generate_initial_prompt(self, form: PodcastCustomForm, analysis_result: Dict[str, Any] = None,
                               rag_context: Dict[str, Any] = None) -> str:
        """生成初始化Prompt（开场白+第一轮对话，包含RAG知识）"""
        characters_info = []
        for char in form.characters:
            characters_info.append(
                f"* **角色：** {char.name}\n"
                f"    * **人设身份：** {char.persona}\n"
                f"    * **音色：** {char.voice_description}\n"
                f"    * **语气风格：** {char.tone_description}\n"
                f"    * **核心观点：** {char.core_viewpoint}"
            )

        characters_str = "\n".join(characters_info)

        # 构建知识参考部分
        knowledge_section = ""
        if rag_context and rag_context.get("knowledge_points"):
            knowledge_points = rag_context["knowledge_points"][:3]  # 使用前3个最相关的知识点
            knowledge_texts = []
            for point in knowledge_points:
                knowledge_texts.append(f"- {point['content'][:200]}... (来源: {point['source']})")

            knowledge_section = f"""
## 权威知识参考
以下是与主题相关的权威信息，请在对话中自然地引用和讨论：
{chr(10).join(knowledge_texts)}

请确保在讨论中：
1. 引用这些知识点时要自然，不要生硬
2. 可以对这些信息进行质疑、补充或延伸
3. 用角色的语言风格表达这些观点
"""

        analysis_section = ""
        if analysis_result:
            analysis_section = f"\n## 背景素材分析\n根据素材分析，请重点关注以下要点：\n{json.dumps(analysis_result, ensure_ascii=False, indent=2)}\n"

        return f"""# 任务：生成播客开场白和第一轮对话（基于知识库增强）

你现在是一位顶级的播客节目总监兼剧本作家。你的任务是根据以下设定，创作播客的开场白和第一轮对话。

## 播客核心设定
* **主题：** {form.topic}
* **标题：** {form.title or form.topic}
* **氛围：** {form.atmosphere.value}
* **预估时长：** {form.target_duration}

## 角色介绍
{characters_str}

{knowledge_section}

{analysis_section}

## 创作要求
1. **开场白**：由主持人角色引导，简洁介绍主题和嘉宾（约50-80字）
2. **第一轮对话**：2-3个回合的自然互动，建立讨论基础（约150-200字）
3. **互动自然**：避免独白，确保角色间真实互动
4. **人设保持**：每个角色保持其预设的人设、语气风格和观点
5. **知识融入**：如有权威知识参考，请自然融入讨论中

## ⚠️ 关键输出规则（必须严格遵守）

**emotion字段**：
- 用于标注角色的情感状态（如：开心、好奇、思考等）
- 这个字段**仅用于后期处理**，不会被朗读

**content字段**：
- **必须是纯粹的对话内容**
- **绝对不能包含**：情绪词、语气描述、舞台指示、动作描述等
- 只写角色实际说出的话

**正确示例**：
```json
{{
  "character_name": "李博士",
  "content": "欢迎大家收听今天的节目！今天我们要探讨人工智能对未来工作的影响。",
  "emotion": "开心"
}}
```

**错误示例（content中混入了提示词）**：
```json
{{
  "character_name": "李博士",
  "content": "欢迎大家收听今天的节目！今天我们要探讨人工智能对未来工作的影响。 开心",
  "emotion": "开心"
}}
```

## 输出格式
严格的JSON格式：
{{
  "dialogues": [
    {{
      "character_name": "角色名",
      "content": "纯对话内容（不含任何提示词）",
      "emotion": "情感标注"
    }}
  ]
}}

请开始创作开场白和第一轮对话："""

    def generate_continue_prompt(self, form: PodcastCustomForm, next_speaker: str,
                                rag_context: Dict[str, Any] = None) -> str:
        """生成循环Prompt（继续对话，可包含RAG知识）"""
        # 构建对话历史
        history_text = "\n".join([
            f"【{dialogue.character_name}】：{dialogue.content}" +
            (f" ({dialogue.emotion})" if dialogue.emotion else "")
            for dialogue in self.conversation_history[-6:]  # 只保留最近6轮对话
        ])

        characters_str = "、".join([char.name for char in form.characters])

        # 知识点提示（仅在有未使用的知识时添加）
        knowledge_hint = ""
        if rag_context and rag_context.get("knowledge_points"):
            unused_points = rag_context["knowledge_points"][3:6]  # 使用第4-6个知识点
            if unused_points:
                knowledge_hint = f"""
## 可参考的深度知识点
如果对话需要更深入的信息支撑，可以考虑引入：
{chr(10).join([f"- {point['content'][:150]}..." for point in unused_points])}
（请根据对话自然程度决定是否使用）
"""

        return f"""# 上下文：这是一场关于"{form.topic}"的播客，参与者有{characters_str}。以下是已进行的对话：

{history_text}

{knowledge_hint}

# 任务：请基于以上对话，自然地生成下一轮讨论。

## 要求：
- 保持角色人设和观点一致
- 推动话题深入，或引入新的子论点/观点碰撞
- 确保互动性，避免独白
- 现在请让【{next_speaker}】开始发言，然后其他角色自然回应
- 生成2-3个回合的对话
- 如有合适的知识点，可以自然地融入讨论

## ⚠️ 关键输出规则（必须严格遵守）

**emotion字段**：用于情感标注（如：开心、好奇、思考等），仅用于后期处理，不会被朗读

**content字段**：
- **必须是纯粹的对话内容**
- **绝对不能包含**：情绪词、语气描述、舞台指示、动作描述、括号标注等
- 只写角色实际说出的话

## 输出格式
严格的JSON格式：
{{
  "dialogues": [
    {{
      "character_name": "角色名",
      "content": "纯对话内容（不含任何提示词）",
      "emotion": "情感标注"
    }}
  ]
}}

请继续对话："""

    async def generate_script(self, form: PodcastCustomForm) -> PodcastScript:
        """使用状态化循环生成机制生成播客剧本（集成RAG知识检索）"""
        print(f"[DEBUG] 开始生成脚本，主题: {form.topic}")
        print(f"[DEBUG] 角色数量: {len(form.characters)}")
        print(f"[DEBUG] 使用的客户端类型: {type(self.deepseek_client).__name__}")

        # 初始化生成状态
        self.initialize_generation_state(form)
        print(f"[DEBUG] 生成状态初始化完成，目标字数: {self.target_word_count}")

        # 第一步：RAG知识检索 - 为播客内容提供深度支撑（如果启用）
        rag_context = None
        if getattr(settings, 'rag_enabled', False):
            try:
                print(f"[RAG] 正在检索相关知识: {form.topic}")
                character_names = [char.name for char in form.characters]
                rag_context = await self.rag_service.get_podcast_context(form.topic, character_names)

                if rag_context and rag_context.get("knowledge_points"):
                    print(f"[RAG] 成功获取 {len(rag_context['knowledge_points'])} 个知识点")
                else:
                    print(f"[RAG] 未找到相关知识，将使用基础生成")
            except Exception as e:
                print(f"[RAG] 知识检索失败: {str(e)}，继续基础生成")
        else:
            print("[RAG] RAG功能已禁用，使用基础生成模式")

        # 第二步：素材分析 - 如果有背景素材，先使用Gemini进行分析
        analysis_result = None
        if form.background_materials:
            print(f"[DEBUG] 开始分析背景素材...")
            analysis_result = await self.analyze_materials(form.background_materials)
            print(f"[DEBUG] 素材分析完成")

        # 第三步：生成开场白和第一轮对话
        try:
            print(f"[DEBUG] 开始生成初始对话...")
            initial_prompt = self.generate_initial_prompt(form, analysis_result, rag_context)
            print(f"[DEBUG] 初始Prompt生成完成，长度: {len(initial_prompt)}")

            print(f"[DEBUG] 调用客户端生成初始对话...")
            response = await self.deepseek_client.chat.completions.create(
                model=settings.deepseek_model,
                messages=[{"role": "user", "content": initial_prompt}],
                temperature=0.8
            )

            print(f"[DEBUG] 客户端响应收到，类型: {type(response)}")
            result_text = response.choices[0].message.content
            print(f"[DEBUG] 响应内容长度: {len(result_text)}, 前100字符: {result_text[:100]}")

            initial_data = json.loads(result_text)
            print(f"[DEBUG] JSON解析成功，对话数量: {len(initial_data.get('dialogues', []))}")

            # 添加初始对话到历史
            for dialogue_data in initial_data["dialogues"]:
                # 【重要】清理LLM生成的文本，移除可能混入的情绪标注
                original_content = dialogue_data["content"]
                cleaned_content = clean_for_tts(original_content, emotion=dialogue_data.get("emotion"))

                # 记录清理情况（便于调试）
                if cleaned_content != original_content:
                    print(f"[CLEAN] 剧本生成阶段清理: [{original_content[:50]}...] -> [{cleaned_content[:50]}...]")

                dialogue = ScriptDialogue(
                    character_name=dialogue_data["character_name"],
                    content=cleaned_content,  # 使用清理后的内容
                    emotion=dialogue_data.get("emotion")
                )
                self.conversation_history.append(dialogue)

            # 更新字数统计
            self.current_word_count = self.count_words_in_history()
            print(f"[DEBUG] 初始对话添加完成，当前字数: {self.current_word_count}")

        except Exception as e:
            print(f"[DEBUG] 初始对话生成失败: {str(e)}")
            print(f"[DEBUG] 异常类型: {type(e).__name__}")
            import traceback
            print(f"[DEBUG] 异常详细: {traceback.format_exc()}")
            raise Exception(f"初始对话生成失败: {str(e)}")

        print(f"[DEBUG] 开始循环生成对话...")
        # 第四步：循环生成对话直到满足终止条件
        max_iterations = 15  # 防止无限循环
        iteration = 0

        while not self.should_terminate() and iteration < max_iterations:
            try:
                print(f"[DEBUG] 循环第 {iteration + 1} 轮...")
                # 决定下一位发言者
                next_speaker = self.get_next_speaker()
                print(f"[DEBUG] 下一位发言者: {next_speaker}")

                # 生成继续对话的prompt（可能包含RAG知识）
                continue_prompt = self.generate_continue_prompt(form, next_speaker, rag_context)

                # 调用LLM生成下一轮对话
                response = await self.deepseek_client.chat.completions.create(
                    model=settings.deepseek_model,
                    messages=[{"role": "user", "content": continue_prompt}],
                    temperature=0.8
                )

                result_text = response.choices[0].message.content
                continue_data = json.loads(result_text)

                # 添加新对话到历史
                for dialogue_data in continue_data["dialogues"]:
                    # 【重要】清理LLM生成的文本，移除可能混入的情绪标注
                    original_content = dialogue_data["content"]
                    cleaned_content = clean_for_tts(original_content, emotion=dialogue_data.get("emotion"))

                    # 记录清理情况（便于调试）
                    if cleaned_content != original_content:
                        print(f"[CLEAN] 循环对话清理: [{original_content[:50]}...] -> [{cleaned_content[:50]}...]")

                    dialogue = ScriptDialogue(
                        character_name=dialogue_data["character_name"],
                        content=cleaned_content,  # 使用清理后的内容
                        emotion=dialogue_data.get("emotion")
                    )
                    self.conversation_history.append(dialogue)

                # 更新字数统计
                self.current_word_count = self.count_words_in_history()
                print(f"[DEBUG] 第{iteration + 1}轮完成，当前字数: {self.current_word_count}")

                iteration += 1

            except Exception as e:
                print(f"循环生成第{iteration+1}轮失败: {str(e)}")
                break

        print(f"[DEBUG] 对话循环完成，总计 {iteration} 轮")

        # 第五步：如果没有自然结束，生成结束语
        if self.conversation_history and not any(
            keyword in self.conversation_history[-1].content
            for keyword in ["感谢大家收听", "今天的播客", "我们下期再见", "谢谢收听"]
        ):
            print(f"[DEBUG] 生成结束语...")
            await self._generate_ending(form)

        # 第六步：构建最终剧本（包含RAG来源信息）
        script = PodcastScript(
            title=form.title or form.topic,
            topic=form.topic,
            dialogues=self.conversation_history
        )

        # 如果使用了RAG知识，添加到元数据
        if rag_context and rag_context.get("knowledge_points"):
            script.metadata = {
                "rag_enabled": True,
                "knowledge_sources": len(rag_context.get("source_summary", {})),
                "knowledge_points_used": len(rag_context["knowledge_points"]),
                "source_summary": rag_context.get("source_summary", {})
            }

        print(f"[DEBUG] 脚本生成完成，总对话数: {len(script.dialogues)}")
        return script

    async def _generate_ending(self, form: PodcastCustomForm):
        """生成播客结束语"""
        # 找到主持人角色（通常是第一个角色）
        host_name = self.characters_list[0] if self.characters_list else "主持人"

        ending_prompt = f"""# 任务：为播客生成简洁的结束语

这是一场关于"{form.topic}"的播客即将结束。请让【{host_name}】简洁地总结核心观点并感谢听众。

## 要求：
- 字数控制在50-80字
- 体现主题的核心价值
- 自然感谢听众和嘉宾

## ⚠️ 关键输出规则

**content字段**：必须是纯粹的对话内容，不能包含任何情绪词、语气描述等提示词

## 输出格式
{{
  "dialogues": [
    {{
      "character_name": "{host_name}",
      "content": "纯对话内容（不含任何提示词）",
      "emotion": "温暖"
    }}
  ]
}}"""

        try:
            response = await self.deepseek_client.chat.completions.create(
                model=settings.deepseek_model,
                messages=[{"role": "user", "content": ending_prompt}],
                temperature=0.7
            )

            result_text = response.choices[0].message.content
            ending_data = json.loads(result_text)

            # 添加结束语
            for dialogue_data in ending_data["dialogues"]:
                # 【重要】清理LLM生成的文本
                original_content = dialogue_data["content"]
                cleaned_content = clean_for_tts(original_content, emotion=dialogue_data.get("emotion"))

                if cleaned_content != original_content:
                    print(f"[CLEAN] 结束语清理: [{original_content[:50]}...] -> [{cleaned_content[:50]}...]")

                dialogue = ScriptDialogue(
                    character_name=dialogue_data["character_name"],
                    content=cleaned_content,  # 使用清理后的内容
                    emotion=dialogue_data.get("emotion")
                )
                self.conversation_history.append(dialogue)

        except Exception as e:
            print(f"生成结束语失败: {str(e)}")
            # 添加默认结束语
            default_ending = ScriptDialogue(
                character_name=host_name,
                content="感谢大家收听今天的播客，我们下期再见！",
                emotion="温暖"
            )
            self.conversation_history.append(default_ending)