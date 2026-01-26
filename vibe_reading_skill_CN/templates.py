#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Vibe Reading Skill - Templates
存放所有 HTML/CSS/JavaScript 模板
"""


def get_pdf_css() -> str:
    """返回 PDF 专业排版 CSS"""
    return """
@page {
    size: A4;
    margin: 25mm 20mm 25mm 20mm;
    
    @top-center {
        content: string(chapter-title);
        font-size: 9pt;
        color: #666;
        border-bottom: 0.5pt solid #ddd;
        padding-bottom: 3pt;
        font-weight: normal;
    }
    
    @bottom-center {
        content: counter(page);
        font-size: 10pt;
        color: #333;
        font-weight: 500;
        padding-top: 5pt;
    }
    
    @bottom-left {
        content: "Vibe Reading Skill";
        font-size: 8pt;
        color: #999;
    }
    
    @bottom-right {
        content: "第 " counter(page) " 页";
        font-size: 9pt;
        color: #666;
    }
}

/* 封面页 */
.cover-page {
    page: cover;
    display: flex;
    align-items: center;
    justify-content: center;
    height: 100vh;
    text-align: center;
}

.cover-content {
    max-width: 500pt;
}

.cover-title {
    font-size: 36pt;
    font-weight: bold;
    color: #0f172a;
    margin-bottom: 16pt;
    line-height: 1.3;
    letter-spacing: -0.5pt;
}

.cover-author {
    font-size: 18pt;
    color: #475569;
    margin-bottom: 30pt;
    font-weight: 500;
}

.cover-subtitle {
    font-size: 14pt;
    color: #64748b;
    margin-bottom: 20pt;
    font-weight: normal;
}

