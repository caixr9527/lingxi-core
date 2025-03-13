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
@Time    : 2025/01/02 22:30
@Author  : rxccai@gmail.com
@File    : builtin_app_handler.py
"""
from dataclasses import dataclass

from flask_login import login_required, current_user
from injector import inject

from internal.schema.builtin_app_schema import (
    GetBuiltinAppCategoriesResp,
    GetBuiltinAppsResp,
    AddBuiltinAppToSpaceReq,
)
from internal.service import BuiltinAppService
from pkg.response import success_json, validate_error_json


@inject
@dataclass
class BuiltinAppHandler:
    """LLMOps内置应用处理器"""
    builtin_app_service: BuiltinAppService

    @login_required
    def get_builtin_app_categories(self):
        """获取内置应用分类列表信息"""
        categories = self.builtin_app_service.get_categories()
        resp = GetBuiltinAppCategoriesResp(many=True)
        return success_json(resp.dump(categories))

    @login_required
    def get_builtin_apps(self):
        """获取所有内置应用列表信息"""
        builtin_apps = self.builtin_app_service.get_builtin_apps()
        resp = GetBuiltinAppsResp(many=True)
        return success_json(resp.dump(builtin_apps))

    @login_required
    def add_builtin_app_to_space(self):
        """将指定的内置应用添加到个人空间"""
        # 提取请求并校验
        req = AddBuiltinAppToSpaceReq()
        if not req.validate():
            return validate_error_json(req.errors)

        # 将指定内置应用模板添加到个人空间
        app = self.builtin_app_service.add_builtin_app_to_space(req.builtin_app_id.data, current_user)

        return success_json({"id": app.id})
