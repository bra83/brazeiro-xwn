#!/usr/bin/env python3
"""Build a deterministic Android integration bundle around a Barbara wheel."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import zipfile

VERSION = '1.0.0'
SUPPORTED = [
    'dnd','mystara','mausritter','forbidden_lands','the_one_ring','gurps',
    'worlds_without_number','stars_without_number','cities_without_number',
    'ashes_without_number','tales_from_the_loop','traveller_2e',
]


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda: f.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def build(wheel: Path, output: Path, source_commit: str) -> dict:
    if not wheel.is_file():
        raise FileNotFoundError(wheel)
    gateway = Path('integration/android/BarbaraGateway.kt')
    guide = Path('docs/ANDROID_INTEGRATION.md')
    for required in (gateway, guide):
        if not required.is_file():
            raise FileNotFoundError(required)
    manifest = {
        'format': 1,
        'motor': 'motor-barbara',
        'version': VERSION,
        'source_commit': source_commit,
        'wheel': wheel.name,
        'wheel_sha256': sha256(wheel),
        'android_entrypoint': 'barbara.android',
        'host_contract': 'json-v1',
        'supported_systems': SUPPORTED,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, 'w', compression=zipfile.ZIP_DEFLATED) as z:
        z.write(wheel, f'python/{wheel.name}')
        z.write(gateway, 'kotlin/BarbaraGateway.kt')
        z.write(guide, 'ANDROID_INTEGRATION.md')
        z.writestr('barbara-android-manifest.json', json.dumps(manifest, ensure_ascii=False, sort_keys=True, indent=2) + '\n')
    return manifest


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument('wheel', type=Path)
    p.add_argument('-o', '--output', type=Path, default=Path('dist/motor-barbara-android-1.0.0.zip'))
    p.add_argument('--source-commit', default=os.environ.get('GITHUB_SHA', 'unknown'))
    args = p.parse_args()
    manifest = build(args.wheel, args.output, args.source_commit)
    print(json.dumps(manifest, sort_keys=True))


if __name__ == '__main__':
    main()
