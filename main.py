
import os
os.environ["NLTK_DATA"] = "./nltk_data"

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict, Any
import logging


from models import DownloadRequest, OptimizeDocumentRequest, OptimizeDocumentResponse, SelectiveAnalyzeRequest, BatchOptimizeRequest, BatchOptimizeResponse, DocumentDiff
from github_service import GitHubService

from readability import get_readability
from code_checker import check_document_quality

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 创建FastAPI应用
app = FastAPI(
    title="GitHub 文档质量分析系统 API",
    description="用于分析和优化GitHub仓库文档的API服务",
    version="2.1.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境应该限制来源
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 初始化GitHub服务
github_service = GitHubService()


@app.post("/api/scan-repo")
async def scan_repo_docs(request: DownloadRequest):
    """
    扫描仓库所有文档（12种类型）
    
    扫描GitHub仓库的所有主要文档，包括：
    - 核心文档：README, CONTRIBUTING, CODE_OF_CONDUCT, CHANGELOG, LICENSE
    - 扩展文档：SECURITY, SUPPORT, WIKI, DOCS, INSTALLATION, USAGE, API
    
    Args:
        repo_url: GitHub仓库URL，支持多种格式：
            - https://github.com/username/reponame
            - github.com/username/reponame  
            - username/reponame
    
    Returns:
        包含所有找到的文档内容和元数据
    """
    logger.info(f"收到文档扫描请求: {request.repo_url}")
    
    try:
        owner, repo = github_service.extract_repo_info(request.repo_url)
        if not owner or not repo:
            raise HTTPException(status_code=400, detail="无效的GitHub仓库URL")

        # 获取仓库基本信息（包括stars、forks等）
        repo_info = github_service.get_repo_info(owner, repo)
        if not repo_info:
            logger.warning("无法获取仓库信息，使用默认值")
            repo_info = {}

        # 获取所有文档（12种类型）
        docs = github_service.get_all_repo_docs(owner, repo)
        
        # 统计找到的文档
        found_count = sum(1 for v in docs.values() if v is not None)
        logger.info(f"扫描完成，找到 {found_count}/12 个文档")

        # 构造返回的仓库信息
        response_repo_info = {
            "owner": owner,
            "repo": repo,
            "full_name": f"{owner}/{repo}",
            "stargazers_count": repo_info.get("stargazers_count", 0),
            "forks_count": repo_info.get("forks_count", 0),
            "description": repo_info.get("description", ""),
            "language": repo_info.get("language", ""),
            "created_at": repo_info.get("created_at", ""),
            "updated_at": repo_info.get("updated_at", "")
        }

        return {
            "success": True,
            "repo_info": response_repo_info,
            "docs": docs,
            "stats": {
                "total_types": 12,
                "found_count": found_count,
                "found_percentage": round(found_count / 12 * 100, 1)
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"扫描失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/analyze-project")
async def analyze_project(request: SelectiveAnalyzeRequest):
    """
    分析选定的项目文档（支持选择性分析）
    
    对用户选择的文档进行深度质量分析，包括：
    - 规则检查：每个文档单独检查（链接、代码块、标题结构、章节完整性、语法）
    - AI分析：所有选中文档的综合语义分析和评分
    
    Args:
        docs: 从 scan-repo 获取的文档字典
        selected_doc_types: 选择要分析的文档类型列表，如 ["readme", "contributing"]
    
    Returns:
        包含规则检查结果和AI分析结果
    """
    logger.info(f"收到项目分析请求，选择的文档: {request.selected_doc_types}")
    
    try:
        docs = request.docs
        selected_types = request.selected_doc_types
        
        if not docs:
            raise HTTPException(status_code=400, detail="未提供文档内容")
        
        if not selected_types:
            raise HTTPException(status_code=400, detail="未选择要分析的文档")
            
        # 1. 规则检查（只检查选中的文档）
        # rule_check_results = {}
        combined_markdown = ""
        
        for doc_type in selected_types:
            doc_info = docs.get(doc_type)
            if doc_info and 'content' in doc_info:
                content = doc_info['content']
                # 累加用于AI分析的文本
                combined_markdown += f"\n\n# FILE: {doc_info['filename']} ({doc_type.upper()})\n\n{content}"
                
                # 单个文档规则检查
                # check_result = check_document_quality(content, doc_type)
                # rule_check_results[doc_type] = check_result
            else:
                logger.warning(f"文档类型 {doc_type} 不存在或无内容")
        
        if not combined_markdown:
            raise HTTPException(status_code=400, detail="选择的文档都没有内容")

        # 2. 计算可读性指标
        logger.info("开始计算可读性指标...")
        readability_data = get_readability(combined_markdown)
        logger.info("可读性指标计算完成")

        # 3. AI 分析
        from ask import analyze_readme_with_llm
        from fastapi.concurrency import run_in_threadpool

        # 简化规则检查结果给LLM
        # simple_rule_checks = {}
        # for dtype, res in rule_check_results.items():
        #     simple_rule_checks[dtype] = {
        #         "issues_count": res['summary']['total_issues'],
        #         "missing_sections": res['section_completeness_check'].get('missing_sections', [])
        #     }
            
        api_key = 'sk-99ed7f2e56bd478cb3147fd1593d4157'
        
        logger.info("开始调用 LLM 进行分析...")
        ai_result = await run_in_threadpool(analyze_readme_with_llm, combined_markdown, readability_data, api_key)
        logger.info("LLM 分析完成")
        
        # 只返回选中文档的内容（不返回未选中的文档内容）
        selected_docs = {}
        for doc_type in selected_types:
            if doc_type in docs and docs[doc_type]:
                selected_docs[doc_type] = docs[doc_type]
        
        # 添加调试信息
        debug_info = {
            "analyzed_doc_count": len(selected_types),
            "analyzed_doc_types": selected_types,
            "total_content_length": len(combined_markdown),
            "individual_doc_lengths": {
                doc_type: len(docs[doc_type]['content']) if doc_type in docs and docs[doc_type] else 0
                for doc_type in selected_types
            }
        }
        return {
            "success": True,
            "selected_doc_types": selected_types,
            "selected_docs": selected_docs,  # 只包含选中的文档内容
            # "rule_checks": rule_check_results,
            "readability": readability_data,
            "ai_analysis": ai_result,
            "debug_info": debug_info  # 调试信息，帮助排查问题
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"分析失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/optimize-document", response_model=OptimizeDocumentResponse)
async def optimize_document(request: OptimizeDocumentRequest):
    """
    基于AI分析结果优化单个文档
    
    根据AI分析结果中的建议，自动优化文档内容，包括：
    - 修复格式和语法问题
    - 补充缺失的章节
    - 改善表达清晰度
    - 优化代码示例
    
    Args:
        original_content: 原始文档内容（Markdown格式）
        analysis_result: AI分析结果（从 /api/analyze-project 获取）
        doc_type: 文档类型（readme, contributing等）
    
    Returns:
        优化后的文档内容和变化摘要
    """
    logger.info(f"收到文档优化请求，文档类型: {request.doc_type}")
    
    try:
        from ask import optimize_document_with_llm
        from fastapi.concurrency import run_in_threadpool
        
        api_key = 'sk-99ed7f2e56bd478cb3147fd1593d4157'
        
        # 调用优化函数
        logger.info("开始调用 LLM 进行文档优化...")
        optimized_content = await run_in_threadpool(
            optimize_document_with_llm,
            request.original_content,
            request.analysis_result,
            api_key,
            request.doc_type
        )
        logger.info("文档优化完成")
        
        # 生成变化摘要
        changes_summary = {
            "original_length": len(request.original_content),
            "optimized_length": len(optimized_content),
            "length_change": len(optimized_content) - len(request.original_content),
            "original_lines": request.original_content.count('\n') + 1,
            "optimized_lines": optimized_content.count('\n') + 1,
        }
        
        # 生成差异对比HTML（行内高亮）
        diff_html = _generate_inline_diff_html(request.original_content, optimized_content)
        
        return OptimizeDocumentResponse(
            success=True,
            original_content=request.original_content,
            optimized_content=optimized_content,
            changes_summary=changes_summary,
            diff_html=diff_html
        )
        
    except Exception as e:
        logger.error(f"文档优化失败: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"文档优化失败: {str(e)}"
        )




@app.post("/api/batch-optimize", response_model=BatchOptimizeResponse)
async def batch_optimize_documents(request: BatchOptimizeRequest):
    """
    批量优化多个文档并生成差异对比
    
    一次性优化多个文档，并生成HTML格式的差异对比，包括：
    - 绿色高亮：新增内容
    - 红色高亮：删除内容
    - 黄色高亮：修改内容
    - 精确统计：添加/删除/修改的行数
    
    Args:
        documents: 文档列表，每个包含 doc_type, original_content, analysis_result

    Returns:
        每个文档的优化结果和HTML差异对比
    """
    logger.info(f"收到批量优化请求，文档数量: {len(request.documents)}")

    try:
        from ask import optimize_document_with_llm
        from fastapi.concurrency import run_in_threadpool
        import difflib
        
        api_key = 'sk-99ed7f2e56bd478cb3147fd1593d4157'

        results = []
        diffs = []
        
        for doc in request.documents:
            doc_type = doc.get('doc_type', 'readme')
            original_content = doc.get('original_content', '')
            analysis_result = doc.get('analysis_result', {})
            
            logger.info(f"正在优化 {doc_type}...")
            
            try:
                # 优化文档
                optimized_content = await run_in_threadpool(
                    optimize_document_with_llm,
                    original_content,
                    analysis_result,
                    api_key,
                    doc_type
                )
                
                # 生成差异对比 HTML
                diff_html, stats = _generate_diff_html(original_content, optimized_content)
                
                results.append({
                    "doc_type": doc_type,
                    "success": True,
                    "original_content": original_content,
                    "optimized_content": optimized_content,
                    "changes_summary": {
                        "original_length": len(original_content),
                        "optimized_length": len(optimized_content),
                        "length_change": len(optimized_content) - len(original_content),
                        "additions": stats['additions'],
                        "deletions": stats['deletions'],
                        "modifications": stats['modifications']
                    }
                })
                
                diffs.append(DocumentDiff(
                    doc_type=doc_type,
                    original_content=original_content,
                    optimized_content=optimized_content,
                    diff_html=diff_html,
                    additions=stats['additions'],
                    deletions=stats['deletions'],
                    modifications=stats['modifications']
                ))
                
                logger.info(f"{doc_type} 优化完成")
                
            except Exception as e:
                logger.error(f"{doc_type} 优化失败: {e}")
                results.append({
                    "doc_type": doc_type,
                    "success": False,
                    "error": str(e)
                })
        
        return BatchOptimizeResponse(
            success=True,
            results=results,
            diffs=diffs
        )
        
    except Exception as e:
        logger.error(f"批量优化失败: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"批量优化失败: {str(e)}"
        )


def _generate_inline_diff_html(original: str, optimized: str) -> str:
    """
    生成行内差异高亮HTML（类似 Cursor 编辑器风格）
    删除的内容用红色背景和删除线，添加的内容用绿色背景
    
    Returns:
        HTML字符串，包含完整的样式和差异高亮
    """
    import difflib
    import html
    
    # 转义HTML特殊字符
    def escape_html(text: str) -> str:
        return html.escape(text)
    
    # 将文本分割成单词和空格（保留空白字符）
    def tokenize(text: str):
        import re
        # 匹配非空白字符序列或空白字符序列
        tokens = re.findall(r'\S+|\s+', text)
        return tokens
    
    # 按行处理，每行内部进行词级差异对比
    original_lines = original.splitlines(True)  # 保留换行符
    optimized_lines = optimized.splitlines(True)
    
    html_parts = ['<div class="diff-container" style="font-family: \'Consolas\', \'Monaco\', \'Courier New\', monospace; line-height: 1.8; padding: 20px; background: #ffffff; border: 1px solid #e0e0e0; border-radius: 8px; max-width: 100%; overflow-x: auto;">']
    html_parts.append('<style>')
    html_parts.append('''
        .diff-deleted {
            background-color: #ffebee;
            color: #c62828;
            text-decoration: line-through;
            padding: 2px 4px;
            border-radius: 3px;
            display: inline-block;
        }
        .diff-added {
            background-color: #e8f5e9;
            color: #2e7d32;
            padding: 2px 4px;
            border-radius: 3px;
            display: inline-block;
        }
        .diff-unchanged {
            color: #333;
        }
        .diff-line {
            margin: 2px 0;
            padding: 4px 8px;
            white-space: pre-wrap;
            word-wrap: break-word;
            border-left: 3px solid transparent;
        }
        .diff-line-deleted {
            background-color: #fff5f5;
            border-left-color: #ff5252;
        }
        .diff-line-added {
            background-color: #f1f8f4;
            border-left-color: #4caf50;
        }
        .diff-line-modified {
            background-color: #fffef0;
            border-left-color: #ffc107;
        }
    ''')
    html_parts.append('</style>')
    
    # 使用 SequenceMatcher 进行行级对比
    line_matcher = difflib.SequenceMatcher(None, original_lines, optimized_lines)
    
    for tag, i1, i2, j1, j2 in line_matcher.get_opcodes():
        if tag == 'equal':
            # 相同的行，检查行内是否有差异
            for line_idx in range(i1, i2):
                line = original_lines[line_idx]
                # 如果行完全相同，直接显示
                html_parts.append(f'<div class="diff-line diff-unchanged">{escape_html(line)}</div>')
                
        elif tag == 'delete':
            # 删除的行（红色背景）
            for line_idx in range(i1, i2):
                line = original_lines[line_idx]
                html_parts.append(f'<div class="diff-line diff-line-deleted"><span class="diff-deleted">{escape_html(line.rstrip())}</span></div>')
                
        elif tag == 'insert':
            # 添加的行（绿色背景）
            for line_idx in range(j1, j2):
                line = optimized_lines[line_idx]
                html_parts.append(f'<div class="diff-line diff-line-added"><span class="diff-added">{escape_html(line.rstrip())}</span></div>')
                
        elif tag == 'replace':
            # 替换的行：进行词级差异对比
            for orig_idx in range(i1, i2):
                orig_line = original_lines[orig_idx]
                # 尝试找到对应的优化行
                if j1 < j2:
                    opt_line = optimized_lines[j1]
                    j1 += 1
                    
                    # 对这两行进行词级差异对比
                    orig_tokens = tokenize(orig_line)
                    opt_tokens = tokenize(opt_line)
                    word_matcher = difflib.SequenceMatcher(None, orig_tokens, opt_tokens)
                    
                    html_parts.append('<div class="diff-line diff-line-modified">')
                    for word_tag, wi1, wi2, wj1, wj2 in word_matcher.get_opcodes():
                        if word_tag == 'equal':
                            for token in orig_tokens[wi1:wi2]:
                                html_parts.append(f'<span class="diff-unchanged">{escape_html(token)}</span>')
                        elif word_tag == 'delete':
                            deleted_text = ''.join(orig_tokens[wi1:wi2])
                            html_parts.append(f'<span class="diff-deleted">{escape_html(deleted_text)}</span>')
                        elif word_tag == 'insert':
                            added_text = ''.join(opt_tokens[wj1:wj2])
                            html_parts.append(f'<span class="diff-added">{escape_html(added_text)}</span>')
                        elif word_tag == 'replace':
                            deleted_text = ''.join(orig_tokens[wi1:wi2])
                            added_text = ''.join(opt_tokens[wj1:wj2])
                            html_parts.append(f'<span class="diff-deleted">{escape_html(deleted_text)}</span>')
                            html_parts.append(f'<span class="diff-added">{escape_html(added_text)}</span>')
                    html_parts.append('</div>')
                else:
                    # 没有对应的优化行，显示为删除
                    html_parts.append(f'<div class="diff-line diff-line-deleted"><span class="diff-deleted">{escape_html(orig_line.rstrip())}</span></div>')
            
            # 处理剩余的添加行
            while j1 < j2:
                opt_line = optimized_lines[j1]
                html_parts.append(f'<div class="diff-line diff-line-added"><span class="diff-added">{escape_html(opt_line.rstrip())}</span></div>')
                j1 += 1
    
    html_parts.append('</div>')
    
    return ''.join(html_parts)


def _generate_diff_html(original: str, optimized: str) -> tuple[str, Dict[str, int]]:
    """
    生成HTML格式的差异对比（行内高亮显示）
    删除的内容用红色背景和删除线，添加的内容用绿色背景
    
    Returns:
        (diff_html, stats) - HTML字符串和统计信息
    """
    import difflib
    
    # 生成行内差异高亮
    inline_diff_html = _generate_inline_diff_html(original, optimized)
    
    # 统计变化
    original_lines = original.splitlines(keepends=True)
    optimized_lines = optimized.splitlines(keepends=True)
    diff = list(difflib.unified_diff(original_lines, optimized_lines, lineterm=''))
    additions = sum(1 for line in diff if line.startswith('+') and not line.startswith('+++'))
    deletions = sum(1 for line in diff if line.startswith('-') and not line.startswith('---'))
    
    stats = {
        'additions': additions,
        'deletions': deletions,
        'modifications': min(additions, deletions)
    }
    
    return inline_diff_html, stats


@app.get("/")
async def root():
    """API根路径，显示欢迎信息和可用端点"""
    return {
        "message": "GitHub 文档质量分析系统 API",
        "version": "2.1.0",
        "docs": "/docs",
        "redoc": "/redoc",
        "api_endpoints": {
            "scan_repo": {
                "path": "/api/scan-repo",
                "method": "POST",
                "description": "扫描仓库所有文档（12种类型）"
            },
            "analyze_project": {
                "path": "/api/analyze-project",
                "method": "POST",
                "description": "分析选定的项目文档（支持多选）"
            },
            "optimize_document": {
                "path": "/api/optimize-document",
                "method": "POST",
                "description": "优化单个文档"
            },
            "batch_optimize": {
                "path": "/api/batch-optimize",
                "method": "POST",
                "description": "批量优化多个文档并生成差异对比"
            }
        },
        "supported_doc_types": [
            "readme",
            "contributing",
            "code_of_conduct",
            "changelog",
            "license",
            "security",
            "support",
            "wiki",
            "docs",
            "installation",
            "usage",
            "api"
        ],
        "features": {
            "scanning": [
                "一次性扫描12种文档类型",
                "自动识别常见文件名变体",
                "支持.github目录和docs目录"
            ],
            "analysis": [
                "选择性分析（只分析勾选的文档）",
                "规则检查：链接、代码块、标题、章节、语法",
                "AI语义分析：内容质量、可读性、完整性"
            ],
            "optimization": [
                "基于AI建议的自动优化",
                "批量优化多个文档",
                "HTML差异对比（高亮显示变化）",
                "精确统计添加/删除/修改行数"
            ]
        },
        "workflow": [
            "1. 调用 /api/scan-repo 扫描仓库",
            "2. 显示找到的文档列表",
            "3. 用户多选要分析的文档",
            "4. 调用 /api/analyze-project 分析",
            "5. 显示每个文档的评分和问题",
            "6. 调用 /api/batch-optimize 优化",
            "7. 显示优化结果和差异对比"
        ]
    }


if __name__ == "__main__":
    import uvicorn
    
    host = os.getenv('API_HOST', '0.0.0.0')
    port = int(os.getenv('API_PORT', 8000))
    
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=True,  # 开发时启用热重载
        log_level="info"
    )
