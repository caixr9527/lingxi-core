#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2024/6/30 16:01
@Author : rxccai@gmail.com
@File   : test_app_handler.py
"""
import pytest

from pkg.response import HttpCode


class TestAppHandler:
    """app控制器测试类"""

    @pytest.mark.parametrize("query", [None, "你好,你是谁"])
    def test_completion(self, query, client):
        resp = client.post("/app/completion", json={"query": query})
        assert resp.status_code == 200
        if query is None:
            assert resp.json.get("code") == HttpCode.VALIDATE_ERROR
        else:
            assert resp.json.get("code") == HttpCode.SUCCESS
        print("响应内容:", resp.json)
