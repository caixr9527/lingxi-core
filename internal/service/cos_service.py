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
@Time   : 2024/10/15 21:47
@Author : rxccai@gmail.com
@File   : cos_service.py
"""
import hashlib
import os
import uuid
from dataclasses import dataclass
from datetime import datetime

from injector import inject
from qcloud_cos import CosS3Client, CosConfig
from werkzeug.datastructures import FileStorage

from internal.entity.upload_file_entity import ALLOW_IMAGE_EXTENSION, ALL_DOCUMENT_EXTENSION
from internal.exception import FailException
from internal.model import UploadFile, Account
from .upload_file_service import UploadFileService


@inject
@dataclass
class CosService:
    upload_file_service: UploadFileService

    def upload_file(self, file: FileStorage, account: Account, only_image: bool = False) -> UploadFile:

        filename = file.filename
        extension = filename.rsplit(".", 1)[-1] if "." in filename else ""
        if extension.lower() not in (ALLOW_IMAGE_EXTENSION + ALL_DOCUMENT_EXTENSION):
            raise FailException(f"该.{extension}扩展的文件不允许上传")
        elif only_image and extension not in ALLOW_IMAGE_EXTENSION:
            raise FailException(f"该.{extension}扩展的文件不允许上传,请上传正确的图片")

        client = self._get_client()
        bucket = self._get_bucket()
        random_filename = str(uuid.uuid4()) + "." + extension
        now = datetime.now()
        upload_filename = f"{now.year}/{now.month:02d}/{now.day:02d}/{random_filename}"
        file_content = file.stream.read()
        try:
            client.put_object(bucket, file_content, upload_filename)
        except Exception as e:
            raise FailException("上传文件失败，请稍后重试")
        return self.upload_file_service.create_upload_file(
            account_id=account.id,
            name=filename,
            key=upload_filename,
            size=len(file_content),
            extension=extension,
            mime_type=file.mimetype,
            hash=hashlib.sha3_256(file_content).hexdigest(),
        )

    def download_file(self, key: str, target_file_path: str):
        client = self._get_client()
        bucket = self._get_bucket()
        client.download_file(bucket, key, target_file_path)

    @classmethod
    def get_file_url(cls, key: str) -> str:
        cos_domain = os.getenv("COS_DOMAIN")
        if not cos_domain:
            bucket = os.getenv("COS_BUCKET")
            schema = os.getenv("COS_SCHEMA", "https")
            region = os.getenv("COS_REGION")
            cos_domain = f"{schema}://{bucket}.cos.{region}.myqcloud.com"
        return f"{cos_domain}/{key}"

    @classmethod
    def _get_client(cls) -> CosS3Client:
        conf = CosConfig(
            Region=os.getenv("COS_REGION"),
            SecretId=os.getenv("COS_SECRET_ID"),
            SecretKey=os.getenv("COS_SECRET_KEY"),
            Token=None,
            Scheme=os.getenv("COS_SCHEMA", "https")
        )
        return CosS3Client(conf)

    @classmethod
    def _get_bucket(cls) -> str:
        return os.getenv("COS_BUCKET")
