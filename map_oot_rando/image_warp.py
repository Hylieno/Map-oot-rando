"""Bounded local image alignment in the globally calibrated pixel frame."""
from math import dist

from PIL import Image


def align_local(image, pairs, fixed=()):
    """Sample source pixels at verified control points without moving markers.

    Each correction fades to zero before any other control point. A derivative
    bound rejects maps that would fold or stretch excessively.
    """
    width, height = image.size
    controls = [point for point, _ in pairs]
    fixed = tuple(fixed)
    if len(set(controls)) != len(controls) or set(controls).intersection(fixed):
        raise ValueError('Repères locaux incompatibles.')
    supports = []
    for point, source in pairs:
        if not all(0 <= x < width and 0 <= y < height for x, y in (point, source)):
            raise ValueError('Repère d’alignement hors de l’image.')
        separation = min((dist(point, other) for other in (*controls, *fixed)
                          if other != point), default=min(width, height))
        radius = min(0.23 * min(width, height), separation * 0.9)
        dx, dy = source[0] - point[0], source[1] - point[1]
        if dist(point, source) > 0.5:
            supports.append((point, dx, dy, radius))
    if not supports:
        return image
    if sum(1.5 * dist((0, 0), (dx, dy)) / radius for _, dx, dy, radius in supports) > 0.45:
        raise ValueError('Correction locale trop importante.')

    def sample(x, y):
        u, v = x, y
        for center, dx, dy, radius in supports:
            distance = dist((x, y), center) / radius
            if distance < 1:
                weight = (1 - distance) ** 2 * (1 + 2 * distance)
                u += weight * dx
                v += weight * dy
        return u, v

    # Bake the correction once. Pan/zoom and coverage use the existing affine
    # transform on the resulting image and remain consistent with each other.
    step = max(1, min(24, round(min(radius for _, _, _, radius in supports) / 10)))
    xs, ys = [*range(0, width, step), width], [*range(0, height, step), height]
    nodes = {(x, y): sample(x, y) for y in ys for x in xs}
    mesh = []
    for y0, y1 in zip(ys, ys[1:]):
        for x0, x1 in zip(xs, xs[1:]):
            quad = (nodes[x0, y0] + nodes[x0, y1] + nodes[x1, y1] + nodes[x1, y0])
            mesh.append(((x0, y0, x1, y1), quad))
    return image.transform(image.size, Image.Transform.MESH, mesh,
                           resample=Image.Resampling.BILINEAR, fillcolor='#0d1f2e')
