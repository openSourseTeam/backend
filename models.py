from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from enum import Enum

class DownloadRequest(BaseModel):
    repo_url: str = Field(..., description="GitHub仓库URL")

class OptimizeDocumentRequest(BaseModel):
    """文档优化请求"""
    original_content: str = Field(..., description="原始文档内容")
    analysis_result: Dict[str, Any] = Field(..., description="AI分析结果")
    doc_type: str = Field(default="readme", description="文档类型")

class OptimizeDocumentResponse(BaseModel):
    """文档优化响应"""
    success: bool
    original_content: Optional[str] = None
    optimized_content: Optional[str] = None
    changes_summary: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

class SelectiveAnalyzeRequest(BaseModel):
    """选择性分析请求"""
    docs: Dict[str, Any] = Field(..., description="文档内容字典")
    selected_doc_types: List[str] = Field(..., description="选择要分析的文档类型列表")


class BatchOptimizeRequest(BaseModel):
    """批量优化请求"""
    documents: List[Dict[str, Any]] = Field(..., description="要优化的文档列表")
    
class DocumentDiff(BaseModel):
    """文档差异"""
    doc_type: str
    original_content: str
    optimized_content: str
    diff_html: str  # HTML格式的差异对比
    additions: int  # 添加的行数
    deletions: int  # 删除的行数
    modifications: int  # 修改的行数

class BatchOptimizeResponse(BaseModel):
    """批量优化响应"""
    success: bool
    results: List[Dict[str, Any]] = []
    diffs: List[DocumentDiff] = []
    error: Optional[str] = None