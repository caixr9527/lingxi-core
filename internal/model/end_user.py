#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2024/12/28 16:13
@Author  : rxccai@gmail.com
@File    : end_user.py
"""
from sqlalchemy import (
    Column,
    UUID,
    DateTime,
    text,
    PrimaryKeyConstraint
)

from internal.extension.database_extension import db


class EndUser(db.Model):
    """终端用户表模型"""
    __tablename__ = "end_user"
    __table_args__ = (
        PrimaryKeyConstraint("id", name="pk_end_user_id"),
    )

    id = Column(UUID, nullable=False, server_default=text("uuid_generate_v4()"))  # 终端id
    tenant_id = Column(UUID, nullable=False)  # 归属的账号/空间id
    app_id = Column(UUID, nullable=False)  # 归属应用的id，终端用户只能在应用下使用
    updated_at = Column(
        DateTime,
        nullable=False,
        server_default=text('CURRENT_TIMESTAMP(0)'),
        server_onupdate=text('CURRENT_TIMESTAMP(0)')
    )
    created_at = Column(DateTime, nullable=False, server_default=text('CURRENT_TIMESTAMP(0)'))
