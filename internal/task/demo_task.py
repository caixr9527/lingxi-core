#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2024/10/16 22:30
@Author : rxccai@gmail.com
@File   : demo_task.py
"""
import logging
import time
from uuid import UUID

from celery import shared_task
from flask import current_app


@shared_task
def demo_task(id: UUID) -> str:
    logging.info("睡眠5s")
    time.sleep(5)
    logging.info(f"id的值：{id}")
    logging.info(f"配置信息：{current_app}")
    return "慕小课"
