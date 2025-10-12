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
            # 定义无效的API key列表（仅占位符）
            invalid_keys = [
                "",
                "your_actual_deepseek_api_key_here",
                "your_valid_hunyuan_api_key_here",
                "your_openai_api_key_here"
            ]

            # 检查API key是否有效
            if settings.deepseek_api_key and settings.deepseek_api_key not in invalid_keys:
                try:
                    # 使用异步客户端（AsyncOpenAI）用于异步函数
                    self.deepseek_client = openai.AsyncOpenAI(
                        api_key=settings.deepseek_api_key,
                        base_url=settings.deepseek_base_url
                    )
                    print(f"[配置] 使用腾讯混元API模式（异步）")
                    print(f"[配置] Base URL: {settings.deepseek_base_url}")
                    print(f"[配置] Model: {settings.deepseek_model}")
                    print(f"[配置] API Key (前10位): {settings.deepseek_api_key[:10]}...")
                except Exception as e:
                    print(f"[错误] API客户端初始化失败: {str(e)}")
                    print("[回退] 使用模板模式")
                    self.deepseek_client = self._create_fallback_client()
            else:
                print("[配置] 未配置有效API Key，使用回退模板模式")
                self.deepseek_client = self._create_fallback_client()

        # 初始化RAG知识库服务
        self.rag_service = RAGKnowledgeService()

        # 状态化循环生成相关属性
        self.conversation_history: List[ScriptDialogue] = []
        self.characters_list: List[str] = []
        self.current_speaker_index: int = 0
        self.target_word_count: int = 0
        self.current_word_count: int = 0

        # 性能优化：缓存机制
        self._rag_cache = {}  # RAG检索结果缓存
        self._structure_cache = {}  # 结构规划缓存
        self._cache_max_size = 50  # 最大缓存条目数
        self._cache_enabled = True  # 是否启用缓存

    def _get_cache_key(self, prefix: str, *args) -> str:
        """生成缓存键"""
        import hashlib
        content = prefix + "_" + "_".join(str(arg) for arg in args)
        return hashlib.md5(content.encode()).hexdigest()

    def _get_from_cache(self, cache_dict: dict, key: str):
        """从缓存获取数据"""
        if not self._cache_enabled:
            return None
        return cache_dict.get(key)

    def _set_to_cache(self, cache_dict: dict, key: str, value: Any):
        """设置缓存数据"""
        if not self._cache_enabled:
            return

        # 简单的LRU策略：如果缓存满了，清除最旧的一半
        if len(cache_dict) >= self._cache_max_size:
            keys_to_remove = list(cache_dict.keys())[:self._cache_max_size // 2]
            for k in keys_to_remove:
                del cache_dict[k]

        cache_dict[key] = value

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

    def _calculate_knowledge_confidence(self, knowledge_point: Dict[str, Any]) -> float:
        """计算RAG知识点的置信度评分

        基于来源类型和元数据评估知识可信度：
        - 学术论文、官方文档: 0.9-1.0 (高可信度)
        - 专业网站、行业报告: 0.7-0.9 (中高可信度)
        - 一般网页、博客: 0.5-0.7 (中等可信度)
        - 社交媒体、论坛: 0.3-0.5 (低可信度)
        """
        source = knowledge_point.get("source", "").lower()
        metadata = knowledge_point.get("metadata", {})

        # 基础置信度
        base_confidence = 0.6

        # 根据来源类型调整
        if any(keyword in source for keyword in ['.pdf', 'arxiv', 'doi', 'paper', 'journal']):
            # 学术论文
            base_confidence = 0.95
        elif any(keyword in source for keyword in ['.gov', '.edu', 'official', 'documentation']):
            # 官方文档、教育机构
            base_confidence = 0.90
        elif any(keyword in source for keyword in ['wikipedia', 'wiki']):
            # 维基百科（相对可靠但需验证）
            base_confidence = 0.75
        elif any(keyword in source for keyword in ['blog', 'medium', 'zhihu', 'csdn']):
            # 技术博客、社区
            base_confidence = 0.65
        elif any(keyword in source for keyword in ['twitter', 'weibo', 'forum', 'reddit']):
            # 社交媒体、论坛
            base_confidence = 0.45

        # 根据元数据微调
        if metadata.get("type") == "file":
            # 本地文件一般是用户提供的，可信度较高
            base_confidence = min(base_confidence + 0.1, 1.0)

        # 内容长度调整（过短的内容可能不完整）
        content_length = len(knowledge_point.get("content", ""))
        if content_length < 50:
            base_confidence *= 0.8
        elif content_length > 500:
            base_confidence = min(base_confidence + 0.05, 1.0)

        return round(base_confidence, 2)

    def _validate_against_knowledge(self, dialogue_content: str,
                                   rag_context: Dict[str, Any] = None) -> Dict[str, Any]:
        """事实校验层：检测生成内容与RAG知识的冲突

        返回格式：
        {
            "is_valid": bool,          # 是否通过校验
            "confidence": float,       # 整体可信度
            "warnings": List[str],     # 警告信息
            "conflicting_facts": List  # 可能存在的冲突事实
        }
        """
        validation_result = {
            "is_valid": True,
            "confidence": 0.8,
            "warnings": [],
            "conflicting_facts": []
        }

        if not rag_context or not rag_context.get("knowledge_points"):
            # 没有RAG知识参考，默认通过
            validation_result["confidence"] = 0.6
            validation_result["warnings"].append("无RAG知识参考，无法进行事实校验")
            return validation_result

        # 提取对话中的关键数字和断言（简化版）
        import re

        # 检测数字陈述（如"增长了50%"、"有1000万用户"）
        number_statements = re.findall(r'(\d+(?:\.\d+)?%|\d+(?:万|亿|千|百)?[\u4e00-\u9fa5]{0,3})',
                                      dialogue_content)

        # 检测绝对性断言（如"一定"、"必然"、"永远"）
        absolute_words = ['一定', '必然', '绝对', '永远', '从不', '总是', '所有', '没有任何']
        has_absolute = any(word in dialogue_content for word in absolute_words)

        if has_absolute:
            validation_result["warnings"].append("检测到绝对性断言，建议保持谨慎态度")
            validation_result["confidence"] *= 0.95

        # 简化版冲突检测：检查是否包含与知识库矛盾的关键词
        # （实际应用中应使用语义相似度或专门的事实校验模型）
        knowledge_text = " ".join([
            point.get("content", "")
            for point in rag_context.get("knowledge_points", [])[:5]
        ])

        # 提取知识库中的数字
        knowledge_numbers = re.findall(r'\d+(?:\.\d+)?', knowledge_text)

        # 如果对话提到的数字过多且知识库中也有数字，可能存在冲突风险
        if len(number_statements) > 3 and len(knowledge_numbers) > 0:
            validation_result["warnings"].append(
                f"检测到{len(number_statements)}处数据陈述，建议与知识库核对"
            )
            validation_result["confidence"] *= 0.9

        # 检测否定性冲突（如对话说"不会"，但知识库说"会"）
        negative_patterns = ['不会', '不能', '没有', '无法', '不可能']
        dialogue_negatives = [word for word in negative_patterns if word in dialogue_content]

        if dialogue_negatives and len(knowledge_text) > 100:
            # 简化的冲突检测（实际应该用语义分析）
            validation_result["warnings"].append(
                f"检测到否定性表述：{', '.join(dialogue_negatives[:3])}，请确保与知识库一致"
            )

        # 计算最终置信度
        final_confidence = validation_result["confidence"]
        if len(validation_result["warnings"]) > 2:
            validation_result["is_valid"] = False
            validation_result["conflicting_facts"].append(
                "多处潜在冲突，建议人工审核"
            )

        validation_result["confidence"] = round(final_confidence, 2)

        return validation_result

    def validate_content_safety(self, content: str, rag_context: Dict[str, Any] = None) -> tuple[bool, str]:
        """内容安全验证：综合敏感词检测、事实性检查和逻辑一致性验证

        Args:
            content: 待验证的内容
            rag_context: RAG知识上下文（可选）

        Returns:
            (是否通过验证, 详细说明)
        """
        import re

        # 1. 敏感词检测（基础敏感词列表 - 生产环境建议使用专业敏感词库）
        sensitive_keywords = {
            '政治敏感': ['政治', '政府', '领导人', '党', '政策'],  # 示例，实际应更全面
            '暴力': ['暴力', '杀人', '伤害', '攻击', '暴打'],
            '色情': ['色情', '性', '裸体'],  # 示例关键词
            '歧视': ['歧视', '种族', '性别歧视', '地域歧视'],
            '谣言': ['未经证实', '据说', '听说', '传闻'],
            '商业风险': ['投资建议', '保证赚钱', '稳赚不赔', '必涨']
        }

        detected_issues = []

        # 检测敏感词（生产环境应使用更复杂的算法，如DFA或AC自动机）
        for category, keywords in sensitive_keywords.items():
            for keyword in keywords:
                if keyword in content:
                    detected_issues.append(f"检测到{category}相关内容：{keyword}")

        # 2. 事实性检查（结合RAG）
        if rag_context:
            fact_check_result = self._validate_against_knowledge(content, rag_context)
            if not fact_check_result["is_valid"]:
                detected_issues.append(f"事实性校验未通过：{', '.join(fact_check_result['warnings'])}")
            elif fact_check_result["confidence"] < 0.7:
                detected_issues.append(f"事实可信度偏低 ({fact_check_result['confidence']})")

        # 3. 逻辑一致性验证
        # 检测自相矛盾的表述（简化版）
        contradiction_patterns = [
            (r'(不会|不能|没有|无法).{0,20}(但是|然而|可是).{0,20}(会|能|有|可以)', '检测到可能的逻辑矛盾：前后表述不一致'),
            (r'(一定|必然|肯定).{0,20}(可能|也许|或许)', '检测到逻辑冲突：确定性与不确定性混用'),
            (r'(增加|上升|提高).{0,20}(减少|下降|降低)', '检测到数值矛盾：增减表述冲突'),
        ]

        for pattern, message in contradiction_patterns:
            if re.search(pattern, content):
                detected_issues.append(message)

        # 检测过于夸张的陈述
        exaggeration_keywords = ['100%', '完全', '绝对', '所有', '从不', '永远', '必然']
        exaggeration_count = sum(1 for keyword in exaggeration_keywords if keyword in content)
        if exaggeration_count > 2:
            detected_issues.append(f"检测到过多绝对化表述（{exaggeration_count}处），可能缺乏客观性")

        # 判断是否通过
        is_safe = len(detected_issues) == 0

        if is_safe:
            return True, "内容安全验证通过"
        else:
            return False, "内容安全问题：" + "; ".join(detected_issues)

    async def _plan_dialogue_structure(self, form: PodcastCustomForm,
                                     rag_context: Dict[str, Any] = None,
                                     analysis_result: Dict[str, Any] = None) -> Dict[str, Any]:
        """结构化内容生成 - 第一阶段：规划对话结构

        生成播客对话的整体结构框架，包括：
        - 各个讨论阶段的划分
        - 每个阶段的目标、字数、参与角色
        - 关键讨论点和转折点

        Args:
            form: 播客定制表单
            rag_context: RAG知识上下文
            analysis_result: Gemini素材分析结果

        Returns:
            结构化的对话规划字典
        """
        # 生成缓存键
        cache_key = self._get_cache_key(
            "structure",
            form.topic,
            form.target_duration,
            len(form.characters),
            form.atmosphere.value
        )

        # 尝试从缓存获取
        cached_structure = self._get_from_cache(self._structure_cache, cache_key)
        if cached_structure:
            print(f"[结构规划] 使用缓存的结构规划")
            return cached_structure

        print(f"[结构规划] 开始生成对话结构...")

        # 计算总目标字数
        target_word_count = self.estimate_target_word_count(form.target_duration)

        # 构建角色信息
        characters_info = [char.name for char in form.characters]
        host_name = characters_info[0] if characters_info else "主持人"

        # 构建知识要点（如果有）
        knowledge_highlights = []
        if rag_context and rag_context.get("knowledge_points"):
            knowledge_highlights = [
                point.get("content", "")[:100] for point in rag_context["knowledge_points"][:3]
            ]

        # 构建素材要点（如果有）
        material_highlights = []
        if analysis_result:
            if analysis_result.get("main_thesis"):
                material_highlights.append(f"核心观点：{analysis_result['main_thesis']}")
            if analysis_result.get("key_arguments"):
                material_highlights.extend(analysis_result["key_arguments"][:2])

        # 生成结构规划Prompt
        structure_prompt = f"""# 任务：为播客生成结构化对话规划

## 播客信息
- 主题：{form.topic}
- 时长目标：{form.target_duration} ({target_word_count}字左右)
- 氛围：{form.atmosphere.value}
- 主持人：{host_name}
- 嘉宾：{', '.join(characters_info[1:])}

## 可用素材
{chr(10).join(['- ' + h for h in knowledge_highlights + material_highlights]) if knowledge_highlights or material_highlights else '暂无额外素材'}

## 任务要求
请设计一个**结构化的对话流程**，将整个播客分为5-7个阶段，每个阶段包含：
1. 阶段名称和目标
2. 预计字数（总计{target_word_count}字）
3. 讨论重点/关键问题
4. 参与角色和互动方式

## 输出格式（JSON）
{{
  "total_target_words": {target_word_count},
  "total_stages": 6,
  "stages": [
    {{
      "stage_number": 1,
      "stage_name": "开场欢迎",
      "target_words": 150,
      "objectives": ["主持人自我介绍", "介绍嘉宾", "引入话题"],
      "discussion_points": ["今天的主题是什么", "为什么重要"],
      "participants": ["{host_name}"],
      "interaction_style": "主持人独白+简短嘉宾回应"
    }},
    {{
      "stage_number": 2,
      "stage_name": "话题引入",
      "target_words": 200,
      "objectives": ["提出核心问题", "嘉宾表明立场"],
      "discussion_points": ["核心问题是什么", "各自的初步观点"],
      "participants": ["{host_name}", "{characters_info[1] if len(characters_info) > 1 else '嘉宾'}"],
      "interaction_style": "问答互动"
    }},
    {{
      "stage_number": 3,
      "stage_name": "深入讨论",
      "target_words": 300,
      "objectives": ["深入阐述各自观点", "提供案例支撑"],
      "discussion_points": ["具体案例分析", "数据或事实支撑"],
      "participants": ["{', '.join(characters_info)}"],
      "interaction_style": "轮流阐述+主持人追问"
    }},
    {{
      "stage_number": 4,
      "stage_name": "观点碰撞",
      "target_words": 250,
      "objectives": ["不同观点交锋", "辩论和回应"],
      "discussion_points": ["争议焦点", "各方立场差异"],
      "participants": ["{', '.join(characters_info)}"],
      "interaction_style": "辩论式互动"
    }},
    {{
      "stage_number": 5,
      "stage_name": "总结与展望",
      "target_words": 150,
      "objectives": ["总结关键观点", "未来展望"],
      "discussion_points": ["核心结论", "未来趋势"],
      "participants": ["{host_name}"],
      "interaction_style": "主持人总结"
    }},
    {{
      "stage_number": 6,
      "stage_name": "致谢结束",
      "target_words": 100,
      "objectives": ["感谢嘉宾", "感谢听众", "道别"],
      "discussion_points": ["致谢", "预告下期"],
      "participants": ["{', '.join(characters_info)}"],
      "interaction_style": "集体道别"
    }}
  ],
  "key_transitions": [
    "从引入到深入：主持人提出关键追问",
    "从讨论到碰撞：引入争议话题或反对观点",
    "从碰撞到总结：主持人梳理共识与分歧"
  ],
  "quality_checkpoints": [
    "每个阶段是否有具体案例或数据",
    "嘉宾之间是否有真实互动",
    "是否避免空洞的套话"
  ]
}}

**注意**：
- 直接输出JSON，不要用```包裹
- stages数组长度为5-7个
- 每个阶段target_words总和应约等于{target_word_count}
- discussion_points要具体且与主题相关

现在生成结构规划："""

        try:
            # 调用LLM生成结构规划
            response = await self.deepseek_client.chat.completions.create(
                model=settings.deepseek_model,
                messages=[{"role": "user", "content": structure_prompt}],
                temperature=0.5  # 较低温度确保结构合理
            )

            result_text = response.choices[0].message.content.strip()

            # 清理JSON
            if "```json" in result_text:
                result_text = result_text.split("```json")[1].split("```")[0].strip()
            elif "```" in result_text:
                result_text = result_text.split("```")[1].split("```")[0].strip()

            # 解析结构规划
            structure_plan = json.loads(result_text)

            print(f"[结构规划] 生成成功，共{structure_plan.get('total_stages', 0)}个阶段")
            for stage in structure_plan.get('stages', [])[:3]:
                print(f"  阶段{stage['stage_number']}: {stage['stage_name']} ({stage['target_words']}字)")

            # 缓存结果
            self._set_to_cache(self._structure_cache, cache_key, structure_plan)

            return structure_plan

        except Exception as e:
            print(f"[结构规划] 生成失败: {str(e)}")
            # 返回默认结构
            fallback_structure = self._get_fallback_structure(target_word_count, characters_info)
            # 缓存默认结构
            self._set_to_cache(self._structure_cache, cache_key, fallback_structure)
            return fallback_structure

    def _get_fallback_structure(self, target_word_count: int, characters: List[str]) -> Dict[str, Any]:
        """生成默认的对话结构（当LLM规划失败时）"""
        host_name = characters[0] if characters else "主持人"

        return {
            "total_target_words": target_word_count,
            "total_stages": 6,
            "stages": [
                {
                    "stage_number": 1,
                    "stage_name": "开场欢迎",
                    "target_words": int(target_word_count * 0.15),
                    "objectives": ["主持人开场", "介绍嘉宾"],
                    "discussion_points": ["今天的话题介绍"],
                    "participants": [host_name],
                    "interaction_style": "主持人独白"
                },
                {
                    "stage_number": 2,
                    "stage_name": "话题引入",
                    "target_words": int(target_word_count * 0.20),
                    "objectives": ["引入核心话题", "嘉宾表态"],
                    "discussion_points": ["核心问题阐述"],
                    "participants": characters,
                    "interaction_style": "问答互动"
                },
                {
                    "stage_number": 3,
                    "stage_name": "深入讨论",
                    "target_words": int(target_word_count * 0.30),
                    "objectives": ["深入阐述观点"],
                    "discussion_points": ["案例分析", "数据支撑"],
                    "participants": characters,
                    "interaction_style": "轮流发言"
                },
                {
                    "stage_number": 4,
                    "stage_name": "观点交流",
                    "target_words": int(target_word_count * 0.20),
                    "objectives": ["观点碰撞"],
                    "discussion_points": ["不同视角对比"],
                    "participants": characters,
                    "interaction_style": "互动辩论"
                },
                {
                    "stage_number": 5,
                    "stage_name": "总结",
                    "target_words": int(target_word_count * 0.10),
                    "objectives": ["总结要点"],
                    "discussion_points": ["核心结论"],
                    "participants": [host_name],
                    "interaction_style": "主持人总结"
                },
                {
                    "stage_number": 6,
                    "stage_name": "结束",
                    "target_words": int(target_word_count * 0.05),
                    "objectives": ["致谢道别"],
                    "discussion_points": ["感谢收听"],
                    "participants": characters,
                    "interaction_style": "集体道别"
                }
            ],
            "key_transitions": ["引入话题", "深入讨论", "总结收尾"],
            "quality_checkpoints": ["是否有具体案例", "是否有真实互动"],
            "_fallback": True
        }

    async def _generate_stage_content(self, stage_info: Dict[str, Any],
                                     form: PodcastCustomForm,
                                     rag_context: Dict[str, Any] = None) -> List[ScriptDialogue]:
        """结构化内容生成 - 第二阶段：基于结构规划生成具体对话内容

        Args:
            stage_info: 当前阶段的结构信息
            form: 播客定制表单
            rag_context: RAG知识上下文

        Returns:
            生成的对话列表
        """
        print(f"[阶段生成] 开始生成阶段{stage_info['stage_number']}: {stage_info['stage_name']}")

        # 构建角色人设信息
        characters_personas = []
        for char in form.characters:
            if char.name in stage_info.get('participants', []):
                persona = self.generate_character_persona_prompt(char)
                characters_personas.append(persona)

        # 构建已有对话上下文（最近3轮）
        recent_history = ""
        if self.conversation_history:
            recent_dialogues = self.conversation_history[-3:]
            recent_history = "\n".join([
                f"{d.character_name}：{d.content[:50]}..."
                for d in recent_dialogues
            ])

        # 构建RAG知识参考（如果有）
        rag_section = ""
        if rag_context and rag_context.get("knowledge_points"):
            knowledge_items = []
            for point in rag_context["knowledge_points"][:2]:
                confidence = self._calculate_knowledge_confidence(point)
                marker = "🟢" if confidence >= 0.8 else "🟡"
                knowledge_items.append(f"{marker} {point['content'][:150]}...")

            rag_section = f"""
## 📚 可参考知识（自然融入）
{chr(10).join(knowledge_items)}
"""

        # 生成本阶段的对话Prompt
        stage_prompt = f"""# 任务：生成播客第{stage_info['stage_number']}阶段的对话内容

## 阶段目标
- **阶段名称**：{stage_info['stage_name']}
- **目标字数**：{stage_info['target_words']}字
- **核心目标**：{', '.join(stage_info['objectives'])}
- **讨论重点**：{', '.join(stage_info['discussion_points'])}
- **互动方式**：{stage_info['interaction_style']}

## 播客信息
- 主题：{form.topic}
- 氛围：{form.atmosphere.value}

## 参与角色人设
{chr(10).join(characters_personas)}

## 已有对话（上下文）
{recent_history if recent_history else "这是播客的第一阶段"}

{rag_section}

## 🎭 对话生成要求

**【必须遵守的核心准则】**
1. **观点必须配案例**：每个观点都要有具体案例、数据或故事支撑
2. **真实口语化**：用"其实"、"你看"、"说实话"等口语词，有停顿感
3. **互动回应**：角色之间要真实互动，追问、质疑、补充
4. **避免空洞套话**：禁止"非常精彩"、"很有道理"等敷衍话术

**【字数控制】**
- 生成{max(2, stage_info['target_words'] // 80)}段对话
- 每段60-100字
- 总字数约{stage_info['target_words']}字

## ⚠️ 输出格式（JSON）

{{
  "dialogues": [
    {{
      "character_name": "角色名",
      "content": "对话内容（纯文本，不含情绪标注）",
      "emotion": "情绪词"
    }}
  ]
}}

**注意**：
- 直接输出JSON，不要用```包裹
- content必须是纯文本，不含括号标注
- 生成的对话要符合阶段目标和字数要求

现在生成本阶段对话："""

        try:
            # 调用LLM生成本阶段内容
            response = await self.deepseek_client.chat.completions.create(
                model=settings.deepseek_model,
                messages=[{"role": "user", "content": stage_prompt}],
                temperature=0.7
            )

            result_text = response.choices[0].message.content.strip()

            # 清理JSON
            if "```json" in result_text:
                result_text = result_text.split("```json")[1].split("```")[0].strip()
            elif "```" in result_text:
                result_text = result_text.split("```")[1].split("```")[0].strip()

            result_text = result_text.replace('\n', '\\n').replace('\r', '\\r').replace('\t', '\\t')
            result_text = re.sub(r'\\n\s*\\n', '\\n', result_text)

            # 解析JSON
            stage_data = json.loads(result_text)

            # 转换为对话对象列表
            dialogues = []
            for dialogue_data in stage_data["dialogues"]:
                # 清理内容
                original_content = dialogue_data["content"]
                cleaned_content = clean_for_tts(original_content, emotion=dialogue_data.get("emotion"))

                # 内容安全检查
                is_safe, safety_message = self.validate_content_safety(cleaned_content, rag_context)
                if not is_safe:
                    print(f"[阶段生成] ⚠️ 内容安全问题: {safety_message}")
                    # 生产环境可以选择跳过
                    # continue

                dialogue = ScriptDialogue(
                    character_name=dialogue_data["character_name"],
                    content=cleaned_content,
                    emotion=dialogue_data.get("emotion")
                )
                dialogues.append(dialogue)

            word_count = sum(len(d.content) for d in dialogues)
            print(f"[阶段生成] 阶段{stage_info['stage_number']}生成完成，共{len(dialogues)}段对话，{word_count}字")

            return dialogues

        except Exception as e:
            print(f"[阶段生成] 生成失败: {str(e)}")
            return []

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

    def check_content_repetition(self, new_content: str, window_size: int = 3) -> bool:
        """检查新内容是否与最近的对话重复

        Args:
            new_content: 新生成的内容
            window_size: 检查最近几轮对话

        Returns:
            True表示有重复，False表示无重复
        """
        if not self.conversation_history:
            return False

        # 获取最近几轮对话
        recent_dialogues = self.conversation_history[-window_size:]

        # 计算相似度（简单的字符串包含检查）
        new_content_clean = new_content.strip().lower()

        for dialogue in recent_dialogues:
            old_content_clean = dialogue.content.strip().lower()

            # 如果新内容与旧内容过于相似（超过50%重复）
            if len(new_content_clean) > 20:  # 只检查足够长的内容
                overlap = sum(1 for i in range(len(new_content_clean)-10)
                            if new_content_clean[i:i+10] in old_content_clean)
                similarity = overlap / (len(new_content_clean) - 10) if len(new_content_clean) > 10 else 0

                if similarity > 0.5:  # 50%以上相似度认为重复
                    return True

        return False

    def count_words_in_history(self) -> int:
        """统计对话历史中的字数"""
        return sum(len(dialogue.content) for dialogue in self.conversation_history)

    def generate_character_persona_prompt(self, char) -> str:
        """根据三层角色构建法生成详细的人设描述"""

        # 第一层：核心身份（必填）
        persona_text = f"**{char.name}**：{char.persona}，观点是{char.core_viewpoint}"

        # 第二层：深度构建（可选）
        depth_parts = []

        # 背景故事
        if char.backstory or char.backstory_impact:
            depth_parts.append("\n  - 背景：")
            if char.backstory:
                depth_parts.append(f"{char.backstory}")
            if char.backstory_impact:
                depth_parts.append(f"（{char.backstory_impact}）")

        # 沟通风格
        communication_style = []
        if char.language_habits:
            communication_style.append(f"语言习惯：{char.language_habits}")
        if char.catchphrases:
            communication_style.append(f"口头禅：{char.catchphrases}")
        if char.speech_pace:
            communication_style.append(f"语速特点：{char.speech_pace}")

        if communication_style:
            depth_parts.append("\n  - 沟通风格：" + "；".join(communication_style))

        # 内在价值观与矛盾
        if char.core_values:
            depth_parts.append(f"\n  - 价值观：{char.core_values}")
        if char.inner_contradictions:
            depth_parts.append(f"\n  - 内在矛盾：{char.inner_contradictions}")

        # 隐藏动机
        if char.hidden_motivation:
            depth_parts.append(f"\n  - 隐藏动机：{char.hidden_motivation}")

        # 组合完整描述
        if depth_parts:
            persona_text += "".join(depth_parts)

        return persona_text

    def generate_initial_prompt(self, form: PodcastCustomForm, analysis_result: Dict[str, Any] = None,
                               rag_context: Dict[str, Any] = None) -> str:
        """生成初始化Prompt - 整合三层角色构建法，优化播客结构"""
        # 使用新的角色人设生成方法
        characters_info = []
        host_name = None
        guest_names = []

        for char in form.characters:
            char_desc = f"* {self.generate_character_persona_prompt(char)}"
            characters_info.append(char_desc)

            # 识别主持人（第一个角色默认为主持人）
            if not host_name:
                host_name = char.name
            else:
                guest_names.append(char.name)

        characters_str = "\n".join(characters_info)

        # 如果没有明确的主持人，使用第一个角色
        if not host_name:
            host_name = self.characters_list[0] if self.characters_list else "主持人"

        # 构建嘉宾列表文本
        guests_intro = "、".join(guest_names) if guest_names else "嘉宾"

        # 构建知识参考部分
        knowledge_section = ""
        if rag_context and rag_context.get("knowledge_points"):
            knowledge_points = rag_context["knowledge_points"][:2]
            knowledge_texts = [f"- {point['content'][:150]}..." for point in knowledge_points]
            knowledge_section = f"\n### 可参考的知识\n{chr(10).join(knowledge_texts)}\n"

        analysis_section = ""
        if analysis_result and analysis_result.get('main_thesis'):
            analysis_section = f"\n### 素材要点\n核心观点：{analysis_result['main_thesis']}\n"

        return f"""你是专业播客剧本作家。请为以下播客生成**完整的开场部分**，包括主持人开场、介绍嘉宾和引入话题。

## 基本信息
主题：{form.topic}
氛围：{form.atmosphere.value}
主持人：{host_name}
嘉宾：{guests_intro}

## 角色设定
{characters_str}

{knowledge_section}{analysis_section}

## 🎙️ 播客开场结构要求

**第1段 - 主持人开场白**：
- {host_name}自我介绍，欢迎听众
- 简要说明今天的主题：{form.topic}
- 营造{form.atmosphere.value}的氛围

**第2段 - 介绍嘉宾**：
- {host_name}介绍每位嘉宾的身份、专业背景
- 突出嘉宾在该话题上的专长

**第3-4段 - 引入核心话题**：
- {host_name}提出核心问题或论点
- 嘉宾简要回应，表明各自观点
- 为后续深入讨论铺垫

## 🎭 对话风格（核心要求 - 强制执行）

**1. 严格依据角色深度人设：**
- 如果角色有"背景故事"，必须在对话中自然融入相关经历或案例
- 如果角色有"语言习惯"或"口头禅"，必须在对话中体现
- 如果角色有"内在矛盾"，可在适当时候暗示或流露

**2. 【强制】观点必须配案例/故事：**
- ❌ 禁止干巴巴陈述："新能源车确实有问题，消费者很担心。"
- ✅ 必须有具体案例："去年我们处理过一起电池热失控的客诉，车主半夜被消防吵醒，整个人都吓傻了。虽然最后查出来不是质量问题，但这事儿对一个家庭的冲击太大了。"

**3. 案例必须具体到细节：**
- 必须有数字（如"20人质检组→2台设备"）
- 必须有场景（如"半夜"、"工厂车间"、"质检组"）
- 必须有情感冲击（如"整个人都吓傻了"、"这对我触动很大"）

**4. 真实对话质感：**
- 多用"我觉得"、"其实"、"说实话"、"你看"等口语连接词
- 可以有停顿、转折、自我修正（如"不对，应该说..."）
- 用比喻、类比让抽象观点变具体

## ⚠️ 输出格式（严格遵守）

{{
  "dialogues": [
    {{
      "character_name": "{host_name}",
      "content": "主持人开场白内容（纯文本）",
      "emotion": "热情"
    }},
    {{
      "character_name": "{host_name}",
      "content": "介绍嘉宾的内容",
      "emotion": "友好"
    }},
    {{
      "character_name": "{host_name}",
      "content": "提出核心话题",
      "emotion": "好奇"
    }},
    {{
      "character_name": "{guest_names[0] if guest_names else '嘉宾'}",
      "content": "嘉宾回应",
      "emotion": "思考"
    }}
  ]
}}

注意：
- 直接输出JSON，不要用```包裹
- content必须是纯文本，不含特殊字符
- 生成4-5段开场对话

现在生成开场："""

    def generate_continue_prompt(self, form: PodcastCustomForm, next_speaker: str,
                                rag_context: Dict[str, Any] = None) -> str:
        """生成循环Prompt - 引导嘉宾深入讨论各自观点（集成RAG知识支持）"""
        # 构建对话历史（只保留最近4轮）
        history_text = "\n".join([
            f"{dialogue.character_name}：{dialogue.content}"
            for dialogue in self.conversation_history[-4:]
        ])

        # 构建RAG知识参考部分
        rag_knowledge_section = ""
        if rag_context and rag_context.get("knowledge_points"):
            # 获取相关的知识点（最多3个）
            relevant_knowledge = rag_context["knowledge_points"][:3]
            if relevant_knowledge:
                knowledge_items = []
                for idx, point in enumerate(relevant_knowledge, 1):
                    # 添加置信度标记（基于source类型）
                    confidence = self._calculate_knowledge_confidence(point)
                    confidence_marker = "🟢" if confidence >= 0.8 else "🟡" if confidence >= 0.6 else "🟠"
                    knowledge_items.append(
                        f"{idx}. {confidence_marker} {point['content'][:200]}..."
                        f"\n   来源: {point.get('source', 'unknown')}"
                    )

                rag_knowledge_section = f"""
## 📚 知识库参考（可选引用，增强论述深度）
{chr(10).join(knowledge_items)}

**使用指引**：
- 如果上述知识与当前讨论相关，可自然融入对话（不要生硬引用）
- 可以挑战或质疑知识库内容，保持批判性思维
- 绿色🟢=高可信度，黄色🟡=中等可信度，橙色🟠=需验证
"""

        # 计算进度
        progress_ratio = self.current_word_count / self.target_word_count if self.target_word_count > 0 else 0

        # 识别主持人和嘉宾
        host_name = self.characters_list[0] if self.characters_list else "主持人"
        is_host = (next_speaker == host_name)

        # 根据进度给出内容建议
        if progress_ratio < 0.3:
            stage_hint = "展开讨论"
            if is_host:
                content_guide = "主持人引导嘉宾深入阐述各自观点，可以提出具体问题"
            else:
                content_guide = f"{next_speaker}详细阐述自己的观点，可以举例说明"
        elif progress_ratio < 0.7:
            stage_hint = "观点碰撞"
            if is_host:
                content_guide = "主持人促进嘉宾之间的互动，引导观点交锋或补充"
            else:
                content_guide = f"{next_speaker}回应其他人的观点，可以表示认同或提出不同看法"
        else:
            stage_hint = "准备收尾"
            if is_host:
                content_guide = "主持人开始引导向结论，梳理关键观点"
            else:
                content_guide = f"{next_speaker}总结自己的核心观点"

        # 获取最近的发言内容，用于引导互动
        last_speaker = ""
        last_content_snippet = ""
        if self.conversation_history:
            last_dialogue = self.conversation_history[-1]
            last_speaker = last_dialogue.character_name
            last_content_snippet = last_dialogue.content[:80] + "..." if len(last_dialogue.content) > 80 else last_dialogue.content

        interaction_guide = ""
        if last_speaker and last_speaker != next_speaker:
            interaction_guide = f"""
## 🎯【核心规则1：回应与反驳】必须基于前一发言进行互动
上一位发言者（{last_speaker}）说了："{last_content_snippet}"

**{next_speaker}的发言必须遵循"乒乓球规则"：**

1. **开头必须直接回应**（选择其一）：
   - 认同并补充："对，{last_speaker}说的这个我深有感触/完全同意。我还想补充的是..."
   - 部分认同并转折："您说的XX这点我认同，但关于XX，我有不同看法..."
   - 质疑并反驳："您提到的XX，我有个疑问/我觉得可能不完全是这样。您看..."
   - 追问深挖："您刚才说的XX特别有意思，能不能展开说说？比如..."

2. **严禁自说自话**：
   - ❌ 禁止："我认为XX是个问题。"（完全无视{last_speaker}的发言）
   - ✅ 必须："您刚才提到XX，这让我想到我们公司去年的一个案例..."

3. **制造思想碰撞**：
   - 如果{last_speaker}提供了案例，{next_speaker}必须追问细节或提出质疑
   - 如果{last_speaker}提出了观点，{next_speaker}必须表态（支持/反对/补充）
"""

        return f"""继续播客对话。当前进度：{self.current_word_count}/{self.target_word_count}字

## 已有对话（最近4轮）
{history_text}
{rag_knowledge_section}
{interaction_guide}
## 下一步生成
- 当前阶段：{stage_hint}
- 下一位发言者：【{next_speaker}】
- 内容方向：{content_guide}
- 生成2-3段对话

## 🎭 对话要求（核心准则 - 三大铁律）

**【铁律1：观点必须配案例】**
- ❌ 绝对禁止："我认为成本是个问题。"（纯观点陈述）
- ✅ 强制要求：观点 + 具体案例（含数字、场景、情感）
- 示例："说到成本，去年我朋友买电动车花了20万，现在电池衰减到60%，他说感觉像买了个'到期食品'，三年贬值一半。这谁受得了？"

**【铁律2：必须回应前一发言】**
- ❌ 严禁各说各话："我认为AI会创造新岗位。"（无视对方）
- ✅ 强制开头回应："您刚才说的那个质检组案例，我特别有共鸣。我们公司去年..."
- 必须使用的互动句式：
  * 追问："您提到XX，能详细说说那19个员工后来怎么样了吗？"
  * 质疑："但我有个疑问，您说的新岗位，真能弥补失去的那么多传统岗位吗？"
  * 补充："对，我完全同意。而且我还想补充的是..."

**【铁律3：追问深挖，制造思想火花】**
- 当对方分享案例时，必须追问背后的细节或引申问题
- 示例对话流：
  * A："我们工厂20人质检组被2台设备替代了。"
  * B：【必须追问】"那19个人后来怎么办的？转岗成功率高吗？"
  * A：【必须回应】"说实话，只有3-4个成功转岗，剩下的..."
  * B：【必须深挖】"这就是我担心的！3-4个成功率太低了，这说明..."

**【铁律4：真实口语化】**
- 用"你看"、"其实"、"说白了"、"说实话"开头
- 有停顿感："这个事情……怎么说呢……""不对，应该这么说..."

## ⚠️ 输出格式

{{
  "dialogues": [
    {{
      "character_name": "{next_speaker}",
      "content": "对话内容",
      "emotion": "思考"
    }}
  ]
}}

注意：直接输出JSON，不要用```包裹

现在生成："""

    async def generate_script(self, form: PodcastCustomForm) -> PodcastScript:
        """使用状态化循环生成机制生成播客剧本（集成RAG知识检索）"""
        print(f"[DEBUG] 开始生成脚本，主题: {form.topic}")
        print(f"[DEBUG] 角色数量: {len(form.characters)}")
        print(f"[DEBUG] 使用的客户端类型: {type(self.deepseek_client).__name__}")

        # 初始化生成状态
        self.initialize_generation_state(form)
        print(f"[DEBUG] 生成状态初始化完成，目标字数: {self.target_word_count}")

        # 第一步+第二步：并行执行RAG知识检索和Gemini素材分析（性能优化）
        rag_context = None
        analysis_result = None

        # 准备并行任务
        parallel_tasks = []

        # 任务1：RAG知识检索
        async def rag_task():
            """RAG知识检索任务"""
            if not getattr(settings, 'rag_enabled', False):
                print("[RAG] RAG功能已禁用")
                return None

            try:
                await self.rag_service.ensure_ready()
                print(f"[RAG] 正在检索相关知识: {form.topic}")
                character_names = [char.name for char in form.characters]
                context = await self.rag_service.get_podcast_context(form.topic, character_names)

                if context and context.get("knowledge_points"):
                    print(f"[RAG] 成功获取 {len(context['knowledge_points'])} 个知识点")
                else:
                    print(f"[RAG] 未找到相关知识")
                return context
            except Exception as e:
                print(f"[RAG] 知识检索失败: {str(e)}")
                return None

        # 任务2：Gemini素材分析
        async def analysis_task():
            """Gemini素材分析任务"""
            if not form.background_materials:
                print("[分析] 无背景素材，跳过分析")
                return None

            try:
                print(f"[分析] 开始分析背景素材...")
                result = await self.analyze_materials(form.background_materials)
                print(f"[分析] 素材分析完成")
                return result
            except Exception as e:
                print(f"[分析] 素材分析失败: {str(e)}")
                return None

        # 判断需要执行哪些任务
        tasks_to_run = []
        task_names = []

        if getattr(settings, 'rag_enabled', False):
            tasks_to_run.append(rag_task())
            task_names.append("RAG检索")

        if form.background_materials:
            tasks_to_run.append(analysis_task())
            task_names.append("素材分析")

        # 并行执行所有任务（如果有多个任务）
        if len(tasks_to_run) > 1:
            print(f"[并行] 开始并行执行: {', '.join(task_names)}")
            import asyncio
            results = await asyncio.gather(*tasks_to_run, return_exceptions=True)

            # 分配结果
            result_index = 0
            if getattr(settings, 'rag_enabled', False):
                rag_context = results[result_index] if not isinstance(results[result_index], Exception) else None
                result_index += 1

            if form.background_materials:
                analysis_result = results[result_index] if not isinstance(results[result_index], Exception) else None

            print(f"[并行] 并行任务完成")
        elif len(tasks_to_run) == 1:
            # 只有一个任务，直接执行
            result = await tasks_to_run[0]
            if getattr(settings, 'rag_enabled', False):
                rag_context = result
            elif form.background_materials:
                analysis_result = result
        else:
            print("[INFO] 无需执行RAG检索或素材分析")

        # 第三步：生成开场白和第一轮对话
        try:
            print(f"[DEBUG] 开始生成初始对话...")
            initial_prompt = self.generate_initial_prompt(form, analysis_result, rag_context)
            print(f"[DEBUG] 初始Prompt生成完成，长度: {len(initial_prompt)}")

            print(f"[DEBUG] 调用客户端生成初始对话...")
            response = await self.deepseek_client.chat.completions.create(
                model=settings.deepseek_model,
                messages=[{"role": "user", "content": initial_prompt}],
                temperature=0.7  # 降低temperature，减少随机性和重复
            )

            print(f"[DEBUG] 客户端响应收到，类型: {type(response)}")
            result_text = response.choices[0].message.content
            print(f"[DEBUG] 响应内容长度: {len(result_text)}, 前100字符: {result_text[:100]}")

            # 清理JSON字符串（移除控制字符和修复格式）
            result_text = result_text.strip()

            # 提取JSON部分（如果LLM输出了额外的文本）
            if "```json" in result_text:
                # 移除markdown代码块标记
                result_text = result_text.split("```json")[1].split("```")[0].strip()
            elif "```" in result_text:
                result_text = result_text.split("```")[1].split("```")[0].strip()

            # 替换控制字符为转义序列
            import re
            # 替换未转义的换行符、制表符等
            result_text = result_text.replace('\n', '\\n').replace('\r', '\\r').replace('\t', '\\t')
            # 但要保留JSON结构中的换行
            result_text = re.sub(r'\\n\s*\\n', '\\n', result_text)  # 合并多余换行

            print(f"[DEBUG] 清理后的JSON前200字符: {result_text[:200]}")

            try:
                initial_data = json.loads(result_text)
            except json.JSONDecodeError as je:
                print(f"[DEBUG] JSON解析失败，尝试修复...")
                # 尝试移除所有换行和多余空格
                result_text_clean = re.sub(r'\\[nrt]', ' ', result_text)
                result_text_clean = re.sub(r'\s+', ' ', result_text_clean)
                print(f"[DEBUG] 再次尝试解析，清理后: {result_text_clean[:200]}")
                try:
                    initial_data = json.loads(result_text_clean)
                except:
                    print(f"[DEBUG] 完整响应内容:\n{result_text}")
                    raise je  # 重新抛出原始错误

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
                    temperature=0.7  # 降低temperature，减少随机性
                )

                result_text = response.choices[0].message.content.strip()

                # 清理JSON（同初始对话）
                if "```json" in result_text:
                    result_text = result_text.split("```json")[1].split("```")[0].strip()
                elif "```" in result_text:
                    result_text = result_text.split("```")[1].split("```")[0].strip()

                result_text = result_text.replace('\n', '\\n').replace('\r', '\\r').replace('\t', '\\t')
                result_text = re.sub(r'\\n\s*\\n', '\\n', result_text)

                try:
                    continue_data = json.loads(result_text)
                except json.JSONDecodeError:
                    result_text_clean = re.sub(r'\\[nrt]', ' ', result_text)
                    result_text_clean = re.sub(r'\s+', ' ', result_text_clean)
                    continue_data = json.loads(result_text_clean)

                # 添加新对话到历史（带去重检查、事实校验和安全守护）
                for dialogue_data in continue_data["dialogues"]:
                    # 【重要】清理LLM生成的文本，移除可能混入的情绪标注
                    original_content = dialogue_data["content"]
                    cleaned_content = clean_for_tts(original_content, emotion=dialogue_data.get("emotion"))

                    # 【新增】检查内容重复
                    if self.check_content_repetition(cleaned_content):
                        print(f"[WARN] 检测到重复内容，跳过: {cleaned_content[:50]}...")
                        continue

                    # 【新增】内容安全守护
                    is_safe, safety_message = self.validate_content_safety(cleaned_content, rag_context)
                    if not is_safe:
                        print(f"[SAFETY] ⚠️ 内容安全验证失败")
                        print(f"[SAFETY]   - 问题: {safety_message}")
                        # 当前策略：记录警告但仍然保留内容（生产环境建议跳过）
                        # continue  # 取消注释此行以在检测到安全问题时跳过内容

                    # 【新增】RAG事实校验层
                    if rag_context and rag_context.get("knowledge_points"):
                        validation_result = self._validate_against_knowledge(cleaned_content, rag_context)
                        if not validation_result["is_valid"]:
                            print(f"[FACT-CHECK] ⚠️ 内容未通过事实校验")
                            print(f"[FACT-CHECK]   - 置信度: {validation_result['confidence']}")
                            print(f"[FACT-CHECK]   - 警告: {validation_result['warnings']}")
                            print(f"[FACT-CHECK]   - 冲突: {validation_result['conflicting_facts']}")
                            # 当前策略：记录警告但仍然保留内容（可根据需要调整为跳过）
                        elif validation_result["warnings"]:
                            print(f"[FACT-CHECK] ℹ️ 检测到 {len(validation_result['warnings'])} 个提示")
                            for warning in validation_result['warnings'][:2]:  # 只显示前2个
                                print(f"[FACT-CHECK]   - {warning}")

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
        """生成播客结束语 - 优化为主持人总结+集体道别"""
        # 找到主持人角色（第一个角色）
        host_name = self.characters_list[0] if self.characters_list else "主持人"

        # 构建所有角色列表用于集体道别
        all_characters = self.characters_list if self.characters_list else ["主持人"]

        ending_prompt = f"""# 任务：为播客生成专业的结束部分

这是一场关于"{form.topic}"的播客即将结束。

## 结束流程要求

**第1段 - 主持人总结**：
- {host_name}总结今天讨论的核心观点
- 提炼2-3个关键要点
- 字数控制在60-80字

**第2段 - 主持人致谢**：
- {host_name}感谢各位嘉宾的精彩分享
- 感谢听众的收听

**第3段 - 集体道别**：
- {host_name}引导大家一起和听众道别
- 所有人（{', '.join(all_characters)}）一起说"再见"或"拜拜"
- 营造温馨的结束氛围

## 🎭 对话质感要求

**1. 真诚而非套路：**
- ❌ 禁止："今天的讨论非常精彩"（空洞客套）
- ✅ 必须："今天聊下来，我自己也有不少收获。尤其是王经理提到的那个电池案例，真的让人深思。"（真诚具体）

**2. 自然口语化：**
- 用"其实"、"说实话"、"今天真的"等口语连接词
- 可以有停顿感："这个问题……嗯……确实值得我们继续关注"

## ⚠️ 输出格式（严格遵守）

{{
  "dialogues": [
    {{
      "character_name": "{host_name}",
      "content": "总结核心观点的内容",
      "emotion": "认真"
    }},
    {{
      "character_name": "{host_name}",
      "content": "感谢嘉宾和听众",
      "emotion": "温暖"
    }},
    {{
      "character_name": "{host_name}",
      "content": "好的，让我们一起和听众朋友们说再见吧！",
      "emotion": "开心"
    }}
  ]
}}

注意：
- 直接输出JSON，不要用```包裹
- content必须是纯文本
- 生成3段结束对话
- 最后一段要自然引导集体道别

现在生成结束语："""

        try:
            response = await self.deepseek_client.chat.completions.create(
                model=settings.deepseek_model,
                messages=[{"role": "user", "content": ending_prompt}],
                temperature=0.6  # 结束语更稳定
            )

            result_text = response.choices[0].message.content.strip()

            # 清理JSON（同初始对话）
            if "```json" in result_text:
                result_text = result_text.split("```json")[1].split("```")[0].strip()
            elif "```" in result_text:
                result_text = result_text.split("```")[1].split("```")[0].strip()

            result_text = result_text.replace('\n', '\\n').replace('\r', '\\r').replace('\t', '\\t')
            result_text = re.sub(r'\\n\s*\\n', '\\n', result_text)

            try:
                ending_data = json.loads(result_text)
            except json.JSONDecodeError:
                result_text_clean = re.sub(r'\\[nrt]', ' ', result_text)
                result_text_clean = re.sub(r'\s+', ' ', result_text_clean)
                ending_data = json.loads(result_text_clean)

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

            # 生成集体道别
            print(f"[DEBUG] 生成集体道别...")
            await self._generate_group_farewell()

        except Exception as e:
            print(f"生成结束语失败: {str(e)}")
            # 添加默认结束语
            default_ending = ScriptDialogue(
                character_name=host_name,
                content="感谢大家收听今天的播客，我们下期再见！",
                emotion="温暖"
            )
            self.conversation_history.append(default_ending)

    async def _generate_group_farewell(self):
        """生成集体道别环节"""
        # 所有角色一起说再见
        all_characters = self.characters_list if self.characters_list else ["主持人"]

        farewell_prompt = f"""# 任务：生成集体道别环节

播客即将结束，所有人要一起和听众道别。

## 角色列表
{', '.join(all_characters)}

## 要求
- 每个角色都要说一句简短的道别语
- 可以是"再见"、"拜拜"、"下期见"等
- 要自然、温馨
- 按顺序：{' → '.join(all_characters)}

## ⚠️ 输出格式

{{
  "dialogues": [
    {{
      "character_name": "{all_characters[0]}",
      "content": "再见，各位听众朋友！",
      "emotion": "开心"
    }}
  ]
}}

注意：
- 直接输出JSON，不要用```包裹
- 生成{len(all_characters)}段道别语
- 每人一句，简短温馨

现在生成："""

        try:
            response = await self.deepseek_client.chat.completions.create(
                model=settings.deepseek_model,
                messages=[{"role": "user", "content": farewell_prompt}],
                temperature=0.6
            )

            result_text = response.choices[0].message.content.strip()

            # 清理JSON
            if "```json" in result_text:
                result_text = result_text.split("```json")[1].split("```")[0].strip()
            elif "```" in result_text:
                result_text = result_text.split("```")[1].split("```")[0].strip()

            result_text = result_text.replace('\n', '\\n').replace('\r', '\\r').replace('\t', '\\t')
            result_text = re.sub(r'\\n\s*\\n', '\\n', result_text)

            try:
                farewell_data = json.loads(result_text)
            except json.JSONDecodeError:
                result_text_clean = re.sub(r'\\[nrt]', ' ', result_text)
                result_text_clean = re.sub(r'\s+', ' ', result_text_clean)
                farewell_data = json.loads(result_text_clean)

            # 添加集体道别
            for dialogue_data in farewell_data["dialogues"]:
                original_content = dialogue_data["content"]
                cleaned_content = clean_for_tts(original_content, emotion=dialogue_data.get("emotion"))

                dialogue = ScriptDialogue(
                    character_name=dialogue_data["character_name"],
                    content=cleaned_content,
                    emotion=dialogue_data.get("emotion")
                )
                self.conversation_history.append(dialogue)

            print(f"[DEBUG] 集体道别生成完成")

        except Exception as e:
            print(f"生成集体道别失败: {str(e)}")
            # 添加默认道别
            for character in all_characters:
                default_farewell = ScriptDialogue(
                    character_name=character,
                    content="再见！",
                    emotion="开心"
                )
                self.conversation_history.append(default_farewell)