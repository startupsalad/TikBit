#!/usr/bin/env python3
"""Update a public task-voice installation; preserve voices, hooks and private forks."""
import argparse
from datetime import datetime
import hashlib
import json
import os
from pathlib import Path
import shutil
import tempfile

ROOT = Path(__file__).resolve().parent
BANNERS = {"notify-voice.ps1": "# notify-voice.ps1 -- task voice notify engine (Windows)", "notify-voice.sh": "# notify-voice.sh -- task voice notify engine (macOS)"}


# Exact public 0.3.0 snapshots, normalized for LF/CRLF and UTF-8 BOM differences.
KNOWN_PUBLIC_HASHES = {'notify-voice.ps1': 'ee4fcdbf8770db5a64a8ff28cf4f45fa9b2186372d776163e5da245a67e5f85a', 'notify-voice.sh': 'dbfce3d6a910dd7f51dff5743ef810b214c23eb5500ff1b8e5d6453604dd0374'}

# Verified official OSS TaskVoice packages published on 2026-08-06.
KNOWN_OSS_20260806_HASHES = {
    "notify-voice.ps1": "d7fad07a81356d90a1d5a8447b9153165ed5216670e84aae6c8df9c1006cd3bd",
    "notify-voice.sh": "0d266c2c6a37ef330985577e9943e8e78984d03160d3c62107139efa2226f642",
}


def normalized_sha(raw):
    return hashlib.sha256(raw.decode("utf-8-sig").replace("\r\n", "\n").encode("utf-8")).hexdigest()


def installed_target(explicit=None):
    if explicit:
        return Path(explicit).expanduser().resolve()
    found = [p for p in (Path.home() / ".claude", Path.home() / ".task-voice") if any((p / n).is_file() for n in BANNERS)]
    if len(found) != 1:
        raise ValueError("Need exactly one public installation, or specify --target explicitly.")
    return found[0]


def update(target, check=False):
    if not target.is_dir():
        raise ValueError("Target must be an existing installation directory; use the install guide for first install.")
    if target.resolve() == (ROOT / "engine").resolve():
        raise ValueError("Refusing to update the source engine directory.")
    installed = [name for name in BANNERS if (target / name).is_file()]
    if not installed:
        raise ValueError("No installed voice engine found.")
    for name in installed:
        installed_bytes = (target / name).read_bytes()
        known = {KNOWN_PUBLIC_HASHES[name], KNOWN_OSS_20260806_HASHES[name], normalized_sha((ROOT / "engine" / name).read_bytes())}
        if BANNERS[name] not in installed_bytes.decode("utf-8-sig")[:500] or normalized_sha(installed_bytes) not in known:
            raise ValueError("Custom/private or unsupported old engine detected: " + name + "; refusing to overwrite. Merge manually after backup.")
    names = installed + ["VERSION"]
    sources = {name: (ROOT / "VERSION" if name == "VERSION" else ROOT / "engine" / name) for name in names}
    changed = [name for name in names if not (target / name).is_file() or (target / name).read_bytes() != sources[name].read_bytes()]
    result = {"version": (ROOT / "VERSION").read_text(encoding="utf-8-sig").strip(), "changed": changed, "check_only": check, "preserves": ["choice.txt", "voice_clips", "hooks", ".flag"]}
    if check or not changed:
        return result
    # Tiny script-only backup; no conversation history, tokens or settings copied.
    backup = target / "backups/voice-notification" / datetime.now().strftime("%Y%m%d-%H%M%S-%f")
    backup.mkdir(parents=True, exist_ok=False)
    metadata = {"version": result["version"], "files": {}}
    for name in changed:
        old = target / name
        metadata["files"][name] = {"existed": old.is_file()}
        if old.is_file():
            shutil.copy2(old, backup / name)
            metadata["files"][name]["sha256"] = hashlib.sha256(old.read_bytes()).hexdigest()
    (backup / "backup.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    completed = []
    temporary = []
    try:
        for name in changed:
            fd, staging = tempfile.mkstemp(prefix=".voice-update-", dir=target)
            temporary.append(Path(staging))
            with os.fdopen(fd, "wb") as f:
                f.write(sources[name].read_bytes())
            shutil.copymode(sources[name], staging)
            os.replace(staging, target / name)
            completed.append(name)
    except Exception:
        for name in completed:
            if metadata["files"][name]["existed"]:
                shutil.copy2(backup / name, target / name)
            else:
                (target / name).unlink(missing_ok=True)
        raise
    finally:
        for file in temporary:
            file.unlink(missing_ok=True)
    result["backup"] = str(backup)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target", help="Installed directory, not the source package")
    parser.add_argument("--check", action="store_true", help="Read-only inspection; no backup or write")
    args = parser.parse_args()
    try:
        result = update(installed_target(args.target), args.check)
    except (ValueError, OSError) as exc:
        parser.exit(1, "Update refused: " + str(exc) + "\n")
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