.cover-divider {
    width: 200pt;
    height: 1.5pt;
    background: linear-gradient(to right, transparent, #cbd5e1, transparent);
    margin: 35pt auto;
}

.cover-meta {
    font-size: 11pt;
    color: #64748b;
    margin-top: 50pt;
    line-height: 1.8;
}

.cover-meta-item {
    margin: 8pt 0;
    color: #475569;
}

.cover-brand {
    margin-top: 30pt;
    font-size: 10pt;
    color: #94a3b8;
    font-style: italic;
}

/* 目录页 */
.toc-page {
    page: toc;
}

.toc-title {
    font-size: 24pt;
    font-weight: bold;
    text-align: center;
    margin-bottom: 30pt;
    color: #0f172a;
}

/* 正文样式 */
.content {
    page: content;
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'PingFang SC', 'Hiragino Sans GB', 'Microsoft YaHei', serif;
    font-size: 11pt;
    line-height: 1.6;
    color: #0f172a;
}

/* 章节分割线 */
.chapter-divider {
    page-break-before: always;
    border-top: 3pt solid #2563eb;
    margin: 40pt 0 30pt 0;
    padding-top: 20pt;
}

/* 章节标题 */
h1 {
    font-size: 20pt;
    font-weight: bold;
    color: #0f172a;
    margin-top: 30pt;
    margin-bottom: 20pt;
    padding-bottom: 10pt;
    border-bottom: 2pt solid #e2e8f0;
    page-break-after: avoid;
    string-set: chapter-title content();
}

h2 {
    font-size: 14pt;
    font-weight: bold;
    color: #1e293b;
    margin-top: 18pt;
    margin-bottom: 10pt;
    page-break-after: avoid;
}

h3 {
    font-size: 12pt;
    font-weight: bold;
    color: #334155;
    margin-top: 14pt;
    margin-bottom: 8pt;
    page-break-after: avoid;
}

/* 段落 */
p {
    margin-top: 6pt;
    margin-bottom: 6pt;
    text-align: justify;
    text-indent: 2em; /* 中文首行缩进 */
}

/* 列表 */
ul, ol {
    margin-top: 8pt;
    margin-bottom: 8pt;
    padding-left: 20pt;
}

li {
    margin-top: 4pt;
    margin-bottom: 4pt;
}

/* 引用块 */
blockquote {
    margin: 12pt 0;
    padding: 12pt 16pt;
    border-left: 3pt solid #2563eb;
    background: #f8fafc;
    font-style: italic;
    color: #475569;
}

/* 代码块 */
pre {
    background: #1e293b;
    color: #e2e8f0;
    padding: 12pt;
    border-radius: 4pt;
    overflow-x: auto;
    font-family: 'Consolas', 'Monaco', monospace;
    font-size: 9pt;
    line-height: 1.4;
    margin: 12pt 0;
}

code {
    background: #f1f5f9;
    padding: 2pt 4pt;
    border-radius: 2pt;
    font-family: 'Consolas', 'Monaco', monospace;
    font-size: 10pt;
}

pre code {
    background: transparent;
    padding: 0;
}

/* 分隔线 */
hr {
    border: none;
    border-top: 1pt solid #e2e8f0;
    margin: 20pt 0;
}

/* 强调 */
strong {
    font-weight: bold;
    color: #0f172a;
}

em {
    font-style: italic;
}

/* 避免分页问题 */
h1, h2, h3, h4, h5, h6 {
    page-break-after: avoid;
}

blockquote, pre {
    page-break-inside: avoid;
}

/* 章节分隔 */
h1 {
    page-break-before: always;
}

h1:first-of-type {
    page-break-before: auto;
}
"""


def get_html_css() -> str:
    """返回专业 HTML CSS 样式"""
    return """
        /* CSS 变量定义 */
        :root {
            --primary-color: #2563eb;
            --primary-hover: #1d4ed8;
            --secondary-color: #64748b;
            --bg-primary: #ffffff;
            --bg-secondary: #f8fafc;
            --bg-tertiary: #f1f5f9;
            --text-primary: #0f172a;
            --text-secondary: #475569;
            --text-tertiary: #94a3b8;
            --border-color: #e2e8f0;
            --accent-color: #10b981;
            --shadow-sm: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
            --shadow-md: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
            --shadow-lg: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
            --radius-sm: 4px;
            --radius-md: 8px;
            --radius-lg: 12px;
        }
        
        /* 重置样式 */
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'PingFang SC', 'Hiragino Sans GB', 'Microsoft YaHei', Roboto, sans-serif;
            line-height: 1.7;
            color: var(--text-primary);
            background: var(--bg-secondary);
            font-size: 16px;
        }
        
        /* 容器布局 */
        .container {
            max-width: 1400px;
            margin: 0 auto;
            padding: 24px;
            display: grid;
            grid-template-columns: 280px 1fr;
            gap: 24px;
        }
        
        /* 侧边栏 */
        .sidebar {
            background: var(--bg-primary);
            padding: 24px;
            border-radius: var(--radius-lg);
            box-shadow: var(--shadow-md);
            height: fit-content;
            position: sticky;
            top: 24px;
        }
        
        .sidebar-header {
            margin-bottom: 20px;
            padding-bottom: 16px;
            border-bottom: 2px solid var(--border-color);
        }
        
        .sidebar h2 {
            font-size: 20px;
            font-weight: 600;
            color: var(--text-primary);
            margin-bottom: 8px;
        }
        
        .progress-indicator {
            font-size: 12px;
            color: var(--text-tertiary);
        }
        
        .chapter-list {
            list-style: none;
            max-height: calc(100vh - 200px);
            overflow-y: auto;
        }
        
        .chapter-list::-webkit-scrollbar {
            width: 6px;
        }
        
        .chapter-list::-webkit-scrollbar-track {
            background: var(--bg-tertiary);
            border-radius: 3px;
        }
        
        .chapter-list::-webkit-scrollbar-thumb {
            background: var(--border-color);
            border-radius: 3px;
        }
        
        .chapter-list li {
            margin-bottom: 4px;
        }
        
        .chapter-list a {
            color: var(--text-secondary);
            text-decoration: none;
            display: block;
            padding: 10px 12px;
            border-radius: var(--radius-sm);
            transition: all 0.2s ease;
            font-size: 14px;
            border-left: 3px solid transparent;
        }
        
        .chapter-list a:hover {
            background: var(--bg-tertiary);
            color: var(--primary-color);
            border-left-color: var(--primary-color);
        }
        
        .chapter-list a.active {
            background: var(--primary-color);
            color: white;
            font-weight: 500;
            border-left-color: var(--primary-hover);
        }
        
        /* 主内容区 */
        .main-content {
            background: var(--bg-primary);
            padding: 40px;
            border-radius: var(--radius-lg);
            box-shadow: var(--shadow-md);
            min-height: 600px;
        }
        
        .article-content {
            max-width: 800px;
            margin: 0 auto;
        }
        
        /* 欢迎界面 */
        .welcome-screen {
            text-align: center;
            padding: 60px 20px;
        }
        
        .welcome-screen h1 {
            font-size: 32px;
            font-weight: 700;
            color: var(--text-primary);
            margin-bottom: 16px;
        }
        
        .welcome-screen > p {
            font-size: 18px;
            color: var(--text-secondary);
            margin-bottom: 40px;
        }
        
        .welcome-features {
            display: flex;
            justify-content: center;
            gap: 40px;
            margin-top: 40px;
        }
        
        .feature-item {
            display: flex;
            flex-direction: column;
            align-items: center;
            gap: 8px;
        }
        
        .feature-icon {
            font-size: 32px;
        }
        
        /* Markdown 内容样式 */
        .article-content h1 {
            font-size: 28px;
            font-weight: 700;
            color: var(--text-primary);
            margin-top: 32px;
            margin-bottom: 16px;
            line-height: 1.3;
        }
        
        .article-content h2 {
            font-size: 22px;
            font-weight: 600;
            color: var(--text-primary);
            margin-top: 32px;
            margin-bottom: 12px;
            line-height: 1.4;
        }
        
        .article-content h3 {
            font-size: 18px;
            font-weight: 600;
            color: var(--text-secondary);
            margin-top: 24px;
            margin-bottom: 10px;
        }
        
        .article-content p {
            margin-top: 12px;
            margin-bottom: 12px;
            line-height: 1.8;
            color: var(--text-primary);
        }
        
        .article-content ul, .article-content ol {
            margin-top: 12px;
            margin-bottom: 12px;
            padding-left: 24px;
        }
        
        .article-content li {
            margin-top: 6px;
            margin-bottom: 6px;
            line-height: 1.7;
        }
        
        .article-content blockquote {
            margin: 20px 0;
            padding: 16px 20px;
            border-left: 4px solid var(--primary-color);
            background: var(--bg-tertiary);
            border-radius: var(--radius-sm);
            font-style: italic;
            color: var(--text-secondary);
        }
        
        .article-content code {
            background: var(--bg-tertiary);
            padding: 2px 6px;
            border-radius: var(--radius-sm);
            font-family: 'SF Mono', 'Monaco', 'Consolas', monospace;
            font-size: 14px;
            color: var(--primary-color);
        }
        
        .article-content pre {
            background: #1e293b;
            color: #e2e8f0;
            padding: 16px;
            border-radius: var(--radius-md);
            overflow-x: auto;
            margin: 16px 0;
        }
        
        .article-content pre code {
            background: transparent;
            padding: 0;
            color: inherit;
        }
        
        .article-content hr {
            border: none;
            border-top: 2px solid var(--border-color);
            margin: 32px 0;
        }
        
        .article-content strong {
            font-weight: 600;
            color: var(--text-primary);
        }
        
        .article-content em {
            font-style: italic;
        }
        
        /* 问答区 */
        .qa-section {
            margin-top: 60px;
            padding-top: 40px;
            border-top: 2px solid var(--border-color);
        }
        
        .qa-header {
            margin-bottom: 24px;
        }
        
        .qa-header h3 {
            font-size: 20px;
            font-weight: 600;
            color: var(--text-primary);
            margin-bottom: 8px;
        }
        
        .qa-hint {
            font-size: 14px;
            color: var(--text-tertiary);
        }
        
        .qa-input-group {
            display: flex;
            gap: 12px;
            margin-bottom: 20px;
        }
        
        .question-input {
            flex: 1;
            padding: 14px 16px;
            border: 2px solid var(--border-color);
            border-radius: var(--radius-md);
            font-size: 15px;
            font-family: inherit;
            transition: all 0.2s ease;
            background: var(--bg-primary);
        }
        
        .question-input:focus {
            outline: none;
            border-color: var(--primary-color);
            box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.1);
        }
        
        .submit-btn {
            background: var(--primary-color);
            color: white;
            border: none;
            padding: 14px 28px;
            border-radius: var(--radius-md);
            cursor: pointer;
            font-size: 15px;
            font-weight: 500;
            display: flex;
            align-items: center;
            gap: 8px;
            transition: all 0.2s ease;
        }
        
        .submit-btn:hover {
            background: var(--primary-hover);
            transform: translateY(-1px);
            box-shadow: var(--shadow-md);
        }
        
        .submit-btn:active {
            transform: translateY(0);
        }
        
        .btn-icon {
            font-size: 18px;
        }
        
        .answer-container {
            max-height: 500px;
            overflow-y: auto;
            padding: 16px;
            background: var(--bg-secondary);
            border-radius: var(--radius-md);
            border: 1px solid var(--border-color);
            margin-top: 24px;
            min-height: 60px;
        }
        
        .answer {
            padding: 20px;
            background: var(--bg-tertiary);
            border-radius: var(--radius-md);
            border-left: 4px solid var(--primary-color);
            animation: fadeIn 0.3s ease;
            margin-bottom: 16px;
        }
        
        .answer:last-child {
            margin-bottom: 0;
        }
        
        @keyframes fadeIn {
            from {
                opacity: 0;
                transform: translateY(-10px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }
        
        .answer p {
            margin: 0;
            line-height: 1.7;
        }
        
        .answer.loading {
            text-align: center;
            color: var(--text-tertiary);
        }
        
        .answer.error {
            border-left-color: #d32f2f;
            background: #ffebee;
        }
        
        .answer.error p {
            color: #d32f2f;
        }
        
        /* 返回顶部按钮 */
        .back-to-top {
            position: fixed;
            bottom: 32px;
            right: 32px;
            width: 48px;
            height: 48px;
            background: var(--primary-color);
            color: white;
            border: none;
            border-radius: 50%;
            cursor: pointer;
            font-size: 20px;
            box-shadow: var(--shadow-lg);
            transition: all 0.3s ease;
            z-index: 1000;
        }
        
        .back-to-top:hover {
            background: var(--primary-hover);
            transform: translateY(-4px);
            box-shadow: var(--shadow-lg);
        }
        
        /* 响应式设计 */
        @media (max-width: 1024px) {
            .container {
                grid-template-columns: 220px 1fr;
                gap: 20px;
                padding: 20px;
            }
            
            .main-content {
                padding: 32px;
            }
        }
        
        @media (max-width: 768px) {
            .container {
                grid-template-columns: 1fr;
                gap: 16px;
                padding: 16px;
            }
            
            .sidebar {
                position: static;
                max-height: 300px;
                overflow-y: auto;
            }
            
            .main-content {
                padding: 24px;
            }
            
            .welcome-features {
                flex-direction: column;
                gap: 24px;
            }
            
            .qa-input-group {
                flex-direction: column;
            }
            
            .submit-btn {
                width: 100%;
                justify-content: center;
            }
            
            .back-to-top {
                bottom: 20px;
                right: 20px;
                width: 44px;
                height: 44px;
            }
        }
        """


def get_pdf_html_template(html_body: str, book_title: str, book_author: str, model_name: str, gen_date: str) -> str:
    """生成包含封面和样式的 PDF HTML"""
    return f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>{book_title}</title>
</head>
<body>
    <!-- 封面页 -->
    <div class="cover-page">
        <div class="cover-content">
            <h1 class="cover-title">{book_title}</h1>
            <div class="cover-author">作者：{book_author}</div>
            <div class="cover-divider"></div>
            <div class="cover-subtitle">AI 智能阅读分析总结</div>
            <div class="cover-meta">
                <p class="cover-meta-item">使用模型：{model_name}</p>
                <p class="cover-meta-item">总结日期：{gen_date}</p>
                <p class="cover-brand">使用 Vibe Reading Skill 生成</p>
            </div>
        </div>
    </div>
    
    <!-- 目录页 -->
    <div class="toc-page">
        <h1 class="toc-title">目录</h1>
        <div class="toc-content">
            <!-- 目录将通过 CSS 自动生成 -->
        </div>
    </div>
    
    <!-- 正文内容 -->
    <div class="content">
        {html_body}
    </div>
</body>
</html>"""


def get_html_interface_template(html_css: str, html_javascript: str, summary_count: int) -> str:
    """生成 HTML 交互界面模板"""
    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Vibe Reading - Interactive Reader</title>
    <script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
    <style>
        {html_css}
    </style>
</head>
<body>
    <div class="container">
        <aside class="sidebar">
            <div class="sidebar-header">
                <h2>📚 章节列表</h2>
                <div class="progress-indicator" id="progressIndicator">
                    <span>0 / {summary_count}</span>
                </div>
            </div>
            <nav>
                <ul class="chapter-list" id="chapterList">
                    <!-- 章节列表将通过 JavaScript 动态生成 -->
                </ul>
            </nav>
        </aside>
        
        <main class="main-content">
            <article id="chapterContent" class="article-content">
                <div class="welcome-screen">
                    <h1>欢迎使用 Vibe Reading</h1>
                    <p>请从左侧选择章节开始阅读。</p>
                    <div class="welcome-features">
                        <div class="feature-item">
                            <span class="feature-icon">📖</span>
                            <span>逐章深度分析</span>
                        </div>
                        <div class="feature-item">
                            <span class="feature-icon">💬</span>
                            <span>智能问答讨论</span>
                        </div>
                        <div class="feature-item">
                            <span class="feature-icon">🔗</span>
                            <span>上下文连贯理解</span>
                        </div>
                    </div>
                </div>
            </article>
            
            <section class="qa-section">
                <div class="qa-header">
                    <h3>💬 问答讨论</h3>
                    <p class="qa-hint">输入关于本章的问题，AI 会基于上下文回答</p>
                </div>
                <div class="qa-input-group">
                    <input 
                        type="text" 
                        class="question-input" 
                        id="questionInput" 
                        placeholder="例如：这一章的核心观点是什么？"
                        onkeypress="if(event.key==='Enter') askQuestion()"
                    >
                    <button class="submit-btn" onclick="askQuestion()">
                        <span class="btn-text">提问</span>
                        <span class="btn-icon">→</span>
                    </button>
                </div>
                <div id="answer" class="answer-container"></div>
            </section>
        </main>
    </div>
    
    <button class="back-to-top" id="backToTop" onclick="scrollToTop()" style="display: none;">
        ↑
    </button>
    
    <script>
        {html_javascript}
    </script>
</body>
</html>"""


def get_html_javascript_template(summaries_data: dict, chapter_originals: dict, chapter_titles: dict, 
                                  api_key: str, model_name: str) -> str:
    """生成 HTML JavaScript 代码"""
    import json
    return f"""
        const summaries = {json.dumps(summaries_data, ensure_ascii=False)};
        const chapterOriginals = {json.dumps(chapter_originals, ensure_ascii=False)};
        const chapterTitles = {json.dumps(chapter_titles, ensure_ascii=False)};
        const geminiApiKey = {json.dumps(api_key, ensure_ascii=False)};
        const geminiModel = {json.dumps(model_name, ensure_ascii=False)};
        let currentChapterIndex = 0;
        let currentChapterKey = null;
        
        // Markdown 渲染函数（使用 marked.js 库）
        // 如果没有 marked.js，使用简单实现
        function renderMarkdown(markdown) {{
            if (typeof marked !== 'undefined') {{
                return marked.parse(markdown);
            }}
            
            // 简单实现作为后备
            let html = markdown;
            
            // 代码块（先处理，避免被其他规则影响）
            html = html.replace(/```([\\s\\S]*?)```/g, '<pre><code>$1</code></pre>');
            html = html.replace(/`([^`]+)`/g, '<code>$1</code>');
            
            // 标题
            html = html.replace(/^#### (.*$)/gim, '<h4>$1</h4>');
            html = html.replace(/^### (.*$)/gim, '<h3>$1</h3>');
            html = html.replace(/^## (.*$)/gim, '<h2>$1</h2>');
            html = html.replace(/^# (.*$)/gim, '<h1>$1</h1>');
            
            // 粗体和斜体
            html = html.replace(/\\*\\*([^\\*]+)\\*\\*/g, '<strong>$1</strong>');
            html = html.replace(/\\*([^\\*]+)\\*/g, '<em>$1</em>');
            
            // 引用
            html = html.replace(/^> (.*$)/gim, '<blockquote>$1</blockquote>');
            
            // 链接
            html = html.replace(/\\[([^\\]]+)\\]\\(([^\\)]+)\\)/g, '<a href="$2">$1</a>');
            
            // 段落（将双换行转换为段落）
            const lines = html.split('\\n');
            let result = [];
            let currentPara = [];
            
            for (let i = 0; i < lines.length; i++) {{
                const line = lines[i].trim();
                if (!line) {{
                    if (currentPara.length > 0) {{
                        result.push('<p>' + currentPara.join(' ') + '</p>');
                        currentPara = [];
                    }}
                }} else if (line.match(/^<[h|b|p|u|o|l|d|pre]/)) {{
                    if (currentPara.length > 0) {{
                        result.push('<p>' + currentPara.join(' ') + '</p>');
                        currentPara = [];
                    }}
                    result.push(line);
                }} else {{
                    currentPara.push(line);
                }}
            }}
            if (currentPara.length > 0) {{
                result.push('<p>' + currentPara.join(' ') + '</p>');
            }}
            
            return result.join('\\n');
        }}
        
        // 生成章节列表
        const chapterList = document.getElementById('chapterList');
        Object.keys(summaries).forEach((key, index) => {{
            const li = document.createElement('li');
            const a = document.createElement('a');
            a.href = '#';
            a.textContent = chapterTitles[key] || `第 ${{index + 1}} 章`;
            a.onclick = (e) => {{
                e.preventDefault();
                loadChapter(key, index);
            }};
            li.appendChild(a);
            chapterList.appendChild(li);
        }});
        
        function loadChapter(key, index) {{
            // 渲染 Markdown 内容
            const markdown = summaries[key];
            const html = renderMarkdown(markdown);
            const contentDiv = document.getElementById('chapterContent');
            contentDiv.innerHTML = html;
            
            // 更新当前章节
            currentChapterIndex = index;
            currentChapterKey = key;
            
            // 更新活动状态
            document.querySelectorAll('.chapter-list a').forEach((a, i) => {{
                if (i === index) {{
                    a.classList.add('active');
                }} else {{
                    a.classList.remove('active');
                }}
            }});
            
            // 更新进度
            updateProgress(index + 1, Object.keys(summaries).length);
            
            // 清空问答区域
            document.getElementById('answer').innerHTML = '';
            document.getElementById('questionInput').value = '';
            
            // 滚动到顶部
            window.scrollTo({{ top: 0, behavior: 'smooth' }});
        }}
        
        function updateProgress(current, total) {{
            const indicator = document.getElementById('progressIndicator');
            indicator.textContent = `${{current}} / ${{total}}`;
        }}
        
        async function askQuestion() {{
            const question = document.getElementById('questionInput').value.trim();
            if (!question) {{
                alert('请输入问题');
                return;
            }}
            
            if (!currentChapterKey) {{
                alert('请先选择一个章节');
                return;
            }}
            
            const answerDiv = document.getElementById('answer');
            
            // 添加加载提示（追加到现有内容后面）
            const loadingDiv = document.createElement('div');
            loadingDiv.className = 'answer loading';
            loadingDiv.innerHTML = '<p>正在思考...</p>';
            answerDiv.appendChild(loadingDiv);
            
            // 滚动到底部
            answerDiv.scrollTop = answerDiv.scrollHeight;
            
            try {{
                // 构建上下文：当前章节原文、当前章节总结、前一章、后一章的总结
                const chapterKeys = Object.keys(summaries);
                const currentIndex = chapterKeys.indexOf(currentChapterKey);
                
                let context = '';
                
                // 添加当前章节原文（最重要）
                if (chapterOriginals[currentChapterKey]) {{
                    context += `当前章节原文：\\n${{chapterOriginals[currentChapterKey]}}\\n\\n`;
                }}
                
                // 添加当前章节总结
                context += `当前章节总结：\\n${{summaries[currentChapterKey]}}\\n\\n`;
                
                // 添加前一章总结（用于上下文连贯）
                if (currentIndex > 0) {{
                    const prevKey = chapterKeys[currentIndex - 1];
                    context += `前一章总结（用于上下文）：\\n${{summaries[prevKey]}}\\n\\n`;
                }}
                
                // 添加后一章总结（用于上下文连贯）
                if (currentIndex < chapterKeys.length - 1) {{
                    const nextKey = chapterKeys[currentIndex + 1];
                    context += `下一章总结（用于上下文）：\\n${{summaries[nextKey]}}\\n\\n`;
                }}
                
                // 构建提示词
                const prompt = `${{context}}用户问题：${{question}}\\n\\n请基于以上章节原文和总结回答用户的问题。回答要准确、详细，可以引用原文内容。直接回答问题，不要重复问题本身。使用中文回答。`;
                
                // 调用 Gemini API
                const response = await fetch(`https://generativelanguage.googleapis.com/v1beta/models/${{geminiModel}}:generateContent?key=${{geminiApiKey}}`, {{
                    method: 'POST',
                    headers: {{
                        'Content-Type': 'application/json',
                    }},
                    body: JSON.stringify({{
                        contents: [{{
                            parts: [{{
                                text: prompt
                            }}]
                        }}]
                    }})
                }});
                
                if (!response.ok) {{
                    throw new Error(`API 请求失败: ${{response.status}} ${{response.statusText}}`);
                }}
                
                const data = await response.json();
                
                if (data.error) {{
                    throw new Error(data.error.message || 'API 返回错误');
                }}
                
                const answer = data.candidates[0].content.parts[0].text;
                
                // 移除加载提示
                loadingDiv.remove();
                
                // 渲染回答（支持 Markdown）
                const answerHtml = renderMarkdown(answer);
                
                // 追加新的问答（不覆盖之前的）
                const newQADiv = document.createElement('div');
                newQADiv.className = 'answer';
                newQADiv.innerHTML = `
                    <div style="border-bottom: 1px solid #e2e8f0; padding-bottom: 12px; margin-bottom: 12px;">
                        <p style="margin: 0; color: #64748b; font-size: 14px;"><strong>问题：</strong>${{question}}</p>
                    </div>
                    <div style="margin-top: 12px;">
                        <p style="margin: 0 0 8px 0; color: #64748b; font-size: 14px;"><strong>回答：</strong></p>
                        <div style="margin-top: 8px;">${{answerHtml}}</div>
                    </div>
                `;
                answerDiv.appendChild(newQADiv);
                
                // 滚动到底部
                answerDiv.scrollTop = answerDiv.scrollHeight;
                
            }} catch (error) {{
                console.error('问答错误:', error);
                
                // 移除加载提示
                loadingDiv.remove();
                
                // 追加错误信息
                const errorDiv = document.createElement('div');
                errorDiv.className = 'answer error';
                errorDiv.innerHTML = `
                    <div style="border-bottom: 1px solid #e2e8f0; padding-bottom: 12px; margin-bottom: 12px;">
                        <p style="margin: 0; color: #64748b; font-size: 14px;"><strong>问题：</strong>${{question}}</p>
                    </div>
                    <p style="margin-top: 12px; color: #d32f2f;"><strong>错误：</strong>${{error.message}}</p>
                    <p style="margin-top: 8px; color: #666;">请检查 API Key 是否正确配置，或查看浏览器控制台获取更多信息。</p>
                `;
                answerDiv.appendChild(errorDiv);
                
                // 滚动到底部
                answerDiv.scrollTop = answerDiv.scrollHeight;
            }}
            
            // 清空输入框（但保留问答历史）
            document.getElementById('questionInput').value = '';
        }}
        
        function scrollToTop() {{
            window.scrollTo({{ top: 0, behavior: 'smooth' }});
        }}
        
        // 显示/隐藏返回顶部按钮
        window.addEventListener('scroll', () => {{
            const backToTop = document.getElementById('backToTop');
            if (window.scrollY > 300) {{
                backToTop.style.display = 'block';
            }} else {{
                backToTop.style.display = 'none';
            }}
        }});
        
        // 初始化：加载第一章
        if (Object.keys(summaries).length > 0) {{
            const firstKey = Object.keys(summaries)[0];
            loadChapter(firstKey, 0);
        }}
        """
