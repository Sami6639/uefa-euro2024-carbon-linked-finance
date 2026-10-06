"""Capture provenance and software state after a completed runner."""
from pathlib import Path
import hashlib
import json
from datetime import datetime,timezone
from .preflight import preflight
ROOT=Path(__file__).resolve().parents[1]

def main():
    paths=[]
    for folder in ['model','tests','scripts','data','outputs','figures']:
        paths.extend((ROOT/folder).rglob('*'))
    paths += [ROOT/'requirements.txt',ROOT/'environment.yml',ROOT/'run_analysis.py',ROOT/'README.md',ROOT/'acquisition_requirements.txt',ROOT/'environment-acquisition.yml',ROOT/'THIRD_PARTY_DATA.md',ROOT/'.gitignore']
    rows=[]
    for path in sorted(set(paths)):
        if not path.is_file() or '__pycache__' in path.parts or path.name=='manifest.json':continue
        if path.suffix in ['.pyc']:continue
        rows.append({'path':str(path.relative_to(ROOT)),'bytes':path.stat().st_size,
                     'sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
    env=preflight();env['scientific_execution_status']='completed; validation_summary.json and test_report.json'
    manifest={'created_utc':datetime.now(timezone.utc).isoformat(),'environment':env,
       'scientific_design':'locked-2026-10-06-v1; zero-noise endpoint clarified during validation',
       'runner':'python run_analysis.py','artifacts':rows,
       'scope':'Hashes preserve local analytical version. No repository publication or third-party upload performed.',
       'interpretation_limitations':['This is an analytical contract-design study, not an empirical event-effects study.',
          'Noise and financing-gap domains are assumptions, not estimated uncertainty distributions.',
          'Exact source redistribution terms are not presumed; review source licences before public archiving.']}
    (ROOT/'outputs/manifest.json').write_text(json.dumps(manifest,indent=2)+'\n', newline="\n")
    print(f'Manifest: {len(rows)} files hashed.')

if __name__=='__main__':main()
