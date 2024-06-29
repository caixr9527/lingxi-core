#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2024/6/29 21:01
@Author : rxccai@gmail.com
@File   : app_schema.py
"""
from flask_wtf import FlaskForm
from wtforms import StringField
from wtforms.validators import DataRequired, Length


class CompletionReq(FlaskForm):
    """基础聊天接口请求校验"""
    query = StringField("query", validators=[
        DataRequired(message="用户的提问是必填"),
        Length(max=2000, message="用户的提问最大长度是2000")
    ])
