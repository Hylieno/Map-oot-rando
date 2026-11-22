"""Align a user-provided overhead image with real X/Z coordinates."""
import base64
from io import BytesIO
from math import isfinite

from PIL import Image, ImageOps


def affine(source, target):
    """Map three non-collinear 2D points to their counterparts."""
    (x, y), (x1, y1), (x2, y2) = source
    dx1, dy1 = x1 - x, y1 - y
    dx2, dy2 = x2 - x, y2 - y
    determinant = dx1 * dy2 - dx2 * dy1
    if abs(determinant) <= 1e-6 * max(1, abs(dx1 * dy2), abs(dx2 * dy1)):
        raise ValueError('Choisis trois repères distincts qui forment un triangle.')
    result = []
    for (start, end1, end2) in zip(*target):
        a = ((end1 - start) * dy2 - (end2 - start) * dy1) / determinant
        b = (dx1 * (end2 - start) - dx2 * (end1 - start)) / determinant
        result.extend((a, b, start - a * x - b * y))
    return tuple(result)


def apply(matrix, point):
    a, b, c, d, e, f = matrix
    x, y = point
    return a * x + b * y + c, d * x + e * y + f


def read_image(source):
    with Image.open(source, formats=['PNG', 'JPEG']) as image:
        if image.width * image.height > 16_000_000:
            raise ValueError('Image trop grande (maximum 16 millions de pixels).')
        return ImageOps.exif_transpose(image).convert('RGB')


class AerialImage:
    def __init__(self, image, pixels, world):
        self.image = image
        self.pixels = pixels
        self.world = world
        self.world_to_image = affine(world, pixels)
        self.image_to_world = affine(pixels, world)

    def corners(self):
        w, h = self.image.size
        return [apply(self.image_to_world, p) for p in [(0, 0), (w, 0), (w, h), (0, h)]]

    def render(self, viewport, size):
        a, b, c, d, e, f = self.world_to_image
        s = viewport.scale
        matrix = (a/s, b/s, c - (a * viewport.x + b * viewport.y)/s,
                  d/s, e/s, f - (d * viewport.x + e * viewport.y)/s)
        return self.image.transform(size, Image.Transform.AFFINE, matrix,
                                    resample=Image.Resampling.BILINEAR, fillcolor='#18252b')

    def to_document(self):
        stream = BytesIO()
        self.image.save(stream, 'PNG')
        return {'image': base64.b64encode(stream.getvalue()).decode('ascii'),
                'pixels': self.pixels, 'world': self.world}

    @classmethod
    def from_document(cls, row):
        coordinates = row['pixels'], row['world']
        if any(len(points) != 3 or any(len(point) != 2 or any(
                type(v) not in (int, float) or not isfinite(v) for v in point) for point in points)
               for points in coordinates):
            raise ValueError('Calibrage du fond image invalide.')
        image = read_image(BytesIO(base64.b64decode(row['image'], validate=True)))
        return cls(image, *coordinates)
