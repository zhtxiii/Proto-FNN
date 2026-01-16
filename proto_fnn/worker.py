"""
工作者节点 (Worker Node)
ReAct 风格的任务执行 Agent

注意：为了兼容 Python 3.14，langchain 导入在函数内部进行
"""

import json
from typing import Dict, Any

from .state import AgentState
from .prompts import WORKER_SYSTEM, WORKER_TASK
from .tools import WORKER_TOOLS
from .role_factory import load_role, create_llm

# 加载角色配置
ROLE = load_role("worker")


def create_worker_llm():
    """创建工作者使用的 LLM（基于角色配置）"""
    return create_llm(ROLE.llm)


def worker_node(state: AgentState) -> Dict[str, Any]:
    """
    工作者节点 - ReAct 执行逻辑
    
    1. 接收仲裁者分配的子任务
    2. 读取黑板了解背景
    3. 使用工具完成任务
    4. 将结果写入黑板
    """
    from langchain_core.messages import HumanMessage, SystemMessage
    
    llm = create_worker_llm()
    
    # 构建系统提示词
    system_prompt = WORKER_SYSTEM.format(
        user_instruction=state["user_instruction"],
        current_task=state["current_task"],
        code_snippets=json.dumps(state["code_snippets"], ensure_ascii=False, indent=2)
    )
    
    # 构建任务提示词
    task_prompt = WORKER_TASK.format(
        current_task=state["current_task"]
    )
    
    # 调用 LLM 执行任务
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=task_prompt)
    ]
    
    response = llm.invoke(messages)
    
    # 解析响应
    try:
        result = json.loads(response.content)
    except json.JSONDecodeError:
        # 如果解析失败，返回错误状态
        result = {
            "module_name": "error",
            "code": "",
            "description": "执行失败：无法解析响应",
            "status": "need_help"
        }
    
    # 更新代码片段
    new_code_snippets = state["code_snippets"].copy()
    if result.get("code"):
        module_name = result.get("module_name", "unnamed")
        new_code_snippets[module_name] = result["code"]
        
        # 保存代码到文件
        _save_code_to_file(module_name, result["code"])
    
    # 记录思考路径
    thought_trace = f"[WORKER] 完成模块 '{result.get('module_name', 'unknown')}': {result.get('description', '')}"
    new_thought_traces = state["thought_traces"] + [thought_trace]
    
    # 增加递归深度
    new_depth = state["recursion_depth"] + 1
    
    return {
        "code_snippets": new_code_snippets,
        "thought_traces": new_thought_traces,
        "recursion_depth": new_depth,
        "status": "pending_audit"  # 等待审核
    }


def _save_code_to_file(module_name: str, code: str):
    """保存代码到项目输出目录"""
    from pathlib import Path
    import builtins
    
    # 获取项目输出目录
    output_dir = getattr(builtins, '_proto_fnn_project_dir', None)
    if not output_dir:
        output_dir = Path(__file__).parent.parent / "output"
    output_dir.mkdir(exist_ok=True)
    
    # 确定文件扩展名
    if "import" in code or "def " in code or "class " in code:
        ext = ".py"
    elif "<html" in code.lower() or "<!doctype" in code.lower():
        ext = ".html"
    elif "function" in code or "const " in code or "let " in code:
        ext = ".js"
    else:
        ext = ".py"  # 默认 Python
    
    # 保存文件
    file_path = output_dir / f"{module_name}{ext}"
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(code)
    
    print(f"  💾 代码已保存到: {file_path}")


def create_react_worker(state: AgentState):
    """
    创建 ReAct 风格的工作者 Agent（可选的更复杂实现）
    使用 LangGraph 的 prebuilt ReAct agent
    """
    import os
    from langchain_openai import ChatOpenAI
    from langgraph.prebuilt import create_react_agent
    
    llm = ChatOpenAI(
        model=project_config.model,
        temperature=0.3,
        openai_api_key=project_config.api_key,
        openai_api_base=project_config.base_url
    )
    
    # 创建 ReAct Agent
    react_agent = create_react_agent(
        llm,
        tools=WORKER_TOOLS,
        state_modifier=WORKER_SYSTEM.format(
            user_instruction=state["user_instruction"],
            current_task=state["current_task"],
            code_snippets=json.dumps(state["code_snippets"], ensure_ascii=False)
        )
    )
    
    return react_agent
