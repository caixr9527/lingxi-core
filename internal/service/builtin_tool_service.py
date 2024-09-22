#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2024/9/22 11:08
@Author : rxccai@gmail.com
@File   : builtin_tool_service.py
"""
from dataclasses import dataclass

from injector import inject
from langchain_core.pydantic_v1 import BaseModel

from internal.core.tools.builtin_tools.providers import BuiltinProviderManager
from internal.exception import NotFoundException


@inject
@dataclass
class BuiltinToolService:
    """内置工具服务"""
    builtin_provider_manager: BuiltinProviderManager

    def get_builtin_tools(self) -> list:
        """获取所有内置提供商和工具对应信息"""
        # 获取所有提供商
        providers = self.builtin_provider_manager.get_providers()
        # 遍历所有提供商并提取工具信息
        builtin_toos = []
        for provider in providers:
            provider_entity = provider.provider_entity
            builtin_tool = {
                **provider_entity.model_dump(exclude=["icon"]),
                "tools": [],
            }
            # 提取提供者的所有工具实体
            for tool_entity in provider.get_tool_entities():
                # 提取工具函数
                tool = provider.get_tool(tool_entity.name)
                # 构建工具实体信息
                tool_dict = {
                    **tool_entity.model_dump(),
                    "inputs": self.get_tool_inputs(tool),
                }
                builtin_tool["tools"].append(tool_dict)
            builtin_toos.append(builtin_tool)
        return builtin_toos

    def get_provider_tool(self, provider_name: str, tool_name: str) -> dict:
        """根据传递的提供商名字和工具名字获取工具信息"""
        # 获取内置提供商
        provider = self.builtin_provider_manager.get_provider(provider_name)
        if provider is None:
            raise NotFoundException(f"该提供商{provider_name}不存在")
        #  获取工具
        tool_entity = provider.get_tool_entity(tool_name)
        if tool_entity is None:
            raise NotFoundException(f"该工具{tool_name}不存在")
        provider_entity = provider.provider_entity
        tool = provider.get_tool(tool_name)
        builtin_tool = {
            "provider": {**provider_entity.model_dump(exclude=["icon", "created_at"])},
            **tool_entity.model_dump(),
            "created_at": provider_entity.created_at,
            "inputs": self.get_tool_inputs(tool)
        }
        return builtin_tool

    @classmethod
    def get_tool_inputs(cls, tool) -> list:
        inputs = []
        # 检测工具是否有args_schema属性，并且是BaseModel的子类
        if hasattr(tool, "args_schema") and issubclass(tool.args_schema, BaseModel):

            for field_name, model_field in tool.args_schema.__fields__.items():
                inputs.append({
                    "name": field_name,
                    "description": model_field.field_info.description or "",
                    "required": model_field.required,
                    "type": model_field.outer_type_.__name__,
                })
        return inputs
