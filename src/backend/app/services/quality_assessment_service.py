"""
播客质量评估服务
提供全方位的播客内容质量评估和控制功能
"""

import asyncio
import json
import re
import statistics
import os
import ssl
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from enum import Enum

import aiofiles
import numpy as np
from textstat import flesch_reading_ease, lexicon_count, syllable_count

# 【SSL修复】禁用SSL验证以支持HuggingFace模型下载
os.environ['CURL_CA_BUNDLE'] = ''
os.environ['REQUESTS_CA_BUNDLE'] = ''
ssl._create_default_https_context = ssl._create_unverified_context

try:
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
except:
    pass

from transformers import pipeline
import librosa
import soundfile as sf

class QualityLevel(Enum):
    """质量等级枚举"""
    EXCELLENT = "excellent"  # 优秀 (90-100)
    GOOD = "good"           # 良好 (80-89)
    ACCEPTABLE = "acceptable"  # 合格 (70-79)
    NEEDS_IMPROVEMENT = "needs_improvement"  # 待改进 (60-69)
    POOR = "poor"           # 不合格 (0-59)

@dataclass
class QualityMetrics:
    """质量评估指标"""
    # 内容质量维度
    content_logic: float = 0.0      # 逻辑性
    content_depth: float = 0.0      # 深度性
    content_accuracy: float = 0.0   # 准确性
    content_innovation: float = 0.0 # 创新性

    # 对话自然度维度
    dialogue_fluency: float = 0.0      # 流畅性
    dialogue_interaction: float = 0.0   # 交互性
    dialogue_consistency: float = 0.0  # 人格一致性
    dialogue_emotion: float = 0.0      # 情感表达

    # 音频质量维度
    audio_clarity: float = 0.0         # 语音清晰度
    audio_emotion: float = 0.0         # 情感表达
    audio_effects: float = 0.0         # 背景音效
    audio_technical: float = 0.0       # 技术质量

    # 用户体验维度
    user_attraction: float = 0.0       # 吸引力
    user_comprehension: float = 0.0    # 易懂性
    user_entertainment: float = 0.0    # 娱乐性
    user_value: float = 0.0            # 价值性

@dataclass
class QualityReport:
    """质量评估报告"""
    overall_score: float
    quality_level: QualityLevel
    dimension_scores: Dict[str, float]
    metrics: QualityMetrics
    issues: List[Dict[str, Any]]
    suggestions: List[str]
    timestamp: datetime
    metadata: Dict[str, Any]

