
import os
os.environ["NLTK_DATA"] = "./nltk_data"

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict, Any
import logging


from models import DownloadRequest, DownloadResponse
from github_service import GitHubService

from readability import get_readability
from code_checker import check_document_quality

# import nltk
# nltk.set_proxy('http://127.0.0.1:7890')

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 创建FastAPI应用
app = FastAPI(
    title="GitHub README 下载器 API",
    description="用于下载和分析GitHub仓库README文档的API服务",
    version="1.0.0",
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


@app.post("/api/download-readme", response_model=DownloadResponse)
async def download_readme(request: DownloadRequest):
    """
    下载指定GitHub仓库的README文件
    
    - **repo_url**: GitHub仓库URL，支持多种格式：
        - https://github.com/username/reponame
        - github.com/username/reponame  
        - username/reponame
    """
    logger.info(f"收到README下载请求: {request.repo_url}")
    
    try:
        # 提取仓库信息
        owner, repo = github_service.extract_repo_info(request.repo_url)
        if not owner or not repo:
            logger.error(f"无效的GitHub仓库URL: {request.repo_url}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="无效的GitHub仓库URL，请检查格式是否正确"
            )
        
        logger.info(f"提取的仓库信息: {owner}/{repo}")
        
        # 获取仓库基本信息
        repo_info = github_service.get_repo_info(owner, repo)
        if not repo_info:
            logger.error(f"仓库不存在或无法访问: {owner}/{repo}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="仓库不存在或无法访问，请检查仓库名称和权限"
            )
        
        # 获取README内容
        readme_result = github_service.get_readme_content(owner, repo)
        
        if 'error' in readme_result:
            logger.error(f"获取README失败: {readme_result['error']}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=readme_result['error']
            )
        
        # 构建响应数据
        response_data = DownloadResponse(
            success=True,
            repo_info={
                "owner": owner,
                "repo": repo,
                "full_name": f"{owner}/{repo}",
                "url": f"https://github.com/{owner}/{repo}",
                "description": repo_info.get('description', ''),
                "stars": repo_info.get('stargazers_count', 0),
                "forks": repo_info.get('forks_count', 0),
                "language": repo_info.get('language', ''),
                "license": repo_info.get('license', {}).get('name', '') if repo_info.get('license') else ''
            },
            readme_info={
                "filename": readme_result['filename'],
                "size": readme_result['size'],
                "sha": readme_result['sha'],
                "download_url": readme_result['download_url']
            },
            content=readme_result['content']
        )
        
        logger.info(f"成功获取README: {owner}/{repo}, 大小: {readme_result['size']} 字节")
        return response_data
        
    except HTTPException:
        # 重新抛出已有的HTTP异常
        raise
    except Exception as e:
        logger.error(f"服务器内部错误: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"服务器内部错误: {str(e)}"
        )


@app.post("/api/scan-repo")
async def scan_repo_docs(request: DownloadRequest):
    """
    扫描仓库文档
    此步骤只获取文档内容，不进行深入分析
    """
    logger.info(f"收到文档扫描请求: {request.repo_url}")
    
    try:
        owner, repo = github_service.extract_repo_info(request.repo_url)
        if not owner or not repo:
            raise HTTPException(status_code=400, detail="无效的GitHub仓库URL")
            
        # 获取所有文档
        docs = github_service.get_all_repo_docs(owner, repo)
        
        # 统计找到的文档
        found_count = sum(1 for v in docs.values() if v is not None)
        logger.info(f"扫描完成，找到 {found_count} 个文档")
        
        return {
            "success": True,
            "repo_info": {
                "owner": owner,
                "repo": repo,
                "full_name": f"{owner}/{repo}"
            },
            "docs": docs
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"扫描失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/analyze-project")
async def analyze_project(request: Dict[str, Any]):
    """
    分析项目文档（接收 scan-repo 返回的 docs 结构）
    """
    logger.info("收到项目分析请求")
    
    try:
        docs = request.get("docs", {})
        if not docs:
            raise HTTPException(status_code=400, detail="未提供文档内容")
            
        # 1. 规则检查
        rule_check_results = {}
        combined_markdown = ""
        
        for doc_type, doc_info in docs.items():
            if doc_info and 'content' in doc_info:
                content = doc_info['content']
                # 累加用于AI分析的文本
                combined_markdown += f"\n\n# FILE: {doc_info['filename']} ({doc_type.upper()})\n\n{content}"
                
                # 单个文档规则检查
                check_result = check_document_quality(content, doc_type)
                rule_check_results[doc_type] = check_result
        
        # 2. AI 分析
        from ask import analyze_readme_with_llm # Note: This imports the function we modified, even if name is old
        from fastapi.concurrency import run_in_threadpool

        # We need to construct the input for LLM
        # The modified ask.py expects 'docs_content' and 'rule_checks' in user prompt format
        
        # 简化规则检查结果给LLM
        simple_rule_checks = {}
        for dtype, res in rule_check_results.items():
            simple_rule_checks[dtype] = {
                "issues_count": res['summary']['total_issues'],
                "missing_sections": res['section_completeness_check'].get('missing_sections', [])
            }
            
        api_key = 'sk-99ed7f2e56bd478cb3147fd1593d4157'
        
        # 调用ask.py中的分析函数 (注意：我们需要适配 ask.py 的参数)
        # 实际上我们修改了 ask.py 的 user_prompt, 但函数签名还是 analyze_readme_with_llm(markdown_content, readability, api_key)
        # 我们这里把 simple_rule_checks 当作 readability 传进去，因为 prompt 里使用的是 {readability} 占位符
        
        logger.info("开始调用 LLM 进行分析...")
        ai_result = await run_in_threadpool(analyze_readme_with_llm, combined_markdown, simple_rule_checks, api_key)
        logger.info("LLM 分析完成")
        
        return {
            "success": True,
            "rule_checks": rule_check_results,
            "ai_analysis": ai_result
        }

    except Exception as e:
        logger.error(f"分析失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


def _generate_recommendation(code_passed: bool, code_issues: int, ai_score: int) -> str:
    """生成最终建议"""
    if code_passed and ai_score >= 80:
        return "优秀 - 文档质量很高"
    elif code_passed and ai_score >= 60:
        return "良好 - 有一些改进空间"
    elif not code_passed and code_issues <= 3:
        return "需要改进 - 修复代码检查问题"
    else:
        return "亟需改进 - 存在较多问题"


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