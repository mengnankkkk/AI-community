#!/usr/bin/env python3
"""
PDF生成脚本 - 将技术报告Markdown转换为PDF格式

支持多种转换方法：
1. markdown2（推荐，无需额外依赖）
2. pandoc（需要预先安装pandoc）
3. weasyprint（HTML转PDF）

使用方法：
    python scripts/generate_pdf.py
    python scripts/generate_pdf.py --method pandoc
    python scripts/generate_pdf.py --output custom_report.pdf
"""

import os
import sys
import argparse
import subprocess
from pathlib import Path


def check_pandoc():
    """检查pandoc是否已安装"""
    try:
        result = subprocess.run(['pandoc', '--version'], 
                              capture_output=True, 
                              text=True, 
                              check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def convert_with_pandoc(md_file, pdf_file):
    """使用pandoc转换（需要预先安装）"""
    print("🔄 使用Pandoc转换...")
    
    # pandoc命令
    cmd = [
        'pandoc',
        str(md_file),
        '-o', str(pdf_file),
        '--pdf-engine=xelatex',
        '-V', 'CJKmainfont=SimSun',  # 中文字体
        '--toc',  # 生成目录
        '--number-sections',  # 章节编号
        '-V', 'geometry:margin=1in',  # 页边距
        '-V', 'fontsize=12pt',  # 字体大小
    ]
    
    try:
        subprocess.run(cmd, check=True, capture_output=True, text=True)
        print(f"✅ 成功生成PDF：{pdf_file}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Pandoc转换失败：{e.stderr}")
        return False


def convert_with_markdown2pdf(md_file, pdf_file):
    """使用markdown2pdf包转换"""
    try:
        from markdown2 import markdown
        from weasyprint import HTML, CSS
        from weasyprint.text.fonts import FontConfiguration
        
        print("🔄 使用markdown2pdf转换...")
        
        # 读取Markdown内容
        with open(md_file, 'r', encoding='utf-8') as f:
            md_content = f.read()
        
        # 转换为HTML
        html_content = markdown(md_content, extras=['tables', 'fenced-code-blocks', 'header-ids'])
        
        # 添加样式
        html_template = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                @page {{
                    size: A4;
                    margin: 2cm;
                }}
                body {{
                    font-family: "SimSun", "Microsoft YaHei", sans-serif;
                    font-size: 12pt;
                    line-height: 1.6;
                    color: #333;
                }}
                h1 {{
                    color: #2c3e50;
                    border-bottom: 3px solid #3498db;
                    padding-bottom: 10px;
                    margin-top: 30px;
                }}
                h2 {{
                    color: #34495e;
                    border-bottom: 2px solid #95a5a6;
                    padding-bottom: 8px;
                    margin-top: 25px;
                }}
                h3 {{
                    color: #555;
                    margin-top: 20px;
                }}
                code {{
                    background: #f4f4f4;
                    padding: 2px 6px;
                    border-radius: 3px;
                    font-family: "Courier New", monospace;
                }}
                pre {{
                    background: #f8f8f8;
                    padding: 15px;
                    border-left: 4px solid #3498db;
                    overflow-x: auto;
                }}
                table {{
                    border-collapse: collapse;
                    width: 100%;
                    margin: 20px 0;
                }}
                th, td {{
                    border: 1px solid #ddd;
                    padding: 12px;
                    text-align: left;
                }}
                th {{
                    background-color: #3498db;
                    color: white;
                }}
                tr:nth-child(even) {{
                    background-color: #f9f9f9;
                }}
                blockquote {{
                    border-left: 4px solid #3498db;
                    padding-left: 20px;
                    margin-left: 0;
                    color: #555;
                    font-style: italic;
                }}
            </style>
        </head>
        <body>
            {html_content}
        </body>
        </html>
        """
        
        # 转换为PDF
        font_config = FontConfiguration()
        HTML(string=html_template).write_pdf(
            pdf_file,
            font_config=font_config
        )
        
        print(f"✅ 成功生成PDF：{pdf_file}")
        return True
        
    except ImportError as e:
        print(f"❌ 缺少依赖包：{e}")
        print("请安装：pip install markdown2 weasyprint")
        return False
    except Exception as e:
        print(f"❌ 转换失败：{e}")
        return False


def convert_with_pypandoc(md_file, pdf_file):
    """使用pypandoc包转换"""
    try:
        import pypandoc
        
        print("🔄 使用pypandoc转换...")
        
        pypandoc.convert_file(
            str(md_file),
            'pdf',
            outputfile=str(pdf_file),
            extra_args=[
                '--pdf-engine=xelatex',
                '-V', 'CJKmainfont=SimSun',
                '--toc',
                '--number-sections',
            ]
        )
        
        print(f"✅ 成功生成PDF：{pdf_file}")
        return True
        
    except ImportError:
        print("❌ 未安装pypandoc包")
        print("请安装：pip install pypandoc")
        return False
    except Exception as e:
        print(f"❌ 转换失败：{e}")
        return False


def create_simple_pdf(md_file, pdf_file):
    """创建简单的说明PDF（当其他方法都失败时）"""
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import inch
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont
        
        print("🔄 使用ReportLab创建简单PDF...")
        
        # 读取Markdown内容
        with open(md_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # 创建PDF
        doc = SimpleDocTemplate(str(pdf_file), pagesize=A4)
        story = []
        styles = getSampleStyleSheet()
        
        # 添加内容
        story.append(Paragraph("AI虚拟播客工作室技术报告", styles['Title']))
        story.append(Spacer(1, 0.5*inch))
        
        for line in lines[:50]:  # 只显示前50行
            if line.strip():
                try:
                    story.append(Paragraph(line.strip(), styles['Normal']))
                    story.append(Spacer(1, 0.1*inch))
                except:
                    pass
        
        story.append(Spacer(1, 0.5*inch))
        story.append(Paragraph(
            "注意：这是简化版PDF。完整版本请查看 TECHNICAL_REPORT.md 文件。",
            styles['Normal']
        ))
        
        doc.build(story)
        print(f"✅ 成功生成简单PDF：{pdf_file}")
        return True
        
    except ImportError:
        print("❌ 未安装reportlab包")
        return False
    except Exception as e:
        print(f"❌ 创建PDF失败：{e}")
        return False


def show_instructions():
    """显示手动转换说明"""
    print("\n" + "="*60)
    print("📋 手动转换PDF指南")
    print("="*60)
    print("\n方法1：在线转换工具（推荐）")
    print("  1. 访问：https://md2pdf.netlify.app/")
    print("  2. 上传文件：TECHNICAL_REPORT.md")
    print("  3. 下载生成的PDF")
    print("\n方法2：使用Markdown编辑器")
    print("  1. 使用Typora、MacDown等编辑器打开TECHNICAL_REPORT.md")
    print("  2. 选择 文件 -> 导出 -> PDF")
    print("\n方法3：安装pandoc")
    print("  Windows: choco install pandoc")
    print("  macOS: brew install pandoc")
    print("  Linux: sudo apt-get install pandoc texlive-xetex")
    print("  然后运行: python scripts/generate_pdf.py --method pandoc")
    print("\n方法4：使用VS Code")
    print("  1. 安装插件：Markdown PDF")
    print("  2. 右键 TECHNICAL_REPORT.md -> Markdown PDF: Export (pdf)")
    print("="*60 + "\n")


def main():
    parser = argparse.ArgumentParser(description='将技术报告转换为PDF格式')
    parser.add_argument('--method', 
                       choices=['auto', 'pandoc', 'markdown2pdf', 'pypandoc', 'simple'],
                       default='auto',
                       help='转换方法')
    parser.add_argument('--input',
                       default='TECHNICAL_REPORT.md',
                       help='输入的Markdown文件')
    parser.add_argument('--output',
                       default='docs/技术报告_AI虚拟播客工作室.pdf',
                       help='输出的PDF文件')
    
    args = parser.parse_args()
    
    # 获取项目根目录
    project_root = Path(__file__).parent.parent
    md_file = project_root / args.input
    pdf_file = project_root / args.output
    
    # 检查输入文件
    if not md_file.exists():
        print(f"❌ 找不到文件：{md_file}")
        return 1
    
    # 创建输出目录
    pdf_file.parent.mkdir(parents=True, exist_ok=True)
    
    print("="*60)
    print("📄 PDF生成工具")
    print("="*60)
    print(f"输入文件：{md_file}")
    print(f"输出文件：{pdf_file}")
    print("="*60 + "\n")
    
    success = False
    
    # 根据指定的方法转换
    if args.method == 'auto':
        # 自动选择可用的方法
        print("🔍 正在检测可用的转换方法...\n")
        
        if check_pandoc():
            print("✓ 检测到pandoc")
            success = convert_with_pandoc(md_file, pdf_file)
        else:
            print("✗ 未检测到pandoc")
        
        if not success:
            success = convert_with_markdown2pdf(md_file, pdf_file)
        
        if not success:
            success = convert_with_pypandoc(md_file, pdf_file)
        
        if not success:
            success = create_simple_pdf(md_file, pdf_file)
            
    elif args.method == 'pandoc':
        success = convert_with_pandoc(md_file, pdf_file)
    elif args.method == 'markdown2pdf':
        success = convert_with_markdown2pdf(md_file, pdf_file)
    elif args.method == 'pypandoc':
        success = convert_with_pypandoc(md_file, pdf_file)
    elif args.method == 'simple':
        success = create_simple_pdf(md_file, pdf_file)
    
    if not success:
        print("\n⚠️  所有自动转换方法均失败")
        show_instructions()
        return 1
    
    print(f"\n✨ PDF文件已生成：{pdf_file}")
    print(f"📊 文件大小：{pdf_file.stat().st_size / 1024:.2f} KB")
    return 0


if __name__ == '__main__':
    sys.exit(main())
