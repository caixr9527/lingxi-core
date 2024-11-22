#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2024/11/22 21:16
@Author  : rxccai@gmail.com
@File    : account.py
"""
from flask_login import UserMixin
from sqlalchemy import (
    Column,
    UUID,
    String,
    DateTime,
    text,
    PrimaryKeyConstraint,
)

from internal.extension.database_extension import db


class Account(UserMixin, db.Model):
    """账号模型"""
    __tablename__ = "account"
    __table_args__ = (
        PrimaryKeyConstraint("id", name="pk_account_id"),
    )

    id = Column(UUID, nullable=False, server_default=text("uuid_generate_v4()"))
    name = Column(String(255), nullable=False, server_default=text("''::character varying"))
    email = Column(String(255), nullable=False, server_default=text("''::character varying"))
    avatar = Column(String(255), nullable=False, server_default=text("''::character varying"))
    password = Column(String(255), nullable=True, server_default=text("''::character varying"))
    password_salt = Column(String(255), nullable=True, server_default=text("''::character varying"))
    last_login_at = Column(DateTime, nullable=False, server_default=text("CURRENT_TIMESTAMP(0)"))
    last_login_ip = Column(String(255), nullable=False, server_default=text("''::character varying"))
    updated_at = Column(
        DateTime,
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP(0)"),
        server_onupdate=text("CURRENT_TIMESTAMP(0)"),
    )
    created_at = Column(DateTime, nullable=False, server_default=text("CURRENT_TIMESTAMP(0)"))

    @property
    def is_password_set(self) -> bool:
        """只读属性，获取当前账号的密码是否设置"""
        return self.password is not None and self.password != ""


class AccountOAuth(db.Model):
    """账号与第三方授权认证记录表"""
    __tablename__ = "account_oauth"
    __table_args__ = (
        PrimaryKeyConstraint("id", name="pk_account_oauth_id"),
    )

    id = Column(UUID, nullable=False, server_default=text("uuid_generate_v4()"))
    account_id = Column(UUID, nullable=False)
    provider = Column(String(255), nullable=False, server_default=text("''::character varying"))
    openid = Column(String(255), nullable=False, server_default=text("''::character varying"))
    encrypted_token = Column(String(255), nullable=False, server_default=text("''::character varying"))
    updated_at = Column(
        DateTime,
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP(0)"),
        server_onupdate=text("CURRENT_TIMESTAMP(0)"),
    )
    created_at = Column(DateTime, nullable=False, server_default=text("CURRENT_TIMESTAMP(0)"))
