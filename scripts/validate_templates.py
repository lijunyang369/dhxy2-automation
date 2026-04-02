from __future__ import annotations

import json
from pathlib import Path

from src.perception import TemplateCatalog


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    catalog_path = root / "resources" / "templates" / "battle" / "catalog.json"
    catalog = TemplateCatalog.load(catalog_path)
    missing_files = catalog.missing_files()

    payload = {
        "catalog": str(catalog_path),
        "template_count": len(catalog.all()),
        "missing_count": len(missing_files),
        "missing_files": [str(path) for path in missing_files],
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 1 if missing_files else 0


if __name__ == "__main__":
    raise SystemExit(main())