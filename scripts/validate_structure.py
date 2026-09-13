#!/usr/bin/env python3
"""Validate rendered GitOps ownership; --ready rejects deployment placeholders."""
from pathlib import Path
import argparse
import re
import subprocess
import sys
import yaml

ROOT = Path(__file__).resolve().parents[1]
SERVICES = ('auth-service', 'flag-service', 'targeting-service', 'evaluation-service', 'analytics-service')
PLACEHOLDER = re.compile(r'__[A-Z0-9_]+__|ocir\.invalid|replace-with|:bootstrap|:latest')


def validate(root, ready=False):
    errors, owners = [], {}
    for owner, path in [('platform', root/'platform/overlays/homolog')] + [(s, root/'apps'/s/'overlays/homolog') for s in SERVICES]:
        result = subprocess.run(['kubectl', 'kustomize', str(path)], capture_output=True, text=True)
        if result.returncode:
            errors.append(f'{owner}: Kustomize failed: {result.stderr.strip()}')
            continue
        docs = [d for d in yaml.safe_load_all(result.stdout) if d]
        if ready and PLACEHOLDER.search(result.stdout):
            errors.append(f'{owner}: unresolved endpoint or image placeholders')
        if owner in SERVICES:
            for kind in ['Deployment', 'Service', 'ServiceAccount']:
                if sum(d['kind'] == kind and d['metadata']['name'] == owner for d in docs) != 1:
                    errors.append(f'{owner}: expected exactly one {kind}')
            for d in docs:
                if d['kind'] == 'Deployment' and ready:
                    image = d['spec']['template']['spec']['containers'][0]['image']
                    if not re.fullmatch(r'[^\s]+:sha-[0-9a-f]{12}', image):
                        errors.append(f'{owner}: image must use sha-<12 hex>')
        for d in docs:
            key = (d['apiVersion'], d['kind'], d['metadata'].get('namespace', ''), d['metadata']['name'])
            if key in owners:
                errors.append(f'duplicate ownership: {key}, {owners[key]} and {owner}')
            owners[key] = owner
            if d['kind'] == 'Secret':
                errors.append(f'{owner}: rendered Secret values must not be committed')
        print(f'{owner}: {len(docs)} resources')
    return errors


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--ready', action='store_true')
    parser.add_argument('--root', type=Path, default=ROOT)
    args = parser.parse_args()
    errors = validate(args.root, args.ready)
    for error in errors:
        print('error: ' + error, file=sys.stderr)
    if not errors:
        print('GitOps manifests validated' + (' for configured deployment inputs' if args.ready else '; readiness requires --ready after configuration'))
    return bool(errors)


if __name__ == '__main__':
    sys.exit(main())
