import hashlib
import json
from pathlib import Path


FIXTURES_ROOT = Path(__file__).resolve().parent.parent / "fixtures"
MANIFEST_PATH = Path(__file__).resolve().parent.parent / "fixtures_manifest.json"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            digest.update(chunk)
    return digest.hexdigest()


def build_manifest():
    entries = []
    for path in sorted(FIXTURES_ROOT.rglob("*")):
        if path.is_file():
            entries.append(
                {
                    "path": str(path.relative_to(Path(__file__).resolve().parent.parent)),
                    "sha256": sha256_file(path),
                    "size": path.stat().st_size,
                }
            )
    return {"files": entries}


def main():
    manifest = build_manifest()
    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2) + "\n")
    print(f"Wrote manifest with {len(manifest['files'])} files to {MANIFEST_PATH}")


if __name__ == "__main__":
    main()
