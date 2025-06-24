#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright [2025] [caixiaorong]
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""
@Time   : 2024/9/22 11:08
@Author : caixiaorong01@outlook.com
@File   : builtin_tool_service.py
"""
import mimetypes
import os.path
from dataclasses import dataclass
from typing import Any

from flask import current_app
from injector import inject
from pydantic import BaseModel

from internal.core.tools.builtin_tools.categories import BuiltinCategoryManager
from internal.core.tools.builtin_tools.providers import BuiltinProviderManager
from internal.exception import NotFoundException


@inject
@dataclass
class BuiltinToolService:
    """内置工具服务"""
    builtin_provider_manager: BuiltinProviderManager
    builtin_category_manager: BuiltinCategoryManager

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

    def get_provider_icon(self, provider_name: str) -> tuple[bytes, str]:
        # 获取提供商
        provider = self.builtin_provider_manager.get_provider(provider_name)
        if not provider:
            raise NotFoundException(f"该提供商{provider_name}不存在")
        # 获取根目录信息
        root_path = os.path.dirname(os.path.dirname(current_app.root_path))
        provider_path = os.path.join(root_path, "internal", "core", "tools", "builtin_tools", "providers",
                                     provider_name)
        icon_path = os.path.join(provider_path, "_asset", provider.provider_entity.icon)

        if not os.path.exists(icon_path):
            raise NotFoundException(f"图标不存在")
        mimetype, _ = mimetypes.guess_type(icon_path)
        mimetype = mimetype or "application/octet-stream"
        with open(icon_path, "rb") as f:
            byte_data = f.read()
            return byte_data, mimetype

    def get_categories(self) -> list[dict[str, Any]]:
        category_map = self.builtin_category_manager.get_category_map()
        return [{
            "name": category["entity"].name,
            "category": category["entity"].category,
            "icon": category["icon"]
        } for category in category_map.values()]

    @classmethod
    def get_tool_inputs(cls, tool) -> list:
        inputs = []
        # 检测工具是否有args_schema属性，并且是BaseModel的子类
        if hasattr(tool, "args_schema") and issubclass(tool.args_schema, BaseModel):

            for field_name, model_field in tool.args_schema.__fields__.items():
                inputs.append({
                    "name": field_name,
                    "description": model_field.description or "",
                    "required": model_field.is_required(),
                    "type": model_field.annotation.__name__,
                })
        return inputs
