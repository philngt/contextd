# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec for contextd CLI.

Build from repo root:
    pyinstaller --clean contextd.spec

Output: dist/contextd (Linux/macOS) or dist/contextd.exe (Windows)
"""

block_cipher = None

a = Analysis(
    ['scripts/cli.py'],
    pathex=[
        '.',
        'scripts',
        'scripts/lib',
    ],
    binaries=[],
    datas=[
        ('.contextd/manifest.json', '.contextd'),
    ],
    hiddenimports=[
        'cmd_resolve',
        'cmd_find',
        'cmd_bundle',
        'cmd_task_context',
        'cmd_contract_path',
        'cmd_migrate_config',
        'cmd_mcp_config',
        'mcp_server',
        'render_runtime',
        'pack_loader',
        'contextd_resolver',
        'find_engine',
        'task_context_engine',
        'atomic_write',
        'repetition',
        '_version',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
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
    name='contextd',
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
