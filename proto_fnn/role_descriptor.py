"""
角色描述数据模型 (Role Descriptor)
定义角色元数据的数据结构

为了兼容 Python 3.14，使用延迟导入
"""

from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional


@dataclass
class LLMConfig:
    """LLM 配置"""
    model: Optional[str] = None  # None 表示使用全局配置
    temperature: float = 0.5
    response_format: str = "text"  # "json" or "text"
    api_key: Optional[str] = None  # None 表示使用全局配置
    base_url: Optional[str] = None  # None 表示使用全局配置


@dataclass
class RoutingConfig:
    """路由配置"""
    entry_point: bool = False
    next_nodes: List[str] = field(default_factory=list)
    routing_function: Optional[str] = None
    routing_outcomes: List[str] = field(default_factory=list)


@dataclass
class IOConfig:
    """输入输出配置"""
    input: List[str] = field(default_factory=list)
    output: List[str] = field(default_factory=list)


@dataclass
class RoleDescriptor:
    """
    角色描述器
    包含角色的完整元数据
    """
    name: str
    display_name: str
    description: str
    llm: LLMConfig = field(default_factory=LLMConfig)
    capabilities: List[str] = field(default_factory=list)
    io: IOConfig = field(default_factory=IOConfig)
    routing: RoutingConfig = field(default_factory=RoutingConfig)
    tools: List[str] = field(default_factory=list)
    limits: Dict[str, Any] = field(default_factory=dict)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'RoleDescriptor':
        """从字典创建角色描述器"""
        # 解析 LLM 配置
        llm_data = data.get('llm', {})
        llm = LLMConfig(
            model=llm_data.get('model'),
            temperature=llm_data.get('temperature', 0.5),
            response_format=llm_data.get('response_format', 'text'),
            api_key=llm_data.get('api_key'),
            base_url=llm_data.get('base_url')
        )
        
        # 解析路由配置
        routing_data = data.get('routing', {})
        routing = RoutingConfig(
            entry_point=routing_data.get('entry_point', False),
            next_nodes=routing_data.get('next_nodes', []),
            routing_function=routing_data.get('routing_function'),
            routing_outcomes=routing_data.get('routing_outcomes', [])
        )
        
        # 解析 IO 配置
        io_data = data.get('io', {})
        io = IOConfig(
            input=io_data.get('input', []),
            output=io_data.get('output', [])
        )
        
        return cls(
            name=data.get('name', 'unknown'),
            display_name=data.get('display_name', data.get('name', 'Unknown')),
            description=data.get('description', ''),
            llm=llm,
            capabilities=data.get('capabilities', []),
            io=io,
            routing=routing,
            tools=data.get('tools', []),
            limits=data.get('limits', {})
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'name': self.name,
            'display_name': self.display_name,
            'description': self.description,
            'llm': {
                'model': self.llm.model,
                'temperature': self.llm.temperature,
                'response_format': self.llm.response_format,
            },
            'capabilities': self.capabilities,
            'io': {
                'input': self.io.input,
                'output': self.io.output
            },
            'routing': {
                'entry_point': self.routing.entry_point,
                'next_nodes': self.routing.next_nodes,
                'routing_function': self.routing.routing_function
            },
            'tools': self.tools,
            'limits': self.limits
        }
