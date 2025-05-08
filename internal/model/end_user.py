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
@Time    : 2024/12/28 16:13
@Author  : caixiaorong01@outlook.com
@File    : end_user.py
"""
from datetime import datetime

from sqlalchemy import (
    Column,
    UUID,
    DateTime,
    text,
    PrimaryKeyConstraint,
    Index,
)

from internal.extension.database_extension import db


class EndUser(db.Model):
    """终端用户表模型"""
    __tablename__ = "end_user"
    __table_args__ = (
        PrimaryKeyConstraint("id", name="pk_end_user_id"),
        Index("end_user_tenant_id_idx", "tenant_id"),
        Index("end_user_app_id_idx", "app_id"),
    )

    id = Column(UUID, nullable=False, server_default=text("uuid_generate_v4()"))  # 终端id
    tenant_id = Column(UUID, nullable=False)  # 归属的账号/空间id
    app_id = Column(UUID, nullable=False)  # 归属应用的id，终端用户只能在应用下使用
    updated_at = Column(
        DateTime,
        nullable=False,
        server_default=text('CURRENT_TIMESTAMP(0)'),
        onupdate=datetime.now,
    )
    created_at = Column(DateTime, nullable=False, server_default=text('CURRENT_TIMESTAMP(0)'))
