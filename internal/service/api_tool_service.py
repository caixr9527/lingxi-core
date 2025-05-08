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
@Time   : 2024/9/24 23:35
@Author : caixiaorong01@outlook.com
@File   : api_tool_service.py
"""
import json
from dataclasses import dataclass
from typing import Any
from uuid import UUID

from injector import inject
from sqlalchemy import desc

from internal.core.tools.api_tools.entites import OpenAPISchema
from internal.core.tools.api_tools.providers import ApiProviderManager
from internal.exception import ValidateException, NotFoundException
from internal.model import ApiToolProvider, ApiTool, Account
from internal.schema.api_tool_schema import CreateApiToolReq, GetApiToolProvidersWithPageReq, UpdateApiToolProviderReq
from pkg.paginator import Paginator
from pkg.sqlalchemy import SQLAlchemy
from .base_service import BaseService


@inject
@dataclass
class ApiToolService(BaseService):
    """自定义api插件服务"""
    db: SQLAlchemy
    api_provider_manager: ApiProviderManager

    def update_api_tool_provider(self,
                                 provider_id: UUID,
                                 req: UpdateApiToolProviderReq,
                                 account: Account):
        api_tool_provider = self.get(ApiToolProvider, provider_id)
        if api_tool_provider is None or api_tool_provider.account_id != account.id:
            raise ValidateException("该工具提供者不存在")
        openapi_schema = self.parse_openapi_schema(req.openapi_schema.data)
        check_api_tool_provider = self.db.session.query(ApiToolProvider).filter(
            ApiToolProvider.account_id == account.id,
            ApiToolProvider.name == req.name.data,
            ApiToolProvider.id != api_tool_provider.id
        ).one_or_none()
        if check_api_tool_provider:
            raise ValidateException(f"该工具提供者{req.name.data}已存在")
        with self.db.auto_commit():
            self.db.session.query(ApiTool).filter(
                ApiTool.provider_id == api_tool_provider.id,
                ApiTool.account_id == account.id
            ).delete()

        self.update(
            api_tool_provider,
            name=req.name.data,
            icon=req.icon.data,
            headers=req.headers.data,
            description=openapi_schema.description,
            openapi_schema=req.openapi_schema.data,
        )

        for path, path_item in openapi_schema.paths.items():
            for method, method_item in path_item.items():
                self.create(
                    ApiTool,
                    account_id=account.id,
                    provider_id=api_tool_provider.id,
                    name=method_item.get("operationId"),
                    description=method_item.get("description"),
                    url=f"{openapi_schema.server}{path}",
                    method=method,
                    parameters=method_item.get("parameters", []),
                )

    def get_api_tool_providers_with_page(self,
                                         req: GetApiToolProvidersWithPageReq,
                                         account: Account) -> tuple[list[Any], Paginator]:
        paginator = Paginator(db=self.db, req=req)
        filters = [ApiToolProvider.account_id == account.id]
        if req.search_word.data:
            filters.append(ApiToolProvider.name.ilike(f"%{req.search_word.data}%"))
        api_tool_providers = paginator.paginate(
            self.db.session.query(ApiToolProvider).filter(*filters).order_by(desc("created_at"))
        )
        return api_tool_providers, paginator

    def get_api_tool(self, provider_id: UUID, tool_name: str, account: Account) -> ApiTool:
        api_tool = self.db.session.query(ApiTool).filter_by(
            provider_id=provider_id,
            name=tool_name,
        ).one_or_none()
        if api_tool is None or api_tool.account_id != account.id:
            raise NotFoundException("该工具不存在")
        return api_tool

    def get_api_tool_provider(self, provider_id: UUID, account: Account) -> ApiToolProvider:
        api_tool_provider = self.get(ApiToolProvider, provider_id)
        if api_tool_provider is None or api_tool_provider.account_id != account.id:
            raise NotFoundException("该工具提供者不存在")
        return api_tool_provider

    def create_api_tool(self, req: CreateApiToolReq, account: Account) -> None:
        openapi_schema = self.parse_openapi_schema(req.openapi_schema.data)
        api_tool_provider = self.db.session.query(ApiToolProvider).filter_by(
            account_id=account.id,
            name=req.name.data
        ).one_or_none()
        if api_tool_provider:
            raise ValidateException(f"该工具{req.name.data}已存在")
        api_tool_provider = self.create(
            ApiToolProvider,
            account_id=account.id,
            name=req.name.data,
            icon=req.icon.data,
            description=openapi_schema.description,
            openapi_schema=req.openapi_schema.data,
            headers=req.headers.data,
        )

        for path, path_item in openapi_schema.paths.items():
            for method, method_item in path_item.items():
                self.create(
                    ApiTool,
                    account_id=account.id,
                    provider_id=api_tool_provider.id,
                    name=method_item.get("operationId"),
                    description=method_item.get("description"),
                    url=f"{openapi_schema.server}{path}",
                    method=method,
                    parameters=method_item.get("parameters", []),
                )

    def delete_api_tool_provider(self, provider_id: UUID, account: Account):
        api_tool_provider = self.get(ApiToolProvider, provider_id)
        if api_tool_provider is None or api_tool_provider.account_id != account.id:
            raise NotFoundException("工具提供者不存在")

        with self.db.auto_commit():
            self.db.session.query(ApiTool).filter(
                ApiTool.provider_id == provider_id,
                ApiTool.account_id == account.id,
            ).delete()
            self.db.session.delete(api_tool_provider)

    @classmethod
    def parse_openapi_schema(cls, openapi_schema_str: str) -> OpenAPISchema:
        try:
            data = json.loads(openapi_schema_str.strip())
            if not isinstance(data, dict):
                raise
        except Exception as e:
            raise ValidateException("格式错误")
        return OpenAPISchema(**data)
