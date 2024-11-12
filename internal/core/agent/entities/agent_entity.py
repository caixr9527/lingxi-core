#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2024/11/12 21:18
@Author : rxccai@gmail.com
@File   : agent_entity.py
"""
from langchain_core.language_models import BaseLanguageModel
from langchain_core.messages import AnyMessage
from langchain_core.pydantic_v1 import BaseModel, Field
from langchain_core.tools import BaseTool
from langgraph.graph import MessagesState

# Agent智能体系统预设提示词模板
AGENT_SYSTEM_PROMPT_TEMPLATE = """你是一个高度定制的智能体应用，旨在为用户提供准确、专业的内容生成和问题解答，请严格遵守以下规则：

1.**预设任务执行**
  - 你需要基于用户提供的预设提示(PRESET-PROMPT)，按照要求生成特定内容，确保输出符合用户的预期和指引；

2.**工具调用和参数生成**
  - 当任务需要时，你可以调用绑定的外部工具(如知识库检索、计算工具等)，并生成符合任务需求的调用参数，确保工具使用的准确性和高效性；

3.**历史对话和长期记忆**
  - 你可以参考`历史对话`记录，结合经过摘要提取的`长期记忆`，以提供更加个性化和上下文相关的回复，这将有助于在连续对话中保持一致性，并提供更加精确的反馈；

4.**外部知识库检索**
  - 如果用户的问题超出当前的知识范围或需要额外补充，你可以调用`recall_dataset(知识库检索工具)`以获取外部信息，确保答案的完整性和正确性；

5.**高效性和简洁性**
  - 保持对用户需求的精准理解和高效响应，提供简洁且有效的答案，避免冗长或无关信息；

<预设提示>
{preset_prompt}
</预设提示>

<长期记忆>
{long_term_memory}
</长期记忆>
"""


class AgentConfig(BaseModel):
    """智能体配置信息，涵盖：LLM大语言模型、预设prompt、关联插件、知识库、工作流、是否开启长期记忆等内容，后期可以随时扩展"""
    # 智能体使用的LLM
    llm: BaseLanguageModel

    # 智能体预设提示词
    system_prompt: str = AGENT_SYSTEM_PROMPT_TEMPLATE
    preset_prompt: str = ""  # 预设prompt，默认为空，该值由前端用户在编排的时候记录，并填充到system_prompt中

    # 智能体长期记忆是否开启
    enable_long_term_memory: bool = False  # 是否开启会话信息汇总/长期记忆

    # 智能体使用的工具列表
    tools: list[BaseTool] = Field(default_factory=list)


class AgentState(MessagesState):
    """智能体状态类"""
    history: list[AnyMessage]  # 短期记忆(历史记录)
    long_term_memory: str  # 长期记忆
