#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2024/8/27 21:55
@Author : rxccai@gmail.com
@File   : 1.递归字符文本分割器示例.py
"""
from langchain_community.document_loaders import UnstructuredMarkdownLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

loader = UnstructuredMarkdownLoader("./项目API文档.md")
documents = loader.load()

text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=500,
    chunk_overlap=50,
    add_start_index=True,
)
chunks = text_splitter.split_documents(documents)

for chunk in chunks:
    print(f"块大小:{len(chunk.page_content)}, 块元数据:{chunk.metadata}")
