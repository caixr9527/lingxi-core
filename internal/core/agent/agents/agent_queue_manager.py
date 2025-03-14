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
@Time   : 2024/11/13 21:45
@Author : rxccai@gmail.com
@File   : agent_queue_manager.py
"""
import queue
import time
import uuid
from queue import Queue
from typing import Generator
from uuid import UUID

from redis import Redis

from internal.core.agent.entities.queue_entity import AgentThought, QueueEvent
from internal.entity.conversation_entity import InvokeFrom


class AgentQueueManager:
    user_id: UUID
    invoke_from: InvokeFrom
    redis_client: Redis
    _queues: dict[str, Queue]

    def __init__(
            self,
            user_id: UUID,
            invoke_from: InvokeFrom,
    ) -> None:
        self.user_id = user_id
        self.invoke_from = invoke_from
        self._queues = {}

        from app.http.module import injector
        self.redis_client = injector.get(Redis)

    def listen(self, task_id: UUID) -> Generator:
        listen_timeout = 60 * 2.5
        start_time = time.time()
        last_ping_time = 0
        first_ping_time = 0

        while True:
            try:
                item = self.queue(task_id).get(timeout=1)
                if item is None:
                    break
                if item.event not in [QueueEvent.PING]:
                    first_ping_time = 0
                yield item
            except queue.Empty:
                continue
            finally:
                elapsed_time = time.time() - start_time
                if elapsed_time // 10 > last_ping_time:
                    self.publish(task_id, AgentThought(
                        id=uuid.uuid4(),
                        task_id=task_id,
                        event=QueueEvent.PING
                    ))
                    last_ping_time = elapsed_time // 10
                    if first_ping_time == 0:
                        first_ping_time = time.time()

                if first_ping_time != 0 and time.time() - first_ping_time >= listen_timeout:
                    self.publish(task_id, AgentThought(
                        id=uuid.uuid4(),
                        task_id=task_id,
                        event=QueueEvent.TIMEOUT
                    ))
                    first_ping_time = 0
                if self._is_stopped(task_id):
                    self.publish(task_id, AgentThought(
                        id=uuid.uuid4(),
                        task_id=task_id,
                        event=QueueEvent.STOP
                    ))

    def stop_listen(self, task_id: UUID) -> None:
        self.queue(task_id).put(None)

    def publish(self, task_id: UUID, agent_though: AgentThought) -> None:
        self.queue(task_id).put(agent_though)

        if agent_though.event in [QueueEvent.STOP, QueueEvent.ERROR, QueueEvent.TIMEOUT, QueueEvent.AGENT_END]:
            self.stop_listen(task_id)

    def publish_error(self, task_id: UUID, error) -> None:
        self.publish(task_id, AgentThought(
            id=uuid.uuid4(),
            task_id=task_id,
            event=QueueEvent.ERROR,
            observation=str(error),
        ))

    def _is_stopped(self, task_id: UUID) -> bool:
        task_stopped_cache_key = self.generate_task_stopped_cache_key(task_id)
        result = self.redis_client.get(task_stopped_cache_key)
        if result is not None:
            return True
        return False

    def queue(self, task_id: UUID) -> Queue:
        # 从队列字典中获取对应的任务队列信息
        q = self._queues.get(str(task_id))
        if not q:
            user_prefix = "account" if self.invoke_from in [InvokeFrom.WEB_APP, InvokeFrom.DEBUGGER,
                                                            InvokeFrom.ASSISTANT_AGENT] else "end-user"

            self.redis_client.setex(
                self.generate_task_belong_cache_key(task_id),
                1800,
                f"{user_prefix}-{str(self.user_id)}"
            )

            q = Queue()
            self._queues[str(task_id)] = q
        return q

    @classmethod
    def set_stop_flag(cls, task_id: UUID, invoke_from: InvokeFrom, user_id: UUID) -> None:
        """根据传递的任务id+调用来源停止某次会话"""
        # 获取redis_client客户端
        from app.http.module import injector
        redis_client = injector.get(Redis)

        # 获取当前任务的缓存键，如果任务没执行，则不需要停止
        result = redis_client.get(cls.generate_task_belong_cache_key(task_id))
        if not result:
            return

        # 计算对应缓存键的结果
        user_prefix = "account" if invoke_from in [InvokeFrom.WEB_APP, InvokeFrom.DEBUGGER,
                                                   InvokeFrom.ASSISTANT_AGENT] else "end-user"
        if result.decode("utf-8") != f"{user_prefix}-{str(user_id)}":
            return

        # 生成停止键标识
        stopped_cache_key = cls.generate_task_stopped_cache_key(task_id)
        redis_client.setex(stopped_cache_key, 600, 1)

    @classmethod
    def generate_task_belong_cache_key(cls, task_id: UUID) -> str:
        return f"generate_task_belong:{str(task_id)}"

    @classmethod
    def generate_task_stopped_cache_key(cls, task_id: UUID) -> str:
        return f"generate_task_stopped:{str(task_id)}"
