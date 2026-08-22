from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from service.transport.framing import HEADER, KIND_JSON, encode_json  # noqa: E402


async def read_json(reader: asyncio.StreamReader) -> dict:
    header = await reader.readexactly(HEADER.size)
    _, _, kind, length = HEADER.unpack(header)
    payload = await reader.readexactly(length)
    if kind != KIND_JSON:
        raise RuntimeError(f"Expected JSON frame, received kind={kind}")
    return json.loads(payload)


async def run(pipe_name: str) -> None:
    loop = asyncio.get_running_loop()
    reader = asyncio.StreamReader()
    protocol = asyncio.StreamReaderProtocol(reader)
    transport, _ = await loop.create_pipe_connection(lambda: protocol, pipe_name)
    writer = asyncio.StreamWriter(transport, protocol, reader, loop)
    try:
        writer.write(encode_json({"type": "open", "channel": "provider", "name": "live-smoke"}))
        await writer.drain()
        opened = await asyncio.wait_for(read_json(reader), timeout=5)
        if opened != {"type": "open_ok", "channel": "provider"}:
            raise RuntimeError(f"Unexpected open response: {opened}")

        initial_types = {(await asyncio.wait_for(read_json(reader), timeout=5)).get("type") for _ in range(2)}
        if initial_types != {"logs_full", "status"}:
            raise RuntimeError(f"Unexpected provider initialization: {initial_types}")

        writer.write(encode_json({"type": "status_request"}))
        await writer.drain()
        for _ in range(4):
            response = await asyncio.wait_for(read_json(reader), timeout=5)
            if response.get("type") == "status" and isinstance(response.get("status"), dict):
                print("pipe provider smoke passed")
                return
        raise RuntimeError("Provider did not return a status response")
    finally:
        writer.close()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("pipe_name")
    args = parser.parse_args()
    asyncio.run(run(args.pipe_name))


if __name__ == "__main__":
    main()
