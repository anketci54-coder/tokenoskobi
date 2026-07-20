#!/usr/bin/python3
import json, os, pwd, grp, socket, struct

SOCK = "/run/tokenoskobi-era57f7/audit/audit.sock"
FILE = "/var/lib/tokenoskobi-era57f7/audit/audit_service.log"
RUNTIME_UID = pwd.getpwnam("tokenoskobi-runtime").pw_uid

try:
    os.unlink(SOCK)
except FileNotFoundError:
    pass

server = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
server.bind(SOCK)
os.chown(SOCK, -1, grp.getgrnam("tokenoskobi-audit-ipc").gr_gid)
os.chmod(SOCK, 0o660)
server.listen(8)

while True:
    client, _ = server.accept()
    pid, uid, gid = struct.unpack(
        "3i",
        client.getsockopt(socket.SOL_SOCKET, socket.SO_PEERCRED, 12),
    )
    request = client.recv(512)

    if uid != RUNTIME_UID or request != b'{"event":"AUDIT_PROBE_V1"}\n':
        client.sendall(b"DENY\n")
        client.close()
        continue

    record = json.dumps(
        {"event": "AUDIT_PROBE_V1", "pid": pid, "uid": uid},
        separators=(",", ":"),
    ).encode() + b"\n"

    fd = os.open(FILE, os.O_WRONLY | os.O_APPEND)
    os.write(fd, record)
    os.fsync(fd)
    os.close(fd)

    client.sendall(b"OK\n")
    client.close()
