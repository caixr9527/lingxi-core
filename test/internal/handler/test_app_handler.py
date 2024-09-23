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

    @pytest.mark.parametrize("app_id,query",
                             [("9211086e-2120-4fec-8674-d17de1ca8c6a", None),
                              ("9211086e-2120-4fec-8674-d17de1ca8c6a", "你好，你是？")])
    def test_completion(self, app_id, query, client):
        resp = client.post(f"/apps/{app_id}/debug", json={"query": query})
        assert resp.status_code == 200
        if query is None:
            assert resp.json.get("code") == HttpCode.VALIDATE_ERROR
        else:
            assert resp.json.get("code") == HttpCode.SUCCESS
        print("响应内容:", resp.json)
