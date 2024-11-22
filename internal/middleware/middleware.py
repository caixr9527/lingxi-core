#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2024/11/22 22:28
@Author : rxccai@gmail.com
@File   : middleware.py
"""
from dataclasses import dataclass
from typing import Optional

from flask import Request
from injector import inject

from internal.exception import UnauthorizedException
from internal.model import Account
from internal.service import JwtService, AccountService


@inject
@dataclass
class Middleware:
    jwt_service: JwtService
    account_service: AccountService

    def request_loader(self, request: Request) -> Optional[Account]:
        if request.blueprint == 'llmops':
            auth_header = request.headers.get("Authorization")
            if not auth_header:
                raise UnauthorizedException("未授权，请登陆后尝试")

            if " " not in auth_header:
                raise UnauthorizedException("授权失败，请重新登陆后尝试")

            auth_schema, access_token = auth_header.split(None, 1)
            if auth_schema.lower() != "bearer":
                raise UnauthorizedException("授权失败，认证格式错误，请重试")

            payload = self.jwt_service.parse_token(access_token)
            account_id = payload.get("sub")
            return self.account_service.get_account(account_id)
        else:
            return None
