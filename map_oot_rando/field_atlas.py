"""Open and align published Field Atlas backgrounds."""
from itertools import combinations
from math import hypot
from io import BytesIO

from resvg_py import svg_to_bytes

from .aerial import AerialImage, apply, read_image
from .background_assets import verified_asset
from .image_warp import align_local

SOURCE = 'https://oot.gousse.cool/content/maps/7e802ffa8684f3cd.svg'
CALIBRATION = 2
DIGEST = '7e802ffa8684f3cdbe4e342c5f8b3312918b50bc1b1f1904ecc3957cb9d7abc0'


def load_kokiri_image():
    return load_atlas_image(DIGEST, width=1800, height=996, url=SOURCE)


def load_atlas_image(digest, *, width, height=None, url=None):
    url = url or f'https://oot.gousse.cool/content/maps/{digest[:16]}.svg'
    data = verified_asset(url, digest, provider='Field Atlas', extension='svg', limit=100_000)
    dimensions = {'width': width}
    if height is not None:
        dimensions['height'] = height
    return read_image(BytesIO(svg_to_bytes(svg_string=data.decode('utf-8'), **dimensions)))


REGION_MAPS = {
    'KakarikoVillage': {
        'Child': ('field-atlas-kakariko-child', 'ec8d8a9fcf46a7b5f159d3fa112772041a720270124fa28db9bf3391f41a6ec5'),
        'Adult': ('field-atlas-kakariko-adult', 'a2991a3861d98c7331e597948d1370e63b0f14bff72d0a11eb3d1f7ce4b19979'),
    },
    'Graveyard': {
        'Child': ('field-atlas-graveyard-child', 'fad753b7a0f64d863530f30c6ad5b0f3962468a06ae274a6f85a2b0e6dce47f7'),
        'Adult': ('field-atlas-graveyard-adult', '48cc191d6b543edae7d9432920c6ac7a237c229c8b937aee2a38b228259c4d00'),
    },
}
DMT_DIGEST = 'db76ca2b051650690012b8d3eb737e1856cfdbb6eaddd7ef896f7a953c8104d7'
REGION_MAPS['DeathMountainTrail'] = dict.fromkeys(('Child', 'Adult'), ('field-atlas-death-mountain', DMT_DIGEST))
GORON_DIGEST = 'bd62600104b51d5d42bb658c34d41bcc7f421b3d8c79e9393ef024a80a774e14'
REGION_MAPS['GoronCity'] = dict.fromkeys(('Child', 'Adult'), ('field-atlas-goron-city', GORON_DIGEST))
REGION_MAPS['DodongoCavern'] = {
    '1F': ('field-atlas-dodongo-1f', '9df7f3e24787a2e6f4bed707ed26e46687c4bf76779b2fa1d854a11ff0c7b111'),
    '2F': ('field-atlas-dodongo-2f', '4193834d6b36cf47e8f52b8d138a5fcb2124373b693c73b748f9c6b50c271f49'),
}
REGION_CALIBRATION = 1


def align_region_image(image, references, region, age):
    from .map_projection import registered_background

    if region == 'KakarikoVillage':
        controls = {
            'Vers la plaine d’Hyrule': (42, 346),
            'Vers le Mont du Péril': (367 if age == 'Child' else 369, 43),
            'Vers le cimetière': (608, 395),
            'Maison au sud': (342, 498),
            'Puits': (415, 314),
        }
        holdout = {'Moulin': (510, 313)}
    elif region == 'Graveyard':
        controls = {
            'Pilier nord du portail': (57, 137),
            'Première tombe au nord': (240, 69),
            'Tombe au sud-est': (337, 208),
            'Tombe de la rangée centrale': (258, 146),
            'Monument royal': (462, 132),
        }
        holdout = {'Maison du gardien': (174, 211), 'Stèle royale sud': (433, 150)}
    elif region == 'DeathMountainTrail':
        controls = {
            'Repère du cratère': (485, 134),
            'Repère Goron': (345, 541),
            'Repère Dodongo': (205, 915),
            'Repère Cocorico': (322, 1463),
            'Rocher au virage sud': (200, 1226),
        }
        holdout = {'Vers la Caverne Dodongo': (181, 861)}
    elif region == 'GoronCity':
        controls = {
            'Repère nord Goron': (351, 64),
            'Vers le mont du Péril': (362, 631),
            'Repère des Bois Perdus': (519, 363),
            'Place centrale Goron': (353, 379),
            'Seuil nord Goron': (351, 93),
        }
        holdout = {'Galerie est Goron': (543, 448)}
    elif age == '1F':
        controls = {
            'Vers le mont du Péril': (247, 591),
            'Plateforme centrale Dodongo': (248, 359),
            'Escaliers nord Dodongo': (180, 70),
            'Plateforme nord-ouest Dodongo': (542, 245),
            'Plateforme nord-est Dodongo': (612, 244),
            'Plateforme sud-est Dodongo': (612, 284),
        }
        holdout = {'Salle ouest basse Dodongo': (74, 428), 'Plateforme ouest Dodongo': (505, 263)}
    else:
        controls = {
            'Salle ouest haute Dodongo': (79, 254),
            'Plateforme centrale Dodongo': (243, 204),
            'Plateforme haute Dodongo': (550, 116),
            'Îlot nord-ouest Dodongo': (581, 176),
            'Îlot sud Dodongo': (614, 212),
            'Îlot est Dodongo': (633, 201),
        }
        holdout = {'Îlot nord Dodongo': (601, 152)}
    return registered_background(image, references, controls, holdout, source=REGION_MAPS[region][age][0],
                                 calibration=REGION_CALIBRATION, require_validation=True)


# Centers read against the published 900 × 498 drawing. These are visual
# correspondences to OotrR's room centers, not surveyed game coordinates.
HOUSE_PIXELS = {
    'know it all house': (239, 239),
    'midos house': (309, 168),
    'links house': (339, 331),
    'sarias house': (444, 338),
    'twins house': (505, 335),
}


# Center of the training enclosure on the published drawing. The check
# coordinate itself is always read from the seed metadata at runtime.
DETAIL_PIXELS = {'KF Kokiri Sword Chest': (223, 380)}


def align_kokiri_image(image, references, details=()):
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
        coefficients, basis, error = fit_landmarks(pairs)
        if max(error) <= 18:
            return _aligned_image(image, coefficients, basis, pairs, details)
    except ValueError:
        pass

    candidates = []
    if len(pairs) >= 5:
        for subset in combinations(pairs, len(pairs) - 1):
            try:
                coefficients, basis, error = fit_landmarks(subset)
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
    return _aligned_image(image, best, basis, pairs, details)


def fit_landmarks(pairs):
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


def _aligned_image(image, coefficients, basis, pairs, details):
    def scaled(point):
        return point[0] * image.width / 900, point[1] * image.height / 498

    positions = {}
    for name, point in details:
        if name in DETAIL_PIXELS:
            positions.setdefault(name, set()).add(tuple(point))
    controls = [(scaled(apply(coefficients, next(iter(points)))), scaled(DETAIL_PIXELS[name]))
                for name, points in positions.items() if len(points) == 1]
    fixed = [scaled(apply(coefficients, point)) for point, _ in pairs]
    if controls:
        try:
            image = align_local(image, controls, fixed)
        except ValueError:
            pass  # Keep the checked global fit when local evidence is incompatible.
    pixels = [scaled(apply(coefficients, point)) for point in basis]
    return AerialImage(image, pixels, basis, source='field-atlas', calibration=CALIBRATION)
