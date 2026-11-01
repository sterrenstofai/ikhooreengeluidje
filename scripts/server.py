"""Lokale testserver die zich gedraagt als Netlify: SPA-paden geven index.html, met de CSP uit netlify.toml.

Gebruik: python3 scripts/server.py [poort]   (vanuit de repo-root)
"""
import http.server, os, sys

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "site")


import re
_toml = open(os.path.join(ROOT, "..", "netlify.toml")).read()
CSP = re.search(r'Content-Security-Policy = "([^"]+)"', _toml).group(1)


class Handler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        # dezelfde CSP als op Netlify, zodat een blokkade al lokaal opvalt
        self.send_header("Content-Security-Policy", CSP)
        super().end_headers()

    def __init__(self, *a, **k):
        super().__init__(*a, directory=ROOT, **k)

    def send_head(self):
        pad = self.path.split("?")[0]
        if pad.startswith(("/nummer/", "/instrument/", "/onderzoekjes", "/gevonden/")) or pad in ("/nummers", "/instrumenten", "/ontdek", "/kinderen", "/sporen", "/mijn", "/zoek"):
            self.path = "/index.html"
        elif pad == "/hoe-dit-werkt":
            self.path = "/hoe-dit-werkt.html"
        return super().send_head()

    def log_message(self, *a):
        pass


http.server.ThreadingHTTPServer(("127.0.0.1", int(sys.argv[1]) if len(sys.argv) > 1 else 8080), Handler).serve_forever()
