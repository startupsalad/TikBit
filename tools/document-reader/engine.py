#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
转换引擎层 —— 把 Office 文档转成 PDF / PNG，自动挑本机能用的引擎。

为什么要这一层：读 PPT、读带图表的 Excel 必须转成 PDF 才能"视觉读"，而转换得靠
办公软件。每台机器装的东西不一样（客户机常常只有 WPS，Mac 上两个都没有），所以
按保真度从高到低自动降级，别让脚本在客户机上直接死掉：

    1. Microsoft Office (COM)  保真度最高。Windows + 装了 Office
    2. WPS Office (COM)        国内客户机最常见，只有 WPS 也能干活
    3. LibreOffice (soffice)   跨平台，Mac / Linux 主力
    4. markitdown              纯文字兜底，丢版面只保内容（走 markitdown_text）

踩过的坑，都在代码里处理了：
    - WPS 的 Quit() 不一定真退，会留 wpp.exe / et.exe 常驻内存（实测 213MB）。
      本模块记下调用前的进程快照，只清"我们自己起的"，绝不按进程名一刀切 ——
      用户可能正开着 Word 编未保存的稿子。
    - 用 DispatchEx 而不是 Dispatch。Dispatch 会挂到用户已打开的实例上，我们
      Quit() 就把人家的文档一并关了。DispatchEx 强制起独立进程。
    - COM 不认正斜杠和相对路径，一律走 abs_win()。
    - 各家 COM 的 Open / 导出方法签名不完全一致，从严到宽逐个试。

