"""Read-only connection to the pinned OotrR save tracker."""
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from .save_discovery import SaveDirectory
from .save_profiles import local_tracker_dir
from .state import tracker_states


@dataclass
class SaveUpdate:
    detail: str
    timestamp: str | None = None
    states: dict | None = None
    rows: dict | None = None
    reset: bool = False
    action_error: str = ''
    age: str | None = None
    mode: str = 'save'


class SaveConnection:
    def __init__(self, seed_folder, save_path, store, *, manual_dir=None, live_factory=None):
        from oot_rando.tracker.auto_tracker import TrackerSession
        from oot_rando.randomizer.randomizer_services import ManualTracker
        from oot_rando.tracker.live_memory import LiveGameData, SEQUENCE_IS_CHILDHOOD
        from oot_rando.tracker.save_reader import load_snapshot

        class MapSession(TrackerSession):
            # Reuse the accepted snapshot rather than reading progress.sav
            # twice. OotrR 0.8 invokes this only for a changed, matched save.
            age = None

            def _availability(self, snapshot, metadata):
                flag = snapshot['bool'].get(SEQUENCE_IS_CHILDHOOD)
                self.age = {True: 'Child', False: 'Adult'}.get(flag)
                return super()._availability(snapshot, metadata)

        path = Path(save_path).resolve()
        self.session = MapSession(seed_folder, str(path), live=None)
        if self.session.seed_id != store.seed_id:
            raise ValueError('Ce dossier de seed ne correspond pas à la carte.')
        if not self.session.metadata or not self.session.metadata.get('seed_marker'):
            raise ValueError('Cette seed OotrR ne contient pas de marqueur de suivi.')
        self.ids = tuple(store.states)
        self.directory = manual_dir if manual_dir is not None else local_tracker_dir() / 'manual'
        self.manual_factory = ManualTracker
        self.live_factory = live_factory or LiveGameData
        self.selector = SaveDirectory(path, int(self.session.metadata['seed_marker']),
                                      load_snapshot) if path.is_dir() else None
        self.path = None
        if self.selector is None:
            self._select(path)

    def _select(self, path):
        self.session.manual = self.manual_factory(self.directory, self.session.seed_id, str(path), self.ids)
        self.session.save_path = str(path)
        self.path = path

    def close(self):
        if self.session.live is not None:
            self.session.live.memory.close()
            self.session.live = None

    def refresh(self, manual_changes=(), *, live=False):
        if self.selector is not None:
            path = self.selector.newest()
            if path is None:
                self.close()
                return SaveUpdate('Aucun progress.sav lisible lié à cette seed dans le dossier.',
                                  reset=self.path is None,
                                  action_error='Aucune sauvegarde liée à cette seed.' if manual_changes else '')
            if path != self.path:
                self._select(path)
                changed_slot = bool(manual_changes)
                manual_changes = ()
            else:
                changed_slot = False
        else:
            changed_slot = False
        if live:
            if self.session.live is None:
                self.session.live = self.live_factory()
        else:
            self.close()
        summary = self.session.refresh()
        detail = summary['status']
        # TrackerSession's pinned refresh contract keeps updated_at during
        # transient errors and clears it for a save belonging to another seed.
        realtime = detail.startswith('Real time (game memory)')
        if not realtime and not detail.startswith('Synced with the latest save'):
            return SaveUpdate(detail, reset=not summary.get('updated_at'),
                              action_error='Synchronise la sauvegarde avant de cocher un check.'
                              if manual_changes else '')
        action_error = 'Le fichier de sauvegarde suivi a changé.' if changed_slot else ''
        for ident, checked in manual_changes:
            try:
                if ident not in self.ids or not self.session.check_state(ident)['untracked']:
                    raise ValueError('Ce check est suivi par la sauvegarde.')
                self.session.set_completed(ident, checked)
            except (OSError, ValueError) as error:
                action_error = str(error)
        return SaveUpdate(detail,
                          datetime.now(timezone.utc).isoformat(timespec='seconds'),
                          tracker_states(self.session, self.ids),
                          {ident: self.session.check_state(ident) for ident in self.ids},
                          action_error=action_error, age=self.session.age, mode='live' if realtime else 'save')


def apply_save_update(store, update):
    if update.states is not None:
        store.publish(store.seed_id, update.states, mode=update.mode, timestamp=update.timestamp)
    elif update.reset:
        store.reset(store.seed_id, store.states)
    else:
        store.disconnect()
