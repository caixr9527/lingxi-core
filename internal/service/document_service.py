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
from sqlalchemy import desc

from internal.entity.dataset_entity import ProcessType
from internal.entity.upload_file_entity import ALL_DOCUMENT_EXTENSION
from internal.exception import ForbiddenException, FailException
from internal.model import Document, Dataset, UploadFile, ProcessRule
from internal.task.document_task import build_documents
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
