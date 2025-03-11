#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2025/3/11 21:44
@Author : rxccai@gmail.com
@File   : wechat_handler.py
"""
from dataclasses import dataclass
from uuid import UUID

from injector import inject

from internal.service import WechatService


@inject
@dataclass
class WechatHandler:
    """微信公众号服务服务"""
    wechat_service: WechatService

    def wechat(self, app_id: UUID):
        """Agent微信API校验与消息推送"""
        return self.wechat_service.wechat(app_id)
