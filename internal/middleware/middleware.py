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
from internal.service import JwtService, AccountService, ApiKeyService


@inject
@dataclass
class Middleware:
    jwt_service: JwtService
    account_service: AccountService
    api_key_service: ApiKeyService

    def request_loader(self, request: Request) -> Optional[Account]:
        if request.blueprint == 'llmops':
            access_token = self._validate_credential(request)

            payload = self.jwt_service.parse_token(access_token)
            account_id = payload.get("sub")
            return self.account_service.get_account(account_id)
        elif request.blueprint == 'openapi':
            api_key = self._validate_credential(request)
            api_key_record = self.api_key_service.get_api_by_credential(api_key)

            if not api_key_record or not api_key_record.is_active:
                raise UnauthorizedException("该秘钥不存在或未激活")

            return api_key_record.account
        else:
            return None

    @classmethod
    def _validate_credential(cls, request: Request) -> str:
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            raise UnauthorizedException("未授权，请登陆后尝试")

        if " " not in auth_header:
            raise UnauthorizedException("授权失败，请重新登陆后尝试")

        auth_schema, credential = auth_header.split(None, 1)
        if auth_schema.lower() != "bearer":
            raise UnauthorizedException("授权失败，认证格式错误，请重试")

        return credential
