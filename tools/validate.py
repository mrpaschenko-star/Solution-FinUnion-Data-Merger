#!/usr/bin/env python3
"""Validate coursework structure, local links, source hash and PNG exports."""
import argparse
import hashlib
import json
from pathlib import Path
import re
from urllib.parse import unquote
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
REQUIRED = {
    'Task1': ['README', 'entities', 'logical-data-model', 'data-classification',
              'storage-strategy', 'reference-model'],
    'Task2': ['README', 'master-systems', 'data-ownership', 'data-flows',
              'data-flow-management', 'data-dependencies'],
    'Task3': ['README', 'target-data-architecture', 'architecture-options', 'dwh-lakehouse',
              'data-pipelines', 'analytical-model', 'data-products'],
    'Task4': ['README', 'migration-target-state', 'migration-plan', 'cutover-plan',
              'migration-risks', 'tech-roadmap'],
}
DIAGRAMS = {
    'Task1': ['logical-model'],
    'Task2': ['context-zero', 'flows-3m'],
    'Task3': ['target-12m', 'analytical-star'],
    'Task4': ['migration-roadmap', 'reporting-cutover'],
}

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, help='Optional original Sprint#6.docx')
    args = parser.parse_args()
    errors = []
    for task, names in REQUIRED.items():
        for name in names:
            path = ROOT / task / (name + '.md')
            if not path.is_file() or path.stat().st_size < 100:
                errors.append(f'Missing/empty: {path.relative_to(ROOT)}')
    for task, names in DIAGRAMS.items():
        for name in names:
            base = ROOT / task / 'diagrams' / name
            source = base.with_suffix('.puml')
            if not source.exists():
                errors.append(f'Missing source: {source}')
                continue
            content = source.read_text()
            if '@startuml' not in content or '@enduml' not in content:
                errors.append(f'Invalid PlantUML delimiters: {source}')
            if re.search(r'^\s*!include', content, flags=re.M):
                errors.append(f'Unexpected external diagram dependency: {source}')
            try:
                with Image.open(base.with_suffix('.png')) as image:
                    if image.format != 'PNG' or min(image.size) < 100:
                        errors.append(f'Invalid PNG: {base}')
                    image.verify()
            except (OSError, SyntaxError) as exc:
                errors.append(f'PNG error: {base}: {exc}')
    for path in ROOT.rglob('*.md'):
        for destination in re.findall(r'!?\[[^\]]*\]\(([^\n)]+)\)', path.read_text()):
            destination = destination.strip().strip('<>')
            if re.match(r'^[a-zA-Z][a-zA-Z0-9+.-]*:', destination) or destination.startswith('#'):
                continue
            local = unquote(destination.split('#', 1)[0])
            if local and not (path.parent / local).exists():
                errors.append(f'Broken link: {path.relative_to(ROOT)} -> {destination}')
    for pattern in ('*.svg', '*.drawio', '*.mmd'):
        errors.extend(f'Unexpected diagram format: {p}' for p in ROOT.rglob(pattern))
    if args.source:
        manifest = json.loads((ROOT / 'sources/manifest.json').read_text())
        if hashlib.sha256(args.source.read_bytes()).hexdigest() != manifest['sha256']:
            errors.append('Original DOCX hash differs from source manifest')
    if errors:
        raise SystemExit('\n'.join(errors))
    print('PASS: 25 required task documents; 7 PlantUML/PNG pairs; local links; PNG integrity; no SVG.')
    if args.source:
        print('PASS: original DOCX SHA256 matches manifest.')
    print('Scope: structural checks only; not a bank deployment or financial acceptance test.')

if __name__ == '__main__':
    main()
