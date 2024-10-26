#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2024/10/24 22:21
@Author : rxccai@gmail.com
@File   : indexing_service.py
"""
import logging
import re
import uuid
from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from injector import inject
from langchain_core.documents import Document as LCDocument
from sqlalchemy import func

from internal.core.file_extractor import FileExtractor
from internal.entity.dataset_entity import DocumentStatus, SegmentStatus
from internal.lib.helper import generate_text_hash
from internal.model import Document, Segment
from pkg.sqlalchemy import SQLAlchemy
from .base_service import BaseService
from .embeddings_service import EmbeddingsService
from .jieba_service import JiebaService
from .keyword_table_service import KeywordTableService
from .process_rule_service import ProcessRuleService
from .vector_database_service import VectorDatabaseService


@inject
@dataclass
class IndexingService(BaseService):
    db: SQLAlchemy
    file_extractor: FileExtractor
    process_rule_service: ProcessRuleService
    embeddings_service: EmbeddingsService
    jieba_service: JiebaService
    keyword_table_service: KeywordTableService
    vector_database_service: VectorDatabaseService

    def build_documents(self, document_ids: list[UUID]) -> None:
        # 根据传递的文档id获取所有文档
        documents = self.db.session.query(Document).filter(
            Document.id.in_(document_ids)
        ).all()
        for document in documents:
            try:
                # 更新状态和时间
                self.update(
                    document,
                    status=DocumentStatus.PARSING,
                    processing_started_at=datetime.now()
                )
                # 执行文档加载，更新文档状态和时间
                lc_documents = self._parsing(document)
                # 执行文档分割
                lc_segments = self._splitting(document, lc_documents)
                # 执行文档索引构建
                self._indexing(document, lc_segments)
                # 存储操作
                self._completed(document, lc_segments)
            except Exception as e:
                logging.exception(f"构建文档 {document.id}, 发生错误信息: {str(e)}")
                self.update(
                    document,
                    status=DocumentStatus.ERROR,
                    error=str(e),
                    stopped_at=datetime.now(),
                )

    def _completed(self, document: Document, lc_segments: list[LCDocument]) -> None:
        for lc_segment in lc_segments:
            lc_segment.metadata["document_enabled"] = True
            lc_segment.metadata["segment_enabled"] = True

        for i in range(0, len(lc_segments), 10):
            chunks = lc_segments[i:i + 10]
            ids = [chunk.metadata["node_id"] for chunk in chunks]
            self.vector_database_service.vector_store.add_documents(
                chunks,
                ids=ids
            )
            self.db.session.query(Segment).filter(
                Segment.node_id.in_(ids)
            ).update({
                "status": SegmentStatus.COMPLETED,
                "completed_at": datetime.now(),
                "enabled": True,
            })
        self.update(
            document,
            status=DocumentStatus.COMPLETED,
            completed_at=datetime.now(),
            enabled=True,
        )

    def _indexing(self, document: Document, lc_segments: list[LCDocument]) -> None:
        for lc_segment in lc_segments:
            keywords = self.jieba_service.extract_keywords(lc_segment.page_content, 10)
            self.db.session.query(Segment).filter(
                Segment.id == lc_segment.metadata["segment_id"]
            ).update(
                {
                    "keywords": keywords,
                    "status": SegmentStatus.INDEXING,
                    "indexing_completed_at": datetime.now()
                }
            )
            keyword_table_record = self.keyword_table_service.get_keyword_table_from_dataset_id(document.dataset_id)
            keyword_table = {
                field: set(value) for field, value in keyword_table_record.keyword_table.items()
            }
            for keyword in keywords:
                if keyword not in keyword_table:
                    keyword_table[keyword] = set()
                keyword_table[keyword].add(lc_segment.metadata["segment_id"])

            self.update(
                keyword_table_record,
                keyword_table={field: list(value) for field, value in keyword_table.items()}
            )

        self.update(
            document,
            indexing_completed_at=datetime.now(),
        )

    def _parsing(self, document: Document) -> list[LCDocument]:
        # 获取upload_file 并加载Langchain文档
        upload_file = document.upload_file
        lc_documents = self.file_extractor.load(upload_file, False, True)
        for lc_document in lc_documents:
            lc_document.page_content = self._clean_extra_text(lc_document.page_content)

        self.update(
            document,
            character_count=sum([len(lc_document.page_content) for lc_document in lc_documents]),
            status=DocumentStatus.SPLITTING,
            parsing_completed_at=datetime.now()
        )
        return lc_documents

    def _splitting(self, document: Document, lc_documents: list[LCDocument]) -> list[LCDocument]:
        # 根据process_rule获取文本分割器
        process_rule = document.process_rule
        text_splitter = self.process_rule_service.get_text_splitter_by_process_rule(
            process_rule,
            self.embeddings_service.calculate_token_count,
        )
        # 根据process_rule规则消除多余的字符串
        for lc_document in lc_documents:
            lc_document.page_content = self.process_rule_service.clean_text_by_process_rule(
                lc_document.page_content,
                process_rule
            )
        # 分割文档列表为片段
        lc_segments = text_splitter.split_documents(lc_documents)
        position = self.db.session.query(func.coalesce(func.max(Segment.position), 0)).filter(
            Segment.document_id == document.id,
        ).scalar()

        segments = []
        for lc_segment in lc_segments:
            position += 1
            content = lc_segment.page_content
            segment = self.create(
                Segment,
                account_id=document.account_id,
                dataset_id=document.dataset_id,
                document_id=document.id,
                node_id=uuid.uuid4(),
                position=position,
                content=content,
                character_count=len(content),
                token_count=self.embeddings_service.calculate_token_count(content),
                hash=generate_text_hash(content),
                status=SegmentStatus.WAITING,
            )
            lc_segment.metadata = {
                "account_id": str(document.account_id),
                "dataset_id": str(document.dataset_id),
                "document_id": str(document.id),
                "segment_id": str(segment.id),
                "node_id": str(segment.node_id),
                "document_enabled": False,
                "segment_enabled": False,
            }
            segments.append(segment)
        self.update(
            document,
            token_count=sum([segment.token_count for segment in segments]),
            status=DocumentStatus.INDEXING,
            splitting_completed_at=datetime.now(),
        )
        return lc_segments

    @classmethod
    def _clean_extra_text(cls, text: str) -> str:
        """清除过滤传递的多余空白字符串"""
        text = re.sub(r'<\|', '<', text)
        text = re.sub(r'\|>', '>', text)
        text = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F\xEF\xBF\xBE]', '', text)
        text = re.sub('\uFFFE', '', text)  # 删除零宽非标记字符
        return text
