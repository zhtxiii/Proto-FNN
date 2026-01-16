"""
执行追踪器 (Execution Tracer)
记录代码运行的所有中间思考和结果

为了兼容 Python 3.14，使用延迟导入
"""

import json
import time
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path


@dataclass
class LLMCall:
    """LLM 调用记录"""
    role: str  # 角色名
    prompt: str  # 发送的提示词
    response: str  # LLM 响应
    model: str = ""
    temperature: float = 0.0
    duration_ms: int = 0
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class ExecutionStep:
    """单步执行记录"""
    step_id: int
    node_name: str  # 节点名称
    node_display_name: str  # 节点显示名称
    timestamp: str
    duration_ms: int = 0
    
    # 输入输出状态
    input_state: Dict[str, Any] = field(default_factory=dict)
    output_state: Dict[str, Any] = field(default_factory=dict)
    
    # LLM 调用
    llm_calls: List[LLMCall] = field(default_factory=list)
    
    # 思考和决策
    thinking: str = ""  # 当前思考
    decision: str = ""  # 做出的决定
    reasoning: str = ""  # 推理过程
    
    # 生成的内容
    generated_code: str = ""
    generated_plans: List[Dict] = field(default_factory=list)
    
    # 状态
    status: str = "running"  # running, completed, error


