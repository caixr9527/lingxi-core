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
@Time   : 2025/2/7 21:09
@Author : rxccai@gmail.com
@File   : react_agent.py
"""
import json
import logging
import re
import time
import uuid

from langchain_core.messages import SystemMessage, messages_to_dict, HumanMessage, RemoveMessage, AIMessage
from langchain_core.tools import render_text_description_and_args

from internal.core.agent.entities.agent_entity import (
    AgentState,
    AGENT_SYSTEM_PROMPT_TEMPLATE,
    REACT_AGENT_SYSTEM_PROMPT_TEMPLATE, MAX_ITERATION_RESPONSE,
)
from internal.core.agent.entities.queue_entity import QueueEvent, AgentThought
from internal.core.language_model.entities.model_entity import ModelFeature
from internal.exception import FailException
from .function_call_agent import FunctionCallAgent


class ReACTAgent(FunctionCallAgent):
    """基于ReACT推理的智能体，继承FunctionCallAgent，并重写long_term_memory_node和llm_node两个节点"""

    def _long_term_memory_recall_node(self, state: AgentState) -> AgentState:
        """重写长期记忆召回节点，使用prompt实现工具调用及规范数据生成"""
        # 判断是否支持工具调用，如果支持工具调用，则可以直接使用工具智能体的长期记忆召回节点
        if ModelFeature.TOOL_CALL in self.llm.features:
            return super()._long_term_memory_recall_node(state)

        # 根据传递的智能体配置判断是否需要召回长期记忆
        long_term_memory = ""
        if self.agent_config.enable_long_term_memory:
            long_term_memory = state["long_term_memory"]
            self.agent_queue_manager.publish(state["task_id"], AgentThought(
                id=uuid.uuid4(),
                task_id=state["task_id"],
                event=QueueEvent.LONG_TERM_MEMORY_RECALL,
                observation=long_term_memory,
            ))

        # 检测是否支持AGENT_THOUGHT，如果不支持，则使用没有工具描述的prompt
        if ModelFeature.AGENT_THOUGHT not in self.llm.features:
            preset_messages = [
                SystemMessage(AGENT_SYSTEM_PROMPT_TEMPLATE.format(
                    preset_prompt=self.agent_config.preset_prompt,
                    long_term_memory=long_term_memory,
                ))
            ]
        else:
            # 支持智能体推理，则使用REACT_AGENT_SYSTEM_PROMPT_TEMPLATE并添加工具描述
            preset_messages = [
                SystemMessage(REACT_AGENT_SYSTEM_PROMPT_TEMPLATE.format(
                    preset_prompt=self.agent_config.preset_prompt,
                    long_term_memory=long_term_memory,
                    tool_description=render_text_description_and_args(self.agent_config.tools),
                ))
            ]

        # 将短期历史消息添加到消息列表中
        history = state["history"]
        if isinstance(history, list) and len(history) > 0:
            # 校验历史消息是不是复数形式，也就是[人类消息, AI消息, 人类消息, AI消息, ...]
            if len(history) % 2 != 0:
                self.agent_queue_manager.publish_error(state["task_id"], "智能体历史消息列表格式错误")
                logging.exception(
                    "智能体历史消息列表格式错误, len(history)=%(len_history)d, history=%(history)s",
                    {"len_history": len(history), "history": json.dumps(messages_to_dict(history))},
                )
                raise FailException("智能体历史消息列表格式错误")
            # 拼接历史消息
            preset_messages.extend(history)

        # 拼接当前用户的提问消息
        human_message = state["messages"][-1]
        preset_messages.append(HumanMessage(human_message.content))

        # 处理预设消息，将预设消息添加到用户消息前，先去删除用户的原始消息，然后补充一个新的代替
        return {
            "messages": [RemoveMessage(id=human_message.id), *preset_messages],
        }

    def _llm_node(self, state: AgentState) -> AgentState:
        """重写工具调用智能体的LLM节点"""
        # 判断当前LLM是否支持tool_call，如果是则使用FunctionCallAgent的_llm_node
        if ModelFeature.TOOL_CALL in self.llm.features:
            return super()._llm_node(state)

        # 检测当前Agent迭代次数是否符合需求
        if state["iteration_count"] > self.agent_config.max_iteration_count:
            self.agent_queue_manager.publish(
                state["task_id"],
                AgentThought(
                    id=uuid.uuid4(),
                    task_id=state["task_id"],
                    event=QueueEvent.AGENT_MESSAGE,
                    thought=MAX_ITERATION_RESPONSE,
                    message=messages_to_dict(state["messages"]),
                    answer=MAX_ITERATION_RESPONSE,
                    latency=0,
                ))
            self.agent_queue_manager.publish(
                state["task_id"],
                AgentThought(
                    id=uuid.uuid4(),
                    task_id=state["task_id"],
                    event=QueueEvent.AGENT_END,
                ))
            return {"messages": [AIMessage(MAX_ITERATION_RESPONSE)]}

        # 从智能体配置中提取大语言模型
        id = uuid.uuid4()
        start_at = time.perf_counter()
        llm = self.llm

        # 定义变量存储流式输出内容
        gathered = None
        is_first_chunk = True
        generation_type = ""

        # 流式输出调用LLM，并判断输出内容是否以"```json"为开头，用于区分工具调用和文本生成
        for chunk in llm.stream(state["messages"]):
            # 修复第三方api中转导致数据为None
            if chunk.usage_metadata is not None:
                chunk.usage_metadata['input_tokens'] = 0 if chunk.usage_metadata["input_tokens"] is None else \
                    chunk.usage_metadata["input_tokens"]
                chunk.usage_metadata['output_tokens'] = 0 if chunk.usage_metadata["output_tokens"] is None else \
                    chunk.usage_metadata["output_tokens"]
                chunk.usage_metadata['total_tokens'] = 0 if chunk.usage_metadata["total_tokens"] is None else \
                    chunk.usage_metadata["total_tokens"]
            # 处理流式输出内容块叠加
            if is_first_chunk:
                gathered = chunk
                is_first_chunk = False
            else:
                gathered += chunk

            # 如果生成的是消息则提交智能体消息事件
            if generation_type == "message":
                # 提取片段内容并校测是否开启输出审核
                review_config = self.agent_config.review_config
                content = chunk.content
                if review_config["enable"] and review_config["outputs_config"]["enable"]:
                    for keyword in review_config["keywords"]:
                        content = re.sub(re.escape(keyword), "**", content, flags=re.IGNORECASE)

                self.agent_queue_manager.publish(state["task_id"], AgentThought(
                    id=id,
                    task_id=state["task_id"],
                    event=QueueEvent.AGENT_MESSAGE,
                    thought=content,
                    message=messages_to_dict(state["messages"]),
                    answer=content,
                    latency=(time.perf_counter() - start_at),
                ))

            # 检测生成的类型是工具调用还是文本生成，同时赋值
            if not generation_type:
                # 当生成内容的长度大于等于7(```json)长度时才可以判断出类型是什么
                if len(gathered.content.strip()) >= 7:
                    if gathered.content.strip().startswith("```json"):
                        generation_type = "thought"
                    else:
                        generation_type = "message"
                        # 添加发布事件，避免前几个字符遗漏
                        self.agent_queue_manager.publish(state["task_id"], AgentThought(
                            id=id,
                            task_id=state["task_id"],
                            event=QueueEvent.AGENT_MESSAGE,
                            thought=gathered.content,
                            message=messages_to_dict(state["messages"]),
                            answer=gathered.content,
                            latency=(time.perf_counter() - start_at),
                        ))

        # 计算输入、输出token数
        input_token_count = self.llm.get_num_tokens_from_messages(state["messages"])
        output_token_count = self.llm.get_num_tokens_from_messages([gathered])

        # 获取输入/输出价格和单位
        input_price, output_price, unit = self.llm.get_pricing()

        # 计算总token+总成本
        total_token_count = input_token_count + output_token_count
        total_price = (input_token_count * input_price + output_token_count * output_price) * unit

        # 如果类型为推理则解析json，并添加智能体消息
        if generation_type == "thought":
            try:
                # 使用正则解析信息，如果失败则当成普通消息返回
                pattern = r"^```json(.*?)```$"
                matches = re.findall(pattern, gathered.content, re.DOTALL)
                match_json = json.loads(matches[0])
                tool_calls = [{
                    "id": str(uuid.uuid4()),
                    "type": "tool_call",
                    "name": match_json.get("name", ""),
                    "args": match_json.get("args", {}),
                }]
                self.agent_queue_manager.publish(state["task_id"], AgentThought(
                    id=id,
                    task_id=state["task_id"],
                    event=QueueEvent.AGENT_THOUGHT,
                    thought=json.dumps(gathered.content),
                    message=messages_to_dict(state["messages"]),
                    message_token_count=input_token_count,
                    message_unit_price=input_price,
                    message_price_unit=unit,
                    answer="",
                    answer_token_count=output_token_count,
                    answer_unit_price=output_price,
                    answer_price_unit=unit,
                    total_token_count=total_token_count,
                    total_price=total_price,
                    latency=(time.perf_counter() - start_at),
                ))
                return {
                    "messages": [AIMessage(content="", tool_calls=tool_calls)],
                    "iteration_count": state["iteration_count"] + 1
                }
            except Exception as _:
                generation_type = "message"
                self.agent_queue_manager.publish(state["task_id"], AgentThought(
                    id=id,
                    task_id=state["task_id"],
                    event=QueueEvent.AGENT_MESSAGE,
                    thought=gathered.content,
                    message=messages_to_dict(state["messages"]),
                    answer=gathered.content,
                    latency=(time.perf_counter() - start_at),
                ))

        # 如果LLM直接生成answer则表示已经拿到了最终答案，推送一条空消息用于计算总token+总成本并停止监听
        if generation_type == "message":
            self.agent_queue_manager.publish(state["task_id"], AgentThought(
                id=id,
                task_id=state["task_id"],
                event=QueueEvent.AGENT_MESSAGE,
                thought="",
                message=messages_to_dict(state["messages"]),
                message_token_count=input_token_count,
                message_unit_price=input_price,
                message_price_unit=unit,
                answer="",
                answer_token_count=output_token_count,
                answer_unit_price=output_price,
                answer_price_unit=unit,
                total_token_count=total_token_count,
                total_price=total_price,
                latency=(time.perf_counter() - start_at),
            ))
            self.agent_queue_manager.publish(state["task_id"], AgentThought(
                id=uuid.uuid4(),
                task_id=state["task_id"],
                event=QueueEvent.AGENT_END,
            ))

        return {"messages": [gathered], "iteration_count": state["iteration_count"] + 1}

    def _tools_node(self, state: AgentState) -> AgentState:
        """重写工具节点，处理工具节点的`AI工具调用参数消息`与`工具消息转人类消息`"""
        # 调用父类的工具节点执行并获取结果
        super_agent_state = super()._tools_node(state)

        # 移除原始的AI工具调用参数消息，并创建新的ai消息
        tool_call_message = state["messages"][-1]
        remove_tool_call_message = RemoveMessage(id=tool_call_message.id)

        # 提取工具调用的第1条消息还原原始AI消息(ReACTAgent一次最多只有一个工具调用)
        tool_call_json = [{
            "name": tool_call_message.tool_calls[0].get("name", ""),
            "args": tool_call_message.tool_calls[0].get("args", {}),
        }]
        ai_message = AIMessage(content=f"```json\n{json.dumps(tool_call_json)}\n```")

        # 将ToolMessage转换成HumanMessage，提升LLM的兼容性
        tool_messages = super_agent_state["messages"]
        content = ""
        for tool_message in tool_messages:
            content += f"工具: {tool_message.name}\n执行结果: {tool_message.content}\n==========\n\n"
        human_message = HumanMessage(content=content)

        return {"messages": [remove_tool_call_message, ai_message, human_message]}
