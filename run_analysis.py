#!/usr/bin/env python3
"""One-command deterministic reproduction; never fetches or mutates raw data."""
from pathlib import Path
import io
import json
import os
import unittest
ROOT=Path(__file__).resolve().parent
os.chdir(ROOT)
os.environ.setdefault('MPLCONFIGDIR','/tmp/euro-finance-matplotlib')
os.environ.setdefault('XDG_CACHE_HOME','/tmp/euro-finance-cache')
os.environ.setdefault('OPENBLAS_NUM_THREADS','1')
os.environ.setdefault('OMP_NUM_THREADS','1')
from model.preflight import preflight
from model.generate_results import main as generate
from model.render_figures import main as figures
from model.write_manifest import main as manifest

(ROOT/'outputs').mkdir(exist_ok=True)
(ROOT/'outputs/preflight.json').write_text(json.dumps(preflight(),indent=2)+'\n', newline="\n")
log=io.StringIO()
suite=unittest.defaultTestLoader.discover(str(ROOT/'tests'))
r=unittest.TextTestRunner(stream=log,verbosity=2).run(suite)
(ROOT/'outputs/test_report.txt').write_text(log.getvalue(), newline="\n")
(ROOT/'outputs/test_report.json').write_text(json.dumps({'tests_run':r.testsRun,
  'failures':len(r.failures),'errors':len(r.errors),'skipped':len(r.skipped),
  'passed':r.wasSuccessful()},indent=2)+'\n', newline="\n")
print(log.getvalue())
if not r.wasSuccessful():raise SystemExit('Unit-test gate failed; analysis stopped.')
generate()
figures()
env=preflight();env['scientific_execution_status']='completed; all numerical checks passed'
(ROOT/'outputs/preflight.json').write_text(json.dumps(env,indent=2)+'\n', newline="\n")
manifest()
