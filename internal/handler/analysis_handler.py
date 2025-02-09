#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2025/2/9 13:32
@Author : rxccai@gmail.com
@File   : analysis_handler.py.py
"""
from dataclasses import dataclass
from uuid import UUID

from flask_login import current_user, login_required
from injector import inject

from internal.service import AnalysisService
from pkg.response import success_json


@inject
@dataclass
class AnalysisHandler:
    """统计分析处理器"""
    analysis_service: AnalysisService

    @login_required
    def get_app_analysis(self, app_id: UUID):
        """根据传递的应用id获取应用的统计信息"""
        app_analysis = self.analysis_service.get_app_analysis(app_id, current_user)
        return success_json(app_analysis)
