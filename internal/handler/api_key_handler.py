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
@Time   : 2024/12/28 17:49
@Author : rxccai@gmail.com
@File    : api_key_handler.py
"""
from dataclasses import dataclass
from uuid import UUID

from flask import request
from flask_login import login_required, current_user
from injector import inject

from internal.schema.api_key_schema import (
    CreateApiKeyReq,
    UpdateApiKeyReq,
    UpdateApiKeyIsActiveReq,
    GetApiKeysWithPageResp,
)
from internal.service import ApiKeyService
from pkg.paginator import PaginatorReq, PageModel
from pkg.response import validate_error_json, success_message, success_json


@inject
@dataclass
class ApiKeyHandler:
    api_key_service: ApiKeyService

    @login_required
    def create_api_key(self):
        """创建API秘钥"""
        req = CreateApiKeyReq()
        if not req.validate():
            return validate_error_json(req.errors)

        self.api_key_service.create_api_key(req, current_user)

        return success_message("创建API秘钥成功")

    @login_required
    def delete_api_key(self, api_key_id: UUID):
        """根据传递的id删除API秘钥"""
        self.api_key_service.delete_api_key(api_key_id, current_user)
        return success_message("删除API秘钥成功")

    @login_required
    def update_api_key(self, api_key_id: UUID):
        """根据传递的信息更新API秘钥"""
        req = UpdateApiKeyReq()
        print(req.data)
        if not req.validate():
            return validate_error_json(req.errors)

        self.api_key_service.update_api_key(api_key_id, current_user, **req.data)

        return success_message("更新API秘钥成功")

    @login_required
    def update_api_key_is_active(self, api_key_id: UUID):
        """根据传递的信息更新API秘钥激活状态"""
        req = UpdateApiKeyIsActiveReq()
        if not req.validate():
            return validate_error_json(req.errors)

        self.api_key_service.update_api_key(api_key_id, current_user, **req.data)

        return success_message("更新API秘钥激活状态成功")

    @login_required
    def get_api_keys_with_page(self):
        """获取当前登录账号的API秘钥分页列表信息"""
        req = PaginatorReq(request.args)
        if not req.validate():
            return validate_error_json(req.errors)

        api_keys, paginator = self.api_key_service.get_api_keys_with_page(req, current_user)

        resp = GetApiKeysWithPageResp(many=True)

        return success_json(PageModel(list=resp.dump(api_keys), paginator=paginator))
