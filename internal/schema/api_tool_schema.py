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
@Time   : 2024/9/24 23:31
@Author : caixiaorong01@outlook.com
@File   : api_tool_schema.py
"""
from flask_wtf import FlaskForm
from marshmallow import Schema, fields, pre_dump
from wtforms import StringField, ValidationError
from wtforms.validators import DataRequired, Length, URL, Optional

from internal.model import ApiToolProvider, ApiTool
from pkg.paginator import PaginatorReq
from .schema import ListField


class ValidateOpenAPISchemaReq(FlaskForm):
    """校验参数"""
    openapi_schema = StringField("openapi_schema", validators=[
        DataRequired(message="openapi_schema不能为空")
    ])


class GetApiToolProvidersWithPageReq(PaginatorReq):
    search_word = StringField("search_word", validators=[
        Optional()
    ])


class CreateApiToolReq(FlaskForm):
    """创建自定义API工具请求"""
    name = StringField("name", validators=[
        DataRequired(message="工具提供者名字不能为空"),
        Length(min=1, max=30, message="工具提供者的名字长度在1-30")
    ])
    icon = StringField("icon", validators=[
        DataRequired(message="icon不能为空"),
        URL(message="icon必须是URL链接")
    ])
    openapi_schema = StringField("openapi_schema", validators=[
        DataRequired(message="openapi_schema字符串不能为空")
    ])
    headers = ListField("headers", default=[])

    @classmethod
    def validate_headers(cls, form, field):
        """校验headers数据"""
        for header in field.data:
            if not isinstance(header, dict):
                raise ValidationError("headers元素类型错误")
            if set(header.keys()) != {"key", "value"}:
                raise ValidationError("headers里面必须包含key和value")


class UpdateApiToolProviderReq(FlaskForm):
    name = StringField("name", validators=[
        DataRequired(message="工具提供者名字不能为空"),
        Length(min=1, max=30, message="工具提供者的名字长度在1-30")
    ])
    icon = StringField("icon", validators=[
        DataRequired(message="icon不能为空"),
        URL(message="icon必须是URL链接")
    ])
    openapi_schema = StringField("openapi_schema", validators=[
        DataRequired(message="openapi_schema字符串不能为空")
    ])
    headers = ListField("headers", default=[])

    @classmethod
    def validate_headers(cls, form, field):
        """校验headers数据"""
        for header in field.data:
            if not isinstance(header, dict):
                raise ValidationError("headers元素类型错误")
            if set(header.keys()) != {"key", "value"}:
                raise ValidationError("headers里面必须包含key和value")


class GetApiToolProviderResp(Schema):
    id = fields.UUID()
    name = fields.String()
    icon = fields.String()
    openapi_schema = fields.String()
    headers = fields.List(fields.Dict, dump_default=[])
    created_at = fields.Integer(dump_default=0)

    @pre_dump
    def process_data(self, data: ApiToolProvider, **kwargs):
        return {
            "id": data.id,
            "name": data.name,
            "icon": data.icon,
            "openapi_schema": data.openapi_schema,
            "headers": data.headers,
            "created_at": int(data.created_at.timestamp()),
        }


class GetApiToolResp(Schema):
    id = fields.UUID()
    name = fields.String()
    description = fields.String()
    inputs = fields.List(fields.Dict, dump_default=[])
    provider = fields.Dict()

    @pre_dump
    def process_data(self, data: ApiTool, **kwargs):
        provider = data.provider
        return {
            "id": data.id,
            "name": data.name,
            "description": data.description,
            "inputs": [{k: v for k, v in parameter.items() if k != "in"} for parameter in data.parameters],
            "provider": {
                "id": provider.id,
                "name": provider.name,
                "icon": provider.icon,
                "description": provider.description,
                "headers": provider.headers,
            }
        }


class GetApiToolProvidersWithPageResp(Schema):
    id = fields.UUID()
    name = fields.String()
    icon = fields.String()
    description = fields.String()
    headers = fields.List(fields.Dict, dump_default=[])
    tools = fields.List(fields.Dict, dump_default=[])
    created_at = fields.Integer(dump_default=0)

    @pre_dump
    def process_data(self, data: ApiToolProvider, **kwargs):
        tools = data.tools
        return {
            "id": data.id,
            "name": data.name,
            "icon": data.icon,
            "description": data.description,
            "headers": data.headers,
            "tools": [{
                "id": tool.id,
                "description": tool.description,
                "name": tool.name,
                "inputs": [
                    {k: v for k, v in parameter.items() if k != "in"} for parameter in tool.parameters
                ]
            } for tool in tools],
            "created_at": int(data.created_at.timestamp())
        }
