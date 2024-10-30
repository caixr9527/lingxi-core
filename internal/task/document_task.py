#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2024/10/24 22:15
@Author : rxccai@gmail.com
@File   : document_task.py
"""
from uuid import UUID

from celery import shared_task


@shared_task
def build_documents(document_ids: list[UUID]) -> None:
    """根据传递的文档id列表，构建文档"""
    from app.http.module import injector
    from internal.service.indexing_service import IndexingService

    indexing_service = injector.get(IndexingService)
    indexing_service.build_documents(document_ids)


@shared_task
def update_document_enabled(document_id: UUID) -> None:
    from app.http.module import injector
    from internal.service.indexing_service import IndexingService
    indexing_service = injector.get(IndexingService)
    indexing_service.update_document_enabled(document_id)
