"""Read-only connection to the pinned OotrR save tracker."""
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
import struct
from types import FunctionType

from .link_position import LinkPosition, read_link_position
from .save_discovery import SaveDirectory
from .save_profiles import local_tracker_dir
from .state import tracker_states
from .trigger_seed import trigger_flag_name

LEGACY_WORLD_FINGERPRINT = '9320b6448b1fb4af4bce35da746e3b593e4dd2c460ac1169d511723a312101e5'
BREAKABLE_SOURCES = {
    'beehives': ('Obj_Kokiri_Beehive_',),
    'bushes': ('Obj_Plant_Grass_',),
    'crates': ('Obj_BrokenBox_',),
    'pots': ('Obj_Pot_',),
    'rocks': ('Obj_BrokenRock_', 'Obj_LiftRock_'),
}
# These native song events are explicitly queried by the corresponding NPC
# flows. Other cutscenes may share a flow or run without triggering the check.
SONG_TRIGGER_EVENTS = {
    'song#Song from Impa': 'Dm_MelodyGet_Zelda',
    'song#Song from Malon': 'Dm_MelodyGet_Epona',
    'song#Song from Windmill': 'Dm_MelodyGet_Storm',
}


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
    link: LinkPosition | None = None
    save_path: Path | None = None


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


def source_break_flags(metadata):
    """Resolve registered destruction keys of shuffled physical sources."""
    known = set(metadata.get('known_bool64', ()))
    checks = metadata.get('checks', {})
    flags = {}
    for record in metadata.get('repeatables', ()):
        ident = record.get('id', '')
        _, _, suffix = ident.partition('#')
        category, _, key = suffix.partition('#')
        actors = BREAKABLE_SOURCES.get(category)
        variants = record.get('variants')
        if (actors and key in known and key.isdecimal() and record.get('kind') == 'pickup' and variants
                and all(v.get('source', '').startswith(actors) for v in variants)
                and checks.get(ident, {}).get('collection') == {'type': 'bool', 'hash': str(record.get('flag_hash'))}):
            flags[ident] = int(key)
    return flags


def event_trigger_flags(metadata, manifest):
    """Match proven native events with the seed's corresponding checks."""
    from oot_rando.patching.child_castle_skip import enabled as child_castle_skipped
    from oot_rando.patching.soul_adapter import murmur3

    skips = (manifest.get('skips') or {}).get('story_fixes', {})
    skip_impa = child_castle_skipped((manifest.get('settings') or {}).get('full')) or 'child_castle_start' in skips
    checks = metadata.get('checks', {})
    event_markers = metadata.get('event_markers', {})
    events = dict(SONG_TRIGGER_EVENTS)
    gift = skips.get('darunia_gift') or {}
    if gift.get('flag') == 'HavePlayedEvent.Dm_Goron_0030':
        events['npc#GC Darunias Joy'] = 'Dm_Goron_0030'
    flags = {}
    for ident, event in events.items():
        if ident == 'song#Song from Impa' and skip_impa:
            # The skip writes HavePlayedEvent before Link can visit Impa.
            continue
        collection = checks.get(ident, {}).get('collection')
        for suffix in ('.bfevfl.zs', '.110.bfevfl.zs'):
            markers = event_markers.get(f'Event/EventFlow/{event}{suffix}', ())
            if any(marker['flag'].endswith('.' + ident)
                   and collection == {'type': 'bool', 'hash': str(murmur3(marker['flag']))} for marker in markers):
                flags[ident] = murmur3(f'HavePlayedEvent.{event}')
                break
    return flags


def chest_opening_checks(metadata, manifest):
    from oot_rando.patching.soul_adapter import murmur3

    records = ((manifest.get('skips') or {}).get('chest_flags') or {}).get('records', ())
    checks = metadata.get('checks', {})
    return {record['id'] for record in records if record.get('flag')
            and checks.get(record['id'], {}).get('collection') == {'type': 'bool', 'hash': str(murmur3(record['flag']))}}


