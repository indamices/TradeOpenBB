"""
Strategy extraction service
从聊天消息中自动识别和提取策略代码
"""

import re
import logging
from typing import Optional, Dict, List, Tuple

logger = logging.getLogger(__name__)


def extract_python_code_blocks(content: str) -> List[str]:
    """
    从文本中提取所有Python代码块
    
    Args:
        content: 包含代码块的文本
        
    Returns:
        提取出的Python代码列表
    """
    # 匹配 ```python ... ``` 格式
    pattern = r'```python\s*\n(.*?)```'
    matches = re.findall(pattern, content, re.DOTALL)
    
    # 如果没有找到，尝试匹配 ``` ... ``` (无语言标识)
    if not matches:
        pattern = r'```\s*\n(.*?)```'
        matches = re.findall(pattern, content, re.DOTALL)
    
    return matches


def validate_strategy_code(code: str) -> Tuple[bool, Optional[str]]:
    """
    验证代码是否包含策略逻辑函数
    
    Args:
        code: 待验证的Python代码
        
    Returns:
        (is_valid, error_message)
    """
    if not code or not code.strip():
        return False, "代码为空"
    
    # 检查是否包含strategy_logic函数定义
    if 'def strategy_logic' not in code:
        return False, "代码不包含strategy_logic函数"
    
    # 尝试检查语法（基本检查）
    try:
        compile(code, '<string>', 'exec')
    except SyntaxError as e:
        return False, f"代码语法错误: {str(e)}"
    except Exception as e:
        logger.warning(f"代码编译检查失败: {str(e)}")
        # 继续执行，因为可能只是缺少导入
    
    return True, None


def extract_strategy_name(code: str, content: str = "") -> str:
    """
    从代码或消息内容中提取策略名称
    
    优先顺序：
    1. 代码注释中的 # Strategy: xxx
    2. 函数文档字符串
    3. 消息内容中的策略描述
    4. 默认名称
    """
    # 1. 从代码注释中提取
    name_pattern = r'#\s*Strategy[:\s]+(.+)'
    match = re.search(name_pattern, code, re.IGNORECASE | re.MULTILINE)
    if match:
        name = match.group(1).strip()
        # 移除可能的换行和注释标记
        name = re.sub(r'\s*#.*', '', name)
        name = name.strip()
        if name:
            return name
    
    # 2. 从函数文档字符串中提取
    docstring_pattern = r'def\s+strategy_logic[^:]*:\s*"""(.*?)"""'
    match = re.search(docstring_pattern, code, re.DOTALL)
    if match:
        docstring = match.group(1).strip()
        # 取第一行作为名称
        first_line = docstring.split('\n')[0].strip()
        if first_line:
            return first_line
    
    # 3. 从消息内容中提取（如果有的话）
    if content:
        # 尝试从"创建一个XXX策略"这样的描述中提取
        name_pattern = r'创建(?:一个)?([^，,。.\n]+?)策略'
        match = re.search(name_pattern, content, re.IGNORECASE)
        if match:
            return match.group(1).strip()
    
    # 4. 默认名称
    return "Extracted Strategy"


def extract_strategy_description(code: str, content: str = "") -> Optional[str]:
    """
    从代码或消息内容中提取策略描述
    """
    # 1. 从函数文档字符串中提取完整描述
    docstring_pattern = r'def\s+strategy_logic[^:]*:\s*"""(.*?)"""'
    match = re.search(docstring_pattern, code, re.DOTALL)
    if match:
        docstring = match.group(1).strip()
        if len(docstring) > 50:  # 只有较长的描述才保留
            return docstring
    
    # 2. 从消息内容中提取描述
    if content:
        # 取消息的前200个字符作为描述
        description = content[:200].strip()
        # 移除代码块
        description = re.sub(r'```.*?```', '', description, flags=re.DOTALL)
        description = description.strip()
        if description and len(description) > 20:
            return description
    
    return None


def extract_strategy_from_message(message_content: str, code_snippets: Optional[Dict[str, str]] = None) -> Optional[Dict[str, str]]:
    """
    从消息中提取策略代码
    
    Args:
        message_content: 消息内容
        code_snippets: 已有的代码片段字典（如果有）
        
    Returns:
        策略信息字典，包含：
        - code: 策略代码
        - name: 策略名称
        - description: 策略描述
        如果无法提取，返回None
    """
    try:
        # 1. 优先使用已有的code_snippets
        python_code = None
        if code_snippets and 'python' in code_snippets:
            python_code = code_snippets['python']
        
        # 2. 如果code_snippets中没有，从消息内容中提取
        if not python_code:
            code_blocks = extract_python_code_blocks(message_content)
            if code_blocks:
                python_code = code_blocks[0]  # 取第一个代码块
        
        # 3. 如果没有找到代码，返回None
        if not python_code:
            return None
        
        # 4. 验证代码
        is_valid, error_msg = validate_strategy_code(python_code)
        if not is_valid:
            logger.info(f"策略代码验证失败: {error_msg}")
            return None
        
        # 5. 提取策略信息
        name = extract_strategy_name(python_code, message_content)
        description = extract_strategy_description(python_code, message_content)
        
        return {
            'code': python_code,
            'name': name,
            'description': description
        }
        
    except Exception as e:
        logger.error(f"提取策略时发生错误: {str(e)}", exc_info=True)
        return None


def auto_extract_strategies_from_message(message_content: str, code_snippets: Optional[Dict[str, str]] = None) -> List[Dict[str, str]]:
    """
    从消息中自动提取所有策略代码（可能包含多个策略）
    
    Args:
        message_content: 消息内容
        code_snippets: 已有的代码片段字典
        
    Returns:
        策略信息列表
    """
    strategies = []
    
    try:
        # 1. 如果有code_snippets，直接使用
        if code_snippets and 'python' in code_snippets:
            strategy = extract_strategy_from_message(
                message_content,
                code_snippets
            )
            if strategy:
                strategies.append(strategy)
        
        # 2. 从消息内容中提取所有代码块
        code_blocks = extract_python_code_blocks(message_content)
        for code_block in code_blocks:
            # 跳过已经在code_snippets中处理过的
            if code_snippets and code_snippets.get('python') == code_block:
                continue
            
            strategy = extract_strategy_from_message(
                message_content,
                {'python': code_block}
            )
            if strategy:
                strategies.append(strategy)
        
        # 3. 去重（基于代码内容的hash）
        seen_codes = set()
        unique_strategies = []
        for strategy in strategies:
            code_hash = hash(strategy['code'])
            if code_hash not in seen_codes:
                seen_codes.add(code_hash)
                unique_strategies.append(strategy)
        
        return unique_strategies
        
    except Exception as e:
        logger.error(f"自动提取策略时发生错误: {str(e)}", exc_info=True)
        return []