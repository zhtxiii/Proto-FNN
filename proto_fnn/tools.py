"""
工具定义 (Tools)
供 Worker Agent 使用的工具集

注意：为了兼容 Python 3.14，langchain 导入在函数内部进行
"""

import sys
from io import StringIO
from typing import Dict, Any, List, Callable


def execute_python(code: str) -> str:
    """
    执行 Python 代码并返回结果。
    
    Args:
        code: 要执行的 Python 代码
        
    Returns:
        代码执行的输出结果或错误信息
    """
    # 捕获标准输出
    old_stdout = sys.stdout
    sys.stdout = captured_output = StringIO()
    
    try:
        # 创建执行环境
        exec_globals: Dict[str, Any] = {}
        exec_locals: Dict[str, Any] = {}
        
        # 执行代码
        exec(code, exec_globals, exec_locals)
        
        # 获取输出
        output = captured_output.getvalue()
        
        # 如果没有打印输出，尝试获取最后一个表达式的值
        if not output and exec_locals:
            last_value = list(exec_locals.values())[-1]
            if last_value is not None:
                output = str(last_value)
        
        return output if output else "代码执行成功，无输出"
        
    except Exception as e:
        return f"执行错误: {type(e).__name__}: {str(e)}"
    finally:
        sys.stdout = old_stdout


def write_code(module_name: str, code: str, description: str) -> str:
    """
    保存代码片段到指定模块。
    
    Args:
        module_name: 模块名称（如 snake_game, movement 等）
        code: 代码内容
        description: 代码功能描述
        
    Returns:
        保存结果消息
    """
    # 这个工具实际上是通过状态更新来工作的
    # 返回确认信息，实际保存由图节点处理
    return f"代码已准备保存到模块 '{module_name}': {description}"


def read_file(file_path: str) -> str:
    """
    读取文件内容。
    
    Args:
        file_path: 文件路径
        
    Returns:
        文件内容或错误信息
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        return f"文件不存在: {file_path}"
    except Exception as e:
        return f"读取错误: {str(e)}"


def get_worker_tools() -> List:
    """
    获取工作者工具列表（延迟导入版本）
    
    Returns:
        LangChain 工具列表
    """
    from langchain_core.tools import tool
    
    @tool
    def execute_python_tool(code: str) -> str:
        """执行 Python 代码并返回结果"""
        return execute_python(code)
    
    @tool
    def write_code_tool(module_name: str, code: str, description: str) -> str:
        """保存代码片段到指定模块"""
        return write_code(module_name, code, description)
    
    @tool
    def read_file_tool(file_path: str) -> str:
        """读取文件内容"""
        return read_file(file_path)
    
    return [execute_python_tool, write_code_tool, read_file_tool]


# 简单的工具描述列表（不依赖 LangChain）
WORKER_TOOLS_SIMPLE = [
    {
        "name": "execute_python",
        "description": "执行 Python 代码并返回结果",
        "function": execute_python
    },
    {
        "name": "write_code", 
        "description": "保存代码片段到指定模块",
        "function": write_code
    },
    {
        "name": "read_file",
        "description": "读取文件内容",
        "function": read_file
    }
]

# 工具列表（延迟加载，避免导入时问题）
WORKER_TOOLS = WORKER_TOOLS_SIMPLE
