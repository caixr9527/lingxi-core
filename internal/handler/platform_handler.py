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
@Time   : 2025/3/11 21:38
@Author : caixiaorong01@outlook.com
@File   : platform_handler.py
"""
from dataclasses import dataclass
from uuid import UUID

from flask_login import login_required, current_user
from injector import inject
from internal.schema.platform_schema import GetWechatConfigResp, UpdateWechatConfigReq

from internal.service import PlatformService
from pkg.response import success_json, validate_error_json, success_message


@inject
@dataclass
class PlatformHandler:
    """第三方平台处理器"""
    platform_service: PlatformService

    @login_required
    def get_wechat_config(self, app_id: UUID):
        """根据传递的id获取指定应用的微信配置"""
        wechat_config = self.platform_service.get_wechat_config(app_id, current_user)

        resp = GetWechatConfigResp()

        return success_json(resp.dump(wechat_config))

    @login_required
    def update_wechat_config(self, app_id: UUID):
        """根据传递的应用id更新该应用的微信发布配置"""
        req = UpdateWechatConfigReq()
        if not req.validate():
            return validate_error_json(req.errors)

        self.platform_service.update_wechat_config(app_id, req, current_user)

        return success_message("更新Agent应用微信公众号配置成功")
