from pathlib import Path
import yaml
def load_manifest(p=None):
    path = Path(p or Path(__file__).resolve().parents[1]/"plugin.yaml")
    return yaml.safe_load(open(path, "r", encoding="utf-8"))
