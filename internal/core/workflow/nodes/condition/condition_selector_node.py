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
@Time   : 2025/4/14 20:16
@Author : caixiaorong01@outlook.com
@File   : condition_selector_node.py
"""
from typing import Optional

from langchain_core.runnables import RunnableConfig

from internal.core.workflow.entities.workflow_entity import WorkflowState
from internal.core.workflow.nodes import BaseNode
from internal.core.workflow.nodes.condition import ConditionSelectNodeData


class ConditionSelectorNode(BaseNode):
    node_data: ConditionSelectNodeData

    def invoke(self,  state: WorkflowState, config: Optional[RunnableConfig] = None) -> str:
        pass