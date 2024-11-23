#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2024/11/22 22:40
@Author : rxccai@gmail.com
@File   : account_service.py
"""
from dataclasses import dataclass
from uuid import UUID

from injector import inject

from internal.model import Account, AccountOAuth
from pkg.sqlalchemy import SQLAlchemy
from .base_service import BaseService


@inject
@dataclass
class AccountService(BaseService):
    db: SQLAlchemy

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
