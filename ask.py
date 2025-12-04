import openai
import json


system_prompt = '''
你是一名资深的开源项目维护者和技术文档工程师，专注于评估开源项目文档的质量。请严格按照指定的JSON格式输出评估结果，不要添加任何额外的解释或标记。

评估维度：
1. 完整性 - 评估必要章节是否齐全，内容是否完整
2. 清晰度 - 评估语言表达是否清晰易懂，逻辑是否顺畅
3. 实用性 - 评估用户能否根据文档快速上手使用项目
4. 规范性 - 评估格式排版、链接有效性、代码示例等规范性

输出必须是纯JSON格式，包含以下字段：
- overall_score: 总体评分（0-100）
- dimension_scores: 各维度评分（0-100）
- strengths: 文档优点列表
- missing_sections: 缺失的必要章节列表
- suggestions: 具体的改进建议列表
- convention_issues: 规范性问题和格式错误列表
- beginner_confusion_points: 新手最可能困惑的步骤列表
- code_quality_issues: 代码示例质量问题列表
- structural_issues: 信息组织结构问题列表
- language_issues: 语言表达问题列表
- priority_recommendations: 优先级改进建议列表（按重要性排序）

请基于提供的README内容进行客观、专业的评估。

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
    "项目简介清晰，准确描述了核心价值",
    "主要功能列表完整，分类合理",
    "安装步骤基本可行"
  ],
  "missing_sections": [
    "缺少详细的配置说明",
    "未提供故障排除指南"
  ],
  "beginner_confusion_points": [
    "安装步骤中提到的'环境变量配置'未说明具体方法",
    "快速开始示例假设用户已了解基础概念，缺乏必要解释",
    "依赖安装命令未区分不同操作系统"
  ],
  "code_quality_issues": [
    "示例代码中硬编码了API密钥，存在安全风险",
    "缺少必要的错误处理代码",
    "代码示例未说明所需的导入语句"
  ],
  "structural_issues": [
    "安装步骤与配置说明分散在不同章节",
    "高级功能介绍出现在快速开始之前",
    "常见问题部分与主要内容存在重复"
  ],
  "language_issues": [
    "技术术语使用不够准确",
    "部分句子过长，影响阅读",
    "存在两处拼写错误"
  ],
  "priority_recommendations": [
    "修复代码示例中的安全风险，移除硬编码的敏感信息",
    "完善安装步骤，补充不同操作系统的具体命令和环境配置方法",
    "重组文档结构，确保信息呈现符合用户学习路径",
    "为复杂概念添加新手友好的解释说明",
    "统一技术术语的使用，修正语言表达问题"
  ],
  "suggestions": [
    "添加配置文件的详细说明",
    "增加故障排除和常见问题章节",
    "为代码示例添加更多注释"
  ],
  "convention_issues": [
    "部分标题层级使用不当",
    "代码块缺少语言标识"
  ]
}
```
'''.strip()

user_prompt = '''
请对以下开源项目的README文档进行全面质量评估：

文档内容：
{cleaned_markdown_text}

初步调用的可读性指标（仅供参考）：
{readability}

请从以下维度进行深入分析：

1. 【基础完整性检查】
判断是否包含以下核心章节，如有缺失请明确指出：
- 项目简介（项目是做什么的？）
- 主要功能（核心功能特性列表）
- 安装方法（详细的安装步骤）
- 基础用法示例（快速开始的代码示例）

2. 【新手可用性评估】
从一个完全新手的角度出发：
- 评估仅凭此文档是否能够成功安装和运行项目
- 指出文档中最可能让人困惑的3个步骤或概念
- 识别哪些地方需要前置知识但未说明

3. 【代码示例质量检查】
检查文档中的所有代码示例：
- 是否完整且可独立运行？
- 是否体现了编程最佳实践？
- 是否存在安全风险（如硬编码密码、不安全API使用）？
- 是否有适当的错误处理？

4. 【信息组织结构评估】
评估文档的信息架构：
- 逻辑流程是否清晰（从介绍→安装→使用→进阶）？
- 层次结构是否合理？
- 是否存在信息重复或矛盾之处？
- 导航是否便捷？

5. 【语言表达质量检查】
检查文档的语言表达：
- 是否存在语法错误或拼写错误？
- 技术用词是否专业准确？
- 表述是否简洁明了？
- 语气是否友好易懂？

6. 【优先级改进建议】
基于以上所有分析，提供3-5个最优先的改进建议，按重要性排序。

请确保评估客观、具体，并提供可操作的改进建议。
'''.strip()



def analyze_readme_with_llm(markdown_content, readability, api_key):
    client = openai.OpenAI(api_key=api_key, base_url="https://api.deepseek.com")
    
    try:
        response = client.chat.completions.create(
            model="deepseek-chat",  # 或 "gpt-3.5-turbo"
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt.format(cleaned_markdown_text=markdown_content, readability=json.dumps(readability))}
            ],
            response_format={"type": "json_object"}  # 强制JSON输出
        )
        # 解析响应
        result_json = json.loads(response.choices[0].message.content)
        result_json.update({"readability": readability})
        print(result_json)
        return result_json
        
    except Exception as e:
        return {"error": f"API调用失败: {str(e)}"}

if __name__ == "__main__":
  api_key = 'sk-99ed7f2e56bd478cb3147fd1593d4157'
  cleaned_markdown_text = "# Sample README\n\nThis is a sample README file for testing purposes.\n\n## Installation\n\nTo install, run:\n\n```bash\npip install sample-package\n```\n\n## Usage\n\nTo use the package, import it in your Python script:\n\n```python\nimport sample_package\n```"
  result = analyze_readme_with_llm(cleaned_markdown_text, api_key)

  print(result)