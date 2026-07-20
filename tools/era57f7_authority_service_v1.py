#!/usr/bin/python3
import base64, json, os, pwd, socket, struct, subprocess, tempfile

SOCK = "/run/tokenoskobi-era57f7/authority/authority.sock"
KEY = "/var/lib/tokenoskobi-era57f7/authority/authority_ed25519_private.pem"
RUNTIME_UID = pwd.getpwnam("tokenoskobi-runtime").pw_uid

try:
    os.unlink(SOCK)
except FileNotFoundError:
    pass

server = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
server.bind(SOCK)
os.chown(SOCK, -1, __import__("grp").getgrnam(
    "tokenoskobi-authority-ipc"
).gr_gid)
os.chmod(SOCK, 0o660)
server.listen(8)

while True:
    client, _ = server.accept()
    pid, uid, gid = struct.unpack(
        "3i",
        client.getsockopt(socket.SOL_SOCKET, socket.SO_PEERCRED, 12),
    )
    request = client.recv(128)

    if uid != RUNTIME_UID or request != b"PROBE_V1\n":
        client.sendall(b'{"ok":false,"error":"peer_denied"}\n')
        client.close()
        continue

    payload = (
        f"TOKENOSKOBI_AUTHORITY_PROBE_V1|uid={uid}|pid={pid}"
    ).encode()

    with tempfile.NamedTemporaryFile() as message:
        message.write(payload)
        message.flush()
        signature = subprocess.run(
            [
                "openssl", "pkeyutl", "-sign", "-rawin",
                "-inkey", KEY, "-in", message.name,
            ],
            check=True,
            stdout=subprocess.PIPE,
        ).stdout

    response = {
        "ok": True,
        "payload": base64.b64encode(payload).decode(),
        "signature": base64.b64encode(signature).decode(),
    }
    client.sendall(json.dumps(response).encode() + b"\n")
    client.close()
