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
@Time   : 2025/4/28 21:35
@Author : rxccai@gmail.com
@File   : sms_service.py
"""
import logging
import os
import smtplib
from dataclasses import dataclass
from email.header import Header
from email.mime.text import MIMEText

from injector import inject

from internal.exception import FailException


@inject
@dataclass
class SmsService:

    def send_email(self, email: str, content: str, subject: str):

        try:
            smtp_server = os.getenv("SMTP_SERVER")
            port = int(os.getenv("SMTP_PORT"))
            sender_email = os.getenv("SENDER_EMAIL")
            password = os.getenv("SMTP_PASSWORD")

            msg = MIMEText(content, "plain", "utf-8")
            msg["To"] = Header(email, "utf-8")
            msg["Subject"] = Header(subject, "utf-8")

            with smtplib.SMTP_SSL(smtp_server, port) as server:
                server.login(sender_email, password)
                server.sendmail(sender_email, [email], msg.as_string())
                server.close()
        except Exception as e:
            logging.exception("邮件发送失败，错误信息: %(error)s", {"error": e})
            raise FailException("邮件发送失败。")
