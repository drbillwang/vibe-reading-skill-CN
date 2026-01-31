#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PDF 生成模块
从 summaries 目录生成专业排版的 PDF 文件

特性：
- 自动封面生成：从文件名提取书名和作者，或使用 00_Cover.md 文件
- 专业排版：使用 Playwright 和 Chromium 生成高质量 PDF
- 支持目录：自动生成目录页
- 中文字体支持：完美支持中文排版
"""

import os
import re
from pathlib import Path
from typing import Optional, List, Tuple
from markdown import markdown

try:
    from playwright.sync_api import sync_playwright
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False

from .templates import get_pdf_css


def clean_text(text: str) -> str:
    """移除不需要的文字，特别是第一行的Expert Ghost-Reader相关文字"""
    lines = text.split('\n')
    
    # 检查并移除第一行的Expert Ghost-Reader相关文字
    if lines:
        first_line = lines[0].strip()
        # 匹配各种变体
        patterns = [
            r'好的，Expert Ghost-Reader 已就位。这是对该章节的["""]高保真浓缩版["""]重写。',
            r'好的，Expert Ghost-Reader 已就位。.*?重写。',
            r'Expert Ghost-Reader.*?重写。',
            r'好的，.*?Expert Ghost-Reader.*?已就位.*?重写。',
            r'Expert Ghost-Reader.*?已就位.*?重写。',
        ]
        
        for pattern in patterns:
            if re.match(pattern, first_line):
                lines = lines[1:]  # 移除第一行
                break
    
    # 重新组合文本
    text = '\n'.join(lines)
    
    # 移除可能残留的多个空行
    text = re.sub(r'\n{3,}', '\n\n', text)
    
    return text.strip()


def standardize_title(title: str) -> str:
    """标准化标题，移除'第x章'或'第x章：'格式"""
    title = re.sub(r'^第[一二三四五六七八九十百千万\d]+章[：:\s]*', '', title)
    title = re.sub(r'^第\d+章[：:\s]*', '', title)
    return title.strip()


def extract_title_from_content(content: str) -> Optional[str]:
    """从内容中提取标题"""
    lines = content.split('\n')
    for line in lines:
        line = line.strip()
        if line.startswith('# '):
            title = line[2:].strip()
            return standardize_title(title)
    return None


def extract_book_info_from_filename(filename: str) -> Tuple[str, Optional[str]]:
    """从文件名提取书名和作者信息
    
    Args:
        filename: 文件名（可以包含路径）
    
    Returns:
        (book_title, book_author): 书名和作者（作者可能为 None）
    """
    # 移除扩展名
    name = Path(filename).stem
    
    # 尝试提取作者（通常在 -- 或 - 之后）
    book_title = name
    book_author = None
    
    # 尝试匹配格式: "书名 -- 作者" 或 "书名 - 作者"
    if ' -- ' in name:
        parts = name.split(' -- ', 1)
        book_title = parts[0].strip()
        if len(parts) > 1:
            author_part = parts[1].strip()
            # 移除可能的额外信息（如出版社、ISBN等）
            # 通常作者名在第一个逗号或分号之前
            if ',' in author_part:
                book_author = author_part.split(',')[0].strip()
            elif ';' in author_part:
                book_author = author_part.split(';')[0].strip()
            else:
                book_author = author_part
    elif ' - ' in name and name.count(' - ') == 1:
        parts = name.split(' - ', 1)
        book_title = parts[0].strip()
        if len(parts) > 1:
            author_part = parts[1].strip()
            if ',' in author_part:
                book_author = author_part.split(',')[0].strip()
            elif ';' in author_part:
                book_author = author_part.split(';')[0].strip()
            else:
                book_author = author_part
    
    # 清理书名（移除可能的额外信息）
    # 如果书名太长，截取前50个字符
    if len(book_title) > 50:
        book_title = book_title[:50] + '...'
    
    return book_title, book_author


def get_sorted_summary_files(directory: Path, include_all_md: bool = False) -> List[Tuple[str, Path]]:
    """获取按顺序排列的 summary 文件列表
    
    Args:
        directory: 目录路径
        include_all_md: 如果为 True，处理所有 .md 文件；如果为 False，只处理 *_summary.md 文件
    
    Returns:
        文件列表，每个元素是 (filename, filepath) 元组
    """
    files = []
    for file in sorted(os.listdir(directory)):
        if file.startswith('.'):
            continue
        if file == '00_Cover.md' or file == '00_Cover':
            continue  # 跳过封面文件
        if include_all_md:
            if not file.endswith('.md'):
                continue
        else:
            if not file.endswith('_summary.md'):
                continue
        file_path = directory / file
        if file_path.is_file():
            files.append((file, file_path))
    
    return sorted(files)


def markdown_to_html(markdown_text: str, is_cover: bool = False) -> str:
    """将Markdown转换为HTML"""
    # 清理文本
    markdown_text = clean_text(markdown_text)
    
    # 标准化标题
    title = extract_title_from_content(markdown_text)
    if title and not is_cover:
        # 移除原标题行
        lines = markdown_text.split('\n')
        new_lines = []
        title_found = False
        for line in lines:
            if not title_found and line.strip().startswith('# '):
                title_found = True
                continue
            new_lines.append(line)
        markdown_text = '\n'.join(new_lines)
        # 添加标准化后的标题
        markdown_text = f"# {title}\n\n{markdown_text}"
    
    # 转换为HTML
    html = markdown(markdown_text, extensions=['extra', 'codehilite', 'tables'])
    return html


def get_html_template() -> str:
    """返回HTML模板"""
    pdf_css = get_pdf_css()
    
    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Book Summary</title>
    <style>
        {pdf_css}
    </style>
</head>
<body>
    {{content}}
</body>
</html>"""


def generate_pdf_from_summaries(
    summaries_dir: Path,
    output_path: Path,
    book_title: Optional[str] = None,
    book_subtitle: Optional[str] = None,
    book_author: Optional[str] = None,
    skip_files: Optional[List[str]] = None,
    auto_extract_title: bool = True,
    include_all_md: bool = False
) -> bool:
    """
    从 summaries 目录生成 PDF
    
    Args:
        summaries_dir: summaries 目录路径
        output_path: 输出 PDF 文件路径
        book_title: 书籍标题（可选，如果为 None 且 auto_extract_title=True，会尝试从文件名提取）
        book_subtitle: 书籍副标题（可选）
        book_author: 作者（可选，如果为 None 且 auto_extract_title=True，会尝试从文件名提取）
        skip_files: 要跳过的文件名关键词列表（如 ['Front_Matter', 'Authors_Note']）
        auto_extract_title: 是否自动从文件名提取书名和作者（默认 True）
        include_all_md: 是否处理所有 .md 文件（默认 False，只处理 *_summary.md）
    
    Returns:
        bool: 是否成功生成
    """
    if not PLAYWRIGHT_AVAILABLE:
        raise ImportError(
            "playwright 未安装。请运行:\n"
            "  pip install playwright\n"
            "  playwright install chromium"
        )
    
    if skip_files is None:
        skip_files = ['Front_Matter', 'Authors_Note']
    
    # 如果没有提供书名且启用自动提取，尝试从父目录的书籍文件提取
    if (not book_title or not book_author) and auto_extract_title:
        script_dir = summaries_dir.parent
        for f in script_dir.glob("*.txt"):
            extracted_title, extracted_author = extract_book_info_from_filename(f.name)
            if not book_title:
                book_title = extracted_title
            if not book_author:
                book_author = extracted_author
            break
        if not book_title:
            for f in script_dir.glob("*.epub"):
                extracted_title, extracted_author = extract_book_info_from_filename(f.name)
                if not book_title:
                    book_title = extracted_title
                if not book_author:
                    book_author = extracted_author
                break
    
    # 如果还是没有，使用默认值
    if not book_title:
        book_title = "书籍摘要"
    
    # 获取所有 summary 文件
    files = get_sorted_summary_files(summaries_dir, include_all_md=include_all_md)
    
    if not files:
        if include_all_md:
            raise ValueError(f"在 {summaries_dir} 中未找到任何 .md 文件")
        else:
            raise ValueError(f"在 {summaries_dir} 中未找到任何 *_summary.md 文件")
    
    print(f"找到 {len(files)} 个文件")
    
    # 检查是否有 00_Cover 文件
    cover_file_found = False
    cover_html = None
    cover_file_md = summaries_dir / "00_Cover.md"
    cover_file_no_ext = summaries_dir / "00_Cover"
    
    if cover_file_md.exists():
        try:
            with open(cover_file_md, 'r', encoding='utf-8') as f:
                cover_content = f.read()
            lines = [line.strip() for line in cover_content.split('\n') if line.strip()]
            if lines:
                cover_html = '<div class="cover">'
                is_first = True
                for line in lines:
                    if is_first:
                        cover_html += f'<div class="cover-title">{line}</div>'
                        is_first = False
                    else:
                        cover_html += f'<div class="cover-subtitle">{line}</div>'
                cover_html += '</div>'
                cover_file_found = True
                print("  ✓ 使用 00_Cover.md 文件作为封面")
        except Exception as e:
            print(f"  ⚠️  读取封面文件失败: {e}")
    elif cover_file_no_ext.exists():
        try:
            with open(cover_file_no_ext, 'r', encoding='utf-8') as f:
                cover_content = f.read()
            lines = [line.strip() for line in cover_content.split('\n') if line.strip()]
            if lines:
                cover_html = '<div class="cover">'
                is_first = True
                for line in lines:
                    if is_first:
                        cover_html += f'<div class="cover-title">{line}</div>'
                        is_first = False
                    else:
                        cover_html += f'<div class="cover-subtitle">{line}</div>'
                cover_html += '</div>'
                cover_file_found = True
                print("  ✓ 使用 00_Cover 文件作为封面")
        except Exception as e:
            print(f"  ⚠️  读取封面文件失败: {e}")
    
    # 收集目录项（跳过功能性章节）
    toc_items = []
    print("\n第一遍：收集标题...")
    for filename, filepath in files:
        # 跳过指定的文件
        should_skip = any(keyword in filename for keyword in skip_files)
        if should_skip:
            continue
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            title = extract_title_from_content(content)
            if title:
                toc_items.append(title)
        except Exception as e:
            print(f"读取文件 {filename} 时出错: {e}")
    
    # 构建HTML内容
    print("\n第二遍：生成HTML内容...")
    html_parts = []
    
    # 封面（如果没有找到 00_Cover 文件，自动生成）
    if not cover_file_found:
        cover_html = '<div class="cover">'
        cover_html += f'<div class="cover-title">{book_title}</div>'
        if book_subtitle:
            cover_html += f'<div class="cover-subtitle">{book_subtitle}</div>'
        if book_author:
            cover_html += f'<div class="cover-author">by {book_author}</div>'
        cover_html += '<div class="cover-subtitle" style="margin-top: 60pt;"></div>'
        cover_html += '<div class="cover-subtitle">Summarized by Vibe Reading</div>'
        cover_html += '</div>'
        print(f"  ✓ 自动生成封面: {book_title}")
        if book_author:
            print(f"    作者: {book_author}")
    
    html_parts.append(cover_html)
    
    # 目录
    if toc_items:
        toc_html = '<div class="toc">'
        toc_html += '<div class="toc-title">目录</div>'
        for title in toc_items:
            toc_html += f'<div class="toc-item">{title}</div>'
        toc_html += '</div>'
        html_parts.append(toc_html)
    
    # 正文内容
    chapter_count = 0
    for idx, (filename, filepath) in enumerate(files):
        # 跳过卷首内容（已在封面显示）
        should_skip = any(keyword in filename for keyword in skip_files)
        if should_skip:
            continue
        
        print(f"处理文件 {idx+1}/{len(files)}: {filename}")
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 转换为HTML
            html_content = markdown_to_html(content)
            
            # 添加章节分隔（从第一个非功能性章节开始）
            if chapter_count > 0:
                html_parts.append(f'<div class="chapter">{html_content}</div>')
            else:
                html_parts.append(f'<div>{html_content}</div>')
            
            chapter_count += 1
                
        except Exception as e:
            print(f"处理文件 {filename} 时出错: {e}")
            continue
    
    # 合并所有HTML
    template = get_html_template()
    # 替换占位符，避免CSS大括号冲突
    full_html = template.replace('{{content}}', ''.join(html_parts))
    
    # 使用Playwright生成PDF
    print("\n生成PDF...")
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page()
            page.set_content(full_html, wait_until='networkidle')
            
            page.pdf(
                path=str(output_path),
                format='A4',
                margin={
                    'top': '2.5cm',
                    'right': '2cm',
                    'bottom': '2.5cm',
                    'left': '2.5cm'
                },
                print_background=True,
                display_header_footer=True,
                header_template='<div></div>',  # 空页眉，不显示页码
                footer_template='<div style="font-size:9pt;color:#666;text-align:center;width:100%;">— <span class="pageNumber"></span> —</div>'
            )
            
            browser.close()
        
        print(f"\nPDF已生成: {output_path}")
        print(f"共 {len(toc_items)} 个章节")
        return True
    except Exception as e:
        error_msg = str(e)
        # 检查是否是浏览器未安装的错误
        if "Executable doesn't exist" in error_msg or "chromium" in error_msg.lower():
            raise RuntimeError(
                "Chromium 浏览器未安装。请运行:\n"
                "  playwright install chromium"
            )
        else:
            raise


def generate_pdf_from_combined_content(
    content: str,
    output_path: Path,
    book_title: str,
    book_author: str,
    model_name: str,
    gen_date: str,
    toc_items: Optional[List[str]] = None,
    summaries_dir: Optional[Path] = None
) -> bool:
    """
    从合并的内容字符串生成 PDF（用于 main.py 中的现有流程）
    
    Args:
        content: 合并后的 Markdown 内容
        output_path: 输出 PDF 文件路径
        book_title: 书籍标题
        book_author: 作者
        model_name: 模型名称
        gen_date: 生成日期
        toc_items: 目录项列表（可选）
        summaries_dir: summaries 目录路径（可选，用于查找 00_Cover 文件）
    
    Returns:
        bool: 是否成功生成
    """
    if not PLAYWRIGHT_AVAILABLE:
        raise ImportError(
            "playwright 未安装。请运行:\n"
            "  pip install playwright\n"
            "  playwright install chromium"
        )
    
    from .templates import get_pdf_css
    
    # 检查是否有 00_Cover 文件
    cover_html = None
    if summaries_dir:
        cover_file_md = summaries_dir / "00_Cover.md"
        cover_file_no_ext = summaries_dir / "00_Cover"
        
        if cover_file_md.exists():
            try:
                with open(cover_file_md, 'r', encoding='utf-8') as f:
                    cover_content = f.read()
                lines = [line.strip() for line in cover_content.split('\n') if line.strip()]
                if lines:
                    cover_html = '<div class="cover">'
                    is_first = True
                    for line in lines:
                        if is_first:
                            cover_html += f'<div class="cover-title">{line}</div>'
                            is_first = False
                        else:
                            cover_html += f'<div class="cover-subtitle">{line}</div>'
                    cover_html += '</div>'
                    print("  ✓ 使用 00_Cover.md 文件作为封面")
            except Exception as e:
                print(f"  ⚠️  读取封面文件失败: {e}")
        elif cover_file_no_ext.exists():
            try:
                with open(cover_file_no_ext, 'r', encoding='utf-8') as f:
                    cover_content = f.read()
                lines = [line.strip() for line in cover_content.split('\n') if line.strip()]
                if lines:
                    cover_html = '<div class="cover">'
                    is_first = True
                    for line in lines:
                        if is_first:
                            cover_html += f'<div class="cover-title">{line}</div>'
                            is_first = False
                        else:
                            cover_html += f'<div class="cover-subtitle">{line}</div>'
                    cover_html += '</div>'
                    print("  ✓ 使用 00_Cover 文件作为封面")
            except Exception as e:
                print(f"  ⚠️  读取封面文件失败: {e}")
    
    # 如果没有找到封面文件，使用默认封面
    if not cover_html:
        cover_html = f'''<div class="cover">
    <div class="cover-title">{book_title}</div>
    <div class="cover-subtitle">by {book_author}</div>
    <div class="cover-subtitle" style="margin-top: 60pt;"></div>
    <div class="cover-subtitle">Summarized by Vibe_reading ({model_name})</div>
    <div class="cover-subtitle">{gen_date}</div>
</div>'''
    
    # 生成目录
    toc_html = ''
    if toc_items:
        toc_html = '<div class="toc">'
        toc_html += '<div class="toc-title">目录</div>'
        for title in toc_items:
            toc_html += f'<div class="toc-item">{title}</div>'
        toc_html += '</div>'
    
    # 清理内容
    content = clean_text(content)
    
    # 转换 Markdown 为 HTML
    html_body = markdown(content, extensions=['extra', 'codehilite', 'tables'])
    
    # 处理章节分隔：为每个 h1 添加 chapter 类（除了第一个）
    h1_pattern = r'<h1>(.*?)</h1>'
    h1_matches = list(re.finditer(h1_pattern, html_body))
    
    if len(h1_matches) > 1:
        # 从第二个 h1 开始添加 chapter 类
        offset = 0
        for i, match in enumerate(h1_matches[1:], start=1):  # 跳过第一个
            start_pos = match.start() + offset
            # 在 h1 前添加 <div class="chapter">
            html_body = html_body[:start_pos] + '<div class="chapter">' + html_body[start_pos:]
            offset += len('<div class="chapter">')
            # 在对应的 </h1> 后添加 </div>
            end_pos = match.end() + offset
            html_body = html_body[:end_pos] + '</div>' + html_body[end_pos:]
            offset += len('</div>')
    
    # 生成完整 HTML
    pdf_css = get_pdf_css()
    html_with_styles = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{book_title}</title>
    <style>
        {pdf_css}
    </style>
</head>
<body>
    {cover_html}
    {toc_html}
    {html_body}
</body>
</html>"""
    
    # 使用 Playwright 生成 PDF
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page()
            page.set_content(html_with_styles, wait_until='networkidle')
            
            page.pdf(
                path=str(output_path),
                format='A4',
                margin={
                    'top': '2.5cm',
                    'right': '2cm',
                    'bottom': '2.5cm',
                    'left': '2.5cm'
                },
                print_background=True,
                display_header_footer=True,
                header_template='<div></div>',  # 空页眉
                footer_template='<div style="font-size:9pt;color:#666;text-align:center;width:100%;">— <span class="pageNumber"></span> —</div>'
            )
            
            browser.close()
        
        return True
    except Exception as e:
        error_msg = str(e)
        # 检查是否是浏览器未安装的错误
        if "Executable doesn't exist" in error_msg or "chromium" in error_msg.lower():
            raise RuntimeError(
                "Chromium 浏览器未安装。请运行:\n"
                "  playwright install chromium"
            )
        else:
            raise
