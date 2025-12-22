# Changelog

本文档记录项目的所有重要更改。

格式基于 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.0.0/)，
版本号遵循 [语义化版本](https://semver.org/lang/zh-CN/)。

## [2.1.0] - 2025-12-22

### 新增

- 批量优化文档功能 (`/api/batch-optimize`)
  - 支持同时优化多个文档
  - 生成 HTML 格式的差异对比
  - 精确统计添加/删除/修改的行数
  - 提供详细的变化摘要

- 完善项目文档
  - 添加 MIT License
  - 添加 Contributing 指南
  - 添加 Code of Conduct
  - 添加 Security 政策
  - 完善 README 文档

### 改进

- 增强文档扫描功能
  - 支持扫描 12 种文档类型
  - 自动识别常见文件名变体
  - 支持 .github 和 docs 目录

- 优化分析结果展示
  - 改进规则检查输出格式
  - 增加可读性指标计算
  - 优化 AI 分析提示词

### 修复

- 修复 CORS 配置问题
- 修复文档类型识别错误
- 修复日志输出格式

## [2.0.0] - 2025-12-15

### 新增

- 选择性分析功能
  - 支持用户选择要分析的文档
  - 优化分析性能
  - 减少不必要的 API 调用

- AI 文档优化
  - 基于 DeepSeek AI 的智能优化
  - 自动修复格式和语法问题
  - 补充缺失的章节内容

### 改进

- 提升分析准确性
  - 改进规则检查算法
  - 优化可读性评分
  - 增强语义分析能力

### 破坏性变更

- API 端点重构
  - `/download-repo` 更名为 `/api/scan-repo`
  - `/check` 更名为 `/api/analyze-project`
  - 响应格式调整

## [1.0.0] - 2025-12-01

### 新增

- 初始版本发布
- GitHub 仓库文档扫描
- 文档质量规则检查
  - 链接有效性检查
  - 代码块格式检查
  - 标题结构检查
  - 章节完整性检查
  - 语法问题检查
- 可读性指标计算
  - Flesch Reading Ease
  - Gunning Fog Index
  - SMOG Index
  - 字符/单词/句子统计
- RESTful API 设计
- Swagger/ReDoc API 文档

### 技术栈

- FastAPI
- Python 3.8+
- GitHub API
- DeepSeek AI API
- textstat (可读性分析)

---

## 版本说明

### 版本号格式

版本号格式为 `主版本号.次版本号.修订号`（MAJOR.MINOR.PATCH）：

- **主版本号**：不兼容的 API 修改
- **次版本号**：向下兼容的功能性新增
- **修订号**：向下兼容的问题修正

### 变更类型

- `新增` - 新功能
- `改进` - 对现有功能的改进
- `修复` - Bug 修复
- `移除` - 移除的功能
- `废弃` - 即将移除的功能
- `安全` - 安全相关的修复
- `破坏性变更` - 不兼容的变更

---

## 未发布 (Unreleased)

### 计划中

- [ ] 支持更多文档类型（ROADMAP, FAQ 等）
- [ ] 添加文档模板生成功能
- [ ] 支持多语言文档分析
- [ ] 增加文档历史版本对比
- [ ] 提供 Docker 部署支持
- [ ] 添加 WebSocket 实时分析进度
- [ ] 集成更多 AI 模型

### 考虑中

- [ ] 图表和图片分析
- [ ] PDF 文档支持
- [ ] 自定义规则配置
- [ ] 文档评分系统
- [ ] 社区贡献的规则库

---

[2.1.0]: https://github.com/openSourseTeam/backend/compare/v2.0.0...v2.1.0
[2.0.0]: https://github.com/openSourseTeam/backend/compare/v1.0.0...v2.0.0
[1.0.0]: https://github.com/openSourseTeam/backend/releases/tag/v1.0.0

