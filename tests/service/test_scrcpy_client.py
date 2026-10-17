from __future__ import annotations

import asyncio
from types import SimpleNamespace

from service.remote import scrcpy


class _Device:
    serial = "127.0.0.1:5557"

    def forward_list(self):
        return iter(
            [
                SimpleNamespace(
                    serial="emulator-5554",
                    local="tcp:10461",
                    remote="tcp:8886",
                ),
                SimpleNamespace(
                    serial=self.serial,
                    local="tcp:6154",
                    remote="tcp:8886",
                ),
            ]
        )


def test_server_connection_uses_forward_for_selected_device(monkeypatch):
    connected_urls = []
    remote_socket = object()

    async def fake_connect(url, **kwargs):
        connected_urls.append(url)
        return remote_socket

    monkeypatch.setattr(scrcpy.websockets, "connect", fake_connect)
    client = scrcpy.ScrcpyClient(_Device())

    asyncio.run(client._ScrcpyClient__init_server_connection())

    assert connected_urls == ["ws://127.0.0.1:6154"]
    assert client.control_socket is remote_socket
