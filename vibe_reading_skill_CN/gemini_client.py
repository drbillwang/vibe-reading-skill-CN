"""
Gemini API 客户端封装
提供与 Google Gemini API 交互的接口

特性：
- 自动重试机制：遇到 429 配额限制错误时，自动重试最多 5 次
- 智能等待时间：从错误信息中提取建议等待时间，或使用预定义序列（60/90/120/150/180 秒）
- 代理支持：支持通过 HTTP_PROXY 和 HTTPS_PROXY 环境变量配置代理
"""

import os
import google.generativeai as genai
from dotenv import load_dotenv
from typing import List, Dict, Optional

# 加载环境变量
load_dotenv()

class GeminiClient:
    """Gemini API 客户端"""
    
    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None, proxy: Optional[str] = None):
        """
        初始化 Gemini 客户端
        
        Args:
            api_key: Gemini API Key，如果不提供则从环境变量读取
            model: 使用的模型名称，如果不提供则从环境变量读取，默认使用 gemini-2.5-pro
            proxy: 代理服务器地址（格式：http://host:port 或 https://host:port），用于解决地理位置限制
        """
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY not found. Please set it in .env file or pass as parameter.")
        
        # 支持的模型列表
        self.available_models = [
            "gemini-3-pro",        # Gemini 3 旗舰模型（最新，最强）
            "gemini-3",            # Gemini 3 标准模型
            "gemini-2.5-pro",      # Gemini 2.5 旗舰模型
            "gemini-2.5-flash",    # Gemini 2.5 快速模型
            "gemini-2.0-flash-exp", # 实验版本
            "gemini-1.5-pro",      # 稳定版本
            "gemini-1.5-flash",    # 快速版本
            "gemini-pro",          # 旧版本
        ]
        
        # 获取模型名称：参数 > 环境变量 > 默认值
        # 默认使用 gemini-2.5-pro（稳定可靠）
        default_model = os.getenv("GEMINI_MODEL", "gemini-2.5-pro")
        self.model_name = model or default_model
        
        # 验证模型是否在支持列表中（允许用户使用其他模型）
        if self.model_name not in self.available_models:
            print(f"⚠️  警告: 模型 '{self.model_name}' 不在推荐列表中，但将继续尝试使用")
            print(f"   推荐模型: {', '.join(self.available_models[:3])}")
        
        # 配置代理（如果提供）
        proxy_url = proxy or os.getenv("HTTP_PROXY") or os.getenv("HTTPS_PROXY")
        if proxy_url:
            print(f"🌐 使用代理: {proxy_url}")
            # 设置环境变量，让 google-generativeai 使用代理
            os.environ['HTTP_PROXY'] = proxy_url
            os.environ['HTTPS_PROXY'] = proxy_url
        
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel(self.model_name)
    
    def generate_content(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        temperature: float = 0.7,
        max_output_tokens: Optional[int] = None
    ) -> str:
        """
        生成内容（带智能重试机制）
        
        当遇到 API 配额限制（429 错误）时，会自动重试：
        - 最多重试 5 次
        - 等待时间：60 → 90 → 120 → 150 → 180 秒（如果错误信息中没有建议时间）
        - 如果错误信息包含建议等待时间，会优先使用该时间 + 5 秒缓冲
        
        Args:
            prompt: 用户提示
            system_instruction: 系统指令（可选）
            temperature: 温度参数
            max_output_tokens: 最大输出 token 数
        
        Returns:
            AI 生成的文本内容
        
        Raises:
            Exception: 如果达到最大重试次数仍失败，会抛出异常
        """
        generation_config = {
            "temperature": temperature,
        }
        if max_output_tokens:
            generation_config["max_output_tokens"] = max_output_tokens
        
        # 如果有系统指令，创建新的模型实例
        if system_instruction:
            model = genai.GenerativeModel(
                model_name=self.model_name,
                system_instruction=system_instruction
            )
        else:
            model = self.model
        
        import time
        max_retries_per_error = 5  # 每次遇到错误时重试 5 次
        # 重试延迟序列：60, 90, 120, 150, 180 秒
        retry_delays = [60, 90, 120, 150, 180]
        
        attempt = 0
        while attempt < max_retries_per_error:
            try:
                response = model.generate_content(
                    prompt,
                    generation_config=generation_config
                )
                return response.text
            except Exception as e:
                error_str = str(e)
                # 打印完整错误信息以便调试
                if attempt == 0:  # 只在第一次失败时打印完整错误
                    print(f"  🔍 完整错误信息: {error_str[:500]}...")  # 只打印前500字符
                
                # 检查是否是配额限制错误（429）
                if "429" in error_str or "Resource has been exhausted" in error_str or "quota" in error_str.lower():
                    if attempt < max_retries_per_error - 1:
                        # 尝试从错误信息中提取重试延迟时间（多种格式）
                        import re
                        retry_delay = None
                        
                        # 格式1: "retry in 13.429413162s"
                        delay_match = re.search(r'retry in ([\d.]+)\s*s', error_str, re.IGNORECASE)
                        if delay_match:
                            retry_delay = int(float(delay_match.group(1))) + 5  # 加5秒缓冲
                            print(f"  📋 从错误信息中提取到建议等待时间: {delay_match.group(1)} 秒")
                        
                        # 格式2: "Please retry in 13.429413162s"
                        if not retry_delay:
                            delay_match = re.search(r'Please retry in ([\d.]+)\s*s', error_str, re.IGNORECASE)
                            if delay_match:
                                retry_delay = int(float(delay_match.group(1))) + 5
                                print(f"  📋 从错误信息中提取到建议等待时间: {delay_match.group(1)} 秒")
                        
                        # 格式3: 检查异常对象的属性（Google API 可能在这里存储信息）
                        if not retry_delay and hasattr(e, 'retry_delay'):
                            retry_delay = int(e.retry_delay) + 5
                            print(f"  📋 从异常对象中提取到等待时间: {e.retry_delay} 秒")
                        
                        # 如果都没有提取到，使用预定义的延迟序列
                        if not retry_delay:
                            retry_delay = retry_delays[attempt]  # 60, 90, 120, 150, 180 秒
                            print(f"  📋 未找到建议等待时间，使用预定义延迟: {retry_delay} 秒")
                        
                        # 确保等待时间至少为序列中的最小值
                        retry_delay = max(retry_delay, retry_delays[0])
                        
                        print(f"  ⚠️  API 配额限制，等待 {retry_delay} 秒后重试 ({attempt + 1}/{max_retries_per_error})...")
                        time.sleep(retry_delay)
                        attempt += 1
                        continue
                    else:
                        # 达到最大重试次数，抛出异常（让上层处理，可能会再次调用这个函数）
                        raise Exception(f"Error generating content: {error_str}\n已达到最大重试次数 ({max_retries_per_error} 次)，请稍后再试或检查 API 配额。")
                else:
                    # 其他错误直接抛出
                    raise Exception(f"Error generating content: {error_str}")
    
    def generate_content_stream(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        temperature: float = 0.7
    ):
        """
        流式生成内容（用于长文本输出）
        
        Args:
            prompt: 用户提示
            system_instruction: 系统指令（可选）
            temperature: 温度参数
        
        Yields:
            AI 生成的文本片段
        """
        generation_config = {
            "temperature": temperature,
        }
        
        if system_instruction:
            model = genai.GenerativeModel(
                model_name=self.model_name,
                system_instruction=system_instruction
            )
        else:
            model = self.model
        
        try:
            response = model.generate_content(
                prompt,
                generation_config=generation_config,
                stream=True
            )
            for chunk in response:
                if chunk.text:
                    yield chunk.text
        except Exception as e:
            raise Exception(f"Error generating content: {str(e)}")
    
    def analyze_document_structure(self, document_content: str) -> Dict:
        """
        分析文档结构（章节识别）
        
        Args:
            document_content: 文档内容
        
        Returns:
            包含章节信息的字典
        """
        prompt = f"""请分析以下文档的章节结构。

文档内容：
{document_content[:50000]}  # 限制长度避免超出上下文窗口

请返回 JSON 格式的章节信息，包含：
- chapters: 章节列表，每个章节包含 number, title, start_line, end_line, filename, confidence

如果文档太长，请先分析前一部分，然后我可以继续提供后续内容。"""
        
        response = self.generate_content(prompt, temperature=0.3)
        return response
    
    def decide_breakdown_strategy(self, chapter_content: str, chapter_info: Dict) -> Dict:
        """
        决定章节是否需要进一步拆分
        
        Args:
            chapter_content: 章节内容
            chapter_info: 章节信息
        
        Returns:
            拆分决策和策略
        """
        prompt = f"""请评估以下章节是否需要进一步拆分。

章节信息：
{chapter_info}

章节内容（前 10000 字符）：
{chapter_content[:10000]}

请考虑：
1. 内容的复杂度和密度
2. 语义完整性
3. 分析质量要求
4. 上下文窗口限制

返回 JSON 格式：
{{
    "needs_breakdown": true/false,
    "reason": "原因",
    "breakdown_points": [拆分点列表],
    "parts": [部分列表]
}}"""
        
        response = self.generate_content(prompt, temperature=0.3)
        return response
    
    def analyze_chapter(
        self,
        chapter_content: str,
        previous_summary: Optional[str] = None,
        chapter_metadata: Optional[Dict] = None
    ) -> str:
        """
        分析章节并生成总结
        
        Args:
            chapter_content: 章节内容
            previous_summary: 前一章的总结（可选）
            chapter_metadata: 章节元数据（可选）
        
        Returns:
            Markdown 格式的章节总结
        """
        # 构建上下文
        context = ""
        if previous_summary:
            context += f"前一章总结：\n{previous_summary}\n\n"
        if chapter_metadata:
            context += f"章节信息：{chapter_metadata}\n\n"
        
        prompt = f"""{context}

请深度分析以下章节内容，生成详细的总结。

章节内容：
{chapter_content}

请生成 Markdown 格式的总结，包含：
1. Executive Summary（章节摘要）
2. Detailed Analysis（详细分析）
3. Key Takeaways（关键要点）
4. Connection to Previous Chapter（与前章联系）
5. Notable Quotes（重要引用）

请确保分析深入、准确，并与前章保持连贯。"""
        
        response = self.generate_content(prompt, temperature=0.7)
        return response
