import hmac
import os

class BearerAuth:
    def __init__(self, app, secret=None):
        self.app = app
        self.secret = secret or os.environ.get('YO_MCP_TOKEN')
        if not self.secret or len(self.secret) < 32:
            raise RuntimeError('YO_MCP_TOKEN must be a random secret of at least 32 characters')

    async def __call__(self, scope, receive, send):
        if scope['type'] != 'http':
            return await self.app(scope, receive, send)
        headers = dict(scope.get('headers', []))
        supplied = headers.get(b'authorization', b'').decode('latin-1')
        expected = 'Bearer ' + self.secret
        if not hmac.compare_digest(supplied.encode(), expected.encode()):
            await send({'type':'http.response.start','status':401,'headers':[(b'content-type',b'application/json'),(b'cache-control',b'no-store')]})
            await send({'type':'http.response.body','body':b'{"error":"unauthorized"}'})
            return
        return await self.app(scope, receive, send)
