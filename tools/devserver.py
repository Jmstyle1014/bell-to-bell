# Local dev server for Bell to Bell: serves the folder like `python -m http.server`, and also accepts
# PUT uploads into art/<name>/ so tools/sprite-prep.html can save processed sprite sheets.
# Run: python tools/devserver.py 8768
import http.server, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SAFE = re.compile(r'^/art/[a-z0-9_-]+/[a-z0-9_.-]+\.(webp|png|json)$')


class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *a, **kw):
        super().__init__(*a, directory=ROOT, **kw)

    def do_PUT(self):
        if not SAFE.match(self.path) or self.client_address[0] not in ('127.0.0.1', '::1'):
            self.send_error(403, 'Only art/<folder>/<file> uploads from this machine')
            return
        size = int(self.headers.get('Content-Length', 0))
        if size > 20 * 1024 * 1024:
            self.send_error(413)
            return
        dest = os.path.join(ROOT, *self.path.strip('/').split('/'))
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        with open(dest, 'wb') as f:
            f.write(self.rfile.read(size))
        self.send_response(204)
        self.end_headers()


port = int(sys.argv[1]) if len(sys.argv) > 1 else 8768
http.server.ThreadingHTTPServer(('localhost', port), Handler).serve_forever()
