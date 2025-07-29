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
@Time   : 2024/6/28 20:28
@Author : caixiaorong01@outlook.com
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
        req = UpdateAppReq()
        if not req.validate():
            return validate_error_json(req.errors)

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
        req = GetAppsWithPageReq(request.args)
        if not req.validate():
            return validate_error_json(req.errors)

        apps, paginator = self.app_service.get_apps_with_page(req, account=current_user)

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

        response = self.app_service.debug_chat(app_id, req, account=current_user)
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
        from langgraph.prebuilt import create_react_agent
        from langchain_core.tools import StructuredTool
        provider = self.language_model_manager.get_provider("openai")
        model_entity = provider.get_model_entity("gpt-4o")
        model_class = provider.get_model_class(model_entity.model_type)
        llm = model_class(**{
            **model_entity.attributes,
            "features": model_entity.features,
            "metadata": model_entity.metadata,
        })

        def web_search() -> str:
            """Find the quantity of apples and bananas"""
            return "苹果数量是20个，香蕉12个。"

        research_agent = create_react_agent(
            model=llm,
            tools=[StructuredTool.from_function(func=web_search)],
            prompt=(
                "You are a research agent.\n\n"
                "INSTRUCTIONS:\n"
                "- Assist ONLY with research-related tasks, DO NOT do any math\n"
                "- After you're done with your tasks, respond to the supervisor directly\n"
                "- Respond ONLY with the results of your work, do NOT include ANY other text."
            ),
            name="research_agent",
        )

        def add(a: float, b: float):
            """Add two numbers."""
            return a + b

        def multiply(a: float, b: float):
            """Multiply two numbers."""
            return a * b

        def divide(a: float, b: float):
            """Divide two numbers."""
            return a / b

        math_agent = create_react_agent(
            model=llm,
            tools=[StructuredTool.from_function(func=add), StructuredTool.from_function(func=multiply),
                   StructuredTool.from_function(func=divide)],
            prompt=(
                "You are a math agent.\n\n"
                "INSTRUCTIONS:\n"
                "- Assist ONLY with math-related tasks\n"
                "- After you're done with your tasks, respond to the supervisor directly\n"
                "- Respond ONLY with the results of your work, do NOT include ANY other text."
            ),
            name="math_agent",
        )

        from typing import Annotated
        from langchain_core.tools import tool, InjectedToolCallId
        from langgraph.prebuilt import InjectedState
        from langgraph.types import Command
        from langgraph.graph import StateGraph, START, MessagesState
        from internal.core.agent.entities.agent_entity import AgentState
        def create_handoff_tool(*, agent_name: str, description: str | None = None):
            name = f"transfer_to_{agent_name}"
            description = description or f"Ask {agent_name} for help."

            @tool(name, description=description)
            def handoff_tool(
                    state: Annotated[MessagesState, InjectedState],
                    tool_call_id: Annotated[str, InjectedToolCallId],
            ) -> Command:
                tool_message = {
                    # "task_id": state["task_id"],
                    # "iteration_count": state["iteration_count"],
                    # "history": state["history"],
                    # "long_term_memory": state["long_term_memory"],
                    "role": "tool",
                    "content": f"Successfully transferred to {agent_name}",
                    "name": name,
                    "tool_call_id": tool_call_id,
                }
                return Command(
                    goto=agent_name,
                    update={**state, "messages": state["messages"] + [tool_message]},
                    graph=Command.PARENT,
                )

            return handoff_tool

        # Handoffs
        assign_to_research_agent = create_handoff_tool(
            agent_name="research_agent",
            description="Assign task to a researcher agent.",
        )

        assign_to_math_agent = create_handoff_tool(
            agent_name="math_agent",
            description="Assign task to a math agent.",
        )
        supervisor_agent = create_react_agent(
            model=llm,
            tools=[assign_to_research_agent, assign_to_math_agent],
            prompt=(
                "You are a supervisor managing two agents:\n"
                "- a research agent. Assign research-related tasks to this agent\n"
                "- a math agent. Assign math-related tasks to this agent\n"
                "Assign work to one agent at a time, do not call agents in parallel.\n"
                "Do not do any work yourself."
            ),
            name="supervisor",
        )
        from langgraph.graph import END

        # Define the multi-agent supervisor graph
        supervisor = (
            StateGraph(AgentState)
            # NOTE: `destinations` is only needed for visualization and doesn't affect runtime behavior
            .add_node(supervisor_agent, destinations=("research_agent", "math_agent", END))
            .add_node(research_agent)
            .add_node(math_agent)
            .add_edge(START, "supervisor")
            # always return back to the supervisor
            .add_edge("research_agent", "supervisor")
            .add_edge("math_agent", "supervisor")
            .compile()
        )
        # for chunk in supervisor.stream(
        #         {
        #             "messages": [
        #                 {
        #                     "role": "user",
        #                     "content": "查找下苹果和香蕉的数量，并计算总数是多少？",
        #                 }
        #             ]
        #         },
        # ):
        #     print(chunk)

        message = supervisor.invoke({
            "messages": [
                {
                    "role": "user",
                    "content": "查找下苹果和香蕉的数量，并计算总数是多少？",
                }
            ],
            "task_id": uuid.uuid4(),
            "iteration_count": 0,
            "history": [],
            "long_term_memory": "",
        })
        return success_json(message.get("messages")[-1].content)
