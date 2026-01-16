# Proto-FNN

> **Proto-Fractal Neural Network** - 基于 MCTS 规划的多智能体协作系统

## 简介

Proto-FNN 是一个模拟分形神经网络思想的原型系统，使用 LangGraph 构建状态图，实现多角色协作处理复杂任务。

## 特性

- **MCTS 规划**：仲裁者生成多方案并推演未来结果
- **分类工作者**：编码/物理/通用三种工作者处理不同类型任务
- **分类审核者**：每种工作者有对应的专属审核者
- **执行追踪**：可视化执行过程和决策路径
- **项目独立输出**：每个任务生成独立的项目目录

## 架构

```
仲裁者 (Arbitrator)
    ├─ 编码工作者 → 代码审核者 ─┐
    ├─ 物理工作者 → 物理审核者 ─┼→ 仲裁者/文档生成
    └─ 通用工作者 → 通用审核者 ─┘
```

## 安装

```bash
pip install -r requirements.txt
```

## 使用

```bash
# 编程任务
python3 main.py "写一个快速排序算法"

# 物理问题
python3 main.py "解释黑洞的霍金辐射原理"

# 通用问题
python3 main.py "如何提高团队协作效率"
```

输出保存在 `output/时间戳_任务名/` 目录中。

## 项目结构

```
proto_fnn/
├── arbitrator.py      # 仲裁者节点
├── worker.py          # 编码工作者
├── physics_worker.py  # 物理工作者
├── general_worker.py  # 通用工作者
├── auditors.py        # 分类审核者
├── graph.py           # 状态图和执行逻辑
├── state.py           # 全局状态定义
├── prompts.py         # 提示词模板
├── visualizer.py      # HTML 报告生成
├── execution_tracer.py # 执行追踪器
├── role_factory.py    # 角色工厂
├── role_descriptor.py # 角色描述符
└── roles/             # 角色 YAML 配置
```

## 依赖

- Python 3.10+
- LangChain / LangGraph
- OpenAI API (或兼容 API)

## 许可

MIT License
