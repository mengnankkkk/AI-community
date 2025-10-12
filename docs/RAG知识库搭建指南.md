# RAG 知识库搭建指南

> 使用腾讯混元嵌入模型构建智能播客知识库

## 📋 目录

1. [配置检查](#1-配置检查)
2. [知识库目录结构](#2-知识库目录结构)
3. [添加知识文档](#3-添加知识文档)
4. [使用API管理知识库](#4-使用api管理知识库)
5. [验证和测试](#5-验证和测试)
6. [常见问题](#6-常见问题)

---

## 1. 配置检查

### 1.1 确认 .env 配置

打开 `.env` 文件，确认以下配置已正确设置：

```bash
# ✅ RAG功能总开关
RAG_ENABLED=true

# ✅ 嵌入模型配置（使用腾讯混元）
RAG_EMBEDDING_PROVIDER=hunyuan
RAG_EMBEDDING_MODEL=hunyuan-embedding
RAG_EMBEDDING_API_KEY=sk-wiTSxxrk5C2LaNdtXe3IkcovWCUpvz8ZCbUwwQR2RyUH6EeR
RAG_EMBEDDING_BASE_URL=https://api.hunyuan.cloud.tencent.com/v1
RAG_EMBEDDING_DIMENSIONS=1024  # 混元固定1024维

# ✅ 知识库路径配置
KNOWLEDGE_BASE_DIR=data/knowledge_base
VECTOR_STORE_DIR=data/knowledge_base/chroma_db

# ✅ 文本分割配置
RAG_CHUNK_SIZE=1000         # 每个文本片段1000字符
RAG_CHUNK_OVERLAP=200       # 片段重叠200字符
RAG_MAX_SEARCH_RESULTS=5    # 返回最相关的5个片段

# 可选：自动导入配置
RAG_AUTO_INGEST=false  # 启动时是否自动导入知识库文件
RAG_AUTO_INGEST_PATTERNS=**/*.txt,**/*.md,**/*.pdf
RAG_MAX_INITIAL_FILES=100  # 最大自动导入文件数
```

### 1.2 安装依赖

确保已安装RAG相关的Python库：

```bash
pip install langchain langchain-community langchain-openai chromadb
pip install beautifulsoup4 PyPDF2 python-docx  # 文档解析
```

---

## 2. 知识库目录结构

### 2.1 自动创建目录

项目启动时会自动创建以下目录：

```
E:\github\AI-community\
├── data/
│   └── knowledge_base/          # 📂 知识文档存放目录
│       ├── documents/           # 📄 原始文档（可选）
│       └── chroma_db/           # 🗄️ 向量数据库存储
```

### 2.2 手动创建（如果需要）

```bash
# 在项目根目录执行
mkdir -p data/knowledge_base/documents
mkdir -p data/knowledge_base/chroma_db
```

---

## 3. 添加知识文档

### 3.1 支持的文件类型

- **📝 文本文件**：`.txt`, `.md`
- **📄 PDF文档**：`.pdf`
- **📑 Word文档**：`.docx`
- **🔗 JSON数据**：`.json`

### 3.2 方法1：直接放入目录（推荐新手）

**步骤：**

1. 将知识文档复制到 `data/knowledge_base/documents/` 目录

```bash
# 示例：添加播客主题相关的文档
data/knowledge_base/documents/
├── AI技术介绍.md
├── 科技发展趋势.pdf
├── 专家访谈记录.txt
└── 行业报告.docx
```

2. 启用自动导入（修改 .env）：

```bash
RAG_AUTO_INGEST=true
RAG_AUTO_INGEST_PATTERNS=**/*.txt,**/*.md,**/*.pdf,**/*.docx
```

3. 重启后端服务，系统会自动导入所有匹配的文件

```bash
cd src/backend
python -m app.main
```

**控制台输出示例：**
```
[INFO] 开始自动导入知识库文件，共 4 个候选
[INFO] 成功添加知识: data/knowledge_base/documents/AI技术介绍.md, 片段数: 3
[INFO] 成功添加知识: data/knowledge_base/documents/科技发展趋势.pdf, 片段数: 12
[INFO] 自动导入完成，共成功导入 4 个文件
```

### 3.3 方法2：使用API动态添加（推荐高级用户）

#### 3.3.1 添加文本知识

```bash
POST http://localhost:8000/api/v1/knowledge/add-text
Content-Type: application/json

{
  "text": "人工智能（AI）是计算机科学的一个分支，致力于创建能够执行通常需要人类智能的任务的系统。",
  "source": "AI基础知识",
  "metadata": {
    "type": "definition",
    "topic": "人工智能"
  }
}
```

#### 3.3.2 添加URL内容

```bash
POST http://localhost:8000/api/v1/knowledge/add-url
Content-Type: application/json

{
  "url": "https://example.com/ai-article",
  "max_length": 10000
}
```

#### 3.3.3 添加本地文件

```bash
POST http://localhost:8000/api/v1/knowledge/add-file
Content-Type: application/json

{
  "file_path": "E:/github/AI-community/data/knowledge_base/documents/AI报告.pdf"
}
```

#### 3.3.4 批量添加

```bash
POST http://localhost:8000/api/v1/knowledge/batch-add
Content-Type: application/json

{
  "sources": [
    {
      "type": "text",
      "data": {
        "content": "第一段知识内容",
        "source": "来源1"
      }
    },
    {
      "type": "file",
      "data": {
        "file_path": "path/to/document.pdf"
      }
    },
    {
      "type": "url",
      "data": {
        "url": "https://example.com/article"
      }
    }
  ]
}
```

---

## 4. 使用API管理知识库

### 4.1 查询知识库统计

```bash
GET http://localhost:8000/api/v1/knowledge/stats
```

**响应示例：**
```json
{
  "document_count": 128,
  "total_documents": 128,
  "database_size_mb": 12.45,
  "vector_store_path": "E:/github/AI-community/data/knowledge_base/chroma_db",
  "embedding_model": "hunyuan: hunyuan-embedding",
  "embedding_dimensions": 1024,
  "status": "ready"
}
```

### 4.2 搜索知识

```bash
POST http://localhost:8000/api/v1/knowledge/search
Content-Type: application/json

{
  "query": "人工智能的应用领域有哪些？",
  "max_results": 5
}
```

**响应示例：**
```json
{
  "results": [
    {
      "content": "人工智能的主要应用领域包括：自然语言处理、计算机视觉、机器学习...",
      "source": "AI技术介绍.md",
      "metadata": {
        "type": "file",
        "file_path": "data/knowledge_base/documents/AI技术介绍.md"
      }
    }
  ],
  "total_found": 5
}
```

### 4.3 清空知识库

⚠️ **危险操作**：会删除所有向量数据和索引

```bash
POST http://localhost:8000/api/v1/knowledge/clear
```

---

## 5. 验证和测试

### 5.1 检查向量数据库

运行后端后，检查目录：

```bash
ls -la data/knowledge_base/chroma_db/
```

应该看到类似以下文件：
```
chroma.sqlite3
uuid.txt
<collection_id>/
```

### 5.2 测试知识检索

创建测试脚本 `test_rag.py`：

```python
import asyncio
from src.backend.app.services.rag_knowledge_service import RAGKnowledgeService

async def test_rag():
    rag_service = RAGKnowledgeService()

    # 初始化
    await rag_service.ensure_ready()

    # 查询知识
    results = await rag_service.search_knowledge("人工智能", max_results=3)

    print(f"找到 {len(results)} 个相关片段：")
    for i, result in enumerate(results, 1):
        print(f"\n{i}. 来源: {result['source']}")
        print(f"   内容: {result['content'][:100]}...")

if __name__ == "__main__":
    asyncio.run(test_rag())
```

运行测试：
```bash
cd src/backend
python ../../test_rag.py
```

### 5.3 测试播客生成集成

创建播客时，知识库会自动参与：

```bash
POST http://localhost:8000/api/v1/podcast/custom
Content-Type: application/json

{
  "title": "AI技术探讨",
  "topic": "人工智能的未来发展",
  "target_duration": "5分钟",
  "atmosphere": "formal",
  "characters": [
    {
      "name": "李博士",
      "persona": "AI领域专家",
      "core_viewpoint": "AI将改变各行各业"
    }
  ]
}
```

**预期行为：**
- 系统会自动从知识库检索相关内容
- 生成的对话会融入知识库的信息
- 控制台会显示 RAG 检索日志：
  ```
  [RAG] 正在检索相关知识: 人工智能的未来发展
  [RAG] 成功获取 5 个知识点
  [FACT-CHECK] ℹ️ 检测到 2 个提示
  ```

---

## 6. 常见问题

### Q1: 向量数据库为空，找不到知识？

**解决方案：**
1. 确认文件已放入 `data/knowledge_base/documents/` 目录
2. 检查 `.env` 中 `RAG_AUTO_INGEST=true`
3. 重启后端服务
4. 查看启动日志确认导入成功

### Q2: 嵌入模型调用失败？

**可能原因：**
- API Key 无效或过期
- 网络连接问题
- 配额不足

**检查方法：**
```bash
# 测试混元API连接
curl -X POST "https://api.hunyuan.cloud.tencent.com/v1/embeddings" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "hunyuan-embedding",
    "input": "测试文本"
  }'
```

### Q3: 如何优化检索效果？

**建议：**
1. **调整分块大小**：
   ```bash
   RAG_CHUNK_SIZE=800  # 减小以提高精确度
   RAG_CHUNK_OVERLAP=150
   ```

2. **增加检索结果数**：
   ```bash
   RAG_MAX_SEARCH_RESULTS=8  # 增加到8个
   ```

3. **优化文档质量**：
   - 使用结构化的Markdown文档
   - 添加清晰的标题和段落
   - 避免过多格式和特殊字符

### Q4: 知识库占用空间太大？

**优化方法：**
1. 清理不需要的文档
2. 压缩PDF文件
3. 定期清理向量数据库并重建：
   ```python
   # 通过API清空
   POST http://localhost:8000/api/v1/knowledge/clear

   # 重新导入核心文档
   ```

### Q5: 如何备份知识库？

**备份方法：**
```bash
# 备份原始文档
cp -r data/knowledge_base/documents/ backup/documents_$(date +%Y%m%d)/

# 备份向量数据库
cp -r data/knowledge_base/chroma_db/ backup/chroma_db_$(date +%Y%m%d)/
```

---

## 7. 高级功能

### 7.1 知识来源追踪

生成的播客剧本会包含知识来源元数据：

```json
{
  "script": {
    "dialogues": [...],
    "metadata": {
      "rag_enabled": true,
      "knowledge_sources": 3,
      "knowledge_points_used": 5,
      "source_summary": {
        "AI技术介绍.md": 2,
        "科技发展趋势.pdf": 3
      }
    }
  }
}
```

### 7.2 置信度评分

系统会对检索到的知识进行可信度评分：

- 🟢 **高可信度** (≥0.8)：学术论文、官方文档
- 🟡 **中等可信度** (0.6-0.8)：专业网站、行业报告
- 🟠 **需验证** (<0.6)：社交媒体、论坛内容

### 7.3 事实性校验

生成对话时会自动进行事实校验：

```python
# 在 script_generator.py 中
validation_result = self._validate_against_knowledge(content, rag_context)
if not validation_result["is_valid"]:
    print(f"[FACT-CHECK] ⚠️ 内容未通过事实校验")
```

---

## 8. 性能优化建议

### 8.1 缓存机制

系统已实现缓存优化：
- RAG检索结果缓存
- 结构规划缓存
- 最大缓存条目：50个

### 8.2 并行处理

RAG检索和Gemini素材分析会并行执行：

```python
# 并行执行RAG和素材分析
results = await asyncio.gather(rag_task(), analysis_task())
```

### 8.3 批量导入优化

```python
# 使用批量API而非单个文件API
POST /api/v1/knowledge/batch-add
```

---

## 📚 参考资源

- [腾讯混元API文档](https://cloud.tencent.com/document/product/1729)
- [LangChain文档](https://python.langchain.com/)
- [ChromaDB文档](https://docs.trychroma.com/)
- [项目RAG源码](../src/backend/app/services/rag_knowledge_service.py)

---

**🎉 恭喜！你已经成功搭建了RAG知识库！**

现在你可以：
✅ 添加各种领域的知识文档
✅ 生成基于事实的高质量播客
✅ 自动进行内容安全守护和事实校验

如有问题，请查看日志文件：`data/output/logs/`
