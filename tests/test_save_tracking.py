"""Exercise the pinned tracker on a minimal synthetic seed and binary save."""
import hashlib
from importlib.util import find_spec
import json
from pathlib import Path
import struct
import tempfile
import unittest

from map_oot_rando.save_tracking import LEGACY_WORLD_FINGERPRINT, SaveConnection, apply_save_update, kakariko_variant
from map_oot_rando.state import StateStore


class VillageVariantTests(unittest.TestCase):
    def test_partial_inventory_and_original_story_state(self):
        keys = (1, 2, 3)
        self.assertIsNone(kakariko_variant({1: True, 2: True}, keys, 4, True))
        self.assertFalse(kakariko_variant({1: True, 2: True, 3: False}, keys, 4, True))
        self.assertTrue(kakariko_variant({1: True, 2: True, 3: True}, keys, 4, True))
        self.assertIsNone(kakariko_variant({1: True, 2: True, 3: True}, keys, 4, False))
        self.assertTrue(kakariko_variant({4: True}, keys, 4, False))


def write_seed(root, *, legacy_world=False, app_version=None, open_forest=False):
    from oot_rando.patching.randomize_kokiri import BUILD, TITLE
    from oot_rando.randomizer.randomizer_core import (
        ADAPTER_VERSION, GENERATOR_VERSION, Settings, settings_identity,
    )

    from oot_rando.logic.world import World

    settings = Settings('Synthetic Kokiri test')
    generator = '0.12.8' if legacy_world else GENERATOR_VERSION
    seed_id = settings_identity(settings, generator, ADAPTER_VERSION)
    chest = 'ap#KF Kokiri Sword Chest'
    impa = 'ap#Kak Impas House Freestanding PoH'
    checks = [{'id': ident, 'name': ident, 'region': 'Kokiri Forest'} for ident in ('test', chest, impa)]
    tracking = dict(schema_version=1, seed_id=seed_id, seed_marker='100', inventory=[{'item': 'Bomb Bag', 'hash': '101'}],
                    logic_world_sha256=LEGACY_WORLD_FINGERPRINT if legacy_world else World().fingerprint(),
                    logic={'settings': {'open_forest': 'open'} if open_forest else {}, 'exits': [], 'virtual': {},
                           'locations': {'KF Kokiri Sword Chest': ['Bomb Bag']}},
                    known_bool64=['42'], checks={'test': {
                        'collection': {'type': 'bool64', 'hash': '42'}, 'reward': 'Test item'}, chest: {}, impa: {}})
    payload = json.dumps(tracking).encode()
    data = b'synthetic resource'
    manifest = dict(schema_version=1, title_id=TITLE, build_id=BUILD, seed_id=seed_id,
                    settings=settings.to_dict(), generator_version=generator, app_version=app_version,
                    adapter_version=ADAPTER_VERSION,
                    tracking={'sha256': hashlib.sha256(payload).hexdigest()},
                    files={'fixture': {'size': len(data), 'sha256': hashlib.sha256(data).hexdigest()}})
    (root / 'romfs').mkdir()
    (root / 'romfs' / 'fixture').write_bytes(data)
    (root / 'checks.json').write_text(json.dumps({'seed_id': seed_id, 'checks': checks}), encoding='utf-8')
    (root / 'tracking.json').write_bytes(payload)
    (root / 'manifest.json').write_text(json.dumps(manifest), encoding='utf-8')
    return seed_id


def write_save(path, *, linked=True, collected=False, bombs=False, child=None):
    from oot_rando.tracker.save_reader import FORMAT_VERSION, MAGIC, PROGRESS_TYPE_HASH

    from oot_rando.tracker.live_memory import SEQUENCE_IS_CHILDHOOD

    end = 32 + 8 * (36 + (child is not None))
    header = struct.pack('<III', MAGIC, FORMAT_VERSION, end) + bytes(20)
    table = struct.pack('<IIIIII', 0, 0, 100, int(linked), 101, int(bombs))
    if child is not None:
        table += struct.pack('<II', SEQUENCE_IS_CHILDHOOD, int(child))
    table += b''.join(struct.pack('<II', 0, section) for section in range(1, 33))
    table += struct.pack('<II', PROGRESS_TYPE_HASH, end)
    sparse = struct.pack('<Q', 42) if collected else b''
    path.write_bytes(header + table + sparse + bytes(8))


