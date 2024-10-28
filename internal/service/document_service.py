#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2024/10/21 23:29
@Author : rxccai@gmail.com
@File   : document_service.py
"""
import logging
import random
import time
from dataclasses import dataclass
from uuid import UUID

from injector import inject
from sqlalchemy import desc, asc, func

from internal.entity.dataset_entity import ProcessType, SegmentStatus
from internal.entity.upload_file_entity import ALL_DOCUMENT_EXTENSION
from internal.exception import ForbiddenException, FailException, NotFoundException
from internal.lib.helper import datetime_to_timestamp
from internal.model import Document, Dataset, UploadFile, ProcessRule, Segment
from internal.schema.document_schema import GetDocumentsWithPageReq
from internal.task.document_task import build_documents
from pkg.paginator import Paginator
from pkg.sqlalchemy import SQLAlchemy
from .base_service import BaseService


@inject
@dataclass
class DocumentService(BaseService):
    db: SQLAlchemy

    def create_documents(self,
                         dataset_id: UUID,
                         upload_file_ids: list[UUID],
                         process_type: str = ProcessType.AUTOMATIC,
                         rule: dict = None
                         ) -> tuple[list[Document], str]:
        # todo
        account_id = "e7300838-b215-4f97-b420-2333a699e22e"
        dataset = self.get(Dataset, dataset_id)
        if dataset is None or str(dataset.account_id) != account_id:
            raise ForbiddenException("当前用户无该知识库权限或知识库不存在")
        upload_files = self.db.session.query(UploadFile).filter(
            UploadFile.account_id == account_id,
            UploadFile.id.in_(upload_file_ids)
        ).all()
        upload_files = [upload_file for upload_file in upload_files if
                        upload_file.extension.lower() in ALL_DOCUMENT_EXTENSION]
        if len(upload_files) == 0:
            logging.warning(
                f"上传文档列表未解析到合法文件, account_id: {account_id}, dataset_id: {dataset_id}, upload_file_ids: {upload_file_ids}")
            raise FailException("暂未解析到合法文件，请重新上传")
        batch = time.strftime("%Y%m%d%H%M%S") + str(random.randint(100000, 999999))
        process_rule = self.create(
            ProcessRule,
            account_id=account_id,
            dataset_id=dataset_id,
            mode=process_type,
            rule=rule
        )
        position = self.get_last_document_position(dataset_id)
        documents = []
        for upload_file in upload_files:
            position += 1
            document = self.create(
                Document,
                account_id=account_id,
                dataset_id=dataset_id,
                upload_file_id=upload_file.id,
                process_rule_id=process_rule.id,
                batch=batch,
                name=upload_file.name,
                position=position,
            )
            documents.append(document)

        build_documents.delay([document.id for document in documents])

        return documents, batch

    def get_last_document_position(self, dataset_id: UUID) -> int:
        document = self.db.session.query(Document).filter(
            Document.dataset_id == dataset_id,
        ).order_by(desc("position")).first()
        return document.position if document else 0

    def get_documents_status(self, dataset_id: UUID, batch: str) -> list[dict]:
        # todo
        account_id = "e7300838-b215-4f97-b420-2333a699e22e"
        dataset = self.get(Dataset, dataset_id)
        if dataset is None or str(dataset.account_id) != account_id:
            raise ForbiddenException("当前用户无该知识库权限或知识库不存在")

        documents = self.db.session.query(Document).filter(
            Document.dataset_id == dataset_id,
            Document.batch == batch
        ).order_by(asc("position")).all()
        if documents is None or len(documents) == 0:
            raise NotFoundException("该处理批次为发现文档，请重试")
        documents_status = []
        for document in documents:
            segment_count = self.db.session.query(func.count(Segment.id)).filter(
                Segment.document_id == document.id,
            ).scalar()
            completed_segment_count = self.db.session.query(func.count(Segment.id)).filter(
                Segment.document_id == document.id,
                Segment.status == SegmentStatus.COMPLETED
            ).scalar()

            upload_file = document.upload_file
            documents_status.append({
                "id": document.id,
                "name": document.name,
                "size": upload_file.size,
                "extension": upload_file.extension,
                "mime_type": upload_file.mime_type,
                "position": document.position,
                "segment_count": segment_count,
                "completed_segment_count": completed_segment_count,
                "error": document.error,
                "status": document.status,
                "process_started_at": datetime_to_timestamp(document.processing_started_at),
                "parsing_completed_at": datetime_to_timestamp(document.parsing_completed_at),
                "splitting_completed_at": datetime_to_timestamp(document.splitting_completed_at),
                "indexing_completed_at": datetime_to_timestamp(document.indexing_completed_at),
                "completed_at": datetime_to_timestamp(document.completed_at),
                "stopped_at": datetime_to_timestamp(document.stopped_at),
                "created_at": datetime_to_timestamp(document.created_at),
            })
        return documents_status

    def get_document(self, dataset_id: UUID, document_id: UUID) -> Document:
        # todo
        account_id = "e7300838-b215-4f97-b420-2333a699e22e"
        document = self.get(Document, document_id)
        if document is None:
            raise NotFoundException("该文档不存在")
        if document.dataset_id != dataset_id or str(document.account_id) != account_id:
            raise ForbiddenException("当前用户无权限获取该文档")
        return document

    def update_document(self, dataset_id: UUID, document_id: UUID, **kwargs) -> Document:
        # todo
        account_id = "e7300838-b215-4f97-b420-2333a699e22e"
        document = self.get(Document, document_id)
        if document is None:
            raise NotFoundException("该文档不存在")
        if document.dataset_id != dataset_id or str(document.account_id) != account_id:
            raise ForbiddenException("当前用户无权限获取该文档")

        return self.update(document, **kwargs)

    def get_document_with_page(self, dataset_id: UUID,
                               req: GetDocumentsWithPageReq) -> tuple[list[Document], Paginator]:
        # todo
        account_id = "e7300838-b215-4f97-b420-2333a699e22e"
        dataset = self.get(Dataset, dataset_id)
        if dataset is None or str(dataset.account_id) != account_id:
            raise NotFoundException("该知识库不存在或无权限")
        paginator = Paginator(db=self.db, req=req)
        filters = [
            Document.account_id == account_id,
            Document.dataset_id == dataset_id,
        ]
        if req.search_word.data:
            filters.append(Document.name.ilike(f"%{req.search_word.data}%"))

        documents = paginator.paginate(
            self.db.session.query(Document).filter(*filters).order_by(desc("created_at"))
        )
        return documents, paginator
