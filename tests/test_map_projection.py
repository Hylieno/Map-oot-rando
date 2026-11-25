from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from PIL import Image

from map_oot_rando.aerial import apply
from map_oot_rando.map_projection import georeferenced_background, registered_background


class MapProjectionTests(unittest.TestCase):
    def test_georeferenced_image_aligns_from_world_file_without_clicks(self):
        with TemporaryDirectory() as folder:
            path = Path(folder) / 'capture.png'
            Image.new('RGB', (140, 100)).save(path)
            self.assertIsNone(georeferenced_background(path))
            path.with_suffix('.pgw').write_text('0.5\n0\n0\n-0.5\n20.25\n99.75\n')
            background = georeferenced_background(path)
            self.assertEqual(apply(background.world_to_image, (20, 100)), (0, 0))
            x, y = apply(background.world_to_image, (55, 75))
            self.assertAlmostEqual(x, 70)
            self.assertAlmostEqual(y, 50)
            path.with_suffix('.pgw').write_text('0\n0\n0\n0\n20\n100\n')
            with self.assertRaises(ValueError):
                georeferenced_background(path)

    def test_registration_checks_points_left_outside_the_fit(self):
        coords = [(50, 50), (120, 350), (400, 40), (480, 390), (250, 220)]
        control = {str(i): (x + 50, y + 60) for i, (x, y) in enumerate(coords)}
        refs = list(zip(control, coords)) + [('independent', (180, 160))]
        image = Image.new('RGB', (800, 600))
        options = dict(source='test', calibration=1)
        background = registered_background(image, refs, control, {'independent': (230, 220)}, **options)
        x, y = apply(background.world_to_image, (180, 160))
        self.assertAlmostEqual(x, 230)
        self.assertAlmostEqual(y, 220)
        with self.assertRaisesRegex(ValueError, 'indépendant'):
            registered_background(image, refs, control, {'independent': (320, 220)}, **options)

    def test_prefers_similarity_when_affine_shear_only_fits_noise(self):
        refs = [(str(i), p) for i, p in enumerate(((15, 23), (110, 25), (38, 142),
                                                   (200, 190), (95, 80), (205, 55)))]
        pixels = {str(i): (x + 130 + [1, 1, -1, 0, -1, -1][i],
                           y + 160 + [0, -1, 1, 0, 1, -1][i])
                  for i, (_, (x, y)) in enumerate(refs)}
        result = registered_background(Image.new('RGB', (500, 500)), refs, pixels, {},
                                       source='test', calibration=1)
        a, b, _, d, e, _ = result.world_to_image
        self.assertAlmostEqual(a, e)
        self.assertAlmostEqual(b, -d)

    def test_field_background_requires_an_unambiguous_independent_landmark(self):
        from map_oot_rando.questfern import FIELD_HOLDOUT, FIELD_LANDMARKS, FIELD_SIZE, align_pause_map

        image = Image.new('RGB', FIELD_SIZE)
        references = list(FIELD_LANDMARKS.items())
        with self.assertRaisesRegex(ValueError, 'indépendant'):
            align_pause_map(image, references, region='HyruleField')
        name, point = next(iter(FIELD_HOLDOUT.items()))
        references.append((name, point))
        self.assertEqual(align_pause_map(image, references, region='HyruleField').image_point(point), point)
        with self.assertRaisesRegex(ValueError, 'ambigu'):
            align_pause_map(image, references + [(name, (500, 500))], region='HyruleField')

    def test_pause_map_reuses_only_verified_cache_bytes(self):
        from dataclasses import replace
        from hashlib import sha256
        from io import BytesIO
        from unittest.mock import patch
        from map_oot_rando.questfern import PAUSE_MAPS, load_pause_map

        with TemporaryDirectory() as folder:
            scratch = BytesIO()
            Image.new('RGB', (30, 20), 'white').save(scratch, format='JPEG')
            asset = scratch.getvalue()
            config = replace(PAUSE_MAPS['HyruleField'], digest=sha256(asset).hexdigest())
            with (patch.dict(PAUSE_MAPS, HyruleField=config),
                  patch('map_oot_rando.background_assets.local_tracker_dir', return_value=Path(folder)),
                  patch('map_oot_rando.background_assets.urlopen') as download):
                response = BytesIO(asset)
                response.url = config.url
                download.return_value = response
                self.assertEqual(load_pause_map('HyruleField').size, (30, 20))
                download.side_effect = OSError('offline')
                self.assertEqual(load_pause_map('HyruleField').size, (30, 20))
                download.assert_called_once()
                cache, = (Path(folder) / 'backgrounds').iterdir()
                cache.write_bytes(b'damaged')
                with self.assertRaisesRegex(OSError, 'offline'):
                    load_pause_map('HyruleField')
