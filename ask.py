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
你是一名资深的开源项目维护者和技术文档工程师，专注于评估开源项目文档的质量。

【核心约束】
你将只收到用户明确选择的文档进行评估。你的所有分析、评分、建议都必须严格限制在这些文档范围内。
绝对不要提及、评论或建议任何用户未提供的文档类型。

评估维度（针对每个提供的文档）：
1. 结构完整性 - 该类型文档的标准章节是否齐全
2. 内容质量 - 信息是否准确、充分、有价值
3. 可读性 - 语言表达是否清晰易懂，逻辑是否顺畅
4. 代码示例 - 代码示例是否完整、正确、安全
5. 新手友好度 - 新手能否轻松理解和使用
6. 维护性 - 格式规范、链接有效性、易于维护
7. 国际化 - 语言使用、术语统一性

输出必须是纯JSON格式，包含以下字段（所有字段都是必需的，不能为空）：
- overall_score: 总体评分（0-100），基于所有提供的文档
- dimension_scores: 每个文档的各维度评分（7个维度，见上方列表），必须为每个提供的文档类型都提供评分
- strengths: 提供的文档的优点列表（至少3-5条，不要提及未提供的文档）
- missing_sections: 提供的文档中缺失的章节列表（指文档内部章节，不是缺失的文档类型），如果没有缺失章节，可以是空数组[]
- suggestions: 针对提供的文档内容的具体改进建议（至少3-5条）
- convention_issues: 规范性问题和格式错误列表，如果没有问题，可以是空数组[]
- beginner_confusion_points: 新手可能困惑的地方（至少2-3条）
- code_quality_issues: 代码示例质量问题列表，如果没有代码示例或没有问题，可以是空数组[]
- structural_issues: 信息组织结构问题列表，如果没有问题，可以是空数组[]
- language_issues: 语言表达问题列表，如果没有问题，可以是空数组[]
- priority_recommendations: 优先级改进建议列表（至少3-5条，只针对提供的文档内容）

【重要】无论分析的是README、CONTRIBUTING、CHANGELOG还是其他任何文档类型，都必须完整输出上述所有字段。不能因为文档类型不同就省略某些字段。

【重要】系统支持12种文档类型：readme、contributing、code_of_conduct、changelog、license、security、support、wiki、docs、installation、usage、api
但用户每次只会选择其中的部分文档进行分析。你必须只分析用户实际提供的文档。

请勿在最终输出中添加任何解释。您的输出必须遵循以下格式:

**EXAMPLE**
（下面示例假设用户选择了installation和usage两个文档）

```json
{
  "overall_score": 75,
  "dimension_scores": {
    "installation":{
        "结构完整性": 70,
        "内容质量": 75,
        "可读性": 80,
        "代码示例": 65,
        "新手友好度": 72,
        "维护性": 78,
        "国际化": 60
    },
    "usage":{
        "结构完整性": 75,
        "内容质量": 80,
        "可读性": 85,
        "代码示例": 70,
        "新手友好度": 78,
        "维护性": 80,
        "国际化": 65
    }
  },
  "strengths": [
    "INSTALLATION文档的安装步骤清晰详细",
    "USAGE文档包含丰富的使用示例",
    "两个文档的格式规范统一"
  ],
  "missing_sections": [
    "INSTALLATION文档中缺少故障排查章节",
    "USAGE文档中缺少高级用法说明"
  ],
  "beginner_confusion_points": [
    "INSTALLATION中提到的'依赖项'未详细说明版本要求",
    "USAGE中某些参数的含义不够清楚"
  ],
  "code_quality_issues": [
    "USAGE文档的示例代码缺少错误处理",
    "INSTALLATION的命令示例未说明执行环境"
  ],
  "structural_issues": [
    "INSTALLATION文档的章节顺序可以优化",
    "USAGE文档的示例分布不够均衡"
  ],
  "language_issues": [
    "部分技术术语表达不够准确",
    "存在个别拼写错误"
  ],
  "priority_recommendations": [
    "在INSTALLATION文档中补充故障排查指南",
    "完善USAGE文档的示例代码，增加错误处理",
    "统一两个文档中的术语使用"
  ],
  "suggestions": [
    "优化INSTALLATION文档的章节结构",
    "为USAGE文档增加快速开始部分",
    "检查并修正拼写错误"
  ],
  "convention_issues": [
    "部分代码块缺少语言标识",
    "标题层级使用不够一致"
  ]
}
```

注意：
1. 上述示例仅针对installation和usage两个文档，没有提及其他未选中的文档类型（如readme、contributing等）。
2. 你在实际分析时，也必须严格遵循这个原则，只分析和评论用户实际提供的文档。
3. **无论分析的是哪种文档类型（README、CONTRIBUTING、CHANGELOG、LICENSE、SECURITY等），都必须输出完整的JSON结构，包含所有字段**：
   - strengths 必须至少3-5条
   - suggestions 必须至少3-5条
   - beginner_confusion_points 必须至少2-3条
   - priority_recommendations 必须至少3-5条
   - 其他字段如果没有问题，可以是空数组[]，但不能省略
