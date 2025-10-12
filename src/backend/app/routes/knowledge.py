from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from fastapi.responses import JSONResponse
from typing import List, Dict, Any, Optional
import json
import os

from ..services.rag_knowledge_service import RAGKnowledgeService
from ..core.config import settings

router = APIRouter(prefix="/knowledge", tags=["knowledge"])

# 初始化RAG服务
rag_service = RAGKnowledgeService()

@router.post("/initialize")
async def initialize_knowledge_base():
    """初始化知识库"""
    try:
        success = await rag_service.initialize_vectorstore()
        if success:
            return {"message": "知识库初始化成功", "status": "ready"}
        else:
            raise HTTPException(status_code=500, detail="知识库初始化失败")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"初始化失败: {str(e)}")

@router.post("/add-text")
async def add_text_knowledge(
    text: str = Form(...),
    source: str = Form("manual_input"),
    metadata: Optional[str] = Form(None)
):
    """添加文本知识"""
    try:
        metadata_dict = {}
        if metadata:
            try:
                metadata_dict = json.loads(metadata)
            except:
                metadata_dict = {"description": metadata}

        success = await rag_service.add_knowledge_from_text(
            text=text,
            source=source,
            metadata=metadata_dict
        )

        if success:
            return {"message": "文本知识添加成功", "source": source}
        else:
            raise HTTPException(status_code=500, detail="文本知识添加失败")

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"添加失败: {str(e)}")

@router.post("/add-url")
async def add_url_knowledge(
    url: str = Form(...),
    max_length: int = Form(50000),
    strategy: str = Form('auto')
):
    """
    从URL添加知识（增强版）

    Args:
        url: 网页URL
        max_length: 最大内容长度（默认50000字符）
        strategy: 抓取策略 ('auto', 'basic', 'advanced', 'browser')
            - auto: 自动检测最佳策略
            - basic: 简单静态网页抓取
            - advanced: JavaScript渲染支持（需要MCP Fetch）
            - browser: 完整浏览器交互（需要MCP Puppeteer）
    """
    try:
        success = await rag_service.add_knowledge_from_url(url, max_length, strategy)

        if success:
            return {
                "message": "URL知识添加成功",
                "url": url,
                "strategy": strategy
            }
        else:
            raise HTTPException(status_code=500, detail="URL知识添加失败")

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"添加失败: {str(e)}")

@router.post("/add-urls-batch")
async def add_urls_batch(
    urls: List[str],
    strategy: str = 'auto',
    max_concurrent: int = 3
):
    """
    批量从多个URL添加知识

    Args:
        urls: URL列表
        strategy: 抓取策略 ('auto', 'basic', 'advanced', 'browser')
        max_concurrent: 最大并发数（默认3）
    """
    try:
        if not urls:
            raise HTTPException(status_code=400, detail="URL列表不能为空")

        if len(urls) > 20:
            raise HTTPException(status_code=400, detail="单次批量导入最多支持20个URL")

        results = await rag_service.add_knowledge_from_urls_batch(
            urls=urls,
            strategy=strategy,
            max_concurrent=max_concurrent
        )

        return {
            "message": "批量URL导入完成",
            "total": results['total'],
            "success": results['success'],
            "failed": results['failed'],
            "results": results['results']
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"批量导入失败: {str(e)}")

@router.post("/add-file")
async def add_file_knowledge(file: UploadFile = File(...)):
    """上传文件添加知识"""
    try:
        # 检查文件类型
        file_ext = os.path.splitext(file.filename)[1].lower()
        supported_extensions = {'.txt', '.md', '.pdf', '.docx', '.json'}

        if file_ext not in supported_extensions:
            raise HTTPException(
                status_code=400,
                detail=f"不支持的文件类型: {file_ext}. 支持的类型: {', '.join(supported_extensions)}"
            )

        # 保存上传的文件
        upload_dir = "uploads"
        os.makedirs(upload_dir, exist_ok=True)
        file_path = os.path.join(upload_dir, file.filename)

        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)

        # 添加到知识库
        success = await rag_service.add_knowledge_from_file(file_path)

        # 清理临时文件
        try:
            os.remove(file_path)
        except:
            pass

        if success:
            return {"message": "文件知识添加成功", "filename": file.filename}
        else:
            raise HTTPException(status_code=500, detail="文件知识添加失败")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"添加失败: {str(e)}")

@router.post("/add-batch")
async def add_batch_knowledge(sources: List[Dict[str, Any]]):
    """批量添加知识源"""
    try:
        results = await rag_service.add_batch_knowledge(sources)
        return {
            "message": "批量添加完成",
            "results": results
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"批量添加失败: {str(e)}")

