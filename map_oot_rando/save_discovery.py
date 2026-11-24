"""Find the newest verifiably matching progress.sav inside a chosen directory."""
import os
from pathlib import Path


class SaveDirectory:
    def __init__(self, directory, seed_marker, load_snapshot):
        self.directory = Path(directory)
        self.seed_marker = seed_marker
        self.load_snapshot = load_snapshot
        self._checked = {}
        self._deferred = None

    @staticmethod
    def _ordinary_dir(path):
        return not path.is_symlink() and not getattr(path, 'is_junction', lambda: False)()

    def is_unlinked(self, path):
        entry = self._checked.get(path)
        return entry is not None and not entry[1]

    def newest(self, *, current=None):
        candidates = []
        for folder, subdirs, files in os.walk(self.directory):
            # Stay in the selected directory. Do not traverse Windows junctions.
            subdirs[:] = [name for name in subdirs if self._ordinary_dir(Path(folder, name))]
            for name in files:
                if name.casefold() != 'progress.sav':
                    continue
                path = Path(folder, name)
                try:
                    if path.is_symlink() or self.directory not in path.resolve().parents:
                        continue
                    stat = path.stat()
                    if path.is_file():
                        candidates.append((stat.st_mtime_ns, stat.st_size, stat.st_ino, path))
                except (OSError, RuntimeError):
                    continue

        present = {path for _, _, _, path in candidates}
        self._checked = {path: stamp for path, stamp in self._checked.items() if path in present}
        for mtime, size, inode, path in sorted(candidates, reverse=True):
            stamp = (mtime, size, inode)
            if self._checked.get(path, (None,))[0] != stamp:
                self._checked.pop(path, None)
                try:
                    matches = self.load_snapshot(path)['bool'].get(self.seed_marker) is True
                except (OSError, ValueError):
                    # A write in progress may become valid without a new timestamp.
                    # Give the watched slot one retry before falling back to an older one.
                    if path == current and self._deferred != path:
                        self._deferred = path
                        return None
                    continue
                self._checked[path] = (stamp, matches)
            if self._checked[path][1]:
                self._deferred = None
                return path
        if self._deferred not in present:
            self._deferred = None
        return None
