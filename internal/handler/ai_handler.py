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
@Time   : 2024/12/8 21:49
@Author : caixiaorong01@outlook.com
@File   : ai_handler.py
"""
from dataclasses import dataclass

from flask_login import login_required, current_user
from injector import inject

from internal.schema.ai_schema import OptimizePromptReq, GenerateSuggestedQuestionsReq
from internal.service import AIService
from pkg.response import validate_error_json, compact_generate_response, success_json


@inject
@dataclass
class AIHandler:
    ai_service: AIService

    @login_required
    def optimize_prompt(self):
        req = OptimizePromptReq()
        if not req.validate():
            return validate_error_json(req.errors)
        resp = self.ai_service.optimize_prompt(req.prompt.data)
        return compact_generate_response(resp)

    @login_required
    def generate_suggested_questions(self):
        req = GenerateSuggestedQuestionsReq()
        if not req.validate():
            return validate_error_json(req.errors)
        suggested_questions = self.ai_service.generate_suggested_questions_from_message_id(
            req.message_id.data,
            account=current_user)
        return success_json(suggested_questions)
