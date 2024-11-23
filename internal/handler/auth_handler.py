#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2024/11/23 15:25
@Author : rxccai@gmail.com
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
        # todo 未清除token退出登陆
        logout_user()
        return success_message("退出登陆成功")
