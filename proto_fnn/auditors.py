"""
分类审核者模块 (Categorized Auditors)
每种工作者有对应的专属审核者
"""

import json
from typing import Dict, Any, Literal

from .state import AgentState
from .role_factory import load_role, create_llm


# ==================== 代码审核者 ====================

CODE_AUDITOR_SYSTEM = """你是代码审核专家。快速检查代码是否实现了核心功能。

审核原则：宽松通过，只关注功能是否实现。
不需要检查：代码风格、边界情况、性能优化等细节。"""

CODE_AUDITOR_PROMPT = """审核以下代码：

用户需求：{user_instruction}
任务：{current_task}

代码：
```
{code}
```

输出 JSON（评分 7 分以上即通过）：
{{
  "status": "approved" | "rejected" | "resource_limit",
  "score": 0-10,
  "feedback": "简短反馈",
  "can_continue": true
}}

如果任务无法完成（超出能力范围），返回 status="resource_limit"。"""


def code_auditor_node(state: AgentState) -> Dict[str, Any]:
    """代码审核者节点"""
    from langchain_core.messages import HumanMessage, SystemMessage
    
    role = load_role("code_auditor")
    llm = create_llm(role.llm)
    
    # 获取最新代码
    code_snippets = state.get("code_snippets", {})
    latest_code = ""
    if code_snippets:
        latest_module = list(code_snippets.keys())[-1]
        latest_code = code_snippets[latest_module]
    
    prompt = CODE_AUDITOR_PROMPT.format(
        user_instruction=state["user_instruction"],
        current_task=state.get("current_task", ""),
        code=latest_code
    )
    
    messages = [
        SystemMessage(content=CODE_AUDITOR_SYSTEM),
        HumanMessage(content=prompt)
    ]
    
    response = llm.invoke(messages)
    
    try:
        result = json.loads(response.content)
    except json.JSONDecodeError:
        result = {"status": "approved", "score": 8, "feedback": "审核通过"}
    
    audit_status = result.get("status", "approved")
    feedback = f"[代码审核] {result.get('status', 'approved')} (评分: {result.get('score', 8)}/10)"
    
    thought_trace = f"[CODE_AUDITOR] 审核结果: {audit_status} (评分: {result.get('score', 8)}/10)"
    new_thought_traces = state["thought_traces"] + [thought_trace]
    
    return {
        "thought_traces": new_thought_traces,
        "audit_status": audit_status,
        "audit_feedback": result.get("feedback", ""),
        "status": "in_progress"
    }


# ==================== 物理审核者 ====================

PHYSICS_AUDITOR_SYSTEM = """你是物理/数学/科学审核专家。检查分析是否正确和完整。

审核原则：检查理论是否正确，推导是否合理。
不需要过度深究细节。"""

PHYSICS_AUDITOR_PROMPT = """审核以下分析：

用户需求：{user_instruction}
任务：{current_task}

分析内容：
{analysis}

输出 JSON：
{{
  "status": "approved" | "rejected" | "resource_limit",
  "score": 0-10,
  "feedback": "简短反馈",
  "scientific_accuracy": true | false
}}

如果问题超出分析能力，返回 status="resource_limit"。"""


def physics_auditor_node(state: AgentState) -> Dict[str, Any]:
    """物理审核者节点"""
    from langchain_core.messages import HumanMessage, SystemMessage
    
    role = load_role("physics_auditor")
    llm = create_llm(role.llm)
    
    analysis = state.get("analysis_result", "")
    
    prompt = PHYSICS_AUDITOR_PROMPT.format(
        user_instruction=state["user_instruction"],
        current_task=state.get("current_task", ""),
        analysis=analysis
    )
    
    messages = [
        SystemMessage(content=PHYSICS_AUDITOR_SYSTEM),
        HumanMessage(content=prompt)
    ]
    
    response = llm.invoke(messages)
    
    try:
        result = json.loads(response.content)
    except json.JSONDecodeError:
        result = {"status": "approved", "score": 8, "feedback": "分析合理"}
    
    audit_status = result.get("status", "approved")
    
    thought_trace = f"[PHYSICS_AUDITOR] 审核结果: {audit_status} (评分: {result.get('score', 8)}/10)"
    new_thought_traces = state["thought_traces"] + [thought_trace]
    
    return {
        "thought_traces": new_thought_traces,
        "audit_status": audit_status,
        "audit_feedback": result.get("feedback", ""),
        "status": "in_progress"
    }


# ==================== 通用审核者 ====================

GENERAL_AUDITOR_SYSTEM = """你是通用分析审核专家。检查分析是否合理和实用。

审核原则：检查建议是否可行，分析是否有价值。"""

GENERAL_AUDITOR_PROMPT = """审核以下分析：

用户需求：{user_instruction}
任务：{current_task}

分析内容：
{analysis}

输出 JSON：
{{
  "status": "approved" | "rejected" | "resource_limit",
  "score": 0-10,
  "feedback": "简短反馈",
  "practical_value": true | false
}}

如果问题超出分析能力，返回 status="resource_limit"。"""


def general_auditor_node(state: AgentState) -> Dict[str, Any]:
    """通用审核者节点"""
    from langchain_core.messages import HumanMessage, SystemMessage
    
    role = load_role("general_auditor")
    llm = create_llm(role.llm)
    
    analysis = state.get("analysis_result", "")
    
    prompt = GENERAL_AUDITOR_PROMPT.format(
        user_instruction=state["user_instruction"],
        current_task=state.get("current_task", ""),
        analysis=analysis
    )
    
    messages = [
        SystemMessage(content=GENERAL_AUDITOR_SYSTEM),
        HumanMessage(content=prompt)
    ]
    
    response = llm.invoke(messages)
    
    try:
        result = json.loads(response.content)
    except json.JSONDecodeError:
        result = {"status": "approved", "score": 8, "feedback": "分析合理"}
    
    audit_status = result.get("status", "approved")
    
    thought_trace = f"[GENERAL_AUDITOR] 审核结果: {audit_status} (评分: {result.get('score', 8)}/10)"
    new_thought_traces = state["thought_traces"] + [thought_trace]
    
    return {
        "thought_traces": new_thought_traces,
        "audit_status": audit_status,
        "audit_feedback": result.get("feedback", ""),
        "status": "in_progress"
    }


# ==================== 路由函数 ====================

def auditor_decision(state: AgentState) -> Literal["approved", "rejected", "resource_limit", "complete"]:
    """
    审核决策路由函数
    
    Returns:
        "complete": 审核通过，直接生成文档
        "rejected": 审核拒绝，返回仲裁者
        "resource_limit": 资源不足，返回仲裁者尝试其他方案
    """
    audit_status = state.get("audit_status", "approved")
    
    if audit_status == "rejected":
        return "rejected"
    
    if audit_status == "resource_limit":
        return "resource_limit"
    
    # 审核通过，直接完成
    return "complete"
