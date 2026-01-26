#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Vibe Reading Skill - AI Prompts
存放所有 AI 提示词模板
"""

from typing import Optional, Dict, List, Tuple


def get_chapter_identification_prompt(document_text: str) -> str:
    """获取章节识别的 prompt - 阶段1：让AI分析文档格式并生成扫描代码"""
    lines = document_text.split('\n')
    total_lines = len(lines)
    
    # 获取文档的多个关键部分用于分析
    preview_parts = []
    # 开头部分（前 500 行）
    preview_parts.append(("开头部分（前 500 行）", '\n'.join(lines[:500])))
    # 中间部分（25% 位置，前后各 200 行）
    mid_start = max(0, total_lines // 4 - 200)
    mid_end = min(total_lines, total_lines // 4 + 200)
    preview_parts.append((f"中间部分（第 {mid_start}-{mid_end} 行）", '\n'.join(lines[mid_start:mid_end])))
    # 50% 位置
    mid2_start = max(0, total_lines // 2 - 200)
    mid2_end = min(total_lines, total_lines // 2 + 200)
    preview_parts.append((f"中间部分（第 {mid2_start}-{mid2_end} 行）", '\n'.join(lines[mid2_start:mid2_end])))
    # 结尾部分（最后 500 行）
    preview_parts.append(("结尾部分（最后 500 行）", '\n'.join(lines[-500:])))
    
    preview_text = "\n\n".join([f"=== {name} ===\n{content}" for name, content in preview_parts])
    
    return f"""请仔细分析这个文档的章节结构，然后生成 Python 代码来**扫描所有章节标记**。

文档统计：
- 总长度：{len(document_text):,} 字符
- 总词数：{len(document_text.split()):,} 词
- 总行数：{total_lines:,} 行

文档关键部分（用于分析结构）：
{preview_text}

**你的任务（阶段1：生成扫描代码）**：

1. **分析文档的章节格式**：
   - 观察文档中章节标记的格式（如 "CHAPTER 1", "Chapter One", "Part I", "第X章" 等）
   - 识别章节标题的常见模式（是否单独一行、是否有编号、格式是否统一等）
   - 注意：不同书籍的格式可能不同，需要根据实际文档特点生成代码

2. **生成扫描代码**：
   - 生成一个函数 `scan_chapter_markers(document_text)` 
   - 函数应该**遍历整个文档的所有行**，找到所有可能的章节标记
   - 返回一个列表，每个元素是 `(line_number, line_content)` 元组
   - 行号从 1 开始计数
   - 代码应该使用正则表达式或字符串匹配来识别章节标记

3. **关键要求**：
   - 代码必须**遍历整个文档的所有行**，不能只看前几行
   - 扫描应该找到**所有可能的章节标记**（包括目录、标题页等，后续会由AI判断哪些是真正的章节）
   - 代码应该适应文档的实际格式（根据你观察到的格式特点）

**返回格式**：
```json
{{
    "code": "生成的 Python 扫描代码（字符串）",
    "format_analysis": "你观察到的章节格式特点",
    "reasoning": "为什么这样设计扫描代码"
}}
```

**示例代码结构**：
```python
def scan_chapter_markers(document_text):
    import re
    lines = document_text.split('\\n')
    markers = []
    for i, line in enumerate(lines, 1):
        # 根据文档格式设计匹配规则
        if re.match(r'^(?:CHAPTER|Chapter|Part|第.*?章)', line.strip(), re.I):
            markers.append((i, line.strip()))
    return markers
```

**重要**：生成的代码必须能够遍历整个文档并找到所有章节标记！"""


def get_chapter_boundary_prompt(markers: List[tuple], total_lines: int) -> str:
    """获取章节边界确定的 prompt - 阶段2：基于扫描结果让AI确定边界"""
    markers_text = "\n".join([f"- 第 {line_num} 行: {content[:100]}" for line_num, content in markers[:50]])  # 最多显示50个
    if len(markers) > 50:
        markers_text += f"\n... (共 {len(markers)} 个标记，仅显示前50个)"
    
    return f"""我扫描了整个文档，找到了以下章节标记：

