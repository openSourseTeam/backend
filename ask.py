import openai
import json



system_prompt = '''
你是一名资深的开源项目维护者和技术文档工程师，专注于评估开源项目文档的整体质量。请严格按照指定的JSON格式输出评估结果，不要添加任何额外的解释或标记。

评估维度：
1. 完整性 - 评估必要文档（README, CONTRIBUTING, CODE_OF_CONDUCT等）是否齐全，内容是否完整
2. 清晰度 - 评估语言表达是否清晰易懂，逻辑是否顺畅
3. 实用性 - 评估用户能否根据文档快速上手使用项目，以及开发者能否顺利参与贡献
4. 规范性 - 评估格式排版、链接有效性、代码示例等规范性

输出必须是纯JSON格式，包含以下字段：
- overall_score: 总体评分（0-100）
- dimension_scores: 各维度评分（0-100）
- strengths: 项目文档的整体优点列表
- missing_sections: 缺失的必要文档或章节列表
- suggestions: 具体的改进建议列表
- convention_issues: 规范性问题和格式错误列表
- beginner_confusion_points: 新手（用户或贡献者）最可能困惑的地方
- code_quality_issues: 代码示例质量问题列表
- structural_issues: 信息组织结构问题列表
- language_issues: 语言表达问题列表
- priority_recommendations: 优先级改进建议列表（按重要性排序）

请基于提供的项目文档内容（可能包含README, CONTRIBUTING等多个文件）进行客观、专业的评估。

请勿在最终输出中添加任何解释。您的输出必须遵循以下格式:

**EXAMPLE**

```json
{
  "overall_score": 78,
  "dimension_scores": {
    "completeness": 70,
    "clarity": 85,
    "usability": 75,
    "convention": 80,
    "beginner_friendly": 65,
    "code_quality": 70
  },
  "strengths": [
    "README简介清晰，准确描述了核心价值",
    "包含详细的CONTRIBUTING指南，对贡献者友好",
    "安装步骤基本可行"
  ],
  "missing_sections": [
    "缺少CODE_OF_CONDUCT文档",
    "README中缺少详细的配置说明",
    "CONTRIBUTING中未说明如何运行测试"
  ],
  "beginner_confusion_points": [
    "安装步骤中提到的'环境变量配置'未说明具体方法",
    "贡献指南未说明分支命名规范"
  ],
  "code_quality_issues": [
    "示例代码中硬编码了API密钥",
    "缺少必要的错误处理代码"
  ],
  "structural_issues": [
    "安装步骤与配置说明分散在不同章节",
    "贡献指南与README部分内容重复"
  ],
  "language_issues": [
    "技术术语使用不够准确",
    "存在拼写错误"
  ],
  "priority_recommendations": [
    "添加CODE_OF_CONDUCT文档以完善社区规范",
    "完善CONTRIBUTING文档，补充测试运行说明",
    "修复代码示例中的安全风险"
  ],
  "suggestions": [
    "添加配置文件的详细说明",
    "增加故障排除章节",
    "统一术语使用"
  ],
  "convention_issues": [
    "部分标题层级使用不当",
    "代码块缺少语言标识"
  ]
}
```
'''.strip()

user_prompt = '''
请对以下开源项目的文档集合进行全面质量评估：

{docs_content}

初步调用的规则检查结果（仅供参考）：
{rule_checks}

请从以下维度进行深入分析：

1. 【基础完整性检查】
判断核心文档（README, CONTRIBUTING, CODE_OF_CONDUCT, LICENSE, CHANGELOG）是否齐全，核心章节是否缺失。

2. 【新手可用性评估】
从新手用户和新手贡献者的角度出发：
- 仅凭文档是否能成功安装和运行？
- 是否清楚如何提交第一个PR？
- 识别困惑点。

3. 【代码示例质量检查】
检查所有文档中的代码示例：
- 是否完整可运行？
- 是否存在安全风险？

4. 【信息组织结构评估】
评估整体架构：
- 文档间链接是否通畅？
- 逻辑流程是否清晰？

5. 【语言表达质量检查】
检查表达是否准确、友好、简洁。

6. 【优先级改进建议】
提供3-5个最优先的改进建议。

请确保评估客观、具体。
'''.strip()




def analyze_readme_with_llm(markdown_content, readability, api_key):
    print(f"正在调用 LLM API... 文档长度: {len(markdown_content)}")
    client = openai.OpenAI(api_key=api_key, base_url="https://api.deepseek.com")
    
    try:
        response = client.chat.completions.create(
            model="deepseek-chat",  # 或 "gpt-3.5-turbo"
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt.format(docs_content=markdown_content, rule_checks=json.dumps(readability))}
            ],
            response_format={"type": "json_object"},  # 强制JSON输出
            timeout=120  # 设置超时时间为 120 秒
        )
        print("LLM API 调用成功，正在解析结果...")
        # 解析响应
        result_json = json.loads(response.choices[0].message.content)
        result_json.update({"readability": readability})
        # print(result_json) # 避免打印过大的 JSON
        return result_json
        
    except Exception as e:
        print(f"LLM API 调用出错: {e}")
        return {"error": f"API调用失败: {str(e)}"}

if __name__ == "__main__":
  api_key = 'sk-99ed7f2e56bd478cb3147fd1593d4157'
  cleaned_markdown_text = "# Sample README\n\nThis is a sample README file for testing purposes.\n\n## Installation\n\nTo install, run:\n\n```bash\npip install sample-package\n```\n\n## Usage\n\nTo use the package, import it in your Python script:\n\n```python\nimport sample_package\n```"
  readability = {"score": 80, "issues": []}
  result = analyze_readme_with_llm(cleaned_markdown_text, readability, api_key)

  print(result)