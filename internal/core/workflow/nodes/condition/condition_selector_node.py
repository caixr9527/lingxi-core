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

from internal.core.workflow.entities.variable_entity import ConditionType
from internal.core.workflow.entities.workflow_entity import WorkflowState
from internal.core.workflow.nodes import BaseNode
from internal.core.workflow.nodes.condition import ConditionSelectNodeData
from internal.core.workflow.utils.helper import extract_variables_from_state
import rule_engine


class ConditionSelectorNode(BaseNode):
    node_data: ConditionSelectNodeData

    def invoke(self, state: WorkflowState, config: Optional[RunnableConfig] = None) -> str:
        inputs_dict = extract_variables_from_state(self.node_data.inputs, state)
        # 按照优先级排序
        self.node_data.classes.sort(key=lambda x: x.priority)
        node_flag = None
        for _, class_config_group in self.node_data.classes[len(self.node_data.classes) - 1]:
            condition_group = class_config_group.condition_group
            if len(condition_group) == 1:
                condition = condition_group[0]
                rule = f"{condition.variable} {condition.condition_type} {condition.parameter}"
                match_dict = {
                    condition.variable: inputs_dict[condition.variable],
                }
                if rule_engine.Rule(rule).matches(match_dict):
                    node_flag = class_config_group.source_handle_id
                    break
            else:
                rules = []
                match_dict = {}
                for condition in condition_group:
                    if (
                            condition.condition_type == ConditionType.STARTS_WITH.value
                            or condition.condition_type == ConditionType.ENDS_WITH.value
                    ):
                        rule_exper = f'{condition.variable}.{condition.condition_type}("{condition.parameter}")'
                    elif condition.condition_type == ConditionType.EMPTY.value:
                        rule_exper = f"{condition.variable} == null"
                    elif condition.condition_type == ConditionType.NOT_EMPTY.value:
                        rule_exper = f"{condition.variable} != null"
                    else:
                        rule_exper = f"{condition.variable} {condition.condition_type} {condition.parameter}"

                    rules.append(rule_exper+" ")
                    match_dict[condition.variable] = inputs_dict[condition.variable]

                rule = class_config_group.logical_type.join(rules)
                if rule_engine.Rule(rule).matches(match_dict):
                    node_flag = class_config_group.source_handle_id
                    break

        if node_flag is not None:
            return f"cn_source_handle_{node_flag}"
        return f"cn_source_handle_{self.node_data.classes[-1].source_handle_id}"


# if __name__ == '__main__':
#     print(rule_engine.Rule('name.ends_with(".png")').matches({"name": "xxx.png"}))
#     print(rule_engine.Rule('name.starts_with("xxx")').matches({"name": "xxx.png"}))
#     print(rule_engine.Rule('name in ["xxx.png"]').matches({"name": "xxx.png"}))
#     print(rule_engine.Rule('name not in ["xxx.png"]').matches({"name": "xxx.png"}))
#     print(rule_engine.Rule('name == null').matches({"name": "xxx.png"}))
#     print(rule_engine.Rule('name == null').matches({"name": None}))
