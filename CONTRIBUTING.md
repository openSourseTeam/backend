# Contributing to GitHub Documentation Quality Analysis System

感谢您对 GitHub 文档质量分析系统的贡献兴趣。我们欢迎所有形式的贡献。

## 目录

- [行为准则](#行为准则)
- [如何贡献](#如何贡献)
- [开发环境搭建](#开发环境搭建)
- [代码规范](#代码规范)
- [提交规范](#提交规范)
- [Pull Request 流程](#pull-request-流程)

## 行为准则

本项目采用 [行为准则](CODE_OF_CONDUCT.md)。参与本项目即表示您同意遵守其条款。

## 如何贡献

您可以通过以下方式贡献：

### 报告 Bug

如果您发现 Bug，请创建 Issue 并包含：

- Bug 的详细描述
- 复现步骤
- 期望行为
- 实际行为
- 运行环境（Python 版本、操作系统等）
- 相关日志或截图

### 提出新功能

如果您有新功能建议：

- 创建 Issue 描述功能需求
- 说明功能的使用场景
- 如有可能，提供实现思路

### 改进文档

文档改进包括：

- 修复拼写或语法错误
- 添加使用示例
- 改进 API 文档
- 翻译文档

### 提交代码

1. Fork 本仓库
2. 创建您的特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交您的更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

## 开发环境搭建

### 前置要求

- Python 3.8+
- pip

### 安装步骤

1. **克隆仓库**

```bash
git clone https://github.com/openSourseTeam/backend.git
cd backend
```

2. **创建虚拟环境**

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

3. **安装依赖**

```bash
pip install -r requirements.txt
```

4. **配置环境变量**

创建 `.env` 文件（可选）：

```env
API_HOST=0.0.0.0
API_PORT=8000
```

5. **运行开发服务器**

```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

6. **访问 API 文档**

打开浏览器访问：
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 代码规范

### Python 代码规范

我们遵循 [PEP 8](https://www.python.org/dev/peps/pep-0008/) 代码规范。

#### 命名规范

- **变量和函数**: 小写字母，单词间用下划线分隔 (`snake_case`)
  ```python
  def get_repo_info(owner, repo):
      repo_name = f"{owner}/{repo}"
  ```

- **类名**: 大驼峰命名法 (`PascalCase`)
  ```python
  class GitHubService:
      pass
  ```

- **常量**: 全大写，单词间用下划线分隔
  ```python
  API_VERSION = "2.1.0"
  MAX_RETRIES = 3
  ```

#### 类型提示

使用类型提示增强代码可读性：

```python
from typing import Dict, List, Optional

def analyze_document(content: str, doc_type: str) -> Dict[str, any]:
    pass
```

#### 文档字符串

使用 Google 风格的文档字符串：

```python
def scan_repo_docs(repo_url: str) -> Dict:
    """
    扫描仓库所有文档
    
    Args:
        repo_url: GitHub仓库URL
        
    Returns:
        包含所有找到的文档内容和元数据
        
    Raises:
        HTTPException: 当仓库URL无效或访问失败时
    """
    pass
```

#### 日志记录

使用 logging 模块记录日志：

```python
import logging

logger = logging.getLogger(__name__)

logger.info("扫描完成")
logger.warning("无法获取仓库信息")
logger.error(f"分析失败: {e}")
```

#### 错误处理

合理处理异常：

```python
try:
    result = process_data()
except ValueError as e:
    logger.error(f"数据处理错误: {e}")
    raise HTTPException(status_code=400, detail="无效的输入数据")
except Exception as e:
    logger.error(f"未知错误: {e}")
    raise HTTPException(status_code=500, detail="内部服务器错误")
```

### 代码格式化

建议使用以下工具：

- **Black**: 代码格式化
  ```bash
  pip install black
  black .
  ```

- **isort**: 导入排序
  ```bash
  pip install isort
  isort .
  ```

- **flake8**: 代码检查
  ```bash
  pip install flake8
  flake8 .
  ```

## 提交规范

### Commit Message 格式

使用以下格式编写提交信息：

```
<type>(<scope>): <subject>

<body>

<footer>
```

#### Type 类型

- `feat`: 新功能
- `fix`: Bug 修复
- `docs`: 文档更新
- `style`: 代码格式调整（不影响功能）
- `refactor`: 重构（既不是新功能也不是 Bug 修复）
- `perf`: 性能优化
- `test`: 添加或修改测试
- `chore`: 构建过程或辅助工具的变动

#### 示例

```
feat(api): 添加批量优化文档接口

- 实现 /api/batch-optimize 端点
- 支持同时优化多个文档
- 生成 HTML 差异对比

Closes #123
```

## Pull Request 流程

1. **确保代码质量**
   - 通过所有测试
   - 遵循代码规范
   - 添加必要的文档

2. **更新 CHANGELOG**
   
   在 `CHANGELOG.md` 中记录您的更改

3. **填写 PR 模板**
   
   描述您的更改内容和动机

4. **等待审查**
   
   维护者会尽快审查您的 PR

5. **响应反馈**
   
   根据审查意见修改代码

6. **合并**
   
   PR 被批准后，维护者会合并您的代码

## 测试

### 运行测试

```bash
# 运行所有测试
pytest

# 运行指定测试文件
pytest tests/test_github_service.py

# 查看覆盖率
pytest --cov=.
```

### 编写测试

为新功能编写单元测试：

```python
import pytest
from main import app
from fastapi.testclient import TestClient

client = TestClient(app)

def test_scan_repo():
    response = client.post("/api/scan-repo", json={
        "repo_url": "owner/repo"
    })
    assert response.status_code == 200
    assert "success" in response.json()
```

## 需要帮助？

如有任何问题：

- 提交 Issue
- 参与 Discussions
- 查看 [API 文档](前端API调用指南.md)

再次感谢您的贡献。

