from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description='Run a hotspot scan using button-calibration.json')
    parser.add_argument('--group', required=True)
    parser.add_argument('--button', required=True)
    parser.add_argument('--label', required=True)
    parser.add_argument('--offsets', default='0:0,-12:0,12:0,0:-8,0:8')
    parser.add_argument('--delay', type=float, default=1.0)
    args = parser.parse_args()

    project_root = Path(__file__).resolve().parents[1]
    config_path = project_root / 'configs' / 'ui' / 'button-calibration.json'
    config = json.loads(config_path.read_text(encoding='utf-8-sig'))
    group = config[args.group]
    button = group['buttons'][args.button]
    point = button['point']

    cmd = [
        str(project_root / '.venv' / 'Scripts' / 'python.exe'),
        str(project_root / 'scripts' / 'scan_probe.py'),
        '--center-x', str(point[0]),
        '--center-y', str(point[1]),
        '--label', args.label,
        '--offsets', args.offsets,
        '--delay', str(args.delay),
    ]
    completed = subprocess.run(cmd, check=False)
    return int(completed.returncode)


if __name__ == '__main__':
    raise SystemExit(main())

