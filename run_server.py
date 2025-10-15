#!/usr/bin/env python3
"""
启动服务器脚本 - 自动使用虚拟环境
"""
import uvicorn
import sys
import os
import subprocess
from pathlib import Path

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.append(project_root)
sys.path.append(os.path.join(project_root, "src"))

def get_venv_python():
    """获取虚拟环境的Python路径"""
    venv_paths = [
        Path(project_root) / ".venv" / "Scripts" / "python.exe",  # Windows
        Path(project_root) / ".venv" / "bin" / "python",  # Linux/Mac
        Path(project_root) / "venv" / "Scripts" / "python.exe",  # Windows (venv)
        Path(project_root) / "venv" / "bin" / "python",  # Linux/Mac (venv)
    ]

    for venv_python in venv_paths:
        if venv_python.exists():
            return str(venv_python)

    return None

def is_venv_active():
    """检查是否已在虚拟环境中"""
    return hasattr(sys, 'real_prefix') or (
        hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix
    )

if __name__ == "__main__":
    # 检查是否已在虚拟环境中
    if not is_venv_active():
        venv_python = get_venv_python()

        if venv_python:
            print(f"🔄 检测到虚拟环境，使用: {venv_python}")
            print(f"🚀 重新启动服务器...")

            # 使用虚拟环境的Python重新执行脚本
            result = subprocess.run([venv_python, __file__] + sys.argv[1:])
            sys.exit(result.returncode)
        else:
            print("⚠️  未检测到虚拟环境 (.venv 或 venv)")
            print("💡 提示: 建议创建并激活虚拟环境")
            print("   python -m venv .venv")
            print("   .venv\\Scripts\\activate  (Windows)")
            print("   source .venv/bin/activate  (Linux/Mac)")
            print()
            response = input("是否继续使用系统Python? (y/N): ")
            if response.lower() != 'y':
                print("❌ 已取消启动")
                sys.exit(1)

    print(f"✅ 使用Python: {sys.executable}")
    print(f"📦 Python版本: {sys.version.split()[0]}")
    print(f"🌐 启动服务器: http://0.0.0.0:8000")
    print("-" * 50)

    uvicorn.run(
        "src.backend.app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )