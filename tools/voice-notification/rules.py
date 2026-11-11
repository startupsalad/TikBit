"""Merge task voice rules into the real client homes without replacing personal data."""
from datetime import datetime
import json
import os
from pathlib import Path
import tempfile

BEGIN = '<!-- TIKBIT-VOICE:BEGIN -->'
END = '<!-- TIKBIT-VOICE:END -->'


def client_homes(home, env, key, defaults):
    if env.get(key):
        root = Path(env[key]).expanduser()
        if not root.is_absolute():
            raise ValueError(key + ' must be absolute')
        roots = [root]
    else:
        roots = [home / item for item in defaults if (home / item).is_dir()]
        roots = roots or [home / defaults[0]]
    for root in roots:
        for current in [root, *root.parents]:
            if current.is_symlink() or (hasattr(current, 'is_junction') and current.is_junction()):
                raise ValueError('Linked client configuration directory')
    return roots


def instruction(voice_dir):
    directory = str(voice_dir).replace('\\', '/')
    if any(char in directory for char in ['"', '\n', '\r', '`', '$']):
        raise ValueError('Unsupported voice directory characters')
    command = ('powershell.exe -NoProfile -ExecutionPolicy Bypass -File "' + directory + '/notify-voice.ps1" -Mode'
               if os.name == 'nt' else 'bash "' + directory + '/notify-voice.sh"')
    return (BEGIN + '\n'
        'Only the visible main conversation may notify. Before final delivery, after all work and the final reply are ready, run `' + command + ' done` once. '
        'Before asking for authorization use `perm`; before asking for a choice or confirmation use `ask`, including optional questions, request_user_input and request_user_input_async; '
        'before waiting for login, verification codes or external human operations use `stuck`. Substitute the mode in the same command. '
        'One reminder per waiting point. Native dialogs owned by the TikBit notification integration announce themselves; do not manually repeat those reminders. '
        'Text-only questions still require an explicit ask. Do not announce ordinary Q&A, intermediate steps, recoverable errors, compaction or subagent completion. '
        'Never enable Stop-based done or flag/done-if-flagged. Preserve voice choice and exact visible-tab ownership; never guess a tab. '
        'Rules being written does not prove a running session has loaded them.\n' + END + '\n')


def rule_writes(voice_dir, home=None, env=None):
    home = Path.home() if home is None else Path(home)
    env = os.environ if env is None else env
    targets = [(root / 'CLAUDE.md') for root in client_homes(home, env, 'CLAUDE_CONFIG_DIR', ['.claude', '.tikbit/claude'])]
    targets += [(root / 'AGENTS.md') for root in client_homes(home, env, 'CODEX_HOME', ['.codex', '.tikbit/codex'])]
    writes = {}
    for target in targets:
        if target.is_symlink() or (target.exists() and (not target.is_file() or target.stat().st_size > 4 * 1024 * 1024)):
            raise ValueError('Unsafe client rule file')
        raw = target.read_bytes() if target.exists() else b''
        current = raw.decode('utf-8-sig')
        first, last = current.find(BEGIN), current.find(END)
        if current.count(BEGIN) != current.count(END) or current.count(BEGIN) > 1 or (first >= 0 and last < first):
            raise ValueError('Malformed managed task voice rule')
        block = instruction(voice_dir)
        next_text = (current[:first] + block.rstrip('\n') + current[last + len(END):]
                     if first >= 0 else current + ('\n' if current and not current.endswith('\n') else '') + '\n' + block)
        bom = b'\xef\xbb\xbf' if raw.startswith(b'\xef\xbb\xbf') else b''
        writes[target] = bom + next_text.encode('utf-8')
    return writes


def apply_rule_writes(writes, voice_dir, check=False):
    originals = {file: file.read_bytes() if file.exists() else None for file in writes}
    changed = [file for file, data in writes.items() if originals[file] != data]
    result = {'changed': [str(file) for file in changed], 'check_only': check}
    if check or not changed:
        return result
    backup = Path(voice_dir) / 'backups/rules' / datetime.now().strftime('%Y%m%d-%H%M%S-%f')
    backup.mkdir(parents=True, exist_ok=False)
    for index, file in enumerate(changed):
        if originals[file] is not None:
            (backup / str(index)).write_bytes(originals[file])
    (backup / 'files.json').write_text(json.dumps([str(file) for file in changed]), encoding='utf-8')
    completed = []
    try:
        for file in changed:
            file.parent.mkdir(parents=True, exist_ok=True)
            if (file.read_bytes() if file.exists() else None) != originals[file]:
                raise OSError('Client rules changed concurrently')
            fd, temporary = tempfile.mkstemp(prefix='.voice-rules-', dir=file.parent)
            try:
                with os.fdopen(fd, 'wb') as stream:
                    stream.write(writes[file])
                os.replace(temporary, file)
                completed.append(file)
            finally:
                Path(temporary).unlink(missing_ok=True)
    except Exception:
        for file in completed:
            if originals[file] is None:
                file.unlink(missing_ok=True)
            else:
                file.write_bytes(originals[file])
        raise
    result['backup'] = str(backup)
    return result
