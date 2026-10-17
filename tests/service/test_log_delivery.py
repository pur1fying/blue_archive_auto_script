from __future__ import annotations

import asyncio
import queue
from datetime import datetime, timezone

from service.utils.broadcast import BroadcastChannel
from service.utils.logging import LogManager


def _record(message: str) -> dict:
    return {"time": datetime.now(timezone.utc), "level": 1, "message": message}


def test_log_bursts_preserve_live_delivery_and_history_across_scopes():
    async def scenario():
        manager = LogManager(asyncio.get_running_loop())
        received = await manager.subscribe()
        scope_count = 8
        records_per_scope = 257
        for scope in range(scope_count):
            source = queue.Queue()
            for index in range(records_per_scope):
                source.put_nowait(_record(f"{scope}:{index}"))
            manager.register_queue(source, f"config:{scope}")

        async def consume():
            return [await received.get() for _ in range(scope_count * records_per_scope)]

        consumer = asyncio.create_task(consume())
        await manager.start()
        await asyncio.wait_for(manager.stop(), timeout=5)
        entries = await asyncio.wait_for(consumer, timeout=1)

        assert entries == manager.get_history()
        for scope in range(scope_count):
            history = manager.get_history(f"config:{scope}")
            assert [entry["message"] for entry in history] == [
                f"{scope}:{index}" for index in range(records_per_scope)
            ]
        assert received.empty()

    asyncio.run(scenario())


def test_single_live_log_does_not_wait_for_batch_to_fill():
    async def scenario():
        manager = LogManager(asyncio.get_running_loop())
        source = queue.Queue()
        manager.register_queue(source)
        received = await manager.subscribe()
        await manager.start()
        try:
            source.put_nowait(_record("single live record"))
            entry = await asyncio.wait_for(received.get(), timeout=1)
            assert entry["message"] == "single live record"
            assert manager.get_history() == [entry]
        finally:
            await asyncio.wait_for(manager.stop(), timeout=1)

    asyncio.run(scenario())


def test_log_batch_stops_at_sentinel_without_consuming_later_records():
    async def scenario():
        manager = LogManager(asyncio.get_running_loop())
        source = queue.Queue()
        sentinel = object()
        source.put_nowait(_record("before stop"))
        source.put_nowait(sentinel)
        after = _record("after stop")
        source.put_nowait(after)

        await asyncio.wait_for(manager._pump_async(source, "global", sentinel), timeout=1)

        assert [entry["message"] for entry in manager.get_history()] == ["before stop"]
        assert source.get_nowait() is after

    asyncio.run(scenario())


def test_threadsafe_broadcast_delivers_in_order_and_unsubscribes():
    async def scenario():
        channel = BroadcastChannel(asyncio.get_running_loop())
        received = channel.subscribe()
        messages = [{"seq": index} for index in range(32)]

        def produce():
            for message in messages:
                channel.publish_threadsafe(message)

        await asyncio.to_thread(produce)
        delivered = [await asyncio.wait_for(received.get(), timeout=1) for _ in messages]
        assert delivered == messages
        channel.unsubscribe(received)
        await asyncio.to_thread(channel.publish_threadsafe, {"seq": 33})
        await asyncio.sleep(0)
        assert received.empty()

    asyncio.run(scenario())
