"""
全局黑板 (Global Blackboard) - AgentState 定义
所有 Agent 共享的状态区，作为唯一真实数据源
"""

from typing import TypedDict, Dict, List, Any, Optional


class AgentState(TypedDict):
    """Proto-FNN 全局黑板结构"""
    
    # 用户的原始需求（只读）
    user_instruction: str
    
    # 当前的任务状态 (pending/in_progress/completed/failed)
    status: str
    
    # 已生成的代码片段（不同子 Agent 贡献）
    # key: 模块名, value: 代码内容
    code_snippets: Dict[str, str]
    
    # 分析结果（物理/通用工作者的输出）
    analysis_result: str
    
    # 最终文档内容
    documentation: str
    
    # MCTS 的思考路径记录（用于调试和回溯）
    thought_traces: List[str]
    
    # 当前递归深度（防止死循环，最大=2）
    recursion_depth: int
    
    # 当前正在处理的子任务
    current_task: str
    
    # 工作者类型 (code/physics/general)
    worker_type: str
    
    # 审核反馈（来自 Auditor）
    audit_feedback: str
    
    # 审核状态 (None/approved/rejected)
    audit_status: Optional[str]
    
    # 消息历史（简化版本，避免 Python 3.14 兼容性问题）
    messages: List[Any]


def create_initial_state(user_instruction: str) -> AgentState:
    """创建初始状态"""
    return AgentState(
        user_instruction=user_instruction,
        status="pending",
        code_snippets={},
        analysis_result="",
        documentation="",
        thought_traces=[],
        recursion_depth=0,
        current_task="",
        worker_type="code",
        audit_feedback="",
        audit_status=None,
        messages=[]
    )

