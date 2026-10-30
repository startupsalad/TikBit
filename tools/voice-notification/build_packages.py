#!/usr/bin/env python3
"""Build local Windows/macOS TaskVoice packages. Never upload or replace releases."""
import argparse
import hashlib
import json
from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parent
TOP = "TikBit-TaskVoice"


def package(platform, output):
    suffix = "Windows" if platform == "windows" else "Mac"
    destination = output / ("TikBit-TaskVoice-" + suffix + ".zip")
    if destination.exists():
        raise ValueError("Refusing to overwrite existing package: " + str(destination))
    selected = []
    for name in ("INSTALL.md", "CHANGELOG.md", "VERSION", "install.py", "update.py", "给AI的安装指令.md", "📖 使用说明.md"):
        selected.append(ROOT / name)
    selected.append(ROOT / ("选择语音.bat" if platform == "windows" else "选择语音.command"))
    for path in (ROOT / "engine").iterdir():
        if path.suffix == ".py" or path.suffix == (".ps1" if platform == "windows" else ".sh"):
            selected.append(path)
    selected.extend(path for path in (ROOT / "voice_clips").rglob("*.mp3") if path.is_file())
    output.mkdir(parents=True, exist_ok=True)
    try:
        with zipfile.ZipFile(destination, "x", zipfile.ZIP_DEFLATED) as archive:
            for path in sorted(selected, key=lambda p: p.relative_to(ROOT).as_posix()):
                relative = path.relative_to(ROOT).as_posix()
                info = zipfile.ZipInfo(TOP + "/" + relative, date_time=(2026, 1, 1, 0, 0, 0))
                info.compress_type = zipfile.ZIP_DEFLATED
                info.create_system = 3
                mode = 0o755 if path.suffix in (".sh", ".command") else 0o644
                info.external_attr = (0o100000 | mode) << 16
                content = path.read_bytes()
                if platform == "macos" and path.suffix in (".sh", ".command") and b"\r\n" in content:
                    raise ValueError("Mac shell must use LF line endings: " + relative)
                archive.writestr(info, content)
        with zipfile.ZipFile(destination) as archive:
            if archive.testzip() is not None:
                raise ValueError("ZIP integrity failure")
            version = archive.read(TOP + "/VERSION").decode("utf-8-sig").strip()
    except Exception:
        destination.unlink(missing_ok=True)
        raise
    return {"platform": platform, "file": destination.name, "version": version, "bytes": destination.stat().st_size, "sha256": hashlib.sha256(destination.read_bytes()).hexdigest(), "entries": len(selected)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path, help="Local staging directory outside the source/vault")
    args = parser.parse_args()
    output = args.output.expanduser().resolve()
    if output == ROOT or ROOT in output.parents:
        parser.error("Output must be outside the tool source tree")
    manifest = [package(platform, output) for platform in ("windows", "macos")]
    (output / "taskvoice-manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
