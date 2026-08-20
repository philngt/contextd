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
        'cmd_synapse',
        'cmd_contract_path',
        'cmd_migrate_config',
        'cmd_mcp_config',
        'cmd_doctor',
        'mcp_server',
        'render_runtime',
        'pack_loader',
        'lib.contextd_resolver',
        'lib.contextd_version',
        'lib.context_policy',
        'lib.context_security',
        'lib.find_engine',
        'lib.task_context_engine',
        'lib.synapse_engine',
        'lib.frontmatter',
        'lib.atomic_write',
        'lib.pack_validation',
        'lib.repetition',
        'lib.stdio',
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