class PodcastQualityAssessment:
    """播客质量评估服务"""

    def __init__(self):
        self.sentiment_analyzer = None
        self.emotion_classifier = None
        self.quality_thresholds = {
            'publish': 80.0,      # 发布阈值
            'warning': 70.0,      # 预警阈值
            'reject': 60.0        # 拒绝阈值
        }
        self.dimension_weights = {
            'content': 0.35,      # 内容质量权重
            'dialogue': 0.25,     # 对话自然度权重
            'audio': 0.25,        # 音频质量权重
            'user_experience': 0.15  # 用户体验权重
        }

    async def initialize(self):
        """初始化评估模型（已禁用 HuggingFace 模型）"""
        # 不再加载 HuggingFace 模型，使用基础评估方法
        print("质量评估服务已初始化（基础模式，无需外部模型）")
        return True

    async def assess_podcast_quality(
        self,
        script: Dict[str, Any],
        audio_path: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> QualityReport:
        """
        全面评估播客质量

        Args:
            script: 播客脚本数据
            audio_path: 音频文件路径
            metadata: 播客元数据

        Returns:
            QualityReport: 质量评估报告
        """

        # 初始化评估指标
        metrics = QualityMetrics()
        issues = []
        suggestions = []

        # 1. 内容质量评估
        content_scores = await self._assess_content_quality(script)
        metrics.content_logic = content_scores['logic']
        metrics.content_depth = content_scores['depth']
        metrics.content_accuracy = content_scores['accuracy']
        metrics.content_innovation = content_scores['innovation']

        # 2. 对话自然度评估
        dialogue_scores = await self._assess_dialogue_naturalness(script)
        metrics.dialogue_fluency = dialogue_scores['fluency']
        metrics.dialogue_interaction = dialogue_scores['interaction']
        metrics.dialogue_consistency = dialogue_scores['consistency']
        metrics.dialogue_emotion = dialogue_scores['emotion']

        # 3. 音频质量评估
        if audio_path:
            audio_scores = await self._assess_audio_quality(audio_path)
            metrics.audio_clarity = audio_scores['clarity']
            metrics.audio_emotion = audio_scores['emotion']
            metrics.audio_effects = audio_scores['effects']
            metrics.audio_technical = audio_scores['technical']
        else:
            # 基于文本预估音频质量
            estimated_scores = await self._estimate_audio_quality_from_text(script)
            metrics.audio_clarity = estimated_scores['clarity']
            metrics.audio_emotion = estimated_scores['emotion']
            metrics.audio_effects = estimated_scores['effects']
            metrics.audio_technical = estimated_scores['technical']

        # 4. 用户体验评估
        ux_scores = await self._assess_user_experience(script)
        metrics.user_attraction = ux_scores['attraction']
        metrics.user_comprehension = ux_scores['comprehension']
        metrics.user_entertainment = ux_scores['entertainment']
        metrics.user_value = ux_scores['value']

        # 5. 计算综合评分
        dimension_scores = self._calculate_dimension_scores(metrics)
        overall_score = self._calculate_overall_score(dimension_scores)

        # 6. 确定质量等级
        quality_level = self._determine_quality_level(overall_score)

        # 7. 识别问题和生成建议
        issues = self._identify_issues(metrics, script)
        suggestions = self._generate_suggestions(metrics, issues)

        # 8. 生成报告
        report = QualityReport(
            overall_score=overall_score,
            quality_level=quality_level,
            dimension_scores=dimension_scores,
            metrics=metrics,
            issues=issues,
            suggestions=suggestions,
            timestamp=datetime.now(),
            metadata=metadata or {}
        )

        return report

    async def _assess_content_quality(self, script: Dict[str, Any]) -> Dict[str, float]:
        """评估内容质量"""
        dialogues = script.get('dialogues', [])
        full_text = ' '.join([d.get('content', '') for d in dialogues])

        # 逻辑性评估
        logic_score = await self._assess_logic(dialogues)

        # 深度性评估
        depth_score = await self._assess_depth(full_text)

        # 准确性评估
        accuracy_score = await self._assess_accuracy(full_text)

        # 创新性评估
        innovation_score = await self._assess_innovation(full_text)

        return {
            'logic': logic_score,
            'depth': depth_score,
            'accuracy': accuracy_score,
            'innovation': innovation_score
        }

    async def _assess_logic(self, dialogues: List[Dict]) -> float:
        """评估对话逻辑性"""
        if not dialogues:
            return 0.0

        # 检查对话连贯性
        coherence_score = 0.0
        transition_quality = 0.0

        for i in range(1, len(dialogues)):
            prev_content = dialogues[i-1].get('content', '')
            curr_content = dialogues[i].get('content', '')

            # 简单的连贯性检查（基于关键词重叠）
            prev_keywords = set(re.findall(r'\b\w+\b', prev_content.lower()))
            curr_keywords = set(re.findall(r'\b\w+\b', curr_content.lower()))

            if prev_keywords and curr_keywords:
                overlap = len(prev_keywords & curr_keywords)
                coherence_score += overlap / max(len(prev_keywords), len(curr_keywords))

        if len(dialogues) > 1:
            coherence_score /= (len(dialogues) - 1)

        # 检查结构完整性
        structure_score = self._check_dialogue_structure(dialogues)

        # 综合评分
        logic_score = (coherence_score * 0.6 + structure_score * 0.4) * 100
        return min(100.0, max(0.0, logic_score))

    async def _assess_depth(self, text: str) -> float:
        """评估内容深度"""
        if not text:
            return 0.0

        # 词汇丰富度
        word_count = lexicon_count(text)
        unique_words = len(set(text.lower().split()))
        lexical_diversity = unique_words / word_count if word_count > 0 else 0

        # 句子复杂度
        sentences = re.split(r'[.!?]+', text)
        avg_sentence_length = statistics.mean([len(s.split()) for s in sentences if s.strip()])

        # 概念密度（专业词汇比例）
        professional_terms = self._count_professional_terms(text)
        concept_density = professional_terms / word_count if word_count > 0 else 0

        # 综合评分
        depth_score = (
            lexical_diversity * 30 +
            min(avg_sentence_length / 20, 1) * 30 +
            concept_density * 40
        )

        return min(100.0, max(0.0, depth_score))

    async def _assess_accuracy(self, text: str) -> float:
        """评估内容准确性"""
        # 这里可以集成事实检查API
        # 目前使用简单的规则检查

        accuracy_score = 85.0  # 默认分数

        # 检查明显的错误模式
        error_patterns = [
            r'可能.*错误',
            r'不确定.*准确',
            r'似乎.*不对',
            r'可能.*有误'
        ]

        for pattern in error_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                accuracy_score -= 10

        # 检查数据引用
        has_data = bool(re.search(r'\d+%|\d+年|\d+万|\d+亿', text))
        if has_data:
            accuracy_score += 5

        return min(100.0, max(0.0, accuracy_score))

    async def _assess_innovation(self, text: str) -> float:
        """评估内容创新性"""
        # 检查新颖观点的标识词
        innovation_indicators = [
            '新的角度', '独特视角', '创新思路', '颠覆性',
            '前沿', '突破', '变革', '未来',
            '重新思考', '不同的是', '换个角度'
        ]

        innovation_score = 60.0  # 基础分数

        for indicator in innovation_indicators:
            if indicator in text:
                innovation_score += 8

        # 检查问题提出
        questions = len(re.findall(r'[？?]', text))
        innovation_score += min(questions * 3, 15)

        return min(100.0, max(0.0, innovation_score))

    async def _assess_dialogue_naturalness(self, script: Dict[str, Any]) -> Dict[str, float]:
        """评估对话自然度"""
        dialogues = script.get('dialogues', [])

        # 流畅性评估
        fluency_score = await self._assess_fluency(dialogues)

        # 交互性评估
        interaction_score = await self._assess_interaction(dialogues)

        # 一致性评估
        consistency_score = await self._assess_consistency(dialogues)

        # 情感表达评估
        emotion_score = await self._assess_emotion_expression(dialogues)

        return {
            'fluency': fluency_score,
            'interaction': interaction_score,
            'consistency': consistency_score,
            'emotion': emotion_score
        }

    async def _assess_fluency(self, dialogues: List[Dict]) -> float:
        """评估对话流畅性"""
        if not dialogues:
            return 0.0

        fluency_scores = []

        for dialogue in dialogues:
            content = dialogue.get('content', '')

            # 使用阅读难易度评估
            readability = flesch_reading_ease(content)
            readability_score = min(readability / 100 * 100, 100)

            # 检查语言流畅性
            smoothness_score = self._check_language_smoothness(content)

            # 综合评分
            dialogue_fluency = (readability_score * 0.6 + smoothness_score * 0.4)
            fluency_scores.append(dialogue_fluency)

        return statistics.mean(fluency_scores) if fluency_scores else 0.0

    async def _assess_interaction(self, dialogues: List[Dict]) -> float:
        """评估对话交互性"""
        if len(dialogues) < 2:
            return 0.0

        interaction_indicators = 0
        total_pairs = 0

        for i in range(1, len(dialogues)):
            prev_dialogue = dialogues[i-1]
            curr_dialogue = dialogues[i]

            prev_speaker = prev_dialogue.get('character_name', '')
            curr_speaker = curr_dialogue.get('character_name', '')

            # 检查说话人是否不同（基本交互）
            if prev_speaker != curr_speaker:
                interaction_indicators += 1

            # 检查回应关系
            prev_content = prev_dialogue.get('content', '')
            curr_content = curr_dialogue.get('content', '')

            if self._is_response(prev_content, curr_content):
                interaction_indicators += 2

            total_pairs += 1

        interaction_score = (interaction_indicators / (total_pairs * 3)) * 100 if total_pairs > 0 else 0
        return min(100.0, max(0.0, interaction_score))

    async def _assess_consistency(self, dialogues: List[Dict]) -> float:
        """评估人格一致性"""
        # 按角色分组对话
        character_dialogues = {}
        for dialogue in dialogues:
            char_name = dialogue.get('character_name', '')
            if char_name not in character_dialogues:
                character_dialogues[char_name] = []
            character_dialogues[char_name].append(dialogue.get('content', ''))

        consistency_scores = []

        for char_name, char_dialogues in character_dialogues.items():
            if len(char_dialogues) < 2:
                continue

            # 检查语言风格一致性
            style_consistency = self._check_style_consistency(char_dialogues)
            consistency_scores.append(style_consistency)

        return statistics.mean(consistency_scores) if consistency_scores else 80.0

    async def _assess_emotion_expression(self, dialogues: List[Dict]) -> float:
        """评估情感表达"""
        if not dialogues or not self.emotion_classifier:
            return 70.0  # 默认分数

        emotion_scores = []

        for dialogue in dialogues:
            content = dialogue.get('content', '')
            if not content:
                continue

            try:
                # 使用情感分类模型
                emotion_result = self.emotion_classifier(content[:512])  # 限制长度
                confidence = emotion_result[0]['score']
                emotion_scores.append(confidence * 100)
            except Exception as e:
                print(f"情感分析失败: {e}")
                emotion_scores.append(70.0)

        return statistics.mean(emotion_scores) if emotion_scores else 70.0

    async def _assess_audio_quality(self, audio_path: str) -> Dict[str, float]:
        """评估音频质量"""
        try:
            # 加载音频文件
            y, sr = librosa.load(audio_path, sr=None)

            # 语音清晰度评估
            clarity_score = self._assess_audio_clarity(y, sr)

            # 情感表达评估
            emotion_score = self._assess_audio_emotion(y, sr)

            # 背景音效评估
            effects_score = self._assess_audio_effects(y, sr)

            # 技术质量评估
            technical_score = self._assess_audio_technical(y, sr)

            return {
                'clarity': clarity_score,
                'emotion': emotion_score,
                'effects': effects_score,
                'technical': technical_score
            }

        except Exception as e:
            print(f"音频质量评估失败: {e}")
            return {
                'clarity': 70.0,
                'emotion': 70.0,
                'effects': 70.0,
                'technical': 70.0
            }

    async def _estimate_audio_quality_from_text(self, script: Dict[str, Any]) -> Dict[str, float]:
        """基于文本预估音频质量"""
        dialogues = script.get('dialogues', [])

        # 基于文本特征预估
        total_chars = sum(len(d.get('content', '')) for d in dialogues)
        avg_dialogue_length = total_chars / len(dialogues) if dialogues else 0

        # 预估分数
        base_score = 75.0

        # 根据对话长度调整
        if avg_dialogue_length > 100:
            clarity_adjustment = 5
        elif avg_dialogue_length < 20:
            clarity_adjustment = -10
        else:
            clarity_adjustment = 0

        return {
            'clarity': base_score + clarity_adjustment,
            'emotion': base_score,
            'effects': base_score,
            'technical': base_score
        }

    async def _assess_user_experience(self, script: Dict[str, Any]) -> Dict[str, float]:
        """评估用户体验"""
        dialogues = script.get('dialogues', [])

        # 吸引力评估
        attraction_score = self._assess_attraction(dialogues)

        # 易懂性评估
        comprehension_score = self._assess_comprehension(dialogues)

        # 娱乐性评估
        entertainment_score = self._assess_entertainment(dialogues)

        # 价值性评估
        value_score = self._assess_value(dialogues)

        return {
            'attraction': attraction_score,
            'comprehension': comprehension_score,
            'entertainment': entertainment_score,
            'value': value_score
        }

    def _calculate_dimension_scores(self, metrics: QualityMetrics) -> Dict[str, float]:
        """计算各维度评分"""
        # 内容质量维度
        content_score = (
            metrics.content_logic * 0.30 +
            metrics.content_depth * 0.25 +
            metrics.content_accuracy * 0.25 +
            metrics.content_innovation * 0.20
        )

        # 对话自然度维度
        dialogue_score = (
            metrics.dialogue_fluency * 0.35 +
            metrics.dialogue_interaction * 0.30 +
            metrics.dialogue_consistency * 0.25 +
            metrics.dialogue_emotion * 0.10
        )

        # 音频质量维度
        audio_score = (
            metrics.audio_clarity * 0.40 +
            metrics.audio_emotion * 0.30 +
            metrics.audio_effects * 0.20 +
            metrics.audio_technical * 0.10
        )

        # 用户体验维度
        ux_score = (
            metrics.user_attraction * 0.35 +
            metrics.user_comprehension * 0.30 +
            metrics.user_entertainment * 0.25 +
            metrics.user_value * 0.10
        )

        return {
            'content': content_score,
            'dialogue': dialogue_score,
            'audio': audio_score,
            'user_experience': ux_score
        }

    def _calculate_overall_score(self, dimension_scores: Dict[str, float]) -> float:
        """计算综合评分"""
        overall_score = (
            dimension_scores['content'] * self.dimension_weights['content'] +
            dimension_scores['dialogue'] * self.dimension_weights['dialogue'] +
            dimension_scores['audio'] * self.dimension_weights['audio'] +
            dimension_scores['user_experience'] * self.dimension_weights['user_experience']
        )

        return round(overall_score, 2)

    def _determine_quality_level(self, overall_score: float) -> QualityLevel:
        """确定质量等级"""
        if overall_score >= 90:
            return QualityLevel.EXCELLENT
        elif overall_score >= 80:
            return QualityLevel.GOOD
        elif overall_score >= 70:
            return QualityLevel.ACCEPTABLE
        elif overall_score >= 60:
            return QualityLevel.NEEDS_IMPROVEMENT
        else:
            return QualityLevel.POOR

    def _identify_issues(self, metrics: QualityMetrics, script: Dict[str, Any]) -> List[Dict[str, Any]]:
        """识别质量问题"""
        issues = []

        # 检查各项指标
        metric_dict = asdict(metrics)

        for metric_name, score in metric_dict.items():
            if score < 60:
                issues.append({
                    'type': 'low_score',
                    'metric': metric_name,
                    'score': score,
                    'severity': 'high' if score < 40 else 'medium',
                    'description': f'{metric_name}评分过低: {score:.1f}分'
                })

        # 检查结构问题
        dialogues = script.get('dialogues', [])
        if len(dialogues) < 3:
            issues.append({
                'type': 'structure',
                'metric': 'dialogue_count',
                'severity': 'medium',
                'description': f'对话轮次过少: {len(dialogues)}轮'
            })

        return issues

    def _generate_suggestions(self, metrics: QualityMetrics, issues: List[Dict[str, Any]]) -> List[str]:
        """生成改进建议"""
        suggestions = []

        # 基于问题生成建议
        for issue in issues:
            metric = issue.get('metric', '')

            if 'content' in metric:
                suggestions.append("建议增加更多专业观点和深入分析")
            elif 'dialogue' in metric:
                suggestions.append("建议加强角色间的互动和回应")
            elif 'audio' in metric:
                suggestions.append("建议优化语音合成参数和音效配置")
            elif 'user' in metric:
                suggestions.append("建议增强内容的趣味性和实用价值")

        # 基于评分生成通用建议
        metric_dict = asdict(metrics)
        avg_score = statistics.mean(metric_dict.values())

        if avg_score < 70:
            suggestions.append("整体质量偏低，建议重新生成内容")
        elif avg_score < 80:
            suggestions.append("建议进行细节优化以提升用户体验")

        return list(set(suggestions))  # 去重

    # 辅助方法
    def _check_dialogue_structure(self, dialogues: List[Dict]) -> float:
        """检查对话结构"""
        if not dialogues:
            return 0.0

        # 检查是否有开头、发展、结尾
        has_opening = any('开始' in d.get('content', '') or '大家好' in d.get('content', '')
                         for d in dialogues[:2])
        has_conclusion = any('总结' in d.get('content', '') or '最后' in d.get('content', '')
                           for d in dialogues[-2:])

        structure_score = 0.5  # 基础分
        if has_opening:
            structure_score += 0.25
        if has_conclusion:
            structure_score += 0.25

        return structure_score * 100

    def _count_professional_terms(self, text: str) -> int:
        """统计专业术语数量"""
        # 简单的专业术语识别
        professional_patterns = [
            r'\b[A-Z]{2,}\b',  # 缩写词
            r'\b\w+系统\b',     # 系统类
            r'\b\w+技术\b',     # 技术类
            r'\b\w+模式\b',     # 模式类
            r'\b\w+理论\b',     # 理论类
        ]

        count = 0
        for pattern in professional_patterns:
            count += len(re.findall(pattern, text))

        return count

    def _check_language_smoothness(self, text: str) -> float:
        """检查语言流畅性"""
        # 检查重复词汇
        words = text.split()
        if not words:
            return 0.0

        unique_ratio = len(set(words)) / len(words)

        # 检查句子连接词
        connectors = ['因此', '所以', '但是', '然而', '而且', '另外', '首先', '其次', '最后']
        connector_count = sum(1 for conn in connectors if conn in text)
        connector_score = min(connector_count / 5, 1) * 0.3

        smoothness_score = (unique_ratio * 0.7 + connector_score) * 100
        return min(100.0, max(0.0, smoothness_score))

    def _is_response(self, prev_content: str, curr_content: str) -> bool:
        """检查是否为回应"""
        response_indicators = [
            '是的', '确实', '我认为', '不过', '但是', '对于', '关于'
        ]

        return any(indicator in curr_content for indicator in response_indicators)

    def _check_style_consistency(self, dialogues: List[str]) -> float:
        """检查语言风格一致性"""
        if len(dialogues) < 2:
            return 100.0

        # 简单的风格一致性检查
        # 检查句子长度变化
        sentence_lengths = [len(d.split()) for d in dialogues]
        length_std = statistics.stdev(sentence_lengths) if len(sentence_lengths) > 1 else 0
        length_consistency = max(0, 100 - length_std * 2)

        return length_consistency

    def _assess_audio_clarity(self, y: np.ndarray, sr: int) -> float:
        """评估音频清晰度"""
        # 计算信噪比
        rms = librosa.feature.rms(y=y)[0]
        snr = np.mean(rms) / (np.std(rms) + 1e-8)
        clarity_score = min(snr * 20, 100)

        return max(0.0, min(100.0, clarity_score))

    def _assess_audio_emotion(self, y: np.ndarray, sr: int) -> float:
        """评估音频情感表达"""
        # 计算音频特征变化
        mfccs = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13)
        mfcc_var = np.var(mfccs)
        emotion_score = min(mfcc_var * 1000, 100)

        return max(0.0, min(100.0, emotion_score))

    def _assess_audio_effects(self, y: np.ndarray, sr: int) -> float:
        """评估背景音效"""
        # 简单的音效检测
        spectral_centroid = librosa.feature.spectral_centroid(y=y, sr=sr)[0]
        effects_score = min(np.mean(spectral_centroid) / 2000 * 100, 100)

        return max(0.0, min(100.0, effects_score))

    def _assess_audio_technical(self, y: np.ndarray, sr: int) -> float:
        """评估音频技术质量"""
        # 检查音频动态范围
        dynamic_range = np.max(y) - np.min(y)
        technical_score = min(dynamic_range * 200, 100)

        return max(0.0, min(100.0, technical_score))

    def _assess_attraction(self, dialogues: List[Dict]) -> float:
        """评估吸引力"""
        if not dialogues:
            return 0.0

        # 检查开头吸引力
        first_dialogue = dialogues[0].get('content', '')
        attraction_keywords = ['有趣', '惊人', '令人', '想象', '发现', '揭秘', '探讨']

        attraction_score = 60.0  # 基础分数

        for keyword in attraction_keywords:
            if keyword in first_dialogue:
                attraction_score += 8

        # 检查问题引导
        questions = sum(1 for d in dialogues if '？' in d.get('content', '') or '?' in d.get('content', ''))
        attraction_score += min(questions * 5, 20)

        return min(100.0, max(0.0, attraction_score))

    def _assess_comprehension(self, dialogues: List[Dict]) -> float:
        """评估易懂性"""
        if not dialogues:
            return 0.0

        comprehension_scores = []

        for dialogue in dialogues:
            content = dialogue.get('content', '')
            if not content:
                continue

            # 使用阅读难度评估
            readability = flesch_reading_ease(content)
            comprehension_scores.append(readability)

        return statistics.mean(comprehension_scores) if comprehension_scores else 70.0

    def _assess_entertainment(self, dialogues: List[Dict]) -> float:
        """评估娱乐性"""
        if not dialogues:
            return 0.0

        entertainment_score = 60.0  # 基础分数

        # 检查娱乐性元素
        entertainment_keywords = ['有趣', '好玩', '搞笑', '幽默', '惊喜', '奇特', '神奇']

        for dialogue in dialogues:
            content = dialogue.get('content', '')
            for keyword in entertainment_keywords:
                if keyword in content:
                    entertainment_score += 5

        return min(100.0, max(0.0, entertainment_score))

    def _assess_value(self, dialogues: List[Dict]) -> float:
        """评估价值性"""
        if not dialogues:
            return 0.0

        value_score = 70.0  # 基础分数

        # 检查价值性元素
        value_keywords = ['学习', '启发', '思考', '建议', '方法', '经验', '教训', '收获']

        for dialogue in dialogues:
            content = dialogue.get('content', '')
            for keyword in value_keywords:
                if keyword in content:
                    value_score += 4

        return min(100.0, max(0.0, value_score))

# 质量评估服务实例
quality_assessment_service = PodcastQualityAssessment()