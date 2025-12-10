import requests
import base64
import logging
import os
from urllib.parse import urlparse
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

GITHUB_TOKEN = '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'  # 替换为你的 GitHub Token
headers = {
    'Authorization': f'token {GITHUB_TOKEN}',
    'Accept': 'application/vnd.github.v3+json'
}

class GitHubService:
    def __init__(self):
        self.github_token = os.getenv('GITHUB_TOKEN')
        self.base_headers = {
            'Accept': 'application/vnd.github.v3+json',
            'User-Agent': 'README-Quality-Checker/1.0'
        }
        if self.github_token:
            self.base_headers['Authorization'] = f'token {self.github_token}'
        
        self.session = requests.Session()
        self.session.headers.update(self.base_headers)

    def extract_repo_info(self, repo_url: str) -> tuple[Optional[str], Optional[str]]:
        """从GitHub仓库URL提取用户名和仓库名"""
        try:
            # 处理直接输入 username/repo 的情况
            if '/' in repo_url and 'github.com' not in repo_url:
                parts = repo_url.split('/')
                if len(parts) >= 2:
                    return parts[0], parts[1]
            
            # 确保URL有协议头
            if not repo_url.startswith('http'):
                repo_url = 'https://' + repo_url
            
            parsed = urlparse(repo_url)
            path_parts = parsed.path.strip('/').split('/')
            
            if len(path_parts) >= 2:
                owner = path_parts[0]
                repo = path_parts[1].replace('.git', '')  # 移除.git后缀
                return owner, repo
                
        except Exception as e:
            logger.error(f"URL解析错误: {e}")
        
        return None, None

    def get_rate_limit(self) -> Dict[str, Any]:
        """获取GitHub API速率限制信息"""
        try:
            response = self.session.get('https://api.github.com/rate_limit')
            if response.status_code == 200:
                return response.json()
        except Exception as e:
            logger.error(f"获取速率限制失败: {e}")
        return {}

    def get_repo_info(self, owner: str, repo: str) -> Optional[Dict[str, Any]]:
        """获取仓库基本信息"""
        url = f'https://api.github.com/repos/{owner}/{repo}'
        try:
            response = self.session.get(url, headers=headers)
            if response.status_code == 200:
                return response.json()
            else:
                logger.warning(f"获取仓库信息失败: {response.status_code}")
        except Exception as e:
            logger.error(f"获取仓库信息错误: {e}")
        return None

    def get_readme_content(self, owner: str, repo: str) -> Dict[str, Any]:
        """获取仓库的README内容，尝试多种可能的文件名"""
        readme_files = [
            'README.md',
            'readme.md', 
            'README.MD',
            'README',
            'readme',
            'README.txt',
            'readme.txt'
        ]
        
        for readme_file in readme_files:
            url = f'https://api.github.com/repos/{owner}/{repo}/contents/{readme_file}'
            logger.info(f"尝试获取README: {url}")
            
            try:
                response = self.session.get(url, headers=headers)
                
                if response.status_code == 200:
                    data = response.json()
                    if 'content' in data:
                        # GitHub API返回的是base64编码的内容
                        content = base64.b64decode(data['content']).decode('utf-8')
                        logger.info(f"成功获取 {readme_file}, 大小: {len(content)} 字符")
                        
                        return {
                            'content': content,
                            'filename': readme_file,
                            'download_url': data.get('download_url', ''),
                            'sha': data.get('sha', ''),
                            'size': data.get('size', 0),
                            'html_url': data.get('html_url', '')
                        }
                
                elif response.status_code == 404:
                    continue  # 尝试下一个文件名
                    
                elif response.status_code == 403:
                    rate_limit = self.get_rate_limit()
                    limits = rate_limit.get('resources', {}).get('core', {})
                    error_msg = "GitHub API速率限制"
                    if limits.get('remaining') == 0:
                        reset_time = limits.get('reset')
                        error_msg += f"，重置时间: {reset_time}"
                    logger.error(error_msg)
                    return {'error': error_msg}
                    
                elif response.status_code == 401:
                    error_msg = "GitHub API认证失败"
                    logger.error(error_msg)
                    return {'error': error_msg}
                    
                else:
                    logger.error(f"GitHub API错误: {response.status_code} - {response.text}")
                    return {'error': f'GitHub API错误: {response.status_code}'}
                    
            except requests.exceptions.RequestException as e:
                logger.error(f"网络请求错误: {e}")
                return {'error': f'网络请求失败: {str(e)}'}
            except Exception as e:
                logger.error(f"处理响应错误: {e}")
                return {'error': f'处理响应失败: {str(e)}'}
        
        return {'error': '未找到README文件'}

    def get_all_repo_docs(self, owner: str, repo: str) -> Dict[str, Any]:
        """获取仓库的所有主要文档"""
        docs_to_find = {
            'readme': ['README.md', 'readme.md', 'README', 'readme', 'README.txt'],
            'contributing': ['CONTRIBUTING.md', 'contributing.md', 'CONTRIBUTING', 'contributing'],
            'code_of_conduct': ['CODE_OF_CONDUCT.md', 'code_of_conduct.md', 'CODE_OF_CONDUCT'],
            'changelog': ['CHANGELOG.md', 'changelog.md', 'CHANGELOG', 'HISTORY.md'],
            'license': ['LICENSE', 'license', 'LICENSE.md', 'license.md', 'LICENSE.txt']
        }
        
        results = {}
        
        for doc_type, filenames in docs_to_find.items():
            found = False
            for filename in filenames:
                url = f'https://api.github.com/repos/{owner}/{repo}/contents/{filename}'
                try:
                    response = self.session.get(url, headers=headers)
                    if response.status_code == 200:
                        data = response.json()
                        if 'content' in data:
                            content = base64.b64decode(data['content']).decode('utf-8')
                            results[doc_type] = {
                                'content': content,
                                'filename': filename,
                                'download_url': data.get('download_url', ''),
                                'html_url': data.get('html_url', ''),
                                'size': data.get('size', 0)
                            }
                            found = True
                            logger.info(f"找到 {doc_type}: {filename}")
                            break # 找到一种后缀即可
                except Exception as e:
                    logger.warning(f"检查 {filename} 时出错: {e}")
                    continue
            
            if not found:
                results[doc_type] = None
                
        return results