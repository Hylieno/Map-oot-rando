"""Open the published Kokiri background from its author on explicit request."""
from hashlib import sha256
from io import BytesIO
from urllib.request import Request, urlopen

from resvg_py import svg_to_bytes

from .aerial import read_image

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
    """Fit a common transform using the matching house centers."""
    from math import hypot
    from .aerial import AerialImage, apply

    matches = {}
    for name, position in references:
        if name in HOUSE_PIXELS:
            matches.setdefault(name, set()).add(position)
    pairs = [(next(iter(positions)), HOUSE_PIXELS[name])
             for name, positions in sorted(matches.items()) if len(positions) == 1]
    if len(pairs) < 4:
        raise ValueError('Il faut au moins quatre maisons identifiables dans cette vue.')

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
    for point, expected in pairs:
        sx, sy = apply(coefficients, point)
        if hypot(sx - expected[0], sy - expected[1]) > 18:
            raise ValueError('Les maisons de cette vue ne correspondent pas assez au dessin de Field Atlas.')

    # Encode the fitted transform as three control points for the existing map
    # renderer and JSON format. The basis uses the scale of the sampled houses.
    basis = [(x0, z0), (x0 + (xx/count)**0.5, z0), (x0, z0 + (zz/count)**0.5)]
    pixels = [(x * image.width / 900, y * image.height / 498)
              for x, y in (apply(coefficients, point) for point in basis)]
    return AerialImage(image, pixels, basis)
