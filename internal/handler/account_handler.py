#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2024/11/23 14:18
@Author : rxccai@gmail.com
@File   : account_handler.py
"""
from dataclasses import dataclass

from flask_login import login_required, current_user
from injector import inject

from internal.schema.account_schema import GetCurrentUserResp, UpdatePasswordReq, UpdateNameReq, UpdateAvatarReq
from internal.service import AccountService
from pkg.response import success_json, validate_error_json, success_message


@inject
@dataclass
class AccountHandler:
    account_service: AccountService

    @login_required
    def get_current_user(self):
        resp = GetCurrentUserResp()
        return success_json(resp.dump(current_user))

    @login_required
    def update_password(self):
        req = UpdatePasswordReq()
        if not req.validate():
            return validate_error_json(req.errors)
        self.account_service.update_password(req.password.data, account=current_user)
        return success_message("修改密码成功")

    @login_required
    def update_name(self):
        req = UpdateNameReq()
        if not req.validate():
            return validate_error_json(req.errors)
        self.account_service.update_account(current_user, name=req.name.data)

        return success_message("更新账号名称成功")

    @login_required
    def update_avatar(self):
        req = UpdateAvatarReq()
        if not req.validate():
            return validate_error_json(req.errors)
        self.account_service.update_account(current_user, avatar=req.avatar.data)

        return success_message("更新账号头像成功")