@router.get("/search")
async def search_knowledge(query: str, max_results: int = 5):
    """搜索知识库"""
    try:
        results = await rag_service.search_knowledge(query, max_results)
        return {
            "query": query,
            "total_results": len(results),
            "results": results
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"搜索失败: {str(e)}")

@router.get("/podcast-context")
async def get_podcast_context(topic: str, characters: Optional[str] = None):
    """为播客主题获取相关上下文"""
    try:
        character_list = []
        if characters:
            character_list = [char.strip() for char in characters.split(",")]

        context = await rag_service.get_podcast_context(topic, character_list)
        return {
            "topic": topic,
            "context": context
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取上下文失败: {str(e)}")

@router.get("/stats")
async def get_knowledge_stats():
    """获取知识库统计信息"""
    try:
        stats = await rag_service.get_knowledge_stats()
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取统计失败: {str(e)}")

@router.delete("/clear")
async def clear_knowledge_base():
    """清空知识库"""
    try:
        success = await rag_service.clear_knowledge_base()
        if success:
            return {"message": "知识库清空成功"}
        else:
            raise HTTPException(status_code=500, detail="知识库清空失败")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"清空失败: {str(e)}")

@router.post("/quick-setup")
async def quick_setup_knowledge_base():
    """快速设置知识库（添加一些示例知识）"""
    try:
        # 定义一些示例知识源
        sample_sources = [
            {
                "type": "text",
                "data": {
                    "content": """
                    人工智能(AI)的发展历程可以分为几个重要阶段：
                    1. 1950年代：图灵测试提出，AI概念诞生
                    2. 1960-1970年代：专家系统发展
                    3. 1980-1990年代：机器学习兴起
                    4. 2000年代：深度学习突破
                    5. 2010年至今：大模型时代到来

                    目前AI技术在各个领域都有广泛应用，包括自然语言处理、计算机视觉、推荐系统等。
                    ChatGPT等大语言模型的出现标志着AI进入了新的发展阶段。
                    """,
                    "source": "AI发展史-基础知识",
                    "metadata": {"category": "技术", "topic": "人工智能"}
                }
            },
            {
                "type": "text",
                "data": {
                    "content": """
                    远程工作的优势和挑战：

                    优势：
                    - 提高工作效率，减少通勤时间
                    - 更好的工作生活平衡
                    - 降低企业运营成本
                    - 扩大人才招聘范围

                    挑战：
                    - 沟通协作难度增加
                    - 员工孤独感和归属感问题
                    - 网络安全风险
                    - 团队文化建设困难

                    研究表明，混合办公模式可能是未来的主流趋势。
                    """,
                    "source": "远程工作研究报告",
                    "metadata": {"category": "职场", "topic": "远程工作"}
                }
            },
            {
                "type": "text",
                "data": {
                    "content": """
                    可持续发展的核心理念：

                    经济可持续：
                    - 创新驱动的经济增长
                    - 资源效率最大化
                    - 循环经济模式

                    环境可持续：
                    - 减少碳排放
                    - 保护生物多样性
                    - 可再生能源利用

                    社会可持续：
                    - 教育公平
                    - 健康保障
                    - 社会包容性

                    联合国2030年可持续发展目标为全球发展提供了重要指导。
                    """,
                    "source": "可持续发展指南",
                    "metadata": {"category": "环境", "topic": "可持续发展"}
                }
            }
        ]

        # 批量添加示例知识
        results = await rag_service.add_batch_knowledge(sample_sources)

        return {
            "message": "知识库快速设置完成",
            "added_sources": len(sample_sources),
            "results": results
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"快速设置失败: {str(e)}")

@router.get("/demo-topics")
async def get_demo_topics():
    """获取演示主题列表"""
    demo_topics = [
        {
            "topic": "人工智能的未来发展",
            "description": "探讨AI技术的发展趋势和社会影响",
            "suggested_characters": ["技术专家", "伦理学者", "产业分析师"]
        },
        {
            "topic": "远程工作的利与弊",
            "description": "分析远程工作模式的优势挑战和未来趋势",
            "suggested_characters": ["企业管理者", "远程工作者", "人力资源专家"]
        },
        {
            "topic": "可持续发展的实践路径",
            "description": "讨论企业和个人的可持续发展实践",
            "suggested_characters": ["环保专家", "企业代表", "政策研究员"]
        }
    ]

    return {
        "demo_topics": demo_topics,
        "message": "这些主题已有相关知识库支持，可以直接使用"
    }