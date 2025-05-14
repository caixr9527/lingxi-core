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
@Time   : 2025/1/13 21:23
@Author : caixiaorong01@outlook.com
@File   : workflow_handler.py.py
"""
from dataclasses import dataclass
from uuid import UUID

from flask import request
from flask_login import current_user, login_required
from injector import inject

from internal.schema.workflow_schema import (
    CreateWorkflowReq,
    UpdateWorkflowReq,
    GetWorkflowResp,
    GetWorkflowsWithPageReq,
    GetWorkflowsWithPageResp,
)
from internal.service import WorkflowService
from pkg.paginator import PageModel
from pkg.response import validate_error_json, success_json, success_message, compact_generate_response


@inject
@dataclass
class WorkflowHandler:
    """工作流处理器"""
    workflow_service: WorkflowService

    @login_required
    def create_workflow(self):
        """新增工作流"""
        req = CreateWorkflowReq()
        if not req.validate():
            return validate_error_json(req.errors)

        workflow = self.workflow_service.create_workflow(req, current_user)

        return success_json({"id": workflow.id})

    @login_required
    def delete_workflow(self, workflow_id: UUID):
        """根据传递的工作流id删除指定的工作流"""
        self.workflow_service.delete_workflow(workflow_id, current_user)
        return success_message("删除工作流成功")

    @login_required
    def update_workflow(self, workflow_id: UUID):
        """根据传递的工作流id获取工作流详情"""
        req = UpdateWorkflowReq()
        if not req.validate():
            return validate_error_json(req.errors)

        self.workflow_service.update_workflow(workflow_id, current_user, **req.data)

        return success_message("修改工作流基础信息成功")

    @login_required
    def get_workflow(self, workflow_id: UUID):
        """根据传递的工作流id获取工作流详情"""
        workflow = self.workflow_service.get_workflow(workflow_id, current_user)
        resp = GetWorkflowResp()
        return success_json(resp.dump(workflow))

    @login_required
    def get_workflows_with_page(self):
        """获取当前登录账号下的工作流分页列表数据"""
        req = GetWorkflowsWithPageReq(request.args)
        if not req.validate():
            return validate_error_json(req.errors)

        workflows, paginator = self.workflow_service.get_workflows_with_page(req, current_user)

        resp = GetWorkflowsWithPageResp(many=True)

        return success_json(PageModel(list=resp.dump(workflows), paginator=paginator))

    @login_required
    def update_draft_graph(self, workflow_id: UUID):
        """根据传递的工作流id+请求信息更新工作流草稿图配置"""
        draft_graph_dict = request.get_json(force=True, silent=True) or {
            "nodes": [],
            "edges": [],
        }

        self.workflow_service.update_draft_graph(workflow_id, draft_graph_dict, current_user)

        return success_message("更新工作流草稿配置成功")

    @login_required
    def get_draft_graph(self, workflow_id: UUID):
        """根据传递的工作流id获取该工作流的草稿配置信息"""
        draft_graph = self.workflow_service.get_draft_graph(workflow_id, current_user)
        return success_json(draft_graph)

    @login_required
    def debug_workflow(self, workflow_id: UUID):
        """根据传递的变量字典+工作流id调试指定的工作流"""
        inputs = request.get_json(force=True, silent=True) or {}

        response = self.workflow_service.debug_workflow(workflow_id, inputs, current_user)

        return compact_generate_response(response)

    @login_required
    def publish_workflow(self, workflow_id: UUID):
        """根据传递的工作流id发布指定的工作流"""
        self.workflow_service.publish_workflow(workflow_id, current_user)
        return success_message("发布工作流成功")

    @login_required
    def cancel_publish_workflow(self, workflow_id: UUID):
        """根据传递的工作流id取消发布指定的工作流"""
        self.workflow_service.cancel_publish_workflow(workflow_id, current_user)
        return success_message("取消发布工作流成功")
