# Desktop tool distribution

`catalog.json` is the versioned machine-readable catalog used by TikBit Settings → More tools. `desktop-tools.json` declares the tools supported by direct installation. Rebuild with:

```powershell
python scripts/build-desktop-tools.py --ppt-core "<verified PPT core archive>"
```

All 18 catalog entries have an installation recipe. Every entry pins a package version, byte count, SHA-256, skill list and supported engines. ZIP files contain `manifest.json` plus only declared `skills/` files. The client verifies installed bytes, applies supported managed integrations transactionally and retains a recoverable previous version. User templates and accumulated memories are created only when missing. Existing rules and hooks are merged. Packages never execute remote setup scripts or include user credentials.

Schema 2 adds provider scope, readiness requirements, managed activation and seed templates. AI read-aloud is Claude-only; server deployment guides require the user's server and credentials, account tools require connection, and a new media team requires personalization. These are shown as setup states instead of false ready messages. Python-backed tools prepare a fixed dependency set through an existing workstation interpreter, in an isolated local package directory. Local models and browser login remain task-specific.

The PPT core is a verified external build input, not an incomplete README-only package. The resulting large ZIP is excluded from Git and must be attached to the exact GitHub Release URL listed in the catalog. Source assets, reference scripts and licenses are retained; a redundant nested Windows GPT-image installer and internal project memory are excluded. Private local user-path examples are replaced in public Markdown. Keep the source archive and generated release artifact intact until upload and remote hash verification.

Publish package files, including the PPT Release attachment, before publishing the matching catalog. Never overwrite a published version; update the tool's VERSION and generate a new package. Existing in-progress chats remain intact; “Use now” opens a fresh composer, while “Continue setup” starts a guided configuration chat. Both preserve the current draft and send nothing automatically. A new manifest schema or installer type requires a compatible plugin update; schema 2 must ship with its matching client.

After GitHub publication, synchronize every referenced package and the exact official catalog bytes to Shanghai OSS using `scripts/publish-desktop-tools.py`. It previews by default; `--apply --report <receipt.json>` verifies local artifacts, refuses immutable collisions, uploads packages with server-side overwrite protection, verifies public bytes, then publishes the catalog. Supported clients prefer the fixed OSS source and retain GitHub fallback; older clients keep their original behavior. See the root README for complete commands. Plugin releases must pass `node scripts/check-tool-distribution.mjs` before uploading.
