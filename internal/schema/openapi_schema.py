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
@Time    : 2024/12/29 15:01
@Author : rxccai@gmail.com
@File    : openapi_schema.py
"""
import uuid
from urllib.parse import urlparse

from flask_wtf import FlaskForm
from wtforms import StringField, BooleanField
from wtforms.validators import DataRequired, UUID, Optional, ValidationError

from .schema import ListField


class OpenAPIChatReq(FlaskForm):
    """开放API聊天接口请求结构体"""
    app_id = StringField("app_id", validators=[
        DataRequired("应用id不能为空"),
        UUID("应用id格式必须为UUID"),
    ])
    end_user_id = StringField("end_user_id", default="", validators=[
        Optional(),
        UUID("终端用户id必须为UUID"),
    ])
    conversation_id = StringField("conversation_id", default="")
    query = StringField("query", default="", validators=[
        DataRequired("用户提问query不能为空"),
    ])
    image_urls = ListField("image_urls", default=[])
    stream = BooleanField("stream", default=True)

    def validate_conversation_id(self, field: StringField) -> None:
        """自定义校验conversation_id函数"""
        # 检测是否传递数据，如果传递了，则类型必须为UUID
        if field.data:
            try:
                uuid.UUID(field.data)
            except Exception as _:
                raise ValidationError("会话id格式必须为UUID")

            # 终端用户id是不是为空
            if not self.end_user_id.data:
                raise ValidationError("传递会话id则终端用户id不能为空")

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
