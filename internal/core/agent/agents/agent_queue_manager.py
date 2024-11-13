#!/usr/bin/env python
# -*- coding: utf-8 -*-
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

from internal.core.agent.entities.queue_entity import AgentQueueEvent, QueueEvent
from internal.entity.conversation_entity import InvokeFrom


class AgentQueueManager:
    q: Queue
    user_id: UUID
    task_id: UUID
    invoke_from: InvokeFrom
    redis_client: Redis

    def __init__(
            self,
            user_id: UUID,
            task_id: UUID,
            invoke_from: InvokeFrom,
            redis_client: Redis
    ) -> None:
        self.q = Queue()
        self.user_id = user_id
        self.task_id = task_id
        self.invoke_from = invoke_from
        self.redis_client = redis_client

        user_prefix = "account" if invoke_from in [InvokeFrom.WEB_APP, InvokeFrom.DEBUGGER] else "end-user"

        self.redis_client.setex(
            self.generate_task_belong_cache_key(task_id),
            1800,
            f"{user_prefix}-{str(user_id)}"
        )

    def listen(self) -> Generator:
        listen_timeout = 600
        start_time = time.time()
        last_ping_time = 0

        while True:
            try:
                item = self.q.get(timeout=1)
                if item is None:
                    break
                yield item
            except queue.Empty:
                continue
            finally:
                elapsed_time = time.time() - start_time
                if elapsed_time // 10 > last_ping_time:
                    self.publish(AgentQueueEvent(
                        id=uuid.uuid4(),
                        task_id=self.task_id,
                        event=QueueEvent.PING
                    ))
                    last_ping_time = elapsed_time // 10

                if elapsed_time >= listen_timeout:
                    self.publish(AgentQueueEvent(
                        id=uuid.uuid4(),
                        task_id=self.task_id,
                        event=QueueEvent.TIMEOUT
                    ))
                if self._is_stopped():
                    self.publish(AgentQueueEvent(
                        id=uuid.uuid4(),
                        task_id=self.task_id,
                        event=QueueEvent.STOP
                    ))

    def stop_listen(self) -> None:
        self.q.put(None)

    def publish(self, agent_queue_event: AgentQueueEvent) -> None:
        self.q.put(agent_queue_event)

        if agent_queue_event.event in [QueueEvent.STOP, QueueEvent.ERROR, QueueEvent.TIMEOUT, QueueEvent.AGENT_END]:
            self.stop_listen()

    def publish_error(self, error) -> None:
        self.publish(AgentQueueEvent(
            id=uuid.uuid4(),
            task_id=self.task_id,
            event=QueueEvent.ERROR,
            observation=str(error),
        ))

    def _is_stopped(self) -> bool:
        task_stopped_cache_key = self.generate_task_stopped_cache_key(self.task_id)
        result = self.redis_client.get(task_stopped_cache_key)
        if result is not None:
            return True
        return False

    @classmethod
    def generate_task_belong_cache_key(cls, task_id: UUID) -> str:
        return f"generate_task_belong:{str(task_id)}"

    @classmethod
    def generate_task_stopped_cache_key(cls, task_id: UUID) -> str:
        return f"generate_task_stopped:{str(task_id)}"
