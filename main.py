
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
            
        # 获取所有文档（12种类型）
        docs = github_service.get_all_repo_docs(owner, repo)
        
        # 统计找到的文档
        found_count = sum(1 for v in docs.values() if v is not None)
        logger.info(f"扫描完成，找到 {found_count}/12 个文档")
        
        return {
            "success": True,
            "repo_info": {
                "owner": owner,
                "repo": repo,
                "full_name": f"{owner}/{repo}"
            },
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
        rule_check_results = {}
        combined_markdown = ""
        
        for doc_type in selected_types:
            doc_info = docs.get(doc_type)
            if doc_info and 'content' in doc_info:
                content = doc_info['content']
                # 累加用于AI分析的文本
                combined_markdown += f"\n\n# FILE: {doc_info['filename']} ({doc_type.upper()})\n\n{content}"
                
                # 单个文档规则检查
                check_result = check_document_quality(content, doc_type)
                rule_check_results[doc_type] = check_result
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
        simple_rule_checks = {}
        for dtype, res in rule_check_results.items():
            simple_rule_checks[dtype] = {
                "issues_count": res['summary']['total_issues'],
                "missing_sections": res['section_completeness_check'].get('missing_sections', [])
            }
            
        api_key = 'sk-99ed7f2e56bd478cb3147fd1593d4157'
        
        logger.info("开始调用 LLM 进行分析...")
        ai_result = await run_in_threadpool(analyze_readme_with_llm, combined_markdown, readability_data, api_key)
        logger.info("LLM 分析完成")
        
        return {
            "success": True,
            "selected_doc_types": selected_types,
            "rule_checks": rule_check_results,
            "readability": readability_data,
            "ai_analysis": ai_result
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
        
        return OptimizeDocumentResponse(
            success=True,
            original_content=request.original_content,
            optimized_content=optimized_content,
            changes_summary=changes_summary
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


def _generate_diff_html(original: str, optimized: str) -> tuple[str, Dict[str, int]]:
    """
    生成HTML格式的差异对比，带高亮显示
    
    Returns:
        (diff_html, stats) - HTML字符串和统计信息
    """
    import difflib
    
    original_lines = original.splitlines(keepends=True)
    optimized_lines = optimized.splitlines(keepends=True)
    
    differ = difflib.HtmlDiff(wrapcolumn=80)
    diff_html = differ.make_table(
        original_lines,
        optimized_lines,
        fromdesc='原始文档',
        todesc='优化后文档',
        context=True,
        numlines=3
    )
    
    # 统计变化
    diff = list(difflib.unified_diff(original_lines, optimized_lines, lineterm=''))
    additions = sum(1 for line in diff if line.startswith('+') and not line.startswith('+++'))
    deletions = sum(1 for line in diff if line.startswith('-') and not line.startswith('---'))
    
    stats = {
        'additions': additions,
        'deletions': deletions,
        'modifications': min(additions, deletions)  # 估算修改数
    }
    
    return diff_html, stats


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
