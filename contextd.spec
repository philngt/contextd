# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec for contextd CLI.

Build from repo root:
    python -m pip install .
    pyinstaller --clean contextd.spec

Output: dist/contextd (Linux/macOS) or dist/contextd.exe (Windows)
"""

from PyInstaller.utils.hooks import collect_data_files, copy_metadata

block_cipher = None

a = Analysis(
    ['scripts/frozen_entry.py'],
    pathex=[],
    binaries=[],
    datas=collect_data_files('contextd') + copy_metadata('philngt-contextd'),
    hiddenimports=[
        'contextd.cmd_resolve',
        'contextd.cmd_find',
        'contextd.cmd_bundle',
        'contextd.cmd_task_context',
        'contextd.cmd_synapse',
        'contextd.cmd_contract_path',
        'contextd.cmd_migrate_config',
        'contextd.cmd_mcp_config',
        'contextd.cmd_doctor',
        'contextd.mcp_server',
        'contextd.render_runtime',
        'contextd.pack_loader',
        'contextd.lib.contextd_resolver',
        'contextd.lib.contextd_version',
        'contextd.lib.context_policy',
        'contextd.lib.context_security',
        'contextd.lib.find_engine',
        'contextd.lib.task_context_engine',
        'contextd.lib.synapse_engine',
        'contextd.lib.frontmatter',
        'contextd.lib.atomic_write',
        'contextd.lib.pack_validation',
        'contextd.lib.repetition',
        'contextd.lib.runtime_resources',
        'contextd.lib.stdio',
        'contextd._version',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    # Legacy source-script branches must not collect unrelated generic packages.
    excludes=['scripts', 'lib', 'cmd_resolve', 'cmd_find', 'cmd_bundle',
              'cmd_task_context', 'cmd_synapse', 'cmd_contract_path',
              'cmd_migrate_config', 'cmd_mcp_config', 'cmd_doctor', 'cmd_explain',
              'cmd_eval', 'cmd_policy_check', 'cmd_pack_validate',
              'mcp_server', 'render_runtime', 'pack_loader', '_version'],
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
