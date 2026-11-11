"""Build reproducible, declarative desktop tool packages without running installers."""
import argparse
import hashlib
import io
import json
from pathlib import Path
import re
import zipfile

ROOT = Path(__file__).resolve().parents[1]


def sha(data):
    return hashlib.sha256(data).hexdigest()


def collect(source):
    paths = sorted(source.rglob('*')) if source.is_dir() else [source]
    for file in paths:
        if file.is_symlink():
            raise ValueError(f'Symbolic link in source: {file.name}')
        if file.is_file():
            yield file, file.relative_to(source).as_posix() if source.is_dir() else file.name


def skill_text(name, description, body):
    return f'---\nname: {name}\ndescription: {json.dumps(description, ensure_ascii=False)}\n---\n\n{body}\n'.encode('utf-8')


def safe_name(value):
    parts = value.split('/')
    return not value.startswith('/') and '\\' not in value and all(p not in ('', '.', '..') for p in parts)


def archive_payload(archive_path, recipe):
    payload = {}
    with zipfile.ZipFile(archive_path) as archive:
        entries = [f for f in archive.infolist() if not f.is_dir()]
        for item in entries:
            if not safe_name(item.filename) or ((item.external_attr >> 16) & 0o170000) == 0o120000:
                raise ValueError('Unsafe source archive')
        skill_names = sorted({f.filename.split('/')[1] for f in entries if f.filename.startswith('skills/')})
        for item in entries:
            name = item.filename
            if any(part in {'.WeDrive', '.DS_Store', 'Thumbs.db', '__MACOSX', 'node_modules', '__pycache__', '.git'} for part in name.split('/')):
                continue
            # The nested Windows installer duplicates another independently maintained tool.
            if '分发包（给同事下载）' in name:
                continue
            if name.endswith('项目记忆.md'):
                continue
            data = archive.read(item)
            if name.lower().endswith(('.md', '.txt')):
                text = data.decode('utf-8-sig', errors='strict')
                text = re.sub(r'c:[\\/]users[\\/]administrator(?=[\\/]|$)', '<USER_HOME>', text, flags=re.I)
                data = text.encode('utf-8')
            if name.startswith('skills/'):
                payload[name] = data
            else:
                payload[f'skills/{skill_names[0]}/resources/{name}'] = data
        for name in skill_names:
            target = f'skills/{name}/SKILL.md'
            if target not in payload:
                candidates = [file for file in payload if file.startswith(f'skills/{name}/') and file.lower().endswith('/skill.md')]
                if len(candidates) != 1:
                    raise ValueError(f'Ambiguous nested skill entry: {name}')
                nested = candidates[0]
                relative = nested[len(f'skills/{name}/'):]
                payload[target] = skill_text(name, f'{name} presentation tools', f'Read `{relative}` for the complete original instructions. Its scripts and resources are retained at their original relative locations.')
            text = payload[target].decode('utf-8-sig').replace('\r\r\n', '\n').replace('\r\n', '\n')
            text = re.sub(r'^name:.*$', f'name: {name}', text, count=1, flags=re.M)
            payload[target] = text.encode('utf-8')
    return payload, [{'name': name} for name in skill_names]


