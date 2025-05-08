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
@Time   : 2024/12/28 17:50
@Author : caixiaorong01@outlook.com
@File    : api_key_schema.py
"""
from flask_wtf import FlaskForm
from marshmallow import Schema, fields, pre_dump
from wtforms import BooleanField, StringField
from wtforms.validators import Length

from internal.lib.helper import datetime_to_timestamp
from internal.model import ApiKey


class CreateApiKeyReq(FlaskForm):
    """创建API秘钥请求"""
    is_active = BooleanField("is_active")
    remark = StringField("remark", validators=[
        Length(max=100, message="秘钥备注不能超过100个字符")
    ])


class UpdateApiKeyReq(FlaskForm):
    """更新API秘钥请求"""
    is_active = BooleanField("is_active")
    remark = StringField("remark", validators=[
        Length(max=100, message="秘钥备注不能超过100个字符")
    ])


class UpdateApiKeyIsActiveReq(FlaskForm):
    """更新API秘钥激活请求"""
    is_active = BooleanField("is_active")


class GetApiKeysWithPageResp(Schema):
    """获取API秘钥分页列表数据"""
    id = fields.UUID(dump_default="")
    api_key = fields.String(dump_default="")
    is_active = fields.Boolean(dump_default=False)
    remark = fields.String(dump_default="")
    updated_at = fields.Integer(dump_default=0)
    created_at = fields.Integer(dump_default=0)

    @pre_dump
    def process_data(self, data: ApiKey, **kwargs):
        return {
            "id": data.id,
            "api_key": data.api_key,
            "is_active": data.is_active,
            "remark": data.remark,
            "updated_at": datetime_to_timestamp(data.updated_at),
            "created_at": datetime_to_timestamp(data.created_at),
        }
