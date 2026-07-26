#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, os, re, subprocess
from pathlib import Path

ALLOWED_DIRTY = {
    'config/product_slice_02_v1.json',
    'config/nginx/panel.coinoskobi.xyz.conf',
    'tools/tokenoskobi_product_slice_02_server.py',
    'tests/test_product_slice_02.py',
    'systemd_drafts/tokenoskobi-product-slice-02.service',
}
TARGETS = {
    'config/product_slice_02_v1.json',
    'tools/tokenoskobi_product_slice_02_server.py',
    'tests/test_product_slice_02.py',
    'systemd_drafts/tokenoskobi-product-slice-02.service',
}


def dirty_check(root: Path) -> None:
    rows = subprocess.check_output(
        ['git', '-C', str(root), 'status', '--porcelain=v1', '--untracked-files=all'],
        text=True,
    ).splitlines()
    seen = []
    for row in rows:
        path = row[3:]
        if ' -> ' in path:
            path = path.split(' -> ', 1)[1]
        seen.append(path)
    unexpected = sorted(set(seen) - ALLOWED_DIRTY)
    print(f'WORKTREE_ROWS={len(rows)}')
    print('EXPECTED_RECOVERY_DIRTY_PATHS=' + (','.join(sorted(set(seen) & ALLOWED_DIRTY)) or 'NONE'))
    if unexpected:
        raise SystemExit('BLOCKED=UNEXPECTED_DIRTY_PATHS:' + ','.join(unexpected))


def extract(deploy: Path, stage: Path) -> None:
    lines = deploy.read_text(encoding='utf-8').splitlines()
    found: dict[str, str] = {}
    pattern = re.compile(r"^cat > ([^ ]+) <<'([^']+)'$")
    i = 0
    while i < len(lines):
        match = pattern.match(lines[i])
        if not match:
            i += 1
            continue
        path, tag = match.groups()
        i += 1
        body: list[str] = []
        while i < len(lines) and lines[i] != tag:
            body.append(lines[i])
            i += 1
        if i >= len(lines):
            raise SystemExit('BLOCKED=UNTERMINATED_HEREDOC:' + path)
        if path in TARGETS:
            found[path] = '\n'.join(body) + '\n'
        i += 1
    missing = sorted(TARGETS - set(found))
    if missing:
        raise SystemExit('BLOCKED=MISSING_SOURCE_BLOCKS:' + ','.join(missing))
    for rel, body in found.items():
        target = stage / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(body, encoding='utf-8')
        target.chmod(0o755 if rel.endswith('_server.py') else 0o644)
    print('EXTRACTED=' + ','.join(sorted(found)))


def verify_packet(path: Path) -> None:
    packet = json.loads(path.read_text(encoding='utf-8'))
    authority = packet['authority']
    assert all(authority[k] is False for k in ('paper', 'live', 'wallet', 'signing', 'order', 'broadcast'))
    assert authority['human_action_required'] is True
    assert packet['decision']['authority'] == 'ADVISORY_ONLY'
    print('AUTHORITY=VERIFIED_ZERO')
    print('DECISION=' + str(packet['decision']['decision']))
    print('DATA_QUALITY=' + str(packet['decision']['data_quality']))


def discover_auth() -> None:
    files: set[str] = set()
    for root in (Path('/etc/nginx/conf.d'), Path('/etc/nginx/sites-enabled'), Path('/etc/nginx/sites-available')):
        if not root.exists():
            continue
        for path in root.rglob('*'):
            try:
                if not path.is_file():
                    continue
                text = path.read_text(errors='ignore')
            except Exception:
                continue
            for raw in re.findall(r'(?m)^\s*auth_basic_user_file\s+([^;]+);', text):
                value = raw.strip().strip('"').strip("'")
                if value.startswith('/') and '$' not in value and Path(value).is_file():
                    files.add(str(Path(value).resolve()))
    if len(files) != 1:
        print(f'AUTH_FILE_CANDIDATE_COUNT={len(files)}')
        for value in sorted(files):
            print('AUTH_FILE_CANDIDATE=' + value)
        raise SystemExit('BLOCKED=AUTH_FILE_DISCOVERY_NOT_UNIQUE')
    print(next(iter(files)))


