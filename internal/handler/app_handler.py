#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2024/6/28 20:28
@Author : rxccai@gmail.com
@File   : app_handler.py
"""
import uuid
from dataclasses import dataclass

from flask import request
from flask_login import login_required, current_user
from injector import inject

from internal.schema.app_schema import (
    CreateAppReq,
    GetAppResp,
    GetPublishHistoriesWithPageReq,
    GetPublishHistoriesWithPageResp,
    FallbackHistoryToDraftReq,
    UpdateDebugConversationSummaryReq,
    DebugChatReq
)
from internal.service import AppService, RetrievalService
from pkg.paginator import PageModel
from pkg.response import validate_error_json, success_json, success_message, compact_generate_response


@inject
@dataclass
class AppHandler:
    app_service: AppService
    retrieval_service: RetrievalService

    @login_required
    def create_app(self):
        """创建新的APP记录"""
        req = CreateAppReq()
        if not req.validate():
            return validate_error_json(req.errors)
        app = self.app_service.create_app(req, account=current_user)
        return success_json({"id": app.id})

    @login_required
    def get_app(self, app_id: uuid.UUID):
        app = self.app_service.get_app(app_id, account=current_user)
        resp = GetAppResp()
        return success_json(resp.dump(app))

    @login_required
    def get_draft_app_config(self, app_id: uuid.UUID):
        return success_json(self.app_service.get_draft_app_config(app_id, account=current_user))

    @login_required
    def update_draft_app_config(self, app_id: uuid.UUID):
        draft_app_config = request.get_json(force=True, silent=True) or {}
        self.app_service.update_draft_app_config(app_id, draft_app_config, account=current_user)
        return success_message("更新应用草稿配置成功")

    @login_required
    def publish(self, app_id: uuid.UUID):
        self.app_service.publish_draft_app_config(app_id, account=current_user)
        return success_message("发布/更新应用配置成功")

    @login_required
    def cancel_publish(self, app_id: uuid.UUID):
        self.app_service.cancel_publish_app_config(app_id, account=current_user)
        return success_message("取消发布应用成功")

    @login_required
    def get_publish_histories_with_page(self, app_id: uuid.UUID):
        req = GetPublishHistoriesWithPageReq()
        if not req.validate():
            return validate_error_json(req.errors)
        app_config_versions, paginator = self.app_service.get_publish_histories_with_page(app_id,
                                                                                          req,
                                                                                          account=current_user)
        resp = GetPublishHistoriesWithPageResp(many=True)
        return success_json(PageModel(list=resp.dump(app_config_versions), paginator=paginator))

    @login_required
    def fallback_history_to_draft(self, app_id: uuid.UUID):
        req = FallbackHistoryToDraftReq()
        if not req.validate():
            return validate_error_json(req.errors)
        self.app_service.fallback_history_to_draft(app_id, req.app_config_version_id.data, account=current_user)
        return success_message("回退历史配置到草稿成功")

    @login_required
    def get_debug_conversation_summary(self, app_id: uuid.UUID):

        summary = self.app_service.get_debug_conversation_summary(app_id, account=current_user)
        return success_json({"summary": summary})

    @login_required
    def update_debug_conversation_summary(self, app_id: uuid.UUID):
        req = UpdateDebugConversationSummaryReq()
        if not req.validate():
            return validate_error_json(req.errors)

        self.app_service.update_debug_conversation_summary(app_id, req.summary.data, account=current_user)
        return success_message("更新AI应用长期记忆成功")

    @login_required
    def delete_debug_conversation(self, app_id: uuid.UUID):

        self.app_service.delete_debug_conversation(app_id, account=current_user)
        return success_message("删除AI应用长期记忆成功")

    @login_required
    def debug_chat(self, app_id: uuid.UUID):
        req = DebugChatReq()
        if not req.validate():
            return validate_error_json(req.errors)

        response = self.app_service.debug_chat(app_id, req.query.data, account=current_user)
        return compact_generate_response(response)

    @login_required
    def ping(self):
        from internal.entity.dataset_entity import RetrievalStrategy, RetrievalSource
        dataset_retrieval = self.retrieval_service.create_langchain_tool_from_search(
            dataset_ids=["e6fc9059-2570-4315-994e-e566d4398926", "3ea4623d-3c7a-45f0-9ace-33e68ab408e0"],
            account_id=current_user.id,
            retrieval_strategy=RetrievalStrategy.SEMANTIC,
            k=10,
            score=0.5,
            retrival_source=RetrievalSource.DEBUG
        )
        print("工具名称：", dataset_retrieval.name)
        print("工具描述：", dataset_retrieval.description)
        print("工具参数：", dataset_retrieval.args)
        content = dataset_retrieval.invoke({"query": "能简单介绍下什么是LLMOPS吗"})
        return success_json({"content": content})
