"""Remember verified save choices on this computer, separately from exported maps."""
import json
import os
from pathlib import Path
from tempfile import NamedTemporaryFile


def local_tracker_dir():
    if os.name == 'nt' and os.environ.get('LOCALAPPDATA'):
        return Path(os.environ['LOCALAPPDATA']) / 'Map-oot-rando'
    return Path.home() / '.local' / 'share' / 'Map-oot-rando'


class SaveProfiles:
    def __init__(self, path):
        self.path = Path(path)

    def _read(self):
        try:
            rows = json.loads(self.path.read_text(encoding='utf-8'))
            return rows if isinstance(rows, dict) else {}
        except (OSError, ValueError):
            return {}

    def get(self, seed_id, *, automatic=False):
        row = self._read().get(seed_id)
        if not isinstance(row, dict) or automatic and not row.get('resume'):
            return None
        folder, save = row.get('seed_folder'), row.get('save_path')
        if not isinstance(folder, str) or not isinstance(save, str):
            return None
        folder, save = Path(folder), Path(save)
        if folder.is_absolute() and save.is_absolute():
            return folder, save
        return None

    def remember(self, seed_id, folder, save):
        self._update(seed_id, {'seed_folder': str(Path(folder).resolve()),
                               'save_path': str(Path(save).resolve()), 'resume': True})

    def pause(self, seed_id):
        row = self._read().get(seed_id)
        if isinstance(row, dict) and row.get('resume'):
            self._update(seed_id, dict(row, resume=False))

    def _update(self, seed_id, row):
        if not seed_id:
            return
        profiles = self._read()
        profiles[seed_id] = row
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with NamedTemporaryFile(mode='w', encoding='utf-8', dir=self.path.parent,
                                prefix='profiles-', suffix='.tmp', delete=False) as stream:
            temporary = Path(stream.name)
            try:
                json.dump(profiles, stream, ensure_ascii=False, indent=2)
            except Exception:
                stream.close()
                temporary.unlink(missing_ok=True)
                raise
        try:
            temporary.replace(self.path)
        finally:
            temporary.unlink(missing_ok=True)
