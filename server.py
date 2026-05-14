import csv
import json
import os
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse

SAFE_DOMAINS = set()

def load_safe_domains(path="safeUrl.csv"):
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.reader(f):
            if len(row) >= 2:
                SAFE_DOMAINS.add(row[1].strip().lower())
    print(f"[서버] 안전 도메인 {len(SAFE_DOMAINS):,}개 로드 완료")

def extract_domain(url):
    url = url.strip()
    if not url.startswith(("http://", "https://")):
        url = "http://" + url
    parsed = urlparse(url)
    domain = parsed.netloc.lower()
    if domain.startswith("www."):
        domain = domain[4:]
    return domain

def is_safe(url):
    domain = extract_domain(url)
    return domain in SAFE_DOMAINS, domain

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path in ("/", "/urlChecker.html"):
            html_path = os.path.join(os.path.dirname(__file__), "urlChecker.html")
            with open(html_path, "rb") as f:
                body = f.read()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        else:
            self.send_response(404)
            self.end_headers()

    def do_OPTIONS(self):
        self._send_cors()

    def do_POST(self):
        if self.path != "/check":
            self.send_response(404)
            self.end_headers()
            return

        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length).decode("utf-8")

        try:
            data = json.loads(body)
            url = data.get("url", "").strip()
        except Exception:
            url = body.strip()

        if not url:
            self._respond({"safe": False, "message": "URL을 입력해주세요.", "domain": ""})
            return

        safe, domain = is_safe(url)
        if safe:
            msg = f"안전한 URL입니다. ({domain}은 신뢰 목록에 있습니다)"
        else:
            msg = f"위험 URL로 의심됩니다. ({domain}은 신뢰 목록에 없습니다)"

        self._respond({"safe": safe, "message": msg, "domain": domain})

    def _respond(self, data):
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self._send_cors(200)
        self.wfile.write(body)

    def _send_cors(self, code=204):
        self.send_response(code)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.end_headers()

    def log_message(self, fmt, *args):
        print(f"[요청] {self.address_string()} - {fmt % args}")

if __name__ == "__main__":
    load_safe_domains("safeUrl.csv")
    host, port = "0.0.0.0", 8765
    server = HTTPServer((host, port), Handler)
    print(f"[서버] http://localhost:{port} 에서 실행 중...")
    server.serve_forever()
