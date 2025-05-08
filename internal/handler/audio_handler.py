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
@Time   : 2025/3/8 21:04
@Author : caixiaorong01@outlook.com
@File   : audio_handler.py
"""
from dataclasses import dataclass

from flask_login import login_required, current_user
from injector import inject

from internal.schema.audio_schema import AudioToTextReq, MessageToAudioReq
from internal.service import AudioService
from pkg.response import validate_error_json, success_json, compact_generate_response


@inject
@dataclass
class AudioHandler:
    """语音处理器"""
    audio_service: AudioService

    @login_required
    def audio_to_text(self):
        """将语音转换成文本"""
        req = AudioToTextReq()
        if not req.validate():
            return validate_error_json(req.errors)

        text = self.audio_service.audio_to_text(req.file.data)

        return success_json({"text": text})

    @login_required
    def message_to_audio(self):
        """将消息转换成流式输出音频"""
        req = MessageToAudioReq()
        if not req.validate():
            return validate_error_json(req.errors)

        response = self.audio_service.message_to_audio(req.message_id.data, current_user)

        return compact_generate_response(response)
