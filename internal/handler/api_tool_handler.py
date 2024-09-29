#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2024/9/24 23:28
@Author : rxccai@gmail.com
@File   : api_tool_handler.py
"""
from dataclasses import dataclass
from uuid import UUID

from injector import inject

from internal.schema.api_tool_schema import (
    ValidateOpenAPISchemaReq,
    CreateApiToolReq,
    GetApiToolProviderResp,
    GetApiToolResp
)
from internal.service import ApiToolService
from pkg.response import validate_error_json, success_message, success_json


@inject
@dataclass
class ApiToolHandler:
    """自定义API插件处理器"""
    api_tool_service: ApiToolService

    def create_api_tool(self):
        """创建自定义API工具"""
        req = CreateApiToolReq()
        if not req.validate():
            return validate_error_json(req.errors)
        self.api_tool_service.create_api_tool(req)
        return success_message("创建成功")

    def get_api_tool(self, provider_id: UUID, tool_name: str):
        api_tool = self.api_tool_service.get_api_tool(provider_id, tool_name)
        resp = GetApiToolResp()
        return success_json(resp.dump(api_tool))

    def get_api_tool_provider(self, provider_id: UUID):
        """根据provider_id获取工具提供者"""
        api_tool_provider = self.api_tool_service.get_api_tool_provider(provider_id)

        resp = GetApiToolProviderResp()
        return success_json(resp.dump(api_tool_provider))

    def delete_api_tool_provider(self, provider_id: UUID):
        self.api_tool_service.delete_api_tool_provider(provider_id)
        return success_message("删除成功")

    def validate_openapi_schema(self):
        """校验参数"""
        # 提取数据并校验
        req = ValidateOpenAPISchemaReq()
        if not req.validate():
            return validate_error_json(req.errors)

        # 调用服务解析数据
        self.api_tool_service.parse_openapi_schema(req.openapi_schema.data)
        return success_message("数据校验成功")
