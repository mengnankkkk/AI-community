"""
查看RAG知识库存储内容
展示向量数据库中的所有文档和元数据
"""
import sys
import os
import asyncio

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src', 'backend'))

async def inspect_knowledge_base():
    """检查知识库存储的详细内容"""
    print("=" * 70)
    print("RAG 知识库存储内容检查")
    print("=" * 70)

    try:
        from app.services.rag_knowledge_service import RAGKnowledgeService
        from pathlib import Path

        # 创建RAG服务实例
        rag_service = RAGKnowledgeService()
        await rag_service.ensure_ready()

        # 1. 显示存储位置
        print("\n📁 存储位置信息：")
        print(f"   项目根目录: {rag_service.project_root}")
        print(f"   知识库目录: {rag_service.knowledge_base_dir}")
        print(f"   向量数据库目录: {rag_service.vector_store_dir}")

        # 2. 显示目录结构和文件大小
        print("\n📂 向量数据库目录结构：")
        vector_dir = Path(rag_service.vector_store_dir)

        if vector_dir.exists():
            total_size = 0
            for item in sorted(vector_dir.rglob("*")):
                if item.is_file():
                    size = item.stat().st_size
                    total_size += size
                    relative_path = item.relative_to(vector_dir)

                    if size < 1024:
                        size_str = f"{size} B"
                    elif size < 1024 * 1024:
                        size_str = f"{size / 1024:.1f} KB"
                    else:
                        size_str = f"{size / (1024 * 1024):.2f} MB"

                    print(f"   - {relative_path}: {size_str}")

            print(f"\n   总大小: {total_size / (1024 * 1024):.2f} MB")
        else:
            print("   ⚠️ 向量数据库目录不存在")

        # 3. 获取统计信息
        print("\n📊 数据库统计：")
        stats = await rag_service.get_knowledge_stats()
        print(f"   文档片段总数: {stats.get('document_count', 0)}")
        print(f"   嵌入模型: {stats.get('embedding_model', 'N/A')}")
        print(f"   向量维度: {stats.get('embedding_dimensions', 0)}")
        print(f"   数据库状态: {stats.get('status', 'unknown')}")

        # 4. 获取并显示所有文档的元数据
        print("\n📄 存储的文档列表：")
        print("=" * 70)

        # 直接访问ChromaDB collection获取所有文档
        if rag_service.vectorstore:
            collection = rag_service.vectorstore._collection

            # 获取所有文档
            results = collection.get(
                include=['documents', 'metadatas']
            )

            documents = results.get('documents', [])
            metadatas = results.get('metadatas', [])
            ids = results.get('ids', [])

            # 按来源分组统计
            source_groups = {}
            for doc_id, doc, metadata in zip(ids, documents, metadatas):
                source = metadata.get('source', 'unknown')

                if source not in source_groups:
                    source_groups[source] = {
                        'count': 0,
                        'total_length': 0,
                        'metadata': metadata,
                        'preview': doc[:150] if doc else ''
                    }

                source_groups[source]['count'] += 1
                source_groups[source]['total_length'] += len(doc) if doc else 0

            # 显示每个来源
            for i, (source, info) in enumerate(sorted(source_groups.items()), 1):
                print(f"\n{i}. 来源: {source}")
                print(f"   文档片段数: {info['count']}")
                print(f"   总字符数: {info['total_length']:,}")

                # 显示元数据
                metadata = info['metadata']
                print("   元数据:")
                for key, value in sorted(metadata.items()):
                    if key != 'source':
                        if isinstance(value, str) and len(value) > 50:
                            value = value[:50] + "..."
                        print(f"      - {key}: {value}")

                # 显示内容预览
                print(f"   内容预览: {info['preview']}...")

            print("\n" + "=" * 70)
            print(f"✅ 共 {len(source_groups)} 个不同来源的文档")
            print(f"✅ 总共 {len(documents)} 个文档片段")

        else:
            print("   ⚠️ 向量数据库未初始化")

        # 5. 显示存储说明
        print("\n" + "=" * 70)
        print("💡 存储说明：")
        print("=" * 70)
        print("""
向量数据库使用 ChromaDB 存储，包含以下组件：

1. chroma.sqlite3 (216 KB)
   - SQLite数据库文件
   - 存储文档元数据、ID映射等结构化信息

2. {collection_id}/ 目录 (4+ MB)
   - data_level0.bin: 向量嵌入数据（主要存储空间）
   - header.bin: 索引头信息
   - length.bin: 向量长度信息
   - link_lists.bin: HNSW索引的链接列表

数据流程：
   网页/文件 → 文本提取 → 分块(1000字符) →
   嵌入向量(1024维) → 存储到ChromaDB →
   支持语义搜索

每个文档会被：
   1. 分割成多个片段（chunk_size=1000, overlap=200）
   2. 每个片段转换为1024维向量（腾讯混元嵌入模型）
   3. 向量和元数据一起存储到ChromaDB
   4. 查询时通过向量相似度检索相关片段
""")

        return True

    except Exception as e:
        print(f"\n❌ 检查失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("\n设置环境编码为 UTF-8...")
    import sys
    if sys.platform == 'win32':
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

    success = asyncio.run(inspect_knowledge_base())
    sys.exit(0 if success else 1)
