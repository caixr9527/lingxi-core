#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2024/9/24 23:35
@Author : rxccai@gmail.com
@File   : api_tool_service.py
"""
import json
from dataclasses import dataclass
from uuid import UUID

from injector import inject

from internal.core.tools.api_tools.entites import OpenAPISchema
from internal.exception import ValidateException, NotFoundException
from internal.model import ApiToolProvider, ApiTool
from internal.schema.api_tool_schema import CreateApiToolReq
from pkg.sqlalchemy import SQLAlchemy


@inject
@dataclass
class ApiToolService:
    """自定义api插件服务"""
    db: SQLAlchemy

    def get_api_tool(self, provider_id: UUID, tool_name: str) -> ApiTool:
        # todo
        account_id = "e7300838-b215-4f97-b420-2333a699e22e"
        api_tool = self.db.session.query(ApiTool).filter_by(
            provider_id=provider_id,
            name=tool_name,
        ).one_or_none()
        if api_tool is None or str(api_tool.account_id) != account_id:
            raise NotFoundException("该工具不存在")
        return api_tool

    def get_api_tool_provider(self, provider_id: UUID) -> ApiToolProvider:
        # todo
        account_id = "e7300838-b215-4f97-b420-2333a699e22e"
        api_tool_provider = self.db.session.query(ApiToolProvider).get(provider_id)
        if api_tool_provider is None or str(api_tool_provider.account_id) != account_id:
            raise NotFoundException("该工具提供者不存在")
        return api_tool_provider

    def create_api_tool(self, req: CreateApiToolReq) -> None:
        # todo
        account_id = "e7300838-b215-4f97-b420-2333a699e22e"
        openapi_schema = self.parse_openapi_schema(req.openapi_schema.data)
        api_tool_provider = self.db.session.query(ApiToolProvider).filter_by(
            account_id=account_id,
            name=req.name.data
        ).one_or_none()
        if api_tool_provider:
            raise ValidateException(f"该工具{req.name.data}已存在")
        with self.db.auto_commit():
            api_tool_provider = ApiToolProvider(
                account_id=account_id,
                name=req.name.data,
                icon=req.icon.data,
                description=openapi_schema.description,
                openapi_schema=req.openapi_schema.data,
                headers=req.headers.data,
            )
            self.db.session.add(api_tool_provider)
            self.db.session.flush()
            for path, path_item in openapi_schema.paths.items():
                for method, method_item in path_item.items():
                    api_tool = ApiTool(
                        account_id=account_id,
                        provider_id=api_tool_provider.id,
                        name=method_item.get("operationId"),
                        description=method_item.get("description"),
                        url=f"{openapi_schema.server}{path}",
                        method=method,
                        parameters=method_item.get("parameters", []),
                    )
                    self.db.session.add(api_tool)

    def delete_api_tool_provider(self, provider_id: UUID):
        # todo
        account_id = "e7300838-b215-4f97-b420-2333a699e22e"
        api_tool_provider = self.db.session.query(ApiToolProvider).get(provider_id)
        if api_tool_provider is None or str(api_tool_provider.account_id) != account_id:
            raise NotFoundException("工具提供者不存在")

        with self.db.auto_commit():
            self.db.session.query(ApiTool).filter(
                ApiTool.provider_id == provider_id,
                ApiTool.account_id == account_id,
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
