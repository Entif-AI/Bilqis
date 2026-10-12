"""Bounded HTTP to an explicitly selected operator-owned loopback service."""
import json
import urllib.parse
import urllib.request
from .semantics import canonical


def encode_body(body, preserve_order=False):
    if preserve_order:
        return json.dumps(body,separators=(',',':'),ensure_ascii=True,allow_nan=False).encode()
    return canonical(body)


def local_bytes(endpoint, expected_path, body=None, *, preserve_order=False):
    u=urllib.parse.urlparse(endpoint)
    if (u.scheme!='http' or u.hostname not in ('127.0.0.1','localhost','::1') or u.path!=expected_path
            or u.username or u.password or u.query or u.fragment):raise ValueError('LOCAL_ENDPOINT_ONLY')
    class NoRedirect(urllib.request.HTTPRedirectHandler):
        def redirect_request(self,*args,**kwargs):raise ValueError('LOCAL_SERVICE_REDIRECT_FORBIDDEN')
    opener=urllib.request.build_opener(urllib.request.ProxyHandler({}),NoRedirect())
    request=urllib.request.Request(endpoint,data=encode_body(body,preserve_order) if body is not None else None,
                                   headers={'Content-Type':'application/json'})
    with opener.open(request,timeout=120) as response:raw=response.read(1_000_001)
    if len(raw)>1_000_000:raise ValueError('LOCAL_RESPONSE_TOO_LARGE')
    return raw


def local_json(endpoint, expected_path, body=None, *, preserve_order=False):
    return json.loads(local_bytes(endpoint,expected_path,body,preserve_order=preserve_order))
