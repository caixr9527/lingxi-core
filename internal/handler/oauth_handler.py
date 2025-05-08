#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright [2025] [caixiaorong]
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""
@Time   : 2024/11/23 10:50
@Author : caixiaorong01@outlook.com
@File   : oauth_handler.py
"""
from dataclasses import dataclass

from injector import inject

from internal.schema.oauth_schema import AuthorizeReq, AuthorizeResp
from internal.service import OAuthService
from pkg.response import success_json, validate_error_json


@inject
@dataclass
class OAuthHandler:
    oauth_service: OAuthService

    def provider(self, provider_name: str):
        oauth = self.oauth_service.get_oauth_by_provider_name(provider_name)
        redirect_url = oauth.get_authorization_url()
        return success_json({"redirect_url": redirect_url})

    def authorize(self, provider_name: str):
        req = AuthorizeReq()
        if not req.validate():
            return validate_error_json(req.errors)

        credential = self.oauth_service.oauth_login(provider_name, req.code.data)
        return success_json(AuthorizeResp().dump(credential))
