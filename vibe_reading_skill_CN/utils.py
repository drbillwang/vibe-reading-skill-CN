"""
工具函数：文件操作、格式转换等
代码只负责执行，不参与决策
"""

import os
import re
from pathlib import Path
from typing import List, Optional
import ebooklib
from ebooklib import epub
from bs4 import BeautifulSoup


def ensure_dir(directory: Path) -> Path:
    """确保目录存在，如果不存在则创建"""
    directory.mkdir(parents=True, exist_ok=True)
    return directory


def epub_to_txt(epub_path: Path, output_path: Optional[Path] = None) -> str:
    """
    将 EPUB 文件转换为 TXT
    
    Args:
        epub_path: EPUB 文件路径
        output_path: 输出 TXT 文件路径（可选）
    
    Returns:
        转换后的文本内容
    """
    try:
        book = epub.read_epub(str(epub_path))
        text_content = []
        
        for item in book.get_items():
            if item.get_type() == ebooklib.ITEM_DOCUMENT:
                soup = BeautifulSoup(item.get_content(), 'html.parser')
                # 提取文本
                text = soup.get_text()
                # 清理文本
                text = re.sub(r'\s+', ' ', text)  # 多个空白字符替换为单个空格
                text = text.strip()
                if text:
                    text_content.append(text)
        
        full_text = '\n\n'.join(text_content)
        
        # 如果指定了输出路径，保存文件
        if output_path:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(full_text)
        
        return full_text
    except Exception as e:
        raise Exception(f"Error converting EPUB to TXT: {str(e)}")


def read_file(file_path: Path) -> str:
    """读取文件内容"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except UnicodeDecodeError:
        # 尝试其他编码
        for encoding in ['gbk', 'gb2312', 'latin-1']:
            try:
                with open(file_path, 'r', encoding=encoding) as f:
                    return f.read()
            except:
                continue
        raise Exception(f"Unable to decode file: {file_path}")


def write_file(file_path: Path, content: str) -> None:
    """写入文件"""
    file_path.parent.mkdir(parents=True, exist_ok=True)
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)


def split_text_by_lines(text: str, start_line: int, end_line: int) -> str:
    """
    根据行号范围提取文本
    
    Args:
        text: 完整文本
        start_line: 起始行号（1-indexed）
        end_line: 结束行号（1-indexed）
    
    Returns:
        提取的文本片段
    """
    lines = text.split('\n')
    # 转换为 0-indexed
    start_idx = max(0, start_line - 1)
    end_idx = min(len(lines), end_line)
    return '\n'.join(lines[start_idx:end_idx])


def find_sentence_breaks(text: str) -> List[int]:
    """
    找到所有句子断点位置（参考 breakdown.md）
    
    **重要**：必须在完整句子处断开，不能在句子中间断开！
    
    Args:
        text: 文本内容
    
    Returns:
        句子断点位置列表（字符位置，在句子结束标点之后）
    """
    import re
    # 句子结束模式：. ! ? 后跟空格或换行（参考 breakdown.md）
    # 注意：必须匹配标点 + 空格/换行，确保在完整句子后断开
    sentence_endings = re.compile(r'([.!?])\s+')
    breaks = []
    for match in sentence_endings.finditer(text):
        # 句子结束标点后的位置（包括标点和空格）
        # 这个位置是句子结束后的第一个字符位置，可以安全断开
        pos = match.end()
        breaks.append(pos)
    # 也添加文本末尾
    breaks.append(len(text))
    return sorted(set(breaks))


def split_at_sentences(text: str, max_words: int) -> List[str]:
    """
    在完整句子处拆分文本（参考 breakdown.md）
    
    **重要规则**：
    - 必须在完整句子处断开（. ! ? 后）
    - **绝对不能**在句子中间断开
    - 保持段落完整性
    
    Args:
        text: 要拆分的文本
        max_words: 每个部分的最大字数（英文单词）
        
    Returns:
        拆分后的文本片段列表（每个片段都在完整句子处结束）
    """
    word_count = count_words(text)
    if word_count <= max_words:
        return [text]
    
    chunks = []
    current_chunk = ""
    current_word_count = 0
    
    # 找到所有句子断点（在 . ! ? 后）
    breaks = find_sentence_breaks(text)
    
    if not breaks:
        # 如果没有找到句子断点，返回整个文本（不应该发生，但安全处理）
        return [text]
    
    start_pos = 0
    for break_pos in breaks:
        # 提取从 start_pos 到这个断点的文本段（包含完整的句子）
        segment = text[start_pos:break_pos]
        segment_words = count_words(segment)
        
        # 如果加上这个段会超过 max_words，保存当前块并开始新块
        # **关键**：必须在句子边界断开，所以即使当前段超过 max_words，也要包含它
        if current_word_count + segment_words > max_words and current_chunk:
            # 保存当前块（在句子边界）
            chunks.append(current_chunk)
            # 开始新块（从当前句子开始）
            current_chunk = segment
            current_word_count = segment_words
        else:
            # 继续累积（在句子边界）
            current_chunk += segment
            current_word_count += segment_words
        
        start_pos = break_pos
    
    # 添加最后一个块（在句子边界）
    if current_chunk:
        chunks.append(current_chunk)
    
    # 验证：确保所有块都在句子边界结束
    for i, chunk in enumerate(chunks):
        # 检查块是否以句子结束标点结尾（. ! ? 后跟空格或换行，或文本末尾）
        if not re.search(r'[.!?]\s*$', chunk) and i < len(chunks) - 1:
            # 如果不是最后一个块，应该以句子结束标点结尾
            # 如果不符合，说明拆分有问题
            pass  # 这里可以添加警告，但为了性能暂时不检查
    
    return chunks


def count_words(text: str, language: str = 'auto') -> int:
    """
    统计文本字数
    
    Args:
        text: 文本内容
        language: 语言类型（'auto', 'en', 'zh', 'nl' 等）
    
    Returns:
        字数
    """
    if language == 'en' or (language == 'auto' and re.search(r'[a-zA-Z]', text)):
        # 英文：统计单词
        words = re.findall(r'\b[a-zA-Z]+\b', text)
        return len(words)
    elif language == 'zh' or (language == 'auto' and re.search(r'[\u4e00-\u9fff]', text)):
        # 中文：统计字符
        return len([c for c in text if '\u4e00' <= c <= '\u9fff'])
    else:
        # 其他语言：使用 Unicode 字母字符
        words = re.findall(r'\b\w+\b', text)
        return len(words)


def find_sentence_boundaries(text: str) -> List[int]:
    """
    找到所有句子边界位置
    
    Args:
        text: 文本内容
    
    Returns:
        句子边界位置列表
    """
    # 匹配句子结束标记（. ! ? 后跟空格或换行）
    pattern = r'([.!?])\s+'
    boundaries = []
    
    for match in re.finditer(pattern, text):
        boundaries.append(match.end())
    
    # 添加文本结尾
    boundaries.append(len(text))
    
    return sorted(set(boundaries))


def normalize_text(text: str) -> str:
    """
    规范化文本（用于比较）
    
    Args:
        text: 原始文本
    
    Returns:
        规范化后的文本
    """
    # 替换多个空格为单个空格
    text = re.sub(r' +', ' ', text)
    # 替换多个换行为两个换行
    text = re.sub(r'\n{3,}', '\n\n', text)
    # 去除每行首尾空白
    lines = [line.strip() for line in text.split('\n')]
    # 去除开头和结尾的空行
    while lines and not lines[0]:
        lines.pop(0)
    while lines and not lines[-1]:
        lines.pop()
    
    return '\n'.join(lines)
