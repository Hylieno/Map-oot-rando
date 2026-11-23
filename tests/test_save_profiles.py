from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from map_oot_rando.save_profiles import SaveProfiles


class SaveProfilesTests(unittest.TestCase):
    def test_remembers_verified_files_per_seed_and_retains_paths_when_paused(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            path = root / 'state' / 'profiles.json'
            first = SaveProfiles(path)
            first.remember('seed-a', root / 'seed-a', root / 'one' / 'progress.sav')
            first.remember('seed-b', root / 'seed-b', root / 'two' / 'progress.sav')
            second = SaveProfiles(path)
            self.assertEqual(second.get('seed-a', automatic=True), (root / 'seed-a', root / 'one' / 'progress.sav'))
            second.pause('seed-a')
            self.assertIsNone(first.get('seed-a', automatic=True))
            self.assertIsNotNone(first.get('seed-a'))
            self.assertIsNotNone(first.get('seed-b', automatic=True))
            self.assertIsNone(first.get('unknown'))
            self.assertEqual(list(path.parent.glob('*.tmp')), [])

    def test_corrupt_profiles_do_not_prevent_opening_a_map(self):
        with TemporaryDirectory() as directory:
            path = Path(directory) / 'profiles.json'
            path.write_text('{invalid', encoding='utf-8')
            self.assertIsNone(SaveProfiles(path).get('seed', automatic=True))
