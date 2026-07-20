#!/usr/bin/python3
import base64, json, os, socket, subprocess, tempfile

def exchange(path, request):
    client = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    client.settimeout(3)
    client.connect(path)
    client.sendall(request)
    response = client.recv(8192)
    client.close()
    return response

signed = json.loads(exchange(
    "/run/tokenoskobi-era57f7/authority/authority.sock",
    b"PROBE_V1\n",
))
assert signed["ok"] is True

payload = base64.b64decode(signed["payload"])
signature = base64.b64decode(signed["signature"])
assert f"|uid={os.getuid()}|".encode() in payload

with tempfile.NamedTemporaryFile() as message, \
        tempfile.NamedTemporaryFile() as sig:
    message.write(payload); message.flush()
    sig.write(signature); sig.flush()
    subprocess.run([
        "openssl", "pkeyutl", "-verify", "-rawin", "-pubin",
        "-inkey", "/etc/tokenoskobi-era57f7/authority_ed25519_public.pem",
        "-in", message.name, "-sigfile", sig.name,
    ], check=True, stdout=subprocess.DEVNULL)

assert exchange(
    "/run/tokenoskobi-era57f7/audit/audit.sock",
    b'{"event":"AUDIT_PROBE_V1"}\n',
) == b"OK\n"

print("RUNTIME_E2E_FLOW=PASS", flush=True)
