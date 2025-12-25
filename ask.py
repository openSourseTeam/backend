import openai
import json

DOC_TYPE_CONFIGS = {
    "readme": {
        "name": "README文档",
        "focus_areas": ["项目介绍", "安装指南", "使用说明", "功能特性", "快速开始"],
        "key_sections": ["项目简介", "安装步骤", "使用示例", "功能列表", "贡献指南链接"],
        "optimization_tips": "README是项目的门面，应该简洁明了，让用户快速了解项目价值并上手使用"
    },
    "contributing": {
        "name": "贡献指南",
        "focus_areas": ["贡献流程", "开发环境搭建", "代码规范", "提交规范", "测试要求"],
        "key_sections": ["如何贡献", "开发环境配置", "代码风格", "Pull Request流程", "测试指南"],
        "optimization_tips": "CONTRIBUTING文档应该详细说明如何参与项目开发，降低贡献门槛"
    },
    "changelog": {
        "name": "更新日志",
        "focus_areas": ["版本历史", "变更记录", "时间线", "破坏性变更标注"],
        "key_sections": ["版本号", "发布日期", "新增功能", "Bug修复", "破坏性变更"],
        "optimization_tips": "CHANGELOG应该按时间倒序排列，清晰标注每个版本的变更内容"
    },
    "code_of_conduct": {
        "name": "行为准则",
        "focus_areas": ["社区准则", "行为规范", "举报流程", "执行措施"],
        "key_sections": ["我们的承诺", "行为标准", "举报方式", "执行指南"],
        "optimization_tips": "CODE_OF_CONDUCT应该明确社区行为规范，营造友好包容的氛围"
    },
    "security": {
        "name": "安全政策",
        "focus_areas": ["漏洞报告流程", "支持的版本", "响应时间", "联系方式"],
        "key_sections": ["如何报告安全问题", "支持的版本", "响应流程", "联系方式"],
        "optimization_tips": "SECURITY文档应该清楚说明如何安全地报告漏洞，保护用户和项目"
    },
    "license": {
        "name": "许可证",
        "focus_areas": ["许可证类型", "使用权限", "限制条款", "免责声明"],
        "key_sections": ["许可证声明", "版权信息", "使用条款"],
        "optimization_tips": "LICENSE文档通常使用标准模板，无需大幅修改"
    },
    "installation": {
        "name": "安装文档",
        "focus_areas": ["系统要求", "依赖项", "安装步骤", "验证方法", "故障排除"],
        "key_sections": ["前置条件", "安装命令", "配置说明", "验证安装", "常见问题"],
        "optimization_tips": "安装文档应该提供详细的步骤和多种安装方式，考虑不同平台的差异"
    },
    "usage": {
        "name": "使用文档",
        "focus_areas": ["基本用法", "代码示例", "API说明", "高级功能", "最佳实践"],
        "key_sections": ["快速开始", "基础示例", "API参考", "进阶用法", "常见场景"],
        "optimization_tips": "使用文档应该从简单到复杂，提供丰富的实际代码示例"
    },
    "api": {
        "name": "API文档",
        "focus_areas": ["接口列表", "参数说明", "返回值", "错误码", "示例代码"],
        "key_sections": ["API概述", "端点列表", "请求参数", "响应格式", "错误处理"],
        "optimization_tips": "API文档应该详细、准确、格式统一，最好包含可运行的示例"
    },
    "support": {
        "name": "支持文档",
        "focus_areas": ["获取帮助", "资源链接", "社区论坛", "常见问题", "联系方式"],
        "key_sections": ["如何获取帮助", "资源链接", "社区/论坛", "常见问题", "联系方式"],
        "optimization_tips": "SUPPORT文档应该清晰说明如何获取帮助，提供多种支持渠道和资源链接"
    },
    "wiki": {
        "name": "Wiki文档",
        "focus_areas": ["目录索引", "概述介绍", "内容组织", "导航结构"],
        "key_sections": ["目录/索引", "概述/介绍", "主要内容", "导航链接"],
        "optimization_tips": "Wiki文档应该结构清晰，有良好的导航和索引，方便用户查找信息"
    },
    "docs": {
        "name": "文档目录",
        "focus_areas": ["快速开始", "目录导航", "文档结构", "内容组织"],
        "key_sections": ["快速开始", "目录/导航", "文档结构", "主要内容"],
        "optimization_tips": "文档目录应该提供清晰的导航结构，帮助用户快速找到所需信息"
    }
}


def get_doc_specific_prompt(doc_type="readme"):
    """
    根据文档类型获取特定的评估和优化提示
    """
    config = DOC_TYPE_CONFIGS.get(doc_type, DOC_TYPE_CONFIGS["readme"])
    return config


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
    "readme":{
        "结构完整性": 75,
        "内容质量": 80,
        "可读性": 85,
        "代码示例": 70,
        "新手友好度": 65,
        "维护性": 78,
        "国际化": 60
    },
    "contributing":{
        "结构完整性": 75,
        "内容质量": 80,
        "可读性": 85,
        "代码示例": 70,
        "新手友好度": 65,
        "维护性": 78,
        "国际化": 60
    },
    "code_of_conduct":{
        "结构完整性": 75,
        "内容质量": 80,
        "可读性": 85,
        "代码示例": 70,
        "新手友好度": 65,
        "维护性": 78,
        "国际化": 60
    },
    ...
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


