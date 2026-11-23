"""Validate a reference image as one coherent projection before displaying it."""
from math import dist, isfinite
from pathlib import Path

from .aerial import AerialImage, apply, read_image
from .field_atlas import fit_landmarks


def _unique_pairs(references, pixels):
    positions = {}
    for name, point in references:
        if name in pixels:
            positions.setdefault(name, set()).add(tuple(point))
    return [(next(iter(points)), pixels[name]) for name, points in sorted(positions.items())
            if len(points) == 1]


def registered_background(image, references, control_pixels, validation_pixels, *, source, calibration):
    """Fit distributed landmarks and check unseen points before trusting a background."""
    pairs = _unique_pairs(references, control_pixels)
    if len(pairs) < 5:
        raise ValueError('Au moins cinq repères distincts sont nécessaires pour valider cette projection.')
    matrix, basis, errors = fit_landmarks(pairs)
    # Express limits relative to the image so profiles can vary in resolution.
    size = min(image.size)
    if max(errors) > 0.023 * size:
        raise ValueError('Les repères ne correspondent pas à une projection commune.')
    for index, (world, pixel) in enumerate(pairs):
        held_out, _, _ = fit_landmarks(pairs[:index] + pairs[index+1:])
        if dist(apply(held_out, world), pixel) > 0.037 * size:
            raise ValueError('La projection ne prédit pas assez bien les repères non utilisés.')
    for world, pixel in _unique_pairs(references, validation_pixels):
        if dist(apply(matrix, world), pixel) > 0.027 * size:
            raise ValueError('Un repère de contrôle indépendant est trop éloigné.')
    return AerialImage(image, [apply(matrix, point) for point in basis], basis,
                       source=source, calibration=calibration)


def georeferenced_background(path):
    """Load a standard world file. Its world axes must be the game's X and Z."""
    raster = Path(path)
    sidecars = {'.png': ('.pgw', '.pngw'), '.jpg': ('.jgw', '.jpgw'),
                '.jpeg': ('.jgw', '.jpegw')}
    candidates = [raster.with_suffix(ext) for ext in (*sidecars.get(raster.suffix.lower(), ()), '.wld')]
    sidecar = next((p for p in candidates if p.is_file()), None)
    if sidecar is None:
        return None
    values = [float(line) for line in sidecar.read_text(encoding='utf-8-sig').splitlines()]
    if len(values) != 6 or not all(isfinite(value) for value in values):
        raise ValueError('Le fichier de coordonnées doit contenir six nombres finis.')
    a, d, b, e, c, f = values
    # World files express the center of the first pixel, while our renderer
    # interprets the image origin as the corner of that pixel.
    matrix = (a, b, c - (a + b) / 2, d, e, f - (d + e) / 2)
    image = read_image(raster, normalize_orientation=False)
    pixels = [(0, 0), (image.width, 0), (0, image.height)]
    return AerialImage(image, pixels, [apply(matrix, point) for point in pixels], source='world-file')
