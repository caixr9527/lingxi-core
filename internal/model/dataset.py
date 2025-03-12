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
@Time   : 2024/10/16 23:14
@Author : rxccai@gmail.com
@File   : dataset.py
"""
from datetime import datetime

from sqlalchemy import (
    Column,
    UUID,
    String,
    Text,
    Integer,
    Boolean,
    DateTime,
    text,
    func,
    PrimaryKeyConstraint,
    Index,
)
from sqlalchemy.dialects.postgresql import JSONB

from internal.extension.database_extension import db
from .app import AppDatasetJoin
from .upload_file import UploadFile


class Dataset(db.Model):
    """知识库表"""
    __tablename__ = "dataset"
    __table_args__ = (
        PrimaryKeyConstraint("id", name="pk_dataset_id"),
        Index("dataset_account_id_name_idx", "account_id", "name"),
    )

    id = Column(UUID, nullable=False, server_default=text("uuid_generate_v4()"))
    account_id = Column(UUID, nullable=False)
    name = Column(String(255), nullable=False, server_default=text("''::character varying"))
    icon = Column(String(255), nullable=False, server_default=text("''::character varying"))
    description = Column(Text, nullable=False, server_default=text("''::text"))
    updated_at = Column(
        DateTime,
        nullable=False,
        server_default=text('CURRENT_TIMESTAMP(0)'),
        onupdate=datetime.now,
    )
    created_at = Column(DateTime, nullable=False, server_default=text('CURRENT_TIMESTAMP(0)'))

    @property
    def document_count(self) -> int:
        """只读属性，获取知识库下的文档数"""
        return (
            db.session.
            query(func.count(Document.id)).
            filter(Document.dataset_id == self.id).
            scalar()
        )

    @property
    def hit_count(self) -> int:
        """只读属性，获取该知识库的命中次数"""
        return (
            db.session.
            query(func.coalesce(func.sum(Segment.hit_count), 0)).
            filter(Segment.dataset_id == self.id).
            scalar()
        )

    @property
    def related_app_count(self) -> int:
        """只读属性，获取该知识库关联的应用数"""
        return (
            db.session.
            query(func.count(AppDatasetJoin.id)).
            filter(AppDatasetJoin.dataset_id == self.id).
            scalar()
        )

    @property
    def character_count(self) -> int:
        """只读属性，获取该知识库下的字符总数"""
        return (
            db.session.
            query(func.coalesce(func.sum(Document.character_count), 0)).
            filter(Document.dataset_id == self.id).
            scalar()
        )


class Document(db.Model):
    """文档表模型"""
    __tablename__ = "document"
    __table_args__ = (
        PrimaryKeyConstraint("id", name="pk_document_id"),
        Index("document_account_id_idx", "account_id"),
        Index("document_dataset_id_idx", "dataset_id"),
        Index("document_batch_idx", "batch"),
    )

    id = Column(UUID, nullable=False, server_default=text("uuid_generate_v4()"))
    account_id = Column(UUID, nullable=False)
    dataset_id = Column(UUID, nullable=False)
    upload_file_id = Column(UUID, nullable=False)
    process_rule_id = Column(UUID, nullable=False)
    batch = Column(String(255), nullable=False, server_default=text("''::character varying"))
    name = Column(String(255), nullable=False, server_default=text("''::character varying"))
    position = Column(Integer, nullable=False, server_default=text("1"))
    character_count = Column(Integer, nullable=False, server_default=text("0"))
    token_count = Column(Integer, nullable=False, server_default=text("0"))
    processing_started_at = Column(DateTime, nullable=True)
    parsing_completed_at = Column(DateTime, nullable=True)
    splitting_completed_at = Column(DateTime, nullable=True)
    indexing_completed_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    stopped_at = Column(DateTime, nullable=True)
    error = Column(Text, nullable=False, server_default=text("''::text"))
    enabled = Column(Boolean, nullable=False, server_default=text("false"))
    disabled_at = Column(DateTime, nullable=True)
    status = Column(String(255), nullable=False, server_default=text("'waiting'::character varying"))
    updated_at = Column(
        DateTime,
        nullable=False,
        server_default=text('CURRENT_TIMESTAMP(0)'),
        onupdate=datetime.now,
    )
    created_at = Column(DateTime, nullable=False, server_default=text('CURRENT_TIMESTAMP(0)'))

    @property
    def upload_file(self) -> "UploadFile":
        return db.session.query(UploadFile).filter(
            UploadFile.id == self.upload_file_id,
        ).one_or_none()

    @property
    def process_rule(self) -> "ProcessRule":
        return db.session.query(ProcessRule).filter(
            ProcessRule.id == self.process_rule_id,
        ).one_or_none()

    @property
    def segment_count(self) -> int:
        return db.session.query(func.count(Segment.id)).filter(
            Segment.document_id == self.id,
        ).scalar()

    @property
    def hit_count(self) -> int:
        return db.session.query(func.coalesce(func.sum(Segment.hit_count), 0)).filter(
            Segment.document_id == self.id,
        ).scalar()


class Segment(db.Model):
    """片段表模型"""
    __tablename__ = "segment"
    __table_args__ = (
        PrimaryKeyConstraint("id", name="pk_segment_id"),
        Index("segment_account_id_idx", "account_id"),
        Index("segment_dataset_id_idx", "dataset_id"),
        Index("segment_document_id_idx", "document_id"),
    )

    id = Column(UUID, nullable=False, server_default=text("uuid_generate_v4()"))
    account_id = Column(UUID, nullable=False)
    dataset_id = Column(UUID, nullable=False)
    document_id = Column(UUID, nullable=False)
    node_id = Column(UUID, nullable=False)
    position = Column(Integer, nullable=False, server_default=text("1"))
    content = Column(Text, nullable=False, server_default=text("''::text"))
    character_count = Column(Integer, nullable=False, server_default=text("0"))
    token_count = Column(Integer, nullable=False, server_default=text("0"))
    keywords = Column(JSONB, nullable=False, server_default=text("'[]'::jsonb"))
    hash = Column(String(255), nullable=False, server_default=text("''::character varying"))
    hit_count = Column(Integer, nullable=False, server_default=text("0"))
    enabled = Column(Boolean, nullable=False, server_default=text("false"))
    disabled_at = Column(DateTime, nullable=True)
    processing_started_at = Column(DateTime, nullable=True)
    indexing_completed_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    stopped_at = Column(DateTime, nullable=True)
    error = Column(Text, nullable=False, server_default=text("''::text"))
    status = Column(String(255), nullable=False, server_default=text("'waiting'::character varying"))
    updated_at = Column(
        DateTime,
        nullable=False,
        server_default=text('CURRENT_TIMESTAMP(0)'),
        onupdate=datetime.now,
    )
    created_at = Column(DateTime, nullable=False, server_default=text('CURRENT_TIMESTAMP(0)'))

    @property
    def document(self) -> "Document":
        return db.session.query(Document).get(self.document_id)


class KeywordTable(db.Model):
    """关键词表模型"""
    __tablename__ = "keyword_table"
    __table_args__ = (
        PrimaryKeyConstraint("id", name="pk_keyword_table_id"),
        Index("keyword_table_dataset_id_idx", "dataset_id"),
    )

    id = Column(UUID, nullable=False, server_default=text("uuid_generate_v4()"))
    dataset_id = Column(UUID, nullable=False)
    keyword_table = Column(JSONB, nullable=False, server_default=text("'{}'::jsonb"))
    updated_at = Column(
        DateTime,
        nullable=False,
        server_default=text('CURRENT_TIMESTAMP(0)'),
        onupdate=datetime.now,
    )
    created_at = Column(DateTime, nullable=False, server_default=text('CURRENT_TIMESTAMP(0)'))


class DatasetQuery(db.Model):
    """知识库查询表模型"""
    __tablename__ = "dataset_query"
    __table_args__ = (
        PrimaryKeyConstraint("id", name="pk_dataset_query_id"),
        Index("dataset_query_dataset_id_idx", "dataset_id"),
        Index("dataset_created_by_idx", "created_by"),
        Index("dataset_source_app_id_idx", "source_app_id"),
    )

    id = Column(UUID, nullable=False, server_default=text("uuid_generate_v4()"))
    dataset_id = Column(UUID, nullable=False)
    query = Column(Text, nullable=False, server_default=text("''::text"))
    source = Column(String(255), nullable=False, server_default=text("'HitTesting'::character varying"))
    source_app_id = Column(UUID, nullable=True)
    created_by = Column(UUID, nullable=True)
    updated_at = Column(
        DateTime,
        nullable=False,
        server_default=text('CURRENT_TIMESTAMP(0)'),
        onupdate=datetime.now,
    )
    created_at = Column(DateTime, nullable=False, server_default=text('CURRENT_TIMESTAMP(0)'))


class ProcessRule(db.Model):
    """文档处理规则表模型"""
    __tablename__ = "process_rule"
    __table_args__ = (
        PrimaryKeyConstraint("id", name="pk_process_rule_id"),
        Index("process_rule_account_id_idx", "account_id"),
        Index("process_rule_dataset_id_idx", "dataset_id"),
    )

    id = Column(UUID, nullable=False, server_default=text("uuid_generate_v4()"))
    account_id = Column(UUID, nullable=False)
    dataset_id = Column(UUID, nullable=False)
    mode = Column(String(255), nullable=False, server_default=text("'automic'::character varying"))
    rule = Column(JSONB, nullable=False, server_default=text("'{}'::jsonb"))
    updated_at = Column(
        DateTime,
        nullable=False,
        server_default=text('CURRENT_TIMESTAMP(0)'),
        onupdate=datetime.now,
    )
    created_at = Column(DateTime, nullable=False, server_default=text('CURRENT_TIMESTAMP(0)'))
