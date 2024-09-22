#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2024/9/22 10:59
@Author : rxccai@gmail.com
@File   : builtin_tool_handler.py
"""
import io
from dataclasses import dataclass

from flask import send_file
from injector import inject

from internal.service import BuiltinToolService
from pkg.response import success_json


@inject
@dataclass
class BuiltinToolHandler:
    """内置工具处理器"""
    builtin_tool_service: BuiltinToolService

    def get_builtin_tools(self):
        """获取内置工具信息+提供商信息"""
        builtin_tools = self.builtin_tool_service.get_builtin_tools()
        return success_json(builtin_tools)

    def get_provider_tool(self, provider_name: str, tool_name: str):
        """根据传递的提供商名字和工具名字获取指定工具信息"""
        builtin_tool = self.builtin_tool_service.get_provider_tool(provider_name, tool_name)
        return success_json(builtin_tool)

    def get_provider_icon(self, provider_name: str):
        icon, mimetype = self.builtin_tool_service.get_provider_icon(provider_name)
        return send_file(io.BytesIO(icon), mimetype)

    def get_categories(self):
        categories = self.builtin_tool_service.get_categories()
        return success_json(categories)
