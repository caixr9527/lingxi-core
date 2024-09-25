#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2024/9/25 23:45
@Author : rxccai@gmail.com
@File   : test_api_tool_handler.py
"""
import pytest

from pkg.response import HttpCode

openapi_schema_string = """{"server": "https://baidu.com", "description": "123", "paths": {"/location": {"get": {"description": "获取本地位置", "operationId":"xxx", "parameters":[{"name":"location", "in":"query", "description":"参数描述", "required":true, "type":"str"}]}}}}"""


class TestApiToolHandler:

    @pytest.mark.parametrize("openapi_schema", ["123", openapi_schema_string])
    def test_validate_openapi_schema(self, openapi_schema, client):
        resp = client.post("/api-tools/validate-openapi-schema", json={"openapi_schema": openapi_schema})
        assert resp.status_code == 200
        if openapi_schema == "123":
            assert resp.json.get("code") == HttpCode.VALIDATE_ERROR
        else:
            assert resp.json.get("code") == HttpCode.SUCCESS
