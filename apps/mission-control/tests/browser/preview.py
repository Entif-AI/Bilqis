from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import json
root = Path('apps/mission-control/renderer').resolve()
operator = json.loads(Path('apps/mission-control/fixtures/operator-view-v1.json').read_text())
class Preview(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(root), **kwargs)
    def do_GET(self):
        if self.path == '/preview-bridge.mjs':
            data = ('window.bamfMissionControl={connect:async()=>({state:"disconnected"}),querySnapshot:async(q)=>{if(q.schemaVersion)return '+json.dumps(operator)+';throw new Error("PREVIEW_SERVICE_UNAVAILABLE");}};').encode()
            self.send_response(200);self.send_header('Content-Type','text/javascript');self.end_headers();self.wfile.write(data);return
        if self.path.split('?')[0] == '/':
            data=root.joinpath('index.html').read_text().replace('<script type="module" src="./renderer.mjs">','<script src="/preview-bridge.mjs"></script><script type="module" src="./renderer.mjs">').encode()
            self.send_response(200);self.send_header('Content-Type','text/html');self.end_headers();self.wfile.write(data);return
        super().do_GET()
ThreadingHTTPServer(('127.0.0.1', 8760), Preview).serve_forever()
