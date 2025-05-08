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
@Time   : 2025/3/8 21:05
@Author : caixiaorong01@outlook.com
@File   : audio_service.py
"""
import base64
import json
import logging
import os
from dataclasses import dataclass
from io import BytesIO
from typing import Generator, Union
from uuid import UUID

from injector import inject
from openai import OpenAI
from werkzeug.datastructures import FileStorage

from internal.exception import NotFoundException, FailException
from internal.model import Account, Message, App, AppConfig, AppConfigVersion
from pkg.sqlalchemy import SQLAlchemy
from .app_service import AppService
from .base_service import BaseService
from ..entity.app_entity import AppStatus
from ..entity.conversation_entity import InvokeFrom


@inject
@dataclass
class AudioService(BaseService):
    """语音服务，涵盖语音转文本、消息流式输出语音"""
    db: SQLAlchemy
    app_service: AppService

    def audio_to_text(self, audio: FileStorage) -> str:
        """将传递的语音转换成文本"""
        # 提取音频文件，并将音频文件转换成FileContent类型
        file_content = audio.stream.read()
        audio_file = BytesIO(file_content)
        audio_file.name = "recording.wav"

        # 创建OpenAI客户端，并调用whisper服务将音频转换成文字
        client = self._get_openai_client()
        transcription = client.audio.transcriptions.create(
            model="whisper-1",
            file=audio_file,
        )

        # 返回识别的文字内容
        return transcription.text

    def message_to_audio(self, message_id: UUID, account: Account) -> Generator:
        """将消息转换成流式时间输出语音"""
        # 根据传递的消息id获取消息并校验权限
        message = self.get(Message, message_id)
        if not message or message.is_deleted or message.answer.strip() == "" or message.created_by != account.id:
            raise NotFoundException("该消息不存在，请核实后重试")

        # 校验消息归属的会话状态是否正常
        conversation = message.conversation
        if conversation is None or conversation.is_deleted or conversation.created_by != account.id:
            raise NotFoundException("该消息会话不存在，请核实后重试")

        # 定义文本转语音启动配置、音色，默认为开启+echo音色
        enable = True
        voice = "echo"

        # 根据会话信息获取会话归属的应用
        if message.invoke_from in [InvokeFrom.WEB_APP, InvokeFrom.DEBUGGER]:
            app = self.get(App, conversation.app_id)
            if not app:
                raise NotFoundException("该消息会话归属应用不存在或校验失败，请核实后重试")
            if message.invoke_from == InvokeFrom.DEBUGGER is True and app.account_id != account.id:
                raise NotFoundException("该消息会话归属的应用不存在或校验失败，请核实后重试")
            if message.invoke_from == InvokeFrom.WEB_APP is False and app.status != AppStatus.PUBLISHED:
                raise NotFoundException("该消息会话归属的应用未发布，请核实后重试")

            app_config: Union[AppConfig, AppConfigVersion] = (
                app.draft_app_config
                if message.invoke_from == InvokeFrom.DEBUGGER
                else app.app_config
            )
            text_to_speech = app_config.text_to_speech
            enable = text_to_speech.get("enable", False)
            voice = text_to_speech.get("voice", "echo")
        elif message.invoke_from == InvokeFrom.SERVICE_API:
            raise NotFoundException("开放API消息不支持文本转语音服务")

        # 根据状态获取不同的配置并判断是否开启文字转语音
        if enable is False:
            raise FailException("该应用未开启文字转语音功能，请核实后重试")

        # 调用tts服务将消息answer转换成流式事件输出语音
        try:
            client = self._get_openai_client()
            response = client.audio.speech.with_streaming_response.create(
                model="tts-1",
                voice=voice,
                response_format="mp3",
                input=message.answer.strip(),
            )
        except Exception as error:
            logging.error("文字转语音失败: %(error)s", {"error": error}, exc_info=True)
            raise FailException("文字转语音失败，请稍后重试")

        # 定义内部函数实现流式事件输出
        def tts() -> Generator:
            """内部函数，从response中获取音频流式事件输出数据"""
            common_data = {
                "conversation_id": str(conversation.id),
                "message_id": str(message.id),
                "audio": "",
            }
            for chunk in response.__enter__().iter_bytes(1024):
                data = {**common_data, "audio": base64.b64encode(chunk).decode("utf-8")}
                yield f"event: tts_message\ndata: {json.dumps(data)}\n\n"
            yield f"event: tts_end\ndata: {json.dumps(common_data)}\n\n"

        # 调用tts函数流式事件输出语音数据
        return tts()

    @classmethod
    def _get_openai_client(cls) -> OpenAI:
        """获取OpenAI客户端"""
        return OpenAI(
            api_key=os.environ.get("OPENAI_API_KEY"),
            base_url=os.environ.get("OPENAI_API_BASE"),
        )
