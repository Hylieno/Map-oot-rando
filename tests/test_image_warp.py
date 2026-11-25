import unittest

from PIL import Image

from map_oot_rando.image_warp import align_local


class ImageWarpTests(unittest.TestCase):
    def test_adjusts_two_separate_neighborhoods_without_shifting_fixed_landmark(self):
        image = Image.new('RGB', (240, 160), '#000000')
        for x, color in ((44, (255, 0, 0)), (196, (0, 255, 0)), (120, (0, 0, 255))):
            image.paste(color, (x-2, 78, x+3, 83))

        result = align_local(image, [((40, 80), (44, 80)), ((200, 80), (196, 80))],
                             fixed=[(120, 80)])
        self.assertEqual(result.getpixel((40, 80)), (255, 0, 0))
        self.assertEqual(result.getpixel((200, 80)), (0, 255, 0))
        self.assertEqual(result.getpixel((120, 80)), (0, 0, 255))

    def test_rejects_local_jump_conflicting_with_nearby_landmark(self):
        image = Image.new('RGB', (100, 100))
        with self.assertRaisesRegex(ValueError, 'trop importante'):
            align_local(image, [((50, 50), (70, 50))], fixed=[(55, 50)])
