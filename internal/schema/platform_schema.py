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
@Time   : 2025/3/11 21:39
@Author : rxccai@gmail.com
@File   : platform_schema.py
"""
import os

from flask_wtf import FlaskForm
from marshmallow import Schema, fields, pre_dump
from wtforms import StringField
from wtforms.validators import Optional

from internal.lib.helper import datetime_to_timestamp
from internal.model import WechatConfig


class GetWechatConfigResp(Schema):
    """获取微信配置响应结构"""
    app_id = fields.UUID(dump_default="")
    url = fields.String(dump_default="")
    ip = fields.String(dump_default="")
    wechat_app_id = fields.String(dump_default="")
    wechat_app_secret = fields.String(dump_default="")
    wechat_token = fields.String(dump_default="")
    status = fields.String(dump_default="")
    updated_at = fields.Integer(dump_default=0)
    created_at = fields.Integer(dump_default=0)

    @pre_dump
    def process_data(self, data: WechatConfig, **kwargs):
        return {
            "app_id": data.app_id,
            "url": f"{os.getenv('SERVICE_API_PREFIX', '')}/wechat/{str(data.app_id)}",
            "ip": os.getenv("SERVICE_IP", ""),
            "wechat_app_id": data.wechat_app_id,
            "wechat_app_secret": data.wechat_app_secret,
            "wechat_token": data.wechat_token,
            "status": data.status,
            "updated_at": datetime_to_timestamp(data.updated_at),
            "created_at": datetime_to_timestamp(data.created_at),
        }


class UpdateWechatConfigReq(FlaskForm):
    """更新微信配置请求"""
    wechat_app_id = StringField("wechat_app_id", default="", validators=[Optional()])
    wechat_app_secret = StringField("wechat_app_secret", default="", validators=[Optional()])
    wechat_token = StringField("wechat_token", default="", validators=[Optional()])