@unittest.skipUnless(find_spec('oot_rando'), 'Pinned OotrR sources not on PYTHONPATH')
class SaveTrackingTests(unittest.TestCase):
    def test_preserves_both_logic_versions_independent_of_the_app_release(self):
        from oot_rando.logic.world import World

        ident = 'ap#KF Kokiri Sword Chest'
        runtime_fingerprint = World().fingerprint()
        for legacy in (True, False):
            with self.subTest(legacy=legacy), tempfile.TemporaryDirectory() as directory:
                folder = Path(directory)
                save = folder / 'progress.sav'
                store = StateStore(write_seed(folder, legacy_world=legacy, app_version='0.8.99'), [ident])
                write_save(save)
                session = SaveConnection(folder, save, store, manual_dir=folder / 'manual')
                self.assertEqual(session.refresh().states[ident], 'blocked')
                write_save(save, bombs=True)
                self.assertEqual(session.refresh().states[ident], 'available')
                self.assertEqual(World().fingerprint(), runtime_fingerprint)

    def test_legacy_seed_keeps_the_original_approach_to_impas_house(self):
        from oot_rando.logic.world import World

        ident = 'ap#Kak Impas House Freestanding PoH'
        current = World().fingerprint() != LEGACY_WORLD_FINGERPRINT
        for legacy in (True, False):
            with self.subTest(legacy=legacy), tempfile.TemporaryDirectory() as directory:
                folder = Path(directory)
                save = folder / 'progress.sav'
                store = StateStore(write_seed(folder, legacy_world=legacy, open_forest=True), [ident])
                write_save(save, child=True)
                session = SaveConnection(folder, save, store, manual_dir=folder / 'manual')
                expected = 'unknown' if current and not legacy else 'available'
                self.assertEqual(session.refresh().states[ident], expected)

    def test_real_tracker_collection_rollback_disconnect_and_seed_mismatch(self):
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            save = folder / 'progress.sav'
            store = StateStore(write_seed(folder), ['test', 'ap#KF Kokiri Sword Chest'])
            connection = SaveConnection(folder, save, store)
            write_save(save, child=True)
            first = connection.refresh()
            self.assertEqual(first.age, 'Child')
            apply_save_update(store, first)
            self.assertEqual(store.states['test'], 'unknown')
            self.assertEqual(store.states['ap#KF Kokiri Sword Chest'], 'blocked')
            write_save(save, collected=True, bombs=True, child=False)
            good = connection.refresh()
            self.assertEqual(good.age, 'Adult')
            self.assertEqual(connection.refresh().age, 'Adult')
            apply_save_update(store, good)
            self.assertEqual(store.states['test'], 'completed')
            self.assertEqual(store.states['ap#KF Kokiri Sword Chest'], 'available')
            self.assertEqual(good.rows['test']['reward'], 'Test item')
            contents = save.read_bytes()
            save.unlink()
            apply_save_update(store, connection.refresh())
            self.assertEqual(store.connection, 'disconnected')
            self.assertEqual(store.states['test'], 'completed')
            save.write_bytes(contents)
            apply_save_update(store, connection.refresh())
            self.assertEqual(store.connection, 'save')
            self.assertEqual(save.read_bytes(), contents)
            write_save(save)
            apply_save_update(store, connection.refresh())
            self.assertEqual(store.states['test'], 'unknown')
            write_save(save, collected=True)
            apply_save_update(store, connection.refresh())
            write_save(save, linked=False, collected=True)
            apply_save_update(store, connection.refresh())
            self.assertEqual(store.states['test'], 'unknown')
            self.assertIsNone(store.last_success)

    def test_manual_mark_is_for_untracked_checks_and_isolated_by_save(self):
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            save, second = folder / 'progress.sav', folder / 'second.sav'
            manual = folder / 'app-data'
            untracked = 'ap#KF Kokiri Sword Chest'
            store = StateStore(write_seed(folder), ['test', untracked])
            write_save(save)
            write_save(second)
            before = save.read_bytes()
            connection = SaveConnection(folder, save, store, manual_dir=manual)
            result = connection.refresh([(untracked, True), ('test', True)])
            self.assertEqual(result.states[untracked], 'completed')
            self.assertEqual(result.states['test'], 'unknown')
            self.assertEqual(result.rows[untracked]['source'], 'manual')
            self.assertEqual(result.rows[untracked]['reward'], '')
            self.assertIn('suivi par la sauvegarde', result.action_error)
            reopened = SaveConnection(folder, save, store, manual_dir=manual)
            self.assertEqual(reopened.refresh().states[untracked], 'completed')
            another = SaveConnection(folder, second, store, manual_dir=manual)
            self.assertEqual(another.refresh().states[untracked], 'blocked')
            self.assertEqual(reopened.refresh([(untracked, False)]).states[untracked], 'blocked')
            self.assertEqual(save.read_bytes(), before)
            write_save(save, linked=False)
            denied = reopened.refresh([(untracked, True)])
            self.assertTrue(denied.action_error)
            write_save(save)
            self.assertEqual(reopened.refresh().states[untracked], 'blocked')

    def test_folder_prefers_newest_readable_matching_save_and_follows_updates(self):
        import os

        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory).resolve()
            store = StateStore(write_seed(folder), ['test'])
            root = folder / 'saves'
            paths = [root / str(i) / 'progress.sav' for i in range(4)]
            for path in paths:
                path.parent.mkdir(parents=True)
            write_save(paths[0])
            write_save(paths[1], collected=True)
            write_save(paths[2], linked=False, collected=True)
            paths[3].write_bytes(b'truncated')
            for i, path in enumerate(paths):
                os.utime(path, ns=(1_700_000_000_000_000_000 + i*10**9,) * 2)
            conn = SaveConnection(folder, root, store)
            self.assertEqual(conn.refresh().states['test'], 'completed')
            self.assertEqual(conn.path, paths[1])
            os.utime(paths[0], ns=(1_700_000_010_000_000_000,) * 2)
            self.assertEqual(conn.refresh().states['test'], 'unknown')
            self.assertEqual(conn.path, paths[0])

    def test_pending_manual_mark_is_rejected_when_discovery_switches_slots(self):
        import os

        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory).resolve()
            seed_id = write_seed(folder)
            check = 'ap#KF Kokiri Sword Chest'
            root = folder / 'saves'
            first, second = (root / slot / 'progress.sav' for slot in ('first', 'second'))
            for path, mtime in ((first, 1_700_000_001), (second, 1_700_000_000)):
                path.parent.mkdir(parents=True)
                write_save(path)
                os.utime(path, (mtime, mtime))
            connection = SaveConnection(folder, root, StateStore(seed_id, [check]), manual_dir=folder / 'manual')
            self.assertEqual(connection.refresh().save_path, first)
            self.assertEqual(connection.refresh([(check, True)]).states[check], 'completed')

            os.utime(second, (1_700_000_002,) * 2)
            update = connection.refresh([(check, True)])
            self.assertEqual(update.save_path, second)
            self.assertEqual(update.states[check], 'blocked')
            self.assertIn('fichier de sauvegarde suivi a changé', update.action_error)
            os.utime(first, (1_700_000_003,) * 2)
            self.assertEqual(connection.refresh().states[check], 'completed')

    def test_temporary_rewrite_of_selected_slot_keeps_the_last_snapshot(self):
        import os

        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory).resolve()
            store = StateStore(write_seed(folder), ['test'])
            root = folder / 'saves'
            older = root / 'older' / 'progress.sav'
            current = root / 'current' / 'progress.sav'
            for path in (older, current):
                path.parent.mkdir(parents=True)
            write_save(older)
            os.utime(older, (1_700_000_000,) * 2)
            write_save(current, collected=True)
            conn = SaveConnection(folder, root, store)
            apply_save_update(store, conn.refresh())
            self.assertEqual(store.states['test'], 'completed')

            current.write_bytes(b'truncated')
            paused = conn.refresh()
            apply_save_update(store, paused)
            self.assertEqual(conn.path, current)
            self.assertIsNone(paused.states)
            self.assertEqual(store.states['test'], 'completed')
            self.assertEqual(store.connection, 'disconnected')

            write_save(current)
            self.assertEqual(conn.refresh().states['test'], 'unknown')
            self.assertEqual(conn.path, current)
            current.write_bytes(b'truncated')
            self.assertIsNone(conn.refresh().states)
            self.assertEqual(conn.refresh().states['test'], 'unknown')
            self.assertEqual(conn.path, older)

    def test_save_rename_waits_once_before_returning_to_an_older_slot(self):
        import os

        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory).resolve()
            store = StateStore(write_seed(folder), ['test'])
            root = folder / 'saves'
            older = root / 'older' / 'progress.sav'
            current = root / 'current' / 'progress.sav'
            for path in (older, current):
                path.parent.mkdir(parents=True)
            write_save(older)
            os.utime(older, (1_700_000_000,) * 2)
            write_save(current, collected=True)
            os.utime(current, (1_700_000_010,) * 2)
            conn = SaveConnection(folder, root, store)
            apply_save_update(store, conn.refresh())

            backup = current.rename(current.with_suffix('.bak'))
            interrupted = conn.refresh()
            self.assertIsNone(interrupted.states)
            apply_save_update(store, interrupted)
            self.assertEqual(conn.path, current)
            self.assertEqual(store.states['test'], 'completed')

            backup.rename(current)
            self.assertEqual(conn.refresh().save_path, current)
            current.rename(backup)
            self.assertIsNone(conn.refresh().states)
            self.assertEqual(conn.refresh().save_path, older)

            backup.rename(current)
            self.assertEqual(conn.refresh().save_path, current)
            current.rename(backup)
            os.utime(older, (1_700_000_020,) * 2)
            self.assertEqual(conn.refresh().save_path, older)

    def test_reopening_during_a_save_rewrite_retains_the_watched_slot(self):
        import os

        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory).resolve()
            seed_id = write_seed(folder)
            store = StateStore(seed_id, ['test'])
            saves = folder / 'saves'
            older = saves / 'older' / 'progress.sav'
            current = saves / 'current' / 'progress.sav'
            for path in (older, current):
                path.parent.mkdir(parents=True)
            write_save(older)
            os.utime(older, (1_700_000_000,) * 2)
            write_save(current, collected=True)
            initial = SaveConnection(folder, saves, store).refresh()
            self.assertEqual(initial.save_path, current)
            apply_save_update(store, initial)

            current.write_bytes(b'truncated')
            reopened = SaveConnection(folder, saves, store, preferred_save=initial.save_path)
            paused = reopened.refresh()
            self.assertIsNone(paused.states)
            self.assertIsNone(reopened.path)
            apply_save_update(store, paused)
            self.assertEqual(store.states['test'], 'completed')
            self.assertEqual(store.connection, 'disconnected')

            write_save(current, collected=True)
            resumed = reopened.refresh()
            self.assertEqual(resumed.save_path, current)
            apply_save_update(store, resumed)
            self.assertEqual(store.states['test'], 'completed')
            self.assertEqual(store.connection, 'save')

    def test_replaced_slot_for_another_seed_discards_the_previous_snapshot(self):
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory).resolve()
            store = StateStore(write_seed(folder), ['test'])
            saves = folder / 'saves'
            saves.mkdir()
            path = saves / 'progress.sav'
            write_save(path, collected=True)
            conn = SaveConnection(folder, saves, store)
            apply_save_update(store, conn.refresh())
            self.assertEqual(store.states['test'], 'completed')

            write_save(path, linked=False)
            update = conn.refresh()
            self.assertTrue(update.reset)
            apply_save_update(store, update)
            self.assertEqual(store.states['test'], 'unknown')
            self.assertIsNone(store.last_success)

    def test_link_samples_same_seed_memory_even_without_changes_to_check_flags(self):
        from unittest.mock import Mock
        from oot_rando.tracker.live_memory import SEQUENCE_IS_CHILDHOOD
        from test_link_position import PlayerMemory

        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            save = folder / 'progress.sav'
            store = StateStore(write_seed(folder), ['test'])
            write_save(save, child=True)
            live_flags = dict(bool={100: True, SEQUENCE_IS_CHILDHOOD: True}, sha256='steady')
            reader = Mock()
            reader.memory = PlayerMemory()
            reader.snapshot.return_value = live_flags
            connection = SaveConnection(folder, save, store, live_factory=lambda: reader)
            self.assertIsNone(connection.refresh(show_link=True).link)
            first = connection.refresh(live=True, show_link=True).link
            self.assertEqual(first.scene, 'KokiriForest')
            reader.memory = PlayerMemory(scene='LostWood_Child', x=14)
            second = connection.refresh(live=True, show_link=True).link
            self.assertEqual((second.scene, second.x), ('LostWood', 14))
            reader.snapshot.return_value = dict(bool={100: False}, sha256='other-seed')
            fallback = connection.refresh(live=True, show_link=True)
            self.assertEqual(fallback.mode, 'save')
            self.assertIsNone(fallback.link)
            reader.snapshot.return_value = live_flags
            resumed = connection.refresh(live=True, show_link=True)
            self.assertEqual(resumed.mode, 'live')
            self.assertEqual(resumed.link, second)
            write_save(save)
            reader.snapshot.return_value = dict(bool={100: True}, sha256='no-age')
            reader.memory = PlayerMemory(scene='SpiritTemple', appearance='Link_Adult')
            without_age_flag = connection.refresh(live=True, show_link=True)
            self.assertIsNone(without_age_flag.age)
            self.assertEqual((without_age_flag.link.scene, without_age_flag.link.age),
                             ('SpiritTemple', 'Adult'))

    def test_live_updates_before_save_and_falls_back_on_wrong_seed_or_disconnect(self):
        from unittest.mock import Mock
        from oot_rando.tracker.live_memory import LiveUnavailable, SEQUENCE_IS_CHILDHOOD

        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            save = folder / 'progress.sav'
            store = StateStore(write_seed(folder), ['test'])
            write_save(save, child=True)
            before = save.read_bytes()
            reader = Mock()
            marker = {100: True, SEQUENCE_IS_CHILDHOOD: False}
            reader.snapshot.side_effect = [
                dict(bool=marker, bool64={42: True}, bool64_complete=True, sha256='live'),
                dict(bool=marker, bool64_complete=False, sha256='partial'),
                dict(bool={100: False}, sha256='different-seed'),
                LiveUnavailable('game stopped'),
            ]
            factory = Mock(return_value=reader)
            session = SaveConnection(folder, save, store, live_factory=factory)
            session.refresh()
            factory.assert_not_called()
            update = session.refresh(live=True)
            apply_save_update(store, update)
            self.assertEqual(store.connection, 'live')
            self.assertEqual(store.states['test'], 'completed')
            self.assertEqual(update.age, 'Adult')
            partial = session.refresh(live=True)
            self.assertEqual(partial.mode, 'live')
            self.assertIn('chests at the latest save', partial.detail)
            self.assertEqual(partial.states['test'], 'unknown')
            self.assertEqual(session.refresh(live=True).mode, 'save')
            self.assertEqual(session.refresh(live=True).mode, 'save')
            session.refresh()
            reader.memory.close.assert_called_once()
            factory.assert_called_once()
            self.assertEqual(save.read_bytes(), before)
