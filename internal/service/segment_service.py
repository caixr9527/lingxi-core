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
@Time   : 2024/11/3 17:37
@Author : caixiaorong01@outlook.com
@File   : segment_service.py
"""
import logging
import uuid
from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from injector import inject
from langchain_core.documents import Document as LCDocument
from redis import Redis
from sqlalchemy import asc, func

from internal.entity.cache_entity import LOCK_SEGMENT_UPDATE_ENABLED, LOCK_EXPIRE_TIME
from internal.entity.dataset_entity import SegmentStatus, DocumentStatus
from internal.exception import NotFoundException, FailException, ValidateException
from internal.lib.helper import generate_text_hash
from internal.model import Segment, Document, Account
from internal.schema.segment_schema import (
    GetSegmentsWithPageReq,
    CreateSegmentReq,
    UpdateSegmentReq
)
from pkg.paginator import Paginator
from pkg.sqlalchemy import SQLAlchemy
from .base_service import BaseService
from .embeddings_service import EmbeddingsService
from .jieba_service import JiebaService
from .keyword_table_service import KeywordTableService
from .vector_database_service import VectorDatabaseService


@inject
@dataclass
class SegmentService(BaseService):
    db: SQLAlchemy
    redis_client: Redis
    keyword_table_service: KeywordTableService
    vector_database_service: VectorDatabaseService
    embeddings_service: EmbeddingsService
    jieba_service: JiebaService

    def create_segment(self, dataset_id: UUID, document_id: UUID, req: CreateSegmentReq, account: Account) -> Segment:
        token_count = self.embeddings_service.calculate_token_count(req.content.data)
        if token_count > 1000:
            raise ValidateException("片段内容长度不超过1000 token")
        document = self.get(Document, document_id)
        if (
                document is None
                or document.account_id != account.id
                or document.dataset_id != dataset_id
        ):
            raise NotFoundException("该知识库文档不存在，或无权新增，请核实后重试")
        if document.status != DocumentStatus.COMPLETED:
            raise FailException("当前文档不可新增片段，请稍后重试")
        position = self.db.session.query(func.coalesce(func.max(Segment.position), 0)).filter(
            Segment.document_id == document_id,
        ).scalar()
        if req.keywords.data is None or len(req.keywords.data) == 0:
            req.keywords.data = self.jieba_service.extract_keywords(req.content.data, 10)

        segment = None
        try:
            position += 1
            segment = self.create(
                Segment,
                account_id=account.id,
                dataset_id=dataset_id,
                document_id=document_id,
                node_id=uuid.uuid4(),
                position=position,
                content=req.content.data,
                character_count=len(req.content.data),
                token_count=token_count,
                keywords=req.keywords.data,
                hash=generate_text_hash(req.content.data),
                enabled=True,
                processing_started_at=datetime.now(),
                indexing_completed_at=datetime.now(),
                completed_at=datetime.now(),
                status=SegmentStatus.COMPLETED,
            )
            self.vector_database_service.vector_store.add_documents([
                LCDocument(
                    page_content=req.content.data,
                    metadata={
                        "account_id": str(document.account_id),
                        "dataset_id": str(document.dataset_id),
                        "document_id": str(document.id),
                        "segment_id": str(segment.id),
                        "node_id": str(segment.node_id),
                        "document_enabled": document.enabled,
                        "segment_enabled": True,
                    }
                )], ids=[str(segment.node_id)])
            document_character_count, document_token_count = self.db.session.query(
                func.coalesce(func.sum(Segment.character_count), 0),
                func.coalesce(func.sum(Segment.token_count), 0)
            ).filter(Segment.document_id == document.id).first()

            self.update(
                document,
                character_count=document_character_count,
                token_count=document_token_count
            )
            if document.enabled is True:
                self.keyword_table_service.add_keyword_table_from_ids(dataset_id, [segment.id])
        except Exception as e:
            logging.exception("新增文档片段内容发生异常，错误信息: %(error)s", {"error": e})
            if segment:
                self.update(
                    Segment,
                    error=str(e),
                    status=SegmentStatus.ERROR,
                    enabled=False,
                    disabled_at=datetime.now(),
                    stopped_at=datetime.now(),
                )
            raise FailException("新增文档片段失败，请稍后重试")

    def update_segment(
            self, dataset_id: UUID,
            document_id: UUID,
            segment_id: UUID,
            req: UpdateSegmentReq,
            account: Account
    ) -> Segment:
        """根据传递的信息更新指定的文档片段信息"""

        # 1.获取片段信息并校验权限
        segment = self.get(Segment, segment_id)
        if (
                segment is None
                or segment.account_id != account.id
                or segment.dataset_id != dataset_id
                or segment.document_id != document_id
        ):
            raise NotFoundException("该文档片段不存在，或无权限修改，请核实后重试")

        # 2.判断文档片段是否处于可修改的环境
        if segment.status != SegmentStatus.COMPLETED:
            raise FailException("当前片段不可修改状态，请稍后尝试")

        # 3.检测是否传递了keywords，如果没有传递的话，调用jieba服务生成关键词
        if req.keywords.data is None or len(req.keywords.data) == 0:
            req.keywords.data = self.jieba_service.extract_keywords(req.content.data, 10)

        # 4.计算新内容hash值，用于判断是否需要更新向量数据库以及文档详情
        new_hash = generate_text_hash(req.content.data)
        required_update = segment.hash != new_hash

        try:
            # 5.更新segment表记录
            self.update(
                segment,
                keywords=req.keywords.data,
                content=req.content.data,
                hash=new_hash,
                character_count=len(req.content.data),
                token_count=self.embeddings_service.calculate_token_count(req.content.data),
            )

            # 7.更新片段归属关键词信息
            self.keyword_table_service.delete_keyword_table_from_ids(dataset_id, [segment_id])
            self.keyword_table_service.add_keyword_table_from_ids(dataset_id, [segment_id])

            # 8.检测是否需要更新文档信息以及向量数据库
            if required_update:
                # 7.更新文档信息，涵盖字符总数、token总次数
                document = segment.document
                document_character_count, document_token_count = self.db.session.query(
                    func.coalesce(func.sum(Segment.character_count), 0),
                    func.coalesce(func.sum(Segment.token_count), 0)
                ).filter(Segment.document_id == document.id).first()
                self.update(
                    document,
                    character_count=document_character_count,
                    token_count=document_token_count,
                )

                # 9.更新向量数据库对应记录
                self.vector_database_service.collection.data.update(
                    uuid=str(segment.node_id),
                    properties={
                        "text": req.content.data,
                    },
                    vector=self.embeddings_service.embeddings.embed_query(req.content.data)
                )
        except Exception as e:
            logging.exception(
                "更新文档片段记录失败, segment_id: %(segment_id)s, 错误信息: %(error)s",
                {"segment_id": segment_id, "error": e},
            )
            raise FailException("更新文档片段记录失败，请稍后尝试")

        return segment

    def update_segment_enabled(self,
                               dataset_id: UUID,
                               document_id: UUID,
                               segment_id: UUID,
                               enabled: bool,
                               account: Account) -> Segment:
        # 获取文档并校验权限
        segment = self.get(Segment, segment_id)
        if (segment is None
                or segment.dataset_id != dataset_id
                or segment.account_id != account.id
                or segment.document_id != document_id
        ):
            raise NotFoundException("该知识库文档片段不存在，或无权限查看，请核实后重试")

        if segment.status != SegmentStatus.COMPLETED:
            raise FailException("当前片段不可修改，请稍后尝试")
        if enabled == segment.enabled:
            raise FailException(f"片段修改错误，当前已是{'启用' if enabled else '禁用'}")

        cache_key = LOCK_SEGMENT_UPDATE_ENABLED.format(segment_id=segment_id)
        result = self.redis_client.get(cache_key)
        if result is not None:
            raise FailException("当前文档状态正在修改状态，请稍后重试")
        with self.redis_client.lock(cache_key, LOCK_EXPIRE_TIME):
            try:
                self.update(
                    segment,
                    enabled=enabled,
                    disabled_at=None if enabled else datetime.now(),
                )

                document = segment.document

                if enabled is True and document.enabled is True:
                    self.keyword_table_service.add_keyword_table_from_ids(dataset_id, [segment_id])
                else:
                    self.keyword_table_service.delete_keyword_table_from_ids(dataset_id, [segment_id])
                # 同步处理向量数据库数据
                self.vector_database_service.collection.data.update(
                    uuid=segment.node_id,
                    properties={"segment_enabled": enabled}
                )
                return segment
            except Exception as e:
                logging.exception(
                    "更改文档片段启用状态出现异常, segment_id: %(segment_id)s, 错误信息: %(error)s",
                    {"segment_id": segment_id, "error": e},
                )
                self.update(
                    segment,
                    error=str(e),
                    status=SegmentStatus.ERROR,
                    enabled=False,
                    disabled_at=datetime.now(),
                    stopped_at=datetime.now(),
                )
                raise FailException("更新文档片段启用状态失败，请稍后重试")

    def get_segment(self, dataset_id: UUID, document_id: UUID, segment_id: UUID, account: Account) -> Segment:
        # 获取文档并校验权限
        segment = self.get(Segment, segment_id)
        if (segment is None
                or segment.dataset_id != dataset_id
                or segment.account_id != account.id
                or segment.document_id != document_id
        ):
            raise NotFoundException("该知识库文档片段不存在，或无权限查看，请核实后重试")
        return segment

    def get_segment_with_page(
            self,
            dataset_id: UUID,
            document_id: UUID,
            req: GetSegmentsWithPageReq,
            account: Account
    ) -> tuple[list[Segment], Paginator]:

        # 获取文档并校验权限
        document = self.get(Document, document_id)
        if document is None or document.dataset_id != dataset_id or document.account_id != account.id:
            raise NotFoundException("该知识库文档不存在，或无权限查看，请核实后重试")

        # 构建分页查询器
        paginator = Paginator(db=self.db, req=req)

        # 构建筛选器
        filters = [Segment.document_id == document_id]
        if req.search_word.data:
            filters.append(Segment.content.ilike(f"%{req.search_word.data}%"))

        # 执行分页并获取数据
        segments = paginator.paginate(
            self.db.session.query(Segment).filter(*filters).order_by(asc("position"))
        )

        return segments, paginator

    def delete_segment(self, dataset_id: UUID, document_id: UUID, segment_id: UUID, account: Account) -> Segment:
        """根据传递的信息删除指定的文档片段信息，该服务是同步方法"""
        # 获取片段信息并校验权限
        segment = self.get(Segment, segment_id)
        if (
                segment is None
                or segment.account_id != account.id
                or segment.dataset_id != dataset_id
                or segment.document_id != document_id
        ):
            raise NotFoundException("该文档片段不存在，或无权限修改，请核实后重试")

        # 2.判断文档是否处于可以删除的状态，只有COMPLETED/ERROR才可以删除
        if segment.status not in [SegmentStatus.COMPLETED, SegmentStatus.ERROR]:
            raise FailException("当前文档片段处于不可删除状态，请稍后尝试")

        # 3.删除文档片段并获取该片段的文档信息
        document = segment.document
        self.delete(segment)

        # 4.同步删除关键词表中属于该片段的关键词
        self.keyword_table_service.delete_keyword_table_from_ids(dataset_id, [segment_id])

        # 5.同步删除向量数据库存储的记录
        try:
            self.vector_database_service.collection.data.delete_by_id(str(segment.node_id))
        except Exception as e:
            logging.exception(
                "删除文档片段记录失败, segment_id: %(segment_id)s, 错误信息: %(error)s",
                {"segment_id": segment_id, "error": e},
            )

        # 6.更新文档信息，涵盖字符总数、token总次数
        document_character_count, document_token_count = self.db.session.query(
            func.coalesce(func.sum(Segment.character_count), 0),
            func.coalesce(func.sum(Segment.token_count), 0)
        ).filter(Segment.document_id == document.id).first()
        self.update(
            document,
            character_count=document_character_count,
            token_count=document_token_count,
        )

        return segment
