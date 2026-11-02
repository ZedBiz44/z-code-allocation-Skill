"""Build only the client runtime files; exclude tests and authoring tools."""
import hashlib
import json
from pathlib import Path
import shutil

root = Path(__file__).resolve().parents[1]
destination = root / 'dist' / 'z-code-allocation'
files = ['SKILL.md', 'agents/openai.yaml', 'scripts/request_z_code.mjs', 'scripts/request_z_code.py']
destination.mkdir(parents=True, exist_ok=True)
for path in destination.rglob('*'):
    if path.is_file() and path.relative_to(destination).as_posix() not in files:
        raise RuntimeError('Unexpected file in package; inspect before rebuilding: '+str(path))
for name in files:
    target = destination / name
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(root / name, target)
manifest = {name: hashlib.sha256((destination / name).read_bytes()).hexdigest() for name in files}
(root / 'dist' / 'package-sha256.json').write_text(json.dumps(manifest, indent=2)+'\n')
print(json.dumps({'package':str(destination), 'files':len(files)}))
