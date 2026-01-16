"""
项目配置 - 使用环境变量获取敏感信息
"""
import os

# API 配置 (从环境变量读取)
api_key = os.environ.get("DEEPSEEK_API_KEY", "")
base_url = os.environ.get("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
model = os.environ.get("LLM_MODEL", "deepseek-chat")