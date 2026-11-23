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


def _fit_similarity(pairs):
    """Fit translation, rotation and a common scale with no shear."""
    world, pixels = zip(*pairs)
    count = len(pairs)
    x, z = (sum(axis) / count for axis in zip(*world))
    u, v = (sum(axis) / count for axis in zip(*pixels))
    offsets = [(wx - x, wz - z) for wx, wz in world]
    magnitude = sum(dx*dx + dz*dz for dx, dz in offsets)
    if not magnitude:
        raise ValueError('Les repères se superposent.')
    a = sum(dx*(px-u) + dz*(py-v) for (dx, dz), (px, py) in zip(offsets, pixels)) / magnitude
    b = sum(dx*(py-v) - dz*(px-u) for (dx, dz), (px, py) in zip(offsets, pixels)) / magnitude
    if a*a + b*b < 1e-12:
        raise ValueError('Échelle de projection indéterminée.')
    matrix = (a, -b, u - a*x + b*z, b, a, v - b*x - a*z)
    span = (magnitude/count)**0.5
    basis = [(x, z), (x + span, z), (x, z + span)]
    return matrix, basis, [dist(apply(matrix, point), pixel) for point, pixel in pairs]


def registered_background(image, references, control_pixels, validation_pixels, *, source, calibration):
    """Choose the model that best predicts references omitted from the fit."""
    pairs = _unique_pairs(references, control_pixels)
    if len(pairs) < 5:
        raise ValueError('Au moins cinq repères distincts sont nécessaires pour valider cette projection.')
    independent = _unique_pairs(references, validation_pixels)
    size = min(image.size)
    candidates = []
    failures = []
    for fit in (_fit_similarity, fit_landmarks):
        try:
            matrix, basis, errors = fit(pairs)
            if max(errors) > 0.023 * size:
                raise ValueError('Les repères ne correspondent pas à une projection commune.')
            held_out = []
            for index, (world, pixel) in enumerate(pairs):
                prediction, _, _ = fit(pairs[:index] + pairs[index+1:])
                held_out.append(dist(apply(prediction, world), pixel))
            if max(held_out) > 0.037 * size:
                raise ValueError('La projection ne prédit pas assez bien les repères non utilisés.')
            validation = [dist(apply(matrix, world), pixel) for world, pixel in independent]
            if any(error > 0.027 * size for error in validation):
                raise ValueError('Un repère de contrôle indépendant est trop éloigné.')
            # Round away floating-point noise so an exact tie uses the simpler model.
            score = round(sum(error**2 for error in held_out + validation), 9)
            candidates.append((score, matrix, basis))
        except ValueError as error:
            failures.append(error)
    if not candidates:
        raise failures[0]
    _, matrix, basis = min(candidates, key=lambda candidate: candidate[0])
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
