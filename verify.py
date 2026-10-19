"""Run the delivered algorithm checks without any earlier download or container path."""
from pathlib import Path
import importlib.util, shutil, subprocess, sys
ROOT=Path(__file__).resolve().parent
if not shutil.which('node'):
 raise SystemExit('Node.js is needed to test the same JavaScript engine used by the guide.')
if importlib.util.find_spec('networkx') is None:
 raise SystemExit('Install the testing dependency first: python -m pip install networkx')
for relative in ['tests/final','tests/algorithm_lessons','tests/simulations','tests/applications']:
 (ROOT/relative).mkdir(parents=True,exist_ok=True)
commands=[
 ['tests/simulations/validate_algorithms.py'],
 ['tests/check_algorithm_foundations.py'],
 ['code/run_checks.py','--cases','5000','--out','tests/final/proof_checks.json'],
 ['tests/applications/verify_examples.py'],
 ['tests/final/check_integrity.py'],
]
for args in commands:
 print('\nChecking '+args[0],flush=True)
 subprocess.run([sys.executable,*args],cwd=ROOT,check=True)
print('\nAll delivered algorithm and integrity checks passed. These are not runtime benchmarks.')
