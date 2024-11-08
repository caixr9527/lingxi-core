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
from operator import itemgetter
from queue import Queue
from threading import Thread
from typing import Any, Dict, Literal, Generator

from injector import inject
from langchain.memory import ConversationBufferWindowMemory
from langchain_community.chat_message_histories import FileChatMessageHistory
from langchain_core.memory import BaseMemory
from langchain_core.messages import ToolMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables import RunnablePassthrough, RunnableLambda, RunnableConfig
from langchain_core.tracers import Run
from langchain_openai import ChatOpenAI
from langgraph.constants import END
from langgraph.graph import MessagesState, StateGraph

from internal.core.tools.builtin_tools.providers import BuiltinProviderManager
from internal.schema.app_schema import CompletionReq
from internal.service import AppService, VectorDatabaseService
from internal.task.demo_task import demo_task
from pkg.response import success_json, validate_error_json, success_message, compact_generate_response


@inject
@dataclass
class AppHandler:
    app_service: AppService
    vector_database_service: VectorDatabaseService
    builtin_provider_manager: BuiltinProviderManager

    def create_app(self):
        """创建新的APP记录"""
        app = self.app_service.create_app()
        return success_message(f"应用创建成功,id为{app.id}")

    def get_app(self, id: uuid.UUID):
        app = self.app_service.get_app(id)
        return success_message(f"获取应用详情，名称为{app.name}")

    def update_app(self, id: uuid.UUID):
        app = self.app_service.update_app(id)
        return success_message(f"更新应用详情，名称为{app.name}")

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
        q = Queue()
        query = req.query.data

        def graph_app() -> None:
            tools = [
                self.builtin_provider_manager.get_tool("google", "google_serper")(),
                self.builtin_provider_manager.get_tool("gaode", "gaode_weather")(),
                self.builtin_provider_manager.get_tool("dalle", "dalle3")(),
            ]

            # 定义LLM机器人节点
            def chatbot(state: MessagesState) -> MessagesState:
                llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.7).bind_tools(tools)
                is_first_chunk = True
                is_tool_call = False
                gathered = None
                id = str(uuid.uuid4())
                for chunk in llm.stream(state["messages"]):
                    if is_first_chunk and chunk.content == "" and not chunk.tool_calls:
                        continue

                    if is_first_chunk:
                        gathered = chunk
                        is_first_chunk = False
                    else:
                        gathered += chunk

                    if chunk.tool_calls or is_tool_call:
                        is_tool_call = True
                        q.put({
                            "id": id,
                            "event": "agent_thought",
                            "data": json.dumps(chunk.tool_call_chunks),
                        })
                    else:
                        q.put({
                            "id": id,
                            "event": "agent_message",
                            "data": chunk.content,
                        })
                return {"messages": [gathered]}

            # 定义工具/函数调用节点
            def tool_executor(state: MessagesState) -> MessagesState:
                # 提取数据状态中的tool_calls
                tool_calls = state["messages"][-1].tool_calls
                tools_by_name = {tool.name: tool for tool in tools}
                # 执行工具获取结果
                messages = []
                for tool_call in tool_calls:
                    id = str(uuid.uuid4())
                    tool = tools_by_name[tool_call["name"]]
                    tool_result = tool.invoke(tool_call["args"])
                    messages.append(ToolMessage(
                        tool_call_id=tool_call["id"],
                        content=json.dumps(tool_result),
                        name=tool_call["name"]
                    ))
                    q.put({
                        "id": id,
                        "event": "agent_action",
                        "data": json.dumps(tool_result)
                    })
                return {"messages": messages}

            # 定义路由函数
            def route(state: MessagesState) -> Literal["tool_executor", "__end__"]:
                ai_message = state["messages"][-1]
                if hasattr(ai_message, "tool_calls") and len(ai_message.tool_calls) > 0:
                    return "tool_executor"
                return END

            # 创建状态图
            graph_builder = StateGraph(MessagesState)
            # 添加节点
            graph_builder.add_node("llm", chatbot)
            graph_builder.add_node("tool_executor", tool_executor)

            graph_builder.set_entry_point("llm")
            graph_builder.add_conditional_edges("llm", route)
            graph_builder.add_edge("tool_executor", "llm")

            graph = graph_builder.compile()

            result = graph.invoke({"messages": [("human", query)]})
            print("结果:", result)
            q.put(None)

        def stream_event_response() -> Generator:
            # 从队列获取数据
            while True:
                item = q.get()
                if item is None:
                    break
                yield f"event: {item.get('event')}\ndata: {json.dumps(item)}\n\n"
                q.task_done()

        t = Thread(target=graph_app)
        t.start()
        return compact_generate_response(stream_event_response())

    def _debug(self, app_id: uuid.UUID):
        """聊天接口"""
        req = CompletionReq()
        if not req.validate():
            return validate_error_json(req.errors)
        system_prompt = "你是一个强大的聊天机器人,能根据对应的上下文和历史对话信息回复用户问题。\n\n<context>{context}</context>"
        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            MessagesPlaceholder("history"),
            ("human", "{query}"),
        ])
        memory = ConversationBufferWindowMemory(
            k=3,
            input_key="query",
            output_key="output",
            return_messages=True,
            chat_memory=FileChatMessageHistory("./storage/memory/chat_history.txt")
        )
        # todo 这里换成chatgpt的模型
        llm = ChatOpenAI(model="moonshot-v1-8k")
        retriever = self.vector_database_service.get_retriever() | self.vector_database_service.combine_documents
        chain = (RunnablePassthrough.assign(
            history=RunnableLambda(self._load_memory_variables) | itemgetter("history"),
            context=itemgetter("query") | retriever
        ) | prompt | llm | StrOutputParser()).with_listeners(on_end=self._save_content)

        chain_input = {"query": req.query.data}
        content = chain.invoke(chain_input, config={"configurable": {"memory": memory}})

        return success_json({"content": content})

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
        demo_task.delay(uuid.uuid4())
        return success_json()
