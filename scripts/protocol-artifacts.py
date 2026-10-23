#!/usr/bin/env python3
"""Import an explicit clean TypeScript revision, or verify the pinned local snapshot."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess

ROOT = Path(__file__).resolve().parent.parent
PROTOCOL = ROOT / "protocol"


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def artifacts(directory):
    return {str(p.relative_to(directory)): digest(p)
            for p in sorted(directory.rglob("*")) if p.is_file() and p.name != "SOURCE.json"}


def verify():
    manifest = json.loads((PROTOCOL / "SOURCE.json").read_text())
    assert manifest["sourceRepository"] == "pi-sdk-typescript", "Unexpected protocol authority"
    assert re.fullmatch(r"[0-9a-f]{40}", manifest["sourceRevision"]), "Missing pinned source revision"
    assert manifest["files"] and artifacts(PROTOCOL) == manifest["files"], "Protocol snapshot drift"
    for target in (ROOT / "Sources/PiSDK/Contract").glob("*.schema.json"):
        assert target.read_bytes() == (PROTOCOL / "schema/v2" / target.name).read_bytes(), target
    assert (ROOT / "experiments/swift-generation/Sources/GeneratedModels.swift").read_bytes() == (PROTOCOL / "swift/GeneratedModels.swift").read_bytes(), "Generated Swift probe drift"
    print("Verified pinned protocol snapshot from", manifest["sourceRevision"])


def import_source(source):
    source = source.resolve()
    revision = subprocess.check_output(["git", "-C", str(source), "rev-parse", "HEAD"], text=True).strip()
    status = subprocess.check_output(["git", "-C", str(source), "status", "--porcelain"], text=True)
    assert not status.strip(), "Commit TypeScript changes before importing a pinned snapshot"
    assert (source / "src/protocol/v2.ts").is_file(), "Not a TypeScript SDK repository"
    incoming = source / "protocol"
    files = artifacts(incoming)
    assert "schema/v2/Request.schema.json" in files and "swift/GeneratedModels.swift" in files
    assert incoming.resolve() != PROTOCOL.resolve(), "Source and destination must differ"
    for directory in ("schema", "fixtures", "swift"):
        target = PROTOCOL / directory
        if target.exists():
            shutil.rmtree(target)
        shutil.copytree(incoming / directory, target)
    manifest = {"sourceRepository": "pi-sdk-typescript", "sourceRevision": revision, "files": files}
    (PROTOCOL / "SOURCE.json").write_text(json.dumps(manifest, indent=2) + "\n")
    for target in (ROOT / "Sources/PiSDK/Contract").glob("*.schema.json"):
        shutil.copyfile(PROTOCOL / "schema/v2" / target.name, target)
    shutil.copyfile(PROTOCOL / "swift/GeneratedModels.swift", ROOT / "experiments/swift-generation/Sources/GeneratedModels.swift")
    verify()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["check", "import"])
    parser.add_argument("source", type=Path, nargs="?")
    args = parser.parse_args()
    if args.action == "import":
        if args.source is None:
            parser.error("import requires an explicit TypeScript SDK repository path")
        import_source(args.source)
    else:
        if args.source is not None:
            parser.error("check uses the pinned local snapshot, not a sibling repository")
        verify()