class SaveConnection:
    def __init__(self, seed_folder, save_path, store, *, preferred_save=None, manual_dir=None, live_factory=None):
        from oot_rando.tracker.auto_tracker import TrackerSession
        from oot_rando.tracker.manual_tracker import ManualTracker
        from oot_rando.tracker.live_memory import LiveGameData, SEQUENCE_IS_CHILDHOOD
        from oot_rando.formats.save_file import load_snapshot
        from oot_rando.patching.soul_adapter import murmur3
        from oot_rando.patching.story_fixes import KAKARIKO_MEDALS

        medallions = tuple(murmur3(name) for name in KAKARIKO_MEDALS)
        story_played = murmur3('HavePlayedEvent.Dm_Kakariko_0030')

        class MapSession(TrackerSession):
            # Reuse the accepted snapshot rather than reading progress.sav
            # twice. OotrR 0.8 invokes this only for a changed, matched save.
            age = None
            kakariko_burned = None
            broken_sources = frozenset()
            played_events = frozenset()
            instrumented_triggers = frozenset()

            def check_state(self, ident):
                state = super().check_state(ident)
                if not state['observed']:
                    if ident in self.broken_sources:
                        state.update(completed=True, source='source_break')
                    elif ident in self.played_events:
                        state.update(completed=True, source='event_played')
                    elif ident in self.instrumented_triggers:
                        state.update(completed=True, source='instrumented_trigger')
                if ident in self.manual.completed:
                    state['manual_confirmation'] = False
                elif not state['completed'] and ident in self.catalogue_ids and ident not in self.action_checks:
                    state['manual_confirmation'] = True
                return state

            def _get_logic(self):
                if (self._logic is not None or self._logic_error
                        or self.metadata.get('logic_world_sha256') != LEGACY_WORLD_FINGERPRINT
                        or not (graph := self.metadata.get('logic'))):
                    return super()._get_logic()
                from oot_rando.logic.rules import Logic
                from oot_rando.logic.world import World

                try:
                    world = World()
                    # The current base tables and evaluator are identical to 0.8.0.
                    # Revert the two remake rules on this seed's private world.
                    world.remake['exit_rules'].pop('Kakariko Village -> Kak Impas Ledge', None)
                    world.remake['events'].pop('GC Woods Warp', None)
                    if world.fingerprint() != LEGACY_WORLD_FINGERPRINT:
                        return super()._get_logic()
                    exits = {(a, b): set(items) for a, b, items in graph['exits']}
                    # OotrR's constructor reads three module-level tables.
                    # Give it this world's verified tables without changing
                    # the rules used by other sessions.
                    initialize = Logic.__init__
                    tables = dict(initialize.__globals__,
                                  REMAKE_EXIT_RULES=world.remake['exit_rules'],
                                  REMAKE_LOCATION_RULES=world.remake['location_rules'],
                                  REMAKE_LOCATION_REGIONS=world.remake['location_regions'])
                    initialize_legacy = FunctionType(initialize.__code__, tables,
                                                     argdefs=initialize.__defaults__)
                    logic = Logic.__new__(Logic)
                    initialize_legacy(logic, world, graph['settings'], exits, graph['locations'])
                    logic.virtual = graph['virtual']
                    self._logic = logic
                except (OSError, ValueError, KeyError, ImportError) as error:
                    self._logic_error = str(error)
                return self._logic

            def _availability(self, snapshot, metadata):
                native = snapshot['bool64'] if snapshot.get('bool64_complete') else {}
                self.broken_sources = {ident for ident, key in self.break_flags.items() if native.get(key) is True}
                flags = snapshot['bool']
                self.played_events = {ident for ident, key in self.event_flags.items() if flags.get(key) is True}
                self.instrumented_triggers = {ident for ident, key in self.trigger_flags.items()
                                              if flags.get(key) is True}
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
        self.session.break_flags = source_break_flags(self.session.metadata)
        self.session.event_flags = event_trigger_flags(self.session.metadata, self.session.manifest)
        self.session.action_checks = (self.session.break_flags.keys() | self.session.event_flags.keys()
                                      | chest_opening_checks(self.session.metadata, self.session.manifest))
        self.session.catalogue_ids = {row['id'] for row in self.session.checks}
        self.session.trigger_flags = {ident: key for ident, key in self.session.metadata.get('trigger_flags', {}).items()
                                      if ident in self.session.catalogue_ids and type(key) is int
                                      and key == murmur3(trigger_flag_name(ident))}
        self.ids = tuple(store.states)
        self.directory = manual_dir if manual_dir is not None else local_tracker_dir() / 'manual'
        self.manual_factory = ManualTracker
        self.live_factory = live_factory or LiveGameData
        self.selector = SaveDirectory(path, int(self.session.metadata['seed_marker']),
                                      load_snapshot) if path.is_dir() else None
        self.preferred_save = Path(preferred_save) if self.selector is not None and preferred_save else None
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

    def refresh(self, manual_changes=(), *, live=False, show_link=False):
        from oot_rando.tracker.live_memory import LiveUnavailable

        if self.selector is not None:
            watched = self.path or self.preferred_save
            path = self.selector.newest(current=watched)
            if path is None:
                self.close()
                return SaveUpdate('En attente d’un progress.sav lisible lié à cette seed.',
                                  reset=watched is None or self.selector.is_unlinked(watched),
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
                if ident not in self.ids or self.session.check_state(ident).get('manual_confirmation') is not checked:
                    raise ValueError('L’état actuel de ce check ne permet pas cette confirmation manuelle.')
                self.session.set_completed(ident, checked)
            except (OSError, ValueError) as error:
                action_error = str(error)
        position = None
        if show_link and realtime and self.session.live is not None:
            try:
                position = read_link_position(self.session.live.memory, self.session.age)
            except (LiveUnavailable, OSError, struct.error):
                pass
        return SaveUpdate(detail,
                          datetime.now(timezone.utc).isoformat(timespec='seconds'),
                          tracker_states(self.session, self.ids),
                          {ident: self.session.check_state(ident) for ident in self.ids},
                          action_error=action_error, age=self.session.age, mode='live' if realtime else 'save',
                          kakariko_burned=self.session.kakariko_burned, link=position, save_path=self.path)


def apply_save_update(store, update):
    if update.states is not None:
        store.publish(store.seed_id, update.states, mode=update.mode, timestamp=update.timestamp)
    elif update.reset:
        store.reset(store.seed_id, store.states)
    else:
        store.disconnect()