def build(output, external_sources=None, tool_ids=None):
    external_sources = external_sources or {}
    recipes = json.loads((ROOT / 'desktop-tools.json').read_text(encoding='utf-8'))['tools']
    if tool_ids:
        unknown = set(tool_ids) - {recipe['id'] for recipe in recipes}
        if unknown:
            raise ValueError('Unknown tool IDs: ' + ', '.join(sorted(unknown)))
        recipes = [recipe for recipe in recipes if recipe['id'] in tool_ids]
    catalog = json.loads((ROOT / 'catalog.json').read_text(encoding='utf-8'))
    entries = {tool['id']: dict(tool) for tool in catalog['tools']}
    if tool_ids:
        previous = json.loads((ROOT / 'desktop/catalog.json').read_text(encoding='utf-8'))
        for entry in previous['tools']:
            if entry['id'] in entries and entry['id'] not in tool_ids:
                entries[entry['id']] = entry
    output.mkdir(parents=True, exist_ok=True)
    (output / 'packages').mkdir(exist_ok=True)
    for recipe in recipes:
        tool_id = recipe['id']
        source = ROOT / 'tools' / tool_id
        version = (source / 'VERSION').read_text(encoding='utf-8').strip()
        payload = {}
        if recipe.get('archive') or recipe.get('externalArchive'):
            archive = source / recipe['archive'] if recipe.get('archive') else external_sources.get(recipe['externalArchive'])
            if not archive or not Path(archive).is_file():
                raise ValueError(f'Provide the complete {tool_id} archive using --ppt-core; incomplete packages cannot be published')
            payload, skills = archive_payload(archive, recipe)
        else:
            skills = recipe.get('skills')
        if recipe.get('wrapper'):
            skills = [{'name': recipe['wrapper'], 'wrapper': recipe['wrapper']}]
        if skills is None:
            skills = [{'source': f'skills/{p.name}', 'name': p.name}
                      for p in sorted((source / recipe['skillDirectory']).iterdir()) if p.is_dir()]
        for skill in skills:
            name = skill['name']
            files = collect(source / skill['source']) if 'source' in skill else []
            if skill.get('wrapper'):
                payload[f'skills/{name}/SKILL.md'] = (ROOT / 'desktop-skills' / f'{name}.md').read_bytes()
            for file, relative in files:
                if relative.lower() == 'skill.md':
                    relative = 'SKILL.md'
                data = file.read_bytes()
                if relative == 'SKILL.md':
                    text = data.decode('utf-8-sig')
                    if not text.startswith('---') or not re.search(r'^name:\s*\S+', text, re.M):
                        raise ValueError(f'Missing skill metadata: {tool_id}/{name}')
                    if tool_id == 'html-page':
                        text = text.replace('.claude/design-systems/', 'resources/design-systems/')
                    elif tool_id == 'document-reader':
                        text = text.replace('{{工具包路径}}', './resources')
                        text = re.sub(r'^name:.*$', f'name: {name}', text, count=1, flags=re.M)
                    elif tool_id == 'gpt-image':
                        text = text.replace('~/.tikbit/gpt-image/gpt-image.js', './resources/gpt-image.js')
                        text = text.replace('<用户目录>/.tikbit/gpt-image/gpt-image.js', './resources/gpt-image.js')
                    elif recipe.get('id') not in ['writing-humanizer', 'web-design', 'ai-marketing']:
                        text = re.sub(r'^name:.*$', f'name: {name}', text, count=1, flags=re.M)
                    text += '\n\n## Installed resources\n\nRead bundled resources relative to this SKILL.md. This tool is installed for the current vault in both Claude and GPT.\n'
                    if recipe.get('resources'):
                        text += '\nReference files: ' + ', '.join(f'`resources/{r}`' for r in recipe['resources']) + '.\n'
                    data = text.encode('utf-8')
                payload[f'skills/{name}/{relative}'] = data
            for resource in recipe.get('resources', []):
                for file, relative in collect(source / resource):
                    if any(p in {'tests', '__pycache__', '.DS_Store', '.WeDrive'} for p in file.relative_to(source).parts):
                        continue
                    if resource == '.' and relative.startswith('skill/'):
                        continue
                    target = f'{resource}/{relative}' if (source / resource).is_dir() else resource
                    target = target.removeprefix('./')
                    payload[f'skills/{name}/resources/{target}'] = file.read_bytes()
            for license_file in sorted(source.glob('LICENSE*')):
                if license_file.is_file():
                    payload[f'skills/{name}/licenses/{license_file.name}'] = license_file.read_bytes()
            notices = ROOT / 'THIRD_PARTY_NOTICES.md'
            payload[f'skills/{name}/licenses/THIRD_PARTY_NOTICES.md'] = notices.read_bytes()
        seeds = []
        if recipe.get('seeds'):
            seed = recipe['seeds']
            for file, relative in collect(source / seed['source']):
                if any(relative == prefix or relative.startswith(prefix + '/') for prefix in seed.get('exclude', [])):
                    continue
                target = f'{seed["target"]}/{relative}'
                key = f'skills/{skills[0]["name"]}/seed/{target}'
                payload[key] = file.read_bytes()
                seeds.append({'source': key, 'target': target})
        if tool_id == 'ai-self-growth':
            for folder in ['成长大脑', '记忆模板']:
                for file, relative in collect(source / 'core' / folder):
                    key = f'skills/ai-self-growth/resources/core/{folder}/{relative}'
                    seeds.append({'source': key, 'target': f'🌱AI成长档案/{relative}'})
        if recipe.get('setup') in ['python', 'media', 'browser-login']:
            for skill in skills:
                name = skill['name']
                payload[f'skills/{name}/python.cjs'] = (ROOT / 'desktop-skills' / 'python-runner.cjs').read_bytes()
                key = f'skills/{name}/SKILL.md'
                payload[key] += b'\n\n## Managed Python runtime\n\nRun bundled Python scripts through `node python.cjs <script-path-relative-to-this-SKILL.md> [arguments]`. This launcher uses the prepared workstation interpreter and isolated tool dependencies. Resolve paths from this Skill directory; keep outputs in the user task folder. Do not use a different bare Python interpreter and then incorrectly report missing packages. Optional models and external login are prepared only for the requested task.\n'
        if tool_id == 'voice-notification':
            launcher = (ROOT / 'desktop-skills' / 'voice-runner.cjs').read_bytes()
            payload['skills/task-voice-notification/run.cjs'] = launcher
            for file, relative in collect(source / 'voice_clips'):
                payload[f'skills/task-voice-notification/resources/engine/voice_clips/{relative}'] = file.read_bytes()
        if tool_id == 'ai-voice-pack':
            key = 'skills/ai-voice-pack/resources/speak.js'
            text = payload[key].decode('utf-8').replace("path.join(HOME, '.claude', 'ss-speak')", '__dirname')
            payload[key] = text.encode('utf-8')
        schema = 2 if tool_id not in ['writing-humanizer', 'html-page', 'web-design', 'ai-marketing'] else 1
        manifest = {'schemaVersion': 1, 'id': tool_id, 'version': version,
                    'skills': [s['name'] for s in skills],
                    'files': [{'path': name, 'bytes': len(data), 'sha256': sha(data)}
                              for name, data in sorted(payload.items())]}
        if schema == 2:
            manifest.update({'schemaVersion': 2, 'providers': recipe.get('providers', ['claude', 'codex']),
                             'setup': recipe.get('setup', 'none'), 'integration': recipe.get('integration', 'none'), 'seeds': seeds})
        payload['manifest.json'] = json.dumps(manifest, ensure_ascii=False, separators=(',', ':')).encode('utf-8')
        name = f'{tool_id}-{version}.zip'
        package = output / 'packages' / name
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
            for file, data in sorted(payload.items()):
                info = zipfile.ZipInfo(file, date_time=(2026, 1, 1, 0, 0, 0))
                info.compress_type = zipfile.ZIP_DEFLATED
                info.external_attr = 0o100644 << 16
                archive.writestr(info, data)
        data = buffer.getvalue()
        if len(data) > 256 * 1024 * 1024 or sum(len(d) for d in payload.values()) > 512 * 1024 * 1024:
            raise ValueError(f'Package too large: {tool_id}')
        if package.exists() and package.read_bytes() != data:
            raise ValueError(f'Version already exists with different bytes; increase VERSION: {tool_id}/{version}')
        package.write_bytes(data)
        entry = entries[tool_id]
        entry['install'] = {'version': version, 'url': f'https://raw.githubusercontent.com/startupsalad/TikBit/main/desktop/packages/{name}',
                            'bytes': len(data), 'sha256': sha(data), 'skills': manifest['skills']}
        if schema == 2:
            entry['install'].update({'schemaVersion': 2, 'providers': manifest['providers'], 'setup': manifest['setup'], 'integration': manifest['integration']})
        if len(data) > 50 * 1024 * 1024:
            entry['install']['url'] = f'https://github.com/startupsalad/TikBit/releases/download/desktop-{tool_id}-{version}/{name}'
    clean = [{key: entry[key] for key in ['id', 'name', 'description', 'platforms', 'recommendation', 'install'] if key in entry}
             for entry in entries.values()]
    (output / 'catalog.json').write_text(json.dumps({'schemaVersion': 2, 'tools': clean}, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(f'Built {len(recipes)} installable tools; {len(clean)} catalog entries.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, default=ROOT / 'desktop')
    parser.add_argument('--ppt-core', type=Path)
    parser.add_argument('--tool', action='append', help='Rebuild only this tool and retain other published catalog entries')
    args = parser.parse_args()
    build(args.output.resolve(), {'ppt-core': args.ppt_core}, args.tool)
