"""Verify SHA-256 hashes for distributed repository files; --write refreshes them."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / 'SHA256SUMS.json'


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--write', action='store_true')
    args = parser.parse_args()
    # Git's ignore rules exclude virtual environments, private notes and fresh
    # test outputs. Include pending source files when preparing a release.
    listing = subprocess.check_output(
        ['git', 'ls-files', '--cached', '--others', '--exclude-standard', '-z'], cwd=ROOT
    ).decode('utf-8')
    paths = sorted(set(listing.rstrip('\0').split('\0')) - {'SHA256SUMS.json', ''})
    current = {
        path: hashlib.sha256((ROOT / path).read_bytes()).hexdigest()
        for path in paths if (ROOT / path).is_file()
    }
    if args.write:
        MANIFEST.write_text(json.dumps(current, indent=2) + '\n', encoding='utf-8')
        print(f'Updated SHA256SUMS.json for {len(current)} repository files.')
        return 0
    expected = json.loads(MANIFEST.read_text(encoding='utf-8'))
    mismatches = sorted(path for path in set(current) | set(expected)
                        if current.get(path) != expected.get(path))
    if mismatches:
        print('FAIL: manifest differs for ' + ', '.join(mismatches))
        print('After reviewing source changes, run python3 tools/check_manifest.py --write.')
        return 1
    print(f'PASS: {len(current)} repository file hashes match SHA256SUMS.json.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
