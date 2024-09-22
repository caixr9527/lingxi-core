#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2024/9/20 23:21
@Author : rxccai@gmail.com
@File   : wikipedia_search.py
"""

from langchain_community.tools.wikipedia.tool import WikipediaQueryInput, WikipediaQueryRun
from langchain_community.utilities import WikipediaAPIWrapper
from langchain_core.tools import BaseTool

from internal.lib.helper import add_attribute


@add_attribute("args_schema", WikipediaQueryInput)
def wikipedia_search(**kwargs) -> BaseTool:
    return WikipediaQueryRun(
        api_wrapper=WikipediaAPIWrapper(),
    )
