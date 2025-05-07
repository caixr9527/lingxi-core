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
@Time   : 2024/11/3 16:51
@Author : caixiaorong01@outlook.com
@File   : segment_handler.py
"""
from dataclasses import dataclass
from uuid import UUID

from flask import request
from flask_login import login_required, current_user
from injector import inject

from internal.schema.segment_schema import (
    GetSegmentsWithPageReq,
    GetSegmentsWithPageResp,
    GetSegmentResp,
    UpdateSegmentEnabledReq,
    CreateSegmentReq,
    UpdateSegmentReq
)
from internal.service import SegmentService
from pkg.paginator import PageModel
from pkg.response import validate_error_json, success_json, success_message


@inject
@dataclass
class SegmentHandler:
    segment_service: SegmentService

    @login_required
    def create_segment(self, dataset_id: UUID, document_id: UUID):
        """创建知识库文档片段"""
        req = CreateSegmentReq()
        if not req.validate():
            return validate_error_json(req.errors)
        self.segment_service.create_segment(dataset_id, document_id, req, account=current_user)
        return success_message("新增知识库文档片段成功")

    @login_required
    def get_segment_with_page(self, dataset_id: UUID, document_id: UUID):
        req = GetSegmentsWithPageReq(request.args)
        if not req.validate():
            return validate_error_json(req.errors)
        segments, paginator = self.segment_service.get_segment_with_page(dataset_id,
                                                                         document_id,
                                                                         req,
                                                                         account=current_user)
        resp = GetSegmentsWithPageResp(many=True)
        return success_json(PageModel(list=resp.dump(segments), paginator=paginator))

    @login_required
    def get_segment(self, dataset_id: UUID, document_id: UUID, segment_id: UUID):
        segment = self.segment_service.get_segment(dataset_id, document_id, segment_id, account=current_user)
        resp = GetSegmentResp()
        return success_json(resp.dump(segment))

    @login_required
    def update_segment_enabled(self, dataset_id: UUID, document_id: UUID, segment_id: UUID):
        req = UpdateSegmentEnabledReq()
        if not req.validate():
            return validate_error_json(req.errors)
        self.segment_service.update_segment_enabled(dataset_id,
                                                    document_id,
                                                    segment_id,
                                                    req.enabled.data,
                                                    account=current_user)
        return success_message("修改片段状态成功")

    @login_required
    def update_segment(self, dataset_id: UUID, document_id: UUID, segment_id: UUID):
        """根据传递的信息更新文档片段信息"""
        # 1.提取请求并校验
        req = UpdateSegmentReq()
        if not req.validate():
            return validate_error_json(req.errors)

        # 2.调用服务更新文档片段信息
        self.segment_service.update_segment(dataset_id, document_id, segment_id, req, account=current_user)

        return success_message("更新文档片段成功")

    @login_required
    def delete_segment(self, dataset_id: UUID, document_id: UUID, segment_id: UUID):
        self.segment_service.delete_segment(dataset_id, document_id, segment_id, account=current_user)
        return success_message("删除文档片段成功")
