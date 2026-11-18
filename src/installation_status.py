"""Report installation readiness without downloading or starting a model."""
import json
from pathlib import Path

from src.model_manager import ROOT, hardware, manifest, verify


def status(root=ROOT):
    root = Path(root)
    spec = manifest()['models']['qwen3-1.7b-q4']
    model = root / 'models' / spec['file']
    runtime = list((root / 'runtime').rglob('llama-server.exe'))
    return {
        'hardware': hardware(),
        'core_ready': (root / 'app.py').is_file(),
        'search_model_present': (root / 'models/embedding/astraeus-model-revision.txt').is_file(),
        'diagnosis_model_verified': verify(model, spec),
        'diagnosis_runtime_present': bool(runtime),
        'data_directory': str(root / 'data'),
    }


if __name__ == '__main__':
    print(json.dumps(status(), indent=2))
