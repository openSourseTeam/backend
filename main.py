
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
async def analyze_readme(request: Dict[str, Any]):
    """
    分析README内容的质量
    
    - **content**: README的Markdown内容
    """
    logger.info("收到README分析请求")
    
    try:
        # 检查请求内容
        content = request.get("content", "").strip()
        if not content:
            logger.error("README内容为空")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="README内容不能为空"
            )
        
        readability = get_readability(content)
        
        logger.info("README分析成功")
        return readability
    
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
@app.post("/api/analyze-readme")
async def analyze_readme(request: Dict[str, Any]):
    """
    分析README内容的质量
    
    - **content**: README的Markdown内容
    """
    logger.info("收到README分析请求")
    
    try:
        # 检查请求内容
        content = request.get("content", "").strip()
        if not content:
            logger.error("README内容为空")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="README内容不能为空"
            )
        
        readability = get_readability(content)

        # 调用分析函数
        api_key = 'sk-99ed7f2e56bd478cb3147fd1593d4157'
        # api_key = os.getenv("OPENAI_API_KEY", "your_openai_api_key")  # 从环境变量中获取API Key
        result = analyze_readme_with_llm(content, readability, api_key)
        
        if "error" in result:
            logger.error(f"README分析失败: {result['error']}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"README分析失败: {result['error']}"
            )
        
        logger.info("README分析成功")
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