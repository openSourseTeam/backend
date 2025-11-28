from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List

class DownloadRequest(BaseModel):
    repo_url: str = Field(..., description="GitHub仓库URL")

class RepoInfo(BaseModel):
    owner: str
    repo: str
    full_name: str
    url: str
    description: Optional[str] = ""
    stars: int = 0
    forks: int = 0
    language: Optional[str] = ""
    license: Optional[str] = ""

class ReadmeInfo(BaseModel):
    filename: str
    size: int
    sha: str
    download_url: str

class DownloadResponse(BaseModel):
    success: bool
    repo_info: Optional[RepoInfo] = None
    readme_info: Optional[ReadmeInfo] = None
    content: Optional[str] = None
    error: Optional[str] = None

class HealthResponse(BaseModel):
    status: str
    service: str
    github_rate_limit: Optional[Dict] = None