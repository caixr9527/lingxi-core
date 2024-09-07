#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2024/9/7 13:34
@Author : rxccai@gmail.com
@File   : 02. LLM绑定天气预报与谷歌实时搜索.py
"""
import json
import os
from typing import Type, Any

import dotenv
import requests
from langchain_community.tools import GoogleSerperRun
from langchain_community.utilities import GoogleSerperAPIWrapper
from langchain_core.messages import ToolMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.pydantic_v1 import Field, BaseModel
from langchain_core.runnables import RunnablePassthrough
from langchain_core.tools import BaseTool
from langchain_openai import ChatOpenAI

dotenv.load_dotenv()


class GaodeWeatherArgsSchema(BaseModel):
    city: str = Field(description="需要查询天气预报的目标城市，例如：广州")


class GoogleSerperArgsSchema(BaseModel):
    query: str = Field(description="执行谷歌搜索的查询语句")


class GaodeWeatherTool(BaseTool):
    """根据传入的城市名查询天气"""
    name = "gaode_weather"
    description = "当你想询问天气或与天气相关的问题时的工具。"
    args_schema: Type[BaseModel] = GaodeWeatherArgsSchema

    def _run(self, *args: Any, **kwargs: Any) -> str:
        """运行工具获取对应城市的天气预报"""
        try:
            # 1.获取高德API秘钥，如果没有则抛出错误
            gaode_api_key = os.getenv("GAODE_API_KEY")
            if not gaode_api_key:
                return f"高德开放平台API秘钥未配置"

            # 2.提取传递的城市名字并查询行政编码
            city = kwargs.get("city", "")
            session = requests.session()
            api_domain = "https://restapi.amap.com/v3"
            city_response = session.request(
                method="GET",
                url=f"{api_domain}/config/district?keywords={city}&subdistrict=0&extensions=all&key={gaode_api_key}",
                headers={"Content-Type": "application/json; charset=utf-8"},
            )
            city_response.raise_for_status()
            city_data = city_response.json()

            # 3.提取行政编码调用天气预报查询接口
            if city_data.get("info") == "OK":
                if len(city_data.get("districts")) > 0:
                    ad_code = city_data["districts"][0]["adcode"]

                    weather_response = session.request(
                        method="GET",
                        url=f"{api_domain}/weather/weatherInfo?city={ad_code}&extensions=all&key={gaode_api_key}&output=json",
                        headers={"Content-Type": "application/json; charset=utf-8"},
                    )
                    weather_response.raise_for_status()
                    weather_data = weather_response.json()
                    if weather_data.get("info") == "OK":
                        return json.dumps(weather_data)

            session.close()
            return f"获取{kwargs.get('city')}天气预报信息失败"
            # 4.整合天气预报信息并返回
        except Exception as e:
            return f"获取{kwargs.get('city')}天气预报信息失败"


# 1.定义工具列表
gaode_weather = GaodeWeatherTool()
google_serper = GoogleSerperRun(
    name="google_serper",
    description=(
        "一个低成本的谷歌搜索API。"
        "当你需要回答有关时事的问题时，可以调用该工具。"
        "该工具的输入是搜索查询语句。"
    ),
    args_schema=GoogleSerperArgsSchema,
    api_wrapper=GoogleSerperAPIWrapper(),
)
tool_dict = {
    gaode_weather.name: gaode_weather,
    google_serper.name: google_serper,
}
tools = [tool for tool in tool_dict.values()]

# 2.创建Prompt
prompt = ChatPromptTemplate.from_messages([
    ("system", "你是由OpenAI开发的聊天机器人，可以帮助用户回答问题，必要时刻请调用工具帮助用户解答"),
    ("human", "{query}"),
])

# 3.创建大语言模型并绑定工具
llm = ChatOpenAI(model="gpt-3.5-turbo-16k", temperature=0)
llm_with_tool = llm.bind_tools(tools=tools)

# 4.创建链应用
chain = {"query": RunnablePassthrough()} | prompt | llm_with_tool

# 5.解析输出
query = "广州现在天气怎样，有什么适合穿的衣服呢"
resp = chain.invoke(query)
tool_calls = resp.tool_calls

# 6.判断是工具调用还是正常输出结果
if len(tool_calls) <= 0:
    print("生成内容:", resp.content)
else:
    # 7.将历史的系统消息、人类消息、AI消息组合
    messages = prompt.invoke(query).to_messages()
    messages.append(resp)

    # 8.循环遍历所有工具调用信息
    for tool_call in tool_calls:
        tool = tool_dict.get(tool_call.get("name"))
        print("正在执行工具: ", tool.name)
        id = tool_call.get("id")
        content = tool.invoke(tool_call.get("args"))
        print("工具输出: ", content)
        messages.append(ToolMessage(
            content=content,
            tool_call_id=id,
        ))
    print("输出内容: ", llm.invoke(messages))
