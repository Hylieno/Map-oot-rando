from hashlib import sha256
from io import BytesIO
import unittest
from unittest.mock import patch

from map_oot_rando.field_atlas import SOURCE, load_kokiri_image


class Response(BytesIO):
    url = SOURCE


class FieldAtlasTests(unittest.TestCase):
    def test_rasterizes_expected_svg(self):
        data = (b'<svg xmlns="http://www.w3.org/2000/svg" width="900" height="498">'
                b'<rect width="900" height="498" fill="#00ff00"/></svg>')
        with (patch('map_oot_rando.field_atlas.urlopen', return_value=Response(data)),
              patch('map_oot_rando.field_atlas.DIGEST', sha256(data).hexdigest())):
            image = load_kokiri_image()
        self.assertEqual(image.size, (1800, 996))
        self.assertEqual(image.getpixel((100, 100)), (0, 255, 0))

    def test_rejects_changed_image_before_rendering(self):
        with (patch('map_oot_rando.field_atlas.urlopen', return_value=Response(b'changed')),
              patch('map_oot_rando.field_atlas.svg_to_bytes') as render):
            with self.assertRaisesRegex(ValueError, 'fond Field Atlas a changé'):
                load_kokiri_image()
        render.assert_not_called()
