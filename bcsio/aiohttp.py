import asyncio
import aiohttp
from typing import Mapping, Tuple

from . import abc as bc_abc


class BaseCampAPI(bc_abc.BaseCampAPI):

    def __init__(self, session: aiohttp.ClientSession, requester: str,
                 oauth_token: str, account: str, cache=None) -> None:
        self._session = session
        super().__init__(requester, oauth_token=oauth_token, account=account,
                         cache=cache)

    async def _request(self, method: str, url: str, headers: Mapping,
                       body: bytes = b'') -> Tuple[int, Mapping, bytes]:
        n = 0
        while True:
            try:
                async with self._session.request(method, url, headers=headers,
                                                 data=body) as resp:
                    return resp.status, resp.headers, await resp.read()
            except aiohttp.ServerDisconnectedError as e:
                n += 1
                if n > 10:
                    raise e
                print(f'server disconnected, sleeping for 1s and trying again')
                await self.sleep(1)

    async def sleep(self, seconds: float) -> None:
        await asyncio.sleep(seconds)
