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

from internal.core.language_model import LanguageModelManager
from internal.schema.app_schema import (
    CreateAppReq,
    GetAppResp,
    GetPublishHistoriesWithPageReq,
    GetPublishHistoriesWithPageResp,
    FallbackHistoryToDraftReq,
    UpdateDebugConversationSummaryReq,
    DebugChatReq,
    GetDebugConversationMessagesWithPageReq,
    GetDebugConversationMessagesWithPageResp, UpdateAppReq, GetAppsWithPageReq, GetAppsWithPageResp
)
from internal.service import AppService, RetrievalService
from pkg.paginator import PageModel
from pkg.response import validate_error_json, success_json, success_message, compact_generate_response


@inject
@dataclass
class AppHandler:
    app_service: AppService
    retrieval_service: RetrievalService
    language_model_manager: LanguageModelManager

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
    def update_app(self, app_id: uuid.UUID):
        """根据传递的信息更新指定的应用"""
        # 1.提取数据并校验
        req = UpdateAppReq()
        if not req.validate():
            return validate_error_json(req.errors)

        # 2.调用服务更新数据
        self.app_service.update_app(app_id, account=current_user, **req.data)

        return success_message("修改Agent智能体应用成功")

    @login_required
    def copy_app(self, app_id: uuid.UUID):
        """根据传递的应用id快速拷贝该应用"""
        app = self.app_service.copy_app(app_id, account=current_user)
        return success_json({"id": app.id})

    @login_required
    def delete_app(self, app_id: uuid.UUID):
        """根据传递的信息删除指定的应用"""
        self.app_service.delete_app(app_id, account=current_user)
        return success_message("删除Agent智能体应用成功")

    @login_required
    def get_apps_with_page(self):
        """获取当前登录账号的应用分页列表数据"""
        # 1.提取数据并校验
        req = GetAppsWithPageReq(request.args)
        if not req.validate():
            return validate_error_json(req.errors)

        # 2.调用服务获取列表数据以及分页器
        apps, paginator = self.app_service.get_apps_with_page(req, account=current_user)

        # 3.构建响应结构并返回
        resp = GetAppsWithPageResp(many=True)

        return success_json(PageModel(list=resp.dump(apps), paginator=paginator))

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
        req = GetPublishHistoriesWithPageReq(request.args)
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
        return success_message("清空应用调试会话记录成功")

    @login_required
    def debug_chat(self, app_id: uuid.UUID):
        req = DebugChatReq()
        if not req.validate():
            return validate_error_json(req.errors)

        response = self.app_service.debug_chat(app_id, req.query.data, account=current_user)
        return compact_generate_response(response)

    @login_required
    def stop_debug(self, app_id: uuid.UUID, task_id: uuid.UUID):
        self.app_service.stop_debug_chat(app_id, task_id, account=current_user)
        return success_message("停止应用调试会话成功")

    @login_required
    def get_debug_conversation_messages_with_page(self, app_id: uuid.UUID):
        req = GetDebugConversationMessagesWithPageReq(request.args)
        if not req.validate():
            return validate_error_json(req.errors)

        messages, paginator = self.app_service.get_debug_conversation_messages_with_page(app_id,
                                                                                         req,
                                                                                         account=current_user)
        resp = GetDebugConversationMessagesWithPageResp(many=True)
        return success_json(PageModel(list=resp.dump(messages), paginator=paginator))

    @login_required
    def get_published_config(self, app_id: uuid.UUID):
        """根据传递的应用id获取应用的发布配置信息"""
        published_config = self.app_service.get_published_config(app_id, current_user)
        return success_json(published_config)

    @login_required
    def regenerate_web_app_token(self, app_id: uuid.UUID):
        """根据传递的应用id重新生成WebApp凭证标识"""
        token = self.app_service.regenerate_web_app_token(app_id, current_user)
        return success_json({"token": token})

    # @login_required
    def ping(self):
        provider = self.language_model_manager.get_provider("ollama")
        model_entity = provider.get_model_entity("qwen2.5-7b")
        model_class = provider.get_model_class(model_entity.model_type)
        llm = model_class(**{
            **model_entity.attributes,
            "features": model_entity.features,
            "metadata": model_entity.metadata,
        })
        return success_json({
            "content": llm.invoke("你好，你是").content,
            "features": llm.features,
            "metadata": llm.metadata,
        })
