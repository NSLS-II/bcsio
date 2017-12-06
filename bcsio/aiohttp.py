import asyncio
import aiohttp
from typing import Mapping, Tuple

from . import abc as bc_abc


class BaseCampAPI(bc_abc.BaseCampAPI):

    def __init__(self, session: aiohttp.ClientSession, requester: str,
                 oauth_token: str, account: str) -> None:
        self._session = session
        super().__init__(requester, oauth_token=oauth_token, account=account)

    async def _request(self, method: str, url: str, headers: Mapping,
                       body: bytes = b'') -> Tuple[int, Mapping, bytes]:
        print(method, url, headers, body)
        async with self._session.request(method, url, headers=headers,
                                         data=body) as response:
            return response.status, response.headers, await response.read()

    async def sleep(self, seconds: float) -> None:
        await asyncio.sleep(seconds)
