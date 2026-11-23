import json
import unittest

from PIL import Image

from map_oot_rando.aerial import AerialImage, affine, apply
from map_oot_rando.view import Viewport


class AerialTests(unittest.TestCase):
    def test_affine_aligns_rotated_image_and_rejects_collinear_points(self):
        image_points = [(0, 0), (10, 0), (0, 20)]
        world_points = [(40, 30), (40, 20), (60, 30)]
        matrix = affine(world_points, image_points)
        self.assertEqual([apply(matrix, point) for point in world_points], image_points)
        self.assertEqual(apply(matrix, (50, 25)), (5, 10))
        with self.assertRaises(ValueError):
            affine([(0, 0), (1, 1), (2, 2)], image_points)

    def test_saved_image_round_trip_and_pan_zoom(self):
        image = Image.new('RGB', (20, 20), 'black')
        for x in range(8, 13):
            for y in range(8, 13):
                image.putpixel((x, y), (255, 0, 0))
        points = [(0, 0), (20, 0), (0, 20)]
        original = AerialImage(image, points, points)
        restored = AerialImage.from_document(json.loads(json.dumps(original.to_document())))
        self.assertEqual(restored.corners(), [(0, 0), (20, 0), (20, 20), (0, 20)])
        viewport = Viewport(scale=2, x=5, y=7)
        rendered = restored.render(viewport, (50, 50))
        self.assertEqual(rendered.getpixel((25, 27)), (255, 0, 0))
        self.assertEqual(rendered.getpixel((8, 10)), (0, 0, 0))

    def test_field_atlas_coverage_excludes_grid_and_outside_image(self):
        image = Image.new('RGB', (40, 40), '#17344a')
        image.putpixel((20, 20), (31, 85, 119))
        points = [(0, 0), (40, 0), (0, 40)]
        background = AerialImage(image, points, points, source='field-atlas')
        saved = AerialImage.from_document(background.to_document())
        self.assertTrue(saved.covers((20, 20)))
        self.assertFalse(saved.covers((5, 5)))
        self.assertFalse(saved.covers((-1, 20)))
