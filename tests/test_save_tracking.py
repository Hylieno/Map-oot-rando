"""Exercise the pinned tracker on a minimal synthetic seed and binary save."""
import hashlib
from importlib.util import find_spec
import json
from pathlib import Path
import struct
import tempfile
import unittest

from map_oot_rando.save_tracking import SaveConnection, apply_save_update
from map_oot_rando.state import StateStore


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


def write_save(path, *, linked=True, collected=False, bombs=False):
    from oot_rando.tracker.save_reader import FORMAT_VERSION, MAGIC, PROGRESS_TYPE_HASH

    end = 32 + 8 * 36
    header = struct.pack('<III', MAGIC, FORMAT_VERSION, end) + bytes(20)
    table = struct.pack('<IIIIII', 0, 0, 100, int(linked), 101, int(bombs))
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
            write_save(save)
            apply_save_update(store, connection.refresh())
            self.assertEqual(store.states['test'], 'unknown')
            self.assertEqual(store.states['ap#KF Kokiri Sword Chest'], 'blocked')
            write_save(save, collected=True, bombs=True)
            good = connection.refresh()
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
