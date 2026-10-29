#!/usr/bin/env python3
"""Drainer opt-in presence relay (stdlib). Run behind HTTPS reverse proxy in production.

Honest limitations: this is NOT Mojang-authenticated identity and must not grant roles,
trust, or access. A deployment should add stronger login/authentication before public use.
"""
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlsplit
from threading import Lock
import hashlib
import json
import os
import re
import time
import uuid

TTL = 45
HOST = os.getenv('DRAINER_BIND', '127.0.0.1')
PORT = int(os.getenv('DRAINER_PORT', os.getenv('PORT', '8787')))
records = {}
lock = Lock()
HEX = re.compile(r'^[0-9a-f]{64}$')
NAME = re.compile(r'^[a-zA-Z0-9_]{1,16}$')
TOKEN = re.compile(r'^[0-9a-f]{64}$')


def valid(payload, *, leave=False):
    if not isinstance(payload, dict) or not HEX.fullmatch(payload.get('server', '')):
        return False
    try:
        uid = str(uuid.UUID(payload.get('uuid', '')))
    except (ValueError, TypeError, AttributeError):
        return False
    if uid != payload.get('uuid') or not TOKEN.fullmatch(payload.get('token', '')):
        return False
    if not leave:
        if not NAME.fullmatch(payload.get('name', '')):
            return False
        cos = payload.get('cosmetics', [])
        if not isinstance(cos, list) or len(cos) > 12:
            return False
        for c in cos:
            if not isinstance(c, dict):
                return False
            for key, limit in [('name', 30), ('style', 32)]:
                val = c.get(key)
                if not isinstance(val, str) or len(val) > limit or any(ord(x) < 32 for x in val):
                    return False
    return True


def purge(now):
    for key, record in list(records.items()):
        if now - record['time'] > TTL:
            records.pop(key, None)


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *_):
        return  # Avoid logging usernames, queries or relay keys

    def reply(self, status, obj):
        body = json.dumps(obj, separators=(',', ':')).encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Cache-Control', 'no-store')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        path = urlsplit(self.path)
        if path.path in ('/', '/health'):
            self.reply(200, {'ok': True, 'service': 'drainer-network-relay', 'version': 'v1-test'})
            return
        if path.path != '/v1/players':
            self.reply(404, {'error': 'not found'})
            return
        server = parse_qs(path.query).get('server', [''])[0]
        if not HEX.fullmatch(server):
            self.reply(400, {'error': 'invalid server key'})
            return
        with lock:
            purge(time.monotonic())
            players = [rec['data'] for (srv, _), rec in records.items() if srv == server][:250]
        self.reply(200, {'players': players})

    def do_POST(self):
        if self.path not in ('/v1/presence', '/v1/leave'):
            self.reply(404, {'error': 'not found'})
            return
        try:
            length = int(self.headers.get('Content-Length', '0'))
            if length < 2 or length > 4096:
                raise ValueError('payload too large')
            obj = json.loads(self.rfile.read(length))
            is_leave = self.path == '/v1/leave'
            if not valid(obj, leave=is_leave):
                raise ValueError('invalid body')
        except (ValueError, TypeError, json.JSONDecodeError):
            self.reply(400, {'error': 'invalid request'})
            return
        key = (obj['server'], obj['uuid'])
        token_hash = hashlib.sha256(obj['token'].encode('ascii')).hexdigest()
        now = time.monotonic()
        with lock:
            purge(now)
            old = records.get(key)
            if old and old['token_hash'] != token_hash:
                self.reply(409, {'error': 'claimed identity (not verified)'})
                return
            if is_leave:
                records.pop(key, None)
            else:
                if len(records) > 3000 and not old:
                    self.reply(503, {'error': 'capacity reached'})
                    return
                records[key] = {
                    'data': {k: obj[k] for k in ('uuid', 'name', 'cosmetics')},
                    'time': now,
                    'token_hash': token_hash,
                }
        self.reply(200, {'ok': True})


if __name__ == '__main__':
    print(f'Drainer relay listening on http://{HOST}:{PORT} (use HTTPS reverse proxy for remote access)')
    ThreadingHTTPServer((HOST, PORT), Handler).serve_forever()
