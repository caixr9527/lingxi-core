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
@Time   : 2024/6/30 21:42
@Author : caixiaorong01@outlook.com
@File   : app.py
"""
from datetime import datetime

from sqlalchemy import (
    Column,
    UUID,
    String,
    Text,
    Integer,
    DateTime,
    text,
    PrimaryKeyConstraint,
    Index,
)
from sqlalchemy.dialects.postgresql import JSONB

from internal.entity.app_entity import AppConfigType, DEFAULT_APP_CONFIG, AppStatus
from internal.entity.conversation_entity import InvokeFrom
from internal.entity.platform_entity import WechatConfigStatus
from internal.extension.database_extension import db
from internal.lib.helper import generate_random_string
from .conversation import Conversation
from .platform import WechatConfig


class App(db.Model):
    """AI应用基础模型类"""
    __tablename__ = "app"
    __table_args__ = (
        PrimaryKeyConstraint("id", name="pk_app_id"),
        Index("app_account_id_idx", "account_id"),
        Index("app_token_idx", "token"),
    )

    id = Column(UUID, nullable=False, server_default=text("uuid_generate_v4()"))
    account_id = Column(UUID, nullable=False)  # 创建账号id
    app_config_id = Column(UUID, nullable=True)  # 发布配置id，当值为空时代表没有发布
    draft_app_config_id = Column(UUID, nullable=True)  # 关联的草稿配置id
    debug_conversation_id = Column(UUID, nullable=True)  # 应用调试会话id，为None则代表没有会话信息
    name = Column(String(255), nullable=False, server_default=text("''::character varying"))  # 应用名字
    en_name = Column(String(255), nullable=False, server_default=text("''::character varying"))  # 应用英文名字
    icon = Column(String(255), nullable=False, server_default=text("''::character varying"))  # 应用图标
    description = Column(Text, nullable=False, server_default=text("''::text"))  # 应用描述
    token = Column(String(255), nullable=True, server_default=text("''::character varying"))  # 应用凭证信息
    status = Column(String(255), nullable=False, server_default=text("''::character varying"))  # 应用状态
    mode = Column(Integer, nullable=False, server_default=text("0"))  # 模式 0:单agent模式 1:supervisor模式
    updated_at = Column(
        DateTime,
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP(0)"),
        onupdate=datetime.now,
    )
    created_at = Column(DateTime, nullable=False, server_default=text("CURRENT_TIMESTAMP(0)"))

    @property
    def app_config(self) -> "AppConfig":
        """只读属性，返回当前应用的运行配置"""
        if not self.app_config_id:
            return None
        return db.session.query(AppConfig).get(self.app_config_id)

    @property
    def draft_app_config(self) -> "AppConfigVersion":
        """只读属性，返回当前应用的草稿配置"""
        # 获取当前应用的草稿配置
        app_config_version = db.session.query(AppConfigVersion).filter(
            AppConfigVersion.app_id == self.id,
            AppConfigVersion.config_type == AppConfigType.DRAFT,
        ).one_or_none()

        # 检测配置是否存在，如果不存在则创建一个默认值
        if not app_config_version:
            app_config_version = AppConfigVersion(
                app_id=self.id,
                version=0,
                config_type=AppConfigType.DRAFT,
                **DEFAULT_APP_CONFIG
            )
            db.session.add(app_config_version)
            db.session.commit()

        return app_config_version

    @property
    def debug_conversation(self) -> "Conversation":
        """获取应用的调试会话记录"""
        # 根据debug_conversation_id获取调试会话记录
        debug_conversation = None
        if self.debug_conversation_id is not None:
            debug_conversation = db.session.query(Conversation).filter(
                Conversation.id == self.debug_conversation_id,
                Conversation.invoke_from == InvokeFrom.DEBUGGER,
            ).one_or_none()

        # 检测数据是否存在，如果不存在则创建
        if not self.debug_conversation_id or not debug_conversation:
            # 开启数据库自动提交上下文
            with db.auto_commit():
                # 创建应用调试会话记录并刷新获取会话id
                debug_conversation = Conversation(
                    app_id=self.id,
                    name="New Conversation",
                    invoke_from=InvokeFrom.DEBUGGER,
                    created_by=self.account_id,
                )
                db.session.add(debug_conversation)
                db.session.flush()

                # 更新当前记录的debug_conversation_id
                self.debug_conversation_id = debug_conversation.id

        return debug_conversation

    @property
    def token_with_default(self) -> str:
        if self.status != AppStatus.PUBLISHED:
            if self.token is not None or self.token != "":
                self.token = ''
                db.session.commit()
            return ""

        if self.token is None or self.token == "":
            self.token = generate_random_string(16)
            db.session.commit()
        return self.token

    @property
    def wechat_config(self) -> "WechatConfig":
        """获取应用的微信发布配置信息"""
        # 获取当前应用的微信配置信息
        config = db.session.query(WechatConfig).filter(
            WechatConfig.app_id == self.id,
        ).one_or_none()

        # 检测配置是否存在，不存在则创建
        if not config:
            config = WechatConfig(app_id=self.id, status=WechatConfigStatus.UNCONFIGURED)
            db.session.add(config)
            db.session.commit()

        # 检查wechat_config只要app_id、app_secret和token有一个没填写则更新配置状态
        if config.status == WechatConfigStatus.CONFIGURED:
            if not config.wechat_app_id or not config.wechat_app_secret or not config.wechat_token:
                config.status = WechatConfigStatus.UNCONFIGURED
                db.session.commit()

        # 检测应用发布状态与配置信息是否匹配，不匹配则更新
        if self.status == AppStatus.DRAFT:
            # 草稿配置，检查WechatConfig是否设置为已发布，是的话则更新
            if config.status == WechatConfigStatus.CONFIGURED:
                config.status = WechatConfigStatus.UNCONFIGURED
                db.session.commit()
        elif self.status == AppStatus.PUBLISHED:
            # 已发布配置，检测WechatConfig如果填写了app_id、app_secret与token，则更新配置信息
            if config.status == WechatConfigStatus.UNCONFIGURED:
                if config.wechat_app_id and config.wechat_app_secret and config.wechat_token:
                    config.status = WechatConfigStatus.CONFIGURED
                    db.session.commit()

        return config


class AppConfig(db.Model):
    """应用配置模型"""
    __tablename__ = "app_config"
    __table_args__ = (
        PrimaryKeyConstraint("id", name="pk_app_config_id"),
        Index("app_config_app_id_idx", "app_id"),
    )

    id = Column(UUID, nullable=False, server_default=text("uuid_generate_v4()"))  # 配置id
    app_id = Column(UUID, nullable=False)  # 关联应用id
    model_config = Column(JSONB, nullable=False, server_default=text("'{}'::jsonb"))  # 模型配置
    dialog_round = Column(Integer, nullable=False, server_default=text("0"))  # 鞋带上下文轮数
    preset_prompt = Column(Text, nullable=False, server_default=text("''::text"))  # 预设prompt
    tools = Column(JSONB, nullable=False, server_default=text("'[]'::jsonb"))  # 应用关联工具列表
    agents = Column(JSONB, nullable=False, server_default=text("'[]'::jsonb"))  # 应用关联的agent列表
    workflows = Column(JSONB, nullable=False, server_default=text("'[]'::jsonb"))  # 应用关联的工作流列表
    retrieval_config = Column(JSONB, nullable=False, server_default=text("'[]'::jsonb"))  # 检索配置
    long_term_memory = Column(JSONB, nullable=False, server_default=text("'{}'::jsonb"))  # 长期记忆配置
    opening_statement = Column(Text, nullable=False, server_default=text("''::text"))  # 开场白文案
    opening_questions = Column(JSONB, nullable=False, server_default=text("'[]'::jsonb"))  # 开场白建议问题列表
    speech_to_text = Column(JSONB, nullable=False, server_default=text("'{}'::jsonb"))  # 语音转文本配置
    text_to_speech = Column(JSONB, nullable=False, server_default=text("'{}'::jsonb"))  # 文本转语音配置
    multimodal = Column(JSONB, nullable=False, server_default=text("'{}'::jsonb"))  # 开启多模态
    mcp_server = Column(JSONB, nullable=False, server_default=text("'{}'::jsonb"))  # mcp配置
    suggested_after_answer = Column(
        JSONB,
        nullable=False,
        server_default=text("'{\"enable\": true}'::jsonb"),
    )  # 回答后生成建议问题
    review_config = Column(JSONB, nullable=False, server_default=text("'{}'::jsonb"))  # 审核配置
    updated_at = Column(
        DateTime,
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP(0)"),
        onupdate=datetime.now,
    )
    created_at = Column(DateTime, nullable=False, server_default=text("CURRENT_TIMESTAMP(0)"))

    @property
    def app_dataset_joins(self) -> list["AppDatasetJoin"]:
        """只读属性，获取配置的知识库关联记录"""
        return (
            db.session.query(AppDatasetJoin).filter(
                AppDatasetJoin.app_id == self.app_id
            ).all()
        )


class AppConfigVersion(db.Model):
    """应用配置版本历史表，用于存储草稿配置+历史发布配置"""
    __tablename__ = "app_config_version"
    __table_args__ = (
        PrimaryKeyConstraint("id", name="pk_app_config_version_id"),
        Index("app_config_version_app_id_idx", "app_id"),
    )

    id = Column(UUID, nullable=False, server_default=text("uuid_generate_v4()"))  # 配置id
    app_id = Column(UUID, nullable=False)  # 关联应用id
    model_config = Column(JSONB, nullable=False, server_default=text("'{}'::jsonb"))  # 模型配置
    dialog_round = Column(Integer, nullable=False, server_default=text("0"))  # 鞋带上下文轮数
    preset_prompt = Column(Text, nullable=False, server_default=text("''::text"))  # 人设与回复逻辑
    tools = Column(JSONB, nullable=False, server_default=text("'[]'::jsonb"))  # 应用关联的工具列表
    agents = Column(JSONB, nullable=False, server_default=text("'[]'::jsonb"))  # 应用关联的agent列表
    workflows = Column(JSONB, nullable=False, server_default=text("'[]'::jsonb"))  # 应用关联的工作流列表
    datasets = Column(JSONB, nullable=False, server_default=text("'[]'::jsonb"))  # 应用关联的知识库列表
    retrieval_config = Column(JSONB, nullable=False, server_default=text("'{}'::jsonb"))  # 检索配置
    long_term_memory = Column(JSONB, nullable=False, server_default=text("'{}'::jsonb"))  # 长期记忆配置
    opening_statement = Column(Text, nullable=False, server_default=text("''::text"))  # 开场白文案
    opening_questions = Column(JSONB, nullable=False, server_default=text("'[]'::jsonb"))  # 开场白建议问题列表
    speech_to_text = Column(JSONB, nullable=False, server_default=text("'{}'::jsonb"))  # 语音转文本配置
    multimodal = Column(JSONB, nullable=False, server_default=text("'{}'::jsonb"))  # 开启多模态
    text_to_speech = Column(JSONB, nullable=False, server_default=text("'{}'::jsonb"))  # 文本转语音配置
    mcp_server = Column(JSONB, nullable=False, server_default=text("'{}'::jsonb"))  # mcp配置
    suggested_after_answer = Column(
        JSONB,
        nullable=False,
        server_default=text("'{\"enable\": true}'::jsonb"),
    )  # 回答后生成建议问题
    review_config = Column(JSONB, nullable=False, server_default=text("'{}'::jsonb"))  # 审核配置
    version = Column(Integer, nullable=False, server_default=text("0"))  # 发布版本号
    config_type = Column(String(255), nullable=False, server_default=text("''::character varying"))  # 配置类型
    updated_at = Column(
        DateTime,
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP(0)"),
        onupdate=datetime.now,
    )
    created_at = Column(DateTime, nullable=False, server_default=text("CURRENT_TIMESTAMP(0)"))


class AppDatasetJoin(db.Model):
    """应用知识库关联表模型"""
    __tablename__ = "app_dataset_join"
    __table_args__ = (
        PrimaryKeyConstraint("id", name="pk_app_dataset_join_id"),
        Index("app_dataset_join_app_id_dataset_id_idx", "app_id", "dataset_id"),
    )

    id = Column(UUID, nullable=False, server_default=text("uuid_generate_v4()"))
    app_id = Column(UUID, nullable=False)
    dataset_id = Column(UUID, nullable=False)
    updated_at = Column(
        DateTime,
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP(0)"),
        onupdate=datetime.now,
    )
    created_at = Column(DateTime, nullable=False, server_default=text("CURRENT_TIMESTAMP(0)"))