文档总行数：{total_lines:,} 行

章节标记列表（行号 + 内容）：
{markers_text}

**你的任务（阶段2：确定章节边界）**：

1. **判断哪些是真正的正文章节**：
   - 识别正文章节标记（如 "CHAPTER 1", "Chapter 1" 等）
   - **忽略**非正文内容（目录、地图列表、致谢、标题页等）
   - 只保留正文章节的标记

2. **确定每个章节的边界**：
   - 每个章节的 `start_line` = 章节标记所在的行号
   - 每个章节的 `end_line` = **下一个章节开始的前一行**，或**本章节内容的最后一行**
   - **最后一个章节的 `end_line` 必须等于文档总行数 {total_lines}**
   - 相邻章节的行号必须连续：前一个章节的 `end_line + 1` = 下一个章节的 `start_line`

3. **关键要求**：
   - 所有章节的 `start_line` 和 `end_line` 必须覆盖整个文档（从第 1 行到第 {total_lines} 行）
   - **绝对不能**让所有章节的 `end_line` 都等于文档总行数（除非是最后一章）
   - 只识别正文章节，忽略目录、地图列表等非正文内容
   - 如果某些行没有被任何正文章节覆盖，这些行会被标记为"非正文"（用于字数验证）

**返回格式**：
```json
{{
    "chapters": [
        {{
            "number": "00",
            "title": "Introduction",
            "start_line": 1,
            "end_line": 324,
            "filename": "00_Introduction.txt"
        }},
        {{
            "number": "01",
            "title": "Chapter 1",
            "start_line": 325,
            "end_line": 850,
            "filename": "01_Chapter_1.txt"
        }},
        ...
    ]
}}
```

**重要**：
- 确保所有章节的行号连续覆盖整个文档
- 最后一个章节的 `end_line` 必须等于 {total_lines}
- 相邻章节的行号必须连续（前一个的 end_line + 1 = 下一个的 start_line）"""


def get_fallback_chapter_identification_prompt(document_text: str, preview_length: int) -> str:
    """获取回退方案的章节识别 prompt"""
    lines = document_text.split('\n')
    total_lines = len(lines)
    
    # 获取文档的多个关键部分
    preview_parts = []
    preview_parts.append(("开头部分", '\n'.join(lines[:min(500, total_lines)])))
    if total_lines > 1000:
        mid_start = max(0, total_lines // 2 - 300)
        mid_end = min(total_lines, total_lines // 2 + 300)
        preview_parts.append((f"中间部分（第 {mid_start}-{mid_end} 行）", '\n'.join(lines[mid_start:mid_end])))
    preview_parts.append(("结尾部分", '\n'.join(lines[-min(500, total_lines):])))
    
    preview_text = "\n\n".join([f"=== {name} ===\n{content}" for name, content in preview_parts])
    
    return f"""请仔细分析以下文档的章节结构。这是一本历史传记，请识别所有章节。

文档统计：
- 总长度：{len(document_text):,} 字符
- 总行数：{total_lines:,} 行

文档关键部分（用于分析结构）：
{preview_text}

**重要要求**：
1. **必须识别出所有章节**，不要返回空列表
2. **准确识别章节边界**：
   - 搜索章节标记（如 "CHAPTER", "Chapter", "Part", "第X章" 等）
   - 每个章节的 `start_line` 是章节标题所在的行号
   - 每个章节的 `end_line` 是**下一个章节开始的前一行**，或**本章节内容的最后一行**
   - **绝对不能**让所有章节的 `end_line` 都等于文档总行数！
   - 相邻章节的 `start_line` 应该等于前一个章节的 `end_line + 1`

3. **如果文档没有明确的章节标记**：
   - 根据内容主题变化推断章节边界
   - 至少将文档拆分成 5-10 个部分，每个部分大约 1000-2000 行
   - 每个部分的 `end_line` 必须小于文档总行数（除非是最后一部分）

4. **只识别正文章节**，忽略目录、地图列表等非正文内容

请返回 JSON 格式的章节信息：
{{
    "chapters": [
        {{
            "number": "00",
            "title": "Introduction",
            "start_line": 1,
            "end_line": 324,
            "filename": "00_Introduction.txt"
        }},
        {{
            "number": "01",
            "title": "Chapter 1",
            "start_line": 325,
            "end_line": 850,
            "filename": "01_Chapter_1.txt"
        }},
        ...
    ]
}}

**关键**：确保每个章节的 `end_line` 都小于文档总行数（除非是最后一章），且相邻章节的行号是连续的！"""


def get_fix_chapter_format_prompt(raw_chapter: str, document_text: str) -> str:
    """获取修复章节格式的 prompt"""
    return f"""章节数据格式异常，请修复为正确的 JSON 格式。

原始数据：
{raw_chapter}

文档上下文（前 10000 字符）：
{document_text[:10000]}

请返回一个 JSON 对象，包含以下字段：
- number: 章节编号（字符串）
- title: 章节标题（字符串）
- start_line: 起始行号（整数）
- end_line: 结束行号（整数）
- filename: 文件名（字符串，格式：XX_Title.txt）

如果无法从原始数据中提取，请根据文档上下文推断。

返回格式：
{{
    "number": "00",
    "title": "Introduction",
    "start_line": 1,
    "end_line": 324,
    "filename": "00_Introduction.txt"
}}"""


def get_further_breakdown_prompt(chapter: dict, chapter_content: str, chapter_length: int, 
                                  word_count: int, lines_count: int, max_words_per_chapter: int) -> str:
    """获取进一步拆分的 prompt"""
    import json
    return f"""请将以下章节拆分成更小的部分。

章节信息：
{json.dumps(chapter, ensure_ascii=False, indent=2)}

章节统计：
- 总长度：{chapter_length} 字符
- 总词数：{word_count} 英文单词（不是 token）
- 总行数：{lines_count} 行
- 最大字数限制：{max_words_per_chapter} 英文单词

**重要要求**：
1. 章节超过 {max_words_per_chapter} 英文单词，必须拆分
2. 每个部分不超过 {max_words_per_chapter} 英文单词
3. 在完整句子处断开（. ! ? 后）
4. 保持段落完整性
5. 返回每个部分的完整内容，而不是索引

完整章节内容：
{chapter_content}

请返回 JSON 格式：
{{
    "parts": [
        {{
            "part_number": 1,
            "content": "第一部分的完整内容（不超过 {max_words_per_chapter} 英文单词）",
            "filename": "01_Chapter_1_part01.txt",
            "word_count": 实际字数
        }},
        ...
    ]
}}

确保所有部分合并后的字数等于原始章节的字数。"""


def get_context_strategy_prompt(chapter_length: int, prev_summary_length: int) -> str:
    """获取上下文策略决策的 prompt"""
    return f"""请决定分析这个章节时需要的上下文和内容。

章节统计：
- 章节长度：{chapter_length} 字符
- 前一章总结长度：{prev_summary_length} 字符

请决定：
1. 需要多少前一章总结作为上下文？（可以全部、部分、或不需要）
2. 需要读取多少章节内容进行分析？（可以全部、部分、或分段）

返回 JSON：
{{
    "previous_summary_to_use": "all" 或具体字符数,
    "chapter_content_to_read": "all" 或具体字符数,
    "analysis_strategy": "你的分析策略"
}}"""


def get_fix_chapter_line_numbers_prompt(chapter: dict, document_text: str, index: int, total_lines: int, suggested_start: Optional[int] = None) -> str:
    """获取修复章节行号的 prompt"""
    title = chapter.get('title', f'Chapter {index+1}')
    chapter_preview = document_text[:50000]  # 前 50000 字符用于分析
    
    return f"""请帮我确定章节的行号范围。

章节信息：
- 标题：{title}
- 章节编号：{chapter.get('number', str(index))}
- 文档总行数：{total_lines}
{f"- 建议起始行号：{suggested_start}" if suggested_start else ""}

文档内容（前 50000 字符，用于定位章节）：
{chapter_preview}

请分析文档，找到这个章节的准确起始行号和结束行号。

**重要要求**：
1. 起始行号应该是章节标题所在的行或章节内容开始的行
2. 结束行号应该是下一个章节开始的前一行，或本章节内容的最后一行
3. 如果这是最后一章，结束行号应该是文档的最后一行
4. 行号从 1 开始计数

请返回 JSON 格式：
{{
    "start_line": 起始行号（整数）,
    "end_line": 结束行号（整数）,
    "filename": "{chapter.get('filename', f'{index:02d}_{title}.txt')}"
}}"""


def get_chapter_analysis_prompt(context_str: str, chapter_metadata: dict, analysis_content: str) -> str:
    """获取章节分析的 prompt"""
    import json
    return f"""{context_str}你是我专属的 "Expert Ghost-Reader" (专家级替身读者)。你的目标是阅读我提供的书籍章节，并重写一份**"高保真浓缩版"**。读你的输出，应该等同于读了原书，且不会遗漏任何精彩细节。

**重要：所有输出必须使用中文（简体中文）。包括章节标题、正文内容、所有文字都必须用中文。如果原书是英文，你需要将内容翻译成中文。**

章节信息：
{json.dumps(chapter_metadata, ensure_ascii=False, indent=2)}

章节内容：
{analysis_content}

**核心原则**：

1. **Direct Immersion (直接沉浸)**：
   - ❌ 禁止废话：严禁使用"作者介绍了..."、"本章讨论了..."等元分析语言
   - ✅ 直接陈述内容：像原书一样写，保持原书的语调（幽默、严肃或犀利）
   - ✅ 隐去作者：把书里的观点当成既定事实写出来，不要说"作者指出"

2. **Argument + Evidence (论点 + 证据 —— 关键规则)**：
   - ❌ 拒绝空洞：绝不能只列干巴巴的结论（如"要保持创新"、"他很节俭"）
   - ✅ 必须包含细节：每提出一个观点，必须紧接着复述原书中支持该观点的具体案例、数据、实验、小故事或比喻
   - ✅ 示例：不要只说"他很节俭"，要写"他为了省钱，甚至把办公室的免费咖啡粉带回家，这种极端的节俭在他的员工中传为笑谈。"
   - ✅ 保留精彩案例：如果原书中有精彩的案例/故事/对话，请在段落中自然融入，不要省略

3. **Adaptive Structure (自适应结构)**：
   - **叙事类** (历史/小说)：按时间线或情节推动重写。保留冲突、对话高光和戏剧性转折
   - **论述类** (商业/社科)：按"核心洞察 -> 案例证明 -> 执行建议"的逻辑展开
   - **科普类**：解释原理，并保留原书中的类比和思维实验

4. **识别并忽略非文本内容**：
   - 如果内容主要是零散的标注、坐标、地名列表、方向指示、年份标注、距离标注等，缺乏连贯的句子和段落结构，这是插图/图表的文字标注，完全忽略
   - 如果整章都是这种内容：直接说"本章为插图/图表标注，无文本内容"
   - 功能性章节（目录、地图列表、简单致谢）：一句话带过即可

**输出格式**：
- 使用 Markdown 格式
- 使用 **核心主题 (Bold)** + 深度叙述段落 的形式
- 可以使用无序列表，但每个点都是一段完整、流畅、有细节的小短文（不是简单的 bullet point）
- 只用 # 章节标题，不要用"Executive Summary"、"Detailed Analysis"等标题
- 直接写内容，像在读原书的精简版
- **所有内容必须用中文（简体中文）**

**目标效果**：读者读你的总结，应该感觉像是在读原书的"高保真浓缩版"，等同于读了原书，且不会遗漏任何精彩细节。

**再次强调：所有输出必须使用中文（简体中文），包括章节标题、正文内容、所有文字都必须用中文。如果原书是其他语言，你需要将内容翻译成中文。**"""
