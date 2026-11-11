"""Verify desktop tool artifacts and publish packages before the OSS catalog."""
import argparse
import base64
import configparser
import email.utils
import hashlib
import hmac
import json
import os
from pathlib import Path
import re
import tempfile
import urllib.error
import urllib.parse
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
BASE = 'https://startupsalad-downloads.oss-cn-shanghai.aliyuncs.com/tikbit-tools/'
MAX_BYTES = 256 * 1024 * 1024


def sha(data):
    return hashlib.sha256(data).hexdigest()


def artifacts(directory):
    raw = (directory / 'catalog.json').read_bytes()
    if len(raw) > 512 * 1024:
        raise ValueError('Oversized catalog')
    catalog = json.loads(raw)
    if catalog.get('schemaVersion') not in (1, 2) or not isinstance(catalog.get('tools'), list):
        raise ValueError('Invalid catalog')
    result = []
    identifiers = set()
    for tool in catalog['tools']:
        tool_id = tool['id']
        if not re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*', tool_id) or tool_id in identifiers:
            raise ValueError('Invalid or duplicate tool id')
        identifiers.add(tool_id)
        info = tool.get('install')
        if not info:
            continue
        version = info['version']
        if not re.fullmatch(r'\d+\.\d+\.\d+(?:-[a-zA-Z0-9.-]+)?', version):
            raise ValueError('Invalid tool version')
        name = f'{tool_id}-{version}.zip'
        source = urllib.parse.urlsplit(info['url'])
        trusted = (source.hostname == 'raw.githubusercontent.com' and source.path == f'/startupsalad/TikBit/main/desktop/packages/{name}') or (
            source.hostname == 'github.com' and source.path.startswith('/startupsalad/TikBit/releases/download/') and source.path.endswith('/' + name))
        if not trusted or source.scheme != 'https' or source.username or source.password or source.port or source.query or source.fragment:
            raise ValueError('Untrusted package URL')
        file = directory / 'packages' / name
        if file.is_symlink() or not file.is_file() or not 0 < info['bytes'] <= MAX_BYTES or file.stat().st_size != info['bytes']:
            raise ValueError(f'Package integrity failure: {tool_id}')
        if not re.fullmatch(r'[0-9a-f]{64}', info['sha256']) or sha(file.read_bytes()) != info['sha256']:
            raise ValueError(f'Package integrity failure: {tool_id}')
        result.append((file, f'packages/{name}', info['bytes'], info['sha256']))
    if not result:
        raise ValueError('Empty tool distribution')
    return raw, result


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, request, fp, code, msg, headers, new_url):
        raise ValueError('Unexpected OSS redirect')


def read_remote(key, limit):
    request = urllib.request.Request(BASE + key, headers={'User-Agent': 'TikBit-Tools-Publisher', 'Accept-Encoding': 'identity', 'Cache-Control': 'no-cache'})
    try:
        with urllib.request.build_opener(NoRedirect()).open(request, timeout=60) as response:
            if response.status != 200 or response.headers.get('Content-Encoding', 'identity') != 'identity':
                raise ValueError('Invalid OSS response')
            if not response.headers.get('Last-Modified') or not response.headers.get('Content-Length'):
                raise ValueError('Missing OSS integrity headers')
            expected = int(response.headers['Content-Length'])
            if expected > limit:
                raise ValueError('Oversized OSS object')
            data = response.read(limit + 1)
            if len(data) != expected:
                raise ValueError('Incomplete OSS object')
            return data
    except urllib.error.HTTPError as error:
        if error.code == 404:
            return None
        raise


def published_catalog(local):
    url = 'https://api.github.com/repos/startupsalad/TikBit/contents/desktop/catalog.json?ref=main'
    request = urllib.request.Request(url, headers={'User-Agent': 'TikBit-Tools-Publisher', 'Accept': 'application/vnd.github+json'})
    with urllib.request.build_opener(NoRedirect()).open(request, timeout=30) as response:
        data = response.read(1024 * 1024 + 1)
        if response.status != 200 or len(data) > 1024 * 1024:
            raise ValueError('Official GitHub catalog unavailable')
    wrapper = json.loads(data)
    if wrapper.get('encoding') != 'base64' or not isinstance(wrapper.get('content'), str):
        raise ValueError('Invalid official GitHub catalog')
    raw = base64.b64decode(wrapper['content'])
    if len(raw) > 512 * 1024 or json.loads(raw) != json.loads(local):
        raise ValueError('Publish the matching GitHub catalog before OSS synchronization')
    return raw


