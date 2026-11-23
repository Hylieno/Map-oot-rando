"""Open the published Kokiri background from its author on explicit request."""
from hashlib import sha256
from itertools import combinations
from math import hypot
from io import BytesIO
from urllib.request import Request, urlopen

from resvg_py import svg_to_bytes

from .aerial import AerialImage, apply, read_image

SOURCE = 'https://oot.gousse.cool/content/maps/7e802ffa8684f3cd.svg'
DIGEST = '7e802ffa8684f3cdbe4e342c5f8b3312918b50bc1b1f1904ecc3957cb9d7abc0'


def load_kokiri_image():
    request = Request(SOURCE, headers={'User-Agent': 'Map-oot-rando/1.0'})
    with urlopen(request, timeout=8) as response:
        if response.url != SOURCE:
            raise ValueError('Adresse Field Atlas modifiée.')
        data = response.read(100_001)
    if sha256(data).hexdigest() != DIGEST:
        raise ValueError('Le fond Field Atlas a changé. Il doit être vérifié avant utilisation.')
    return read_image(BytesIO(svg_to_bytes(svg_string=data.decode('utf-8'), width=1800, height=996)))


# Centers read against the published 900 × 498 drawing. These are visual
# correspondences to OotrR's room centers, not surveyed game coordinates.
HOUSE_PIXELS = {
    'know it all house': (239, 239),
    'midos house': (309, 168),
    'links house': (339, 331),
    'sarias house': (444, 338),
    'twins house': (505, 335),
}


def align_kokiri_image(image, references):
    """Fit the house centers, allowing a single inconsistent landmark."""
    matches = {}
    for name, position in references:
        if name in HOUSE_PIXELS:
            matches.setdefault(name, set()).add(tuple(position))
    pairs = [(next(iter(positions)), HOUSE_PIXELS[name])
             for name, positions in sorted(matches.items()) if len(positions) == 1]
    if len(pairs) < 4:
        raise ValueError('Il faut au moins quatre maisons identifiables dans cette vue.')

    try:
        coefficients, basis, error = _fit_houses(pairs)
        if max(error) <= 18:
            return _aligned_image(image, coefficients, basis)
    except ValueError:
        pass

    candidates = []
    if len(pairs) >= 5:
        for subset in combinations(pairs, len(pairs) - 1):
            try:
                coefficients, basis, error = _fit_houses(subset)
            except ValueError:
                continue
            if max(error) <= 12:
                candidates.append((sum(value ** 2 for value in error), coefficients, basis))
    if not candidates:
        raise ValueError('Les maisons de cette vue ne correspondent pas assez au dessin de Field Atlas.')

    _, best, basis = min(candidates)
    # Multiple coherent results are only acceptable if they agree throughout
    # the sampled village, not merely around each individual subset.
    for _, other, _ in candidates:
        if any(hypot(*(a - b for a, b in zip(apply(best, point), apply(other, point)))) > 18
               for point, _ in pairs):
            raise ValueError('Plusieurs alignements possibles. Aucun fond n’a été appliqué.')
    return _aligned_image(image, best, basis)


def _fit_houses(pairs):
    world, target = zip(*pairs)
    count = len(pairs)
    x0, z0 = (sum(axis) / count for axis in zip(*world))
    offsets = [(x - x0, z - z0) for x, z in world]
    xx = sum(x*x for x, _ in offsets)
    zz = sum(z*z for _, z in offsets)
    xz = sum(x*z for x, z in offsets)
    determinant = xx * zz - xz * xz
    if determinant <= 0.01 * xx * zz:
        raise ValueError('Les maisons sont trop rapprochées ou alignées.')

    coefficients = []
    for axis in zip(*target):
        center = sum(axis) / count
        xt = sum(x * (t - center) for (x, _), t in zip(offsets, axis))
        zt = sum(z * (t - center) for (_, z), t in zip(offsets, axis))
        a = (zz * xt - xz * zt) / determinant
        b = (xx * zt - xz * xt) / determinant
        coefficients.extend((a, b, center - a*x0 - b*z0))
    a, b, _, d, e, _ = coefficients
    sx, sz = hypot(a, d), hypot(b, e)
    if (a * e - b * d <= 0 or abs(a * b + d * e) > 0.25 * sx * sz
            or not 0.65 <= sx / sz <= 1.55):
        raise ValueError('La transformation déforme trop le dessin.')

    errors = [hypot(actual[0] - expected[0], actual[1] - expected[1])
              for point, expected in pairs for actual in [apply(coefficients, point)]]
    # Encode the fit as three control points for the existing JSON format.
    basis = [(x0, z0), (x0 + (xx/count)**0.5, z0), (x0, z0 + (zz/count)**0.5)]
    return coefficients, basis, errors


def _aligned_image(image, coefficients, basis):
    pixels = [(x * image.width / 900, y * image.height / 498)
              for x, y in (apply(coefficients, point) for point in basis)]
    return AerialImage(image, pixels, basis, source='field-atlas')
