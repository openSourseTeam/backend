import re
import requests
from typing import Dict, List, Any
from urllib.parse import urlparse
import logging
import mistune
from concurrent.futures import ThreadPoolExecutor, as_completed
from functools import lru_cache

logger = logging.getLogger(__name__)

# 全局链接检查缓存（避免重复检查相同链接）
_link_cache = {}


# 文档类型检查策略配置
DOC_TYPE_CHECK_STRATEGY = {
    "readme": {
        "code_block_check": "strict",      # 严格：必须有代码块且需要语言标识
        "link_check": "strict",            # 严格：链接必须可访问
        "heading_structure_check": "strict" # 严格：标题层级不能跳跃
    },
    "contributing": {
        "code_block_check": "strict",      # 通常有代码示例
        "link_check": "strict",
        "heading_structure_check": "strict"
    },
    "license": {
        "code_block_check": "skip",        # 跳过：LICENSE通常没有代码块
        "link_check": "loose",             # 宽松：可能没有链接
        "heading_structure_check": "loose"  # 宽松：可能只有一级标题或没有标题
    },
    "changelog": {
        "code_block_check": "skip",        # 跳过：CHANGELOG通常没有代码块
        "link_check": "normal",            # 普通：可能有PR/Issue链接
        "heading_structure_check": "normal" # 普通：版本号作为标题
    },
    "code_of_conduct": {
        "code_block_check": "skip",        # 跳过：行为准则通常没有代码块
        "link_check": "normal",
        "heading_structure_check": "normal"
    },
    "security": {
        "code_block_check": "skip",        # 跳过：安全政策通常没有代码块
        "link_check": "strict",            # 严格：需要联系方式链接
        "heading_structure_check": "normal"
    },
    "support": {
        "code_block_check": "skip",        # 跳过：支持文档通常没有代码块
        "link_check": "strict",            # 严格：需要资源链接
        "heading_structure_check": "normal"
    },
    "wiki": {
        "code_block_check": "normal",      # 普通：Wiki可能有代码示例
        "link_check": "strict",            # 严格：Wiki通常有很多内部链接
        "heading_structure_check": "strict" # 严格：需要清晰的导航结构
    },
    "docs": {
        "code_block_check": "normal",      # 普通：文档目录可能有示例
        "link_check": "strict",            # 严格：需要导航链接
        "heading_structure_check": "strict" # 严格：需要清晰的结构
    },
    "installation": {
        "code_block_check": "strict",      # 严格：必须有安装命令示例
        "link_check": "normal",
        "heading_structure_check": "strict"
    },
    "usage": {
        "code_block_check": "strict",      # 严格：必须有使用示例
        "link_check": "normal",
        "heading_structure_check": "strict"
    },
    "api": {
        "code_block_check": "strict",      # 严格：必须有API调用示例
        "link_check": "normal",
        "heading_structure_check": "strict"
    }
}


