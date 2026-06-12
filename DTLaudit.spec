# -*- mode: python ; coding: utf-8 -*-

import sys
from pathlib import Path

python_root = Path(sys.base_prefix)
tcl_root = python_root / 'tcl'
tcl_data = tcl_root / 'tcl8.6'
tk_data = tcl_root / 'tk8.6'
datas = []


def collect_tree(source, target):
    if not source.exists():
        return []
    collected = []
    for path in source.rglob('*'):
        if path.is_file():
            relative_parent = path.relative_to(source).parent
            collected.append((str(path), str(Path(target) / relative_parent)))
    return collected


datas += collect_tree(tcl_data, '_tcl_data')
datas += collect_tree(tk_data, '_tk_data')


a = Analysis(
    ['DTLaudit.py'],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=[
        '_tkinter',
        'tkinter',
        'tkinter.filedialog',
        'tkinter.messagebox',
        'tkinter.ttk',
    ],
    hookspath=['pyinstaller_hooks'],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='DTLaudit',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
