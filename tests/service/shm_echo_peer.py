"""Native Rust/Python interoperability fixture; never initializes BAAS/device state.

The owner creates the agreed native resources, then launches this script with
``--shm-name BASE``. Business stream ``echo`` echoes JSON and binary packets.
"""
from __future__ import annotations

import argparse
import asyncio
import json
import sys
import time
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from service.transport.pipe_server import _HANDLERS  # noqa: E402
from service.transport.shm_server import SharedMemoryTransportServer  # noqa: E402


class EchoHandler:
    def __init__(self, context) -> None:
        pass

    async def handle(self, endpoint) -> None:
        # The first request chooses the number/type of messages that follow.
        plan = await endpoint.recv_json()
        if plan.get("loop_busy_seconds"):
            time.sleep(float(plan["loop_busy_seconds"]))  # Deliberate event-loop stall in stress tests.
        for item in plan.get("messages", []):
            if plan.get("consume_delay_seconds"):
                await asyncio.sleep(float(plan["consume_delay_seconds"]))
            if item == "json":
                await endpoint.send_json(await endpoint.recv_json())
            elif item == "bytes":
                await endpoint.send_bytes(await endpoint.recv_bytes())
            else:
                raise ValueError(f"Unsupported echo message type: {item}")


async def run(base: str, report_budget: bool = False) -> None:
    _HANDLERS["echo"] = EchoHandler
    # The production Rust manager accepts the four business channel names.
    # Alias one only in this fixture to exercise manager routing/lifecycle.
    _HANDLERS["provider"] = EchoHandler
    server = SharedMemoryTransportServer(base, SimpleNamespace())
    try:
        await server.start()
        await server.wait_closed()
    finally:
        await server.close()
    if report_budget:
        print(json.dumps({"inbound_peak_bytes": server._budget.peak_bytes,
                          "inbound_retained_bytes": server._budget.used_bytes}), flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--shm-name", required=True)
    parser.add_argument("--report-budget", action="store_true")
    options = parser.parse_args()
    asyncio.run(run(options.shm_name, options.report_budget))
