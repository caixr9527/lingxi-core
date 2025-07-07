#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2025/7/07 16:14
@Author : caixiaorong01@outlook.com
@File   : youdao_translate.py
"""
import hashlib
import time
import uuid
from typing import Type, Any

import requests
from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field

from internal.lib.helper import add_attribute


class YouDaoTranslateArgsSchema(BaseModel):
    q: str = Field(description="要翻译的文本")


class YouDaoTranslateTool(BaseTool):
    name: str = "youdao_translate"
    description: str = "根据输入的文字翻译成对应的语言"
    args_schema: Type[BaseModel] = YouDaoTranslateArgsSchema
    translate_type: str
    url: str
    app_key: str
    app_secret: str
    vocabId: str | None

    def _run(self, *args: Any, **kwargs: Any) -> Any:
        try:
            q = kwargs.get("q", "")
            if q == "":
                return "输入不能为空"
            if self.url is None or self.app_key is None or self.app_secret is None:
                return "工具参数配置错误,请检查参数配置是否正确"

            source_language = "auto"
            target_language = "zh-CHS"
            if self.translate_type is not None and self.translate_type != 'auto':
                source_language = self.translate_type.split(":")[0]
                target_language = self.translate_type.split(":")[1]
            data = {'from': source_language, 'to': target_language, 'signType': 'v3'}
            curtime = str(int(time.time()))
            data['curtime'] = curtime
            salt = str(uuid.uuid1())
            signStr = self.app_key + self.truncate(q) + salt + curtime + self.app_secret
            sign = self.encrypt(signStr)
            data['appKey'] = self.app_key
            data['q'] = q
            data['salt'] = salt
            data['sign'] = sign
            data['vocabId'] = '' if self.vocabId is None else self.vocabId

            response = self.do_request(data)
            contentType = response.headers['Content-Type']
            if response.status_code != 200:
                return f"{q} 请求结果异常: {response.status_code}"
            json_response = response.json()
            if json_response["errorCode"] != '0':
                return "请求结果失败"

            if contentType == "audio/mp3":
                pass
            else:
                return ",".join(json_response["translation"])
        except Exception as e:
            return f"获取{kwargs.get("q", "")} 信息失败"

    def encrypt(self, signStr):
        hash_algorithm = hashlib.sha256()
        hash_algorithm.update(signStr.encode('utf-8'))
        return hash_algorithm.hexdigest()

    def do_request(self, data):
        headers = {'Content-Type': 'application/x-www-form-urlencoded'}
        return requests.post(self.url, data=data, headers=headers)

    def truncate(self, q):
        size = len(q)
        return q if size <= 20 else q[0:10] + str(size) + q[size - 10:size]


@add_attribute("args_schema", YouDaoTranslateArgsSchema)
def youdao_translate(**kwargs) -> BaseTool:
    return YouDaoTranslateTool(**kwargs)