4. 不要因为文档类型不同就减少输出内容或省略字段。
'''.strip()

user_prompt = '''
【严格限制】本次分析ONLY评估以下文档类型：{selected_doc_types}

请对以下提供的文档进行质量评估：

{docs_content}

【核心原则 - 请务必遵守】
1. 只分析上面明确列出的文档类型：{selected_doc_types}
2. 所有的问题分析、改进建议、优缺点评价，都只能针对这些已选中的文档
3. 绝对不要在任何分析、建议、评论中提及其他文档类型（如README、CHANGELOG、LICENSE等未选中的文档）
4. 如果某个文档类型没有在选中列表中，就完全不要提及它的名字

【禁止行为示例】
❌ 错误："建议完善README文档" （如果README未被选中）
❌ 错误："缺少LICENSE文件" （如果LICENSE未被选中）
❌ 错误："应该在CHANGELOG中记录版本信息" （如果CHANGELOG未被选中）
❌ 错误："建议添加安全政策文档" （如果SECURITY未被选中）
✅ 正确："CONTRIBUTING文档中的开发环境配置不够详细" （如果CONTRIBUTING被选中）
✅ 正确："当前文档的代码示例缺少错误处理" （针对选中的文档）

初步调用的规则检查结果（仅供参考）：
{rule_checks}

请从以下维度进行深入分析（只针对选中的文档：{selected_doc_types}）：

1. 【文档完整性检查】
检查已提供的文档中，该类型文档自身的标准章节是否齐全。
注意：只检查已提供文档自身的章节完整性，不要提及未提供的文档类型。

2. 【新手可用性评估】
基于已提供的文档，评估：
- 新手用户能否根据这些文档成功安装和运行？
- 新手贡献者能否清楚如何参与贡献？
- 识别新手在阅读这些文档时可能的困惑点。
注意：只基于已提供的文档进行评估，不要提及其他文档。

3. 【代码示例质量检查】
检查已提供文档中的代码示例：
- 是否完整可运行？
- 是否存在安全风险？
- 是否有清晰的注释说明？

4. 【信息组织结构评估】
评估已提供文档的内部结构：
- 文档内部结构是否清晰？
- 信息层次是否合理？

5. 【语言表达质量检查】
检查已提供文档的表达质量：
- 语言是否准确、友好、简洁？
- 术语使用是否一致？
- 是否有语法或拼写错误？

6. 【优先级改进建议】
针对已提供的文档内容本身，提供3-5个最优先的改进建议。
严格要求：
- 只针对选中的文档（{selected_doc_types}）的内容提出改进建议
- 不要建议"添加XX文档"或"完善XX文档"（如果XX文档没有被选中）
- 所有建议必须是针对已有文档内容的改进，而不是建议添加新文档类型
- 例如：可以说"当前文档的示例代码需要增加注释"，但不能说"建议添加README文档"

【最后强调 - 输出要求】
1. 你的所有输出（strengths、missing_sections、suggestions、beginner_confusion_points、code_quality_issues、structural_issues、language_issues、priority_recommendations）都必须严格限制在选中的文档范围内：{selected_doc_types}
2. 不要提及任何未选中的文档类型！
3. **必须完整输出所有JSON字段**，包括：
   - strengths: 至少列出3-5个优点
   - suggestions: 至少提供3-5条改进建议
   - beginner_confusion_points: 至少识别2-3个困惑点
   - priority_recommendations: 至少提供3-5条优先级建议
   - 其他字段如果确实没有问题，可以是空数组[]，但不能省略字段
4. 无论分析的是哪种文档类型（README、CONTRIBUTING、CHANGELOG、LICENSE等），都必须提供完整的分析结果，不能因为文档类型不同就减少输出内容。
'''.strip()




def analyze_readme_with_llm(markdown_content, readability, api_key, selected_types=None):
    """
    使用LLM分析文档质量（支持单文档或多文档合并分析）
    
    Args:
        markdown_content: 文档内容（可以是单个文档或多个文档合并后的内容）
        readability: 可读性指标
        api_key: API密钥
        selected_types: 选中的文档类型列表
    """
    if selected_types is None:
        selected_types = ["readme"]
    
    selected_types_str = "、".join(selected_types)
    print(f"正在调用 LLM API 分析文档... 文档长度: {len(markdown_content)}")
    print(f"选中的文档类型: {selected_types_str}")
    client = openai.OpenAI(api_key=api_key, base_url="https://api.deepseek.com")
    
    try:
        response = client.chat.completions.create(
            model="deepseek-chat",  # 或 "gpt-3.5-turbo"
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt.format(
                    docs_content=markdown_content, 
                    selected_doc_types=selected_types_str,
                    rule_checks=json.dumps(readability)
                )}
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
            stream=False  # 改为非流式，简化处理
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