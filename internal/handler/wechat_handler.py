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
@Time   : 2025/3/11 21:44
@Author : caixiaorong01@outlook.com
@File   : wechat_handler.py
"""
from dataclasses import dataclass
from uuid import UUID

from injector import inject

from internal.service import WechatService


@inject
@dataclass
class WechatHandler:
    """微信公众号服务服务"""
    wechat_service: WechatService

    def wechat(self, app_id: UUID):
        """Agent微信API校验与消息推送"""
        return self.wechat_service.wechat(app_id)
