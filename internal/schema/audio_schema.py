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
@Time   : 2025/3/8 21:02
@Author : rxccai@gmail.com
@File   : audio_schema.py
"""
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired, FileSize, FileAllowed
from wtforms.fields import StringField
from wtforms.validators import DataRequired


class AudioToTextReq(FlaskForm):
    """语音转文本请求结构"""
    file = FileField("file", validators=[
        FileRequired(message="转换音频文件不能为空"),
        FileSize(max_size=25 * 1024 * 1024, message="音频文件不能超过25MB"),
        FileAllowed(["webm", "wav"], message="请上传正确的音频文件"),
    ])


class MessageToAudioReq(FlaskForm):
    """消息转流式事件语音请求结构"""
    message_id = StringField("message_id", validators=[
        DataRequired(message="消息id不能为空"),
    ])
