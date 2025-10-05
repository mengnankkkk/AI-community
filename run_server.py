#!/usr/bin/env python3
import uvicorn
import sys
import os

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.append(project_root)
sys.path.append(os.path.join(project_root, "src"))

if __name__ == "__main__":
    uvicorn.run(
        "src.backend.app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )