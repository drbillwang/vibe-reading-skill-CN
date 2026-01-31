#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Vibe Reading Skill - 主程序
智能阅读分析 Agent Skill
"""

import argparse
import json
import re
from pathlib import Path
from typing import Dict, List, Optional

try:
    from .gemini_client import GeminiClient
    from .utils import (
        ensure_dir, epub_to_txt, read_file, write_file,
        split_text_by_lines, count_words
    )
    from .prompts import (
        get_chapter_identification_prompt,
        get_chapter_boundary_prompt,
        get_fallback_chapter_identification_prompt,
        get_fix_chapter_format_prompt,
        get_fix_chapter_line_numbers_prompt,
        get_further_breakdown_prompt,
        get_context_strategy_prompt,
        get_chapter_analysis_prompt
    )
    from .templates import (
        get_pdf_css,
        get_html_css,
        get_pdf_html_template,
        get_html_interface_template,
        get_html_javascript_template
    )
except ImportError:
    # 支持直接运行 main.py 或从外部调用
    import sys
    from pathlib import Path
    # 添加包路径到 sys.path
    package_dir = Path(__file__).parent.parent
    if str(package_dir) not in sys.path:
        sys.path.insert(0, str(package_dir))
    
    try:
        from vibe_reading_skill_CN.gemini_client import GeminiClient
        from vibe_reading_skill_CN.utils import (
            ensure_dir, epub_to_txt, read_file, write_file,
            split_text_by_lines, count_words
        )
        from vibe_reading_skill_CN.prompts import (
            get_chapter_identification_prompt,
            get_chapter_boundary_prompt,
            get_fallback_chapter_identification_prompt,
            get_fix_chapter_format_prompt,
            get_fix_chapter_line_numbers_prompt,
            get_further_breakdown_prompt,
            get_context_strategy_prompt,
            get_chapter_analysis_prompt
        )
        from vibe_reading_skill_CN.templates import (
            get_pdf_css,
            get_html_css,
            get_pdf_html_template,
            get_html_interface_template,
            get_html_javascript_template
        )
    except ImportError:
        # 如果还是失败，尝试直接导入（在包目录内运行）
        from gemini_client import GeminiClient
        from utils import (
            ensure_dir, epub_to_txt, read_file, write_file,
            split_text_by_lines, count_words
        )
        from prompts import (
            get_chapter_identification_prompt,
            get_chapter_boundary_prompt,
            get_fallback_chapter_identification_prompt,
            get_fix_chapter_format_prompt,
            get_fix_chapter_line_numbers_prompt,
            get_further_breakdown_prompt,
            get_context_strategy_prompt,
            get_chapter_analysis_prompt
        )
        from templates import (
            get_pdf_css,
            get_html_css,
            get_pdf_html_template,
            get_html_interface_template,
            get_html_javascript_template
        )


class VibeReadingSkill:
    """
    Vibe Reading Skill 主类
    
    功能特性：
    - 智能章节识别：AI 自动识别书籍结构，支持大文档的渐进式预览策略
    - 自动错误修复：AI 生成的代码执行失败时，会让 AI 看到错误并重新生成
    - 智能重试机制：遇到 API 配额限制时自动重试（最多 5 次）
    - 自动封面生成：从文件名提取书名和作者，生成专业 PDF 封面
    """
    
    def __init__(self, api_key: Optional[str] = None, base_dir: Path = Path("."), model: Optional[str] = None):
        """
        初始化
        
        Args:
            api_key: Gemini API Key
            base_dir: 项目根目录（默认当前目录）
            model: 使用的 Gemini 模型（可选）
        """
        self.client = GeminiClient(api_key=api_key, model=model)
        self.base_dir = Path(base_dir)
        
        # 创建目录结构
        self.input_dir = ensure_dir(self.base_dir / "input")  # 输入文件目录
        self.chapters_dir = ensure_dir(self.base_dir / "chapters")  # 拆分好的原文 txt
        self.summaries_dir = ensure_dir(self.base_dir / "summaries")  # 总结目录
        self.pdf_dir = ensure_dir(self.base_dir / "pdf")  # PDF 目录
        self.html_dir = ensure_dir(self.base_dir / "html")  # HTML 目录
        
        # 加载 SKILL.md 作为系统指令
        skill_path = Path(__file__).parent / "SKILL.md"
        if skill_path.exists():
            self.system_instruction = read_file(skill_path)
        else:
            self.system_instruction = None
    
    def preprocess_document(self, input_path: Path) -> str:
        """
        阶段一：文档预处理与格式转换
        
        Args:
            input_path: 输入文件路径
        
        Returns:
            清理后的文本内容
        """
        print("=" * 70)
        print("阶段一：文档预处理与格式转换")
        print("=" * 70)
        
        if input_path.suffix.lower() == '.epub':
            print(f"检测到 EPUB 格式，正在转换...")
            # 转换后的 TXT 保存到 input 目录
            txt_path = self.input_dir / f"{input_path.stem}.txt"
            text = epub_to_txt(input_path, txt_path)
            print(f"✓ EPUB 已转换为 TXT: {txt_path}")
        else:
            print(f"读取 TXT 文件...")
            text = read_file(input_path)
            print(f"✓ 文件读取完成")
        
        return text
    
    def identify_chapters(self, document_text: str) -> List[Dict]:
        """
        阶段二：智能章节识别（带渐进式预览和自动错误修复）
        
        策略：
        1. 渐进式预览：如果文档太大，逐步减少预览内容（500→400→300→300→300行）
        2. AI 生成代码：让 AI 分析文档格式并生成扫描代码
        3. 自动错误修复：如果代码执行失败，让 AI 看到错误并重新生成（最多 3 次）
        4. 回退方案：如果所有尝试都失败，使用直接询问 AI 的方式
        
        Args:
            document_text: 文档文本
        
        Returns:
            章节信息列表
        """
        print("\n" + "=" * 70)
        print("阶段二：智能章节识别与拆分")
        print("=" * 70)
        
        lines = document_text.split('\n')
        total_lines = len(lines)
        
        # ========== 阶段1：AI 生成扫描代码（渐进式预览策略）==========
        print("\n阶段1：AI 分析文档格式并生成扫描代码...")
        
        # 定义预览策略序列（逐步减少预览量）
        preview_strategies = [
            # 策略1：初始尝试（最大预览）
            {"start": 500, "end": 500, "mid1": 200, "mid2": 200, "desc": "开头500/结尾500/中间25% 400/中间50% 400"},
            # 策略2：第一次减少
            {"start": 400, "end": 400, "mid1": 150, "mid2": 150, "desc": "开头400/结尾400/中间25% 300/中间50% 300"},
            # 策略3：继续减少
            {"start": 300, "end": 300, "mid1": 100, "mid2": 100, "desc": "开头300/结尾300/中间25% 200/中间50% 200"},
            # 策略4：只保留开头和结尾
            {"start": 300, "end": 300, "mid1": 0, "mid2": 0, "desc": "开头300/结尾300"},
            # 策略5：最小预览（最后尝试）
            {"start": 300, "end": 0, "mid1": 0, "mid2": 0, "desc": "仅开头300行"},
        ]
        
        scan_code = None
        last_error = None
        
        response = None
        for i, strategy in enumerate(preview_strategies, 1):
            try:
                if i > 1:
                    print(f"  尝试策略 {i}：{strategy['desc']}...")
                else:
                    print(f"  尝试策略 {i}：{strategy['desc']}...")
                
                prompt = get_chapter_identification_prompt(
                    document_text,
                    start_lines=strategy['start'],
                    end_lines=strategy['end'],
                    mid1_range=strategy['mid1'],
                    mid2_range=strategy['mid2']
                )
                
                response = self.client.generate_content(
                    prompt,
                    system_instruction=self.system_instruction,
                    temperature=0.3
                )
                
                # 如果成功，跳出循环
                print(f"  ✓ 策略 {i} 成功")
                break
                
            except Exception as e:
                error_msg = str(e)
                last_error = e
                
                # 检查是否是 token 超限错误
                if "token count exceeds" in error_msg.lower() or "exceeds the maximum" in error_msg.lower():
                    if i < len(preview_strategies):
                        print(f"  ⚠️  Token 超限，尝试减少预览量...")
                        continue
                    else:
                        # 所有策略都失败了
                        raise Exception(
                            f"文档太大，即使只预览开头300行也超过限制。\n"
                            f"文档总行数: {total_lines:,} 行\n"
                            f"文档总长度: {len(document_text):,} 字符\n"
                            f"建议：请考虑使用更小的文档，或联系开发者优化处理大文档的策略。"
                        )
                else:
                    # 其他错误，直接抛出
                    raise
        
        # 检查是否成功获取了 response
        if response is None:
            if last_error:
                raise last_error
            else:
                raise Exception("无法生成扫描代码，所有策略都失败了")
        
        # 解析 AI 返回的扫描代码
        scan_code = None
        try:
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group())
            else:
                result = json.loads(response)
            
            scan_code = result.get('code', '')
            if not scan_code:
                print("  ⚠️  AI 没有返回扫描代码，使用回退方案...")
                chapters = self._fallback_chapter_identification(document_text)
                return self._validate_and_fix_chapters(chapters, document_text)
        except Exception as e:
            print(f"  ⚠️  解析 AI 响应失败: {str(e)}")
            chapters = self._fallback_chapter_identification(document_text)
            return self._validate_and_fix_chapters(chapters, document_text)
        
        # ========== 执行扫描代码，找到所有章节标记（带错误重试循环）==========
        print("  执行扫描代码，查找所有章节标记...")
        markers = []
        max_retries = 3  # 最多重试 3 次
        current_code = scan_code
        attempt = 0
        
        while attempt <= max_retries:
            try:
                local_vars = {'document_text': document_text}
                exec(current_code, {'__builtins__': __builtins__, 're': re, 'json': json}, local_vars)
                
                # 如果代码定义了函数，调用它
                if 'scan_chapter_markers' in local_vars and callable(local_vars['scan_chapter_markers']):
                    markers = local_vars['scan_chapter_markers'](document_text)
                elif 'markers' in local_vars:
                    markers = local_vars['markers']
                
                # 检查是否找到标记
                if markers and len(markers) > 0:
                    print(f"  ✓ 找到 {len(markers)} 个章节标记")
                    break  # 成功，跳出循环
                else:
                    # 代码执行成功但没找到标记
                    if attempt < max_retries:
                        attempt += 1
                        print(f"  ⚠️  扫描代码没有找到任何标记，让 AI 重新生成代码（尝试 {attempt}/{max_retries}）...")
                        # 让 AI 看到错误，重新生成代码
                        fix_prompt = f"""你生成的 Python 扫描代码执行成功，但没有找到任何章节标记。

原始代码：
```python
{current_code}
```

问题：代码执行后返回空列表，没有找到任何章节标记。

请分析原因并重新生成代码：
1. 检查正则表达式或匹配规则是否正确
2. 确保代码能遍历整个文档的所有行
3. 调整匹配模式以适应文档的实际格式

文档统计：
- 总长度：{len(document_text):,} 字符
- 总行数：{total_lines:,} 行

文档预览（前 1000 行，用于分析格式）：
{'\n'.join(document_text.split('\n')[:1000])}

请返回修复后的代码（JSON 格式）：
{{
    "code": "修复后的 Python 扫描代码（字符串）",
    "format_analysis": "你观察到的章节格式特点",
    "reasoning": "为什么之前的代码没找到标记，以及如何修复"
}}"""
                        
                        fix_response = self.client.generate_content(
                            fix_prompt,
                            system_instruction=self.system_instruction,
                            temperature=0.3
                        )
                        
                        try:
                            json_match = re.search(r'\{.*\}', fix_response, re.DOTALL)
                            if json_match:
                                fix_result = json.loads(json_match.group())
                            else:
                                fix_result = json.loads(fix_response)
                            
                            current_code = fix_result.get('code', current_code)
                            if not current_code:
                                print("  ⚠️  AI 没有返回新代码，使用回退方案...")
                                chapters = self._fallback_chapter_identification(document_text)
                                return self._validate_and_fix_chapters(chapters, document_text)
                            continue  # 重试新代码
                        except Exception as e2:
                            print(f"  ⚠️  解析 AI 修复响应失败: {str(e2)}")
                            if attempt >= max_retries:
                                break
                            attempt += 1
                            continue
                    else:
                        print("  ⚠️  重试次数用尽，使用回退方案...")
                        chapters = self._fallback_chapter_identification(document_text)
                        return self._validate_and_fix_chapters(chapters, document_text)
            
            except Exception as e:
                error_msg = str(e)
                if attempt < max_retries:
                    attempt += 1
                    print(f"  ⚠️  扫描代码执行失败: {error_msg}")
                    print(f"  让 AI 根据错误信息重新生成代码（尝试 {attempt}/{max_retries}）...")
                    
                    # 让 AI 看到错误，重新生成代码
                    fix_prompt = f"""你生成的 Python 扫描代码执行失败，错误信息如下：

错误：{error_msg}

原始代码：
```python
{current_code}
```

请分析错误原因，然后：
1. 修复代码中的问题（比如语法错误、转义字符错误、变量名错误等）
2. 重新生成正确的代码

文档统计：
- 总长度：{len(document_text):,} 字符
- 总行数：{total_lines:,} 行

文档预览（前 1000 行，用于分析格式）：
{'\n'.join(document_text.split('\n')[:1000])}

请返回修复后的代码（JSON 格式）：
{{
    "code": "修复后的 Python 扫描代码（字符串，注意转义字符）",
    "error_analysis": "错误原因分析",
    "fix_reasoning": "如何修复"
}}"""
                    
                    try:
                        fix_response = self.client.generate_content(
                            fix_prompt,
                            system_instruction=self.system_instruction,
                            temperature=0.3
                        )
                        
                        json_match = re.search(r'\{.*\}', fix_response, re.DOTALL)
                        if json_match:
                            fix_result = json.loads(json_match.group())
                        else:
                            fix_result = json.loads(fix_response)
                        
                        current_code = fix_result.get('code', current_code)
                        if not current_code:
                            print("  ⚠️  AI 没有返回新代码，使用回退方案...")
                            chapters = self._fallback_chapter_identification(document_text)
                            return self._validate_and_fix_chapters(chapters, document_text)
                        continue  # 重试新代码
                    except Exception as e2:
                        print(f"  ⚠️  AI 修复也失败: {str(e2)}")
                        if attempt >= max_retries:
                            break
                        continue
                else:
                    print(f"  ⚠️  重试次数用尽，使用回退方案...")
                    chapters = self._fallback_chapter_identification(document_text)
                    return self._validate_and_fix_chapters(chapters, document_text)
        
        # 如果循环结束还没找到标记，使用回退方案
        if not markers or len(markers) == 0:
            print("  ⚠️  所有重试都失败，使用回退方案...")
            chapters = self._fallback_chapter_identification(document_text)
            return self._validate_and_fix_chapters(chapters, document_text)
        
        # ========== 阶段2：基于扫描结果，让AI确定边界 ==========
        print("\n阶段2：AI 基于扫描结果确定章节边界...")
        boundary_prompt = get_chapter_boundary_prompt(markers, total_lines)
        
        boundary_response = self.client.generate_content(
            boundary_prompt,
            system_instruction=self.system_instruction,
            temperature=0.3
        )
        
        # 解析 AI 返回的章节列表
        chapters = []
        try:
            json_match = re.search(r'\{.*\}', boundary_response, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group())
            else:
                result = json.loads(boundary_response)
            
            chapters = result.get('chapters', [])
            if not chapters or len(chapters) == 0:
                print("  ⚠️  AI 没有返回章节列表，使用回退方案...")
                chapters = self._fallback_chapter_identification(document_text)
        except Exception as e:
            print(f"  ⚠️  解析章节边界失败: {str(e)}")
            chapters = self._fallback_chapter_identification(document_text)
            
            # 验证章节格式：确保是字典列表
            if chapters:
                if not isinstance(chapters, list):
                    print("  ⚠️  AI 返回的不是列表，尝试转换...")
                    chapters = [chapters] if chapters else []
                
                # 检查每个章节是否是字典（如果不是，在 split_chapters 中修复）
                validated_chapters = []
                for i, ch in enumerate(chapters):
                    if isinstance(ch, dict):
                        validated_chapters.append(ch)
                    else:
                        print(f"  ⚠️  章节 {i+1} 格式异常（{type(ch).__name__}），将在拆分时修复")
                        validated_chapters.append(ch)  # 保留原格式，在 split_chapters 中修复
                
                chapters = validated_chapters
            else:
                # 如果 AI 生成的代码返回空列表，触发回退方案
                print("  ⚠️  AI 生成的代码返回空列表，触发回退方案...")
                chapters = None  # 标记需要回退
            
        except Exception as e:
            error_msg = str(e)
            print(f"  ⚠️  AI 生成的代码执行失败: {error_msg}")
            print("  让 AI 根据错误信息修复代码...")
            
            # 让 AI 知道错误原因并修复
            fix_prompt = f"""你生成的 Python 代码执行失败，错误信息如下：

错误：{error_msg}

请分析错误原因，然后：
1. 修复代码中的问题（比如转义字符错误、语法错误等）
2. 重新生成正确的代码

原始 prompt 要求：
- 生成一个函数 `identify_chapters(document_text)` 
- 返回章节列表，每个章节包含：number, title, start_line, end_line, filename
- 必须硬编码所有章节的准确行号

文档统计：
- 总长度：{len(document_text):,} 字符
- 总行数：{len(document_text.split(chr(10))):,} 行

请返回修复后的代码（JSON 格式）：
{{
    "code": "修复后的 Python 代码（字符串，注意转义字符）",
    "chapters": [
        {{
            "number": "00",
            "title": "Introduction",
            "start_line": 1,
            "end_line": 324,
            "filename": "00_Introduction.txt"
        }},
        ...
    ]
}}"""
            
            try:
                fix_response = self.client.generate_content(
                    fix_prompt,
                    system_instruction=self.system_instruction,
                    temperature=0.3
                )
                
                json_match = re.search(r'\{.*\}', fix_response, re.DOTALL)
                if json_match:
                    fix_result = json.loads(json_match.group())
                else:
                    fix_result = json.loads(fix_response)
                
                # 尝试使用修复后的代码
                fixed_code = fix_result.get('code', '')
                fixed_chapters = fix_result.get('chapters', [])
                
                if fixed_chapters and isinstance(fixed_chapters, list) and len(fixed_chapters) > 0:
                    print(f"  ✓ AI 修复后直接返回了 {len(fixed_chapters)} 个章节")
                    chapters = fixed_chapters
                elif fixed_code:
                    print("  执行修复后的代码...")
                    try:
                        local_vars = {'document_text': document_text}
                        exec(fixed_code, {'__builtins__': __builtins__, 're': re, 'json': json}, local_vars)
                        chapters = local_vars.get('chapters', [])
                        if 'identify_chapters' in local_vars and callable(local_vars['identify_chapters']):
                            chapters = local_vars['identify_chapters'](document_text)
                    except Exception as e3:
                        print(f"  ⚠️  修复后的代码执行也失败: {str(e3)}")
                        chapters = []
                else:
                    chapters = []
            except Exception as e2:
                print(f"  ⚠️  AI 修复也失败: {str(e2)}")
                chapters = []
            
            # 如果修复失败，使用回退方案
            if not chapters or len(chapters) == 0:
                print("  回退到直接询问 AI...")
                fallback_prompt = get_fallback_chapter_identification_prompt(document_text, 50000)
                
                fallback_response = self.client.generate_content(
                    fallback_prompt,
                    system_instruction=self.system_instruction,
                    temperature=0.3
                )
                
                try:
                    json_match = re.search(r'\{.*\}', fallback_response, re.DOTALL)
                    if json_match:
                        result = json.loads(json_match.group())
                    else:
                        result = json.loads(fallback_response)
                    chapters = result.get('chapters', [])
                except Exception as e3:
                    print(f"  ⚠️  回退方案也失败: {str(e3)}")
                    chapters = []
        
        # 如果章节列表为空，使用回退方案
        if not chapters or len(chapters) == 0:
            print("  ⚠️  章节识别失败，使用回退方案...")
            chapters = self._fallback_chapter_identification(document_text)
        
        # 验证章节识别的合理性
        chapters = self._validate_and_fix_chapters(chapters, document_text)
        
        # 验证行号覆盖，找出空隙并标记为非正文
        chapters = self._verify_line_coverage(chapters, document_text)
        
        # 固定使用 7000 words 作为每章最大字数（不再让 AI 决定）
        self.suggested_max_words = 7000
        
        # 统计正文章节数量（排除非正文章节）
        content_chapters = [ch for ch in chapters if not ch.get('is_non_content', False)]
        print(f"✓ 识别到 {len(content_chapters)} 个正文章节")
        if len(chapters) > len(content_chapters):
            print(f"  包含 {len(chapters) - len(content_chapters)} 个非正文章节（用于字数验证）")
        print(f"  每章最大字数限制：7000 英文单词（固定值，用于进一步拆分）")
        return chapters
    
    def _validate_and_fix_chapters(self, chapters: List[Dict], document_text: str) -> List[Dict]:
        """
        验证章节识别的合理性，如果发现问题让 AI 修复
        
        Args:
            chapters: 章节列表
            document_text: 文档文本
            
        Returns:
            修复后的章节列表
        """
        if not chapters:
            return chapters
        
        lines = document_text.split('\n')
        total_lines = len(lines)
        
        # 检查是否有问题
        issues = []
        
        # 检查1：是否有多个章节的 end_line 都等于文档总行数
        chapters_with_full_end = [i for i, ch in enumerate(chapters) 
                                 if isinstance(ch, dict) and 
                                 (ch.get('end_line') or ch.get('end') or 0) == total_lines]
        if len(chapters_with_full_end) > 1:
            issues.append(f"发现 {len(chapters_with_full_end)} 个章节的 end_line 都等于文档总行数，说明识别有误")
        
        # 检查2：是否有章节的 start_line >= end_line
        invalid_ranges = [i for i, ch in enumerate(chapters)
                         if isinstance(ch, dict) and
                         (ch.get('start_line') or 1) >= (ch.get('end_line') or total_lines)]
        if invalid_ranges:
            issues.append(f"发现 {len(invalid_ranges)} 个章节的行号范围无效")
        
        # 检查3：是否有章节的 start_line == 1 且 end_line == total_lines（包含整个文档）
        full_doc_chapters = [i for i, ch in enumerate(chapters)
                            if isinstance(ch, dict) and
                            (ch.get('start_line') or 1) == 1 and
                            (ch.get('end_line') or total_lines) == total_lines]
        if len(full_doc_chapters) > 0:
            issues.append(f"发现 {len(full_doc_chapters)} 个章节包含整个文档，说明识别有误")
        
        if issues:
            print(f"  ⚠️  检测到章节识别问题：")
            for issue in issues:
                print(f"    - {issue}")
            print(f"  让 AI 重新识别章节...")
            
            # 让 AI 重新识别（使用回退方案，但提供更多文档内容）
            fixed_chapters = self._fallback_chapter_identification(document_text)
            
            # 再次验证修复后的章节
            if fixed_chapters:
                return self._validate_and_fix_chapters(fixed_chapters, document_text)
            else:
                # 如果还是失败，使用紧急拆分
                print("  ⚠️  AI 重新识别也失败，使用紧急拆分方案...")
                return self._emergency_split(document_text)
        
        return chapters
    
    def _verify_line_coverage(self, chapters: List[Dict], document_text: str) -> List[Dict]:
        """
        验证行号覆盖，找出空隙并标记为非正文
        
        Args:
            chapters: 章节列表
            document_text: 文档文本
            
        Returns:
            包含非正文章节的完整章节列表
        """
        if not chapters:
            return chapters
        
        lines = document_text.split('\n')
        total_lines = len(lines)
        
        # 收集所有正文章节的行号范围（排除非正文章节）
        covered_ranges = []
        for chapter in chapters:
            if isinstance(chapter, dict) and not chapter.get('is_non_content', False):
                start = chapter.get('start_line') or chapter.get('start') or 1
                end = chapter.get('end_line') or chapter.get('end') or total_lines
                try:
                    start = int(start)
                    end = int(end)
                    covered_ranges.append((start, end))
                except (ValueError, TypeError):
                    continue
        
        if not covered_ranges:
            return chapters
        
        # 排序
        covered_ranges.sort(key=lambda x: x[0])
        
        # 找出空隙（未被覆盖的行范围）
        gaps = []
        current_pos = 1
        
        for start, end in covered_ranges:
            if current_pos < start:
                # 发现空隙
                gaps.append((current_pos, start - 1))
            current_pos = max(current_pos, end + 1)
        
        # 检查最后是否有空隙
        if current_pos <= total_lines:
            gaps.append((current_pos, total_lines))
        
        # 如果有空隙，标记为非正文章节
        if gaps:
            print(f"\n  发现 {len(gaps)} 个非正文区域（目录、地图列表等）")
            non_content_chapters = []
            for i, (gap_start, gap_end) in enumerate(gaps):
                # 读取空隙内容的前几行，用于生成标题
                gap_preview = '\n'.join(lines[gap_start-1:min(gap_start+5, gap_end)])
                # 尝试提取标题
                title_match = re.search(r'^(Contents?|Table of Contents|List of Maps|Acknowledgements?|Preface|Title Page)', gap_preview, re.I)
                if title_match:
                    title = title_match.group(1)
                else:
                    title = f"Non-Content Section {i+1}"
                
                non_content_chapters.append({
                    "number": f"NC{i+1:02d}",
                    "title": title,
                    "start_line": gap_start,
                    "end_line": gap_end,
                    "filename": f"NC{i+1:02d}_{title.replace(' ', '_')[:30]}.txt",
                    "is_non_content": True  # 标记为非正文
                })
            
            # 合并正文章节和非正文章节
            all_chapters = chapters + non_content_chapters
            # 按 start_line 排序
            all_chapters.sort(key=lambda x: int(x.get('start_line', 0)))
            
            print(f"  ✓ 添加了 {len(non_content_chapters)} 个非正文章节（用于字数验证）")
            return all_chapters
        
        return chapters
    
    def _fallback_chapter_identification(self, document_text: str) -> List[Dict]:
        """
        回退方案：如果 AI 生成的代码失败，直接询问 AI 识别章节
        
        Args:
            document_text: 文档文本
            
        Returns:
            章节信息列表
        """
        print("  使用回退方案：直接询问 AI...")
        
        # 读取更多文档内容（前 100000 字符，或全部文档如果更短）
        preview_length = min(100000, len(document_text))
        fallback_prompt = get_fallback_chapter_identification_prompt(document_text, preview_length)
        
        try:
            fallback_response = self.client.generate_content(
                fallback_prompt,
                system_instruction=self.system_instruction,
                temperature=0.3
            )
            
            json_match = re.search(r'\{.*\}', fallback_response, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group())
            else:
                result = json.loads(fallback_response)
            
            chapters = result.get('chapters', [])
            
            # 如果还是空，使用最后的备用方案：按固定长度拆分
            if not chapters or len(chapters) == 0:
                print("  ⚠️  回退方案也失败，使用最后的备用方案：按固定长度拆分...")
                chapters = self._emergency_split(document_text)
            
            return chapters
            
        except Exception as e:
            print(f"  ⚠️  回退方案执行失败: {str(e)}")
            print("  使用最后的备用方案：按固定长度拆分...")
            return self._emergency_split(document_text)
    
    def _verify_line_coverage(self, chapters: List[Dict], document_text: str) -> List[Dict]:
        """
        验证行号覆盖，找出空隙并标记为非正文
        
        Args:
            chapters: 章节列表
            document_text: 文档文本
            
        Returns:
            包含非正文章节的完整章节列表
        """
        if not chapters:
            return chapters
        
        lines = document_text.split('\n')
        total_lines = len(lines)
        
        # 收集所有正文章节的行号范围（排除非正文章节）
        covered_ranges = []
        for chapter in chapters:
            if isinstance(chapter, dict) and not chapter.get('is_non_content', False):
                start = chapter.get('start_line') or chapter.get('start') or 1
                end = chapter.get('end_line') or chapter.get('end') or total_lines
                try:
                    start = int(start)
                    end = int(end)
                    covered_ranges.append((start, end))
                except (ValueError, TypeError):
                    continue
        
        if not covered_ranges:
            return chapters
        
        # 排序
        covered_ranges.sort(key=lambda x: x[0])
        
        # 找出空隙（未被覆盖的行范围）
        gaps = []
        current_pos = 1
        
        for start, end in covered_ranges:
            if current_pos < start:
                # 发现空隙
                gaps.append((current_pos, start - 1))
            current_pos = max(current_pos, end + 1)
        
        # 检查最后是否有空隙
        if current_pos <= total_lines:
            gaps.append((current_pos, total_lines))
        
        # 如果有空隙，标记为非正文章节
        if gaps:
            print(f"\n  发现 {len(gaps)} 个非正文区域（目录、地图列表等）")
            non_content_chapters = []
            for i, (gap_start, gap_end) in enumerate(gaps):
                # 读取空隙内容的前几行，用于生成标题
                gap_preview = '\n'.join(lines[gap_start-1:min(gap_start+5, gap_end)])
                # 尝试提取标题
                title_match = re.search(r'^(Contents?|Table of Contents|List of Maps|Acknowledgements?|Preface|Title Page)', gap_preview, re.I)
                if title_match:
                    title = title_match.group(1)
                else:
                    title = f"Non-Content Section {i+1}"
                
                non_content_chapters.append({
                    "number": f"NC{i+1:02d}",
                    "title": title,
                    "start_line": gap_start,
                    "end_line": gap_end,
                    "filename": f"NC{i+1:02d}_{title.replace(' ', '_')[:30]}.txt",
                    "is_non_content": True  # 标记为非正文
                })
            
            # 合并正文章节和非正文章节
            all_chapters = chapters + non_content_chapters
            # 按 start_line 排序
            all_chapters.sort(key=lambda x: int(x.get('start_line', 0)))
            
            print(f"  ✓ 添加了 {len(non_content_chapters)} 个非正文章节（用于字数验证）")
            return all_chapters
        
        return chapters
    
    def _emergency_split(self, document_text: str) -> List[Dict]:
        """
        最后的备用方案：如果所有 AI 方案都失败，按固定长度拆分文档
        
        Args:
            document_text: 文档文本
            
        Returns:
            章节信息列表
        """
        lines = document_text.split('\n')
        total_lines = len(lines)
        
        # 拆分成 10 个部分
        num_parts = 10
        lines_per_part = total_lines // num_parts
        
        chapters = []
        for i in range(num_parts):
            start_line = i * lines_per_part + 1
            if i == num_parts - 1:
                end_line = total_lines
            else:
                end_line = (i + 1) * lines_per_part
            
            # 尝试从内容中提取标题（取该部分的前几行）
            part_preview = '\n'.join(lines[start_line-1:min(start_line+10, end_line)])
            title_match = re.search(r'^(?:CHAPTER|Chapter|Part|第.*?章|第.*?部分)\s*[:\-]?\s*(.+?)$', part_preview, re.MULTILINE | re.IGNORECASE)
            if title_match:
                title = title_match.group(1).strip()[:50]  # 限制标题长度
            else:
                title = f"Part {i+1}"
            
            chapters.append({
                "number": f"{i:02d}",
                "title": title,
                "start_line": start_line,
                "end_line": end_line,
                "filename": f"{i:02d}_{title.replace(' ', '_')[:30]}.txt"
            })
        
        print(f"  ✓ 使用备用方案拆分成 {len(chapters)} 个部分")
        return chapters
    
    def split_chapters(self, document_text: str, chapters: List[Dict]) -> None:
        """
        执行章节拆分
        
        Args:
            document_text: 文档文本
            chapters: 章节信息列表（可能是各种格式，需要智能处理）
        """
        print("\n正在拆分章节...")
        lines = document_text.split('\n')
        
        # 智能处理章节格式：如果格式不对，让 AI 修复
        if not chapters:
            print("  ⚠️  没有章节数据，跳过拆分")
            return
        
        # 检查并修复章节格式
        fixed_chapters = []
        for i, chapter in enumerate(chapters):
            if isinstance(chapter, dict):
                # 已经是字典格式，直接使用
                fixed_chapters.append(chapter)
            elif isinstance(chapter, str):
                # 如果是字符串，尝试解析或让 AI 修复
                print(f"  ⚠️  章节 {i+1} 格式异常（字符串），尝试修复...")
                try:
                    # 尝试解析为 JSON
                    parsed = json.loads(chapter)
                    if isinstance(parsed, dict):
                        fixed_chapters.append(parsed)
                    else:
                        # 让 AI 修复格式
                        fixed_chapters.append(self._fix_chapter_format(chapter, document_text, i))
                except:
                    # 让 AI 修复格式
                    fixed_chapters.append(self._fix_chapter_format(chapter, document_text, i))
            else:
                # 其他格式，让 AI 修复
                print(f"  ⚠️  章节 {i+1} 格式异常，尝试修复...")
                fixed_chapters.append(self._fix_chapter_format(str(chapter), document_text, i))
        
        # 使用修复后的章节列表
        chapters = fixed_chapters
        
        for i, chapter in enumerate(chapters):
            # 安全获取字段，支持各种可能的键名
            start_line = chapter.get('start_line') or chapter.get('start') or chapter.get('startLine') or 1
            end_line = chapter.get('end_line') or chapter.get('end') or chapter.get('endLine') or len(lines)
            filename = chapter.get('filename') or chapter.get('name') or f"{chapter.get('number', '00')}_Chapter.txt"
            
            # 确保是整数
            try:
                start_line = int(start_line)
                end_line = int(end_line)
            except (ValueError, TypeError):
                print(f"  ⚠️  章节 {i+1} 行号格式错误，使用默认值")
                start_line = 1
                end_line = len(lines)
            
            # 确保不是 None
            if start_line is None:
                start_line = 1
            if end_line is None:
                end_line = len(lines)
            
            # 验证行号是否合理
            if start_line < 1:
                start_line = 1
            if end_line > len(lines):
                end_line = len(lines)
            if start_line >= end_line:
                print(f"  ⚠️  章节 {i+1} ({filename}) 行号无效 (start={start_line}, end={end_line})，让 AI 修复...")
                # 让 AI 重新识别这个章节的行号
                fixed = self._fix_chapter_line_numbers(chapter, document_text, i, len(lines))
                start_line = fixed.get('start_line') or 1
                end_line = fixed.get('end_line') or len(lines)
                filename = fixed.get('filename') or filename
                # 确保是整数
                try:
                    start_line = int(start_line)
                    end_line = int(end_line)
                except (ValueError, TypeError):
                    start_line = 1
                    end_line = len(lines)
            
            # 检查是否所有章节的 end_line 都是文档总行数（说明识别有问题）
            if i > 0 and end_line == len(lines) and start_line == 1:
                print(f"  ⚠️  章节 {i+1} ({filename}) 可能识别错误（包含整个文档），让 AI 重新识别...")
                fixed = self._fix_chapter_line_numbers(chapter, document_text, i, len(lines))
                start_line = fixed.get('start_line') or 1
                end_line = fixed.get('end_line') or len(lines)
                filename = fixed.get('filename') or filename
                # 确保是整数
                try:
                    start_line = int(start_line)
                    end_line = int(end_line)
                except (ValueError, TypeError):
                    start_line = 1
                    end_line = len(lines)
            
            chapter_text = split_text_by_lines(document_text, start_line, end_line)
            output_path = self.chapters_dir / filename
            
            # 验证提取的内容是否合理（不应该和整个文档一样）
            if len(chapter_text) == len(document_text) and i > 0:
                print(f"  ⚠️  警告：章节 {i+1} ({filename}) 内容与整个文档相同，可能识别错误")
                # 尝试使用前一个章节的 end_line 作为 start_line
                if i > 0 and isinstance(chapters[i-1], dict):
                    prev_end = chapters[i-1].get('end_line') or chapters[i-1].get('end') or chapters[i-1].get('endLine')
                    if prev_end:
                        try:
                            start_line = int(prev_end) + 1
                            # 让 AI 决定这个章节的结束位置
                            fixed = self._fix_chapter_line_numbers(chapter, document_text, i, len(lines), start_line)
                            end_line = fixed.get('end_line') or min(start_line + 1000, len(lines))
                            # 确保是整数
                            try:
                                end_line = int(end_line)
                            except (ValueError, TypeError):
                                end_line = min(start_line + 1000, len(lines))
                            chapter_text = split_text_by_lines(document_text, start_line, end_line)
                            print(f"  ✓ 已修复：{filename} (lines {start_line}-{end_line})")
                        except:
                            pass
            
            write_file(output_path, chapter_text)
            print(f"  ✓ {filename} (lines {start_line}-{end_line}, {len(chapter_text)} 字符)")
        
        print(f"\n✓ 所有章节已保存到: {self.chapters_dir}")
    
    def _fix_chapter_line_numbers(self, chapter: Dict, document_text: str, index: int, total_lines: int, suggested_start: Optional[int] = None) -> Dict:
        """
        让 AI 修复章节的行号
        
        Args:
            chapter: 章节字典
            document_text: 文档文本
            index: 章节索引
            total_lines: 文档总行数
            suggested_start: 建议的起始行号（可选）
            
        Returns:
            修复后的章节字典
        """
        # 使用 prompts.py 中的 prompt
        prompt = get_fix_chapter_line_numbers_prompt(chapter, document_text, index, total_lines, suggested_start)
        
        try:
            response = self.client.generate_content(
                prompt,
                system_instruction=self.system_instruction,
                temperature=0.3
            )
            
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                fixed = json.loads(json_match.group())
                # 获取标题，如果没有则使用默认值
                default_title = chapter.get('title', f"Chapter {index+1}")
                # 确保 start_line 和 end_line 不是 None
                fixed_start = fixed.get('start_line') or suggested_start or max(1, (index * total_lines // 25))
                fixed_end = fixed.get('end_line') or min(total_lines, ((index + 1) * total_lines // 25))
                # 合并原有信息
                fixed.update({
                    "number": chapter.get('number', f"{index:02d}"),
                    "title": chapter.get('title', default_title),
                    "start_line": fixed_start,
                    "end_line": fixed_end
                })
                return fixed
            else:
                # 如果解析失败，使用默认值
                default_title = chapter.get('title', f"Chapter {index+1}")
                safe_title = default_title.replace('/', '_').replace('\\', '_')[:50]  # 清理标题用于文件名
                return {
                    "number": chapter.get('number', f"{index:02d}"),
                    "title": default_title,
                    "start_line": suggested_start or max(1, (index * total_lines // 25)),
                    "end_line": min(total_lines, ((index + 1) * total_lines // 25)),
                    "filename": chapter.get('filename', f"{index:02d}_{safe_title}.txt")
                }
        except Exception as e:
            print(f"    ⚠️  AI 修复失败: {e}")
            # 使用安全的默认值
            default_title = chapter.get('title', f"Chapter {index+1}")
            safe_title = default_title.replace('/', '_').replace('\\', '_')[:50]  # 清理标题用于文件名
            return {
                "number": chapter.get('number', f"{index:02d}"),
                "title": default_title,
                "start_line": suggested_start or max(1, (index * total_lines // 25)),
                "end_line": min(total_lines, ((index + 1) * total_lines // 25)),
                "filename": chapter.get('filename', f"{index:02d}_{safe_title}.txt")
            }
    
    def _fix_chapter_format(self, raw_chapter: str, document_text: str, index: int) -> Dict:
        """
        让 AI 修复章节格式
        
        Args:
            raw_chapter: 原始章节数据（可能是字符串或其他格式）
            document_text: 文档文本
            index: 章节索引
            
        Returns:
            修复后的章节字典
        """
        prompt = get_fix_chapter_format_prompt(raw_chapter, document_text)
        
        try:
            response = self.client.generate_content(
                prompt,
                system_instruction=self.system_instruction,
                temperature=0.3
            )
            
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                fixed = json.loads(json_match.group())
            else:
                fixed = json.loads(response)
            
            return fixed
        except:
            # 如果修复失败，返回默认格式
            return {
                "number": f"{index:02d}",
                "title": f"Chapter {index+1}",
                "start_line": 1,
                "end_line": len(document_text.split('\n')),
                "filename": f"{index:02d}_Chapter_{index+1}.txt"
            }
    
    def further_breakdown(self, chapters: List[Dict], max_words_per_chapter: Optional[int] = None) -> None:
        """
        阶段三：进一步拆分（采用 breakdown.md 的方法：在完整句子处断开）
        
        Args:
            chapters: 章节信息列表
            max_words_per_chapter: 每章最大字数（英文 word），固定为 7000
        """
        print("\n" + "=" * 70)
        print("阶段三：进一步拆分（Further Breakdown）")
        print("=" * 70)
        
        # 固定使用 7000 英文单词作为限制
        max_words_per_chapter = 7000
        
        print(f"每章最大字数限制：{max_words_per_chapter} 英文单词（固定值）")
        
        # 修复格式错误的章节
        fixed_chapters = []
        for i, chapter in enumerate(chapters):
            if not isinstance(chapter, dict):
                print(f"  ⚠️  检测到格式错误的章节（索引 {i}），正在让 AI 修复...")
                # 尝试读取文件来推断章节信息
                all_files = sorted(self.chapters_dir.glob("*.txt"))
                if i < len(all_files):
                    # 使用文件名推断
                    filename = all_files[i].name
                    fixed = {
                        "number": f"{i:02d}",
                        "title": filename.replace('.txt', '').replace('_', ' '),
                        "start_line": 1,
                        "end_line": 1000,
                        "filename": filename
                    }
                else:
                    fixed = self._fix_chapter_format(str(chapter), "", i)
                fixed_chapters.append(fixed)
                chapter = fixed
            else:
                fixed_chapters.append(chapter)
        
        # 更新 chapters 列表
        if fixed_chapters != chapters:
            chapters[:] = fixed_chapters
        
        for chapter in chapters:
            # 跳过非正文章节（不需要进一步拆分）
            if chapter.get('is_non_content', False):
                continue
            
            filename = chapter.get('filename', '')
            chapter_path = self.chapters_dir / filename
            
            if not chapter_path.exists():
                continue
            
            chapter_content = read_file(chapter_path)
            
            # 使用正确的英文单词统计（不是 token，也不是简单的 split）
            chapter_length = len(chapter_content)
            word_count = count_words(chapter_content)  # 使用 count_words 函数统计英文单词
            lines = chapter_content.split('\n')
            
            print(f"\n评估章节: {filename}")
            print(f"  字数：{word_count} 英文单词（不是 token）")
            
            # 如果章节不超过限制，跳过
            if word_count <= max_words_per_chapter:
                print(f"  → 无需拆分（{word_count} <= {max_words_per_chapter}）")
                continue
            
            # 使用 breakdown.md 的方法：在完整句子处断开
            print(f"  → 需要拆分（{word_count} > {max_words_per_chapter}），使用 breakdown.md 的方法...")
            
            try:
                from .utils import split_at_sentences
                chunks = split_at_sentences(chapter_content, max_words_per_chapter)
                
                print(f"  → 拆分成 {len(chunks)} 个部分（在完整句子处断开）")
                
                base_name = filename.rsplit('.', 1)[0]
                total_words = 0
                
                for i, chunk in enumerate(chunks, 1):
                    # 如果只有一个部分，保持原文件名；否则添加 _partXX
                    if len(chunks) == 1:
                        chunk_filename = filename
                    else:
                        chunk_filename = f"{base_name}_part{i:02d}.txt"
                    
                    chunk_path = self.chapters_dir / chunk_filename
                    write_file(chunk_path, chunk)
                    
                    chunk_word_count = count_words(chunk)
                    total_words += chunk_word_count
                    print(f"    ✓ {chunk_filename}: {chunk_word_count} 英文单词")
                
                # 验证字数（允许 5% 误差）
                if abs(total_words - word_count) > word_count * 0.05:
                    print(f"  ⚠️  警告：拆分后总字数 ({total_words}) 与原始字数 ({word_count}) 差异较大")
                else:
                    print(f"  ✅ 字数验证通过：{total_words} ≈ {word_count}")
                
                # 删除原始章节文件（因为已经拆分成多个部分）
                if chapter_path.exists() and len(chunks) > 1:
                    chapter_path.unlink()
                    print(f"  ✓ 已删除原始文件: {filename}")
                
            except Exception as e:
                print(f"  ❌ 拆分失败: {str(e)}")
                import traceback
                traceback.print_exc()
                continue
    
    def verify_chapters_completeness(self, original_text: str, chapters: List[Dict]) -> List[Dict]:
        """
        验证章节拆分完整性：检查拆分后的章节字数是否与原文一致
        
        Args:
            original_text: 原始文档文本
            chapters: 章节信息列表
        """
        print("\n" + "=" * 70)
        print("验证章节拆分完整性")
        print("=" * 70)
        
        original_word_count = count_words(original_text)
        original_char_count = len(original_text)
        
        combined_word_count = 0
        combined_char_count = 0
        
        print(f"原文统计：")
        print(f"  - 字符数：{original_char_count:,}")
        print(f"  - 字数：{original_word_count:,}")
        
        print(f"\n拆分后章节统计：")
        # 修复格式错误的章节
        fixed_chapters = []
        for i, chapter in enumerate(chapters):
            if not isinstance(chapter, dict):
                print(f"  ⚠️  检测到格式错误的章节（索引 {i}），正在让 AI 修复...")
                fixed = self._fix_chapter_format(str(chapter), original_text, i)
                fixed_chapters.append(fixed)
                chapter = fixed
            else:
                fixed_chapters.append(chapter)
            
            filename = chapter.get('filename', '')
            chapter_path = self.chapters_dir / filename
            
            if chapter_path.exists():
                chapter_content = read_file(chapter_path)
                chapter_words = count_words(chapter_content)
                chapter_chars = len(chapter_content)
                
                combined_word_count += chapter_words
                combined_char_count += chapter_chars
                
                print(f"  - {filename}: {chapter_chars:,} 字符, {chapter_words:,} 字")
        
        # 更新 chapters 列表（如果修复了任何章节）
        if fixed_chapters != chapters:
            chapters[:] = fixed_chapters
        
        print(f"\n合并统计：")
        print(f"  - 字符数：{combined_char_count:,}")
        print(f"  - 字数：{combined_word_count:,}")
        
        # 计算差异
        char_diff = abs(original_char_count - combined_char_count)
        word_diff = abs(original_word_count - combined_word_count)
        char_diff_pct = (char_diff / original_char_count * 100) if original_char_count > 0 else 0
        word_diff_pct = (word_diff / original_word_count * 100) if original_word_count > 0 else 0
        
        print(f"\n差异：")
        print(f"  - 字符数差异：{char_diff:,} ({char_diff_pct:.2f}%)")
        print(f"  - 字数差异：{word_diff:,} ({word_diff_pct:.2f}%)")
        
        if char_diff_pct < 1 and word_diff_pct < 1:
            print(f"\n✅ 验证通过：拆分后的内容与原文基本一致（差异 < 1%）")
        elif char_diff_pct < 5 and word_diff_pct < 5:
            print(f"\n⚠️  警告：拆分后的内容与原文有轻微差异（差异 < 5%），可能是由于格式处理")
        else:
            print(f"\n❌ 错误：拆分后的内容与原文差异较大（差异 {char_diff_pct:.2f}% >= 5%）")
            print(f"  让 AI 重新识别章节...")
            
            # 让 AI 重新识别章节
            retry_prompt = f"""之前的章节识别有严重错误，拆分后的内容与原文差异 {char_diff_pct:.2f}%，说明章节边界识别不准确。

