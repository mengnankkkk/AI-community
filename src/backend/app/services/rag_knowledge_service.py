import os
import asyncio
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from urllib.parse import urlparse
import aiohttp
import json

from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.docstore.document import Document
from langchain.chains import RetrievalQA
from langchain_community.llms import OpenAI

import requests
from bs4 import BeautifulSoup
from pypdf import PdfReader  # 使用 pypdf 而不是 PyPDF2（pypdf是PyPDF2的继任者）
from docx import Document as DocxDocument

from ..core.config import settings
from .hunyuan_embeddings import HunyuanEmbeddings
from .web_scraper_service import WebScraperService

logger = logging.getLogger(__name__)

class RAGKnowledgeService:
    """RAG知识库检索服务"""

    def __init__(self):
        # 修复：从 src/backend/app/services/rag_knowledge_service.py 向上4级到项目根目录
        # parents[0] = services, [1] = app, [2] = backend, [3] = src, [4] = 项目根目录
        self.project_root = Path(__file__).resolve().parents[4]
        self.knowledge_base_dir = (self.project_root / settings.knowledge_base_dir).resolve()
        self.vector_store_dir = (self.project_root / settings.vector_store_dir).resolve()

        # 创建必要目录
        os.makedirs(self.knowledge_base_dir, exist_ok=True)
        os.makedirs(self.vector_store_dir, exist_ok=True)

        # 初始化嵌入模型（支持OpenAI和腾讯混元）
        if settings.rag_embedding_provider == "hunyuan":
            # 使用腾讯混元嵌入模型专用适配器
            self.embeddings = HunyuanEmbeddings(
                api_key=settings.rag_embedding_api_key,
                base_url=settings.rag_embedding_base_url,
                model=settings.rag_embedding_model,  # hunyuan-embedding
                dimensions=settings.rag_embedding_dimensions  # 1024
            )
            logger.info(f"使用腾讯混元嵌入模型: {settings.rag_embedding_model} (维度: {settings.rag_embedding_dimensions})")
        else:
            # 默认使用OpenAI嵌入模型
            self.embeddings = OpenAIEmbeddings(
                openai_api_key=settings.openai_api_key,
                openai_api_base=settings.openai_base_url
            )
            logger.info("使用OpenAI嵌入模型: text-embedding-ada-002")

        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,          # 每个片段1000字符
            chunk_overlap=200,        # 片段重叠200字符
            separators=["\n\n", "\n", "。", ".", " ", ""]
        )

        # 向量数据库
        self.vectorstore = None
        self.retriever = None
        self._initial_corpus_loaded = False
        self._load_lock = None
        self._auto_patterns = [pattern.strip() for pattern in settings.rag_auto_ingest_patterns.split(',') if pattern.strip()]

        # 支持的文件类型
        self.supported_extensions = {'.txt', '.md', '.pdf', '.docx', '.json'}

        # 初始化网页抓取服务
        self.web_scraper = WebScraperService()

    async def initialize_vectorstore(self):
        """初始化向量数据库"""
        try:
            self.vectorstore = Chroma(
                persist_directory=str(self.vector_store_dir),
                embedding_function=self.embeddings
            )
            self.retriever = self.vectorstore.as_retriever(
                search_type="similarity",
                search_kwargs={"k": 5}  # 返回最相关的5个片段
            )
            logger.info("向量数据库初始化成功")

            if settings.rag_auto_ingest:
                await self._load_initial_corpus()

            return True
        except Exception as e:
            logger.error(f"向量数据库初始化失败: {str(e)}")
            return False

    async def ensure_ready(self):
        """确保向量数据库和初始语料准备就绪"""
        if not self.vectorstore:
            await self.initialize_vectorstore()
            return

        if settings.rag_auto_ingest and not self._initial_corpus_loaded:
            await self._load_initial_corpus()

    async def _load_initial_corpus(self):
        """加载默认知识库目录下的文件"""
        if self._initial_corpus_loaded:
            return

        if self._load_lock is None:
            self._load_lock = asyncio.Lock()

        async with self._load_lock:
            if self._initial_corpus_loaded:
                return

            files = self._discover_initial_files()
            if not files:
                logger.info("未发现可自动导入的知识库文件")
                self._initial_corpus_loaded = True
                return

            logger.info(f"开始自动导入知识库文件，共 {len(files)} 个候选")

            imported = 0
            max_files = max(0, settings.rag_max_initial_files)

            for file_path in files:
                if max_files and imported >= max_files:
                    logger.info(f"达到自动导入上限 {max_files}，停止加载")
                    break

                success = await self.add_knowledge_from_file(str(file_path))
                if success:
                    imported += 1

            logger.info(f"自动导入完成，共成功导入 {imported} 个文件")
            self._initial_corpus_loaded = True

    def _discover_initial_files(self) -> List[Path]:
        """根据配置扫描知识库目录中的文件"""
        if not self.knowledge_base_dir.exists():
            return []

        matched_paths = []
        for pattern in self._auto_patterns or ["**/*"]:
            matched_paths.extend(self.knowledge_base_dir.glob(pattern))

        unique_files = []
        seen = set()
        for path in matched_paths:
            if not path.is_file():
                continue
            if path.suffix.lower() not in self.supported_extensions:
                continue
            resolved = path.resolve()
            if resolved in seen:
                continue
            seen.add(resolved)
            unique_files.append(resolved)

        unique_files.sort()
        return unique_files

    async def add_knowledge_from_text(self, text: str, source: str = "manual_input",
                                    metadata: Dict[str, Any] = None) -> bool:
        """从文本添加知识"""
        try:
            if not self.vectorstore:
                success = await self.initialize_vectorstore()
                if not success:
                    return False

            # 分割文本
            documents = self.text_splitter.create_documents(
                texts=[text],
                metadatas=[{"source": source, **(metadata or {})}]
            )

            # 添加到向量数据库
            self.vectorstore.add_documents(documents)
            self.vectorstore.persist()

            logger.info(f"成功添加知识: {source}, 片段数: {len(documents)}")
            return True

        except Exception as e:
            logger.error(f"添加文本知识失败: {str(e)}")
            return False

    async def add_knowledge_from_url(
        self,
        url: str,
        max_length: int = 50000,
        strategy: str = 'auto'
    ) -> bool:
        """
        从网页URL添加知识（增强版）

        Args:
            url: 网页URL
            max_length: 最大内容长度
            strategy: 抓取策略 ('auto', 'basic', 'advanced', 'browser')

        Returns:
            bool: 是否成功添加
        """
        try:
            logger.info(f"开始从URL添加知识: {url} (策略: {strategy})")

            # 使用增强的网页抓取服务
            scrape_result = await self.web_scraper.scrape_url(
                url=url,
                strategy=strategy,
                max_length=max_length
            )

            if not scrape_result.get('success'):
                logger.error(f"网页抓取失败: {scrape_result.get('error')}")
                return False

            # 提取内容和元数据
            text = scrape_result.get('content', '')
            title = scrape_result.get('title', 'Untitled')
            metadata = scrape_result.get('metadata', {})

            # 增强元数据
            metadata.update({
                "type": "webpage",
                "title": title,
                "url": url,
                "length": len(text),
                "scrape_strategy": scrape_result.get('strategy_used', strategy)
            })

            # 添加到知识库
            success = await self.add_knowledge_from_text(text, source=url, metadata=metadata)

            if success:
                logger.info(f"成功从URL添加知识: {url} (策略: {scrape_result.get('strategy_used')})")

            return success

        except Exception as e:
            logger.error(f"从URL添加知识失败 {url}: {str(e)}")
            return False

    async def add_knowledge_from_urls_batch(
        self,
        urls: List[str],
        strategy: str = 'auto',
        max_concurrent: int = 3
    ) -> Dict[str, Any]:
        """
        批量从多个URL添加知识

        Args:
            urls: URL列表
            strategy: 抓取策略
            max_concurrent: 最大并发数

        Returns:
            {
                'total': int,
                'success': int,
                'failed': int,
                'results': List[Dict]
            }
        """
        logger.info(f"开始批量URL导入: 总数 {len(urls)}, 并发数 {max_concurrent}")

        results = {
            'total': len(urls),
            'success': 0,
            'failed': 0,
            'results': []
        }

        # 分批处理
        for i in range(0, len(urls), max_concurrent):
            batch = urls[i:i + max_concurrent]

            tasks = [
                self.add_knowledge_from_url(url, strategy=strategy)
                for url in batch
            ]

            batch_results = await asyncio.gather(*tasks, return_exceptions=True)

            for url, success in zip(batch, batch_results):
                if isinstance(success, Exception):
                    results['failed'] += 1
                    results['results'].append({
                        'url': url,
                        'success': False,
                        'error': str(success)
                    })
                elif success:
                    results['success'] += 1
                    results['results'].append({
                        'url': url,
                        'success': True
                    })
                else:
                    results['failed'] += 1
                    results['results'].append({
                        'url': url,
                        'success': False,
                        'error': 'Unknown error'
                    })

        logger.info(f"批量URL导入完成: 成功 {results['success']}/{results['total']}")
        return results

    async def add_knowledge_from_file(self, file_path: str) -> bool:
        """从文件添加知识"""
        try:
            path = Path(file_path)
            if not path.exists():
                logger.error(f"文件不存在: {file_path}")
                return False

            file_ext = path.suffix.lower()

            if file_ext not in self.supported_extensions:
                logger.error(f"不支持的文件类型: {file_ext}")
                return False

            text = ""
            metadata = {
                "type": "file",
                "file_path": str(path),
                "file_type": file_ext
            }

            # 根据文件类型提取文本
            if file_ext == '.txt':
                with path.open('r', encoding='utf-8') as f:
                    text = f.read()

            elif file_ext == '.md':
                with path.open('r', encoding='utf-8') as f:
                    text = f.read()

            elif file_ext == '.pdf':
                text = self._extract_pdf_text(str(path))

            elif file_ext == '.docx':
                text = self._extract_docx_text(str(path))

            elif file_ext == '.json':
                with path.open('r', encoding='utf-8') as f:
                    data = json.load(f)
                    text = json.dumps(data, ensure_ascii=False, indent=2)

            if not text.strip():
                logger.warning(f"文件内容为空: {file_path}")
                return False

            metadata["length"] = len(text)
            return await self.add_knowledge_from_text(text, source=str(path), metadata=metadata)

        except Exception as e:
            logger.error(f"从文件添加知识失败 {file_path}: {str(e)}")
            return False

    def _extract_pdf_text(self, file_path: str) -> str:
        """提取PDF文本"""
        try:
            text = ""
            with open(file_path, 'rb') as file:
                pdf_reader = PdfReader(file)
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n"
            return text
        except Exception as e:
            logger.error(f"PDF文本提取失败: {str(e)}")
            return ""

    def _extract_docx_text(self, file_path: str) -> str:
        """提取DOCX文本"""
        try:
            doc = DocxDocument(file_path)
            text = ""
            for paragraph in doc.paragraphs:
                text += paragraph.text + "\n"
            return text
        except Exception as e:
            logger.error(f"DOCX文本提取失败: {str(e)}")
            return ""

    async def search_knowledge(self, query: str, max_results: int = 5) -> List[Dict[str, Any]]:
        """搜索相关知识"""
        try:
            if not self.retriever:
                await self.ensure_ready()

            if not self.retriever:
                logger.warning("向量数据库未初始化，无法进行检索")
                return []

            # 执行检索
            docs = self.retriever.get_relevant_documents(query)

            # 格式化结果
            results = []
            for doc in docs[:max_results]:
                result = {
                    "content": doc.page_content,
                    "source": doc.metadata.get("source", "unknown"),
                    "metadata": doc.metadata
                }
                results.append(result)

            logger.info(f"知识检索完成: {query}, 找到 {len(results)} 个相关片段")
            return results

        except Exception as e:
            logger.error(f"知识检索失败: {str(e)}")
            return []

    async def get_podcast_context(self, topic: str, characters: List[str] = None) -> Dict[str, Any]:
        """为播客主题获取相关上下文"""
        try:
            await self.ensure_ready()

            # 构建搜索查询
            search_queries = [topic]

            # 添加角色相关查询
            if characters:
                for char in characters:
                    search_queries.append(f"{topic} {char}")

            all_results = []

            # 对每个查询进行检索
            for query in search_queries:
                results = await self.search_knowledge(query, max_results=3)
                all_results.extend(results)

            # 去重和排序
            unique_results = {}
            for result in all_results:
                content_hash = hash(result["content"])
                if content_hash not in unique_results:
                    unique_results[content_hash] = result

            sorted_results = list(unique_results.values())[:8]  # 最多8个相关片段

            # 构建上下文
            context = {
                "topic": topic,
                "total_sources": len(sorted_results),
                "knowledge_points": [],
                "source_summary": {}
            }

            for result in sorted_results:
                context["knowledge_points"].append({
                    "content": result["content"][:500] + "..." if len(result["content"]) > 500 else result["content"],
                    "source": result["source"],
                    "relevance": "high"  # 可以后续添加相关性评分
                })

                source = result["source"]
                if source not in context["source_summary"]:
                    context["source_summary"][source] = 0
                context["source_summary"][source] += 1

            logger.info(f"播客上下文获取完成: {topic}, 知识点数: {len(context['knowledge_points'])}")
            return context

        except Exception as e:
            logger.error(f"获取播客上下文失败: {str(e)}")
            return {"topic": topic, "knowledge_points": [], "source_summary": {}}

    async def add_batch_knowledge(self, sources: List[Dict[str, Any]]) -> Dict[str, Any]:
        """批量添加知识源"""
        results = {
            "total": len(sources),
            "success": 0,
            "failed": 0,
            "errors": []
        }

        for source in sources:
            try:
                source_type = source.get("type")
                source_data = source.get("data")

                if source_type == "text":
                    success = await self.add_knowledge_from_text(
                        text=source_data.get("content"),
                        source=source_data.get("source", "batch_input"),
                        metadata=source_data.get("metadata", {})
                    )

                elif source_type == "url":
                    success = await self.add_knowledge_from_url(source_data.get("url"))

                elif source_type == "file":
                    success = await self.add_knowledge_from_file(source_data.get("file_path"))

                else:
                    results["errors"].append(f"不支持的源类型: {source_type}")
                    results["failed"] += 1
                    continue

                if success:
                    results["success"] += 1
                else:
                    results["failed"] += 1

            except Exception as e:
                results["errors"].append(f"处理失败: {str(e)}")
                results["failed"] += 1

        logger.info(f"批量知识添加完成: 成功 {results['success']}, 失败 {results['failed']}")
        return results

    async def get_knowledge_stats(self) -> Dict[str, Any]:
        """获取知识库统计信息"""
        try:
            if not self.vectorstore:
                await self.ensure_ready()

            if not self.vectorstore:
                return {
                    "status": "not_initialized",
                    "document_count": 0,
                    "total_documents": 0,
                    "database_size_mb": 0.0,
                    "vector_store_path": str(self.vector_store_dir),
                    "embedding_model": settings.rag_embedding_model
                }

            # 获取文档数量
            collection = self.vectorstore._collection
            doc_count = collection.count()

            # 获取数据库大小
            db_size = 0
            if self.vector_store_dir.exists():
                for file in self.vector_store_dir.glob("**/*"):
                    if file.is_file():
                        db_size += file.stat().st_size

            stats = {
                "document_count": doc_count,
                "total_documents": doc_count,
                "database_size_mb": round(db_size / (1024 * 1024), 2),
                "vector_store_path": str(self.vector_store_dir),
                "embedding_model": f"{settings.rag_embedding_provider}: {settings.rag_embedding_model}",
                "embedding_dimensions": settings.rag_embedding_dimensions,
                "status": "ready" if self.vectorstore else "not_initialized"
            }

            return stats

        except Exception as e:
            logger.error(f"获取知识库统计失败: {str(e)}")
            return {"status": "error", "error": str(e)}

    async def clear_knowledge_base(self) -> bool:
        """清空知识库"""
        try:
            if self.vector_store_dir.exists():
                import shutil
                shutil.rmtree(self.vector_store_dir)
                self.vector_store_dir.mkdir(parents=True, exist_ok=True)

            # 重新初始化
            self.vectorstore = None
            self.retriever = None
            self._initial_corpus_loaded = False
            await self.initialize_vectorstore()

            logger.info("知识库清空成功")
            return True

        except Exception as e:
            logger.error(f"清空知识库失败: {str(e)}")
            return False