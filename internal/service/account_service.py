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
@Time   : 2024/11/22 22:40
@Author : caixiaorong01@outlook.com
@File   : account_service.py
"""
import base64
import secrets
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any
from uuid import UUID

from flask import request
from injector import inject
from redis import Redis

from internal.exception import FailException
from internal.lib.helper import decode_password, generate_random_string
from internal.model import Account, AccountOAuth
from internal.schema.account_schema import RegisterReq
from pkg.password import hash_password, compare_password
from pkg.sqlalchemy import SQLAlchemy
from .base_service import BaseService
from .jwt_service import JwtService
from .sms_service import SmsService


@inject
@dataclass
class AccountService(BaseService):
    db: SQLAlchemy
    jwt_service: JwtService
    redis_client: Redis
    sms_service: SmsService

    def get_account(self, account_id: UUID) -> Account:
        return self.get(Account, account_id)

    def get_account_oauth_by_provider_name_and_openid(self, provider_name: str, openid: str) -> AccountOAuth:
        return self.db.session.query(AccountOAuth).filter(
            AccountOAuth.provider == provider_name,
            AccountOAuth.openid == openid
        ).one_or_none()

    def get_account_by_email(self, email: str) -> Account:
        return self.db.session.query(Account).filter(
            Account.email == email
        ).one_or_none()

    def create_account(self, **kwargs) -> Account:
        return self.create(Account, **kwargs)

    def send_verification_code(self, email: str):
        key = f"send_verification_code:{email}"
        if self.redis_client.get(key):
            raise FailException("发送验证码过于频繁，请稍后重试")
        code = generate_random_string(6)
        self.sms_service.send_email(
            email,
            f"您正在进行邮箱验证。您的验证码为:{code}\n\n\n验证码 5 分钟内有效，如果不是本人操作，请忽略。",
            "不懂就问-AI应用开发平台邮箱验证邮件")
        self.redis_client.setex(key, 60, 1)
        self.redis_client.setex(f"verification_code:{email}", 60 * 5, code)

    def register(self, req: RegisterReq):
        email = req.email.data
        verification_code = req.verificationCode.data

        account = self.get_account_by_email(email)
        if account:
            raise FailException("邮箱已存在。")
        key = f"verification_code:{email}"
        code = self.redis_client.get(key)
        if not code:
            raise FailException("验证码失效，请重试。")
        if code.decode() != verification_code:
            raise FailException("验证码错误，请重试。")

        self.redis_client.delete(key)

        password = decode_password(req.password.data)
        confirm_password = decode_password(req.confirmPassword.data)
        if len(password) < 8 or len(password) > 16:
            raise FailException("密码长度在8-16位。")
        if password != confirm_password:
            raise FailException("两次输入密码不一致。")

        salt = secrets.token_bytes(16)
        base64_salt = base64.b64encode(salt).decode()
        password_hashed = hash_password(password, salt)
        base64_password_hashed = base64.b64encode(password_hashed).decode()
        self.create_account(
            name=f"user_{generate_random_string(10)}",
            email=email,
            password=base64_password_hashed,
            password_salt=base64_salt
        )

    def update_password(self, password: str, account: Account) -> Account:
        """更新当前账号密码信息"""
        password = decode_password(password)
        salt = secrets.token_bytes(16)
        base64_salt = base64.b64encode(salt).decode()
        password_hashed = hash_password(password, salt)
        base64_password_hashed = base64.b64encode(password_hashed).decode()
        self.update_account(account, password=base64_password_hashed, password_salt=base64_salt)
        return account

    def update_account(self, account: Account, **kwargs) -> Account:
        """根据传递的信息更新账号"""
        self.update(account, **kwargs)
        return account

    def password_login(self, email: str, password: str) -> dict[str, Any]:
        """根据传递的密码+邮箱登录特定的账号"""
        # 根据传递的邮箱查询账号是否存在
        account = self.get_account_by_email(email)
        if not account:
            raise FailException("账号或者密码错误，请核实后重试")

        password = decode_password(password)

        # 校验账号密码是否正确
        if not account.is_password_set or not compare_password(
                password,
                account.password,
                account.password_salt,
        ):
            raise FailException("账号或者密码错误，请核实后重试")

        # 生成凭证信息
        expire_at = int((datetime.now() + timedelta(days=1)).timestamp())
        payload = {
            "sub": str(account.id),
            "iss": "llmops",
            "exp": expire_at,
        }
        access_token = self.jwt_service.generate_token(payload)

        # 更新账号的登录信息
        self.update(
            account,
            last_login_at=datetime.now(),
            last_login_ip=request.remote_addr,
        )

        return {
            "expire_at": expire_at,
            "access_token": access_token,
        }
