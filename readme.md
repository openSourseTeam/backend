# GitHub 文档质量分析系统 API

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115.6-009688.svg?logo=fastapi)](https://fastapi.tiangolo.com)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

基于 AI 的 GitHub 仓库文档质量分析和优化系统。

本系统是一个强大的后端 API 服务，用于自动扫描、分析和优化 GitHub 仓库的文档质量。支持 12 种主流文档类型，提供深度的规则检查、可读性分析和 AI 智能优化建议。

## 相关项目

本项目是前后端分离架构：

- **后端 API**（本仓库）：[openSourseTeam/backend](https://github.com/openSourseTeam/backend)
- **前端应用**：[openSourseTeam/frontend](https://github.com/openSourseTeam/frontend)

前端项目提供了完整的用户界面，用于与后端 API 交互。详细的前端集成指南请参考 [前端API调用指南.md](前端API调用指南.md)。

## 核心特性

### 智能文档扫描
- 12 种文档类型支持：README、CONTRIBUTING、CODE_OF_CONDUCT、CHANGELOG、LICENSE、SECURITY、SUPPORT、WIKI、DOCS、INSTALLATION、USAGE、API
- 自动识别变体：支持多种文件名格式（大小写、扩展名）
- 多目录扫描：自动搜索根目录、`.github`、`docs` 等常见位置
- 仓库信息获取：Stars、Forks、描述、语言等元数据

### 深度质量分析
**规则检查**（每个文档独立检查）
- 链接有效性检查
- 代码块格式验证
- 标题结构分析
- 章节完整性检查
- 语法问题检测

**可读性指标**（基于 textstat）
- Flesch Reading Ease（0-100，越高越易读）
- Gunning Fog Index（年级水平）
- SMOG Index（理解难度）
- 字符/单词/句子统计

**AI 语义分析**（基于 DeepSeek）
- 内容质量评估
- 完整性分析
- 专业性评分
- 优化建议生成

### 智能文档优化
- 单文档优化：针对性改进建议
- 批量优化：一次性处理多个文档
- 差异对比：HTML 格式高亮显示变化
- 精确统计：添加/删除/修改行数统计

## 快速开始

### 环境要求

- Python 3.8 或更高版本
- pip 包管理器
- （可选）虚拟环境管理工具

### 安装步骤

1. **克隆仓库**

```bash
git clone https://github.com/openSourseTeam/backend.git
cd backend
```

2. **创建虚拟环境**（推荐）

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/Mac
python3 -m venv venv
source venv/bin/activate
```

3. **安装依赖**

```bash
pip install -r requirements.txt
```

4. **配置环境变量**（可选）

创建 `.env` 文件：

```env
API_HOST=0.0.0.0
API_PORT=8000
DEEPSEEK_API_KEY=your_api_key_here  # 生产环境必需
```

5. **运行开发服务器**

```bash
# 方式 1：直接运行
python main.py

# 方式 2：使用 uvicorn
uvicorn main:app --host 0.0.0.0 --port 8000 --reload

# 方式 3：使用脚本（Linux/Mac）
./run.sh
```

6. **访问 API 文档**

- **Swagger UI**：http://localhost:8000/docs
- **ReDoc**：http://localhost:8000/redoc
- **API Root**：http://localhost:8000/

## API 使用指南

### 完整工作流程

```
1. 扫描仓库
   ↓
2. 显示文档列表
   ↓
3. 用户选择要分析的文档
   ↓
4. 执行深度分析
   ↓
5. 查看分析结果
   ↓
6. 批量优化文档
   ↓
7. 查看优化结果和差异对比
```

### 1. 扫描仓库文档

**端点**：`POST /api/scan-repo`

**请求体**：
```json
{
  "repo_url": "https://github.com/owner/repo"
}
```

**支持的 URL 格式**：
- `https://github.com/owner/repo`
- `github.com/owner/repo`
- `owner/repo`

**响应示例**：
```json
{
  "success": true,
  "repo_info": {
    "owner": "owner",
    "repo": "repo",
    "full_name": "owner/repo",
    "stargazers_count": 1234,
    "forks_count": 56,
    "description": "项目描述",
    "language": "Python"
  },
  "docs": {
    "readme": {
      "filename": "README.md",
      "path": "README.md",
      "content": "# 项目标题\n\n项目内容...",
      "size": 1024,
      "sha": "abc123..."
    },
    "contributing": {
      "filename": "CONTRIBUTING.md",
      "path": ".github/CONTRIBUTING.md",
      "content": "# 贡献指南...",
      "size": 512,
      "sha": "def456..."
    }
    // ... 其他文档
  },
  "stats": {
    "total_types": 12,
    "found_count": 8,
    "found_percentage": 66.7
  }
}
```

### 2. 分析选定文档

**端点**：`POST /api/analyze-project`

**请求体**：
```json
{
  "docs": {
    // 从 scan-repo 获取的 docs 对象
  },
  "selected_doc_types": ["readme", "contributing", "security"]
}
```

**响应示例**：
```json
{
  "success": true,
  "selected_doc_types": ["readme", "contributing"],
  "rule_checks": {
    "readme": {
      "summary": {
        "total_issues": 5,
        "severity_breakdown": {
          "high": 1,
          "medium": 2,
          "low": 2
        }
      },
      "link_check": {
        "broken_links": ["https://example.com/404"],
        "total_links": 10
      },
      "code_block_check": {
        "unlabeled_blocks": 2,
        "total_blocks": 5
      },
      "section_completeness_check": {
        "missing_sections": ["Installation", "Usage"],
        "found_sections": ["Introduction", "Features"]
      }
    }
  },
  "readability": {
    "flesch_reading_ease": 65.5,
    "gunning_fog": 8.2,
    "smog_index": 7.8,
    "char_count": 5000,
    "word_count": 800,
    "sentence_count": 45
  },
  "ai_analysis": {
    "overall_score": 75,
    "analysis": "文档整体质量良好，但需要补充安装和使用说明...",
    "suggestions": [
      "添加详细的安装步骤",
      "补充使用示例和代码片段",
      "修复失效的外部链接"
    ]
  }
}
```

### 3. 优化单个文档

**端点**：`POST /api/optimize-document`

**请求体**：
```json
{
  "original_content": "# 项目标题\n\n简单的描述...",
  "analysis_result": {
    // 从 analyze-project 获取的分析结果
  },
  "doc_type": "readme"
}
```

**响应示例**：
```json
{
  "success": true,
  "original_content": "# 项目标题\n\n简单的描述...",
  "optimized_content": "# 项目标题\n\n## 简介\n详细的项目描述...\n\n## 安装\n...",
  "changes_summary": {
    "original_length": 100,
    "optimized_length": 500,
    "length_change": 400,
    "original_lines": 3,
    "optimized_lines": 15
  }
}
```

### 4. 批量优化文档

**端点**：`POST /api/batch-optimize`

**请求体**：
```json
{
  "documents": [
    {
      "doc_type": "readme",
      "original_content": "...",
      "analysis_result": { /* ... */ }
    },
    {
      "doc_type": "contributing",
      "original_content": "...",
      "analysis_result": { /* ... */ }
    }
  ]
}
```

**响应示例**：
```json
{
  "success": true,
  "results": [
    {
      "doc_type": "readme",
      "success": true,
      "original_content": "...",
      "optimized_content": "...",
      "changes_summary": {
        "additions": 50,
        "deletions": 10,
        "modifications": 15
      }
    }
  ],
  "diffs": [
    {
      "doc_type": "readme",
      "diff_html": "<table>...</table>",  // HTML 差异对比
      "additions": 50,
      "deletions": 10,
      "modifications": 15
    }
  ]
}
```

## 项目结构

```
backend/
├── main.py                    # FastAPI 应用主文件，路由定义
├── models.py                  # Pydantic 数据模型定义
├── github_service.py          # GitHub API 交互服务
├── code_checker.py            # 文档规则检查器
├── readability.py             # 可读性指标计算
├── ask.py                     # AI 分析和优化接口
├── requirements.txt           # Python 依赖列表
├── .gitignore                 # Git 忽略文件配置
├── LICENSE                    # MIT 许可证
├── README.md                  # 项目说明文档（本文件）
├── CONTRIBUTING.md            # 贡献指南
├── CODE_OF_CONDUCT.md         # 行为准则
├── CHANGELOG.md               # 版本变更记录
├── SECURITY.md                # 安全政策
├── 前端API调用指南.md          # 前端集成文档
└── 项目文档规范检查.md         # 文档规范检查报告
```

## 技术栈

- **Web 框架**：[FastAPI](https://fastapi.tiangolo.com/) - 现代、高性能的 Python Web 框架
- **API 客户端**：[httpx](https://www.python-httpx.org/) - 异步 HTTP 客户端
- **数据验证**：[Pydantic](https://pydantic-docs.helpmanual.io/) - 数据验证和设置管理
- **文本分析**：[textstat](https://github.com/shivam5992/textstat) - 可读性指标计算
- **AI 服务**：[DeepSeek API](https://platform.deepseek.com/) - 大语言模型
- **ASGI 服务器**：[Uvicorn](https://www.uvicorn.org/) - 高性能 ASGI 服务器

## 详细文档

- [前端 API 调用指南](前端API调用指南.md) - 前端集成详细说明
- [贡献指南](CONTRIBUTING.md) - 如何参与项目开发
- [行为准则](CODE_OF_CONDUCT.md) - 社区行为规范
- [变更日志](CHANGELOG.md) - 版本历史和更新记录
- [安全政策](SECURITY.md) - 安全漏洞报告指南

## 安全注意事项

### 开发环境 vs 生产环境

**警告**：当前代码包含硬编码的 API 密钥，仅适用于开发环境。

生产环境部署前必须修改以下配置：

**1. 使用环境变量存储 API 密钥**

```python
# main.py
import os
api_key = os.getenv('DEEPSEEK_API_KEY')
if not api_key:
    raise ValueError("DEEPSEEK_API_KEY environment variable not set")
```

**2. 限制 CORS 来源**

```python
# main.py
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://yourdomain.com"],  # 限制允许的域名
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)
```

**3. 添加速率限制**

```bash
pip install slowapi
```

```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@app.post("/api/scan-repo")
@limiter.limit("10/minute")
async def scan_repo_docs(...):
    ...
```

详见 [SECURITY.md](SECURITY.md) 了解完整的安全最佳实践。

## 部署指南

### Docker 部署（推荐）

```dockerfile
# Dockerfile
FROM python:3.8-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV API_HOST=0.0.0.0
ENV API_PORT=8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

```bash
# 构建镜像
docker build -t github-doc-analyzer .

# 运行容器
docker run -d -p 8000:8000 \
  -e DEEPSEEK_API_KEY=your_api_key \
  github-doc-analyzer
```

### 传统部署

```bash
# 使用 gunicorn + uvicorn workers
pip install gunicorn
gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

### Nginx 反向代理

```nginx
server {
    listen 80;
    server_name yourdomain.com;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
```

## 测试

```bash
# 安装测试依赖
pip install pytest pytest-cov pytest-asyncio

# 运行所有测试
pytest

# 查看覆盖率
pytest --cov=. --cov-report=html

# 运行特定测试
pytest tests/test_github_service.py
```

## 贡献

我们欢迎各种形式的贡献！请查看 [CONTRIBUTING.md](CONTRIBUTING.md) 了解：

- 如何报告 Bug
- 如何提出新功能
- 如何提交 Pull Request
- 代码规范和开发流程

## 项目状态

- **当前版本**：2.1.0
- **开发状态**：活跃开发中
- **API 稳定性**：Beta

## 许可证

本项目采用 [MIT License](LICENSE) 许可证。

## 作者

- 项目维护者：openSourseTeam
- 贡献者：查看 [Contributors](https://github.com/openSourseTeam/backend/graphs/contributors)

## 致谢

- [FastAPI](https://fastapi.tiangolo.com/) - 优秀的 Web 框架
- [DeepSeek](https://platform.deepseek.com/) - AI 分析能力支持
- [textstat](https://github.com/shivam5992/textstat) - 可读性分析工具
- 所有贡献者和支持者

## 联系方式

- Issues: [GitHub Issues](https://github.com/openSourseTeam/backend/issues)
- Discussions: [GitHub Discussions](https://github.com/openSourseTeam/backend/discussions)

## 路线图

### v2.2.0 (计划中)
- [ ] 支持更多文档类型（ROADMAP、FAQ）
- [ ] 添加文档模板生成功能
- [ ] 支持多语言文档分析

### v3.0.0 (未来)
- [ ] 图表和图片分析
- [ ] PDF 文档支持
- [ ] WebSocket 实时分析进度
- [ ] 自定义规则配置
- [ ] 文档评分排行榜

---

<div align="center">

如果这个项目对你有帮助，欢迎给项目加星支持。

</div>
