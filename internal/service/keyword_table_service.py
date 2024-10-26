#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2024/10/26 09:59
@Author : rxccai@gmail.com
@File   : keyword_table_service.py
"""
from dataclasses import dataclass
from uuid import UUID

from injector import inject

from internal.model import KeywordTable
from pkg.sqlalchemy import SQLAlchemy
from .base_service import BaseService


@inject
@dataclass
class KeywordTableService(BaseService):
    db: SQLAlchemy

    def get_keyword_table_from_dataset_id(self, dataset_id: UUID) -> KeywordTable:
        keyword_table = self.db.session.query(KeywordTable).filter(
            KeywordTable.dataset_id == dataset_id
        ).one_or_none()
        if keyword_table is None:
            keyword_table = self.create(KeywordTable, dataset_id=dataset_id, keyword_table={})

        return keyword_table
