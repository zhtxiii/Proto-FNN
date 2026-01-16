"""
仲裁者节点 (Arbitrator Node)
具有 Lite-MCTS 规划能力的核心决策节点

注意：为了兼容 Python 3.14，langchain 导入在函数内部进行
"""

import json
from typing import Dict, Any, Literal

from .state import AgentState
from .prompts import ARBITRATOR_MCTS_SYSTEM, ARBITRATOR_MCTS_PLAN
from .role_factory import load_role, create_llm

# 加载角色配置
ROLE = load_role("arbitrator")

# 从角色配置获取最大递归深度
MAX_RECURSION_DEPTH = ROLE.limits.get("max_recursion_depth", 2)


def create_arbitrator_llm():
    """创建仲裁者使用的 LLM（基于角色配置）"""
    return create_llm(ROLE.llm)


def arbitrator_node(state: AgentState) -> Dict[str, Any]:
    """
    仲裁者节点 - 核心决策逻辑
    
    1. 读取全局黑板
    2. 使用 Lite-MCTS 生成多方案并评估
    3. 选择最佳方案并决定下一步行动
    """
    from langchain_core.messages import HumanMessage, SystemMessage
    
    llm = create_arbitrator_llm()
    
    # 构建系统提示词
    system_prompt = ARBITRATOR_MCTS_SYSTEM.format(
        user_instruction=state["user_instruction"],
        status=state["status"],
        code_snippets=json.dumps(state["code_snippets"], ensure_ascii=False, indent=2),
        recursion_depth=state["recursion_depth"],
        audit_feedback=state.get("audit_feedback", "无")
    )
    
    # 调用 LLM 进行 MCTS 规划
    import time
    start_time = time.time()
    
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=ARBITRATOR_MCTS_PLAN)
    ]
    
    response = llm.invoke(messages)
    duration_ms = int((time.time() - start_time) * 1000)
    
    # 记录到追踪器
    from .execution_tracer import get_tracer
    tracer = get_tracer()
    if tracer:
        tracer.record_llm_call(
            role="仲裁者",
            prompt=system_prompt + "\n\n" + ARBITRATOR_MCTS_PLAN,
            response=response.content,
            model=ROLE.llm.model or "deepseek-chat",
            temperature=ROLE.llm.temperature,
            duration_ms=duration_ms
        )
    
    # 解析 LLM 响应
    try:
        result = json.loads(response.content)
    except json.JSONDecodeError:
        # 如果解析失败，使用默认行为
        result = {
            "plans": [],
            "selected_plan_id": 0,
            "action": "complete",
            "subtask": "",
            "reasoning": "解析失败，默认完成"
        }
    
    # 记录生成的方案到追踪器
    if tracer and result.get("plans"):
        tracer.record_plans(result["plans"])
        tracer.record_thinking(
            thinking=f"生成了 {len(result.get('plans', []))} 个方案",
            decision=result.get("action", ""),
            reasoning=result.get("reasoning", "")
        )
    
    # 记录思考路径
    thought_trace = f"[MCTS] 生成 {len(result.get('plans', []))} 个方案, " \
                    f"选择方案 {result.get('selected_plan_id')}: {result.get('reasoning', '')}"
    
    new_thought_traces = state["thought_traces"] + [thought_trace]
    
    # 检查是否需要生成文档（如果代码已完成且审核通过）
    action = result.get("action", "complete")
    subtask = result.get("subtask", "")
    
    # 如果审核被拒绝，需要重新处理
    if state.get("audit_status") == "rejected":
        audit_feedback = state.get("audit_feedback", "")
        subtask = f"修复问题: {audit_feedback}. 原任务: {state.get('current_task', '')}"
        action = "delegate"
    
    # 检查递归深度
    if state["recursion_depth"] >= MAX_RECURSION_DEPTH:
        thought_trace_limit = f"[LIMIT] 达到最大递归深度 {MAX_RECURSION_DEPTH}，强制结束"
        new_thought_traces.append(thought_trace_limit)
        action = "complete"
    
    # 获取工作者类型（默认为 code）
    worker_type = result.get("worker_type", "code")
    
    # 更新状态
    updates = {
        "thought_traces": new_thought_traces,
        "status": "in_progress" if action == "delegate" else "completed",
        "current_task": subtask if action == "delegate" else "",
        "worker_type": worker_type if action == "delegate" else "",
        "audit_status": None,  # 重置审核状态
        "audit_feedback": ""   # 重置审核反馈
    }
    
    return updates


def should_delegate(state: AgentState) -> Literal["code_worker", "physics_worker", "general_worker", "doc_generator", "end"]:
    """
    路由函数：决定下一步走向
    
    Returns:
        "code_worker": 分配任务给编码工作者
        "physics_worker": 分配任务给物理工作者
        "general_worker": 分配任务给通用工作者
        "doc_generator": 生成文档
        "end": 结束流程
    """
    status = state.get("status", "pending")
    code_snippets = state.get("code_snippets", {})
    analysis_result = state.get("analysis_result", "")
    documentation = state.get("documentation", "")
    current_task = state.get("current_task", "")
    worker_type = state.get("worker_type", "code")
    
    if status == "completed":
        # 检查是否需要生成文档
        if (code_snippets or analysis_result) and not documentation:
            return "doc_generator"
        return "end"
    
    if current_task:
        # 根据工作者类型路由
        if worker_type == "physics":
            return "physics_worker"
        elif worker_type == "general":
            return "general_worker"
        else:
            return "code_worker"
    
    return "end"
