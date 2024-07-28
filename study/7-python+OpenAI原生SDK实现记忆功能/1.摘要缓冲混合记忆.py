#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2024/7/28 15:24
@Author : rxccai@gmail.com
@File   : 1.摘要缓冲混合记忆.py
"""
from typing import Any

import dotenv
from openai import OpenAI

dotenv.load_dotenv()


class ConversationSummaryBufferMemory:
    def __init__(self, summary: str = '', chat_histories: list = None, max_tokens: int = 300):
        self.summary = summary
        self.chat_histories = [] if chat_histories is None else chat_histories
        self.max_tokens = max_tokens
        self._client = OpenAI(base_url='https://api.moonshot.cn/v1')

    @classmethod
    def get_num_tokes(cls, query: str) -> int:
        return len(query)

    def save_content(self, human_query: str, ai_content: str) -> None:
        self.chat_histories.append({"human": human_query, "ai": ai_content})
        buffer_string = self.get_buffer_string()
        tokens = self.get_num_tokes(buffer_string)
        print("新摘要生成中")
        if tokens > self.max_tokens:
            first_chat = self.chat_histories[0]
            self.summary = self.summary_text(self.summary,
                                             f"Human:{first_chat.get('human')}\nAI:{first_chat.get('ai')}")
            print("新摘要生成成功:", self.summary)
            del self.chat_histories[0]

    def get_buffer_string(self) -> str:
        buffer: str = ""
        for chat in self.chat_histories:
            buffer += f"Human:{chat.get('huma')}\nAI:{chat.get('ai')}\n\n"
        return buffer.strip()

    def load_memory_variables(self) -> dict[str, Any]:
        buffer_string = self.get_buffer_string()
        return {"chat_history": f"摘要:{self.summary}\n\n历史信息:{buffer_string}\n"}

    def summary_text(self, origin_summary: str, new_line: str) -> str:
        prompt = f"""你是一个强大的聊天机器人，请根据用户提供的谈话内容，总结内容，并将其添加到先前提供的摘要中，返回一个新的摘要。

<example>
当前摘要: 人类会问人工智能对人工智能的看法。人工智能认为人工智能是一股向善的力量。

新的谈话内容：
Human: 为什么你认为人工智能是一股向善的力量？
AI: 因为人工智能将帮助人类充分发挥潜力。

新摘要: 人类会问人工智能对人工智能的看法。人工智能认为人工智能是一股向善的力量，因为它将帮助人类充分发挥潜力。
</example>

当前摘要: {origin_summary}

新的对话内容:
{new_line}
"""
        completion = self._client.chat.completions.create(
            model='moonshot-v1-8k',
            messages=[
                {"role": "user", "content": prompt},
            ],
        )
        return completion.choices[0].message.content


client = OpenAI(base_url='https://api.moonshot.cn/v1')
memory = ConversationSummaryBufferMemory("", [], 300)

while True:
    query = input('Human: ')
    if query == 'q':
        break
    memory_variables = memory.load_memory_variables()
    answer_prompt = (
        "你是一个强大的聊天机器人,请根据上下文和用户提问解决问题\n\n"
        f"{memory_variables.get('chat_history')}\n\n"
        f"用户的提问是:{query}"
    )
    response = client.chat.completions.create(
        model='moonshot-v1-8k',
        messages=[
            {"role": "user", "content": answer_prompt},
        ],
        stream=True
    )
    print("AI: ", flush=True, end="")
    ai_content = ""
    for chunk in response:
        content = chunk.choices[0].delta.content
        if content is None:
            break
        ai_content += content
        print(content, flush=True, end="")
    print("")
    memory.save_content(query, ai_content)
