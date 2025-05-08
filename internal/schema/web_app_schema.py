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
@Time   : 2025/2/17 21:50
@Author : caixiaorong01@outlook.com
@File    : web_app_schema.py
"""
from urllib.parse import urlparse

from flask_wtf import FlaskForm
from marshmallow import Schema, fields, pre_dump
from wtforms import StringField, BooleanField
from wtforms.validators import DataRequired, Optional, UUID, ValidationError

from internal.lib.helper import datetime_to_timestamp
from internal.model import Conversation
from .schema import ListField


class WebAppChatReq(FlaskForm):
    """WebApp对话请求结构体"""
    conversation_id = StringField("conversation_id", default="", validators=[
        Optional(),
        UUID(message="会话id格式必须为uuid")
    ])
    query = StringField("query", default="", validators=[
        DataRequired(message="用户提问query不能为空")
    ])
    image_urls = ListField("image_urls", default=[])

    def validate_image_urls(self, field: ListField) -> None:
        """校验传递的图片URL链接列表"""
        # 校验数据类型如果为None则设置默认值空列表
        if not isinstance(field.data, list):
            return []

        # 校验数据的长度，最多不能超过5条URL记录
        if len(field.data) > 5:
            raise ValidationError("上传的图片数量不能超过5，请核实后重试")

        # 循环校验image_url是否为URL
        for image_url in field.data:
            result = urlparse(image_url)
            if not all([result.scheme, result.netloc]):
                raise ValidationError("上传的图片URL地址格式错误，请核实后重试")


class GetConversationsReq(FlaskForm):
    """获取WebApp会话列表请求结构体"""
    is_pinned = BooleanField("is_pinned", default=False)


class GetConversationsResp(Schema):
    """获取WebApp会话列表响应结构体"""
    id = fields.UUID(dump_default="")
    name = fields.String(dump_default="")
    summary = fields.String(dump_default="")
    created_at = fields.Integer(dump_default=0)

    @pre_dump
    def process_data(self, data: Conversation, **kwargs):
        return {
            "id": data.id,
            "name": data.name,
            "summary": data.summary,
            "created_at": datetime_to_timestamp(data.created_at),
        }
