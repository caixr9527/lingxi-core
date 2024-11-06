#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2024/11/6 22:23
@Author : rxccai@gmail.com
@File   : dataset_task.py
"""
from uuid import UUID

from celery import shared_task


@shared_task
def delete_dataset(dataset_id: UUID) -> None:
    from app.http.module import injector
    from internal.service.indexing_service import IndexingService
    indexing_service = injector.get(IndexingService)
    indexing_service.delete_dataset(dataset_id)
