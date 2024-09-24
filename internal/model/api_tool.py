#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2024/9/24 23:20
@Author  : rxccai@gmail.com
@File    : api_tool.py
"""
from sqlalchemy import (
    Column, UUID, String, Text, DateTime, PrimaryKeyConstraint, text
)
from sqlalchemy.dialects.postgresql import JSONB

from internal.extension.database_extension import db


class ApiToolProvider(db.Model):
    """API工具提供者模型"""
    __tablename__ = "api_tool_provider"
    __table_args__ = (
        PrimaryKeyConstraint("id", name="pk_api_tool_provider_id"),
    )

    id = Column(UUID, nullable=False, server_default=text('uuid_generate_v4()'))
    account_id = Column(UUID, nullable=False)
    name = Column(String(255), nullable=False, server_default=text("''::character varying"))
    icon = Column(String(255), nullable=False, server_default=text("''::character varying"))
    description = Column(Text, nullable=False, server_default=text("''::text"))
    openapi_schema = Column(Text, nullable=False, server_default=text("''::text"))
    headers = Column(JSONB, nullable=False, server_default=text("'[]'::jsonb"))
    updated_at = Column(
        DateTime,
        nullable=False,
        server_default=text('CURRENT_TIMESTAMP(0)'),
        server_onupdate=text('CURRENT_TIMESTAMP(0)')
    )
    created_at = Column(DateTime, nullable=False, server_default=text('CURRENT_TIMESTAMP(0)'))

    @property
    def tools(self) -> list["ApiTool"]:
        return db.session.query(ApiTool).filter_by(provider_id=self.id).all()


class ApiTool(db.Model):
    """API工具表"""
    __tablename__ = "api_tool"
    __table_args__ = (
        PrimaryKeyConstraint("id", name="pk_api_tool_id"),
    )

    id = Column(UUID, nullable=False, server_default=text('uuid_generate_v4()'))
    account_id = Column(UUID, nullable=False)
    provider_id = Column(UUID, nullable=False)
    name = Column(String(255), nullable=False, server_default=text("''::character varying"))
    description = Column(Text, nullable=False, server_default=text("''::text"))
    url = Column(String(255), nullable=False, server_default=text("''::character varying"))
    method = Column(String(255), nullable=False, server_default=text("''::character varying"))
    parameters = Column(JSONB, nullable=False, server_default=text("'[]'::jsonb"))
    updated_at = Column(
        DateTime,
        nullable=False,
        server_default=text('CURRENT_TIMESTAMP(0)'),
        server_onupdate=text('CURRENT_TIMESTAMP(0)')
    )
    created_at = Column(DateTime, nullable=False, server_default=text('CURRENT_TIMESTAMP(0)'))

    @property
    def provider(self) -> "ApiToolProvider":
        """只读属性，返回当前工具关联/归属的工具提供者信息"""
        return db.session.query(ApiToolProvider).get(self.provider_id)
