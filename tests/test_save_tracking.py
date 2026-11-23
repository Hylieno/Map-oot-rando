"""Exercise the pinned tracker on a minimal synthetic seed and binary save."""
import hashlib
from importlib.util import find_spec
import json
from pathlib import Path
import struct
import tempfile
import unittest

from map_oot_rando.save_tracking import SaveConnection, apply_save_update, kakariko_variant
from map_oot_rando.state import StateStore


class VillageVariantTests(unittest.TestCase):
    def test_partial_inventory_and_original_story_state(self):
        keys = (1, 2, 3)
        self.assertIsNone(kakariko_variant({1: True, 2: True}, keys, 4, True))
        self.assertFalse(kakariko_variant({1: True, 2: True, 3: False}, keys, 4, True))
        self.assertTrue(kakariko_variant({1: True, 2: True, 3: True}, keys, 4, True))
        self.assertIsNone(kakariko_variant({1: True, 2: True, 3: True}, keys, 4, False))
        self.assertTrue(kakariko_variant({4: True}, keys, 4, False))


def write_seed(root):
    from oot_rando.patching.randomize_kokiri import BUILD, TITLE
    from oot_rando.randomizer.randomizer_core import (
        ADAPTER_VERSION, GENERATOR_VERSION, Settings, settings_identity,
    )

    from oot_rando.logic.world import World

    settings = Settings('Synthetic Kokiri test')
    seed_id = settings_identity(settings)
    chest = 'ap#KF Kokiri Sword Chest'
    checks = [{'id': ident, 'name': ident, 'region': 'Kokiri Forest'} for ident in ('test', chest)]
    tracking = dict(schema_version=1, seed_id=seed_id, seed_marker='100', inventory=[{'item': 'Bomb Bag', 'hash': '101'}],
                    logic_world_sha256=World().fingerprint(),
                    logic={'settings': {}, 'exits': [], 'virtual': {},
                           'locations': {'KF Kokiri Sword Chest': ['Bomb Bag']}},
                    known_bool64=['42'], checks={'test': {
                        'collection': {'type': 'bool64', 'hash': '42'}, 'reward': 'Test item'}, chest: {}})
    payload = json.dumps(tracking).encode()
    data = b'synthetic resource'
    manifest = dict(schema_version=1, title_id=TITLE, build_id=BUILD, seed_id=seed_id,
                    settings=settings.to_dict(), generator_version=GENERATOR_VERSION,
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
            self.assertIsNone(connection.refresh(live=True, show_link=True).link)

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
