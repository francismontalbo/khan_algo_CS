"""Run the delivered algorithm checks and save fresh reports under output/ci."""
import argparse
import importlib.util
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parent


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out-dir', type=Path, default=ROOT / 'output/ci',
                        help='Directory for fresh JSON reports (default: output/ci).')
    args = parser.parse_args()
    if not shutil.which('node'):
        raise SystemExit('Node.js is needed to test the JavaScript engine used by the guide.')
    if importlib.util.find_spec('networkx') is None:
        raise SystemExit('Install the pinned testing dependency: python -m pip install -r requirements-dev.txt')
    out_dir = args.out_dir.resolve()
    commands = [
        ['tests/simulations/validate_algorithms.py', '--out', out_dir / 'simulations-checks.json'],
        ['tests/check_algorithm_foundations.py', '--out', out_dir / 'algorithm-lessons-checks.json'],
        ['code/run_checks.py', '--cases', '5000', '--out', out_dir / 'proof-checks.json'],
        ['tests/applications/verify_examples.py', '--out', out_dir / 'applications-checks.json'],
        ['tests/final/check_integrity.py', '--out', out_dir / 'integrity-checks.json'],
    ]
    for command in commands:
        print('\nChecking ' + command[0], flush=True)
        subprocess.run([sys.executable, *map(str, command)], cwd=ROOT, check=True)
    print(f'\nAll algorithm and integrity checks passed. Reports: {out_dir}')
    print('These are finite correctness checks, not runtime benchmarks.')


if __name__ == '__main__':
    main()
