#!/opt/homebrew/Cellar/python@3.12/3.12.12/bin/python3.12
"""
Proto-FNN (v0.1) - 入口文件
Fractal Neural Network 原型系统

使用方法：
    python main.py "帮我写一个贪吃蛇游戏，并写一个介绍文档。"
    
或者交互模式：
    python main.py
"""

import sys
import os

from proto_fnn.graph import run_proto_fnn


def print_results(state: dict):
    """打印执行结果"""
    print("\n" + "=" * 60)
    print("📊 执行结果")
    print("=" * 60)
    
    # 打印状态
    print(f"\n状态: {state.get('status', 'unknown')}")
    
    # 打印思考路径
    traces = state.get("thought_traces", [])
    if traces:
        print(f"\n📝 思考路径 ({len(traces)} 步):")
        for i, trace in enumerate(traces, 1):
            print(f"  {i}. {trace}")
    
    # 打印代码片段
    code_snippets = state.get("code_snippets", {})
    if code_snippets:
        print(f"\n💻 生成的代码模块 ({len(code_snippets)} 个):")
        for name, code in code_snippets.items():
            print(f"\n--- {name} ---")
            print(code)
    
    # 打印文档
    documentation = state.get("documentation", "")
    if documentation:
        print("\n📖 生成的文档:")
        print("-" * 40)
        print(documentation[:1000] + "..." if len(documentation) > 1000 else documentation)
    
    print("\n" + "=" * 60)


def main():
    """主函数"""
    print("""
    ╔═══════════════════════════════════════════════════════════╗
    ║                   Proto-FNN v0.1                          ║
    ║     Fractal Neural Network with MCTS Planning             ║
    ╚═══════════════════════════════════════════════════════════╝
    """)
    
    # 获取用户输入
    if len(sys.argv) > 1:
        user_instruction = " ".join(sys.argv[1:])
    else:
        print("请输入您的需求（按 Enter 使用默认示例）：")
        user_instruction = input("> ").strip()
        
        if not user_instruction:
            user_instruction = "帮我写一个贪吃蛇游戏，并写一个介绍文档。"
            print(f"使用默认示例: {user_instruction}")
    
    print(f"\n🎯 任务: {user_instruction}")
    print("⏳ 正在启动 Proto-FNN...\n")
    
    try:
        # 运行系统
        final_state = run_proto_fnn(user_instruction, verbose=True)
        
        # 打印结果
        print_results(final_state)
        
    except KeyboardInterrupt:
        print("\n\n⚠️ 用户中断执行")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ 执行错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
