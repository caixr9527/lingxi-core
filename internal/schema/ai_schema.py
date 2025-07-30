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
@Time   : 2024/12/8 21:50
@Author : caixiaorong01@outlook.com
@File    : ai_schema.py
"""
from flask_wtf import FlaskForm
from wtforms import StringField
from wtforms.validators import DataRequired, UUID, Length


class GenerateSuggestedQuestionsReq(FlaskForm):
    """生成建议问题列表请求结构体"""
    message_id = StringField("message_id", validators=[
        DataRequired("消息id不能为空"),
        UUID(message="消息id格式必须为uuid")
    ])


class OptimizePromptReq(FlaskForm):
    """优化预设prompt请求结构体"""
    prompt = StringField("prompt", validators=[
        DataRequired("预设prompt不能为空"),
        Length(max=2000, message="预设prompt的长度不能超过2000个字符")
    ])


class AutoGeneratePromptReq(FlaskForm):
    app_id = StringField("app_id", validators=[
        DataRequired("应用id不能为空")
    ])
