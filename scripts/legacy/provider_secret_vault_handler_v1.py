#!/usr/bin/env python3
import json, os, re, tempfile, urllib.request
from pathlib import Path
from http.server import BaseHTTPRequestHandler, HTTPServer

HOST="127.0.0.1"
PORT=8097
BASE=Path("/root/tokenoskobi_clean_v1")
SECRETS=BASE/".secrets"
BNB_ENV=SECRETS/"alchemy_bnb.env"
MAX_BODY=8192

def _redact(v):
    if not v:
        return None
    v=str(v).strip()
    if "/v2/" in v:
        return re.sub(r"(/v2/)[A-Za-z0-9_\-]+", r"\1<REDACTED>", v)
    if len(v)>10:
        return v[:4]+"..."+v[-4:]
    return "<REDACTED>"

def _read_secret_url():
    if not BNB_ENV.exists():
        return None
    try:
        for line in BNB_ENV.read_text(errors="ignore").splitlines():
            if line.strip().startswith("BSC_ALCHEMY_URL="):
                return line.split("=",1)[1].strip().strip('"').strip("'")
    except Exception:
        return None
    return None

def _write_secret_url(url):
    url=(url or "").strip()
    if not re.match(r"^https://bnb-mainnet\.g\.alchemy\.com/v2/[A-Za-z0-9_\-]+$",url):
        raise ValueError("INVALID_BSC_ALCHEMY_URL_SHAPE")
    SECRETS.mkdir(parents=True,exist_ok=True)
    os.chmod(SECRETS,0o700)
    replaced=BNB_ENV.exists()
    fd,tmp=tempfile.mkstemp(prefix=".alchemy_bnb.",suffix=".tmp",dir=str(SECRETS))
    try:
        with os.fdopen(fd,"w") as f:
            f.write("BSC_ALCHEMY_URL="+url+"\n")
        os.chmod(tmp,0o600)
        os.replace(tmp,BNB_ENV)
        os.chmod(BNB_ENV,0o600)
    finally:
        try:
            if os.path.exists(tmp): os.unlink(tmp)
        except Exception:
            pass
    return replaced

def _json_rpc(url,method,params=None):
    body=json.dumps({"jsonrpc":"2.0","id":1,"method":method,"params":params or []}).encode()
    req=urllib.request.Request(url,data=body,headers={"Content-Type":"application/json"},method="POST")
    with urllib.request.urlopen(req,timeout=8) as r:
        return json.loads(r.read().decode())

class H(BaseHTTPRequestHandler):
    server_version="CoinoskobiProviderSecretVault/1.0"
    def log_message(self,fmt,*args):
        return
    def _send(self,code,obj):
        data=json.dumps(obj,ensure_ascii=False).encode()
        self.send_response(code)
        self.send_header("Content-Type","application/json; charset=utf-8")
        self.send_header("Cache-Control","no-store")
        self.send_header("Content-Length",str(len(data)))
        self.end_headers()
        self.wfile.write(data)
    def _body(self):
        n=int(self.headers.get("Content-Length","0") or "0")
        if n>MAX_BODY:
            raise ValueError("BODY_TOO_LARGE")
        raw=self.rfile.read(n) if n else b"{}"
        return json.loads(raw.decode() or "{}")
    def do_GET(self):
        if self.path.split("?")[0]!="/internal/provider-secret/status":
            return self._send(404,{"ok":False,"error":"NOT_FOUND"})
        url=_read_secret_url()
        return self._send(200,{"ok":True,"bsc_alchemy_configured":bool(url),"redacted":_redact(url),"secret_value_returned":False})
    def do_POST(self):
        path=self.path.split("?")[0]
        if path=="/internal/provider-secret/save":
            try:
                data=self._body()
                url=(data.get("bsc_alchemy_url") or data.get("url") or "").strip()
                replaced=_write_secret_url(url)
                return self._send(200,{"ok":True,"saved":True,"replaced_existing":replaced,"redacted":_redact(url),"secret_value_returned":False})
            except Exception as e:
                return self._send(400,{"ok":False,"error":str(e),"secret_value_returned":False})
        if path=="/internal/provider-secret/test-bsc-alchemy":
            url=_read_secret_url()
            if not url:
                return self._send(400,{"ok":False,"error":"BSC_ALCHEMY_URL_NOT_CONFIGURED","secret_value_returned":False})
            try:
                r=_json_rpc(url,"eth_blockNumber",[])
                return self._send(200,{"ok":True,"method":"eth_blockNumber","latest_block_hex":r.get("result"),"calls_used":1,"max_calls":3,"redacted":_redact(url),"secret_value_returned":False})
            except Exception as e:
                return self._send(502,{"ok":False,"error":"PROVIDER_TEST_FAILED","detail":str(e)[:160],"calls_used":1,"max_calls":3,"secret_value_returned":False})
        return self._send(404,{"ok":False,"error":"NOT_FOUND"})

if __name__=="__main__":
    HTTPServer((HOST,PORT),H).serve_forever()
