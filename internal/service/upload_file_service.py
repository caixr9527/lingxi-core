#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2024/10/15 22:05
@Author : rxccai@gmail.com
@File   : upload_file_service.py
"""
from dataclasses import dataclass

from injector import inject

from internal.model import UploadFile
from pkg.sqlalchemy import SQLAlchemy
from .base_service import BaseService


@inject
@dataclass
class UploadFileService(BaseService):
    db: SQLAlchemy

    def create_upload_file(self, **kwargs) -> UploadFile:
        return self.create(UploadFile, **kwargs)
