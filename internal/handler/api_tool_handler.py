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
@Time   : 2024/9/24 23:28
@Author : rxccai@gmail.com
@File   : api_tool_handler.py
"""
from dataclasses import dataclass
from uuid import UUID

from flask import request
from flask_login import login_required, current_user
from injector import inject

from internal.schema.api_tool_schema import (
    ValidateOpenAPISchemaReq,
    CreateApiToolReq,
    GetApiToolProviderResp,
    GetApiToolResp,
    GetApiToolProvidersWithPageReq,
    GetApiToolProvidersWithPageResp,
    UpdateApiToolProviderReq
)
from internal.service import ApiToolService
from pkg.paginator import PageModel
from pkg.response import validate_error_json, success_message, success_json


@inject
@dataclass
class ApiToolHandler:
    """自定义API插件处理器"""
    api_tool_service: ApiToolService

    @login_required
    def get_api_tool_providers_with_page(self):
        req = GetApiToolProvidersWithPageReq(request.args)
        if not req.validate():
            return validate_error_json(req.errors)
        print(current_user)
        api_tool_providers, paginator = self.api_tool_service.get_api_tool_providers_with_page(req,
                                                                                               account=current_user)
        resp = GetApiToolProvidersWithPageResp(many=True)
        return success_json(PageModel(list=resp.dump(api_tool_providers), paginator=paginator))

    @login_required
    def create_api_tool_provider(self):
        """创建自定义API工具"""
        req = CreateApiToolReq()
        if not req.validate():
            return validate_error_json(req.errors)
        self.api_tool_service.create_api_tool(req, account=current_user)
        return success_message("创建成功")

    @login_required
    def update_api_tool_provider(self, provider_id: UUID):
        req = UpdateApiToolProviderReq()
        if not req.validate():
            return validate_error_json(req.errors)

        self.api_tool_service.update_api_tool_provider(provider_id, req, account=current_user)
        return success_message("更新成功")

    @login_required
    def get_api_tool(self, provider_id: UUID, tool_name: str):
        api_tool = self.api_tool_service.get_api_tool(provider_id, tool_name, account=current_user)
        resp = GetApiToolResp()
        return success_json(resp.dump(api_tool))

    @login_required
    def get_api_tool_provider(self, provider_id: UUID):
        """根据provider_id获取工具提供者"""
        api_tool_provider = self.api_tool_service.get_api_tool_provider(provider_id, account=current_user)

        resp = GetApiToolProviderResp()
        return success_json(resp.dump(api_tool_provider))

    @login_required
    def delete_api_tool_provider(self, provider_id: UUID):
        self.api_tool_service.delete_api_tool_provider(provider_id, account=current_user)
        return success_message("删除成功")

    @login_required
    def validate_openapi_schema(self):
        """校验参数"""
        # 提取数据并校验
        req = ValidateOpenAPISchemaReq()
        if not req.validate():
            return validate_error_json(req.errors)

        # 调用服务解析数据
        self.api_tool_service.parse_openapi_schema(req.openapi_schema.data)
        return success_message("数据校验成功")
