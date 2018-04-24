import re
import urllib
from typing import Any,  Dict, Mapping, Tuple, Optional
import cgi
import json
import uritemplate
import http

from . import (RateLimit, BaseCampBroken, RateLimitExceeded, BadRequest,
               RedirectionException, InvalidField, HTTPException)


def _parse_content_type(content_type: Optional[str]) -> Tuple[Optional[str], str]:
    """Tease out the content-type and character encoding.

    A default character encoding of UTF-8 is used, so the content-type
    must be used to determine if any decoding is necessary to begin
    with.
    """
    if not content_type:
        return None, "utf-8"
    else:
        type_, parameters = cgi.parse_header(content_type)
        encoding = parameters.get("charset", "utf-8")
        return type_, encoding


def _decode_body(content_type: Optional[str], body: bytes,
                 *, strict: bool = False) -> Any:
    """Decode an HTTP body based on the specified content type.

    If 'strict' is true, then raise ValueError if the content type
    is not recognized. Otherwise simply returned the body as a decoded
    string.
    """
    type_, encoding = _parse_content_type(content_type)
    if not len(body) or not content_type:
        return None
    decoded_body = body.decode(encoding)
    if type_ == "application/json":
        return json.loads(decoded_body)
    elif type_ == "application/x-www-form-urlencoded":
        return json.loads(urllib.parse.parse_qs(decoded_body)["payload"][0])
    elif strict:
        raise ValueError(f"unrecognized content type: {type_!r}")
    return decoded_body


_link_re = re.compile(r'\<(?P<uri>[^>]+)\>;\s*'
                      r'(?P<param_type>\w+)="(?P<param_value>\w+)"(,\s*)?')


def _next_link(link: Optional[str]) -> Optional[str]:
    # https://developer.github.com/v3/#pagination
    # https://tools.ietf.org/html/rfc5988
    if link is None:
        return None
    for match in _link_re.finditer(link):
        if match.group("param_type") == "rel":
            if match.group("param_value") == "next":
                return match.group("uri")
    else:
        return None


DOMAIN = "https://3.basecampapi.com/{account}/"


def format_url(url: str, url_vars: Mapping[str, Any]) -> str:
    """Construct a URL for the BaseCamp API.

    The URL may be absolute or relative. In the latter case the appropriate
    domain will be added. This is to help when copying the relative URL directly
    from the BaseCamp developer documentation.

    The dict provided in url_vars is used in URI template formatting.
    """
    # Works even if 'url' is fully-qualified.
    url = urllib.parse.urljoin(DOMAIN, url)
    expanded_url: str = uritemplate.expand(url, var_dict=url_vars)
    return expanded_url


def create_headers(app_name: str, oauth_token: str) -> Dict[str, str]:
    """Create a dict representing BaseCamp-specific header fields.

    app_name must be of the form

       App-name (your@email.com)
       App-name (https://your.app.url.com)


    """
    # https://github.com/basecamp/bc3-api#identifying-your-application
    # https://github.com/basecamp/api/blob/master/sections/authentication.md#oauth-2-from-scratch
    headers = {"User-Agent": app_name}
    headers["Authorization"] = f"Bearer {oauth_token}"
    return headers


def decipher_response(status_code: int, headers: Mapping,
                      body: bytes) -> Tuple[Any, RateLimit, Optional[str]]:
    """Decipher an HTTP response for a GitHub API request.

    The mapping providing the headers is expected to support lowercase keys.

    The parameters of this function correspond to the three main parts
    of an HTTP response: the status code, headers, and body. Assuming
    no errors which lead to an exception being raised, a 3-item tuple
    is returned. The first item is the decoded body (typically a JSON
    object, but possibly None or a string depending on the content
    type of the body). The second item is an instance of RateLimit
    based on what the response specified.

    The last item of the tuple is the URL where to request the next
    part of results. If there are no more results then None is
    returned. Do be aware that the URL can be a URI template and so
    may need to be expanded.

    If the status code is anything other than 200, 201, or 204, then
    an HTTPException is raised.
    """
    data = _decode_body(headers.get("content-type"), body)
    if status_code in {200, 201, 204}:
        return data, None, _next_link(headers.get('link'))
    else:
        try:
            message = data["message"]
        except (TypeError, KeyError):
            message = None
        exc_type: Type[HTTPException]
        if status_code >= 500:
            exc_type = BaseCampBroken
        elif status_code >= 400:
            exc_type = BadRequest
            if status_code == 403:
                rate_limit = RateLimit.from_http(headers)
                if not rate_limit.remaining:
                    raise RateLimitExceeded(rate_limit, message)
            elif status_code == 422:
                errors = data["errors"]
                fields = ", ".join(repr(e["field"]) for e in errors)
                message = f"{message} for {fields}"
                raise InvalidField(errors, message)
        elif status_code >= 300:
            exc_type = RedirectionException
        else:
            exc_type = HTTPException
        status_code_enum = http.HTTPStatus(status_code)
        args: Tuple
        if message:
            args = status_code_enum, message
        else:
            args = status_code_enum,
        raise exc_type(*args)
