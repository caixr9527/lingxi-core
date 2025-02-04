#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2025/1/21 21:16
@Author : rxccai@gmail.com
@File   : model_entity.py
"""
from abc import ABC
from enum import Enum
from typing import Any, Optional

from langchain_core.language_models import BaseLanguageModel as LCBaseLanguageModel
from langchain_core.pydantic_v1 import BaseModel, Field


class DefaultModelParameterName(str, Enum):
    """默认的参数名字，一般是所有LLM都有的一些参数"""
    TEMPERATURE = "temperature"  # 温度
    TOP_P = "top_p"  # 核采样率
    PRESENCE_PENALTY = "presence_penalty"  # 存在惩罚
    FREQUENCY_PENALTY = "frequency_penalty"  # 频率惩罚
    MAX_COMPLETION_TOKENS = "max_completion_tokens"  # 要生成的内容的最大tokens数


class ModelType(str, Enum):
    """模型类型枚举"""
    CHAT = "chat"  # 聊天模型
    COMPLETION = "completion"  # 文本生成模型


class ModelParameterType(str, Enum):
    """模型参数类型"""
    FLOAT = "float"
    INT = "int"
    STRING = "string"
    BOOLEAN = "boolean"


class ModelParameterOption(BaseModel):
    """模型参数选项配置模型"""
    label: str  # 配置选项标签
    value: Any  # 配置选项对应的值


class ModelParameter(BaseModel):
    """模型参数实体信息"""
    name: str = ""  # 参数名字
    label: str = ""  # 参数标签
    type: ModelParameterType = ModelParameterType.STRING  # 参数的类型
    help: str = ""  # 帮助信息
    required: bool = False  # 是否必填
    default: Optional[Any] = None  # 默认参数值
    min: Optional[float] = None  # 最小值
    max: Optional[float] = None  # 最大值
    precision: int = 2  # 保留小数的位数
    options: list[ModelParameterOption] = Field(default_factory=list)  # 可选的参数配置


class ModelFeature(str, Enum):
    """模型特性，用于标记模型支持的特性信息，涵盖工具调用、智能体推理、图片输入"""
    TOOL_CALL = "tool_call"  # 工具调用
    AGENT_THOUGHT = "agent_thought"  # 是否支持智能体推理，一般要求参数量比较大，能回答通用型任务，如果不支持推理则会直接生成答案，而不进行中间步骤
    IMAGE_INPUT = "image_input"  # 图片输入，多模态大语言模型


class ModelEntity(BaseModel):
    """语言模型实体，记录模型的相关信息"""
    model_name: str = Field(default="", alias="model")  # 模型名字，使用model作为别名
    label: str = ""  # 模型标签
    model_type: ModelType = ModelType.CHAT  # 模型类型
    features: list[ModelFeature] = Field(default_factory=list)  # 模型特征信息
    context_window: int = 0  # 上下文窗口长度(输入+输出的总长度)
    max_output_tokens: int = 0  # 最大输出内容长度(输出)
    attributes: dict[str, Any] = Field(default_factory=dict)  # 模型固定属性字典
    parameters: list[ModelParameter] = Field(default_factory=list)  # 模型参数字段规则列表，用于记录模型的配置参数
    metadata: dict[str, Any] = Field(default_factory=dict)  # 模型元数据，用于存储模型的额外数据，例如价格、词表等等信息


class BaseLanguageModel(LCBaseLanguageModel, ABC):
    """基础语言模型"""
    features: list[ModelFeature] = Field(default_factory=list)  # 模型特性
    metadata: dict[str, Any] = Field(default_factory=dict)  # 模型元数据信息
