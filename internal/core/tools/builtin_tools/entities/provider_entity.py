#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2024/9/19 22:09
@Author : rxccai@gmail.com
@File   : provider_entity.py
"""
import os.path
from typing import Any

import yaml
from pydantic import BaseModel

from internal.lib.helper import dynamic_import
from .tool_entity import ToolEntity


class ProviderEntity(BaseModel):
    """服务提供商实体"""
    name: str
    label: str
    description: str
    icon: str
    background: str
    category: str


class Provider(BaseModel):
    name: str
    position: int
    provider_entity: ProviderEntity
    tool_entity_map: dict[str, ToolEntity] = {}
    tool_func_map: dict[str, Any] = {}

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        """完成"""
        self._provider_init()

    class Config:
        protected_namespace = ()

    def get_tool(self, tool_name: str) -> Any:
        """根据名称获取工具"""
        return self.tool_func_map.get(tool_name)

    def get_tool_entity(self, tool_name: str) -> Any:
        """根据名称获取，工具实体"""
        return self.tool_entity_map.get(tool_name)

    def get_tool_entities(self) -> list[ToolEntity]:
        return list(self.tool_entity_map.values())

    def _provider_init(self):
        """初始化函数对应服务提供商的初始化"""
        # 获取当前类的路径，计算到对应服务提供商的地址/路径
        current_path = os.path.abspath(__file__)
        entities_path = os.path.dirname(current_path)
        provider_path = os.path.join(os.path.dirname(entities_path), "providers", self.name)

        # 获取positions.yaml数据
        positions_yaml_path = os.path.join(provider_path, "positions.yaml")
        with open(positions_yaml_path, encoding="utf-8") as f:
            positions_yaml_data = yaml.safe_load(f)

        # 循环获取工具名称
        for tool_name in positions_yaml_data:
            # 获取工具的yaml数据
            tool_yaml_path = os.path.join(provider_path, f"{tool_name}.yaml")
            with open(tool_yaml_path, encoding="utf-8") as f:
                tool_yaml_data = yaml.safe_load(f)
            #
            self.tool_entity_map[tool_name] = ToolEntity(**tool_yaml_data)
            # 动态导入对应的工具填充到tool_func_map
            self.tool_func_map[tool_name] = dynamic_import(
                f"internal.core.tools.builtin_tools.providers.{self.name}",
                tool_name)
