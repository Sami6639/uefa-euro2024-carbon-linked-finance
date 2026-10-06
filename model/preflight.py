"""Inspect execution environment without computing scientific results."""
from pathlib import Path
import importlib.metadata
import json
import platform
import shutil
import sys

ROOT = Path(__file__).resolve().parents[1]

def preflight():
    packages = {p: importlib.metadata.version(p) for p in
                ['numpy', 'scipy', 'pandas', 'matplotlib', 'PyYAML']}
    return {'python': sys.version, 'platform': platform.platform(),
            'packages': packages, 'conda_executable': shutil.which('conda'),
            'execution_runtime': 'provided Python interpreter; not a Conda execution',
            'deterministic': True, 'random_seed': None,
            'random_seed_note': 'No stochastic computation is used.',
            'environment_definition': 'environment.yml',
            'conda_environment_validation': 'not executed; Conda absent in provided runtime',
            'scientific_execution_status': 'awaiting design lock',
            'raw_data_directory': 'data/raw',
            'data_acquisition_owned_by': 'separate acquisition scripts; never mutated by model'}

if __name__ == '__main__':
    out = ROOT / 'outputs' / 'preflight.json'
    out.write_text(json.dumps(preflight(), indent=2) + '\n', newline="\n")
    print(out)