原文统计：
- 字符数：{original_char_count:,}
- 字数：{original_word_count:,}

拆分后统计：
- 字符数：{combined_char_count:,}
- 字数：{combined_word_count:,}

**问题**：章节边界识别不准确，导致大量内容丢失。

请重新仔细分析文档，**准确识别所有章节的起始和结束行号**，确保：
1. 所有章节的行号覆盖整个文档（从第 1 行到最后一行）
2. 相邻章节的行号连续（前一个章节的 end_line + 1 = 下一个章节的 start_line）
3. 所有章节的 end_line 加起来应该等于文档总行数（或接近）

文档总行数：{len(original_text.split(chr(10))):,} 行

请返回 JSON 格式的章节信息（必须准确）："""
            
            try:
                retry_response = self.client.generate_content(
                    retry_prompt,
                    system_instruction=self.system_instruction,
                    temperature=0.3
                )
                
                json_match = re.search(r'\{.*\}', retry_response, re.DOTALL)
                if json_match:
                    retry_result = json.loads(json_match.group())
                else:
                    retry_result = json.loads(retry_response)
                
                retry_chapters = retry_result.get('chapters', [])
                if retry_chapters and len(retry_chapters) > 0:
                    print(f"  ✓ AI 重新识别了 {len(retry_chapters)} 个章节")
                    # 更新 chapters 列表
                    chapters[:] = retry_chapters
                    # 重新拆分章节
                    print("  重新拆分章节...")
                    self.split_chapters(original_text, chapters)
                    # 再次验证（递归调用，但限制深度）
                    print("  再次验证...")
                    return self.verify_chapters_completeness(original_text, chapters)
                else:
                    print(f"  ⚠️  AI 重新识别返回空列表")
                    return chapters
            except Exception as e:
                print(f"  ⚠️  AI 重新识别失败: {str(e)}")
                return chapters
        
        return chapters
    
    def verify_further_breakdown_completeness(self, chapters: List[Dict]) -> None:
        """
        验证进一步拆分后的完整性：检查每个章节拆分后的部分是否与原始章节一致
        
        Args:
            chapters: 章节信息列表
        """
        print("\n" + "=" * 70)
        print("验证进一步拆分完整性")
        print("=" * 70)
        
        all_chapter_files = sorted(self.chapters_dir.glob("*.txt"))
        
        # 修复格式错误的章节
        fixed_chapters = []
        for i, chapter in enumerate(chapters):
            if not isinstance(chapter, dict):
                print(f"  ⚠️  检测到格式错误的章节（索引 {i}），正在让 AI 修复...")
                # 尝试从字符串中提取信息或使用默认值
                if isinstance(chapter, str):
                    # 尝试读取对应的文件来推断
                    # 如果字符串看起来像文件名，尝试使用它
                    if chapter.endswith('.txt'):
                        fixed = {
                            "number": f"{i:02d}",
                            "title": chapter.replace('.txt', '').replace('_', ' '),
                            "start_line": 1,
                            "end_line": 1000,
                            "filename": chapter
                        }
                    else:
                        fixed = self._fix_chapter_format(chapter, "", i)
                else:
                    fixed = {
                        "number": f"{i:02d}",
                        "title": f"Chapter {i+1}",
                        "start_line": 1,
                        "end_line": 1000,
                        "filename": f"{i:02d}_Chapter_{i+1}.txt"
                    }
                fixed_chapters.append(fixed)
                chapter = fixed
            else:
                fixed_chapters.append(chapter)
        
        # 更新 chapters 列表（如果修复了任何章节）
        if fixed_chapters != chapters:
            chapters[:] = fixed_chapters
        
        # 找出哪些是原始章节，哪些是拆分后的部分
        original_chapters = {ch.get('filename', '') for ch in chapters if isinstance(ch, dict)}
        split_parts = {}  # {original_filename: [part_files]}
        
        for file in all_chapter_files:
            filename = file.name
            # 检查是否是拆分后的部分（包含 _part）
            if '_part' in filename:
                # 提取原始章节名
                base_name = filename.rsplit('_part', 1)[0] + '.txt'
                if base_name not in split_parts:
                    split_parts[base_name] = []
                split_parts[base_name].append(file)
        
        if not split_parts:
            print("  没有需要验证的拆分章节")
            return
        
        # 验证每个被拆分的章节
        for original_filename, part_files in split_parts.items():
            original_path = self.chapters_dir / original_filename
            if not original_path.exists():
                continue
            
            original_content = read_file(original_path)
            original_words = count_words(original_content)
            original_chars = len(original_content)
            
            combined_words = 0
            combined_chars = 0
            
            print(f"\n验证章节: {original_filename}")
            print(f"  原始：{original_chars:,} 字符, {original_words:,} 字")
            
            for part_file in sorted(part_files):
                part_content = read_file(part_file)
                part_words = count_words(part_content)
                part_chars = len(part_content)
                
                combined_words += part_words
                combined_chars += part_chars
                
                print(f"  - {part_file.name}: {part_chars:,} 字符, {part_words:,} 字")
            
            print(f"  合并：{combined_chars:,} 字符, {combined_words:,} 字")
            
            char_diff = abs(original_chars - combined_chars)
            word_diff = abs(original_words - combined_words)
            char_diff_pct = (char_diff / original_chars * 100) if original_chars > 0 else 0
            word_diff_pct = (word_diff / original_words * 100) if original_words > 0 else 0
            
            if char_diff_pct < 1 and word_diff_pct < 1:
                print(f"  ✅ 验证通过（差异 < 1%）")
            elif char_diff_pct < 5 and word_diff_pct < 5:
                print(f"  ⚠️  轻微差异（差异 < 5%）")
            else:
                print(f"  ❌ 差异较大（差异 >= 5%）")
    
    def analyze_chapters(self, chapters: List[Dict]) -> None:
        """
        阶段四：逐章深度阅读与分析
        
        Args:
            chapters: 章节信息列表
        """
        print("\n" + "=" * 70)
        print("阶段四：逐章深度阅读与分析")
        print("=" * 70)
        
        # 修复格式错误的章节
        fixed_chapters = []
        for i, chapter in enumerate(chapters):
            if not isinstance(chapter, dict):
                print(f"  ⚠️  检测到格式错误的章节（索引 {i}），正在让 AI 修复...")
                # 尝试从文件名推断
                all_files = sorted(self.chapters_dir.glob("*.txt"))
                # 过滤掉 part 文件
                all_files = [f for f in all_files if '_part' not in f.name]
                if i < len(all_files):
                    filename = all_files[i].name
                    fixed = {
                        "number": f"{i:02d}",
                        "title": filename.replace('.txt', '').replace('_', ' '),
                        "start_line": 1,
                        "end_line": 1000,
                        "filename": filename
                    }
                else:
                    fixed = self._fix_chapter_format(str(chapter), "", i)
                fixed_chapters.append(fixed)
                chapter = fixed
            else:
                fixed_chapters.append(chapter)
        
        # 更新 chapters 列表
        if fixed_chapters != chapters:
            chapters[:] = fixed_chapters
        
        previous_summary = None
        
        for i, chapter in enumerate(chapters):
            filename = chapter.get('filename', '')
            chapter_path = self.chapters_dir / filename
            
            # 如果原始文件不存在，检查是否有 part 文件
            if not chapter_path.exists():
                # 查找对应的 part 文件
                base_name = filename.rsplit('.', 1)[0]  # 去掉 .txt 扩展名
                part_files = sorted(self.chapters_dir.glob(f"{base_name}_part*.txt"))
                
                if part_files:
                    # 为每个 part 单独生成 summary
                    print(f"\n分析章节 {i+1}/{len(chapters)}: {filename} (由 {len(part_files)} 个部分组成，将分别为每个部分生成总结)")
                    
                    # 为每个 part 生成独立的 summary
                    for part_idx, part_file in enumerate(part_files, 1):
                        try:
                            part_content = read_file(part_file)
                        except Exception as e:
                            print(f"    ⚠️  读取 part 文件失败: {part_file.name}, 错误: {str(e)}")
                            continue
                        
                        # 尝试从 part 内容中提取标题（前几行）
                        part_lines = part_content.split('\n')[:20]
                        part_title = None
                        for line in part_lines:
                            # 查找可能的标题（大写、单独一行、不太长）
                            stripped = line.strip()
                            if stripped and len(stripped) < 100 and not stripped.startswith(('Chapter', 'CHAPTER', 'Part')):
                                # 检查是否像标题（首字母大写、没有句号）
                                if stripped[0].isupper() and '.' not in stripped and len(stripped.split()) < 15:
                                    part_title = stripped
                                    break
                        
                        if not part_title:
                            part_title = f"{chapter.get('title', base_name)} - 第 {part_idx} 部分"
                        
                        part_metadata = {
                            "number": f"{chapter.get('number', '')}_part{part_idx:02d}",
                            "title": part_title,
                            "filename": part_file.name
                        }
                        
                        print(f"  分析部分 {part_idx}/{len(part_files)}: {part_file.name}")
                        
                        # 让 AI 决定需要多少上下文和内容
                        part_length = len(part_content)
                        prev_summary_length = len(previous_summary) if previous_summary else 0
                        
                        context_strategy_prompt = get_context_strategy_prompt(part_length, prev_summary_length)
                        
                        print(f"    AI 正在决定分析策略...")
                        context_strategy_response = self.client.generate_content(
                            context_strategy_prompt,
                            system_instruction=self.system_instruction,
                            temperature=0.3
                        )
                        
                        # 解析策略
                        try:
                            strategy_match = re.search(r'\{.*\}', context_strategy_response, re.DOTALL)
                            if strategy_match:
                                context_strategy = json.loads(strategy_match.group())
                            else:
                                context_strategy = json.loads(context_strategy_response)
                            
                            # 决定使用多少前一章总结
                            prev_to_use = context_strategy.get('previous_summary_to_use', 'all')
                            if prev_to_use == 'all' or not previous_summary:
                                context = previous_summary if previous_summary else ""
                            else:
                                prev_len = int(prev_to_use) if isinstance(prev_to_use, (int, str)) and str(prev_to_use).isdigit() else len(previous_summary)
                                context = previous_summary[:prev_len] if previous_summary else ""
                            
                            # 决定读取多少章节内容
                            content_to_read = context_strategy.get('chapter_content_to_read', 'all')
                            if content_to_read == 'all':
                                analysis_content = part_content
                            else:
                                content_len = int(content_to_read) if isinstance(content_to_read, (int, str)) and str(content_to_read).isdigit() else len(part_content)
                                analysis_content = part_content[:content_len]
                        except:
                            # 如果 AI 决策失败，使用全部内容
                            context = previous_summary if previous_summary else ""
                            analysis_content = part_content
                        
                        # 构建分析提示词
                        context_str = f"前一章总结（用于上下文连贯）：\n{context}\n\n" if context else ""
                        prompt = get_chapter_analysis_prompt(context_str, part_metadata, analysis_content)
                        
                        print(f"    AI 正在分析...")
                        try:
                            part_summary = self.client.generate_content(
                                prompt,
                                system_instruction=self.system_instruction,
                                temperature=0.7
                            )
                            
                            # 保存 part 的总结
                            part_base_name = part_file.stem  # 例如 "02_Main_Body_part01"
                            part_summary_filename = f"{part_base_name}_summary.md"
                            part_summary_path = self.summaries_dir / part_summary_filename
                            
                            write_file(part_summary_path, part_summary)
                            print(f"    ✓ 总结已保存: {part_summary_filename}")
                            
                            # 更新前章总结（用于下一部分）
                            previous_summary = part_summary
                        except Exception as e:
                            print(f"    ⚠️  处理 part {part_idx} 失败: {str(e)}")
                            import traceback
                            traceback.print_exc()
                            # 继续处理下一个 part
                            continue
                    
                    # 跳过原始章节的处理（因为已经为每个 part 生成了 summary）
                    continue
                else:
                    print(f"\n⚠️  跳过: {filename} (文件不存在，也没有找到 part 文件)")
                    continue
            else:
                print(f"\n分析章节 {i+1}/{len(chapters)}: {filename}")
                chapter_content = read_file(chapter_path)
            
            chapter_metadata = {
                "number": chapter.get('number', ''),
                "title": chapter.get('title', ''),
                "filename": filename
            }
            
            # 让 AI 决定需要多少上下文和内容
            chapter_length = len(chapter_content)
            prev_summary_length = len(previous_summary) if previous_summary else 0
            
            context_strategy_prompt = get_context_strategy_prompt(chapter_length, prev_summary_length)
            
            print(f"  AI 正在决定分析策略...")
            context_strategy_response = self.client.generate_content(
                context_strategy_prompt,
                system_instruction=self.system_instruction,
                temperature=0.3
            )
            
            # 解析策略
            try:
                strategy_match = re.search(r'\{.*\}', context_strategy_response, re.DOTALL)
                if strategy_match:
                    context_strategy = json.loads(strategy_match.group())
                else:
                    context_strategy = json.loads(context_strategy_response)
                
                # 决定使用多少前一章总结
                prev_to_use = context_strategy.get('previous_summary_to_use', 'all')
                if prev_to_use == 'all' or not previous_summary:
                    context = previous_summary if previous_summary else ""
                else:
                    prev_len = int(prev_to_use) if isinstance(prev_to_use, (int, str)) and str(prev_to_use).isdigit() else len(previous_summary)
                    context = previous_summary[:prev_len] if previous_summary else ""
                
                # 决定读取多少章节内容
                content_to_read = context_strategy.get('chapter_content_to_read', 'all')
                if content_to_read == 'all':
                    analysis_content = chapter_content
                else:
                    content_len = int(content_to_read) if isinstance(content_to_read, (int, str)) and str(content_to_read).isdigit() else len(chapter_content)
                    analysis_content = chapter_content[:content_len]
            except:
                # 如果 AI 决策失败，使用全部内容
                context = previous_summary if previous_summary else ""
                analysis_content = chapter_content
            
            # 构建分析提示词
            context_str = f"前一章总结（用于上下文连贯）：\n{context}\n\n" if context else ""
            prompt = get_chapter_analysis_prompt(context_str, chapter_metadata, analysis_content)
            
            print("  AI 正在分析...")
            summary = self.client.generate_content(
                prompt,
                system_instruction=self.system_instruction,
                temperature=0.7
            )
            
            # 保存总结
            base_name = filename.rsplit('.', 1)[0]
            summary_filename = f"{base_name}_summary.md"
            summary_path = self.summaries_dir / summary_filename
            
            write_file(summary_path, summary)
            print(f"  ✓ 总结已保存: {summary_filename}")
            
            # 更新前章总结（用于下一章）
            # AI 已经在 analyze_chapters 中决定使用多少上下文，这里保存完整总结
            previous_summary = summary
    
    def generate_outputs(self) -> None:
        """
        阶段五：生成 PDF 和 HTML 输出
        """
        print("\n" + "=" * 70)
        print("阶段五：格式转换与输出")
        print("=" * 70)
        
        # 检查是否有封面文件（支持 .md 和没有扩展名）
        cover_info = None
        cover_file_md = self.summaries_dir / "00_Cover.md"
        cover_file_no_ext = self.summaries_dir / "00_Cover"
        
        if cover_file_md.exists():
            try:
                cover_content = read_file(cover_file_md)
                cover_info = self._parse_cover_file(cover_content)
                print(f"  ✓ 找到封面文件: {cover_file_md}")
            except Exception as e:
                print(f"  ⚠️  读取封面文件失败: {e}")
        elif cover_file_no_ext.exists():
            try:
                cover_content = read_file(cover_file_no_ext)
                cover_info = self._parse_cover_file(cover_content)
                print(f"  ✓ 找到封面文件: {cover_file_no_ext}")
            except Exception as e:
                print(f"  ⚠️  读取封面文件失败: {e}")
        
        # 收集所有总结文件（排除封面文件）
        summary_files = sorted([f for f in self.summaries_dir.glob("*.md") if f.name != "00_Cover.md"])
        
        if not summary_files:
            print("⚠️  没有找到总结文件")
            return
        
        # 合并所有 Markdown 文件
        print("\n合并 Markdown 文件...")
        combined_content = ""
        
        for i, summary_file in enumerate(summary_files):
            content = read_file(summary_file)
            
            # 提取章节标题（第一行的 # 标题）
            title_match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
            if title_match:
                chapter_title = title_match.group(1).strip()
            else:
                # 如果没有找到标题，使用文件名
                chapter_title = summary_file.stem.replace('_summary', '').replace('_', ' ')
            
            # 如果不是第一个章节，添加分割线
            if i > 0:
                combined_content += "\n\n<div class='chapter-divider'></div>\n\n"
            
            # 确保章节标题存在
            # 如果原内容没有标题，添加一个；如果有标题，直接使用原内容
            if not title_match:
                combined_content += f"# {chapter_title}\n\n"
                combined_content += content
            else:
                # 如果已经有标题，直接添加内容（标题已经在内容中）
                combined_content += content
            
            # 章节之间添加空行
            combined_content += "\n\n"
        
        # 生成 PDF（使用新的 pdf_generator 模块）
        try:
            from .pdf_generator import generate_pdf_from_combined_content
            from datetime import datetime
            
            print("生成 PDF...")
            
            # 获取书籍信息
            # 优先使用封面文件中的信息
            if cover_info:
                book_title = cover_info.get('title', '书籍总结')
                book_author = cover_info.get('author', '未知作者')
                gen_date = cover_info.get('date', datetime.now().strftime("%Y/%m/%d"))
                model_name = cover_info.get('model', self.client.model_name)
            else:
                # 从第一个总结文件推断，或使用通用标题
                book_title = "书籍总结"
                book_author = "未知作者"
                
                # 尝试从输入文件名提取作者和标题信息（使用 pdf_generator 的函数）
                try:
                    from .pdf_generator import extract_book_info_from_filename
                    if hasattr(self, 'input_file_path') and self.input_file_path:
                        extracted_title, extracted_author = extract_book_info_from_filename(self.input_file_path.name)
                        if extracted_title and extracted_title != "书籍摘要":
                            book_title = extracted_title
                        if extracted_author:
                            book_author = extracted_author
                    elif hasattr(self, 'input_path'):
                        input_file = Path(self.input_path)
                        if input_file.exists():
                            extracted_title, extracted_author = extract_book_info_from_filename(input_file.name)
                            if extracted_title and extracted_title != "书籍摘要":
                                book_title = extracted_title
                            if extracted_author:
                                book_author = extracted_author
                except Exception as e:
                    # 如果提取失败，使用旧的方法作为后备
                    if hasattr(self, 'input_file_path') and self.input_file_path:
                        input_filename = self.input_file_path.stem
                        if ' - ' in input_filename:
                            parts = input_filename.split(' - ', 1)
                            if len(parts) == 2:
                                book_author = parts[0].strip()
                                potential_title = parts[1].strip()
                                if len(potential_title) < 100:  # 合理的标题长度
                                    book_title = potential_title
                
                if summary_files:
                    first_summary = read_file(summary_files[0])
                    # 尝试提取标题
                    title_match = re.search(r'^#\s+(.+)$', first_summary, re.MULTILINE)
                    if title_match:
                        # 如果第一个章节标题看起来像书名，使用它；否则使用通用标题
                        potential_title = title_match.group(1).strip()
                        # 如果标题太长（可能是章节名而不是书名），使用通用标题
                        if len(potential_title) < 50 and book_title == "书籍总结":
                            book_title = potential_title
                
                # 生成日期
                gen_date = datetime.now().strftime("%Y/%m/%d")
                
                # 获取模型名称
                model_name = self.client.model_name
            
            # 收集目录项
            toc_items = []
            for summary_file in summary_files:
                content = read_file(summary_file)
                title_match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
                if title_match:
                    title = title_match.group(1).strip()
                    # 标准化标题（移除"第x章"格式）
                    title = re.sub(r'^第[一二三四五六七八九十百千万\d]+章[：:\s]*', '', title)
                    title = re.sub(r'^第\d+章[：:\s]*', '', title)
                    toc_items.append(title.strip())
            
            # 使用新的 PDF 生成模块
            pdf_path = self.pdf_dir / "book_summary.pdf"
            generate_pdf_from_combined_content(
                combined_content, 
                pdf_path,
                book_title, 
                book_author,
                model_name,
                gen_date,
                toc_items,
                summaries_dir=self.summaries_dir  # 传递 summaries_dir 以支持 00_Cover 文件
            )
            
            print(f"  ✓ PDF 已生成: {pdf_path}")
        except ImportError as e:
            print("  ⚠️  playwright 未安装，跳过 PDF 生成")
            print("  提示: 要启用 PDF 生成功能，需要完成以下两步:")
            print("    1. pip install playwright")
            print("    2. playwright install chromium  ← 这一步很重要！")
            print("  详细说明请查看 README.md 中的「安装 PDF 生成依赖」部分")
        except RuntimeError as e:
            print(f"  ⚠️  PDF 生成失败: {str(e)}")
            print("  详细说明请查看 README.md 中的「安装 PDF 生成依赖」部分")
        except Exception as e:
            error_msg = str(e)
            print(f"  ⚠️  PDF 生成失败: {error_msg}")
            import traceback
            traceback.print_exc()
        
        # 生成 HTML 交互界面
        print("生成 HTML 交互界面...")
        self._generate_html_interface(summary_files)
        print(f"  ✓ HTML 已生成: {self.html_dir / 'interactive_reader.html'}")
    
    def _generate_pdf_html(self, content: str, book_title: str, book_author: str, model_name: str, gen_date: str, toc_items: list = None) -> str:
        """生成包含封面和样式的 PDF HTML（用于 Playwright）"""
        import markdown
        
        # 清理文本（移除不需要的文字）
        def clean_text(text):
            """移除不需要的文字，特别是第一行的Expert Ghost-Reader相关文字"""
            lines = text.split('\n')
            
            # 检查并移除第一行的Expert Ghost-Reader相关文字
            if lines:
                first_line = lines[0].strip()
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
        
        # 标准化标题
        def standardize_title(title):
            """标准化标题，移除'第x章'或'第x章：'格式"""
            title = re.sub(r'^第[一二三四五六七八九十百千万\d]+章[：:\s]*', '', title)
            title = re.sub(r'^第\d+章[：:\s]*', '', title)
            return title.strip()
        
        # 清理内容
        content = clean_text(content)
        
        # 转换 Markdown 为 HTML
        html_body = markdown.markdown(content, extensions=['extra', 'codehilite', 'tables'])
        
        # 处理章节分隔：为每个 h1 添加 chapter 类（除了第一个）
        # 先找到所有 h1 标签
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
        
        # 使用模板生成 HTML
        return get_pdf_html_template(html_body, book_title, book_author, model_name, gen_date, toc_items)
    
    def _parse_cover_file(self, cover_content: str) -> dict:
        """解析封面文件内容
        
        格式示例：
        CAESAR - life of a colossus
        
        by Adrian Goldsworthy
        
        YALE UNIVERSITY PRESS
        
        Summarized by Vibe_reading (Gemini 2.5 pro)
        2026/01/26
        """
        lines = [line.strip() for line in cover_content.split('\n') if line.strip()]
        
        cover_info = {}
        
        if not lines:
            return cover_info
        
        # 第一行通常是书名（可能包含 " - " 分隔符，如 "CAESAR - life of a colossus"）
        title_line = lines[0]
        # 如果包含 " - "，通常是 "TITLE - subtitle" 格式，整个作为书名
        # 或者可能是 "AUTHOR - TITLE"，但通常第一行就是书名
        cover_info['title'] = title_line
        
        # 查找 "by" 开头的作者行
        for line in lines:
            if line.lower().startswith('by '):
                cover_info['author'] = line[3:].strip()
                break
        
        # 查找 "Summarized by" 行
        for line in lines:
            if 'summarized by' in line.lower():
                # 提取模型名称（可能在括号中）
                model_match = re.search(r'\(([^)]+)\)', line)
                if model_match:
                    cover_info['model'] = model_match.group(1).strip()
                break
        
        # 查找日期（格式：YYYY/MM/DD 或 YYYY-MM-DD）
        for line in lines:
            date_match = re.search(r'(\d{4}[/-]\d{1,2}[/-]\d{1,2})', line)
            if date_match:
                date_str = date_match.group(1)
                # 统一格式为 YYYY/MM/DD
                date_str = date_str.replace('-', '/')
                cover_info['date'] = date_str
                break
        
        return cover_info
    
    def _get_pdf_css(self) -> str:
        """返回 PDF 专业排版 CSS"""
        return get_pdf_css()
    
    def _get_html_css(self) -> str:
        """返回专业 HTML CSS 样式"""
        return get_html_css()
    
    def _get_html_javascript(self, summary_files: List[Path]) -> str:
        """返回 HTML JavaScript 代码"""
        import re
        
        # 读取总结文件，提取标题和内容
        summaries_data = {}
        chapter_titles = {}
        chapter_originals = {}  # 存储章节原文
        
        for f in summary_files:
            key = str(f.stem)
            content = read_file(f)
            summaries_data[key] = content
            
            # 提取标题（第一行的 # 标题）
            title_match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
            if title_match:
                chapter_titles[key] = title_match.group(1).strip()
            else:
                # 如果没有找到标题，使用文件名
                chapter_titles[key] = key.replace('_summary', '').replace('_', ' ')
            
            # 读取对应的章节原文
            # 总结文件名格式：XX_Chapter_summary.md
            # 原文文件名格式：XX_Chapter.txt 或 XX_Chapter_part01.txt 等
            original_key = key.replace('_summary', '')
            
            # 尝试查找原文文件（可能是单个文件或多个 part 文件）
            original_files = sorted(self.chapters_dir.glob(f"{original_key}.txt"))
            if not original_files:
                # 如果没有找到，尝试查找 part 文件
                original_files = sorted(self.chapters_dir.glob(f"{original_key}_part*.txt"))
            
            if original_files:
                # 合并所有 part 文件的内容
                original_content = ""
                for orig_file in original_files:
                    original_content += read_file(orig_file) + "\n\n"
                chapter_originals[key] = original_content.strip()
            else:
                # 如果找不到原文，使用空字符串
                chapter_originals[key] = ""
        
        # 获取 API key 和模型名称
        api_key = self.client.api_key
        model_name = self.client.model_name
        
        return get_html_javascript_template(
            summaries_data, chapter_originals, chapter_titles, api_key, model_name
        )
    
    def _generate_html_interface(self, summary_files: List[Path]) -> None:
        """生成 HTML 交互界面（专业美工设计）"""
        html_css = self._get_html_css()
        html_javascript = self._get_html_javascript(summary_files)
        html_content = get_html_interface_template(html_css, html_javascript, len(summary_files))
        write_file(self.html_dir / "interactive_reader.html", html_content)
    
    def process(self, input_path: Path) -> None:
        """
        处理完整流程
        
        包含以下阶段：
        1. 文档预处理：EPUB → TXT 转换（如需要）
        2. 智能章节识别：AI 自动识别章节结构（带渐进式预览和错误修复）
        3. 章节拆分：AI 评估章节长度，必要时拆分
        4. 逐章分析：AI 深度阅读每章，生成总结（带智能重试机制）
        5. 格式输出：生成 Markdown、PDF（自动生成封面）、HTML
        
        Args:
            input_path: 输入文件路径
        """
        # 保存输入文件路径，用于后续提取元数据
        self.input_file_path = Path(input_path)
        print("=" * 70)
        print("Vibe Reading Skill - 开始处理")
        print("=" * 70)
        
        # 阶段一：预处理
        document_text = self.preprocess_document(input_path)
        
        # 阶段二：章节识别
        chapters = self.identify_chapters(document_text)
        if not chapters or len(chapters) == 0:
            print("⚠️  未能识别章节，但会继续尝试处理...")
            # 不再直接返回，而是继续尝试处理
            # 如果确实无法识别，会在后续步骤中处理
        
        # 拆分章节
        self.split_chapters(document_text, chapters)
        
        # 验证章节拆分完整性（如果差距太大，会重新识别并更新 chapters）
        chapters = self.verify_chapters_completeness(document_text, chapters)
        
        # 阶段三：进一步拆分
        # 固定使用 7000 英文单词
        self.further_breakdown(chapters, max_words_per_chapter=7000)
        
        # 验证进一步拆分后的完整性
        self.verify_further_breakdown_completeness(chapters)
        
        # 阶段四：分析
        self.analyze_chapters(chapters)
        
        # 阶段五：生成输出
        self.generate_outputs()
        
        print("\n" + "=" * 70)
        print("处理完成！")
        print(f"输入目录: {self.input_dir}")
        print(f"章节文件: {self.chapters_dir}")
        print(f"总结文件: {self.summaries_dir}")
        print(f"PDF 文件: {self.pdf_dir}")
        print(f"HTML 文件: {self.html_dir}")
        print("=" * 70)


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="Vibe Reading Skill - 智能阅读分析")
    parser.add_argument("--input", "-i", type=Path, help="输入文件路径（EPUB 或 TXT），如果不提供则从 input/ 目录读取")
    parser.add_argument("--base-dir", "-d", type=Path, default=Path("."), help="项目根目录（默认: 当前目录）")
    parser.add_argument("--api-key", type=str, help="Gemini API Key（可选，也可通过 .env 文件设置）")
    
    args = parser.parse_args()
    
    skill = VibeReadingSkill(api_key=args.api_key, base_dir=args.base_dir)
    
    # 确定输入文件
    if args.input:
        input_path = Path(args.input)
        if not input_path.exists():
            print(f"错误: 输入文件不存在: {input_path}")
            return
    else:
        # 从 input 目录查找文件
        input_files = list(skill.input_dir.glob("*.epub")) + list(skill.input_dir.glob("*.txt"))
        if not input_files:
            print(f"错误: 在 {skill.input_dir} 目录中未找到 EPUB 或 TXT 文件")
            print(f"请将文件放入 {skill.input_dir} 目录，或使用 --input 参数指定文件路径")
            return
        input_path = input_files[0]
        print(f"从 input 目录找到文件: {input_path}")
    
    skill.process(input_path)


if __name__ == "__main__":
    import re
    import json
    main()
