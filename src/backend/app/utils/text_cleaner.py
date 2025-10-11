"""
文本清理工具
用于清理TTS文本中的舞台指示、情感标注和命令提示
"""

import re
from typing import Optional


class TextCleaner:
    """文本清理器 - 移除TTS不应该读出的内容"""

    # 预编译正则表达式提高性能
    PATTERNS = [
        # 【关键修复1】句末独立的情绪词（扩展覆盖）：如 "...影响。开心" "...观点。友好" "...内容。 热情"
        # 支持有/无空格、有/无标点的情况
        (re.compile(r'[。！？，；、]\s*(开心|悲伤|激动|平静|愤怒|惊讶|温暖|严肃|幽默|思考|轻松|紧张|焦虑|兴奋|疑惑|好奇|友好|期待|感动|欣慰|满足|骄傲|自豪|羞愧|尴尬|无奈|无聊|困惑|迷茫|坚定|犹豫|担心|害怕|恐惧|厌恶|反感|冷漠|淡然|热情|激昂|喜悦|失望|沮丧|愧疚|感激|同情|厌烦|焦躁|急切|渴望|怀疑|犹豫)\s*$'), r'\1'),

        # 【关键修复2】文本开头的情绪词："友好 大家好" "开心 今天我们要..."
        (re.compile(r'^(开心|悲伤|激动|平静|愤怒|惊讶|温暖|严肃|幽默|思考|轻松|紧张|焦虑|兴奋|疑惑|好奇|友好|期待|感动|欣慰|满足|骄傲|自豪|羞愧|尴尬|无奈|无聊|困惑|迷茫|坚定|犹豫|担心|害怕|恐惧|厌恶|反感|冷漠|淡然|热情|激昂|喜悦|失望|沮丧|愧疚|感激|同情|厌烦|焦躁|急切|渴望|怀疑|犹豫)\s+'), ''),

        # 【关键修复3】任意位置的独立情绪词（前后都有空格或标点）
        (re.compile(r'[\s。！？，；、](开心|悲伤|激动|平静|愤怒|惊讶|温暖|严肃|幽默|思考|轻松|紧张|焦虑|兴奋|疑惑|好奇|友好|期待|感动|欣慰|满足|骄傲|自豪|羞愧|尴尬|无奈|无聊|困惑|迷茫|坚定|犹豫|担心|害怕|恐惧|厌恶|反感|冷漠|淡然|热情|激昂|喜悦|失望|沮丧|愧疚|感激|同情|厌烦|焦躁|急切|渴望|怀疑|犹豫)[\s。！？，；、]'), ' '),

        # 情绪标注（括号格式）：(开心)、(激动)、(平静)等 - 句末或独立出现
        (re.compile(r'\s*[（(]\s*[\u4e00-\u9fa5]{1,4}\s*[）)]\s*(?=[。！？，；\s]|$)'), ''),

        # 括号类标注：（开心地）、(平静地)、[激动]、【思考】
        (re.compile(r'[（(][\u4e00-\u9fa5a-zA-Z]+[地的]?[）)]'), ''),
        (re.compile(r'[\[【][\u4e00-\u9fa5a-zA-Z]+[\]】]'), ''),

        # 舞台指示：<动作>、《表情》
        (re.compile(r'[<《][^>》]+[>》]'), ''),

        # 情感标签：情绪：开心
        (re.compile(r'情绪\s*[：:]\s*[\u4e00-\u9fa5]+'), ''),

        # "以X的语气/口吻/声音/方式/态度" - 精确匹配，不删除后续动词
        (re.compile(r'以[\u4e00-\u9fa5]{1,6}的(?:语气|口吻|声音|方式|态度)\s*'), ''),
        (re.compile(r'用[\u4e00-\u9fa5]{1,6}的(?:语气|口吻|声音|方式|态度)\s*'), ''),

        # "带着X说/问/答/道/讲" - 包括冒号
        (re.compile(r'带着[\u4e00-\u9fa5]{1,6}(?:说|道|讲|问|答|表示|回应)[：:]?\s*'), ''),

        # 前置情绪副词 "开心地，" 或 "平静地看着"
        (re.compile(r'^[\u4e00-\u9fa5]{1,4}[地的]\s*[，,]\s*', re.MULTILINE), ''),

        # 常见情绪词后的冒号
        (re.compile(r'^(开心|悲伤|激动|平静|愤怒|惊讶|温暖|严肃|幽默|思考|轻松|紧张|焦虑|兴奋|疑惑|好奇|友好)[：:]\s*', re.MULTILINE), ''),

        # 注释类：// 注释、# 注释
        (re.compile(r'(^|\s)//.*$', re.MULTILINE), r'\1'),
        (re.compile(r'(^|\s)#.*$', re.MULTILINE), r'\1'),

        # 特殊标记：*动作*、_强调_
        (re.compile(r'\*[^*]+\*'), ''),
        (re.compile(r'_[^_]+_'), ''),

        # 导演指示：【镜头】、【音效】等
        (re.compile(r'【[^】]+】'), ''),

        # 英文舞台指示：[Action], (whispers), <aside>
        (re.compile(r'[\[(][a-zA-Z\s]+[\])]'), ''),

        # 时间标记：[00:10]、(03:45)
        (re.compile(r'[\[(]\d{1,2}:\d{2}[\])]'), ''),

        # AI生成的元信息：```、---分隔符等
        (re.compile(r'```[\s\S]*?```'), ''),
        (re.compile(r'^-{3,}$', re.MULTILINE), ''),

        # 提示类前缀：请用...语气、注意语气等
        (re.compile(r'请用[\u4e00-\u9fa5]+[语气的]'), ''),
        (re.compile(r'注意[语气情绪]'), ''),
    ]

    @staticmethod
    def clean_text(text: str, aggressive: bool = False) -> str:
        """
        清理文本中的舞台指示和命令提示

        Args:
            text: 原始文本
            aggressive: 是否使用激进模式（可能会误删部分正常内容）

        Returns:
            清理后的文本
        """
        if not text or not isinstance(text, str):
            return ""

        cleaned = text.strip()

        # 应用所有预定义的清理规则
        for pattern, replacement in TextCleaner.PATTERNS:
            cleaned = pattern.sub(replacement, cleaned)

        # 激进模式：额外清理
        if aggressive:
            # 移除短的单词情感标记（避免误删正常词）
            cleaned = re.sub(r'\b[（(][a-zA-Z]{2,8}[）)]\b', '', cleaned)

            # 移除过于简短的标注（1-2个字的）
            cleaned = re.sub(r'[（(【\[][\u4e00-\u9fa5]{1,2}[）)】\]]', '', cleaned)

        # 清理多余的空白字符
        cleaned = re.sub(r'\s+', ' ', cleaned)
        cleaned = cleaned.strip()

        # 移除连续的标点符号
        cleaned = re.sub(r'([，。！？；])\1+', r'\1', cleaned)

        # 如果清理后为空，返回原文（避免过度清理）
        if not cleaned and text:
            return text.strip()

        return cleaned

    @staticmethod
    def clean_dialogue_text(text: str, emotion: Optional[str] = None) -> str:
        """
        清理对话文本（针对TTS优化）

        Args:
            text: 对话文本
            emotion: 情感标签（如果有，会更激进地清理情感标注）

        Returns:
            适合TTS朗读的干净文本
        """
        cleaned = TextCleaner.clean_text(text, aggressive=False)

        # 如果已经有情感标签，更激进地清理文本中的情感描述
        if emotion:
            # 移除"以...的语气"、"用...说"等
            cleaned = re.sub(r'[以用][^，。！？]{1,8}[的地][语气口吻声音方式]', '', cleaned)
            cleaned = re.sub(r'[^，。！？]{1,6}[地的]说', '', cleaned)

        # 通用清理：移除残留的情绪副词和提示
        emotion_words = (
            '开心|悲伤|激动|平静|愤怒|惊讶|温暖|严肃|幽默|思考|轻松|紧张|焦虑|兴奋|疑惑|好奇|友好|期待|感动|欣慰|满足|骄傲|自豪|羞愧|尴尬|无奈|无聊|困惑|迷茫|坚定|犹豫|担心|害怕|恐惧|厌恶|反感|冷漠|淡然|热情|激昂|喜悦|失望|沮丧|愧疚|感激|同情|厌烦|焦躁|急切|渴望|怀疑'
        )

        cleaned = re.sub(rf'(^|[，。！？；\s])({emotion_words})[地的](?=(说|讲|分享|表示|强调|提醒|回答|补充|开场|总结))', r'\1', cleaned)
        cleaned = re.sub(rf'({emotion_words})[：:]\s*', '', cleaned)
        cleaned = re.sub(r'[\u4e00-\u9fa5]{1,4}[地的](?:说|说道|回答|讲述|问道|提到|强调|补充|感叹)[：:]?\s*', '', cleaned)

        # 再次清理空白
        cleaned = re.sub(r'\s+', ' ', cleaned).strip()

        return cleaned

    @staticmethod
    def extract_emotion_hints(text: str) -> Optional[str]:
        """
        从文本中提取情感提示（用于增强TTS情感）

        Args:
            text: 原始文本

        Returns:
            提取的情感关键词，如果没有则返回None
        """
        # 常见情感关键词
        emotion_keywords = {
            '开心': ['开心', '高兴', '愉快', '喜悦', '兴奋'],
            '悲伤': ['悲伤', '难过', '伤心', '沮丧', '失落'],
            '激动': ['激动', '兴奋', '热情', '狂热'],
            '平静': ['平静', '淡定', '冷静', '从容'],
            '愤怒': ['愤怒', '生气', '恼火', '暴怒'],
            '惊讶': ['惊讶', '意外', '震惊', '诧异'],
            '温暖': ['温暖', '温柔', '亲切', '和蔼'],
            '严肃': ['严肃', '认真', '正经', '庄重'],
            '幽默': ['幽默', '搞笑', '诙谐', '风趣'],
            '思考': ['思考', '沉思', '琢磨', '考虑'],
        }

        # 在括号或标记中寻找情感词
        emotion_patterns = [
            r'[（(]([^）)]+)[）)]',
            r'[\[【]([^\]】]+)[\]】]',
        ]

        for pattern in emotion_patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                for emotion, keywords in emotion_keywords.items():
                    if any(keyword in match for keyword in keywords):
                        return emotion

        return None


# 便捷函数
def clean_for_tts(text: str, emotion: Optional[str] = None) -> str:
    """
    清理文本用于TTS（便捷函数）

    Args:
        text: 原始文本
        emotion: 情感标签（可选）

    Returns:
        清理后的文本
    """
    return TextCleaner.clean_dialogue_text(text, emotion)


# 测试用例
if __name__ == "__main__":
    test_cases = [
        "（开心地）今天天气真不错！",
        "[激动] 这太重要了，我们必须马上行动！",
        "【思考】让我想想...这个问题确实很复杂。",
        "请用平静的语气说：我们需要冷静下来分析问题。",
        "今天<微笑>我想和大家分享一个观点。",
        "（whispers）这是一个秘密。",
        "// 注释：这句话要读得慢一点",
        "开心：大家好！[00:10] 欢迎收听！",
    ]

    print("=== 文本清理测试 ===\n")
    for text in test_cases:
        cleaned = clean_for_tts(text)
        print(f"原文: {text}")
        print(f"清理: {cleaned}")
        print()