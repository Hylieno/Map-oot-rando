from hashlib import sha256
from io import BytesIO
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from map_oot_rando.field_atlas import SOURCE, load_kokiri_image


class Response(BytesIO):
    url = SOURCE


class FieldAtlasTests(unittest.TestCase):
    def setUp(self):
        self.folder = self.enterContext(TemporaryDirectory())
        self.enterContext(patch('map_oot_rando.background_assets.local_tracker_dir',
                                return_value=Path(self.folder)))

    def test_rasterizes_expected_svg(self):
        data = (b'<svg xmlns="http://www.w3.org/2000/svg" width="900" height="498">'
                b'<rect width="900" height="498" fill="#00ff00"/></svg>')
        with (patch('map_oot_rando.background_assets.urlopen', return_value=Response(data)) as download,
              patch('map_oot_rando.field_atlas.DIGEST', sha256(data).hexdigest())):
            image = load_kokiri_image()
            download.side_effect = OSError('offline')
            self.assertEqual(load_kokiri_image().size, image.size)
            download.assert_called_once()
        self.assertEqual(image.size, (1800, 996))
        self.assertEqual(image.getpixel((100, 100)), (0, 255, 0))

    def test_rejects_changed_image_before_rendering(self):
        with (patch('map_oot_rando.background_assets.urlopen', return_value=Response(b'changed')),
              patch('map_oot_rando.field_atlas.svg_to_bytes') as render):
            with self.assertRaisesRegex(ValueError, 'fond Field Atlas a changé'):
                load_kokiri_image()
        render.assert_not_called()

    def test_fire_floors_align_without_seed_control_points(self):
        from PIL import Image
        from map_oot_rando.field_atlas import align_region_image

        # The same X/Z has different pixel coordinates in each floor crop.
        cases = [(492, (207, 241)), (256, (202, 128)), (403, (339, 208)),
                 (366, (429, 226)), (291, (372, 144))]
        for index, (height, expected) in enumerate(cases, start=1):
            with self.subTest(floor=index):
                atlas = align_region_image(Image.new('RGB', (700, height)), (), 'FireTemple', f'{index}F')
                self.assertEqual(tuple(round(v) for v in atlas.image_point((0, 0))), expected)
        with self.assertRaisesRegex(ValueError, 'dimensions'):
            align_region_image(Image.new('RGB', (700, 320)), (), 'FireTemple', '5F')

    def test_death_mountain_checks_dodongo_independently(self):
        from PIL import Image
        from map_oot_rando.field_atlas import align_region_image

        image = Image.new('RGB', (650, 1603))
        refs = [
            ('Repère du cratère', (-0.32, -157.04)),
            ('Repère Goron', (-24.63, -86.5)),
            ('Repère Dodongo', (-50.8, -21.29)),
            ('Repère Cocorico', (-29.8, 73.27)),
            ('Rocher au virage sud', (-52.0, 33.24)),
        ]
        region = 'DeathMountainTrail'
        image_map = align_region_image(image, refs + [('Vers la Caverne Dodongo', (-55.27, -31.26))],
                                       region, 'Child')
        self.assertTrue(image_map.covers((-26.15, 85.63)))
        with self.assertRaisesRegex(ValueError, 'indépendant'):
            align_region_image(image, refs + [('Vers la Caverne Dodongo', (-40, -31.26))], region, 'Child')

    def test_auto_alignment_fits_house_centers_from_kokiri_view(self):
        from math import dist
        from PIL import Image
        from map_oot_rando.aerial import apply
        from map_oot_rando.field_atlas import HOUSE_PIXELS, align_kokiri_image

        # Approximate points from the user's OotrR schematic screenshot. Its
        # screen coordinates are an affine surrogate for world coordinates.
        references = list(zip(HOUSE_PIXELS, [(596, 498), (662, 437), (681, 580),
                                             (770, 586), (831, 586)]))
        image = Image.new('RGB', (1800, 996))
        background = align_kokiri_image(image, references)
        for name, position in references:
            self.assertLess(dist(apply(background.world_to_image, position),
                                 tuple(2 * v for v in HOUSE_PIXELS[name])), 12)
        with self.assertRaisesRegex(ValueError, 'quatre maisons'):
            align_kokiri_image(image, references[:3])
        references[0] = (references[0][0], (1050, 700))
        background = align_kokiri_image(image, references)
        for name, position in references[1:]:
            self.assertLess(dist(apply(background.world_to_image, position),
                                 tuple(2 * v for v in HOUSE_PIXELS[name])), 24)
        references[1] = (references[1][0], (1400, 820))
        with self.assertRaisesRegex(ValueError, 'ne correspondent pas'):
            align_kokiri_image(image, references)

    def test_child_alignment_from_schematic_screenshot(self):
        from PIL import Image
        from map_oot_rando.field_atlas import HOUSE_PIXELS, align_kokiri_image
        refs = list(zip(HOUSE_PIXELS, [(568, 368), (684, 267), (716, 510),
                                     (870, 521), (976, 520)]))
        self.assertEqual(len(align_kokiri_image(Image.new('RGB', (900, 498)), refs).corners()), 4)

    def test_local_anchor_adjusts_raster_and_preserves_world_projection(self):
        from PIL import Image
        from map_oot_rando.aerial import apply
        from map_oot_rando.field_atlas import DETAIL_PIXELS, HOUSE_PIXELS, align_kokiri_image

        image = Image.new('RGB', (900, 498))
        name, source = next(iter(DETAIL_PIXELS.items()))
        x, y = source
        image.paste((255, 0, 0), (x-3, y-3, x+4, y+4))
        landmark = HOUSE_PIXELS['links house']
        image.putpixel(landmark, (0, 0, 255))
        world = (238, 386)
        base = align_kokiri_image(image, HOUSE_PIXELS.items())
        aligned = align_kokiri_image(image, HOUSE_PIXELS.items(), [(name, world), (name, world)])
        self.assertEqual(apply(base.world_to_image, world), apply(aligned.world_to_image, world))
        self.assertEqual(aligned.image.getpixel(world), (255, 0, 0))
        self.assertGreaterEqual(aligned.image.getpixel(landmark)[2], 254)
