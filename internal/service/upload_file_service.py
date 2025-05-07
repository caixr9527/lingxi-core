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
@Time   : 2024/10/15 22:05
@Author : caixiaorong01@outlook.com
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
