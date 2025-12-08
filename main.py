
import os
os.environ["NLTK_DATA"] = "./nltk_data"

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict, Any
import logging


from models import DownloadRequest, DownloadResponse
from github_service import GitHubService

from readability import get_readability

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


@app.post("/api/analyze-readme-init")
async def analyze_readme_init(request: Dict[str, Any]):
    """
    第一部分：代码层面审查（规则检测，不使用AI）
    包含可读性分析和代码质量检查
    
    - **content**: README的Markdown内容
    - **doc_type**: 文档类型（可选，默认readme）
    """
    logger.info("收到代码审查请求（第一部分）")
    
    try:
        # 检查请求内容
        content = request.get("content", "").strip()
        if not content:
            logger.error("README内容为空")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="README内容不能为空"
            )
        
        doc_type = request.get("doc_type", "readme")
        
        # 第一部分：可读性分析
        logger.info("执行可读性分析...")
        readability = get_readability(content)
        
        # 第二部分：代码质量检查
        logger.info("执行代码质量检查...")
        code_check_results = check_document_quality(content, doc_type)
        
        # 合并结果
        result = {
            "stage": "代码审查（第一部分）",
            "readability": readability,
            "code_check": code_check_results,
            "summary": {
                "readability_level": readability.get("text_standard", "N/A"),
                "code_check_passed": code_check_results["summary"]["overall_passed"],
                "code_issues_count": code_check_results["summary"]["total_issues"],
                "checks_completed": code_check_results["summary"]["total_checks"]
            }
        }
        
        logger.info(f"代码审查完成: {result['summary']['checks_completed']} 项检查，发现 {result['summary']['code_issues_count']} 个问题")
        return result
    
    except HTTPException:
        # 重新抛出已有的HTTP异常
        raise
    except Exception as e:
        logger.error(f"服务器内部错误: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"服务器内部错误: {str(e)}"
        )

from ask import analyze_readme_with_llm  # 导入分析函数
from code_checker import check_document_quality  # 导入代码检查模块

@app.post("/api/analyze-readme")
async def analyze_readme(request: Dict[str, Any]):
    """
    双轨制完整分析：第一部分代码审查 + 第二部分AI分析
    
    - **content**: README的Markdown内容
    - **doc_type**: 文档类型（可选，默认readme）
    """
    logger.info("收到双轨制完整分析请求")
    
    try:
        # 检查请求内容
        content = request.get("content", "").strip()
        if not content:
            logger.error("README内容为空")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="README内容不能为空"
            )
        
        doc_type = request.get("doc_type", "readme")
        
        # ========== 第一部分：代码审查 ==========
        logger.info("【第一部分】执行代码审查...")
        
        # 可读性分析
        readability = get_readability(content)
        
        # 代码质量检查
        code_check_results = check_document_quality(content, doc_type)
        
        logger.info(f"【第一部分】完成: 发现 {code_check_results['summary']['total_issues']} 个问题")
        
        # ========== 第二部分：AI 分析 ==========
        logger.info("【第二部分】执行AI语义分析...")
        
        # 调用分析函数
        api_key = 'sk-99ed7f2e56bd478cb3147fd1593d4157'
        # api_key = os.getenv("OPENAI_API_KEY", "your_openai_api_key")  # 从环境变量中获取API Key
        ai_analysis = analyze_readme_with_llm(content, readability, api_key)
        
        if "error" in ai_analysis:
            logger.error(f"AI分析失败: {ai_analysis['error']}")
            # AI分析失败，仍然返回代码审查结果
            return {
                "success": False,
                "part_1_code_review": {
                    "readability": readability,
                    "code_check": code_check_results
                },
                "part_2_ai_analysis": None,
                "error": ai_analysis['error']
            }
        
        logger.info(f"【第二部分】完成: AI评分 {ai_analysis.get('overall_score', 0)}/100")
        
        # ========== 合并两部分结果 ==========
        complete_result = {
            "success": True,
            "evaluation_mode": "双轨制评估",
            "part_1_code_review": {
                "description": "代码层面规则检测（快速、无成本）",
                "readability": readability,
                "code_check": code_check_results
            },
            "part_2_ai_analysis": {
                "description": "AI语义理解分析（深度、有成本）",
                "overall_score": ai_analysis.get("overall_score", 0),
                "dimension_scores": ai_analysis.get("dimension_scores", {}),
                "strengths": ai_analysis.get("strengths", []),
                "missing_sections": ai_analysis.get("missing_sections", []),
                "beginner_confusion_points": ai_analysis.get("beginner_confusion_points", []),
                "code_quality_issues": ai_analysis.get("code_quality_issues", []),
                "structural_issues": ai_analysis.get("structural_issues", []),
                "language_issues": ai_analysis.get("language_issues", []),
                "priority_recommendations": ai_analysis.get("priority_recommendations", []),
                "suggestions": ai_analysis.get("suggestions", []),
                "convention_issues": ai_analysis.get("convention_issues", [])
            },
            "final_summary": {
                "code_check_passed": code_check_results["summary"]["overall_passed"],
                "code_issues_count": code_check_results["summary"]["total_issues"],
                "ai_overall_score": ai_analysis.get("overall_score", 0),
                "readability_level": readability.get("text_standard", "N/A"),
                "recommendation": _generate_recommendation(
                    code_check_results["summary"]["overall_passed"],
                    code_check_results["summary"]["total_issues"],
                    ai_analysis.get("overall_score", 0)
                )
            }
        }
        
        logger.info("双轨制分析完成")
        return complete_result
    
    except HTTPException:
        # 重新抛出已有的HTTP异常
        raise
    except Exception as e:
        logger.error(f"服务器内部错误: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"服务器内部错误: {str(e)}"
        )


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