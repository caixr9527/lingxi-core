#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2024/9/23 22:49
@Author : rxccai@gmail.com
@File   : test_builtin_tool_handler.py
"""
import pytest

from pkg.response import HttpCode


class TestBuiltinToolHandler:

    def test_get_categories(self, client):
        resp = client.get("/builtin-tools/categories")
        assert resp.status_code == 200
        assert resp.json.get("code") == HttpCode.SUCCESS
        assert len(resp.json.get("data")) > 0

    def test_get_builtin_tools(self, client):
        resp = client.get("/builtin-tools")
        assert resp.status_code == 200
        assert resp.json.get("code") == HttpCode.SUCCESS
        assert len(resp.json.get("data")) > 0

    @pytest.mark.parametrize(
        "provider_name,tool_name",
        [
            ("google", "google_serper"),
            ("google1", "google_serper"),
        ]
    )
    def test_get_provider_tool(self, provider_name, tool_name, client):
        resp = client.get(f"/builtin-tools/{provider_name}/tools/{tool_name}")
        assert resp.status_code == 200
        if provider_name == "google":
            assert resp.json.get("code") == HttpCode.SUCCESS
        else:
            assert resp.json.get("code") == HttpCode.NOT_FOUND

    @pytest.mark.parametrize("provider_name", ["google", "google1"])
    def test_get_provider_icon(self, provider_name, client):
        resp = client.get(f"/builtin-tools/{provider_name}/icon")
        assert resp.status_code == 200
        if provider_name == "google1":
            assert resp.json.get("code") == HttpCode.NOT_FOUND
