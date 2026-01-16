"""
图结构组装 (Graph Assembly)
使用 LangGraph 将所有节点连接成有向图

注意：为了兼容 Python 3.14，使用延迟导入
所有 langgraph/langchain 导入都在函数内部进行
"""

from typing import Literal, Dict, Any

from .state import AgentState, create_initial_state
from .prompts import DOC_GENERATOR
from .role_factory import load_role, create_llm

# 加载文档生成器角色配置
DOC_ROLE = load_role("doc_generator")


def doc_generator_node(state: AgentState) -> Dict[str, Any]:
    """
    文档生成节点
    在所有代码完成后生成项目文档
    """
    import json
    from langchain_core.messages import HumanMessage
    
    # 使用角色工厂创建 LLM
    llm = create_llm(DOC_ROLE.llm)
    
    # 构建提示词
    prompt = DOC_GENERATOR.format(
        user_instruction=state["user_instruction"],
        code_snippets=json.dumps(state["code_snippets"], ensure_ascii=False, indent=2)
    )
    
    messages = [
        HumanMessage(content=prompt)
    ]
    
    response = llm.invoke(messages)
    
    # 保存文档到项目输出目录
    from pathlib import Path
    import builtins
    
    output_dir = getattr(builtins, '_proto_fnn_project_dir', None)
    if not output_dir:
        output_dir = Path(__file__).parent.parent / "output"
    output_dir.mkdir(exist_ok=True)
    
    doc_path = output_dir / "README.md"
    with open(doc_path, "w", encoding="utf-8") as f:
        f.write(response.content)
    print(f"  📄 文档已保存到: {doc_path}")
    
    # 记录思考路径
    thought_trace = "[DOC] 生成项目文档完成"
    new_thought_traces = state["thought_traces"] + [thought_trace]
    
    return {
        "documentation": response.content,
        "thought_traces": new_thought_traces,
        "status": "completed"
    }


def build_graph():
    """
    构建 Proto-FNN 的状态图
    
    图结构：
    Start → Arbitrator
    Arbitrator → [拆解] → Worker
    Arbitrator → [生成文档] → DocGenerator → End
    Arbitrator → [结束] → End
    Worker → Auditor
    Auditor → [通过] → Arbitrator
    Auditor → [不通过] → Arbitrator (带错误反馈)
    """
    # 延迟导入 LangGraph
    from langgraph.graph import StateGraph, END
    
    # 延迟导入节点函数
    from .arbitrator import arbitrator_node, should_delegate
    from .worker import worker_node
    from .physics_worker import physics_worker_node
    from .general_worker import general_worker_node
    from .auditors import (
        code_auditor_node, 
        physics_auditor_node, 
        general_auditor_node,
        auditor_decision
    )
    
    # 创建状态图
    graph = StateGraph(AgentState)
    
    # 添加节点
    graph.add_node("arbitrator", arbitrator_node)
    graph.add_node("code_worker", worker_node)
    graph.add_node("physics_worker", physics_worker_node)
    graph.add_node("general_worker", general_worker_node)
    graph.add_node("code_auditor", code_auditor_node)
    graph.add_node("physics_auditor", physics_auditor_node)
    graph.add_node("general_auditor", general_auditor_node)
    graph.add_node("doc_generator", doc_generator_node)
    
    # 设置入口点
    graph.set_entry_point("arbitrator")
    
    # 添加条件边：仲裁者决定下一步
    graph.add_conditional_edges(
        "arbitrator",
        should_delegate,
        {
            "code_worker": "code_worker",
            "physics_worker": "physics_worker",
            "general_worker": "general_worker",
            "doc_generator": "doc_generator",
            "end": END
        }
    )
    
    # 每种工作者有对应的专属审核者
    graph.add_edge("code_worker", "code_auditor")
    graph.add_edge("physics_worker", "physics_auditor")
    graph.add_edge("general_worker", "general_auditor")
    
    # 所有审核者共用同一个决策函数，结果提交给仲裁者
    for auditor in ["code_auditor", "physics_auditor", "general_auditor"]:
        graph.add_conditional_edges(
            auditor,
            auditor_decision,
            {
                "complete": "doc_generator",  # 审核通过，生成文档
                "rejected": "arbitrator",     # 审核拒绝，返回仲裁者
                "resource_limit": "arbitrator"  # 资源不足，返回仲裁者尝试其他方案
            }
        )
    
    # 文档生成完成后结束
    graph.add_edge("doc_generator", END)
    
    return graph


def compile_graph():
    """编译图结构，准备执行"""
    graph = build_graph()
    return graph.compile()