def upload(file, key, immutable, oss_config):
    config = configparser.ConfigParser(interpolation=None)
    if not config.read(Path(oss_config).expanduser(), encoding='utf-8-sig'):
        raise ValueError('Existing OSS client configuration is required')
    values = config['Credentials']
    data = file.read_bytes()
    headers = {'Cache-Control': 'public,max-age=31536000,immutable' if immutable else 'no-cache',
               'Content-Type': 'application/json' if key.endswith('.json') else 'application/zip',
               'Date': email.utils.formatdate(usegmt=True), 'x-oss-meta-sha256': sha(data),
               'Content-MD5': base64.b64encode(hashlib.md5(data).digest()).decode('ascii')}
    if immutable:
        headers['x-oss-forbid-overwrite'] = 'true'
    if values.get('stsToken'):
        headers['x-oss-security-token'] = values['stsToken']
    canonical = ''.join(f'{name}:{headers[name]}\n' for name in sorted(headers) if name.startswith('x-oss-'))
    message = f"PUT\n{headers['Content-MD5']}\n{headers['Content-Type']}\n{headers['Date']}\n{canonical}/startupsalad-downloads/tikbit-tools/{key}"
    signature = base64.b64encode(hmac.new(values['accessKeySecret'].encode(), message.encode(), hashlib.sha1).digest()).decode('ascii')
    headers['Authorization'] = f"OSS {values['accessKeyID']}:{signature}"
    request = urllib.request.Request(BASE + key, data=data, headers=headers, method='PUT')
    try:
        with urllib.request.build_opener(NoRedirect()).open(request, timeout=600) as response:
            if response.status != 200:
                raise ValueError('Unexpected OSS upload response')
    except urllib.error.HTTPError as error:
        raise RuntimeError(f'OSS upload failed for {key}: HTTP {error.code}') from None


def publish(directory, apply=False, oss_config='~/.ossutilconfig', report=None):
    raw, packages = artifacts(directory)
    receipt = {'applied': apply, 'catalogSha256': sha(raw), 'packages': len(packages), 'bytes': sum(item[2] for item in packages)}
    if apply:
        canonical = published_catalog(raw)
        receipt['catalogSha256'] = sha(canonical)
        with tempfile.TemporaryDirectory(prefix='desktop-catalog-', dir=os.environ.get('TEMP')) as temporary:
            file = Path(temporary) / 'catalog.json'
            file.write_bytes(canonical)
            publish_artifacts(directory, raw, canonical, file, packages, oss_config, report)
    if report:
        report.write_text(json.dumps(receipt, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(receipt), flush=True)
    return receipt


def publish_artifacts(directory, local, raw, catalog_file, packages, oss_config, report):
    previous = read_remote('catalog.json', 512 * 1024)
    for file, key, size, digest in packages:
        existing = read_remote(key, MAX_BYTES)
        if existing is None:
            upload(file, key, True, oss_config)
            existing = read_remote(key, MAX_BYTES)
            if existing is None or len(existing) != size or sha(existing) != digest:
                raise ValueError(f'Package readback failed: {key}')
        elif len(existing) != size or sha(existing) != digest:
            raise ValueError(f'Immutable object differs: {key}; increase VERSION')
        print(json.dumps({'verified': key, 'bytes': size, 'sha256': digest}), flush=True)
    if (directory / 'catalog.json').read_bytes() != local:
        raise ValueError('Catalog changed during publication')
    frozen_key = f'catalogs/{sha(raw)}.json'
    frozen = read_remote(frozen_key, 512 * 1024)
    if frozen is None:
        upload(catalog_file, frozen_key, True, oss_config)
        frozen = read_remote(frozen_key, 512 * 1024)
    if frozen != raw:
        raise ValueError('Immutable catalog readback failed')
    current = read_remote('catalog.json', 512 * 1024)
    if current != previous and current != raw:
        raise ValueError('Concurrent catalog publication detected')
    if current != raw:
        if previous is not None:
            if report is None:
                raise ValueError('A report path is required to preserve the previous catalog')
            report.with_suffix('.previous-catalog.json').write_bytes(previous)
        upload(catalog_file, 'catalog.json', False, oss_config)
    if read_remote('catalog.json', 512 * 1024) != raw:
        raise ValueError('Catalog readback failed; preserve evidence before recovery')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--directory', type=Path, default=ROOT / 'desktop')
    parser.add_argument('--apply', action='store_true', help='Upload verified packages, then publish the catalog')
    parser.add_argument('--oss-config', default='~/.ossutilconfig', help='Existing local OSS credentials; never embedded in artifacts')
    parser.add_argument('--report', type=Path)
    args = parser.parse_args()
    publish(args.directory.resolve(), args.apply, args.oss_config, args.report)


if __name__ == '__main__':
    main()
