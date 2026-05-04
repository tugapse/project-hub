from typing import List, Tuple

class MIMETypeFixerMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        # Only handle HTTP requests for common static assets
        if scope.get('type') == 'http' and scope.get('path', '').endswith(('.js', '.css', '.png', '.jpg', '.svg')):
            original_path = scope['path']
            mime_type = self._determine_mime_type(original_path)

            # Check if Content-Type header already exists to avoid duplicates
            headers: List[Tuple[bytes, bytes]] = scope.get('headers', [])
            if not any(header[0] == b'content-type' for header in headers):
                headers.append((b'Content-Type', mime_type.encode('utf-8')))
                scope['headers'] = headers
           
            await self.app(scope, receive, send)
        else:
            await self.app(scope, receive, send)

    def _determine_mime_type(self, path: str) -> str:
        if path.endswith('.js'):
            return 'application/javascript'
        elif path.endswith('.css'):
            return 'text/css'
        elif path.endswith('.png'):
            return 'image/png'
        elif path.endswith('.jpg') or path.endswith('.jpeg'):
            return 'image/jpeg'
        elif path.endswith('.svg'):
            return 'image/svg+xml'
        else:
            return 'application/octet-stream'  # Default fallback