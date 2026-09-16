# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=['utils', 'utils.colors', 'utils.config', 'utils.logger', 'modules', 'modules.restore', 'modules.cleanup', 'modules.disk', 'modules.network', 'modules.repair', 'modules.system', 'modules.security', 'modules.drivers', 'modules.apps', 'modules.power', 'modules.development', 'modules.tools', 'modules.reports', 'modules.advanced', 'modules.services'],
    hookspath=[],
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
    name='NV Optimizer',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
