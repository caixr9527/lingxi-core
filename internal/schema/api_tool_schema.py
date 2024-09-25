#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2024/9/24 23:31
@Author : rxccai@gmail.com
@File   : api_tool_schema.py
"""
from flask_wtf import FlaskForm
from wtforms import StringField
from wtforms.validators import DataRequired


class ValidateOpenAPISchemaReq(FlaskForm):
    """校验参数"""
    openapi_schema = StringField("openapi_schema", validators=[
        DataRequired(message="openapi_schema不能为空")
    ])
