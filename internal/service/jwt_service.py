#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2024/11/22 21:58
@Author : rxccai@gmail.com
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
