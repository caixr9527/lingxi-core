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
@Time   : 2024/11/22 21:58
@Author : caixiaorong01@outlook.com
@File   : jwt_service.py
"""
import os
from dataclasses import dataclass
from typing import Any

import jwt
from injector import inject

from internal.exception import UnauthorizedException


@inject
@dataclass
class JwtService:

    @classmethod
    def generate_token(cls, payload: dict[str, Any]) -> str:
        secret_key = os.getenv("JWT_SECRET_KEY")
        return jwt.encode(payload, secret_key, algorithm="HS256")

    @classmethod
    def parse_token(cls, token: str) -> dict[str, Any]:
        secret_key = os.getenv("JWT_SECRET_KEY")
        try:
            return jwt.decode(token, secret_key, algorithms=["HS256"])
        except jwt.ExpiredSignatureError:
            raise UnauthorizedException("登陆凭证已过期请重新登陆")
        except jwt.InvalidTokenError:
            raise UnauthorizedException("解析token错误，请重新登陆")
        except Exception as e:
            raise UnauthorizedException(str(e))
