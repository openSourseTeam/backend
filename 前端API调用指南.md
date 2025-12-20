# GitHub 文档质量分析系统 - 前端API调用指南

## 📋 目录
- [基本信息](#基本信息)
- [API端点列表](#api端点列表)
- [完整工作流程](#完整工作流程)
- [详细API说明](#详细api说明)
- [前端集成示例](#前端集成示例)
- [错误处理](#错误处理)
- [最佳实践](#最佳实践)

---

## 基本信息

**Base URL:** `http://localhost:8000`  
**Content-Type:** `application/json`  
**API版本:** `2.1.0`

### CORS配置
- ✅ 允许所有来源 (`*`)
- ✅ 支持所有HTTP方法
- ✅ 支持所有请求头

### 支持的文档类型（12种）

**核心文档（5种）：**
- `readme` - README文档
- `contributing` - 贡献指南
- `code_of_conduct` - 行为准则
- `changelog` - 更新日志
- `license` - 许可证

**扩展文档（7种）：**
- `security` - 安全政策
- `support` - 支持文档
- `wiki` - Wiki首页
- `docs` - 文档目录首页
- `installation` - 安装文档
- `usage` - 使用文档
- `api` - API文档

---

## API端点列表

| 端点 | 方法 | 功能 | 说明 |
|------|------|------|------|
| `/api/scan-repo` | POST | 扫描仓库文档 | 一次性扫描12种文档类型 |
| `/api/analyze-project` | POST | 分析文档质量 | 选择性分析，支持多选 |
| `/api/optimize-document` | POST | 优化单个文档 | 基于AI分析结果优化 |
| `/api/batch-optimize` | POST | 批量优化文档 | 批量优化+差异对比 |
| `/docs` | GET | Swagger文档 | 交互式API文档 |
| `/redoc` | GET | ReDoc文档 | 可读性更好的API文档 |

---

## 完整工作流程

```
┌─────────────────────────────────────────────────────────┐
│ 1. 用户输入仓库URL                                        │
└─────────────────┬───────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────┐
│ 2. POST /api/scan-repo                                  │
│    扫描12种文档，返回所有找到的文档                        │
└─────────────────┬───────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────┐
│ 3. 前端显示文档列表                                       │
│    [x] README.md (5.1 KB)                              │
│    [x] CONTRIBUTING.md (8.3 KB)                        │
│    [ ] LICENSE (未找到)                                 │
└─────────────────┬───────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────┐
│ 4. 用户多选要分析的文档                                   │
│    selected: ['readme', 'contributing']                 │
└─────────────────┬───────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────┐
│ 5. POST /api/analyze-project                            │
│    分析选中的文档，返回评分和问题                          │
└─────────────────┬───────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────┐
│ 6. 前端显示分析结果                                       │
│    - 每个文档的原文和评分                                 │
│    - 规则检查结果                                         │
│    - AI分析建议                                           │
└─────────────────┬───────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────┐
│ 7. 用户点击"优化文档"                                     │
└─────────────────┬───────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────┐
│ 8. POST /api/batch-optimize                             │
│    批量优化选中的文档                                     │
└─────────────────┬───────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────┐
│ 9. 前端显示优化结果                                       │
│    - 优化后的文档内容                                     │
│    - HTML差异对比（高亮显示变化）                          │
│    - 统计信息（添加/删除/修改行数）                       │
└─────────────────────────────────────────────────────────┘
```

---

## 详细API说明

### 1. 扫描仓库文档

#### `POST /api/scan-repo`

**功能：** 一次性扫描仓库的所有12种文档类型

**请求参数：**
```typescript
{
  repo_url: string  // GitHub仓库URL
}
```

**支持的URL格式：**
- `https://github.com/username/reponame`
- `github.com/username/reponame`
- `username/reponame`

**请求示例：**
```javascript
const response = await fetch('http://localhost:8000/api/scan-repo', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    repo_url: 'facebook/react'
  })
});

const data = await response.json();
```

**成功响应 (200)：**
```json
{
  "success": true,
  "repo_info": {
    "owner": "facebook",
    "repo": "react",
    "full_name": "facebook/react"
  },
  "docs": {
    "readme": {
      "content": "# React\n\n...",
      "filename": "README.md",
      "download_url": "https://raw.githubusercontent.com/...",
      "html_url": "https://github.com/...",
      "size": 5234
    },
    "contributing": {
      "content": "# Contributing\n\n...",
      "filename": "CONTRIBUTING.md",
      "size": 8456
    },
    "code_of_conduct": null,  // 未找到
    "changelog": null,
    "license": {
      "content": "MIT License\n\n...",
      "filename": "LICENSE",
      "size": 1234
    },
    "security": null,
    "support": null,
    "wiki": null,
    "docs": {
      "content": "# Documentation\n\n...",
      "filename": "docs/README.md",
      "size": 4567
    },
    "installation": null,
    "usage": null,
    "api": null
  },
  "stats": {
    "total_types": 12,
    "found_count": 4,
    "found_percentage": 33.3
  }
}
```

**错误响应：**
```json
{
  "detail": "无效的GitHub仓库URL"
}
```

**前端处理示例：**
```javascript
// 获取所有找到的文档
const availableDocs = Object.entries(data.docs)
  .filter(([key, value]) => value !== null)
  .map(([type, info]) => ({
    type: type,
    filename: info.filename,
    size: info.size,
    content: info.content
  }));

console.log(`找到 ${availableDocs.length}/12 个文档`);
// 输出: 找到 4/12 个文档
```

---

### 2. 分析项目文档

#### `POST /api/analyze-project`

**功能：** 对选定的文档进行质量分析（规则检查 + AI语义分析）

**请求参数：**
```typescript
{
  docs: {
    [doc_type: string]: {
      content: string,
      filename: string,
      size?: number,
      download_url?: string,
      html_url?: string
    } | null
  },
  selected_doc_types: string[]  // 要分析的文档类型列表
}
```

**请求示例：**
```javascript
// 从 scan-repo 获取的文档
const scanData = await fetch('/api/scan-repo', {
  method: 'POST',
  body: JSON.stringify({ repo_url: 'facebook/react' })
}).then(r => r.json());

// 用户选择了 readme 和 contributing
const selectedTypes = ['readme', 'contributing'];

// 分析选中的文档
const analyzeResponse = await fetch('/api/analyze-project', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    docs: scanData.docs,
    selected_doc_types: selectedTypes
  })
});

const analyzeData = await analyzeResponse.json();
```

**成功响应 (200)：**
```json
{
  "success": true,
  "selected_doc_types": ["readme", "contributing"],
  "rule_checks": {
    "readme": {
      "link_check": {
        "total_links": 15,
        "valid_links": 14,
        "invalid_links": 1,
        "invalid_links_list": [
          {
            "text": "失效链接",
            "url": "https://invalid-url.com",
            "status": "invalid",
            "status_code": 404
          }
        ],
        "check_passed": false
      },
      "code_block_check": {
        "total_code_blocks": 8,
        "blocks_with_language": 8,
        "blocks_without_language": 0,
        "check_passed": true
      },
      "heading_structure_check": {
        "total_headings": 12,
        "issues": [],
        "check_passed": true
      },
      "section_completeness_check": {
        "doc_type": "readme",
        "total_required_sections": 4,
        "found_sections": 4,
        "missing_sections": [],
        "check_passed": true
      },
      "markdown_syntax_check": {
        "parse_success": true,
        "total_issues": 0,
        "total_warnings": 0,
        "check_passed": true
      },
      "summary": {
        "total_checks": 5,
        "passed_checks": 4,
        "failed_checks": 1,
        "total_issues": 1,
        "overall_passed": false
      }
    },
    "contributing": {
      "summary": {
        "total_checks": 5,
        "passed_checks": 3,
        "failed_checks": 2,
        "total_issues": 3
      }
    }
  },
  "ai_analysis": {
    "overall_score": 85,
    "dimension_scores": {
      "completeness": 90,
      "clarity": 85,
      "usability": 80,
      "convention": 88,
      "beginner_friendly": 82,
      "code_quality": 85
    },
    "strengths": [
      "README内容完整，结构清晰",
      "代码示例丰富且规范",
      "包含详细的贡献指南"
    ],
    "missing_sections": [
      "缺少故障排除章节"
    ],
    "suggestions": [
      "补充常见问题FAQ",
      "添加性能优化建议"
    ],
    "priority_recommendations": [
      "修复失效的外部链接",
      "添加故障排除指南",
      "完善配置说明"
    ],
    "beginner_confusion_points": [
      "安装步骤中环境变量配置不够详细"
    ],
    "code_quality_issues": [],
    "structural_issues": [],
    "language_issues": [],
    "convention_issues": [
      "部分代码块缺少语言标识"
    ]
  }
}
```

**前端展示示例：**
```javascript
// 显示每个文档的评分
analyzeData.selected_doc_types.forEach(docType => {
  const ruleCheck = analyzeData.rule_checks[docType];
  const summary = ruleCheck.summary;
  
  console.log(`\n${docType.toUpperCase()}:`);
  console.log(`  规则检查: ${summary.passed_checks}/${summary.total_checks} 通过`);
  console.log(`  问题数: ${summary.total_issues}`);
});

// 显示整体AI评分
console.log(`\n整体AI评分: ${analyzeData.ai_analysis.overall_score}/100`);
console.log(`改进建议:`, analyzeData.ai_analysis.priority_recommendations);
```

---

### 3. 优化单个文档

#### `POST /api/optimize-document`

**功能：** 基于AI分析结果优化单个文档

**请求参数：**
```typescript
{
  original_content: string,      // 原始文档内容
  analysis_result: object,        // AI分析结果（从 analyze-project 获取）
  doc_type: string              // 文档类型，默认 "readme"
}
```

**请求示例：**
```javascript
const optimizeResponse = await fetch('/api/optimize-document', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    original_content: scanData.docs.readme.content,
    analysis_result: analyzeData.ai_analysis,
    doc_type: 'readme'
  })
});

const optimizeData = await optimizeResponse.json();
```

**成功响应 (200)：**
```json
{
  "success": true,
  "original_content": "# My Project\n\n...",
  "optimized_content": "# My Project\n\n## 项目简介\n\n...",
  "changes_summary": {
    "original_length": 500,
    "optimized_length": 2000,
    "length_change": 1500,
    "original_lines": 20,
    "optimized_lines": 80
  }
}
```

---

### 4. 批量优化文档 ⭐

#### `POST /api/batch-optimize`

**功能：** 批量优化多个文档并生成HTML差异对比

**请求参数：**
```typescript
{
  documents: [
    {
      doc_type: string,
      original_content: string,
      analysis_result: object
    },
    ...
  ]
}
```

**请求示例：**
```javascript
// 构建批量优化请求
const documentsToOptimize = selectedTypes.map(docType => ({
  doc_type: docType,
  original_content: scanData.docs[docType].content,
  analysis_result: analyzeData.ai_analysis
}));

// 批量优化
const batchResponse = await fetch('/api/batch-optimize', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    documents: documentsToOptimize
  }),
  timeout: 300000  // 5分钟超时（批量优化可能需要较长时间）
});

const batchData = await batchResponse.json();
```

**成功响应 (200)：**
```json
{
  "success": true,
  "results": [
    {
      "doc_type": "readme",
      "success": true,
      "original_content": "# My Project\n\n...",
      "optimized_content": "# My Project\n\n## 项目简介\n\n...",
      "changes_summary": {
        "original_length": 500,
        "optimized_length": 2000,
        "length_change": 1500,
        "additions": 45,
        "deletions": 3,
        "modifications": 3
      }
    },
    {
      "doc_type": "contributing",
      "success": true,
      ...
    }
  ],
  "diffs": [
    {
      "doc_type": "readme",
      "original_content": "...",
      "optimized_content": "...",
      "diff_html": "<table class='diff'>...</table>",
      "additions": 45,
      "deletions": 3,
      "modifications": 3
    },
    ...
  ]
}
```

**差异HTML说明：**
- `diff_html` 是完整的HTML表格，包含：
  - ✅ 绿色背景：新增的行
  - ❌ 红色背景：删除的行
  - 🟡 黄色背景：修改的行
  - 并排对比：左边原始，右边优化后

**前端使用示例：**
```javascript
// 显示优化结果
batchData.results.forEach(result => {
  if (result.success) {
    console.log(`\n${result.doc_type.toUpperCase()}:`);
    console.log(`  原始: ${result.changes_summary.original_length} 字符`);
    console.log(`  优化后: ${result.changes_summary.optimized_length} 字符`);
    console.log(`  变化: ${result.changes_summary.length_change:+d} 字符`);
    console.log(`  添加: ${result.changes_summary.additions} 行`);
    console.log(`  删除: ${result.changes_summary.deletions} 行`);
  }
});

// 显示差异对比（插入到页面）
batchData.diffs.forEach(diff => {
  const container = document.getElementById(`diff-${diff.doc_type}`);
  if (container) {
    container.innerHTML = diff.diff_html;
  }
});
```

---

## 前端集成示例

### React完整示例

```jsx
import React, { useState } from 'react';

function DocumentAnalyzer() {
  const [repoUrl, setRepoUrl] = useState('');
  const [scanData, setScanData] = useState(null);
  const [selectedDocs, setSelectedDocs] = useState([]);
  const [analysisData, setAnalysisData] = useState(null);
  const [optimizeData, setOptimizeData] = useState(null);
  const [loading, setLoading] = useState(false);

  const BASE_URL = 'http://localhost:8000';

  // 步骤1: 扫描仓库
  const handleScan = async () => {
    setLoading(true);
    try {
      const response = await fetch(`${BASE_URL}/api/scan-repo`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ repo_url: repoUrl })
      });
      
      if (!response.ok) throw new Error('扫描失败');
      
      const data = await response.json();
      setScanData(data);
      setSelectedDocs([]); // 重置选择
    } catch (error) {
      alert('扫描失败: ' + error.message);
    } finally {
      setLoading(false);
    }
  };

  // 步骤2: 分析选中的文档
  const handleAnalyze = async () => {
    if (selectedDocs.length === 0) {
      alert('请至少选择一个文档');
      return;
    }

    setLoading(true);
    try {
      const response = await fetch(`${BASE_URL}/api/analyze-project`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          docs: scanData.docs,
          selected_doc_types: selectedDocs
        })
      });
      
      if (!response.ok) throw new Error('分析失败');
      
      const data = await response.json();
      setAnalysisData(data);
    } catch (error) {
      alert('分析失败: ' + error.message);
    } finally {
      setLoading(false);
    }
  };

  // 步骤3: 批量优化
  const handleOptimize = async () => {
    setLoading(true);
    try {
      const documents = selectedDocs.map(docType => ({
        doc_type: docType,
        original_content: scanData.docs[docType].content,
        analysis_result: analysisData.ai_analysis
      }));

      const response = await fetch(`${BASE_URL}/api/batch-optimize`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ documents }),
        signal: AbortSignal.timeout(300000) // 5分钟超时
      });
      
      if (!response.ok) throw new Error('优化失败');
      
      const data = await response.json();
      setOptimizeData(data);
    } catch (error) {
      alert('优化失败: ' + error.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="document-analyzer">
      {/* 输入区域 */}
      <div className="input-section">
        <input
          type="text"
          value={repoUrl}
          onChange={(e) => setRepoUrl(e.target.value)}
          placeholder="输入GitHub仓库URL，如: facebook/react"
        />
        <button onClick={handleScan} disabled={loading || !repoUrl}>
          {loading ? '扫描中...' : '扫描仓库'}
        </button>
      </div>

      {/* 文档列表 */}
      {scanData && (
        <div className="docs-list">
          <h3>找到的文档 ({scanData.stats.found_count}/12)</h3>
          {Object.entries(scanData.docs).map(([type, info]) => (
            <label key={type}>
              <input
                type="checkbox"
                checked={selectedDocs.includes(type)}
                onChange={(e) => {
                  if (e.target.checked) {
                    setSelectedDocs([...selectedDocs, type]);
                  } else {
                    setSelectedDocs(selectedDocs.filter(t => t !== type));
                  }
                }}
                disabled={!info}
              />
              {info ? (
                <span>{info.filename} ({(info.size / 1024).toFixed(1)} KB)</span>
              ) : (
                <span className="not-found">{type} (未找到)</span>
              )}
            </label>
          ))}
          <button onClick={handleAnalyze} disabled={loading || selectedDocs.length === 0}>
            分析选中的文档
          </button>
        </div>
      )}

      {/* 分析结果 */}
      {analysisData && (
        <div className="analysis-results">
          <h3>分析结果</h3>
          <div className="overall-score">
            整体评分: {analysisData.ai_analysis.overall_score}/100
          </div>
          
          {analysisData.selected_doc_types.map(docType => {
            const ruleCheck = analysisData.rule_checks[docType];
            const summary = ruleCheck.summary;
            
            return (
              <div key={docType} className="doc-result">
                <h4>{docType.toUpperCase()}</h4>
                <p>规则检查: {summary.passed_checks}/{summary.total_checks} 通过</p>
                <p>问题数: {summary.total_issues}</p>
                
                {/* 显示原文 */}
                <details>
                  <summary>查看原文</summary>
                  <pre>{scanData.docs[docType].content}</pre>
                </details>
              </div>
            );
          })}
          
          <div className="recommendations">
            <h4>改进建议</h4>
            <ul>
              {analysisData.ai_analysis.priority_recommendations.map((rec, i) => (
                <li key={i}>{rec}</li>
              ))}
            </ul>
          </div>
          
          <button onClick={handleOptimize} disabled={loading}>
            优化文档
          </button>
        </div>
      )}

      {/* 优化结果 */}
      {optimizeData && (
        <div className="optimize-results">
          <h3>优化结果</h3>
          {optimizeData.diffs.map(diff => (
            <div key={diff.doc_type} className="diff-container">
              <h4>{diff.doc_type.toUpperCase()}</h4>
              <div className="stats">
                添加: {diff.additions} 行 | 
                删除: {diff.deletions} 行 | 
                修改: {diff.modifications} 行
              </div>
              
              {/* 显示差异对比 */}
              <div 
                className="diff-view"
                dangerouslySetInnerHTML={{ __html: diff.diff_html }}
              />
              
              {/* 下载优化后的文档 */}
              <button onClick={() => {
                const blob = new Blob([diff.optimized_content], { type: 'text/markdown' });
                const url = URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `optimized_${diff.doc_type}.md`;
                a.click();
              }}>
                下载优化后的文档
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export default DocumentAnalyzer;
```

### Vue完整示例

```vue
<template>
  <div class="document-analyzer">
    <!-- 输入区域 -->
    <div class="input-section">
      <input 
        v-model="repoUrl" 
        placeholder="输入GitHub仓库URL"
        @keyup.enter="handleScan"
      />
      <button @click="handleScan" :disabled="loading || !repoUrl">
        {{ loading ? '扫描中...' : '扫描仓库' }}
      </button>
    </div>

    <!-- 文档列表 -->
    <div v-if="scanData" class="docs-list">
      <h3>找到的文档 ({{ scanData.stats.found_count }}/12)</h3>
      <div v-for="(info, type) in scanData.docs" :key="type" class="doc-item">
        <label>
          <input
            type="checkbox"
            :checked="selectedDocs.includes(type)"
            @change="toggleDoc(type, $event.target.checked)"
            :disabled="!info"
          />
          <span v-if="info">
            {{ info.filename }} ({{ (info.size / 1024).toFixed(1) }} KB)
          </span>
          <span v-else class="not-found">{{ type }} (未找到)</span>
        </label>
      </div>
      <button @click="handleAnalyze" :disabled="loading || selectedDocs.length === 0">
        分析选中的文档
      </button>
    </div>

    <!-- 分析结果 -->
    <div v-if="analysisData" class="analysis-results">
      <h3>分析结果</h3>
      <div class="overall-score">
        整体评分: {{ analysisData.ai_analysis.overall_score }}/100
      </div>
      
      <div v-for="docType in analysisData.selected_doc_types" :key="docType" class="doc-result">
        <h4>{{ docType.toUpperCase() }}</h4>
        <p>规则检查: {{ analysisData.rule_checks[docType].summary.passed_checks }}/{{ analysisData.rule_checks[docType].summary.total_checks }} 通过</p>
      </div>
      
      <button @click="handleOptimize" :disabled="loading">
        优化文档
      </button>
    </div>

    <!-- 优化结果 -->
    <div v-if="optimizeData" class="optimize-results">
      <h3>优化结果</h3>
      <div v-for="diff in optimizeData.diffs" :key="diff.doc_type" class="diff-container">
        <h4>{{ diff.doc_type.toUpperCase() }}</h4>
        <div class="stats">
          添加: {{ diff.additions }} 行 | 
          删除: {{ diff.deletions }} 行 | 
          修改: {{ diff.modifications }} 行
        </div>
        <div class="diff-view" v-html="diff.diff_html"></div>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  data() {
    return {
      repoUrl: '',
      scanData: null,
      selectedDocs: [],
      analysisData: null,
      optimizeData: null,
      loading: false,
      BASE_URL: 'http://localhost:8000'
    };
  },
  methods: {
    async handleScan() {
      this.loading = true;
      try {
        const response = await fetch(`${this.BASE_URL}/api/scan-repo`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ repo_url: this.repoUrl })
        });
        
        if (!response.ok) throw new Error('扫描失败');
        this.scanData = await response.json();
        this.selectedDocs = [];
      } catch (error) {
        alert('扫描失败: ' + error.message);
      } finally {
        this.loading = false;
      }
    },
    
    toggleDoc(type, checked) {
      if (checked) {
        this.selectedDocs.push(type);
      } else {
        this.selectedDocs = this.selectedDocs.filter(t => t !== type);
      }
    },
    
    async handleAnalyze() {
      if (this.selectedDocs.length === 0) {
        alert('请至少选择一个文档');
        return;
      }
      
      this.loading = true;
      try {
        const response = await fetch(`${this.BASE_URL}/api/analyze-project`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            docs: this.scanData.docs,
            selected_doc_types: this.selectedDocs
          })
        });
        
        if (!response.ok) throw new Error('分析失败');
        this.analysisData = await response.json();
      } catch (error) {
        alert('分析失败: ' + error.message);
      } finally {
        this.loading = false;
      }
    },
    
    async handleOptimize() {
      this.loading = true;
      try {
        const documents = this.selectedDocs.map(docType => ({
          doc_type: docType,
          original_content: this.scanData.docs[docType].content,
          analysis_result: this.analysisData.ai_analysis
        }));

        const response = await fetch(`${this.BASE_URL}/api/batch-optimize`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ documents })
        });
        
        if (!response.ok) throw new Error('优化失败');
        this.optimizeData = await response.json();
      } catch (error) {
        alert('优化失败: ' + error.message);
      } finally {
        this.loading = false;
      }
    }
  }
};
</script>
```

---

## 错误处理

### 常见错误代码

| 状态码 | 说明 | 处理方式 |
|-------|------|---------|
| 400 | 请求参数错误 | 检查请求参数格式 |
| 404 | 资源未找到 | 检查仓库URL或文档是否存在 |
| 500 | 服务器内部错误 | 查看错误详情，可能是API限制或网络问题 |

### 错误响应格式

```json
{
  "detail": "错误信息描述"
}
```

### 统一错误处理函数

```javascript
async function apiCall(url, options) {
  try {
    const response = await fetch(url, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...options.headers
      }
    });
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || `HTTP ${response.status}`);
    }
    
    return await response.json();
    
  } catch (error) {
    // 用户友好的错误提示
    if (error.message.includes('无效的GitHub仓库URL')) {
      alert('请输入正确的GitHub仓库地址，格式如: facebook/react');
    } else if (error.message.includes('未找到')) {
      alert('该仓库不存在或文档缺失');
    } else if (error.message.includes('超时')) {
      alert('请求超时，请稍后重试');
    } else {
      alert('操作失败: ' + error.message);
    }
    throw error;
  }
}

// 使用示例
const scanData = await apiCall('/api/scan-repo', {
  method: 'POST',
  body: JSON.stringify({ repo_url: 'facebook/react' })
});
```

---

## 最佳实践

### 1. 性能优化

#### 使用防抖
```javascript
import { debounce } from 'lodash';

// 用户输入时防抖
const debouncedScan = debounce(handleScan, 500);
```

#### 显示进度
```javascript
// 批量优化可能需要较长时间，显示进度
const handleOptimize = async () => {
  setProgress(0);
  
  // 模拟进度更新
  const progressInterval = setInterval(() => {
    setProgress(prev => Math.min(prev + 10, 90));
  }, 1000);
  
  try {
    await fetch('/api/batch-optimize', { ... });
    setProgress(100);
  } finally {
    clearInterval(progressInterval);
  }
};
```

#### 缓存结果
```javascript
// 缓存扫描结果，避免重复请求
const cache = new Map();

const handleScan = async (repoUrl) => {
  if (cache.has(repoUrl)) {
    return cache.get(repoUrl);
  }
  
  const data = await fetch('/api/scan-repo', { ... });
  cache.set(repoUrl, data);
  return data;
};
```

### 2. 用户体验

#### 加载状态
```javascript
const [loading, setLoading] = useState(false);
const [loadingText, setLoadingText] = useState('');

// 不同阶段显示不同提示
setLoadingText('正在扫描仓库...');
await handleScan();
setLoadingText('正在分析文档...');
await handleAnalyze();
setLoadingText('正在优化文档...');
await handleOptimize();
```

#### 结果展示
```javascript
// 使用图表展示评分
import { Chart } from 'chart.js';

// 展示各维度评分
const scores = analysisData.ai_analysis.dimension_scores;
const chart = new Chart(ctx, {
  type: 'radar',
  data: {
    labels: Object.keys(scores),
    datasets: [{
      data: Object.values(scores)
    }]
  }
});
```

#### 差异对比优化
```javascript
// 添加样式优化差异对比显示
<style>
.diff-view {
  max-height: 600px;
  overflow-y: auto;
  border: 1px solid #ddd;
  padding: 10px;
}

.diff-view table {
  width: 100%;
  border-collapse: collapse;
}

.diff-view .diff_add {
  background-color: #d4edda;
}

.diff-view .diff_sub {
  background-color: #f8d7da;
}

.diff-view .diff_chg {
  background-color: #fff3cd;
}
</style>
```

### 3. 数据管理

#### 状态管理（Redux示例）
```javascript
// actions.js
export const scanRepo = (repoUrl) => async (dispatch) => {
  dispatch({ type: 'SCAN_START' });
  try {
    const data = await fetch('/api/scan-repo', {
      method: 'POST',
      body: JSON.stringify({ repo_url: repoUrl })
    }).then(r => r.json());
    
    dispatch({ type: 'SCAN_SUCCESS', payload: data });
  } catch (error) {
    dispatch({ type: 'SCAN_ERROR', payload: error.message });
  }
};
```

---

## 完整工作流代码示例

```javascript
// 完整的异步工作流
async function analyzeAndOptimizeRepo(repoUrl) {
  const BASE_URL = 'http://localhost:8000';
  
  try {
    // 步骤1: 扫描
    console.log('📥 扫描仓库...');
    const scanData = await fetch(`${BASE_URL}/api/scan-repo`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ repo_url: repoUrl })
    }).then(r => r.json());
    
    console.log(`✅ 找到 ${scanData.stats.found_count}/12 个文档`);
    
    // 步骤2: 用户选择（这里假设选择所有找到的文档）
    const selectedTypes = Object.keys(scanData.docs)
      .filter(type => scanData.docs[type] !== null);
    
    console.log(`👆 选择文档: ${selectedTypes.join(', ')}`);
    
    // 步骤3: 分析
    console.log('🔍 分析文档...');
    const analysisData = await fetch(`${BASE_URL}/api/analyze-project`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        docs: scanData.docs,
        selected_doc_types: selectedTypes
      })
    }).then(r => r.json());
    
    console.log(`✅ 分析完成，评分: ${analysisData.ai_analysis.overall_score}/100`);
    
    // 步骤4: 优化（如果评分低）
    if (analysisData.ai_analysis.overall_score < 80) {
      console.log('📝 开始优化...');
      
      const documents = selectedTypes.map(type => ({
        doc_type: type,
        original_content: scanData.docs[type].content,
        analysis_result: analysisData.ai_analysis
      }));
      
      const optimizeData = await fetch(`${BASE_URL}/api/batch-optimize`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ documents })
      }).then(r => r.json());
      
      console.log('✅ 优化完成');
      
      // 保存差异HTML
      optimizeData.diffs.forEach(diff => {
        const blob = new Blob([diff.diff_html], { type: 'text/html' });
        const url = URL.createObjectURL(blob);
        console.log(`差异对比: ${diff.doc_type} - ${url}`);
      });
      
      return { scanData, analysisData, optimizeData };
    }
    
    return { scanData, analysisData };
    
  } catch (error) {
    console.error('❌ 处理失败:', error);
    throw error;
  }
}

// 使用
analyzeAndOptimizeRepo('facebook/react')
  .then(result => {
    console.log('🎉 处理完成！', result);
  })
  .catch(err => {
    console.error('处理失败:', err);
  });
```

---

## 总结

### API端点速查

| 端点 | 用途 | 关键参数 |
|------|------|---------|
| `/api/scan-repo` | 扫描12种文档 | `repo_url` |
| `/api/analyze-project` | 选择性分析 | `docs`, `selected_doc_types` |
| `/api/optimize-document` | 单个优化 | `original_content`, `analysis_result`, `doc_type` |
| `/api/batch-optimize` | 批量优化+差异 | `documents` |

### 工作流程

```
扫描 → 选择 → 分析 → 优化 → 对比
```

### 关键提示

1. ⚠️ **批量优化可能需要较长时间**（每个文档10-30秒），建议设置超时和进度提示
2. ✅ **差异HTML可直接插入页面**，已包含完整样式
3. 📊 **统计信息精确**，包括添加/删除/修改的行数
4. 🎯 **选择性分析**，只分析用户勾选的文档，节省时间和资源

---

**文档版本:** v2.1.0  
**最后更新:** 2025-12-20  
**维护者:** Backend Team

