# Vibe Reading Skill

一个智能阅读分析 Agent Skill，帮助用户快速理解大部头著作的核心内容。通过 AI 的深度阅读和结构化分析，将整本书转化为易于消化的总结报告。

## 特性

- 📚 **智能章节识别**：AI 自动识别书籍结构，无需手动配置
- 🔄 **上下文连贯**：每章分析时参考前章总结，保持理解连贯
- 📄 **多格式输出**：Markdown、PDF、HTML 交互界面
- 🌍 **多语言支持**：自动识别和适配不同语言的书籍
- 🤖 **AI 驱动**：完全由 AI 决策，适应任何格式的书籍

## 快速开始

### 前置要求

- Python 3.8+
- Google Gemini API Key

### 安装

#### 方式一：作为 Python Package 安装（推荐）

```bash
# 从 GitHub 安装
pip install git+https://github.com/yourusername/vibe-reading-skill.git

# 或从本地安装（开发模式）
git clone https://github.com/yourusername/vibe-reading-skill.git
cd vibe-reading-skill
pip install -e .
```

### 配置

创建 `.env` 文件：

```bash
GEMINI_API_KEY=your_api_key_here

# 可选：指定使用的模型（默认: gemini-2.5-pro）
# 推荐模型：
#   gemini-2.5-pro      - Gemini 2.5 旗舰模型（稳定可靠）⭐ 默认推荐
#   gemini-3-pro        - Gemini 3 旗舰模型（最新，最强性能）
#   gemini-3            - Gemini 3 标准模型
#   gemini-2.5-flash    - Gemini 2.5 快速模型（速度快，成本低）
#   gemini-1.5-pro      - 稳定版本（经过验证）
GEMINI_MODEL=gemini-2.5-pro
```

**模型选择**：默认使用 `gemini-2.5-pro`，也可选择 `gemini-2.5-flash`（快速）或 `gemini-1.5-pro`（稳定）

### 使用

```python
from vibe_reading_skill_CN import process_book

result = process_book("your_book.epub")
print(result["status"])  # 'success' 或 'error'
```

## 工作流程

1. **文档预处理**：EPUB → TXT 转换（如需要）
2. **智能章节识别**：AI 自动识别章节结构
3. **进一步拆分**：AI 评估章节长度，必要时拆分
4. **逐章分析**：AI 深度阅读每章，生成总结
5. **格式输出**：生成 Markdown、PDF、HTML

## 输出目录

处理完成后会在当前目录创建以下输出目录：

- `chapters/` - 拆分好的章节原文
- `summaries/` - 章节总结（Markdown）
- `pdf/` - PDF 输出
- `html/` - HTML 交互界面

## 设计理念

本 Skill 采用 **AI 驱动，而非代码驱动** 的设计理念：

- ✅ **AI 负责所有决策**：章节识别、拆分策略、分析重点等都由 AI 根据具体情况判断
- ✅ **代码只做执行**：代码只负责执行 AI 的决策（文件读写、格式转换等）
- ❌ **避免硬编码规则**：不预设"如果遇到 X 就做 Y"的规则

这使得 Skill 可以处理任何格式、任何语言的书籍，无需为每种新格式编写代码。

## 贡献

欢迎贡献！请提交 Issue 或 Pull Request。

## 许可证

Apache 2.0 License - 详见 [LICENSE](LICENSE)

## 作为 Skill 使用

本项目已配置为标准的 Python Skill，可以：

- ✅ 通过 `pip install` 安装
- ✅ 在 IDE 中直接调用
- ✅ 注册到 Skill 市场

### Skill 调用示例

```python
from vibe_reading_skill_CN import process_book

# 基本调用
result = process_book("book.epub")

# 查看结果
if result["status"] == "success":
    print(f"处理完成！章节数: {result['metadata']['chapter_count']}")
    print(f"PDF: {result['output_paths']['pdf']}")
    print(f"HTML: {result['output_paths']['html']}")
else:
    print(f"错误: {result['message']}")
```

### 返回值格式

```python
{
    "status": "success",  # 或 "error"
    "message": "书籍处理完成",
    "output_paths": {
        "chapters": "chapters/",
        "summaries": "summaries/",
        "pdf": "pdf/book_summary.pdf",
        "html": "html/interactive_reader.html"
    },
    "metadata": {
        "book_title": "书籍标题",
        "chapter_count": 10,
        "processing_time": 123.45
    }
}
```

## 相关链接

- [Skill 指令](SKILL.md) - AI 处理指令
