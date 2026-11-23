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
    kakariko_burned: bool | None = None


def kakariko_variant(flags, medallions, story_played, uses_medallions):
    """Read the pinned release's scene condition from the accepted snapshot."""
    if uses_medallions:
        values = [flags.get(key) for key in medallions]
        if False in values:
            return False
        if all(value is True for value in values):
            return True
    # The burning event itself is proof for seeds with the original condition,
    # but an unplayed event alone does not tell us which scene has loaded.
    return True if flags.get(story_played) is True else None


class SaveConnection:
    def __init__(self, seed_folder, save_path, store, *, manual_dir=None, live_factory=None):
        from oot_rando.tracker.auto_tracker import TrackerSession
        from oot_rando.randomizer.randomizer_services import ManualTracker
        from oot_rando.tracker.live_memory import LiveGameData, SEQUENCE_IS_CHILDHOOD
        from oot_rando.tracker.save_reader import load_snapshot
        from oot_rando.patching.soul_adapter import murmur3
        from oot_rando.patching.story_fixes import KAKARIKO_MEDALS

        medallions = tuple(murmur3(name) for name in KAKARIKO_MEDALS)
        story_played = murmur3('HavePlayedEvent.Dm_Kakariko_0030')

        class MapSession(TrackerSession):
            # Reuse the accepted snapshot rather than reading progress.sav
            # twice. OotrR 0.8 invokes this only for a changed, matched save.
            age = None
            kakariko_burned = None

            def _availability(self, snapshot, metadata):
                flags = snapshot['bool']
                flag = flags.get(SEQUENCE_IS_CHILDHOOD)
                self.age = {True: 'Child', False: 'Adult'}.get(flag)
                patch = ((self.manifest.get('skips') or {}).get('story_fixes') or {}).get(
                    'kakariko_burning_medallions')
                self.kakariko_burned = kakariko_variant(flags, medallions, story_played, bool(patch))
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
                          action_error=action_error, age=self.session.age, mode='live' if realtime else 'save',
                          kakariko_burned=self.session.kakariko_burned)


def apply_save_update(store, update):
    if update.states is not None:
        store.publish(store.seed_id, update.states, mode=update.mode, timestamp=update.timestamp)
    elif update.reset:
        store.reset(store.seed_id, store.states)
    else:
        store.disconnect()
