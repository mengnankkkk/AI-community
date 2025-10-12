"""
腾讯混元嵌入模型适配器
解决 LangChain OpenAIEmbeddings 与腾讯混元 API 格式不兼容问题
"""
import logging
from typing import List
from langchain_core.embeddings import Embeddings
import openai

logger = logging.getLogger(__name__)


class HunyuanEmbeddings(Embeddings):
    """腾讯混元嵌入模型适配器 - 兼容 OpenAI 格式"""

    def __init__(
        self,
        api_key: str,
        base_url: str,
        model: str = "hunyuan-embedding",
        dimensions: int = 1024
    ):
        """
        初始化腾讯混元嵌入模型

        Args:
            api_key: API密钥
            base_url: API基础URL
            model: 模型名称
            dimensions: 向量维度
        """
        self.api_key = api_key
        self.base_url = base_url
        self.model = model
        self.dimensions = dimensions

        # 创建 OpenAI 客户端
        self.client = openai.OpenAI(
            api_key=api_key,
            base_url=base_url
        )

        logger.info(f"腾讯混元嵌入模型初始化: {model} (维度: {dimensions})")

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """
        嵌入文档列表

        Args:
            texts: 文本列表

        Returns:
            嵌入向量列表
        """
        if not texts:
            return []

        try:
            # 过滤空文本
            valid_texts = [text.strip() for text in texts if text and text.strip()]
            if not valid_texts:
                logger.warning("所有文本为空，返回空列表")
                return []

            # 批量处理，避免单次请求过大
            batch_size = 10
            all_embeddings = []

            for i in range(0, len(valid_texts), batch_size):
                batch = valid_texts[i:i + batch_size]

                # 调用腾讯混元 API
                response = self.client.embeddings.create(
                    model=self.model,
                    input=batch  # 腾讯混元支持字符串数组
                )

                # 提取嵌入向量
                batch_embeddings = [item.embedding for item in response.data]
                all_embeddings.extend(batch_embeddings)

            logger.info(f"成功嵌入 {len(valid_texts)} 个文档片段")
            return all_embeddings

        except Exception as e:
            logger.error(f"文档嵌入失败: {str(e)}")
            raise

    def embed_query(self, text: str) -> List[float]:
        """
        嵌入查询文本

        Args:
            text: 查询文本

        Returns:
            嵌入向量
        """
        if not text or not text.strip():
            logger.warning("查询文本为空")
            return [0.0] * self.dimensions

        try:
            # 调用腾讯混元 API（单个文本也用列表格式）
            response = self.client.embeddings.create(
                model=self.model,
                input=[text.strip()]  # 使用列表格式
            )

            embedding = response.data[0].embedding
            logger.debug(f"成功嵌入查询文本: {text[:50]}...")
            return embedding

        except Exception as e:
            logger.error(f"查询嵌入失败: {str(e)}")
            raise

    async def aembed_documents(self, texts: List[str]) -> List[List[float]]:
        """异步嵌入文档列表（当前使用同步实现）"""
        return self.embed_documents(texts)

    async def aembed_query(self, text: str) -> List[float]:
        """异步嵌入查询文本（当前使用同步实现）"""
        return self.embed_query(text)
