"""Publish the patched source without credentials, local state or dependencies."""
from pathlib import Path
from zipfile import ZipFile, ZipInfo, ZIP_DEFLATED
from package import ROOT, game_files

files = set(game_files())
for name in ['README.md', 'package.json', 'package-lock.json', '.gitignore',
             'infra/alchemy.run.ts', 'infra/package.json', 'infra/package-lock.json',
             '.github/workflows/web.yml']:
    files.add(ROOT / name)
for directory, suffixes in [('web', {'.html', '.css', '.js'}),
                             ('scripts', {'.py', '.cjs'}), ('tests', {'.py', '.lua', '.cjs'})]:
    files.update(p for p in (ROOT / directory).iterdir()
                 if p.is_file() and not p.is_symlink() and p.suffix in suffixes)
destination = ROOT / 'dist/source.zip'
with ZipFile(destination, 'w', compression=ZIP_DEFLATED) as archive:
    for path in sorted(files):
        if path.is_symlink():
            raise ValueError(f'Refusing symlink: {path}')
        info = ZipInfo('notpacman/' + path.relative_to(ROOT).as_posix(), (2020, 1, 1, 0, 0, 0))
        info.create_system = 3
        info.external_attr = 0o100644 << 16
        info.compress_type = ZIP_DEFLATED
        archive.writestr(info, path.read_bytes())
print(f'Source archive: {len(files)} files')
