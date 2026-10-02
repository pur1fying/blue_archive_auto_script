from __future__ import annotations

from typing import Any

from service.transport import ChannelEndpoint

class RemoteChannelHandler:
    def __init__(self, service_context: Any) -> None:
        self.context = service_context

    async def handle(self, endpoint: ChannelEndpoint) -> None:
        proxy = None
        try:
            message = await endpoint.recv_json()
            endpoint.configure_binary_encryption(bool(message.get("decrypt", True)))
            config_id = message.get("config_id")
            client = await self.context.runtime.require_remote_(config_id)
            from service.remote import ScrcpyProxySession

            proxy = ScrcpyProxySession(client, None, encrypt_adb_to_ws=False)
            await proxy.run_endpoint(endpoint)
        finally:
            if proxy is not None:
                await proxy.close()
