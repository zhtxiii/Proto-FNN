"""
角色工厂 (Role Factory)
基于角色描述动态创建角色实例和 LLM

为了兼容 Python 3.14，使用延迟导入
"""

import os
from pathlib import Path
from typing import Dict, List, Callable, Any

from .role_descriptor import RoleDescriptor, LLMConfig

# 角色配置目录
ROLES_DIR = Path(__file__).parent / "roles"


def load_role(name: str) -> RoleDescriptor:
    """
    从 YAML 文件加载角色描述
    
    Args:
        name: 角色名称（对应 .yaml 文件名，不含扩展名）
        
    Returns:
        RoleDescriptor 实例
    """
    import yaml
    
    yaml_path = ROLES_DIR / f"{name}.yaml"
    if not yaml_path.exists():
        raise FileNotFoundError(f"角色配置文件不存在: {yaml_path}")
    
    with open(yaml_path, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)
    
    return RoleDescriptor.from_dict(data)


def load_all_roles() -> List[RoleDescriptor]:
    """
    加载所有角色配置
    
    Returns:
        所有 RoleDescriptor 的列表
    """
    import yaml
    
    roles = []
    for yaml_file in ROLES_DIR.glob("*.yaml"):
        with open(yaml_file, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
        roles.append(RoleDescriptor.from_dict(data))
    
    return roles


def create_llm(config: LLMConfig):
    """
    基于配置创建 LLM 实例
    
    Args:
        config: LLM 配置
        
    Returns:
        ChatOpenAI 实例
    """
    from langchain_openai import ChatOpenAI
    import project_config
    
    # 使用配置值或回退到全局配置
    model = config.model or project_config.model
    api_key = config.api_key or project_config.api_key
    base_url = config.base_url or project_config.base_url
    
    # 构建 LLM 参数
    llm_kwargs = {
        "model": model,
        "temperature": config.temperature,
        "openai_api_key": api_key,
        "openai_api_base": base_url
    }
    
    # 如果需要 JSON 格式响应，使用 model_kwargs 传递
    if config.response_format == "json":
        llm_kwargs["model_kwargs"] = {"response_format": {"type": "json_object"}}
    
    return ChatOpenAI(**llm_kwargs)


def create_llm_for_role(role_name: str):
    """
    为指定角色创建 LLM 实例
    
    Args:
        role_name: 角色名称
        
    Returns:
        ChatOpenAI 实例
    """
    role = load_role(role_name)
    return create_llm(role.llm)


def get_role_registry() -> Dict[str, RoleDescriptor]:
    """
    获取角色注册表
    
    Returns:
        角色名称到描述的映射
    """
    roles = load_all_roles()
    return {role.name: role for role in roles}


def get_entry_role() -> RoleDescriptor:
    """
    获取入口角色（entry_point=true 的角色）
    
    Returns:
        入口角色描述
    """
    roles = load_all_roles()
    for role in roles:
        if role.routing.entry_point:
            return role
    raise ValueError("未找到入口角色（entry_point=true）")


def get_role_graph_structure() -> Dict[str, List[str]]:
    """
    获取角色图结构
    
    Returns:
        角色名称到其后续节点的映射
    """
    roles = load_all_roles()
    return {role.name: role.routing.next_nodes for role in roles}


# ==================== 便捷函数 ====================

def get_arbitrator_llm():
    """获取仲裁者 LLM"""
    return create_llm_for_role("arbitrator")


def get_auditor_llm():
    """获取审核者 LLM"""
    return create_llm_for_role("auditor")


def get_worker_llm():
    """获取工作者 LLM"""
    return create_llm_for_role("worker")


def get_doc_generator_llm():
    """获取文档生成器 LLM"""
    return create_llm_for_role("doc_generator")
