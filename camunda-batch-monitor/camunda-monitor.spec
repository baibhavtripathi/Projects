# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for camunda-batch-monitor.
Builds a single self-contained .exe — no Python install required on target machine.
"""

block_cipher = None

a = Analysis(
    ['src/camunda_monitor/__main__.py'],
    pathex=['src'],
    binaries=[],
    datas=[
        # Bundle the .env.example template so users know what config keys are needed
        ('config/.env.example', 'config'),
    ],
    hiddenimports=[
        'camunda_monitor.config',
        'camunda_monitor.api',
        'camunda_monitor.notifier',
        'dotenv',
        'urllib3',
        'urllib3.util',
        'urllib3.util.retry',
        'charset_normalizer',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'tkinter',
        'unittest',
        'xml',
        'pydoc',
        'doctest',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='camunda-monitor',          # Output: dist/camunda-monitor.exe
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,                        # Compress with UPX if available (smaller file)
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,                    # Keep console window (needed to see print output)
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    onefile=True,                    # Single .exe — everything bundled in one file
)
