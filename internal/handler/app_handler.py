#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2024/6/28 20:28
@Author : rxccai@gmail.com
@File   : app_handler.py
"""
import json
import uuid
from dataclasses import dataclass
from typing import Any, Dict, Generator

from flask_login import login_required
from injector import inject
from langchain_core.memory import BaseMemory
from langchain_core.runnables import RunnableConfig
from langchain_core.tracers import Run
from langchain_openai import ChatOpenAI
from redis import Redis

from internal.core.agent.agents import FunctionCallAgent, AgentQueueManager
from internal.core.agent.entities.agent_entity import AgentConfig
from internal.core.tools.builtin_tools.providers import BuiltinProviderManager
from internal.entity.conversation_entity import InvokeFrom
from internal.schema.app_schema import CompletionReq
from internal.service import AppService, VectorDatabaseService, ConversationService
from pkg.response import success_json, validate_error_json, success_message, compact_generate_response


@inject
@dataclass
class AppHandler:
    app_service: AppService
    vector_database_service: VectorDatabaseService
    builtin_provider_manager: BuiltinProviderManager
    conversation_service: ConversationService
    redis_client: Redis

    @login_required
    def create_app(self):
        """创建新的APP记录"""
        app = self.app_service.create_app()
        return success_message(f"应用创建成功,id为{app.id}")

    @login_required
    def get_app(self, id: uuid.UUID):
        app = self.app_service.get_app(id)
        return success_message(f"获取应用详情，名称为{app.name}")

    @login_required
    def update_app(self, id: uuid.UUID):
        app = self.app_service.update_app(id)
        return success_message(f"更新应用详情，名称为{app.name}")

    @login_required
    def delete_app(self, id: uuid.UUID):
        app = self.app_service.delete_app(id)
        return success_message(f"删除应用详情，名称为{app.name}")

    @classmethod
    def _load_memory_variables(cls, input: Dict[str, Any], config: RunnableConfig) -> Dict[str, Any]:
        """加载记忆变量信息"""
        # 从config中获取configurable
        configurable = config.get("configurable")
        configurable_memory = configurable.get("memory", None)
        if configurable_memory is not None and isinstance(configurable_memory, BaseMemory):
            return configurable_memory.load_memory_variables(input)
        return {"history": []}

    @classmethod
    def _save_content(cls, run_obj: Run, config: RunnableConfig) -> None:
        """存储对应的上下文信息到记忆实体"""
        configurable = config.get("configurable")
        configurable_memory = configurable.get("memory", None)
        if configurable_memory is not None and isinstance(configurable_memory, BaseMemory):
            configurable_memory.save_context(run_obj.inputs, run_obj.outputs)

    def debug(self, app_id: uuid.UUID):
        req = CompletionReq()
        if not req.validate():
            return validate_error_json(req.errors)

        tools = [
            self.builtin_provider_manager.get_tool("google", "google_serper")(),
            self.builtin_provider_manager.get_tool("gaode", "gaode_weather")(),
            self.builtin_provider_manager.get_tool("dalle", "dalle3")(),
        ]

        agent = FunctionCallAgent(
            AgentConfig(
                llm=ChatOpenAI(model="gpt-4o-mini"),
                enable_long_term_memory=True,
                tools=tools,
            ),
            AgentQueueManager(
                user_id=uuid.uuid4(),
                task_id=uuid.uuid4(),
                invoke_from=InvokeFrom.DEBUGGER,
                redis_client=self.redis_client
            )
        )

        def stream_event_response() -> Generator:
            for agent_queue_event in agent.run(req.query.data, [], "用户介绍自己叫慕小课"):
                data = {
                    "id": str(agent_queue_event.id),
                    "task_id": str(agent_queue_event.task_id),
                    "event": agent_queue_event.event,
                    "thought": agent_queue_event.thought,
                    "observation ": agent_queue_event.observation,
                    "tool": agent_queue_event.tool,
                    "tool_input": agent_queue_event.tool_input,
                    "answer": agent_queue_event.answer,
                    "latency": agent_queue_event.latency
                }
                yield f"event: {data["event"]}\ndata: {json.dumps(data)}\n\n "

        return compact_generate_response(stream_event_response())

    # @classmethod
    # def _combine_documents(cls, documents: list[Document]) -> str:
    #     return "\n\n".join([document.page_content for document in documents])

    def ping(self):
        # raise CustomException(message="数据未找到")
        # google_seper = self.provider_factory.get_tool("google", "google_serper")()
        # print(google_seper)
        # print(google_seper.invoke("2023年北京半程马拉松的前3名成绩是多少"))
        # ------
        # google = self.provider_factory.get_provider("google")
        # google_serper_entity = google.get_tool_entity("google_serper")
        # print(google_serper_entity)
        # ------
        # providers = self.provider_factory.get_provider_entities()
        # return success_json({"providers": [provider.dict() for provider in providers]})
        # demo_task.delay(uuid.uuid4())
        # human_message = "Java是一门很强大的编程语言"
        # ai_message = "你好，我是Chatgpt，有什么可以帮助您的"
        # old_summary = "人类询问AI关于LLM（大语言模型）和Agent（智能代理）的介绍。AI解释说，LLM是基于深度学习的大型语言模型，专门用于处理自然语言，能够完成语言生成、翻译、情感分析等任务。Agent是一种智能系统，能够自主执行任务并与环境交互，具备自动执行、交互性和多模态处理等特性。LLM和Agent常常结合使用，Agent利用LLM理解人类指令并生成自然语言回复。"
        # summary = self.conversation_service.summary(human_message, ai_message, old_summary)
        # conversation_name = self.conversation_service.generate_conversation_name(human_message)
        # questions = self.conversation_service.generate_suggested_questions(human_message)
        from internal.core.agent.agents import FunctionCallAgent
        from internal.core.agent.entities.agent_entity import AgentConfig
        from langchain_openai import ChatOpenAI
        agent = FunctionCallAgent(AgentConfig(
            llm=ChatOpenAI(model="gpt-4o-mini"),
            preset_prompt="你是一个拥有20年经验的诗人, 请根据用户提供的主题来写一首诗"
        ))
        state = agent.run("月光", [], "")
        return success_json({"message": state["messages"][-1].content})
