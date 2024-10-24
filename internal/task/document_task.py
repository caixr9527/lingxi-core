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
def build_documents(documents_ids: list[UUID]) -> None:
    from app.http.module import injector
    from internal.service.indexing_service import IndexingService

    indexing_service = injector.get(IndexingService)
    indexing_service.build_documents(documents_ids)