本模块只做转换，不做内容解析。给 read_doc / read_excel / read_ppt / read.py 共用。
"""

import os
import shutil
import subprocess
import sys

IS_WIN = sys.platform.startswith('win')

# 每类文档对应的 COM ProgID 和进程名（MSO / WPS 各一套）
_SPEC = {
    'word': {'mso': 'Word.Application', 'wps': 'KWPS.Application',
             'exe': ('WINWORD.EXE', 'wps.exe')},
    'excel': {'mso': 'Excel.Application', 'wps': 'KET.Application',
              'exe': ('EXCEL.EXE', 'et.exe')},
    'ppt': {'mso': 'PowerPoint.Application', 'wps': 'KWPP.Application',
            'exe': ('POWERPNT.EXE', 'wpp.exe')},
}

# 扩展名 → 文档大类（含 WPS 自家格式 .wps/.et/.dps）
KIND_BY_EXT = {
    '.doc': 'word', '.docx': 'word', '.docm': 'word', '.rtf': 'word', '.wps': 'word',
    '.xls': 'excel', '.xlsx': 'excel', '.xlsm': 'excel', '.et': 'excel',
    '.ppt': 'ppt', '.pptx': 'ppt', '.pptm': 'ppt', '.dps': 'ppt',
}

# 导出 PDF 的格式常量（MSO 和 WPS 通用）
WD_FORMAT_PDF = 17   # wdExportFormatPDF / wdFormatPDF
XL_TYPE_PDF = 0      # xlTypePDF
PP_SAVE_AS_PDF = 32  # ppSaveAsPDF

PNG_W, PNG_H = 1920, 1080  # PNG 导出像素，够清晰看小字
ENGINE_ORDER = ('mso', 'wps', 'soffice')

def abs_win(path):
    """COM 不认正斜杠和相对路径，统一转成 Windows 绝对路径"""
    p = os.path.abspath(path)
    return p.replace('/', '\\') if IS_WIN else p


def _pids(names):
    """按进程名取 PID 集合。只用于比对前后快照，不做任何击杀决策。"""
    if not IS_WIN:
        return set()
    try:
        out = subprocess.run(['tasklist', '/FO', 'CSV', '/NH'],
                             capture_output=True, timeout=20).stdout.decode('utf-8', 'replace')
    except (OSError, subprocess.TimeoutExpired):
        return set()
    low = tuple(n.lower() for n in names)
    found = set()
    for line in out.splitlines():
        cols = line.split('","')
        if len(cols) < 2:
            continue
        if cols[0].strip('" ').lower() in low:
            pid = cols[1].strip('" ')
            if pid.isdigit():
                found.add(pid)
    return found


def _kill(pids):
    """只清传进来的 PID —— 即调用期间新冒出来的那些，不碰用户原有实例"""
    for pid in pids:
        try:
            subprocess.run(['taskkill', '/PID', pid, '/F'],
                           capture_output=True, timeout=20)
        except (OSError, subprocess.TimeoutExpired):
            pass


def _com_app(progid):
    """DispatchEx 起独立进程，绝不复用用户已打开的实例（否则 Quit 会关掉人家的稿子）"""
    import win32com.client
    app = win32com.client.DispatchEx(progid)
    for attr, val in (('Visible', False), ('DisplayAlerts', False)):
        try:
            setattr(app, attr, val)
        except Exception:
            pass  # PowerPoint 的 Visible 只读，忽略即可
    return app


def probe(kind, engine):
    """探本机某引擎能不能用。只给 检查环境.py 用（起 COM 慢，转换流程里不预探）。"""
    if engine == 'soffice':
        return find_soffice() is not None
    if not IS_WIN:
        return False
    spec = _SPEC.get(kind)
    if not spec or engine not in spec:
        return False
    before = _pids(spec['exe'])
    app = None
    try:
        app = _com_app(spec[engine])
        return True
    except Exception:
        return False
    finally:
        if app is not None:
            try:
                app.Quit()
            except Exception:
                pass
            del app
        _kill(_pids(spec['exe']) - before)


def find_soffice():
    """找 LibreOffice。Mac / Linux 的主力引擎，Windows 上也可能装了。"""
    exe = shutil.which('soffice') or shutil.which('libreoffice')
    if exe:
        return exe
    for p in (r'C:\Program Files\LibreOffice\program\soffice.exe',
              r'C:\Program Files (x86)\LibreOffice\program\soffice.exe',
              '/Applications/LibreOffice.app/Contents/MacOS/soffice'):
        if os.path.exists(p):
            return p
    return None


def out_path(src, new_ext, out=None):
    """
    默认把中间产物放系统临时目录，不往源目录（本库在微盘实时同步）拉屎。
    用固定子目录 docread/ 而非随机目录，方便反复读同一个转换结果。
    """
    if out:
        return abs_win(out)
    import tempfile
    d = os.path.join(tempfile.gettempdir(), 'docread')
    os.makedirs(d, exist_ok=True)
    base, ext = os.path.splitext(os.path.basename(src))
    # 名字里带上原扩展名：否则 方案.docx 和 方案.pptx 都转成 方案.pdf，后者静默盖掉前者
    tag = ext.lstrip('.').lower()
    return abs_win(os.path.join(d, f'{base}_{tag}{new_ext}' if tag else base + new_ext))


def _try(fns):
    """各家 COM 方法签名不统一，从严到宽逐个试；全挂了抛最后一个错"""
    err = None
    for fn in fns:
        try:
            return fn()
        except Exception as exc:
            err = exc
    raise err if err else RuntimeError('无可用调用方式')


def _com_to_pdf(kind, engine, src, out):
    """用 MSO / WPS 的 COM 接口导出 PDF。转换后清掉本次新起的进程。"""
    spec = _SPEC[kind]
    before = _pids(spec['exe'])
    app = doc = None
    try:
        app = _com_app(spec[engine])
        if kind == 'word':
            doc = _try([lambda: app.Documents.Open(src, ReadOnly=True),
                        lambda: app.Documents.Open(src)])
            _try([lambda: doc.ExportAsFixedFormat(out, WD_FORMAT_PDF),
                  lambda: doc.SaveAs(out, WD_FORMAT_PDF)])
        elif kind == 'excel':
            doc = _try([lambda: app.Workbooks.Open(src, ReadOnly=True),
                        lambda: app.Workbooks.Open(src)])
            doc.ExportAsFixedFormat(XL_TYPE_PDF, out)
        else:
            doc = _try([lambda: app.Presentations.Open(src, ReadOnly=True, WithWindow=False),
                        lambda: app.Presentations.Open(src, ReadOnly=True),
                        lambda: app.Presentations.Open(src)])
            _try([lambda: doc.SaveAs(out, PP_SAVE_AS_PDF),
                  lambda: doc.ExportAsFixedFormat(out, 2)])
        return out
    finally:
        if doc is not None:
            try:
                doc.Close(False) if kind != 'ppt' else doc.Close()
            except Exception:
                pass
            del doc
        if app is not None:
            try:
                app.Quit()
            except Exception:
                pass
            del app
        _kill(_pids(spec['exe']) - before)  # WPS 的 Quit 常不真退，收尾兜住


def _soffice_to_pdf(src, out):
    """LibreOffice 无头转换。它只认『输出目录』不认输出文件名，转完自己改名。"""
    exe = find_soffice()
    if not exe:
        raise RuntimeError('未找到 LibreOffice')
    outdir = os.path.dirname(out) or '.'
    os.makedirs(outdir, exist_ok=True)
    res = subprocess.run([exe, '--headless', '--norestore', '--convert-to', 'pdf',
                          '--outdir', outdir, src],
                         capture_output=True, timeout=300)
    made = os.path.join(outdir, os.path.splitext(os.path.basename(src))[0] + '.pdf')
    if not os.path.exists(made):
        raise RuntimeError('LibreOffice 未产出 PDF：'
                           + res.stderr.decode('utf-8', 'replace')[:200])
    if os.path.abspath(made) != os.path.abspath(out):
        shutil.move(made, out)
    return out


def office_to_pdf(src, out=None, prefer=None, verbose=True):
    """
    Office 文档 → PDF，按 MSO → WPS → LibreOffice 自动降级。
    返回 (pdf路径, 用了哪个引擎)。全挂了抛 RuntimeError 并列出各家的报错。
    """
    src = abs_win(src)
    if not os.path.exists(src):
        raise FileNotFoundError(f'文件不存在: {src}')
    kind = KIND_BY_EXT.get(os.path.splitext(src)[1].lower())
    if not kind:
        raise ValueError(f'不是 Office 文档: {os.path.splitext(src)[1]}')

    dst = out_path(src, '.pdf', out)
    order = list(ENGINE_ORDER)
    if prefer in order:                      # 显式指定的排到最前，仍保留后续降级
        order.remove(prefer)
        order.insert(0, prefer)

    errs = []
    for eng in order:
        if eng != 'soffice' and not IS_WIN:
            continue                         # COM 只有 Windows 有
        try:
            made = (_soffice_to_pdf(src, dst) if eng == 'soffice'
                    else _com_to_pdf(kind, eng, src, dst))
            if verbose:
                print(f'[引擎] {ENGINE_NAME[eng]}', file=sys.stderr)
            return made, eng
        except Exception as exc:
            errs.append(f'{ENGINE_NAME[eng]}: {type(exc).__name__} '
                        f'{str(exc).splitlines()[0][:110]}')
    raise RuntimeError('本机没有可用的转换引擎，逐个试过都失败了：\n  '
                       + '\n  '.join(errs)
                       + '\n装 Microsoft Office / WPS Office / LibreOffice 任一即可；'
                         '也可跑 检查环境.py 看本机情况。')


ENGINE_NAME = {'mso': 'Microsoft Office', 'wps': 'WPS Office', 'soffice': 'LibreOffice'}


def pdf_to_png(pdf, out_dir=None, dpi=150, pages=None):
    """
    PDF 逐页转 PNG（PyMuPDF），用于放大看细节。
    不走各家 COM 自己的导图接口 —— 那套三家签名全不一样，而 PDF 已经是统一中间态，
    从 PDF 栅格化还能自由控 dpi。
    """
    import fitz
    pdf = abs_win(pdf)
    if not out_dir:
        out_dir = os.path.splitext(pdf)[0] + '_pages'
    os.makedirs(out_dir, exist_ok=True)
    doc = fitz.open(pdf)
    made = []
    try:
        idx = pages if pages else range(len(doc))
        for i in idx:
            if i < 0 or i >= len(doc):
                continue
            png = os.path.join(out_dir, f'page{i + 1:02d}.png')
            doc[i].get_pixmap(dpi=dpi).save(png)
            made.append(png)
    finally:
        doc.close()
    return out_dir, made


def markitdown_text(src):
    """
    纯文字兜底：一个引擎都没有时至少把内容捞出来。丢版面、丢图，只保文字。
    别当默认路径用 —— PPT 的信息量大半在版面里。
    """
    from markitdown import MarkItDown
    return MarkItDown().convert(abs_win(src)).text_content


def take_opt(args, flag, cast=str, default=None):
    """从参数表里取 `--flag 值` 并就地删掉。没给就返回 default。"""
    if flag in args:
        i = args.index(flag)
        del args[i]
        if i < len(args) and not str(args[i]).startswith('--'):
            return cast(args.pop(i))
    return default


def take_flag(args, *flags):
    """从参数表里取开关（出现即 True）并就地删掉"""
    hit = any(f in args for f in flags)
    args[:] = [a for a in args if a not in flags]
    return hit


def clip(text, maxchars, flag='--maxchars'):
    """
    正文过长时截断，并**明确告知截断了多少、怎么看全**。

    为什么必须出声：静默丢内容 = AI 以为自己读完了，会拿半份材料下结论。
    标书/合同这种漏一行就出事的活，宁可让 AI 多跑一次也不能让它不知道有缺。
    照 read_excel.py 的 --maxrows / read_web.py 的 --limit 一个套路。

    maxchars 为 0 或 None 表示不截断。只用于打到 stdout 的场景；
    存档（--out）一律写全文，别在归档里留残缺副本。
    """
    if not maxchars or len(text) <= maxchars:
        return text
    return (text[:maxchars] +
            f'\n\n…（已截断，全文 {len(text)} 字，还剩 {len(text) - maxchars} 字未显示，'
            f'加 {flag} 0 看全）')


def fix_console():
    """Windows 控制台默认 GBK，遇到 emoji / 生僻字会 UnicodeEncodeError"""
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding='utf-8', errors='replace')
        except Exception:
            pass


if __name__ == '__main__':
    fix_console()
    print(__doc__)
    print(f'当前平台: {sys.platform}（COM 可用: {IS_WIN}）')
    print(f'LibreOffice: {find_soffice() or "未找到"}')
    print('\n本模块是给其他脚本调用的引擎层，直接读文档请跑 read.py 或 检查环境.py')
