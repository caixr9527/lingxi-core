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
@Time   : 2024/11/23 15:25
@Author : caixiaorong01@outlook.com
@File   : auth_handler.py
"""
from dataclasses import dataclass

from flask_login import logout_user, login_required
from injector import inject

from internal.schema.auth_schema import PasswordLoginReq, PasswordLoginResp
from internal.service import AccountService
from pkg.response import success_message, validate_error_json, success_json


@inject
@dataclass
class AuthHandler:
    account_service: AccountService

    def password_login(self):
        req = PasswordLoginReq()
        if not req.validate():
            return validate_error_json(req.errors)
        credential = self.account_service.password_login(req.email.data, req.password.data)
        resp = PasswordLoginResp()
        return success_json(resp.dump(credential))

    @login_required
    def logout(self):
        logout_user()
        return success_message("退出登陆成功")
