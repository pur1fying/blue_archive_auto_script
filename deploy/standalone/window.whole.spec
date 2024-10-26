# -*- mode: python ; coding: utf-8 -*-

# This is a PyInstaller spec file for the window.py script.
# It is used to create a standalone executable for the Project.
# However, it is relatively huge to include all the dependencies.
# So we don't recommend using it in the project.

# Anyway, if using the spec script for building the executable,
# please move it to the root directory of the project.

a = Analysis(
    ['window.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='window',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='window',
)
