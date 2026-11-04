"""Read-only proxy snapshots. Raw values stay in a local capture session."""
import os
import platform
import subprocess


def _windows_snapshot():
    import ctypes
    from ctypes import wintypes

    class Config(ctypes.Structure):
        _fields_ = [('auto_detect', wintypes.BOOL), ('pac', ctypes.c_void_p),
                    ('proxy', ctypes.c_void_p), ('bypass', ctypes.c_void_p)]

    winhttp = ctypes.WinDLL('winhttp', use_last_error=True)
    query = winhttp.WinHttpGetIEProxyConfigForCurrentUser
    query.argtypes = [ctypes.POINTER(Config)]
    query.restype = wintypes.BOOL
    free = ctypes.WinDLL('kernel32', use_last_error=True).GlobalFree
    free.argtypes = [ctypes.c_void_p]
    free.restype = ctypes.c_void_p
    config = Config()
    if not query(ctypes.byref(config)):
        raise OSError(ctypes.get_last_error(), '无法读取当前用户WinINet代理')
    try:
        return {'auto_detect': bool(config.auto_detect),
                **{key: ctypes.wstring_at(getattr(config, key)) if getattr(config, key) else ''
                   for key in ('pac', 'proxy', 'bypass')}}
    finally:
        for key in ('pac', 'proxy', 'bypass'):
            if getattr(config, key):
                free(getattr(config, key))


def _mac_snapshot():
    def query(*args):
        result = subprocess.run(['networksetup', *args], capture_output=True,
                                text=True, timeout=15, env=dict(os.environ, LC_ALL='C'))
        if result.returncode:
            raise OSError('networksetup读取失败')
        return result.stdout.strip()

    listing = query('-listallnetworkservices').splitlines()
    services = [s for s in listing[1:] if s and not s.startswith('*')]
    if not services:
        raise OSError('未找到网络服务')
    return {service: {option: query(option, service) for option in
                     ('-getwebproxy', '-getsecurewebproxy', '-getautoproxyurl',
                      '-getproxyautodiscovery')} for service in services}


def snapshot():
    system = platform.system()
    try:
        if system == 'Windows':
            settings = _windows_snapshot()
        elif system == 'Darwin':
            settings = _mac_snapshot()
        else:
            return {'status': 'unknown', 'platform': system, 'reason': '此平台需人工核对代理'}
        return {'status': 'captured', 'platform': system, 'settings': settings}
    except (OSError, subprocess.SubprocessError) as error:
        return {'status': 'unknown', 'platform': system, 'reason': type(error).__name__}


def compare(before, after):
    """Return only a verdict; never echo addresses, PAC URLs or credentials."""
    scope = '当前用户WinINet（含自动检测/PAC）' if before.get('platform') == 'Windows' else '系统网络服务HTTP/HTTPS/PAC/自动发现'
    if (before.get('status') != 'captured' or after.get('status') != 'captured'
            or before.get('platform') != after.get('platform')):
        return {'status': 'unknown', 'scope': scope, 'note': '代理恢复待核对；未修改系统配置。'}
    restored = before['settings'] == after['settings']
    return {'status': 'restored' if restored else 'changed', 'scope': scope,
            'note': '与抓取前配置一致。' if restored else '与抓取前配置不同；关闭抓取并恢复原配置后重查。',
            'proxy_modified_by_tool': False}
