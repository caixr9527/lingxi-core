#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2024/6/28 20:28
@Author : rxccai@gmail.com
@File   : app_handler.py
"""
import uuid
from dataclasses import dataclass

from injector import inject
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

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

    def debug(self, app_id: uuid.UUID):
        """聊天接口"""
        req = CompletionReq()
        if not req.validate():
            return validate_error_json(req.errors)
        # 1.提取从接口中获取的输入
        prompt = ChatPromptTemplate.from_template("{query}")
        # 2.构建OpenAI客户端，发送请求
        llm = ChatOpenAI(model="moonshot-v1-8k")
        # 3.返回前端
        parser = StrOutputParser()
        chain = prompt | llm | parser
        content = chain.invoke({"query": req.query.data})
        return success_json({"content": content})

    def ping(self):
        raise CustomException(message="数据未找到")
        # return {"ping": "pong"}
