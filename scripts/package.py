"""Build a deterministic, allowlisted LÖVE archive (no tooling or saves)."""
from pathlib import Path
from zipfile import ZipFile, ZipInfo, ZIP_DEFLATED

ROOT = Path(__file__).resolve().parent.parent

def game_files(root=ROOT):
    files = [p for p in root.iterdir() if p.is_file() and not p.is_symlink() and not p.name.startswith('.')
             and (p.suffix in {'.lua'} or p.name == 'LICENSE.txt')]
    for directory, suffixes in [('graphics', {'.png'}), ('sounds', {'.ogg', '.wav'})]:
        files += [p for p in (root / directory).iterdir()
                  if p.is_file() and not p.is_symlink() and p.suffix in suffixes and not p.name.startswith('.')]
    return sorted(files, key=lambda p: p.relative_to(root).as_posix())

def package(destination=ROOT / 'build/notpacman.love'):
    destination.parent.mkdir(parents=True, exist_ok=True)
    with ZipFile(destination, 'w', compression=ZIP_DEFLATED) as archive:
        for path in game_files():
            info = ZipInfo(path.relative_to(ROOT).as_posix(), (2020, 1, 1, 0, 0, 0))
            info.create_system = 3
            info.external_attr = 0o100644 << 16
            info.compress_type = ZIP_DEFLATED
            archive.writestr(info, path.read_bytes())
    print(f'Packaged {len(game_files())} files: {destination}')

if __name__ == '__main__':
    package()
