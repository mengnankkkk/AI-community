# 知识库目录

此目录用于存储 RAG（检索增强生成）知识库的文档和向量数据库。

## 目录结构

```
knowledge_base/
├── documents/          # 原始文档（PDF、TXT、MD等）
├── chroma_db/          # ChromaDB 向量数据库
└── README.md          # 本文件
```

## 使用说明

1. **添加知识文档**：
   - 将文档放入 `documents/` 目录
   - 支持格式：PDF、TXT、MD、DOCX

2. **向量化处理**：
   - 系统会自动处理新文档
   - 生成向量存储在 `chroma_db/`

3. **API配置**：
   ```env
   RAG_ENABLED=true
   KNOWLEDGE_BASE_DIR=knowledge_base
   VECTOR_STORE_DIR=knowledge_base/chroma_db
   ```

## 注意事项

- 向量数据库文件较大，已在 `.gitignore` 中排除
- 建议定期备份重要文档
- 首次使用需配置 OpenAI Embedding API