# 文档优化提示词
optimize_system_prompt_template = '''
你是一名专业的技术文档编辑专家，擅长根据评估建议优化开源项目文档。

当前文档类型：{doc_type_name}
关注重点：{focus_areas}

你的任务是：
1. 根据提供的评估结果和改进建议，对原始文档进行优化
2. 保持文档的核心信息和结构
3. 修复识别出的问题（格式、语法、内容完整性等）
4. 改善表达清晰度和可读性
5. 确保优化后的文档符合{doc_type_name}的最佳实践
6. 优化后的文档必须使用与原始文档相同的语言（如果原始文档是中文，优化后也必须是中文；如果原始文档是英文，优化后也必须是英文）

重要提示：{optimization_tips}

输出要求：
- 直接返回优化后的完整Markdown文档
- 不要添加任何解释或说明
- 保持Markdown格式规范
- 确保所有链接、代码块、列表格式正确
- 必须使用与原始文档相同的语言撰写优化后的文档
'''.strip()

optimize_user_prompt_template = '''
请根据以下评估结果和建议，优化这份{doc_type_name}：

# 原始文档：
{original_content}

# 文档类型要求：
{doc_type_name}应该包含以下关键章节：{key_sections}

# 评估结果：
- 总体评分: {overall_score}/100
- 主要问题: {main_issues}

# 改进建议：
{suggestions}

# 缺失章节：
{missing_sections}

# 具体要求：
1. 修复所有提到的格式和语法问题
2. 根据{doc_type_name}的特点，补充缺失的必要章节
3. 改善不清晰的表达
4. 优化代码示例（如果有问题）
5. 保持原有信息的准确性
6. 确保文档结构符合{doc_type_name}的最佳实践
7. 优化后的文档必须使用与原始文档完全相同的语言（如果原始文档是中文，优化后必须全部使用中文；如果原始文档是英文，优化后必须全部使用英文。不要混合使用不同语言）

请直接输出优化后的完整Markdown文档，不要添加任何额外说明。
'''.strip()


def optimize_document_with_llm(original_content, analysis_result, api_key, doc_type="readme"):
    """
    使用LLM优化文档（根据文档类型自定义prompt）
    
    Args:
        original_content: 原始文档内容
        analysis_result: AI分析结果（包含评分、建议等）
        api_key: API密钥
        doc_type: 文档类型
        
    Returns:
        优化后的文档内容
    """
    print(f"正在优化 {doc_type.upper()} 文档... 原始长度: {len(original_content)}")
    client = openai.OpenAI(api_key=api_key, base_url="https://api.deepseek.com")
    
    import re
    chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', original_content))
    english_chars = len(re.findall(r'[a-zA-Z]', original_content))
    total_chars = chinese_chars + english_chars
    if total_chars > 0:
        chinese_ratio = chinese_chars / total_chars
        document_language = '中文' if chinese_ratio > 0.3 else '英文'
    else:
        document_language = '英文' 
    
    print(f"检测到原始文档语言: {document_language}")
    
    # 获取文档类型特定配置
    doc_config = get_doc_specific_prompt(doc_type)
    
    # 提取关键信息
    overall_score = analysis_result.get('overall_score', 0)
    suggestions = analysis_result.get('priority_recommendations', [])
    missing_sections = analysis_result.get('missing_sections', [])
    
    # 整理主要问题
    main_issues = []
    if analysis_result.get('code_quality_issues'):
        main_issues.extend(analysis_result['code_quality_issues'][:3])
    if analysis_result.get('structural_issues'):
        main_issues.extend(analysis_result['structural_issues'][:3])
    if analysis_result.get('convention_issues'):
        main_issues.extend(analysis_result['convention_issues'][:3])
    
    # 构建针对文档类型的系统提示词
    system_content = optimize_system_prompt_template.format(
        doc_type_name=doc_config['name'],
        focus_areas='、'.join(doc_config['focus_areas']),
        optimization_tips=doc_config['optimization_tips']
    )
    
    if document_language == '中文':
        system_content += "\n\n【重要语言要求】原始文档是中文，优化后的文档必须完全使用中文撰写，不要使用英文。"
    else:
        system_content += "\n\n【Important Language Requirement】The original document is in English. The optimized document must be written entirely in English. Do not use Chinese."
    
    # 构建针对文档类型的用户提示词
    user_content = optimize_user_prompt_template.format(
        doc_type_name=doc_config['name'],
        key_sections='、'.join(doc_config['key_sections']),
        original_content=original_content,
        overall_score=overall_score,
        main_issues='\n- '.join(main_issues) if main_issues else '无',
        suggestions='\n- '.join(suggestions) if suggestions else '无',
        missing_sections='\n- '.join(missing_sections) if missing_sections else '无'
    )
    
    try:
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": system_content},
                {"role": "user", "content": user_content}
            ],
            timeout=180,  # 优化可能需要更长时间
            stream = True
        )
        
        optimized_content = response.choices[0].message.content.strip()
        
        # 移除可能的代码块标记
        if optimized_content.startswith('```markdown'):
            optimized_content = optimized_content[11:]
        if optimized_content.startswith('```'):
            optimized_content = optimized_content[3:]
        if optimized_content.endswith('```'):
            optimized_content = optimized_content[:-3]
        
        optimized_content = optimized_content.strip()
        
        print(f"文档优化完成，优化后长度: {len(optimized_content)}")
        return optimized_content
        
    except Exception as e:
        print(f"文档优化失败: {e}")
        raise Exception(f"文档优化失败: {str(e)}")

if __name__ == "__main__":
  api_key = 'sk-99ed7f2e56bd478cb3147fd1593d4157'
  cleaned_markdown_text = "# Sample README\n\nThis is a sample README file for testing purposes.\n\n## Installation\n\nTo install, run:\n\n```bash\npip install sample-package\n```\n\n## Usage\n\nTo use the package, import it in your Python script:\n\n```python\nimport sample_package\n```"
  readability = {"score": 80, "issues": []}
  result = analyze_readme_with_llm(cleaned_markdown_text, readability, api_key)

  print(result)