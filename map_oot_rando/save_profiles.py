"""Remember local tracking settings and verified save choices."""
import json
import os
from pathlib import Path
from tempfile import NamedTemporaryFile


def local_tracker_dir():
    if os.name == 'nt' and os.environ.get('LOCALAPPDATA'):
        return Path(os.environ['LOCALAPPDATA']) / 'Map-oot-rando'
    return Path.home() / '.local' / 'share' / 'Map-oot-rando'


def _read_json(path):
    try:
        rows = json.loads(path.read_text(encoding='utf-8'))
        return rows if isinstance(rows, dict) else {}
    except (OSError, ValueError):
        return {}


def _write_json(path, values):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with NamedTemporaryFile(mode='w', encoding='utf-8', dir=path.parent,
                                prefix=path.stem + '-', suffix='.tmp', delete=False) as stream:
            temporary = Path(stream.name)
            json.dump(values, stream, ensure_ascii=False, indent=2)
        temporary.replace(path)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


class SaveProfiles:
    def __init__(self, path):
        self.path = Path(path)
        self.tracking_settings = self.path.with_name('tracking-settings.json')

    def follow_link_enabled(self):
        return _read_json(self.tracking_settings).get('follow_link') is not False

    def remember_follow_link(self, enabled):
        settings = _read_json(self.tracking_settings)
        settings['follow_link'] = enabled
        _write_json(self.tracking_settings, settings)

    def get(self, seed_id, *, automatic=False):
        row = _read_json(self.path).get(seed_id)
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
        row = _read_json(self.path).get(seed_id)
        if isinstance(row, dict) and row.get('resume'):
            self._update(seed_id, dict(row, resume=False))

    def _update(self, seed_id, row):
        if not seed_id:
            return
        profiles = _read_json(self.path)
        profiles[seed_id] = row
        _write_json(self.path, profiles)
