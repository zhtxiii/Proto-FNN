"""
通用工作者节点 (General Worker Node)
处理代码和物理之外的其他问题
"""

import json
from typing import Dict, Any

from .state import AgentState
from .prompts import GENERAL_WORKER_SYSTEM, GENERAL_WORKER_TASK
from .role_factory import load_role, create_llm

# 加载角色配置
ROLE = load_role("general_worker")


def create_general_llm():
    """创建通用工作者使用的 LLM"""
    return create_llm(ROLE.llm)


def general_worker_node(state: AgentState) -> Dict[str, Any]:
    """
    通用工作者节点 - 处理一般性问题
    
    提供分析、建议和解答
    """
    from langchain_core.messages import HumanMessage, SystemMessage
    
    llm = create_general_llm()
    
    # 构建提示词
    system_prompt = GENERAL_WORKER_SYSTEM.format(
        user_instruction=state["user_instruction"]
    )
    
    task_prompt = GENERAL_WORKER_TASK.format(
        current_task=state.get("current_task", state["user_instruction"])
    )
    
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=task_prompt)
    ]
    
    response = llm.invoke(messages)
    
    # 解析响应
    try:
        result = json.loads(response.content)
    except json.JSONDecodeError:
        result = {
            "topic": "通用分析",
            "analysis": response.content,
            "recommendations": [],
            "status": "completed"
        }
    
    # 保存分析结果到文件
    _save_analysis_to_file(result)
    
    # 记录思考路径
    topic = result.get("topic", "未知主题")
    thought_trace = f"[GENERAL] 完成分析 '{topic}': {result.get('summary', '')[:100]}"
    new_thought_traces = state["thought_traces"] + [thought_trace]
    
    # 增加递归深度
    new_depth = state["recursion_depth"] + 1
    
    return {
        "analysis_result": result.get("analysis", ""),
        "thought_traces": new_thought_traces,
        "recursion_depth": new_depth,
        "status": "pending_audit"
    }


def _save_analysis_to_file(result: Dict):
    """保存分析结果到项目目录"""
    from pathlib import Path
    import builtins
    
    output_dir = getattr(builtins, '_proto_fnn_project_dir', None)
    if not output_dir:
        output_dir = Path(__file__).parent.parent / "output"
    output_dir.mkdir(exist_ok=True)
    
    # 保存为 Markdown 文件
    topic = result.get("topic", "analysis")
    import re
    filename = re.sub(r'[^\w\u4e00-\u9fff]', '_', topic)[:30]
    
    # 构建建议列表
    recommendations = result.get("recommendations", [])
    rec_text = "\n".join(f"- {r}" for r in recommendations) if recommendations else "无"
    
    content = f"""# {result.get('topic', '分析报告')}

## 分析内容

{result.get('analysis', '')}

## 建议

{rec_text}

## 总结

{result.get('summary', '')}
"""
    
    file_path = output_dir / f"{filename}.md"
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)
    
    print(f"  📝 分析报告已保存到: {file_path}")
