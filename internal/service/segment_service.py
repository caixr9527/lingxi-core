#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2024/11/3 17:37
@Author : rxccai@gmail.com
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
from internal.model import Segment, Document
from internal.schema.segment_schema import (
    GetSegmentsWithPageReq,
    CreateSegmentReq
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

    def create_segment(self, dataset_id: UUID, document_id: UUID, req: CreateSegmentReq) -> Segment:
        # todo
        # 权限判断
        account_id = "e7300838-b215-4f97-b420-2333a699e22e"
        token_count = self.embeddings_service.calculate_token_count(req.content.data)
        if token_count > 1000:
            raise ValidateException("片段内容长度不超过1000 token")
        document = self.get(Document, document_id)
        if (
                document is None
                or str(document.account_id) != account_id
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
                account_id=account_id,
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
            ).first()

            self.update(
                document,
                character_count=document_character_count,
                token_count=document_token_count
            )
            if document.enabled is True:
                self.keyword_table_service.add_keyword_table_from_ids(dataset_id, [segment.id])
        except Exception as e:
            logging.exception(f"新增文档片段内容发生异常，错误信息: {str(e)}")
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

    def update_segment_enabled(self, dataset_id: UUID, document_id: UUID, segment_id: UUID, enabled: bool) -> Segment:
        # todo
        # 权限判断
        account_id = "e7300838-b215-4f97-b420-2333a699e22e"
        # 获取文档并校验权限
        segment = self.get(Segment, segment_id)
        if (segment is None
                or segment.dataset_id != dataset_id
                or str(segment.account_id) != account_id
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
            except Exception as e:
                logging.exception(f"更改文档片段状态异常, segment_id: {segment_id}, 错误信息: {str(e)}")
                self.update(
                    segment,
                    error=str(e),
                    status=SegmentStatus.ERROR,
                    enabled=False,
                    disabled_at=datetime.now(),
                    stopped_at=datetime.now(),
                )
                raise FailException("更新文档片段启用状态失败，请稍后重试")

    def get_segment(self, dataset_id: UUID, document_id: UUID, segment_id: UUID) -> Segment:
        # todo
        # 权限判断
        account_id = "e7300838-b215-4f97-b420-2333a699e22e"
        # 获取文档并校验权限
        segment = self.get(Segment, segment_id)
        if (segment is None
                or segment.dataset_id != dataset_id
                or str(segment.account_id) != account_id
                or segment.document_id != document_id
        ):
            raise NotFoundException("该知识库文档片段不存在，或无权限查看，请核实后重试")
        return segment

    def get_segment_with_page(
            self,
            dataset_id: UUID,
            document_id: UUID,
            req: GetSegmentsWithPageReq
    ) -> tuple[list[Segment], Paginator]:
        # todo
        # 权限判断
        account_id = "e7300838-b215-4f97-b420-2333a699e22e"
        # 获取文档并校验权限
        document = self.get(Document, document_id)
        if document is None or document.dataset_id != dataset_id or str(document.account_id) != account_id:
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
