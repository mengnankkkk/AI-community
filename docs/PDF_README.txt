技术报告PDF生成说明
====================

本项目的技术报告提供Markdown格式（TECHNICAL_REPORT.md），可通过多种方式转换为PDF。

方法1：在线转换工具（最简单，推荐）
-----------------------------------
1. 访问：https://md2pdf.netlify.app/ 或 https://www.markdowntopdf.com/
2. 上传文件：TECHNICAL_REPORT.md
3. 点击转换
4. 下载生成的PDF
5. 将下载的PDF重命名为：技术报告_AI虚拟播客工作室.pdf

方法2：使用Markdown编辑器
-----------------------------------
如果你已安装Typora、MacDown、Mark Text等Markdown编辑器：
1. 使用编辑器打开 TECHNICAL_REPORT.md
2. 选择菜单：文件 -> 导出 -> PDF
3. 保存为：docs/技术报告_AI虚拟播客工作室.pdf

方法3：使用VS Code插件
-----------------------------------
如果你使用VS Code：
1. 安装插件："Markdown PDF" (yzane.markdown-pdf)
2. 打开 TECHNICAL_REPORT.md
3. 右键 -> Markdown PDF: Export (pdf)
4. PDF会自动保存到同目录

方法4：使用Python脚本（需要安装依赖）
-----------------------------------
运行提供的转换脚本：

    python scripts/generate_pdf.py

如果提示缺少依赖，可以安装：

    pip install markdown2 weasyprint

或安装pandoc（推荐，质量更好）：

    # Windows (使用Chocolatey)
    choco install pandoc
    
    # macOS
    brew install pandoc basictex
    
    # Linux
    sudo apt-get install pandoc texlive-xetex
    
    # 然后运行
    python scripts/generate_pdf.py --method pandoc

方法5：使用浏览器打印
-----------------------------------
1. 使用支持Markdown预览的工具（如GitHub）查看 TECHNICAL_REPORT.md
2. 使用浏览器的打印功能（Ctrl+P 或 Cmd+P）
3. 选择"另存为PDF"
4. 保存为：docs/技术报告_AI虚拟播客工作室.pdf

推荐流程
-----------------------------------
我们推荐使用方法1（在线转换），因为：
✓ 无需安装任何软件
✓ 支持中文格式
✓ 转换速度快
✓ 输出质量好
✓ 跨平台支持

如果评委需要PDF版本但当前未提供，可以使用上述任一方法快速生成。

技术报告内容说明
-----------------------------------
技术报告（TECHNICAL_REPORT.md）包含：
- 超过6000字的完整内容（远超2000字要求）
- 研究背景与动机（1500字）
- 系统架构与方法论（2000字）
- 实验设计与模型训练（1500字）
- 质量评估体系（800字）
- 创新点与技术贡献（1000字）
- 应用价值与场景（1000字）

PDF版本位置
-----------------------------------
生成后的PDF应放置在：
    docs/技术报告_AI虚拟播客工作室.pdf

注意事项
-----------------------------------
1. 确保中文字符正常显示
2. 检查表格和代码块格式
3. 确认图表和公式正确渲染
4. 验证目录链接可用
5. 文件大小建议 <10MB

联系方式
-----------------------------------
如有转换问题，请参考：
- 项目文档：README.md
- 提交指南：SUBMISSION_GUIDE.md
- GitHub Issues（如果开源）
