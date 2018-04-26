import abc
from typing import Any,  Dict, Mapping, Tuple, Optional
import json

from . import sansio


class BaseCampAPI(abc.ABC):

    """Provide an idiomatic API for making calls to BaseCamp's API."""

    def __init__(self, app_name: str, oauth_token: str, account: str,
                 cache=None) -> None:
        self.app_name = app_name
        self.oauth_token = oauth_token
        self.account = account
        self._cache = cache
        # self.rate_limit: Optional[sansio.RateLimit] = None
        self.rate_limit = None

    @abc.abstractmethod
    async def _request(self, method: str, url: str, headers: Mapping,
                       body: bytes = b'') -> Tuple[int, Mapping, bytes]:
        """Make an HTTP request."""

    @abc.abstractmethod
    async def sleep(self, seconds: float) -> None:
        """Sleep for the specified number of seconds."""

    async def _make_request(self, method: str, url: str, url_vars: Dict,
                            data: Any) -> Tuple[bytes, Optional[str]]:
        """Construct and make an HTTP request."""
        url_vars.setdefault('account', self.account)
        filled_url = sansio.format_url(url, url_vars)
        request_headers = sansio.create_headers(self.app_name,
                                                oauth_token=self.oauth_token)
        cached = cacheable = False
        # Can't use None as a "no body" sentinel as it's a legitimate
        # JSON type.
        if data == b"":
            body = b""
            request_headers["content-length"] = "0"
            if method == "GET" and self._cache is not None:
                cacheable = True
                try:
                    etag, last_modified, data, more = self._cache[filled_url]
                    cached = True
                except KeyError:
                    pass
                else:
                    if etag is not None:
                        request_headers["if-none-match"] = etag
                    if last_modified is not None:
                        request_headers["if-modified-since"] = last_modified

        else:
            charset = "utf-8".upper()
            body = json.dumps(data).encode(charset)
            request_headers['Content-Type'] = \
                f"application/json; charset={charset}"
            request_headers['content-length'] = str(len(body))
        if self.rate_limit is not None:
            self.rate_limit.remaining -= 1
        response = await self._request(method, filled_url,
                                       request_headers, body)
        if response[0] == 429:
            sleep_time = int(response[1]['Retry-After']) + 1
            print(f'Hit rate limit, backing off for {sleep_time}')
            await self.sleep(sleep_time)
            return await self._make_request(method, url, url_vars, data)

        if not (response[0] == 304 and cached):
            data, self.rate_limit, more = sansio.decipher_response(*response)
            has_cache_details = ("etag" in response[1]
                                 or "last-modified" in response[1])
            if self._cache is not None and cacheable and has_cache_details:
                etag = response[1].get("etag")
                last_modified = response[1].get("last-modified")
                self._cache[filled_url] = etag, last_modified, data, more

        return data, more

    async def getitem(self, url: str, url_vars: Dict = {}) -> Any:
        """Send a GET request for a single item to the specified endpoint."""
        data, _ = await self._make_request("GET", url, url_vars, b"")
        return data

    async def getiter(self, url: str, url_vars: Dict = {}):
        """Return an async iterable for all items at a specified endpoint."""
        data, more = await self._make_request("GET", url, url_vars, b"")
        for item in data:
            yield item
        if more:
            # `yield from` is not supported in coroutines.
            async for item in self.getiter(more, url_vars):
                yield item

    async def post(self, url: str, url_vars: Dict = {}, *, data: Any) -> Any:
        data, _ = await self._make_request("POST", url, url_vars, data)
        return data

    async def patch(self, url: str, url_vars: Dict = {}, *,
                    data: Any) -> Any:
        data, _ = await self._make_request("PATCH", url, url_vars, data)
        return data

    async def put(self, url: str, url_vars: Dict = {}, *,
                  data: Any = b"") -> Any:
        data, _ = await self._make_request("PUT", url, url_vars, data)
        return data

    async def delete(self, url: str, url_vars: Dict = {}) -> None:
        await self._make_request("DELETE", url, url_vars, b"")