class DocumentCodeChecker:
    """文档代码层面质量检查器"""
    
    def __init__(self):
        """初始化检查器"""
        self.timeout = 3  # HTTP 请求超时时间（从5秒降低到3秒）
        self.link_check_enabled = True
        self.markdown_parser = mistune.create_markdown(renderer=None)  # 创建 Markdown 解析器
        self.max_concurrent_link_checks = 10  # 最大并发链接检查数
    
    def get_check_strategy(self, doc_type: str) -> Dict[str, str]:
        """
        获取文档类型的检查策略
        
        Args:
            doc_type: 文档类型
            
        Returns:
            检查策略配置
        """
        return DOC_TYPE_CHECK_STRATEGY.get(doc_type, DOC_TYPE_CHECK_STRATEGY["readme"])
        
    def check_all(self, markdown_content: str, doc_type: str = "readme") -> Dict[str, Any]:
        """
        执行所有代码层面的检查
        
        Args:
            markdown_content: Markdown 文档内容
            doc_type: 文档类型（readme, contributing等）
            
        Returns:
            包含所有检查结果的字典
        """
        strategy = self.get_check_strategy(doc_type)
        
        results = {
            "link_check": self.check_links(markdown_content, strategy["link_check"]),
            "code_block_check": self.check_code_blocks(markdown_content, strategy["code_block_check"]),
            "heading_structure_check": self.check_heading_structure(markdown_content, strategy["heading_structure_check"]),
            "section_completeness_check": self.check_section_completeness(markdown_content, doc_type),
            "markdown_syntax_check": self.check_markdown_syntax(markdown_content),
        }
        
        # 汇总统计
        results["summary"] = self._generate_summary(results)
        
        return results
    
    def check_links(self, markdown_content: str, strictness: str = "strict") -> Dict[str, Any]:
        """
        检查链接可访问性
        提取文档中的所有链接，检查 HTTP 状态码
        
        Args:
            markdown_content: Markdown 文档内容
            strictness: 检查严格程度 (strict/normal/loose)
            
        Returns:
            链接检查结果
        """
        # 提取所有 Markdown 链接: [text](url)
        link_pattern = r'\[([^\]]+)\]\(([^\)]+)\)'
        links = re.findall(link_pattern, markdown_content)
        
        # 提取所有直接的 URL
        url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+'
        direct_urls = re.findall(url_pattern, markdown_content)
        
        total_links = []
        checked_urls = set()  # 避免重复检查
        
        # 检查 Markdown 链接
        for text, url in links:
            if url.startswith('http') and url not in checked_urls:
                total_links.append({"text": text, "url": url, "type": "markdown"})
                checked_urls.add(url)
        
        # 检查直接 URL（排除已在 Markdown 链接中的）
        for url in direct_urls:
            if url not in checked_urls:
                total_links.append({"text": url, "url": url, "type": "direct"})
                checked_urls.add(url)
        
        # 根据严格程度决定是否实际检查链接
        if strictness == "loose":
            # 宽松模式：只统计链接数量，不实际检查
            return {
                "total_links": len(total_links),
                "valid_links": len(total_links),
                "invalid_links": 0,
                "timeout_links": 0,
                "valid_links_list": total_links,
                "invalid_links_list": [],
                "timeout_links_list": [],
                "check_passed": True,
                "strictness": strictness,
                "note": "宽松模式：跳过链接有效性检查（适用于LICENSE等文档）"
            }
        
        # 执行链接检查（并发执行，提高性能）
        valid_links = []
        invalid_links = []
        timeout_links = []
        
        # 使用线程池并发检查链接
        max_workers = min(self.max_concurrent_link_checks, len(total_links))
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # 提交所有链接检查任务
            future_to_link = {
                executor.submit(self._check_single_link, link_info["url"]): link_info
                for link_info in total_links
            }
            
            # 处理完成的任务
            for future in as_completed(future_to_link):
                link_info = future_to_link[future]
                try:
                    status = future.result()
                    
                    link_result = {
                        "text": link_info["text"],
                        "url": link_info["url"],
                        "type": link_info["type"],
                        "status": status["status"],
                        "status_code": status.get("status_code"),
                        "error": status.get("error")
                    }
                    
                    if status["status"] == "valid":
                        valid_links.append(link_result)
                    elif status["status"] == "timeout":
                        timeout_links.append(link_result)
                    else:
                        invalid_links.append(link_result)
                        
                except Exception as e:
                    logger.error(f"链接检查失败: {link_info['url']} - {e}")
                    invalid_links.append({
                        "text": link_info["text"],
                        "url": link_info["url"],
                        "type": link_info["type"],
                        "status": "error",
                        "error": str(e)
                    })
        
        # 根据严格程度判断是否通过
        if strictness == "normal":
            # 普通模式：允许少量超时，但不能有无效链接
            check_passed = len(invalid_links) == 0
        else:  # strict
            # 严格模式：不允许有无效链接或超时
            check_passed = len(invalid_links) == 0 and len(timeout_links) == 0
        
        return {
            "total_links": len(total_links),
            "valid_links": len(valid_links),
            "invalid_links": len(invalid_links),
            "timeout_links": len(timeout_links),
            "valid_links_list": valid_links,
            "invalid_links_list": invalid_links,
            "timeout_links_list": timeout_links,
            "check_passed": check_passed,
            "strictness": strictness
        }
    
    def _check_single_link(self, url: str) -> Dict[str, Any]:
        """
        检查单个链接的可访问性（带缓存）
        
        Args:
            url: 要检查的 URL
            
        Returns:
            检查结果
        """
        # 检查缓存
        if url in _link_cache:
            return _link_cache[url]
        
        try:
            # 发送 HEAD 请求（比 GET 更快）
            response = requests.head(
                url, 
                timeout=self.timeout, 
                allow_redirects=True,
                headers={'User-Agent': 'README-Quality-Checker/1.0'}
            )
            
            # 如果 HEAD 请求失败，尝试 GET 请求
            if response.status_code >= 400:
                response = requests.get(
                    url, 
                    timeout=self.timeout, 
                    allow_redirects=True,
                    headers={'User-Agent': 'README-Quality-Checker/1.0'}
                )
            
            if response.status_code < 400:
                result = {
                    "status": "valid",
                    "status_code": response.status_code
                }
            else:
                result = {
                    "status": "invalid",
                    "status_code": response.status_code,
                    "error": f"HTTP {response.status_code}"
                }
            
            # 缓存结果
            _link_cache[url] = result
            return result
                
        except requests.exceptions.Timeout:
            result = {
                "status": "timeout",
                "error": "请求超时"
            }
            _link_cache[url] = result
            return result
        except requests.exceptions.RequestException as e:
            result = {
                "status": "invalid",
                "error": str(e)
            }
            _link_cache[url] = result
            return result
        except Exception as e:
            logger.error(f"检查链接时发生错误: {url}, 错误: {e}")
            result = {
                "status": "error",
                "error": str(e)
            }
            _link_cache[url] = result
            return result
    
    def check_code_blocks(self, markdown_content: str, strictness: str = "strict") -> Dict[str, Any]:
        """
        检查代码块语言标识
        检查代码块是否标注了语言类型
        
        Args:
            markdown_content: Markdown 文档内容
            strictness: 检查严格程度 (strict/normal/skip)
            
        Returns:
            代码块检查结果
        """
        # 如果是跳过模式，直接返回通过
        if strictness == "skip":
            return {
                "total_code_blocks": 0,
                "blocks_with_language": 0,
                "blocks_without_language": 0,
                "languages_used": [],
                "language_counts": {},
                "check_passed": True,
                "strictness": strictness,
                "note": "跳过代码块检查（适用于LICENSE、CHANGELOG等文档）"
            }
        
        # 匹配代码块: ```language 或 ```
        code_block_pattern = r'```(\w+)?'
        matches = re.findall(code_block_pattern, markdown_content)
        
        # 成对出现，所以总数除以 2
        total_blocks = len(matches) // 2
        
        # 统计有语言标识的代码块
        blocks_with_language = sum(1 for lang in matches if lang)
        blocks_without_language = total_blocks - (blocks_with_language // 2)
        
        # 提取所有使用的语言
        languages_used = [lang for lang in matches if lang]
        language_counts = {}
        for lang in languages_used:
            language_counts[lang] = language_counts.get(lang, 0) + 1
        
        # 根据严格程度判断是否通过
        if strictness == "strict":
            # 严格模式：所有代码块都必须有语言标识
            check_passed = blocks_without_language == 0
            issues = [
                f"发现 {blocks_without_language} 个代码块缺少语言标识"
            ] if blocks_without_language > 0 else []
        else:  # normal
            # 普通模式：允许少量代码块没有语言标识（< 20%）
            if total_blocks == 0:
                check_passed = True
                issues = []
            else:
                ratio = blocks_without_language / total_blocks
                check_passed = ratio < 0.2
                issues = [
                    f"发现 {blocks_without_language}/{total_blocks} 个代码块缺少语言标识（{ratio*100:.1f}%）"
                ] if not check_passed else []
        
        return {
            "total_code_blocks": total_blocks,
            "blocks_with_language": blocks_with_language // 2,
            "blocks_without_language": blocks_without_language,
            "languages_used": list(set(languages_used)),
            "language_counts": language_counts,
            "check_passed": check_passed,
            "strictness": strictness,
            "issues": issues
        }
    
    def check_heading_structure(self, markdown_content: str, strictness: str = "strict") -> Dict[str, Any]:
        """
        检查标题结构规范性
        检查标题层级是否合理（不应该跳级）
        
        Args:
            markdown_content: Markdown 文档内容
            strictness: 检查严格程度 (strict/normal/loose)
            
        Returns:
            标题结构检查结果
        """
        # 匹配标题: # Heading
        heading_pattern = r'^(#{1,6})\s+(.+)$'
        headings = []
        
        for line in markdown_content.split('\n'):
            match = re.match(heading_pattern, line.strip())
            if match:
                level = len(match.group(1))
                text = match.group(2).strip()
                headings.append({"level": level, "text": text})
        
        # 宽松模式：不检查层级跳跃
        if strictness == "loose":
            level_counts = {}
            for heading in headings:
                level = heading["level"]
                level_counts[f"h{level}"] = level_counts.get(f"h{level}", 0) + 1
            
            return {
                "total_headings": len(headings),
                "level_counts": level_counts,
                "headings": headings,
                "issues": [],
                "check_passed": True,
                "strictness": strictness,
                "note": "宽松模式：跳过标题层级检查（适用于LICENSE等文档）"
            }
        
        # 检查标题层级跳跃
        issues = []
        prev_level = 0
        
        for i, heading in enumerate(headings):
            level = heading["level"]
            
            # 检查是否跳级（例如从 # 直接到 ###）
            if prev_level > 0 and level > prev_level + 1:
                issue = {
                    "type": "level_skip",
                    "heading": heading["text"],
                    "level": level,
                    "prev_level": prev_level,
                    "message": f"标题 '{heading['text']}' 从 H{prev_level} 跳到 H{level}，建议使用 H{prev_level + 1}"
                }
                
                # 普通模式：跳跃2级以上才算问题
                if strictness == "normal":
                    if level > prev_level + 2:
                        issues.append(issue)
                else:  # strict
                    issues.append(issue)
            
            prev_level = level
        
        # 统计各级标题数量
        level_counts = {}
        for heading in headings:
            level = heading["level"]
            level_counts[f"h{level}"] = level_counts.get(f"h{level}", 0) + 1
        
        return {
            "total_headings": len(headings),
            "level_counts": level_counts,
            "headings": headings,
            "issues": issues,
            "check_passed": len(issues) == 0,
            "strictness": strictness
        }
    
    def check_section_completeness(self, markdown_content: str, 
                                   doc_type: str = "readme") -> Dict[str, Any]:
        """
        检查章节完整性
        根据文档类型检查必要章节是否存在
        
        Args:
            markdown_content: Markdown 文档内容
            doc_type: 文档类型 (readme, contributing, changelog 等)
            
        Returns:
            章节完整性检查结果
        """
        # 定义不同文档类型的必要章节
        required_sections = {
            "readme": [
                {"name": "简介/介绍", "patterns": [r"简介", r"介绍", r"introduction", r"about"], "required": True},
                {"name": "功能/特性", "patterns": [r"功能", r"特性", r"features"], "required": True},
                {"name": "安装", "patterns": [r"安装", r"installation", r"install", r"getting started"], "required": True},
                {"name": "使用/用法", "patterns": [r"使用", r"用法", r"usage", r"使用方法", r"how to use"], "required": True},
            ],
            "contributing": [
                {"name": "贡献流程", "patterns": [r"贡献", r"contributing", r"how to contribute", r"pull request", r"流程", r"workflow"], "required": True},
                {"name": "环境搭建", "patterns": [r"环境", r"setup", r"development", r"environment", r"install"], "required": True},
                {"name": "代码规范", "patterns": [r"代码规范", r"code style", r"coding standards", r"style guide"], "required": True},
                {"name": "测试指南", "patterns": [r"测试", r"test", r"testing"], "required": False},
            ],
            "changelog": [
                {"name": "未发布版本", "patterns": [r"unreleased", r"未发布"], "required": False},
                {"name": "版本记录", "patterns": [r"v?\d+\.\d+", r"version", r"\d{4}-\d{2}-\d{2}"], "required": True},
            ],
            "code_of_conduct": [
                {"name": "承诺/誓言", "patterns": [r"pledge", r"commitment", r"承诺"], "required": False},
                {"name": "标准/准则", "patterns": [r"standards", r"behavior", r"准则", r"行为"], "required": True},
                {"name": "举报/执行", "patterns": [r"enforcement", r"reporting", r"contact", r"举报", r"联系"], "required": True},
            ],
            "license": [
                 # License usually doesn't have sections, but we can check if it looks like a license
            ],
            "security": [
                {"name": "报告漏洞", "patterns": [r"reporting", r"report", r"漏洞", r"vulnerability", r"security issue"], "required": True},
                {"name": "联系方式", "patterns": [r"contact", r"email", r"联系", r"报告地址"], "required": True},
                {"name": "响应流程", "patterns": [r"process", r"response", r"disclosure", r"流程"], "required": False},
                {"name": "支持版本", "patterns": [r"supported versions", r"支持版本", r"version"], "required": False},
            ],
            "support": [
                {"name": "获取帮助", "patterns": [r"getting help", r"how to get help", r"获取帮助", r"如何提问", r"how to ask", r"asking for help"], "required": True},
                {"name": "资源/链接", "patterns": [r"resources", r"documentation", r"资源", r"文档", r"links"], "required": False},
                {"name": "社区/论坛", "patterns": [r"community", r"forum", r"社区", r"论坛", r"discussion"], "required": False},
            ],
            "wiki": [
                {"name": "目录/索引", "patterns": [r"table of contents", r"index", r"目录", r"索引", r"导航"], "required": False},
                {"name": "概述/介绍", "patterns": [r"overview", r"introduction", r"概述", r"简介"], "required": False},
                # Wiki 比较自由，不强制要求章节
            ],
            "docs": [
                {"name": "快速开始", "patterns": [r"quick start", r"getting started", r"快速开始", r"入门"], "required": True},
                {"name": "目录/导航", "patterns": [r"table of contents", r"navigation", r"目录", r"导航"], "required": False},
                {"name": "文档结构", "patterns": [r"documentation", r"structure", r"文档", r"guide"], "required": False},
            ],
            "installation": [
                {"name": "前置要求", "patterns": [r"requirements", r"prerequisites", r"前置", r"依赖"], "required": True},
                {"name": "安装步骤", "patterns": [r"installation", r"install", r"setup", r"安装步骤", r"安装方法"], "required": True},
                {"name": "验证安装", "patterns": [r"verify", r"test", r"验证", r"测试"], "required": False},
                {"name": "故障排除", "patterns": [r"troubleshooting", r"问题", r"常见错误", r"faq"], "required": False},
            ],
            "usage": [
                {"name": "基本用法", "patterns": [r"basic usage", r"基本用法", r"快速开始", r"getting started"], "required": True},
                {"name": "示例/Examples", "patterns": [r"examples", r"示例", r"example"], "required": True},
                {"name": "高级用法", "patterns": [r"advanced", r"高级", r"进阶"], "required": False},
            ],
            "api": [
                {"name": "概述/介绍", "patterns": [r"overview", r"introduction", r"概述", r"简介"], "required": False},
                {"name": "接口/方法", "patterns": [r"methods", r"functions", r"endpoints", r"接口", r"方法", r"api"], "required": True},
                {"name": "参数说明", "patterns": [r"parameters", r"arguments", r"参数"], "required": False},
                {"name": "示例/Examples", "patterns": [r"examples", r"示例", r"usage"], "required": False},
            ]
        }
        
        sections_to_check = required_sections.get(doc_type, required_sections["readme"])
        
        # 提取所有标题
        heading_pattern = r'^#{1,6}\s+(.+)$'
        headings = []
        for line in markdown_content.split('\n'):
            match = re.match(heading_pattern, line.strip())
            if match:
                headings.append(match.group(1).strip())
        
        # 检查每个必要章节
        found_sections = []
        missing_sections = []
        
        for section in sections_to_check:
            found = False
            for heading in headings:
                for pattern in section["patterns"]:
                    if re.search(pattern, heading, re.IGNORECASE):
                        found = True
                        found_sections.append({
                            "name": section["name"],
                            "heading": heading
                        })
                        break
                if found:
                    break
            
            if not found and section["required"]:
                missing_sections.append(section["name"])
        
        return {
            "doc_type": doc_type,
            "total_required_sections": len([s for s in sections_to_check if s["required"]]),
            "found_sections": len(found_sections),
            "missing_sections": missing_sections,
            "found_sections_list": found_sections,
            "check_passed": len(missing_sections) == 0,
            "issues": [
                f"缺少必要章节: {section}" for section in missing_sections
            ]
        }
    
    def check_markdown_syntax(self, markdown_content: str) -> Dict[str, Any]:
        """
        检查 Markdown 语法规范性
        使用 mistune 解析器检查语法错误和格式问题
        
        Args:
            markdown_content: Markdown 文档内容
            
        Returns:
            Markdown 语法检查结果
        """
        issues = []
        warnings = []
        
        # 1. 尝试解析 Markdown，捕获语法错误
        try:
            tokens = self.markdown_parser(markdown_content)
            parse_success = True
        except Exception as e:
            parse_success = False
            issues.append({
                "type": "parse_error",
                "message": f"Markdown 解析失败: {str(e)}",
                "severity": "error"
            })
        
        # 2. 检查列表格式
        list_issues = self._check_list_format(markdown_content)
        issues.extend(list_issues)
        
        # 3. 检查表格格式
        table_issues = self._check_table_format(markdown_content)
        issues.extend(table_issues)
        
        # 4. 检查链接和图片格式
        link_format_issues = self._check_link_format(markdown_content)
        issues.extend(link_format_issues)
        
        # 5. 检查代码块格式
        code_block_issues = self._check_code_block_format(markdown_content)
        warnings.extend(code_block_issues)
        
        # 6. 检查引用块格式
        blockquote_issues = self._check_blockquote_format(markdown_content)
        warnings.extend(blockquote_issues)
        
        return {
            "parse_success": parse_success,
            "total_issues": len(issues),
            "total_warnings": len(warnings),
            "issues": issues,
            "warnings": warnings,
            "check_passed": len(issues) == 0,
            "summary": f"发现 {len(issues)} 个错误，{len(warnings)} 个警告"
        }
    
    def _check_list_format(self, markdown_content: str) -> List[Dict[str, Any]]:
        """检查列表格式"""
        issues = []
        lines = markdown_content.split('\n')
        
        for i, line in enumerate(lines, 1):
            # 检查无序列表格式：应该是 "- " 或 "* " 或 "+ "
            if re.match(r'^[\-\*\+](?!\s)', line.strip()):
                issues.append({
                    "type": "list_format",
                    "line": i,
                    "message": f"列表标记后缺少空格: '{line.strip()}'",
                    "severity": "error"
                })
            
            # 检查有序列表格式：应该是 "1. "
            if re.match(r'^\d+\.(?!\s)', line.strip()):
                issues.append({
                    "type": "list_format",
                    "line": i,
                    "message": f"有序列表标记后缺少空格: '{line.strip()}'",
                    "severity": "error"
                })
        
        return issues
    
    def _check_table_format(self, markdown_content: str) -> List[Dict[str, Any]]:
        """检查表格格式"""
        issues = []
        lines = markdown_content.split('\n')
        
        in_table = False
        table_start_line = 0
        
        for i, line in enumerate(lines, 1):
            # 检测表格行（包含 |）
            if '|' in line:
                if not in_table:
                    in_table = True
                    table_start_line = i
                
                # 检查表格行是否以 | 开始和结束
                stripped = line.strip()
                if stripped and not stripped.startswith('|'):
                    issues.append({
                        "type": "table_format",
                        "line": i,
                        "message": "表格行应该以 | 开始",
                        "severity": "warning"
                    })
                if stripped and not stripped.endswith('|'):
                    issues.append({
                        "type": "table_format",
                        "line": i,
                        "message": "表格行应该以 | 结束",
                        "severity": "warning"
                    })
            else:
                in_table = False
        
        return issues
    
    def _check_link_format(self, markdown_content: str) -> List[Dict[str, Any]]:
        """检查链接和图片格式"""
        issues = []
        
        # 检查未闭合的链接：[text 但没有 ](url)
        unclosed_links = re.findall(r'\[([^\]]+)(?!\]\()', markdown_content)
        for match in unclosed_links:
            # 排除正常的链接（后面跟着 ](）
            if not re.search(rf'\[{re.escape(match)}\]\([^\)]+\)', markdown_content):
                issues.append({
                    "type": "link_format",
                    "message": f"未闭合的链接: '[{match}'",
                    "severity": "error"
                })
        
        # 检查空链接：[text]()
        empty_links = re.findall(r'\[([^\]]+)\]\(\s*\)', markdown_content)
        for text in empty_links:
            issues.append({
                "type": "link_format",
                "message": f"空链接: '[{text}]()'",
                "severity": "error"
            })
        
        # 检查空图片：![]()
        empty_images = re.findall(r'!\[([^\]]*)\]\(\s*\)', markdown_content)
        for alt in empty_images:
            issues.append({
                "type": "image_format",
                "message": f"空图片链接: '![{alt}]()'",
                "severity": "error"
            })
        
        return issues
    
    def _check_code_block_format(self, markdown_content: str) -> List[Dict[str, Any]]:
        """检查代码块格式"""
        warnings = []
        
        # 检查代码块是否成对出现
        code_fences = re.findall(r'^```', markdown_content, re.MULTILINE)
        if len(code_fences) % 2 != 0:
            warnings.append({
                "type": "code_block_format",
                "message": f"代码块标记不成对（发现 {len(code_fences)} 个 ```）",
                "severity": "error"
            })
        
        # 检查行内代码格式
        inline_code_backticks = re.findall(r'`', markdown_content)
        if len(inline_code_backticks) % 2 != 0:
            warnings.append({
                "type": "inline_code_format",
                "message": f"行内代码标记不成对（发现 {len(inline_code_backticks)} 个 `）",
                "severity": "warning"
            })
        
        return warnings
    
    def _check_blockquote_format(self, markdown_content: str) -> List[Dict[str, Any]]:
        """检查引用块格式"""
        warnings = []
        lines = markdown_content.split('\n')
        
        for i, line in enumerate(lines, 1):
            # 检查引用块格式：应该是 "> "
            if re.match(r'^>(?!\s)', line.strip()) and line.strip() != '>':
                warnings.append({
                    "type": "blockquote_format",
                    "line": i,
                    "message": f"引用块标记后缺少空格: '{line.strip()}'",
                    "severity": "warning"
                })
        
        return warnings
    
    def _generate_summary(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """
        生成检查结果汇总
        
        Args:
            results: 所有检查结果
            
        Returns:
            汇总信息
        """
        total_issues = 0
        passed_checks = 0
        failed_checks = 0
        
        all_issues = []
        
        # 链接检查
        if results["link_check"]["invalid_links"] > 0:
            failed_checks += 1
            total_issues += results["link_check"]["invalid_links"]
            all_issues.append(f"发现 {results['link_check']['invalid_links']} 个失效链接")
        else:
            passed_checks += 1
        
        # 代码块检查
        if not results["code_block_check"]["check_passed"]:
            failed_checks += 1
            total_issues += results["code_block_check"]["blocks_without_language"]
            all_issues.extend(results["code_block_check"]["issues"])
        else:
            passed_checks += 1
        
        # 标题结构检查
        if not results["heading_structure_check"]["check_passed"]:
            failed_checks += 1
            total_issues += len(results["heading_structure_check"]["issues"])
            all_issues.extend([issue["message"] for issue in results["heading_structure_check"]["issues"]])
        else:
            passed_checks += 1
        
        # 章节完整性检查
        if not results["section_completeness_check"]["check_passed"]:
            failed_checks += 1
            total_issues += len(results["section_completeness_check"]["missing_sections"])
            all_issues.extend(results["section_completeness_check"]["issues"])
        else:
            passed_checks += 1
        
        # Markdown 语法检查
        if not results["markdown_syntax_check"]["check_passed"]:
            failed_checks += 1
            total_issues += results["markdown_syntax_check"]["total_issues"]
            all_issues.extend([issue["message"] for issue in results["markdown_syntax_check"]["issues"]])
        else:
            passed_checks += 1
        
        return {
            "total_checks": passed_checks + failed_checks,
            "passed_checks": passed_checks,
            "failed_checks": failed_checks,
            "total_issues": total_issues,
            "all_issues": all_issues,
            "overall_passed": failed_checks == 0
        }


# 便捷函数
def check_document_quality(markdown_content: str, doc_type: str = "readme") -> Dict[str, Any]:
    """
    便捷函数：检查文档质量
    
    Args:
        markdown_content: Markdown 文档内容
        doc_type: 文档类型
        
    Returns:
        完整的检查结果
    """
    checker = DocumentCodeChecker()
    results = checker.check_all(markdown_content, doc_type)
    
    return results


if __name__ == "__main__":
    # 测试代码
    test_markdown = """
# Test Project

This is a test.

## Installation

Install it:

```
pip install test
```

## Usage

Use it:

```python
import test
```

## Features

-Feature 1 without space
- Feature 2

Check out [Google](https://www.google.com) and [Invalid Link](https://invalid-url-12345.com).

Bad link: [unclosed link

Empty link: [text]()

Table without proper format:
| Header 1 | Header 2
| --- | ---
| Cell 1 | Cell 2 |

>Quote without space
"""
    
    results = check_document_quality(test_markdown, "readme")
    
    print("=== 检查结果汇总 ===")
    print(f"总检查项: {results['summary']['total_checks']}")
    print(f"通过: {results['summary']['passed_checks']}")
    print(f"失败: {results['summary']['failed_checks']}")
    print(f"总问题数: {results['summary']['total_issues']}")
    
    if results['summary']['all_issues']:
        print("\n发现的问题:")
        for issue in results['summary']['all_issues']:
            print(f"  - {issue}")
    
    print("\n=== Markdown 语法检查详情 ===")
    md_check = results['markdown_syntax_check']
    print(f"解析成功: {md_check['parse_success']}")
    print(f"错误数: {md_check['total_issues']}")
    print(f"警告数: {md_check['total_warnings']}")
    
    if md_check['issues']:
        print("\n错误列表:")
        for issue in md_check['issues']:
            print(f"  [{issue['severity']}] {issue['message']}")
    
    if md_check['warnings']:
        print("\n警告列表:")
        for warning in md_check['warnings']:
            print(f"  [{warning['severity']}] {warning['message']}")