def remove_blocks(text: str, header: str) -> tuple[str, int]:
    count = 0
    while True:
        start = text.find(header)
        if start < 0:
            return text, count
        brace = text.find('{', start)
        if brace < 0:
            raise SystemExit('BLOCKED=NGINX_OPEN_BRACE_MISSING:' + header)
        depth, end = 0, None
        for index in range(brace, len(text)):
            if text[index] == '{':
                depth += 1
            elif text[index] == '}':
                depth -= 1
                if depth == 0:
                    end = index + 1
                    break
        if end is None:
            raise SystemExit('BLOCKED=NGINX_CLOSE_BRACE_MISSING:' + header)
        line_start = text.rfind('\n', 0, start) + 1
        line_end = text.find('\n', end)
        line_end = len(text) if line_end < 0 else line_end + 1
        indent = text[line_start:start]
        text = text[:line_start] + indent + '# TOKENOSKOBI_FIX6_AUTHENTICATED_ROOT_PROXY\n' + text[line_end:]
        count += 1


def patch_nginx(path: Path, auth_file: str) -> None:
    text = path.read_text(encoding='utf-8')
    headers = (
        'location = /panel/panel_v2/news_coverage.html {',
        'location = /panel/panel_v2/ {',
        'location ^~ /panel/panel_v2/ {',
    )
    counts: dict[str, int] = {}
    for header in headers:
        text, counts[header] = remove_blocks(text, header)
    if counts[headers[1]] < 2 or counts[headers[2]] < 2:
        raise SystemExit('BLOCKED=EXPECTED_PANEL_SHADOW_BLOCKS_NOT_FOUND')

    header = 'location / {'
    position, patched = 0, 0
    while True:
        start = text.find(header, position)
        if start < 0:
            break
        brace, depth, end = text.find('{', start), 0, None
        for index in range(brace, len(text)):
            if text[index] == '{':
                depth += 1
            elif text[index] == '}':
                depth -= 1
                if depth == 0:
                    end = index + 1
                    break
        if end is None:
            raise SystemExit('BLOCKED=ROOT_LOCATION_UNTERMINATED')
        block = text[start:end]
        if 'proxy_pass http://127.0.0.1:8096/' in block:
            block = re.sub(r'(?m)^\s*auth_basic\s+[^;]+;\s*\n?', '', block)
            block = re.sub(r'(?m)^\s*auth_basic_user_file\s+[^;]+;\s*\n?', '', block)
            newline = block.find('\n')
            insertion = (
                '        auth_basic "Tokenoskobi Private Panel";\n'
                f'        auth_basic_user_file {auth_file};\n'
            )
            block = block[:newline + 1] + insertion + block[newline + 1:]
            text = text[:start] + block + text[end:]
            end = start + len(block)
            patched += 1
        position = end
    if patched < 1 or 'proxy_pass http://127.0.0.1:8096/;' not in text:
        raise SystemExit('BLOCKED=ROOT_REVERSE_PROXY_NOT_PATCHED')
    if headers[1] in text or headers[2] in text:
        raise SystemExit('BLOCKED=STATIC_SHADOW_ROUTE_REMAINS')

    temp = path.with_name(path.name + '.fix6.tmp')
    temp.write_text(text, encoding='utf-8')
    os.chmod(temp, path.stat().st_mode & 0o777)
    os.replace(temp, path)
    print(f'NGINX_REMOVED_NEWS_BLOCKS={counts[headers[0]]}')
    print(f'NGINX_REMOVED_EXACT_BLOCKS={counts[headers[1]]}')
    print(f'NGINX_REMOVED_PREFIX_BLOCKS={counts[headers[2]]}')
    print(f'NGINX_AUTH_ROOT_LOCATIONS={patched}')


def main() -> None:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest='command', required=True)
    p = sub.add_parser('dirty-check'); p.add_argument('root', type=Path)
    p = sub.add_parser('extract'); p.add_argument('deploy', type=Path); p.add_argument('stage', type=Path)
    p = sub.add_parser('verify-packet'); p.add_argument('path', type=Path)
    sub.add_parser('discover-auth')
    p = sub.add_parser('patch-nginx'); p.add_argument('path', type=Path); p.add_argument('auth_file')
    args = parser.parse_args()
    if args.command == 'dirty-check': dirty_check(args.root)
    elif args.command == 'extract': extract(args.deploy, args.stage)
    elif args.command == 'verify-packet': verify_packet(args.path)
    elif args.command == 'discover-auth': discover_auth()
    elif args.command == 'patch-nginx': patch_nginx(args.path, args.auth_file)

if __name__ == '__main__':
    main()
