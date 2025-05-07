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
@Time   : 2025/1/23 22:24
@Author : caixiaorong01@outlook.com
@File   : language_model_handler.py.py
"""
import io
from dataclasses import dataclass

from flask import send_file
from flask_login import login_required
from injector import inject

from internal.service import LanguageModelService
from pkg.response import success_json


@inject
@dataclass
class LanguageModelHandler:
    """语言模型处理器"""
    language_model_service: LanguageModelService

    @login_required
    def get_language_models(self):
        """获取所有的语言模型提供商信息"""
        return success_json(self.language_model_service.get_language_models())

    @login_required
    def get_language_model(self, provider_name: str, model_name: str):
        """根据传递的提供商名字+模型名字获取模型详细信息"""
        return success_json(self.language_model_service.get_language_model(provider_name, model_name))

    def get_language_model_icon(self, provider_name: str):
        """根据传递的提供者名字获取指定提供商的icon图标"""
        icon, mimetype = self.language_model_service.get_language_model_icon(provider_name)
        return send_file(io.BytesIO(icon), mimetype)
