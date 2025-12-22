# Security Policy

## 安全政策

感谢您帮助我们保持 GitHub 文档质量分析系统的安全。

## 支持的版本

我们目前为以下版本提供安全更新：

| 版本 | 支持状态 |
| --- | --- |
| 2.1.x | 支持 |
| 2.0.x | 支持 |
| < 2.0 | 不支持 |

## 报告安全漏洞

如果您发现安全漏洞，请**不要**通过公开的 Issue 报告。

### 报告流程

1. **私密报告**
   
   请通过以下方式之一私密地报告安全问题：
   
   - 使用 GitHub Security Advisories（推荐）
     - 前往：https://github.com/openSourseTeam/backend/security/advisories/new
   - 或通过 GitHub Issues 报告（请标记为 Security 相关）

2. **包含信息**
   
   请在报告中包含以下信息：
   
   - 漏洞类型（如：SQL 注入、XSS、CSRF 等）
   - 受影响的文件或组件
   - 漏洞位置（行号、函数名等）
   - 复现步骤（越详细越好）
   - 潜在影响
   - 可能的修复建议（如果有）

3. **响应时间**
   
   - 我们会在 **48 小时内**确认收到报告
   - 在 **7 天内**提供初步评估
   - 根据严重程度，在 **30-90 天内**发布修复

4. **披露政策**
   
   - 我们采用**协调披露**政策
   - 在修复发布后，我们会公开披露漏洞详情
   - 如果您同意，我们会在安全公告中致谢

## 安全最佳实践

### 对于用户

1. **API 密钥管理**
   
   - 不要在代码中硬编码 API 密钥
   - 使用环境变量或密钥管理服务
   - 定期轮换 API 密钥
   - 限制 API 密钥的权限范围

   ```python
   # 不推荐
   api_key = 'sk-xxxxxxxxxxxxx'
   
   # 推荐
   import os
   api_key = os.getenv('DEEPSEEK_API_KEY')
   ```

2. **CORS 配置**
   
   生产环境应限制 CORS 来源：
   
   ```python
   # 不推荐（生产环境）
   allow_origins=["*"]
   
   # 推荐
   allow_origins=["https://yourdomain.com"]
   ```

3. **依赖更新**
   
   - 定期更新依赖包
   - 使用 `pip list --outdated` 检查过期包
   - 订阅安全公告

4. **日志安全**
   
   - 不要在日志中记录敏感信息
   - 定期清理日志文件
   - 限制日志文件访问权限

### 对于开发者

1. **输入验证**
   
   - 验证所有用户输入
   - 使用 Pydantic 模型进行数据验证
   - 防止 SQL 注入和 XSS 攻击

2. **错误处理**
   
   - 不要在错误信息中暴露敏感信息
   - 使用通用错误消息对外
   - 详细错误记录在日志中

3. **认证与授权**
   
   - 实施适当的认证机制
   - 使用 HTTPS
   - 实施速率限制

4. **代码审查**
   
   - 所有代码变更需经过审查
   - 使用静态代码分析工具
   - 定期进行安全审计

## 已知安全注意事项

### 当前版本的安全考虑

1. **硬编码 API 密钥**
   
   当前版本在代码中包含硬编码的 API 密钥。这仅适用于开发环境。
   
   生产环境修复方案：
   ```python
   # main.py
   import os
   api_key = os.getenv('DEEPSEEK_API_KEY')
   if not api_key:
       raise ValueError("DEEPSEEK_API_KEY environment variable not set")
   ```

2. **CORS 允许所有来源**
   
   当前配置允许所有来源的跨域请求。
   
   生产环境修复方案：
   ```python
   app.add_middleware(
       CORSMiddleware,
       allow_origins=os.getenv("ALLOWED_ORIGINS", "").split(","),
       allow_credentials=True,
       allow_methods=["GET", "POST"],
       allow_headers=["*"],
   )
   ```

3. **无速率限制**
   
   当前没有实施 API 速率限制。
   
   建议添加：
   ```python
   from slowapi import Limiter, _rate_limit_exceeded_handler
   from slowapi.util import get_remote_address
   
   limiter = Limiter(key_func=get_remote_address)
   app.state.limiter = limiter
   app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
   
   @app.post("/api/scan-repo")
   @limiter.limit("10/minute")
   async def scan_repo_docs(request: Request, ...):
       ...
   ```

## 安全检查清单

在部署到生产环境前，请确保：

- [ ] 所有 API 密钥都存储在环境变量中
- [ ] CORS 配置限制了允许的来源
- [ ] 实施了 HTTPS
- [ ] 添加了速率限制
- [ ] 配置了适当的日志级别
- [ ] 更新了所有依赖包
- [ ] 进行了安全测试
- [ ] 配置了防火墙规则
- [ ] 设置了监控和告警
- [ ] 定期备份数据

## 安全更新订阅

要接收安全更新通知：

1. Star 本仓库
2. Watch → Custom → Security alerts
3. 订阅 Security Advisories

## 感谢

我们感谢以下安全研究人员的贡献：

<!-- 
此处会列出报告安全问题的研究人员（在获得许可后）

- [研究员姓名] - 报告了 [漏洞类型] (日期)
-->

## 参考资源

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [CWE Top 25](https://cwe.mitre.org/top25/)
- [Python 安全最佳实践](https://python.readthedocs.io/en/stable/library/security_warnings.html)
- [FastAPI 安全指南](https://fastapi.tiangolo.com/tutorial/security/)

---

最后更新：2025-12-22

