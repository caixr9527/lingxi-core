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
@Time   : 2025/7/17 20:21
@Author : caixiaorong01@outlook.com
@File   : agent_service.py
"""
from dataclasses import dataclass
from typing import Any

from flask import current_app
from injector import inject
from langchain_core.messages import AnyMessage
from langchain_core.tools import BaseTool

from internal.core.agent.agents import BaseAgent, FunctionCallAgent, ReACTAgent, SupervisorAgent
from internal.core.agent.entities.agent_entity import AgentConfig
from internal.core.language_model.entities.model_entity import BaseLanguageModel
from internal.core.language_model.entities.model_entity import ModelFeature
from internal.core.memory import TokenBufferMemory
from internal.entity.app_entity import AppStatus, AppMode
from internal.entity.conversation_entity import InvokeFrom
from internal.entity.dataset_entity import RetrievalSource
from internal.model import AppConfig, AppConfigVersion, App
from internal.service.app_config_service import AppConfigService
from pkg.sqlalchemy import SQLAlchemy
from .language_model_service import LanguageModelService
from .retrieval_service import RetrievalService


@inject
@dataclass
class AgentService:
    db: SQLAlchemy
    language_model_service: LanguageModelService
    app_config_service: AppConfigService
    retrieval_service: RetrievalService

    def getTools(self, config: AppConfig | AppConfigVersion | dict[str, Any], app: App) -> list[BaseTool]:
        tools = self.app_config_service.get_langchain_tools_by_tools_config(config["tools"])

        # 检测是否关联了知识库
        if config["datasets"]:
            # 构建LangChain知识库检索工具
            dataset_retrieval = self.retrieval_service.create_langchain_tool_from_search(
                flask_app=current_app._get_current_object(),
                dataset_ids=[dataset["id"] for dataset in config["datasets"]],
                account_id=app.account_id,
                retrival_source=RetrievalSource.APP,
                **config["retrieval_config"],
            )
            tools.append(dataset_retrieval)

        # 检测是否关联工作流，如果关联了工作流则将工作流构建成工具添加到tools中
        if config["workflows"]:
            workflow_tools = self.app_config_service.get_langchain_tools_by_workflow_ids(
                [workflow["id"] for workflow in config["workflows"]]
            )
            tools.extend(workflow_tools)

        return tools

    def create_agent(self, config: AppConfig | AppConfigVersion | dict[str, Any], app: App, invoke_from: InvokeFrom) \
            -> tuple[BaseAgent, list[AnyMessage], BaseLanguageModel]:
        # 加载大语言模型
        llm = self.language_model_service.load_language_model(config.get("model_config", {}))

        # 实例化TokenBufferMemory用于提取短期记忆
        token_buffer_memory = TokenBufferMemory(
            db=self.db,
            conversation=app.debug_conversation,
            model_instance=llm,
        )
        history = token_buffer_memory.get_history_prompt_message(
            message_limit=config["dialog_round"],
            multimodal=config["multimodal"]["enable"],
        )

        # 将草稿配置中的tools转换成LangChain工具
        tools = self.getTools(config, app)

        # 根据LLM是否支持tool_call决定使用不同的Agent
        agent_class = FunctionCallAgent if ModelFeature.TOOL_CALL in llm.features else ReACTAgent
        agent_config = AgentConfig(
            user_id=app.account_id,
            invoke_from=invoke_from,
            preset_prompt=config["preset_prompt"],
            enable_long_term_memory=config["long_term_memory"]["enable"],
            tools=tools,
            review_config=config["review_config"]
        )
        agent = agent_class(
            name=app.name,
            llm=llm,
            agent_config=agent_config
        )

        if app.mode == AppMode.MULTI and len(config["agents"]) > 0:
            app_ids = [agent["id"] for agent in config["agents"]]
            collaborative_agent = self.get_collaborative_agent(app_ids)
            agent = SupervisorAgent(llm=llm,
                                    agent_config=agent_config,
                                    collaborative_agent=collaborative_agent,
                                    name=agent.name
                                    )

        return agent, history, llm

    def get_collaborative_agent(self, app_ids: list[str]) -> dict[str, Any]:
        apps = self.db.session.query(App).filter(
            App.id.in_(app_ids),
            App.status == AppStatus.PUBLISHED
        ).all()
        agent_dict: {str: BaseAgent} = {}
        for app in apps:
            config = self.app_config_service.get_app_config(app)
            llm = self.language_model_service.load_language_model(config.get("model_config", {}))
            tools = self.getTools(config, app)
            # agent = create_react_agent(model=llm,
            #                            tools=tools,
            #                            prompt=config.get("preset_prompt"),
            #                            name=app.name)
            agent_class = FunctionCallAgent if ModelFeature.TOOL_CALL in llm.features else ReACTAgent
            agent = agent_class(
                name=app.name,
                llm=llm,
                agent_config=AgentConfig(
                    user_id=app.account_id,
                    invoke_from=InvokeFrom.DEBUGGER,
                    preset_prompt=config["preset_prompt"],
                    enable_long_term_memory=False,
                    tools=tools,
                    review_config=config["review_config"]
                )
            )
            agent_dict[app.name] = agent

        return agent_dict
