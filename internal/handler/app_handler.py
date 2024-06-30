#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2024/6/28 20:28
@Author : rxccai@gmail.com
@File   : app_handler.py
"""
import os
import uuid
from dataclasses import dataclass

from flask import request
from injector import inject
from openai import OpenAI

from internal.exception import CustomException
from internal.schema.app_schema import CompletionReq
from internal.service import AppService
from pkg.response import success_json, validate_error_json, success_message


@inject
@dataclass
class AppHandler:
    app_service: AppService

    def create_app(self):
        """创建新的APP记录"""
        app = self.app_service.create_app()
        return success_message(f"应用创建成功,id为{app.id}")

    def get_app(self, id: uuid.UUID):
        app = self.app_service.get_app(id)
        return success_message(f"获取应用详情，名称为{app.name}")

    def update_app(self, id: uuid.UUID):
        app = self.app_service.update_app(id)
        return success_message(f"更新应用详情，名称为{app.name}")

    def delete_app(self, id: uuid.UUID):
        app = self.app_service.delete_app(id)
        return success_message(f"删除应用详情，名称为{app.name}")

    def completion(self):
        """聊天接口"""
        req = CompletionReq()
        if not req.validate():
            return validate_error_json(req.errors)
        # 1.提取从接口中获取的输入
        query = request.json.get("query")
        # 2.构建OpenAI客户端，发送请求
        client = OpenAI(base_url=os.getenv("OPENAI_BASE_URL"))
        # 3.返回前端
        completion = client.chat.completions.create(
            model="moonshot-v1-8k",
            messages=[
                {"role": "system", "content": "你是聊天机器人，请根据用户的输入回复信息"},
                {"role": "user", "content": query},
            ]
        )
        content = completion.choices[0].message.content
        return success_json({"content": content})

    def ping(self):
        raise CustomException(message="数据未找到")
        # return {"ping": "pong"}
