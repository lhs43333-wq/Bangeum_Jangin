"""방음장인 Windows 도우미.

하는 일은 두 가지뿐이다.
  1) 웹 앱(web/index.html)을 http://127.0.0.1:8765 에서 열어 준다.
  2) 웹 앱이 보낸 EQ 설정을 Equalizer APO 설정 폴더에 쓴다.

실행:  python bangeum_helper.py
표준 라이브러리만 사용한다. 이 PC 안(127.0.0.1)에서 온 요청만 받는다.
"""

import argparse
import json
import os
import re
import shutil
import sys
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

PORT = 8765
EQ_FILE = "bangeum_eq.txt"
INCLUDE_LINE = "Include: " + EQ_FILE
WEB_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "docs")

# 설정 파일에 쓸 수 있는 줄의 형식. 이 밖의 내용(다른 파일 포함, 플러그인 로드 등)은 거부한다.
NUM = r"-?\d{1,5}(\.\d{1,3})?"
ALLOWED = [
    re.compile(r"^#[^\r\n]{0,200}$"),
    re.compile(r"^Preamp: %s dB$" % NUM),
    re.compile(r"^Channel: (L|R|ALL)$"),
    re.compile(r"^Filter \d{1,2}: ON PK Fc %s Hz Gain %s dB Q %s$" % (NUM, NUM, NUM)),
]
MAX_LINES = 80
STATIC = {
    "index.html": "text/html; charset=utf-8",
    "phone.html": "text/html; charset=utf-8",
    "vendor/qrcode.js": "text/javascript; charset=utf-8",
    "vendor/peerjs.min.js": "text/javascript; charset=utf-8",
}


def find_config_dir(override=None):
    """Equalizer APO의 config 폴더를 찾는다. 없으면 None."""
    candidates = []
    if override:
        candidates.append(override)
    if os.environ.get("BANGEUM_APO_DIR"):
        candidates.append(os.environ["BANGEUM_APO_DIR"])
    if sys.platform == "win32":
        try:
            import winreg

            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\EqualizerAPO") as key:
                candidates.append(winreg.QueryValueEx(key, "ConfigPath")[0])
        except OSError:
            pass
        candidates.append(os.path.join(os.environ.get("ProgramFiles", r"C:\Program Files"), "EqualizerAPO", "config"))
    for path in candidates:
        if path and os.path.isfile(os.path.join(path, "config.txt")):
            return path
    return None


def validate(config):
    lines = config.replace("\r\n", "\n").strip("\n").split("\n")
    if not 1 <= len(lines) <= MAX_LINES:
        raise ValueError("설정 줄 수가 올바르지 않습니다")
    for line in lines:
        if not any(p.match(line) for p in ALLOWED):
            raise ValueError("허용되지 않는 설정 줄: %r" % line[:60])
    return "\n".join(lines) + "\n"


def apply_config(config_dir, config, enabled=True):
    """EQ 파일을 쓰고, config.txt에 Include 줄이 없으면 (백업 후) 추가한다."""
    text = validate(config)
    if not enabled:
        text = "# 방음장인 보정 꺼짐\n"
    with open(os.path.join(config_dir, EQ_FILE), "w", encoding="utf-8") as fh:
        fh.write(text)
    main = os.path.join(config_dir, "config.txt")
    with open(main, "r", encoding="utf-8", errors="replace") as fh:
        current = fh.read()
    if INCLUDE_LINE not in [ln.strip() for ln in current.splitlines()]:
        backup = main + ".bangeum-backup"
        if not os.path.exists(backup):
            shutil.copyfile(main, backup)
        with open(main, "a", encoding="utf-8") as fh:
            fh.write(("" if current.endswith("\n") or not current else "\n") + INCLUDE_LINE + "\n")


class Handler(BaseHTTPRequestHandler):
    config_override = None
    allowed_origins = set()

    def log_message(self, fmt, *args):
        pass

    def _origin_ok(self):
        host = (self.headers.get("Host") or "").split(":")[0]
        if host not in ("127.0.0.1", "localhost"):  # DNS 리바인딩 방지
            return False
        origin = self.headers.get("Origin")
        return origin is None or origin in self.allowed_origins

    def _send(self, code, body, ctype="application/json; charset=utf-8"):
        data = body if isinstance(body, bytes) else json.dumps(body, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        origin = self.headers.get("Origin")
        if origin in self.allowed_origins:
            self.send_header("Access-Control-Allow-Origin", origin)
            self.send_header("Access-Control-Allow-Headers", "Content-Type")
            self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
            self.send_header("Access-Control-Allow-Private-Network", "true")  # 공개 사이트 -> 이 PC 요청 허용
            self.send_header("Vary", "Origin")
        self.end_headers()
        self.wfile.write(data)

    def do_OPTIONS(self):
        self._send(204 if self._origin_ok() else 403, b"")

    def do_GET(self):
        if not self._origin_ok():
            return self._send(403, {"error": "forbidden"})
        if self.path == "/api/status":
            cfg = find_config_dir(self.config_override)
            return self._send(200, {"helper": True, "apo_installed": cfg is not None, "config_dir": cfg})
        name = self.path.split("?")[0].lstrip("/") or "index.html"
        if name in STATIC:  # 정해 둔 파일만 내보낸다
            try:
                with open(os.path.join(WEB_DIR, *name.split("/")), "rb") as fh:
                    return self._send(200, fh.read(), STATIC[name])
            except OSError:
                pass
        self._send(404, {"error": "not found"})

    def do_POST(self):
        if not self._origin_ok():
            return self._send(403, {"error": "forbidden"})
        if self.path != "/api/apply":
            return self._send(404, {"error": "not found"})
        try:
            length = int(self.headers.get("Content-Length") or 0)
            if not 0 < length <= 20000:
                raise ValueError("요청 크기가 올바르지 않습니다")
            body = json.loads(self.rfile.read(length).decode("utf-8"))
            cfg = find_config_dir(self.config_override)
            if cfg is None:
                return self._send(409, {"error": "Equalizer APO가 설치돼 있지 않습니다"})
            apply_config(cfg, str(body.get("config", "")), bool(body.get("enabled", True)))
            self._send(200, {"ok": True})
        except PermissionError:
            self._send(500, {"error": "설정 폴더에 쓸 권한이 없습니다. 도우미를 관리자 권한으로 실행해 주세요"})
        except (ValueError, KeyError, json.JSONDecodeError) as err:
            self._send(400, {"error": str(err)})


def main():
    ap = argparse.ArgumentParser(description="방음장인 도우미")
    ap.add_argument("--port", type=int, default=PORT)
    ap.add_argument("--apo-dir", help="Equalizer APO config 폴더 (자동으로 못 찾을 때)")
    ap.add_argument("--allow-origin", action="append", default=[], help="추가로 허용할 웹 주소 (예: https://example.com)")
    ap.add_argument("--no-browser", action="store_true")
    args = ap.parse_args()

    Handler.config_override = args.apo_dir
    Handler.allowed_origins = {"http://127.0.0.1:%d" % args.port, "http://localhost:%d" % args.port, *args.allow_origin}
    server = ThreadingHTTPServer(("127.0.0.1", args.port), Handler)
    url = "http://127.0.0.1:%d/" % args.port
    cfg = find_config_dir(args.apo_dir)
    print("방음장인 도우미 실행 중: %s" % url)
    print("Equalizer APO 설정 폴더: %s" % (cfg or "찾지 못함 (설치가 필요합니다)"))
    print("끝내려면 Ctrl+C")
    if not args.no_browser:
        webbrowser.open(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
