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
@Time   : 2024/10/15 21:24
@Author : caixiaorong01@outlook.com
@File   : upload_file_handler.py
"""
from dataclasses import dataclass

from flask_login import login_required, current_user
from injector import inject

from internal.schema.upload_file_schema import UploadFileReq, UploadFileResp, UploadImageReq
from internal.service import CosService
from pkg.response import validate_error_json, success_json


@inject
@dataclass
class UploadFileHandler:
    """上传文件处理器"""
    cos_service: CosService

    @login_required
    def upload_file(self):
        req = UploadFileReq()
        if not req.validate():
            return validate_error_json(req.errors)

        upload_file = self.cos_service.upload_file(req.file.data, account=current_user)

        resp = UploadFileResp()
        return success_json(resp.dump(upload_file))

    @login_required
    def upload_image(self):
        req = UploadImageReq()
        if not req.validate():
            return validate_error_json(req.errors)

        upload_file = self.cos_service.upload_file(req.file.data, account=current_user, only_image=True)
        image_url = self.cos_service.get_file_url(upload_file.key)
        return success_json({"image_url": image_url})
