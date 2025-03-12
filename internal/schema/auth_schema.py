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
@Time    : 2024/11/23 15:33
@Author  : rxccai@gmail.com
@File    : auth_schema.py
"""
from flask_wtf import FlaskForm
from marshmallow import Schema, fields
from wtforms import StringField
from wtforms.validators import DataRequired, Email, Length


class PasswordLoginReq(FlaskForm):
    """账号密码登录请求结构"""
    email = StringField("email", validators=[
        DataRequired("登录邮箱不能为空"),
        Email("登录邮箱格式错误"),
        Length(min=5, max=254, message="登录邮箱长度在5-254个字符"),
    ])
    password = StringField("password", validators=[
        DataRequired("账号密码不能为空")
    ])


class PasswordLoginResp(Schema):
    """账号密码授权认证响应结构"""
    access_token = fields.String()
    expire_at = fields.Integer()
