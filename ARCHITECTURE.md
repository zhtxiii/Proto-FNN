# Proto-FNN 架构

## 核心概念

### 1. 全局黑板 (Global Blackboard)

所有智能体共享的状态区，作为唯一数据源。

```python
AgentState:
  - user_instruction   # 用户需求
  - status            # 任务状态
  - code_snippets     # 代码片段
  - analysis_result   # 分析结果
  - documentation     # 文档
  - worker_type       # 工作者类型
  - audit_status      # 审核状态
```

### 2. 角色系统

| 角色 | 职责 |
|------|------|
| 仲裁者 | MCTS 规划，任务分配 |
| 编码工作者 | 生成代码 |
| 物理工作者 | 物理/数学分析 |
| 通用工作者 | 一般性问题分析 |
| 代码审核者 | 审核代码质量 |
| 物理审核者 | 审核物理分析 |
| 通用审核者 | 审核通用分析 |
| 文档生成器 | 生成项目文档 |

### 3. 状态流转

```
Start → 仲裁者
          ↓
    [选择工作者类型]
     ↓      ↓      ↓
   编码    物理    通用
   工作者  工作者  工作者
     ↓      ↓      ↓
   代码    物理    通用
   审核者  审核者  审核者
          ↓
    [审核结果]
   complete → 文档生成器 → End
   rejected → 仲裁者 (重试)
   resource_limit → 仲裁者 (换方案)
```

## 文件说明

- `graph.py` - 状态图定义和执行入口
- `state.py` - AgentState 类型定义
- `arbitrator.py` - 仲裁者逻辑
- `auditors.py` - 三种审核者
- `roles/*.yaml` - 角色配置
