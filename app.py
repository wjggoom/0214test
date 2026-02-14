import json
from datetime import datetime
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Lock
from urllib.parse import urlparse

ROOT_DIR = Path(__file__).resolve().parent
STATIC_DIR = ROOT_DIR / "static"
TEMPLATES_DIR = ROOT_DIR / "templates"

entries = []
entries_lock = Lock()

CONTENT_TYPES = {
    ".html": "text/html; charset=utf-8",
    ".css": "text/css; charset=utf-8",
    ".js": "application/javascript; charset=utf-8",
}


class DiaryHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        path = urlparse(self.path).path

        if path == "/":
            return self._serve_file(TEMPLATES_DIR / "index.html")
        if path == "/api/entries":
            return self._list_entries()
        if path.startswith("/static/"):
            relative = path.replace("/static/", "", 1)
            return self._serve_file(STATIC_DIR / relative)

        self._send_json({"error": "Not Found"}, status=HTTPStatus.NOT_FOUND)

    def do_POST(self):
        path = urlparse(self.path).path
        if path != "/api/entries":
            return self._send_json({"error": "Not Found"}, status=HTTPStatus.NOT_FOUND)

        content_length = int(self.headers.get("Content-Length", "0"))
        raw_body = self.rfile.read(content_length)

        try:
            payload = json.loads(raw_body.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            return self._send_json({"error": "요청 형식이 올바르지 않습니다."}, status=HTTPStatus.BAD_REQUEST)

        student_name = (payload.get("student_name") or "").strip()
        content = (payload.get("content") or "").strip()

        if not student_name or not content:
            return self._send_json({"error": "학생 이름과 일기 내용을 입력해주세요."}, status=HTTPStatus.BAD_REQUEST)

        with entries_lock:
            new_entry = {
                "id": len(entries) + 1,
                "student_name": student_name,
                "content": content,
                "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            }
            entries.append(new_entry)

        return self._send_json({"message": "일기가 저장되었습니다.", "entry": new_entry}, status=HTTPStatus.CREATED)

    def _list_entries(self):
        with entries_lock:
            ordered_entries = list(reversed(entries))
        self._send_json({"entries": ordered_entries})

    def _serve_file(self, file_path: Path):
        if not file_path.exists() or not file_path.is_file():
            return self._send_json({"error": "Not Found"}, status=HTTPStatus.NOT_FOUND)

        content_type = CONTENT_TYPES.get(file_path.suffix, "application/octet-stream")
        payload = file_path.read_bytes()

        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def _send_json(self, data, status=HTTPStatus.OK):
        payload = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)


if __name__ == "__main__":
    server = ThreadingHTTPServer(("0.0.0.0", 5000), DiaryHandler)
    print("Server running on http://0.0.0.0:5000")
    server.serve_forever()
