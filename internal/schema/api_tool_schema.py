#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2024/9/24 23:31
@Author : rxccai@gmail.com
@File   : api_tool_schema.py
"""
from flask_wtf import FlaskForm
from wtforms import StringField, ValidationError
from wtforms.validators import DataRequired, Length, URL

from .schema import ListField


class ValidateOpenAPISchemaReq(FlaskForm):
    """校验参数"""
    openapi_schema = StringField("openapi_schema", validators=[
        DataRequired(message="openapi_schema不能为空")
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
    headers = ListField("headers")

    @classmethod
    def validate_headers(cls, form, field):
        """校验headers数据"""
        for header in field.data:
            if not isinstance(header, dict):
                raise ValidationError("headers元素类型错误")
            if set(header.keys()) != {"key", "value"}:
                raise ValidationError("headers里面必须包含key和value")
