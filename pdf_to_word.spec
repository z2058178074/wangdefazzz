# -*- mode: python ; coding: utf-8 -*-

from PyInstaller.utils.hooks import collect_all, collect_dynamic_libs


rapid_datas, rapid_binaries, rapid_hiddenimports = collect_all('rapidocr')
onnx_binaries = collect_dynamic_libs('onnxruntime')
pdfium_binaries = collect_dynamic_libs('pypdfium2')
opencv_binaries = collect_dynamic_libs('cv2')

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=rapid_binaries + onnx_binaries + pdfium_binaries + opencv_binaries,
    datas=rapid_datas + [('models/manifest.json', 'models')],
    hiddenimports=rapid_hiddenimports + [
        'cv2',
        'onnxruntime',
        'pdfplumber',
        'pypdfium2',
        'rapidocr',
    ],
    hookspath=[],
    runtime_hooks=[],
    excludes=['tkinter'],
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='PDF转Word',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    contents_directory='dependencies',
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name='PDF转Word-Windows',
)
