"""
架构可视化器 (Visualizer)
生成系统架构的 Mermaid 图和文档

为了兼容 Python 3.14，使用延迟导入
"""

from typing import List, Dict, Any, Optional

from .role_descriptor import RoleDescriptor


def generate_mermaid_graph(roles: Optional[List[RoleDescriptor]] = None) -> str:
    """
    生成 Mermaid 格式的架构图
    
    Args:
        roles: 角色描述列表，如果为 None 则自动加载
        
    Returns:
        Mermaid 格式的图定义字符串
    """
    if roles is None:
        from .role_factory import load_all_roles
        roles = load_all_roles()
    
    lines = ["graph TD"]
    
    # 定义节点样式
    node_styles = {
        "arbitrator": ("A", "仲裁者<br/>MCTS规划", "Core"),
        "worker": ("W", "工作者<br/>ReAct执行", "Workers"),
        "auditor": ("AU", "审核者<br/>代码审查", "QA"),
        "doc_generator": ("D", "文档生成器", "Workers"),
    }
    
    # 添加子图分组
    subgraphs = {
        "Core": [],
        "Workers": [],
        "QA": []
    }
    
    # 分组节点
    for role in roles:
        info = node_styles.get(role.name)
        if info:
            node_id, label, group = info
            subgraphs[group].append(f"        {node_id}[{label}]")
    
    # 生成子图
    subgraph_names = {
        "Core": "核心层",
        "Workers": "执行层", 
        "QA": "质量保障层"
    }
    
    for group, nodes in subgraphs.items():
        if nodes:
            lines.append(f"    subgraph {group}[\"{subgraph_names[group]}\"]")
            lines.extend(nodes)
            lines.append("    end")
    
    # 添加开始和结束节点
    lines.append("    Start((开始))")
    lines.append("    End((结束))")
    lines.append("")
    
    # 添加边
    edges = [
        ("Start", "A", ""),
        ("A", "W", "分配任务"),
        ("A", "D", "生成文档"),
        ("A", "End", "完成"),
        ("W", "AU", ""),
        ("AU", "A", "通过/拒绝"),
        ("D", "End", ""),
    ]
    
    for src, dst, label in edges:
        if label:
            lines.append(f"    {src} -->|{label}| {dst}")
        else:
            lines.append(f"    {src} --> {dst}")
    
    return "\n".join(lines)


def generate_role_table(roles: Optional[List[RoleDescriptor]] = None) -> str:
    """
    生成角色表格
    
    Args:
        roles: 角色描述列表
        
    Returns:
        Markdown 格式的表格
    """
    if roles is None:
        from .role_factory import load_all_roles
        roles = load_all_roles()
    
    lines = [
        "| 角色 | 描述 | 模型温度 | 能力 |",
        "|------|------|---------|------|"
    ]
    
    for role in roles:
        caps = ", ".join(role.capabilities[:3])
        if len(role.capabilities) > 3:
            caps += "..."
        lines.append(
            f"| **{role.display_name}** | {role.description[:30]}... | "
            f"{role.llm.temperature} | {caps} |"
        )
    
    return "\n".join(lines)


def generate_architecture_doc(roles: Optional[List[RoleDescriptor]] = None) -> str:
    """
    生成完整的架构文档
    
    Args:
        roles: 角色描述列表
        
    Returns:
        完整的 Markdown 格式架构文档
    """
    if roles is None:
        from .role_factory import load_all_roles
        roles = load_all_roles()
    
    mermaid = generate_mermaid_graph(roles)
    table = generate_role_table(roles)
    
    doc = f"""# Proto-FNN 系统架构

## 架构图

```mermaid
{mermaid}
```

## 角色说明

{table}

## 工作流程

1. **任务接收**: 仲裁者接收用户需求
2. **方案规划**: 使用 MCTS 生成多个执行方案
3. **任务分配**: 选择最优方案，分配子任务给工作者
4. **代码执行**: 工作者使用 ReAct 模式完成编程
5. **质量审核**: 审核者严格检查代码质量
6. **迭代优化**: 如审核未通过，返回仲裁者重新处理
7. **文档生成**: 所有代码完成后生成项目文档

## 角色详细信息

"""
    
    # 添加每个角色的详细信息
    for role in roles:
        doc += f"""### {role.display_name} ({role.name})

**描述**: {role.description}

**能力**: {', '.join(role.capabilities)}

**LLM 配置**:
- 温度: {role.llm.temperature}
- 响应格式: {role.llm.response_format}

**输入**: {', '.join(role.io.input) if role.io.input else '无'}

**输出**: {', '.join(role.io.output) if role.io.output else '无'}

---

"""
    
    return doc


