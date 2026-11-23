"""Read-only connection to the pinned OotrR save tracker."""
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from .state import tracker_states


@dataclass
class SaveUpdate:
    detail: str
    timestamp: str | None = None
    states: dict | None = None
    rows: dict | None = None
    reset: bool = False


class SaveConnection:
    def __init__(self, seed_folder, save_path, store):
        from oot_rando.tracker.auto_tracker import TrackerSession

        path = Path(save_path).resolve()
        self.session = TrackerSession(seed_folder, str(path), save_path=str(path), live=None)
        if self.session.seed_id != store.seed_id:
            raise ValueError('Ce dossier de seed ne correspond pas à la carte.')
        if not self.session.metadata:
            raise ValueError('Cette seed OotrR ne contient pas de données de suivi.')
        self.ids = tuple(store.states)

    def refresh(self):
        summary = self.session.refresh()
        detail = summary['status']
        # TrackerSession's pinned refresh contract keeps updated_at during
        # transient errors and clears it for a save belonging to another seed.
        if not detail.startswith('Synced with the latest save'):
            return SaveUpdate(detail, reset=not summary.get('updated_at'))
        return SaveUpdate(detail,
                          datetime.now(timezone.utc).isoformat(timespec='seconds'),
                          tracker_states(self.session, self.ids),
                          {ident: self.session.check_state(ident) for ident in self.ids})


def apply_save_update(store, update):
    if update.states is not None:
        store.publish(store.seed_id, update.states, mode='save', timestamp=update.timestamp)
    elif update.reset:
        store.reset(store.seed_id, store.states)
    else:
        store.disconnect()
