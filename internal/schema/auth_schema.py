#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2024/11/23 15:33
@Author  : rxccai@gmail.com
@File    : auth_schema.py
"""
from flask_wtf import FlaskForm
from marshmallow import Schema, fields
from wtforms import StringField
from wtforms.validators import DataRequired, Email, Length, regexp

from pkg.password import password_pattern


class PasswordLoginReq(FlaskForm):
    """账号密码登录请求结构"""
    email = StringField("email", validators=[
        DataRequired("登录邮箱不能为空"),
        Email("登录邮箱格式错误"),
        Length(min=5, max=254, message="登录邮箱长度在5-254个字符"),
    ])
    password = StringField("password", validators=[
        DataRequired("账号密码不能为空"),
        regexp(regex=password_pattern, message="密码最少包含一个字母，一个数字，并且长度为8-16")
    ])


class PasswordLoginResp(Schema):
    """账号密码授权认证响应结构"""
    access_token = fields.String()
    expire_at = fields.Integer()