def print_architecture():
    """打印架构图到控制台"""
    from .role_factory import load_all_roles
    
    roles = load_all_roles()
    print(generate_architecture_doc(roles))


def generate_html_visualization(roles: Optional[List[RoleDescriptor]] = None) -> str:
    """
    生成 HTML 格式的架构可视化页面
    
    Args:
        roles: 角色描述列表
        
    Returns:
        完整的 HTML 页面字符串
    """
    if roles is None:
        from .role_factory import load_all_roles
        roles = load_all_roles()
    
    mermaid_code = generate_mermaid_graph(roles)
    
    # 生成角色卡片 HTML
    role_cards = ""
    for role in roles:
        caps_html = "".join(f'<span class="tag">{cap}</span>' for cap in role.capabilities)
        role_cards += f'''
        <div class="role-card" data-role="{role.name}">
            <div class="role-header">
                <h3>{role.display_name}</h3>
                <span class="role-name">{role.name}</span>
            </div>
            <p class="role-desc">{role.description}</p>
            <div class="role-config">
                <div class="config-item">
                    <span class="label">温度</span>
                    <span class="value">{role.llm.temperature}</span>
                </div>
                <div class="config-item">
                    <span class="label">格式</span>
                    <span class="value">{role.llm.response_format}</span>
                </div>
            </div>
            <div class="capabilities">
                {caps_html}
            </div>
            <div class="io-info">
                <div class="io-section">
                    <strong>输入:</strong> {', '.join(role.io.input) if role.io.input else '无'}
                </div>
                <div class="io-section">
                    <strong>输出:</strong> {', '.join(role.io.output) if role.io.output else '无'}
                </div>
            </div>
        </div>
        '''
    
    html = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Proto-FNN 系统架构</title>
    <script src="https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js"></script>
    <style>
        :root {{
            --bg-primary: #0d1117;
            --bg-secondary: #161b22;
            --bg-tertiary: #21262d;
            --text-primary: #f0f6fc;
            --text-secondary: #8b949e;
            --accent-blue: #58a6ff;
            --accent-green: #3fb950;
            --accent-purple: #a371f7;
            --accent-orange: #d29922;
            --border-color: #30363d;
        }}
        
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: var(--bg-primary);
            color: var(--text-primary);
            min-height: 100vh;
            padding: 2rem;
        }}
        
        .container {{
            max-width: 1400px;
            margin: 0 auto;
        }}
        
        header {{
            text-align: center;
            margin-bottom: 3rem;
            padding: 2rem;
            background: linear-gradient(135deg, var(--bg-secondary) 0%, var(--bg-tertiary) 100%);
            border-radius: 16px;
            border: 1px solid var(--border-color);
        }}
        
        h1 {{
            font-size: 2.5rem;
            background: linear-gradient(90deg, var(--accent-blue), var(--accent-purple));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            margin-bottom: 0.5rem;
        }}
        
        .subtitle {{
            color: var(--text-secondary);
            font-size: 1.1rem;
        }}
        
        .section {{
            margin-bottom: 2rem;
        }}
        
        .section-title {{
            font-size: 1.5rem;
            margin-bottom: 1rem;
            color: var(--accent-blue);
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }}
        
        .section-title::before {{
            content: '';
            display: block;
            width: 4px;
            height: 24px;
            background: var(--accent-blue);
            border-radius: 2px;
        }}
        
        .graph-container {{
            background: var(--bg-secondary);
            border-radius: 16px;
            border: 1px solid var(--border-color);
            padding: 2rem;
            display: flex;
            justify-content: center;
            overflow-x: auto;
        }}
        
        .mermaid {{
            background: transparent !important;
        }}
        
        .roles-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
            gap: 1.5rem;
        }}
        
        .role-card {{
            background: var(--bg-secondary);
            border-radius: 12px;
            border: 1px solid var(--border-color);
            padding: 1.5rem;
            transition: all 0.3s ease;
            cursor: pointer;
        }}
        
        .role-card:hover {{
            transform: translateY(-4px);
            border-color: var(--accent-blue);
            box-shadow: 0 8px 30px rgba(88, 166, 255, 0.15);
        }}
        
        .role-card[data-role="arbitrator"] {{ border-left: 4px solid var(--accent-purple); }}
        .role-card[data-role="worker"] {{ border-left: 4px solid var(--accent-green); }}
        .role-card[data-role="auditor"] {{ border-left: 4px solid var(--accent-orange); }}
        .role-card[data-role="doc_generator"] {{ border-left: 4px solid var(--accent-blue); }}
        
        .role-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 0.75rem;
        }}
        
        .role-header h3 {{
            font-size: 1.25rem;
        }}
        
        .role-name {{
            font-family: 'Monaco', 'Consolas', monospace;
            font-size: 0.8rem;
            color: var(--text-secondary);
            background: var(--bg-tertiary);
            padding: 0.25rem 0.5rem;
            border-radius: 4px;
        }}
        
        .role-desc {{
            color: var(--text-secondary);
            font-size: 0.9rem;
            margin-bottom: 1rem;
            line-height: 1.5;
        }}
        
        .role-config {{
            display: flex;
            gap: 1rem;
            margin-bottom: 1rem;
        }}
        
        .config-item {{
            background: var(--bg-tertiary);
            padding: 0.5rem 1rem;
            border-radius: 8px;
            display: flex;
            flex-direction: column;
        }}
        
        .config-item .label {{
            font-size: 0.75rem;
            color: var(--text-secondary);
        }}
        
        .config-item .value {{
            font-weight: 600;
            color: var(--accent-green);
        }}
        
        .capabilities {{
            display: flex;
            flex-wrap: wrap;
            gap: 0.5rem;
            margin-bottom: 1rem;
        }}
        
        .tag {{
            background: var(--bg-tertiary);
            color: var(--accent-blue);
            padding: 0.25rem 0.75rem;
            border-radius: 16px;
            font-size: 0.8rem;
        }}
        
        .io-info {{
            border-top: 1px solid var(--border-color);
            padding-top: 1rem;
            font-size: 0.85rem;
            color: var(--text-secondary);
        }}
        
        .io-section {{
            margin-bottom: 0.5rem;
        }}
        
        .io-section strong {{
            color: var(--text-primary);
        }}
        
        .workflow {{
            background: var(--bg-secondary);
            border-radius: 12px;
            border: 1px solid var(--border-color);
            padding: 2rem;
        }}
        
        .workflow-steps {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 1rem;
        }}
        
        .workflow-step {{
            background: var(--bg-tertiary);
            padding: 1rem;
            border-radius: 8px;
            display: flex;
            align-items: flex-start;
            gap: 1rem;
        }}
        
        .step-number {{
            background: var(--accent-blue);
            color: var(--bg-primary);
            width: 28px;
            height: 28px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: 700;
            flex-shrink: 0;
        }}
        
        .step-content h4 {{
            margin-bottom: 0.25rem;
        }}
        
        .step-content p {{
            font-size: 0.85rem;
            color: var(--text-secondary);
        }}
        
        footer {{
            text-align: center;
            margin-top: 3rem;
            padding: 1.5rem;
            color: var(--text-secondary);
            font-size: 0.9rem;
        }}
        
        @media (max-width: 768px) {{
            body {{ padding: 1rem; }}
            h1 {{ font-size: 1.75rem; }}
            .roles-grid {{ grid-template-columns: 1fr; }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>Proto-FNN 系统架构</h1>
            <p class="subtitle">Fractal Neural Network with MCTS Planning</p>
        </header>
        
        <section class="section">
            <h2 class="section-title">系统架构图</h2>
            <div class="graph-container">
                <pre class="mermaid">
{mermaid_code}
                </pre>
            </div>
        </section>
        
        <section class="section">
            <h2 class="section-title">角色配置</h2>
            <div class="roles-grid">
                {role_cards}
            </div>
        </section>
        
        <section class="section">
            <h2 class="section-title">工作流程</h2>
            <div class="workflow">
                <div class="workflow-steps">
                    <div class="workflow-step">
                        <span class="step-number">1</span>
                        <div class="step-content">
                            <h4>任务接收</h4>
                            <p>仲裁者接收用户需求</p>
                        </div>
                    </div>
                    <div class="workflow-step">
                        <span class="step-number">2</span>
                        <div class="step-content">
                            <h4>方案规划</h4>
                            <p>使用 MCTS 生成多个方案</p>
                        </div>
                    </div>
                    <div class="workflow-step">
                        <span class="step-number">3</span>
                        <div class="step-content">
                            <h4>任务分配</h4>
                            <p>选择最优方案分配给工作者</p>
                        </div>
                    </div>
                    <div class="workflow-step">
                        <span class="step-number">4</span>
                        <div class="step-content">
                            <h4>代码执行</h4>
                            <p>工作者使用 ReAct 模式完成</p>
                        </div>
                    </div>
                    <div class="workflow-step">
                        <span class="step-number">5</span>
                        <div class="step-content">
                            <h4>质量审核</h4>
                            <p>审核者严格检查代码质量</p>
                        </div>
                    </div>
                    <div class="workflow-step">
                        <span class="step-number">6</span>
                        <div class="step-content">
                            <h4>迭代优化</h4>
                            <p>未通过则返回重新处理</p>
                        </div>
                    </div>
                    <div class="workflow-step">
                        <span class="step-number">7</span>
                        <div class="step-content">
                            <h4>文档生成</h4>
                            <p>完成后生成项目文档</p>
                        </div>
                    </div>
                </div>
            </div>
        </section>
        
        <footer>
            <p>Proto-FNN v0.1 | 由角色配置动态生成</p>
        </footer>
    </div>
    
    <script>
        mermaid.initialize({{
            startOnLoad: true,
            theme: 'dark',
            themeVariables: {{
                primaryColor: '#58a6ff',
                primaryTextColor: '#f0f6fc',
                primaryBorderColor: '#30363d',
                lineColor: '#8b949e',
                secondaryColor: '#21262d',
                tertiaryColor: '#161b22'
            }}
        }});
    </script>
</body>
</html>'''
    
    return html


def save_html_visualization(output_path: str = "architecture.html"):
    """
    保存 HTML 可视化到文件
    
    Args:
        output_path: 输出文件路径
    """
    html = generate_html_visualization()
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)
    print(f"架构可视化已保存到: {output_path}")
    return output_path


if __name__ == "__main__":
    print_architecture()


def generate_execution_html(tracer) -> str:
    """
    生成按时间线顺序的执行报告 HTML
    
    按执行顺序展示每个步骤的思考过程
    """
    # 生成时间线步骤 HTML
    timeline_html = ""
    step_num = 0
    
    for step in tracer.steps:
        node = step.node_name
        step_num += 1
        
        if node == "arbitrator":
            # 仲裁者：显示方案和选择理由
            if step.generated_plans:
                plans_grid = '<div class="plans-grid">'
                for plan in step.generated_plans:
                    score = plan.get('score', 0)
                    plan_id = plan.get('id', '?')
                    is_best = score >= 8
                    plans_grid += f'''
                    <div class="plan-card {'best' if is_best else ''}">
                        <div class="plan-header">
                            <span class="plan-id">方案 {plan_id}</span>
                            <span class="plan-score {'high' if is_best else ''}">{score}/10</span>
                        </div>
                        <p>{_escape_html(plan.get('description', ''))}</p>
                    </div>
                    '''
                plans_grid += '</div>'
                
                # 选择理由
                reason = step.reasoning or step.thinking or ""
                if "选择" in reason:
                    reason_text = f'<div class="reason-box"><strong>🎯 选择:</strong> {_escape_html(reason[:200])}</div>'
                else:
                    reason_text = f'<div class="reason-box">{_escape_html(reason[:200])}</div>' if reason else ""
                
                timeline_html += f'''
                <div class="timeline-item arbitrator">
                    <div class="timeline-marker">🧠</div>
                    <div class="timeline-content">
                        <div class="timeline-header">
                            <span class="node-name">仲裁者 - MCTS 规划</span>
                            <span class="step-badge">Step {step_num}</span>
                        </div>
                        <p class="timeline-desc">生成 {len(step.generated_plans)} 个方案：</p>
                        {plans_grid}
                        {reason_text}
                    </div>
                </div>
                '''
            elif step.thinking:
                # 没有方案的仲裁者步骤（如达到深度限制）
                timeline_html += f'''
                <div class="timeline-item arbitrator limit">
                    <div class="timeline-marker">⚠️</div>
                    <div class="timeline-content">
                        <div class="timeline-header">
                            <span class="node-name">仲裁者</span>
                            <span class="step-badge">Step {step_num}</span>
                        </div>
                        <p class="timeline-desc">{_escape_html(step.thinking[:150])}</p>
                    </div>
                </div>
                '''
                
        elif node == "worker":
            # 工作者：显示执行简报
            if step.thinking:
                thinking = step.thinking
                # 提取简要描述
                if "完成模块" in thinking:
                    parts = thinking.split(":")
                    desc = parts[1].strip()[:200] if len(parts) > 1 else thinking[:200]
                else:
                    desc = thinking[:200]
                
                timeline_html += f'''
                <div class="timeline-item worker">
                    <div class="timeline-marker">⚡</div>
                    <div class="timeline-content">
                        <div class="timeline-header">
                            <span class="node-name">工作者 - 代码执行</span>
                            <span class="step-badge">Step {step_num}</span>
                        </div>
                        <p class="timeline-desc">{_escape_html(desc)}</p>
                    </div>
                </div>
                '''
                
        elif node == "auditor":
            # 审核者：显示审核结论
            if step.thinking:
                # 提取评分
                thinking = step.thinking
                score_text = ""
                if "评分:" in thinking:
                    try:
                        score_part = thinking.split("评分:")[1].split(")")[0]
                        score_text = f'<span class="audit-score">评分: {score_part}</span>'
                    except:
                        pass
                
                # 提取结果
                result = "approved" if "approved" in thinking else "rejected" if "rejected" in thinking else ""
                result_class = "approved" if result == "approved" else "rejected" if result == "rejected" else ""
                
                timeline_html += f'''
                <div class="timeline-item auditor {result_class}">
                    <div class="timeline-marker">{'✅' if result == 'approved' else '❌' if result == 'rejected' else '🔍'}</div>
                    <div class="timeline-content">
                        <div class="timeline-header">
                            <span class="node-name">审核者 - 代码审查</span>
                            {score_text}
                        </div>
                        <p class="timeline-desc">{_escape_html(thinking[:200])}</p>
                    </div>
                </div>
                '''
                
        elif node == "doc_generator":
            timeline_html += f'''
            <div class="timeline-item doc">
                <div class="timeline-marker">📄</div>
                <div class="timeline-content">
                    <div class="timeline-header">
                        <span class="node-name">文档生成器</span>
                        <span class="step-badge">Step {step_num}</span>
                    </div>
                    <p class="timeline-desc">生成项目文档完成</p>
                </div>
            </div>
            '''
    
    # 计算执行时间
    duration = ""
    if tracer.end_time:
        delta = tracer.end_time - tracer.start_time
        duration = f"{int(delta.total_seconds())}秒"
    
    html = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Proto-FNN 执行报告</title>
    <style>
        :root {{ --bg: #0d1117; --card: #161b22; --border: #30363d; --text: #f0f6fc; --text2: #8b949e; --blue: #58a6ff; --green: #3fb950; --purple: #a371f7; --orange: #d29922; --red: #f85149; }}
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: -apple-system, sans-serif; background: var(--bg); color: var(--text); padding: 2rem; line-height: 1.6; }}
        .container {{ max-width: 900px; margin: 0 auto; }}
        header {{ text-align: center; padding: 2rem; background: var(--card); border-radius: 12px; border: 1px solid var(--border); margin-bottom: 2rem; }}
        h1 {{ font-size: 1.8rem; background: linear-gradient(90deg, var(--green), var(--blue)); -webkit-background-clip: text; -webkit-text-fill-color: transparent; margin-bottom: 0.5rem; }}
        .meta {{ color: var(--text2); font-size: 0.9rem; }}
        .meta span {{ margin: 0 0.5rem; }}
        .summary-box {{ background: linear-gradient(135deg, var(--card), #1a2332); border: 1px solid var(--blue); border-radius: 12px; padding: 1.5rem; margin-bottom: 2rem; }}
        .summary-box h3 {{ color: var(--blue); margin-bottom: 0.75rem; }}
        
        /* 时间线 */
        .timeline {{ position: relative; padding-left: 50px; }}
        .timeline::before {{ content: ''; position: absolute; left: 20px; top: 0; bottom: 0; width: 2px; background: var(--border); }}
        
        .timeline-item {{ position: relative; margin-bottom: 1.5rem; }}
        .timeline-marker {{ position: absolute; left: -50px; width: 40px; height: 40px; background: var(--card); border: 2px solid var(--border); border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 1.2rem; }}
        
        .timeline-item.arbitrator .timeline-marker {{ border-color: var(--purple); }}
        .timeline-item.worker .timeline-marker {{ border-color: var(--blue); }}
        .timeline-item.auditor .timeline-marker {{ border-color: var(--green); }}
        .timeline-item.auditor.rejected .timeline-marker {{ border-color: var(--red); }}
        .timeline-item.limit .timeline-marker {{ border-color: var(--orange); }}
        .timeline-item.doc .timeline-marker {{ border-color: var(--text2); }}
        
        .timeline-content {{ background: var(--card); border-radius: 12px; border: 1px solid var(--border); padding: 1.25rem; }}
        .timeline-header {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.75rem; }}
        .node-name {{ font-weight: 600; color: var(--text); }}
        .step-badge {{ background: var(--border); color: var(--text2); font-size: 0.75rem; padding: 0.2rem 0.5rem; border-radius: 4px; }}
        .audit-score {{ background: var(--green); color: var(--bg); font-size: 0.8rem; padding: 0.2rem 0.5rem; border-radius: 4px; }}
        .timeline-desc {{ color: var(--text2); font-size: 0.9rem; }}
        
        /* 方案网格 */
        .plans-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 0.75rem; margin: 0.75rem 0; }}
        .plan-card {{ background: var(--bg); padding: 0.75rem; border-radius: 8px; border-left: 3px solid var(--purple); }}
        .plan-card.best {{ border-left-color: var(--green); background: rgba(63, 185, 80, 0.1); }}
        .plan-header {{ display: flex; justify-content: space-between; margin-bottom: 0.25rem; }}
        .plan-id {{ font-weight: 600; font-size: 0.85rem; }}
        .plan-score {{ color: var(--text2); font-size: 0.85rem; }}
        .plan-score.high {{ color: var(--green); font-weight: 600; }}
        .plan-card p {{ color: var(--text2); font-size: 0.8rem; }}
        
        .reason-box {{ margin-top: 0.75rem; padding: 0.75rem; background: var(--bg); border-radius: 6px; border-left: 3px solid var(--green); font-size: 0.85rem; color: var(--text2); }}
        
        /* 成果区域 */
        .outputs-section, .blackboard-section {{ background: var(--card); border-radius: 12px; border: 1px solid var(--border); padding: 1.25rem; margin-top: 1.5rem; }}
        .outputs-section h3, .blackboard-section h3 {{ color: var(--blue); font-size: 1rem; margin-bottom: 0.75rem; }}
        .outputs-list {{ list-style: none; padding: 0; }}
        .outputs-list li {{ padding: 0.5rem; background: var(--bg); border-radius: 6px; margin-bottom: 0.5rem; font-size: 0.9rem; }}
        .outputs-note {{ font-size: 0.8rem; color: var(--text2); margin-top: 0.5rem; }}
        .outputs-note code {{ background: var(--bg); padding: 0.2rem 0.4rem; border-radius: 4px; }}
        
        /* 黑板变动表格 */
        .bb-table {{ width: 100%; border-collapse: collapse; font-size: 0.85rem; margin-top: 0.5rem; }}
        .bb-table th, .bb-table td {{ padding: 0.5rem; text-align: left; border-bottom: 1px solid var(--border); }}
        .bb-table th {{ color: var(--text2); font-weight: 500; }}
        .bb-table td {{ color: var(--text); }}
        .bb-time {{ color: var(--text2); font-family: monospace; }}
        .bb-actor {{ color: var(--purple); font-weight: 600; }}
        .bb-field {{ color: var(--blue); }}
        .bb-old {{ color: var(--text2); text-decoration: line-through; }}
        .bb-new {{ color: var(--green); font-weight: 500; }}
        
        footer {{ text-align: center; margin-top: 2rem; padding: 1rem; color: var(--text2); }}
        .badge {{ display: inline-block; background: var(--green); color: var(--bg); padding: 0.25rem 0.75rem; border-radius: 12px; font-size: 0.85rem; font-weight: 600; }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>Proto-FNN 执行报告</h1>
            <p class="meta">
                <span>📌 {tracer.task_name}</span>
                <span>⏱️ {duration}</span>
                <span>📊 {len(tracer.steps)} 步</span>
            </p>
        </header>
        
        {f'<div class="summary-box"><h3>📝 总结</h3><p>{tracer.summary}</p></div>' if tracer.summary else ''}
        
        <div class="timeline">
            {timeline_html}
        </div>
        
        {_generate_outputs_section(tracer)}
        {_generate_blackboard_section(tracer)}
        
        <footer>
            <span class="badge">✅ 执行完成</span>
            <p style="margin-top: 0.5rem;">{tracer.end_time.strftime('%Y-%m-%d %H:%M:%S') if tracer.end_time else ''}</p>
        </footer>
    </div>
</body>
</html>'''
    
    return html


def _escape_html(text: str) -> str:
    """转义 HTML 特殊字符"""
    if not text:
        return ""
    return (text
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;")
            .replace("'", "&#39;"))


def _generate_outputs_section(tracer) -> str:
    """生成成果汇总部分"""
    # 统计生成的模块
    modules = []
    for step in tracer.steps:
        if step.node_name == "worker" and step.output_state:
            snippets = step.output_state.get("code_snippets", {})
            for name in snippets.keys():
                if name not in [m[0] for m in modules]:
                    modules.append((name, "已保存到 output/"))
    
    if not modules:
        return ""
    
    items = "".join(f'<li>📄 <strong>{name}</strong> - {desc}</li>' for name, desc in modules)
    
    return f'''
    <div class="outputs-section">
        <h3>📦 生成的成果</h3>
        <ul class="outputs-list">{items}</ul>
        <p class="outputs-note">💾 所有代码已保存到 <code>output/</code> 目录</p>
    </div>
    '''


def _generate_blackboard_section(tracer) -> str:
    """生成黑板变动部分"""
    # 使用新的变动记录
    if hasattr(tracer, 'blackboard_changes') and tracer.blackboard_changes:
        rows = ""
        for change in tracer.blackboard_changes[-10:]:  # 最近10条
            rows += f'''
            <tr>
                <td class="bb-time">{change.get('timestamp', '')}</td>
                <td class="bb-actor">{change.get('actor', '')}</td>
                <td class="bb-field">{change.get('field', '')}</td>
                <td class="bb-old">{change.get('old_value', '-')}</td>
                <td class="bb-new">{change.get('new_value', '-')}</td>
            </tr>
            '''
        
        return f'''
        <div class="blackboard-section">
            <h3>🗒️ 黑板变动记录</h3>
            <table class="bb-table">
                <thead>
                    <tr>
                        <th>时间</th>
                        <th>改动者</th>
                        <th>字段</th>
                        <th>旧值</th>
                        <th>新值</th>
                    </tr>
                </thead>
                <tbody>{rows}</tbody>
            </table>
        </div>
        '''
    
    return ""

