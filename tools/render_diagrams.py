#!/usr/bin/env python3
"""Render Sprint 6 PlantUML sources locally, producing PNG only."""
import argparse
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--java', required=True, help='Existing Java runtime executable')
    parser.add_argument('--jar', required=True, type=Path, help='Existing plantuml.jar')
    args = parser.parse_args()
    sources = sorted(ROOT.glob('Task*/diagrams/*.puml'))
    if not sources:
        parser.error('No PlantUML sources found')
    command = [args.java, '-Djava.awt.headless=true', '-jar', str(args.jar.resolve()),
               '-charset', 'UTF-8', '-failfast2']
    subprocess.run([*command, '-checkonly', *map(str, sources)], check=True)
    subprocess.run([*command, '-tpng', *map(str, sources)], check=True)
    for source in sources:
        output = source.with_suffix('.png')
        if not output.is_file():
            raise RuntimeError(f'Missing output: {output}')
        print(output.relative_to(ROOT))

if __name__ == '__main__':
    main()