class ExecutionTracer:
    """执行追踪器 - 记录整个执行过程"""
    
    def __init__(self, task_name: str = ""):
        self.task_name = task_name
        self.start_time = datetime.now()
        self.end_time: Optional[datetime] = None
        self.steps: List[ExecutionStep] = []
        self.current_step: Optional[ExecutionStep] = None
        self._step_counter = 0
        self._output_dir = Path(__file__).parent.parent
        self.is_complete = False  # 任务是否完成
        self.summary = ""  # 执行总结
        # 黑板变动记录
        self.blackboard_changes: List[Dict] = []
        # 待处理数据缓存（在 step 创建前记录的数据）
        self._pending_plans: List[Dict] = []
        self._pending_thinking: str = ""
        self._pending_reasoning: str = ""
    
    def record_blackboard_change(self, actor: str, field: str, old_value: Any, new_value: Any):
        """记录黑板变动"""
        change = {
            "timestamp": datetime.now().strftime("%H:%M:%S"),
            "actor": actor,
            "field": field,
            "old_value": str(old_value)[:50] if old_value else "-",
            "new_value": str(new_value)[:50] if new_value else "-"
        }
        self.blackboard_changes.append(change)
    
    def start_step(self, node_name: str, node_display_name: str = "", 
                   input_state: Dict = None) -> ExecutionStep:
        """开始一个新的执行步骤"""
        self._step_counter += 1
        
        step = ExecutionStep(
            step_id=self._step_counter,
            node_name=node_name,
            node_display_name=node_display_name or node_name,
            timestamp=datetime.now().isoformat(),
            input_state=self._sanitize_state(input_state) if input_state else {},
            status="running"
        )
        
        # 应用待处理的数据
        if self._pending_plans:
            step.generated_plans = self._pending_plans
            self._pending_plans = []
        if self._pending_thinking:
            step.thinking = self._pending_thinking
            step.reasoning = self._pending_reasoning
            self._pending_thinking = ""
            self._pending_reasoning = ""
        
        self.current_step = step
        self.steps.append(step)
        
        # 实时保存
        self._save_trace()
        
        return step
    
    def record_llm_call(self, role: str, prompt: str, response: str,
                        model: str = "", temperature: float = 0.0, 
                        duration_ms: int = 0):
        """记录 LLM 调用"""
        if self.current_step:
            llm_call = LLMCall(
                role=role,
                prompt=prompt[:2000] + "..." if len(prompt) > 2000 else prompt,
                response=response[:2000] + "..." if len(response) > 2000 else response,
                model=model,
                temperature=temperature,
                duration_ms=duration_ms
            )
            self.current_step.llm_calls.append(llm_call)
            self._save_trace()
    
    def record_thinking(self, thinking: str, decision: str = "", reasoning: str = ""):
        """记录思考过程"""
        if self.current_step:
            self.current_step.thinking = thinking
            self.current_step.decision = decision
            self.current_step.reasoning = reasoning
            self._save_trace()
        else:
            # 保存到待处理缓存
            self._pending_thinking = thinking
            self._pending_reasoning = reasoning
    
    def record_plans(self, plans: List[Dict]):
        """记录生成的计划"""
        if self.current_step:
            self.current_step.generated_plans = plans
            self._save_trace()
        else:
            # 保存到待处理缓存
            self._pending_plans = plans
    
    def record_code(self, code: str):
        """记录生成的代码"""
        if self.current_step:
            self.current_step.generated_code = code
            self._save_trace()
    
    def end_step(self, output_state: Dict = None, status: str = "completed"):
        """结束当前步骤"""
        if self.current_step:
            self.current_step.output_state = self._sanitize_state(output_state) if output_state else {}
            self.current_step.status = status
            
            # 计算持续时间
            start = datetime.fromisoformat(self.current_step.timestamp)
            self.current_step.duration_ms = int((datetime.now() - start).total_seconds() * 1000)
            
            self._save_trace()
            self.current_step = None
    
    def _sanitize_state(self, state: Dict) -> Dict:
        """清理状态以便序列化"""
        if not state:
            return {}
        
        sanitized = {}
        for key, value in state.items():
            if key == "messages":
                sanitized[key] = f"[{len(value)} messages]" if value else "[]"
            elif isinstance(value, dict):
                # 限制代码片段长度
                sanitized[key] = {
                    k: (v[:500] + "..." if isinstance(v, str) and len(v) > 500 else v)
                    for k, v in value.items()
                }
            elif isinstance(value, list):
                sanitized[key] = value[-5:] if len(value) > 5 else value  # 只保留最近5条
            elif isinstance(value, str) and len(value) > 500:
                sanitized[key] = value[:500] + "..."
            else:
                sanitized[key] = value
        
        return sanitized
    
    def _save_trace(self):
        """保存追踪数据到 JSON 文件"""
        trace_data = {
            "task_name": self.task_name,
            "start_time": self.start_time.isoformat(),
            "current_time": datetime.now().isoformat(),
            "total_steps": len(self.steps),
            "steps": [self._step_to_dict(step) for step in self.steps]
        }
        
        output_path = self._output_dir / "execution_trace.json"
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(trace_data, f, ensure_ascii=False, indent=2)
    
    def _step_to_dict(self, step: ExecutionStep) -> Dict:
        """将步骤转换为字典"""
        return {
            "step_id": step.step_id,
            "node_name": step.node_name,
            "node_display_name": step.node_display_name,
            "timestamp": step.timestamp,
            "duration_ms": step.duration_ms,
            "status": step.status,
            "input_state": step.input_state,
            "output_state": step.output_state,
            "llm_calls": [asdict(llm) for llm in step.llm_calls],
            "thinking": step.thinking,
            "decision": step.decision,
            "reasoning": step.reasoning,
            "generated_code": step.generated_code,
            "generated_plans": step.generated_plans
        }
    
    def generate_html_report(self) -> str:
        """生成 HTML 报告"""
        from .visualizer import generate_execution_html
        return generate_execution_html(self)
    
    def mark_complete(self):
        """标记任务完成，停止自动刷新"""
        self.is_complete = True
        self.end_time = datetime.now()
        self._save_trace()
    
    def generate_summary(self) -> str:
        """使用大模型总结执行过程"""
        from .role_factory import create_llm
        from .role_descriptor import LLMConfig
        
        # 构建总结提示词
        steps_summary = []
        for step in self.steps:
            step_info = f"- {step.node_display_name}: {step.thinking or step.decision or '执行完成'}"
            if step.generated_plans:
                step_info += f" (生成{len(step.generated_plans)}个方案)"
            steps_summary.append(step_info)
        
        prompt = f"""请简洁总结以下 AI Agent 的执行过程，突出关键决策和成果。要求：
1. 用 2-3 句话概括整体流程
2. 列出关键决策点（如选择了哪个方案、为什么）
3. 简述最终产出

任务: {self.task_name}
执行步骤:
{chr(10).join(steps_summary)}

请用中文输出简洁的总结（不超过150字）:"""

        try:
            # 使用低温度创建总结用 LLM
            llm_config = LLMConfig(temperature=0.3, response_format="text")
            llm = create_llm(llm_config)
            
            from langchain_core.messages import HumanMessage
            response = llm.invoke([HumanMessage(content=prompt)])
            self.summary = response.content
        except Exception as e:
            self.summary = f"总结生成失败: {e}"
        
        return self.summary

    def save_html_report(self, output_path: str = "execution_viewer.html"):
        """保存 HTML 报告"""
        html = self.generate_html_report()
        full_path = self._output_dir / output_path
        with open(full_path, 'w', encoding='utf-8') as f:
            f.write(html)
        print(f"执行追踪报告已保存到: {full_path}")


# 全局追踪器实例
_global_tracer: Optional[ExecutionTracer] = None


def get_tracer() -> Optional[ExecutionTracer]:
    """获取全局追踪器"""
    return _global_tracer


def init_tracer(task_name: str = "") -> ExecutionTracer:
    """初始化全局追踪器"""
    global _global_tracer
    _global_tracer = ExecutionTracer(task_name)
    return _global_tracer


def reset_tracer():
    """重置全局追踪器"""
    global _global_tracer
    _global_tracer = None
