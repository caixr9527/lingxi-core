#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2024/11/12 21:18
@Author : rxccai@gmail.com
@File   : queue_entity.py
"""
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, Field


class QueueEvent(str, Enum):
    """队列事件类型枚举"""
    LONG_TERM_MEMORY_RECALL = "long_term_memory_recall"  # 长期记忆召回
    AGENT_THOUGHT = "agent_thought"  # 智能体推理
    AGENT_MESSAGE = "agent_message"  # 智能体消息
    AGENT_ACTION = "agent_action"  # 智能体动作
    DATASET_RETRIEVAL = "dataset_retrieval"  # 知识库检索
    AGENT_END = "agent_end"  # 智能体结束
    PING = "ping"  # Ping测试
    STOP = "stop"  # 停止标识
    ERROR = "error"  # 出错


class AgentQueueEvent(BaseModel):
    """智能体队列事件模型"""
    id: UUID  # 事件对应的id
    task_id: UUID  # 事件对应的任务id
    event: QueueEvent  # 事件类型
    thought: str = ""
    observation: str = ""
    tool: str = ""
    tool_input: dict = Field(default_factory=dict)
    message: list[tuple[str, str]] = Field(default_factory=list)
    message_token_count: int = 0
    answer: str = ""
    answer_token_count: int = 0
