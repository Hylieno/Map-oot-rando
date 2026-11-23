"""Align a user-provided overhead image with real X/Z coordinates."""
import base64
from functools import cached_property
from io import BytesIO
from math import isfinite

from PIL import Image, ImageChops, ImageOps


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


def read_image(source, *, normalize_orientation=True):
    with Image.open(source, formats=['PNG', 'JPEG']) as image:
        if image.width * image.height > 16_000_000:
            raise ValueError('Image trop grande (maximum 16 millions de pixels).')
        return (ImageOps.exif_transpose(image) if normalize_orientation else image).convert('RGB')


class AerialImage:
    def __init__(self, image, pixels, world, *, source=None, calibration=None):
        self.image = image
        self.source = source
        self.calibration = calibration
        self._paper_raster = None
        self.pixels = pixels
        self.world = world
        self.world_to_image = affine(world, pixels)
        self.image_to_world = affine(pixels, world)

    def image_point(self, world_point):
        return apply(self.world_to_image, world_point)

    def render_image_view(self, viewport, size, *, fillcolor, blend_paper=False):
        """Show the raster upright with screen navigation in image pixels."""
        s = viewport.scale
        matrix = (1/s, 0, -viewport.x/s, 0, 1/s, -viewport.y/s)
        raster = self.image
        if blend_paper:
            if self._paper_raster is None or self._paper_raster[0] != fillcolor:
                merged = Image.composite(raster, Image.new('RGB', raster.size, fillcolor),
                                         self._paper_edge_mask)
                self._paper_raster = (fillcolor, merged)
            raster = self._paper_raster[1]
        return raster.transform(size, Image.Transform.AFFINE, matrix,
                                resample=Image.Resampling.BILINEAR, fillcolor=fillcolor)

    @cached_property
    def _paper_edge_mask(self):
        width, height = self.image.size
        margin = max(1, min(45, min(width, height) // 10))
        def axis(length):
            return [min(255, round(255 * min(i, length - i - 1) / margin))
                    for i in range(length)]
        horizontal = Image.new('L', (width, 1))
        vertical = Image.new('L', (1, height))
        horizontal.putdata(axis(width))
        vertical.putdata(axis(height))
        edge = ImageChops.darker(horizontal.resize((width, height)), vertical.resize((width, height)))
        hue, saturation, _ = self._hsv.split()
        # Fade only the paper. Terrain such as the western path must stay visible.
        terrain = ImageChops.lighter(hue.point(lambda p: 255 if p < 23 or p > 42 else 0),
                                     saturation.point(lambda p: 255 if p > 115 else 0))
        return ImageChops.lighter(edge, terrain)

    def corners(self):
        w, h = self.image.size
        return [apply(self.image_to_world, p) for p in [(0, 0), (w, 0), (w, h), (0, h)]]

    @cached_property
    def _hsv(self):
        return self.image.convert('HSV')

    def covers(self, point):
        x, y = apply(self.world_to_image, point)
        if not (0 <= x < self.image.width and 0 <= y < self.image.height):
            return False
        if self.source == 'questfern-kokiri':
            # Look around the marker to avoid calling a light trail or icon
            # background on an otherwise solid part of the pause map.
            x, y = int(x), int(y)
            colored = 0
            for dy in (-6, 0, 6):
                for dx in (-6, 0, 6):
                    if 0 <= x+dx < self.image.width and 0 <= y+dy < self.image.height:
                        hue, saturation, _ = self._hsv.getpixel((x+dx, y+dy))
                        colored += hue < 23 or hue > 42 or saturation > 115
            return colored >= 2
        if self.source != 'field-atlas':
            return True
        # The verified drawing uses muted navy for its background and grid.
        # Sample a small area to tolerate antialiasing at the edge of a path.
        x, y = int(x), int(y)
        for dx, dy in ((0, 0), (-4, 0), (4, 0), (0, -4), (0, 4)):
            u, v = x + dx, y + dy
            if 0 <= u < self.image.width and 0 <= v < self.image.height:
                _, green, blue = self.image.getpixel((u, v))
                if green > 75 or blue > 83:
                    return True
        return False

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
                'pixels': self.pixels, 'world': self.world, 'source': self.source, 'calibration': self.calibration}

    @classmethod
    def from_document(cls, row):
        coordinates = row['pixels'], row['world']
        if any(len(points) != 3 or any(len(point) != 2 or any(
                type(v) not in (int, float) or not isfinite(v) for v in point) for point in points)
               for points in coordinates):
            raise ValueError('Calibrage du fond image invalide.')
        image = read_image(BytesIO(base64.b64decode(row['image'], validate=True)))
        return cls(image, *coordinates, source=row.get('source'), calibration=row.get('calibration'))