def run_proto_fnn(user_instruction: str, verbose: bool = True, 
                   enable_trace: bool = True) -> AgentState:
    """
    运行 Proto-FNN 系统
    
    Args:
        user_instruction: 用户的原始需求
        verbose: 是否打印执行过程
        enable_trace: 是否启用执行追踪
        
    Returns:
        最终的 AgentState
    """
    from .execution_tracer import init_tracer, get_tracer
    from .role_factory import load_role
    from pathlib import Path
    import re
    from datetime import datetime
    
    # 创建项目专用输出目录
    base_output = Path(__file__).parent.parent / "output"
    base_output.mkdir(exist_ok=True)
    
    # 生成项目目录名（时间戳 + 任务关键词）
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    # 提取任务关键词（取前10个字符，移除特殊字符）
    task_keyword = re.sub(r'[^\w\u4e00-\u9fff]', '', user_instruction)[:10]
    project_dir = base_output / f"{timestamp}_{task_keyword}"
    project_dir.mkdir(exist_ok=True)
    
    # 保存项目目录到全局变量供其他模块使用
    import builtins
    builtins._proto_fnn_project_dir = project_dir
    
    # 初始化追踪器
    tracer = None
    if enable_trace:
        tracer = init_tracer(user_instruction)
        tracer.project_dir = project_dir  # 传递项目目录给追踪器
        print(f"📂 项目输出目录: {project_dir}")
        print("📊 执行追踪已启用")
    
    # 创建初始状态
    initial_state = create_initial_state(user_instruction)
    
    # 编译并运行图
    app = compile_graph()
    
    if verbose:
        print("=" * 60)
        print("Proto-FNN v0.1 启动")
        print(f"用户需求: {user_instruction}")
        print("=" * 60)
    
    # 角色显示名称映射
    role_names = {
        "arbitrator": "仲裁者",
        "code_worker": "编码工作者",
        "physics_worker": "物理工作者",
        "general_worker": "通用工作者",
        "code_auditor": "代码审核者",
        "physics_auditor": "物理审核者",
        "general_auditor": "通用审核者",
        "doc_generator": "文档生成器"
    }
    
    # 执行图
    final_state = None
    accumulated_state = initial_state.copy()
    
    for step, state in enumerate(app.stream(initial_state)):
        node_name = list(state.keys())[0]
        node_state = state[node_name]
        
        # 在更新前保存旧状态用于比较
        prev_accumulated = accumulated_state.copy()
        
        # 更新累积状态
        accumulated_state.update(node_state)
        
        if verbose:
            print(f"\n[Step {step + 1}] 节点: {node_name}")
            
            # 打印最新的思考路径
            if "thought_traces" in node_state:
                traces = node_state["thought_traces"]
                if traces:
                    print(f"  思考: {traces[-1]}")
        
        # 记录到追踪器（不在中间保存 HTML）
        if tracer:
            display_name = role_names.get(node_name, node_name)
            step_obj = tracer.start_step(node_name, display_name, accumulated_state)
            
            # 记录思考路径
            if "thought_traces" in node_state and node_state["thought_traces"]:
                latest_trace = node_state["thought_traces"][-1]
                tracer.record_thinking(latest_trace)
            
            # 记录黑板变动（使用更新前的状态比较）
            for key, new_val in node_state.items():
                old_val = prev_accumulated.get(key)
                if key in ["status", "audit_status", "recursion_depth", "current_task"] and old_val != new_val:
                    tracer.record_blackboard_change(display_name, key, old_val, new_val)
                elif key == "code_snippets" and isinstance(new_val, dict):
                    old_snippets = old_val if isinstance(old_val, dict) else {}
                    new_modules = set(new_val.keys()) - set(old_snippets.keys())
                    for mod in new_modules:
                        tracer.record_blackboard_change(display_name, f"code_snippets[{mod}]", "-", "新增代码模块")
                elif key == "documentation" and new_val and not old_val:
                    tracer.record_blackboard_change(display_name, "documentation", "-", "生成文档")
            
            tracer.end_step(node_state, "completed")
        
        final_state = state
    
    if verbose:
        print("\n" + "=" * 60)
        print("Proto-FNN 执行完成")
        print("=" * 60)
    
    # 保存最终 HTML 报告到项目目录
    if tracer:
        tracer.mark_complete()  # 标记完成，停止自动刷新
        
        # 生成执行总结
        if verbose:
            print("\n📝 正在生成执行总结...")
        tracer.generate_summary()
        
        # 保存到项目目录
        report_path = project_dir / "execution_report.html"
        tracer.save_html_report(str(report_path))
        print(f"\n📊 执行报告已保存到: {report_path}")
    
    # 获取最终状态
    if final_state:
        last_node = list(final_state.keys())[0]
        return final_state[last_node]
    
    return initial_state
