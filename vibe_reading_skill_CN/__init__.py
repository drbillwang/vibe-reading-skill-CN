"""
Vibe Reading Skill - 智能阅读分析 Agent Skill

一个 AI 驱动的书籍阅读分析工具，能够智能识别章节、深度分析内容，
并生成多格式输出（Markdown、PDF、HTML）。
"""

from pathlib import Path
from typing import Dict, Optional, Any

from .main import VibeReadingSkill
from .pdf_generator import (
    generate_pdf_from_summaries,
    generate_pdf_from_combined_content
)


def process_book(
    input_path: str,
    output_dir: Optional[str] = None,
    api_key: Optional[str] = None,
    model: Optional[str] = None,
    **options: Any
) -> Dict[str, Any]:
    """
    Skill 主入口函数 - 处理书籍并生成分析报告
    
    这是 skill 的标准接口，可以被 IDE 或 skill 市场调用。
    
    功能特性：
    - 智能章节识别：AI 自动识别书籍结构，支持大文档的渐进式预览
    - 自动封面生成：从文件名提取书名和作者，生成专业 PDF 封面
    - 智能重试机制：遇到 API 配额限制时自动重试（最多 5 次，等待 60/90/120/150/180 秒）
    - 错误自动修复：AI 生成的代码执行失败时，会让 AI 看到错误并重新生成
    
    Args:
        input_path: 输入文件路径（EPUB 或 TXT 格式）
        output_dir: 输出目录（可选，默认使用项目目录结构）
        api_key: Gemini API Key（可选，也可通过环境变量设置）
        model: 使用的 Gemini 模型（可选，默认 gemini-2.5-pro）
        **options: 其他选项
            - generate_pdf: 是否生成 PDF（默认 True，需要安装 playwright 和 chromium）
            - generate_html: 是否生成 HTML（默认 True）
            - base_dir: 项目根目录（默认当前目录）
    
    Returns:
        Dict 包含处理结果：
        {
            "status": "success" | "error",
            "message": "处理完成" | 错误信息,
            "output_paths": {
                "chapters": "chapters/",
                "summaries": "summaries/",
                "pdf": "pdf/book_summary.pdf",  # 如果生成成功
                "html": "html/interactive_reader.html"
            },
            "metadata": {
                "book_title": "...",
                "chapter_count": 10,
                "processing_time": 123.45
            }
        }
    
    Example:
        >>> result = process_book("book.epub")
        >>> print(result["status"])
        'success'
        >>> if result["status"] == "success":
        ...     print(f"PDF: {result['output_paths']['pdf']}")
        ...     print(f"章节数: {result['metadata']['chapter_count']}")
    
    Note:
        - 如果遇到 API 配额限制（429 错误），系统会自动重试
        - PDF 生成需要安装 playwright 和 chromium（详见 README.md）
        - 封面会自动从文件名提取，或使用 summaries/00_Cover.md 文件
    """
    import time
    from pathlib import Path
    
    start_time = time.time()
    
    try:
        # 解析参数
        input_file = Path(input_path)
        if not input_file.exists():
            return {
                "status": "error",
                "message": f"输入文件不存在: {input_path}",
                "output_paths": {},
                "metadata": {}
            }
        
        # 确定输出目录
        if output_dir:
            base_dir = Path(output_dir)
        else:
            base_dir = options.get("base_dir", Path("."))
        
        # 创建 skill 实例
        skill = VibeReadingSkill(
            api_key=api_key,
            base_dir=base_dir,
            model=model
        )
        
        # 处理书籍
        skill.process(input_file)
        
        # 收集输出路径
        processing_time = time.time() - start_time
        
        # 尝试获取书籍标题
        book_title = "Book Summary"
        summary_files = list(skill.summaries_dir.glob("*.md"))
        if summary_files:
            try:
                from .utils import read_file
            except ImportError:
                from utils import read_file
            first_summary = read_file(summary_files[0])
            import re
            title_match = re.search(r'^#\s+(.+)$', first_summary, re.MULTILINE)
            if title_match:
                book_title = title_match.group(1)
        
        return {
            "status": "success",
            "message": "书籍处理完成",
            "output_paths": {
                "chapters": str(skill.chapters_dir),
                "summaries": str(skill.summaries_dir),
                "pdf": str(skill.pdf_dir / "book_summary.pdf") if (skill.pdf_dir / "book_summary.pdf").exists() else None,
                "html": str(skill.html_dir / "interactive_reader.html") if (skill.html_dir / "interactive_reader.html").exists() else None
            },
            "metadata": {
                "book_title": book_title,
                "chapter_count": len(list(skill.chapters_dir.glob("*.txt"))),
                "processing_time": round(processing_time, 2)
            }
        }
    
    except Exception as e:
        import traceback
        return {
            "status": "error",
            "message": f"处理失败: {str(e)}",
            "error_details": traceback.format_exc(),
            "output_paths": {},
            "metadata": {}
        }


# 导出主要类和函数
__all__ = [
    "VibeReadingSkill",
    "process_book",
    "generate_pdf_from_summaries",
    "generate_pdf_from_combined_content",
]

__version__ = "0.1.0"
