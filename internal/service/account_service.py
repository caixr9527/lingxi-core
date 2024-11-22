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

from internal.model import Account
from pkg.sqlalchemy import SQLAlchemy
from .base_service import BaseService


@inject
@dataclass
class AccountService(BaseService):
    db: SQLAlchemy

    def get_account(self, account_id: UUID) -> Account:
        return self.get(Account, account_id)
