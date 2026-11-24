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
CRATER_DIGEST = 'c1ab4bbdc19277676b5480a18792f6124e2853a2a05f7567791e8b0ecb3c94c5'
REGION_MAPS['DeathMountainCrater'] = dict.fromkeys(('Child', 'Adult'), ('field-atlas-death-mountain-crater', CRATER_DIGEST))
REGION_MAPS['DodongoCavern'] = {
    '1F': ('field-atlas-dodongo-1f', '9df7f3e24787a2e6f4bed707ed26e46687c4bf76779b2fa1d854a11ff0c7b111'),
    '2F': ('field-atlas-dodongo-2f', '4193834d6b36cf47e8f52b8d138a5fcb2124373b693c73b748f9c6b50c271f49'),
}
FIRE_VIEWBOXES = {
    '1F': (141, -30, 721, 506),
    '2F': (163, 97, 663, 242),
    '3F': (-24, -13, 780, 448),
    '4F': (18, 41, 548, 286),
    '5F': (24, 90, 622, 258),
}
JABU_VIEWBOXES = {
    '1F': (-24, -58, 844, 1823),
    'S1': (37, 760, 668, 587),
    '2F': (31, 754, 805, 624),
}
DEKU_VIEWBOXES = {
    '1F': (629, -6, 232, 340),
    '2F': (173, -10, 701, 375),
    '3F': (113, -34, 772, 333),
    'S1': (-37, -32, 863, 658),
    'S2': (344, 74, 268, 491),
}
FOREST_VIEWBOXES = {
    '1F': (-39, -27, 931, 974),
    '2F': (-37, -36, 903, 949),
    '3F': (-35, -19, 904, 585),
    'S1': (238, 142, 345, 345),
    'S2': (323, 157, 304, 395),
}
WELL_VIEWBOXES = {
    'S1': (-61, 24, 967, 1447),
    'S2': (237, -35, 651, 1101),
}
SHADOW_VIEWBOXES = {
    'S1': (285, 179, 354, 252),
    'S2': (571, 152, 163, 215),
    'S3': (439, 144, 406, 355),
    'S4': (-35, -35, 910, 382),
}
SPIRIT_VIEWBOXES = {
    '1F': (16, -29, 810, 763),
    '2F': (127, 110, 607, 320),
    '3F': (-21, 63, 883, 834),
    '4F': (209, 18, 417, 519),
}
WATER_VIEWBOXES = {
    '3F': (-42, -51, 830, 1030),
    '2F': (-13, -19, 877, 809),
    '1F': (132, -28, 697, 861),
    'S1': (154, 401, 455, 410),
}
SHARED_FIELD_FRAMES = {
    'HyruleField': ((-50, -49, 950, 739), (1.4552, 504.27, 1.4867, 11.89)),
    'SacredForestMeadow': ((190, -8, 492, 1821), (6.15, 487.31, 6.15, 1062.72)),
    'ZoraRiver': ((-48, -40, 951, 444), (3.2759, 352.05, 3.2953, 225.64)),
    'ZoraDomain': ((-47, -47, 950, 612), (6.4055, 218.87, 6.3045, 315.57)),
    # Both ages share the bridge, log, and field passage. The tent is an adult control.
    'GerudoValley': ((-46, -44, 942, 951), (5.5214, 404.3226, 4.3607, 476.2467, -0.3290, 0.1337)),
    'DesertColossus': ((3, -35, 893, 740), (3.9292, 790.626, 4.0185, 282.5508)),
    'LakeHylia': ((-37, -29, 930, 742), (2.9569, 981.3686, 2.9648, -1131.4452, 0.0175, -0.0661)),
}
FIELD_FRAMES = {region: dict.fromkeys(('Child', 'Adult'), frame)
                for region, frame in SHARED_FIELD_FRAMES.items()}
FIELD_FRAMES['ZoraFountain'] = {
    # The entrance arrow is 77 SVG units farther north on the child drawing.
    'Child': ((-44, -33, 927, 864), (7.0485, 200.7, 7.1346, 450.48)),
    'Adult': ((-45, 10, 939, 902), (7.0485, 200.7, 7.1346, 527.48)),
}
FIELD_FRAMES['IceCavern'] = {None: ((-51, -50, 947, 1179), (5.2876, 337.98, 5.1869, 469.16))}
FIELD_FRAMES['Market'] = {
    'Child': ((-34, -38, 887, 795), (5.4314, 422.86, 5.2191, 305.08)),
    'Adult': ((-35, -42, 890, 1207), (8.4001, 190.51, 8.0681, 467.58)),
}
FIELD_FRAMES['HyruleCastle'] = {
    'Child': ((-52, -35, 954, 1390), (8.2959, 286.92, 8.5297, 1319.87)),
}
FIELD_FRAMES['GanonCastle'] = {
    'Adult': ((15, -12, 844, 968), (5.4, 203, 5.49, -1154)),
}
FIELD_FRAMES['GerudoFortress'] = {
    'Adult': ((-34, -17, 928, 768), (3.098, 183.15, 3.152, 426.5)),
}
for region, frame, viewboxes in (
    ('FireTemple', (3.965, 354.2, 3.9651, 218.31), FIRE_VIEWBOXES),
    ('InsideJabuJabuBelly', (7.6, 392, 7.6, 1580), JABU_VIEWBOXES),
    ('InsideTheDekuTree', (8.5609, 733.86, 8.9211, 139.64), DEKU_VIEWBOXES),
    ('ForestTemple', (5.5747, 462.29, 5.6324, 406.55), FOREST_VIEWBOXES),
    ('BottomOfTheWell', (8.0269, 535.33, 8.1374, 945.29), WELL_VIEWBOXES),
    ('ShadowTemple', (1.9291, 467.09, 1.9529, 259.55), SHADOW_VIEWBOXES),
    ('SpiritTemple', (6.08, 421, 6.16, 595), SPIRIT_VIEWBOXES),
    ('WaterTemple', (5.0, 522, 5.25, 644), WATER_VIEWBOXES),
):
    FIELD_FRAMES[region] = {level: (viewbox, frame) for level, viewbox in viewboxes.items()}
for region, source, digest in (
    ('HyruleField', 'hyrule-field', '2cca33a54d435cd8bb42931514d1ac4698e116e683bf9967bfd7b2ced752d252'),
    ('SacredForestMeadow', 'sacred-meadow', '30559071ebb5f020ae7dd00ddc13b4a17c11f202d91df6d1501193eda34a859a'),
    ('ZoraRiver', 'zora-river', '9da62a4f11abba11eed170548a34c90e129420350bdedbb74b4a0f0d74e0aaf4'),
    ('ZoraDomain', 'zora-domain', 'b95e0d63a7da7501193467fe251b484daa93ac88928c246a4c133a73c26d9711'),
    ('GerudoValley', 'gerudo-valley', '254d68e697b8bf52c564d79a5ca178129e9ac5df65376171e29a0243e432b9d2'),
    ('DesertColossus', 'desert-colossus', 'b96a8e67771eb6a92175556550dce8f1c1f93e7241ab4a3c00c3ea7f1ee059c5'),
    ('LakeHylia', 'lake-hylia', '81029fed8441b630fa74c855a65890673c97bb3be5334f68dc10d8c919a7ffac'),
):
    REGION_MAPS[region] = dict.fromkeys(('Child', 'Adult'), (f'field-atlas-{source}', digest))
REGION_MAPS['FireTemple'] = {
    '1F': ('field-atlas-fire-1f', '3f16cb7f3303f228886c0e2d2427bca559002202f0c0c88b93beda28cbbfb457'),
    '2F': ('field-atlas-fire-2f', '61e73d8ecb54aa8a84d6fb46d985aba949a6c0993bd9f9b101bb4ae7777b909b'),
    '3F': ('field-atlas-fire-3f', '6b4577c27123e03dd824a9d7727d1c8c56930bbf4262277ff4249d810762f71a'),
    '4F': ('field-atlas-fire-4f', '7d16228fa66665c302b458a7b9c255ef47fb30ff7c6df55a6e96aadafd2c504b'),
    '5F': ('field-atlas-fire-5f', '1f1900c6bda818467de0e4dc9a9e0f4d5f8d720206268d97b686c2c2ac21ccf5'),
}
REGION_MAPS['ZoraFountain'] = {
    'Child': ('field-atlas-zora-fountain-child', 'ef682defc525b7c846650ed4e3355e5f9e75e68986a088970c677bd1c0a82fb8'),
    'Adult': ('field-atlas-zora-fountain-adult', '7caf49666efec47db9bf937b93ef1464e378593342197f5e92cff69e3a7daf33'),
}
REGION_MAPS['IceCavern'] = {
    None: ('field-atlas-ice-cavern', '1ec8568fd796ef747f703b0898bdfdba35bd1ef4422c3f8b0cc274ecfee4b126'),
}
REGION_MAPS['InsideJabuJabuBelly'] = {
    '1F': ('field-atlas-jabu-1f', '73fc5a3cfaf19cd926e0df9943eeae7e8253e4a5c5a93f7f498b7d236774f08b'),
    'S1': ('field-atlas-jabu-s1', '2296f73815cc3936b81d0629cba971b075059c3cd742b3f740b9b4521df29b08'),
    '2F': ('field-atlas-jabu-2f', 'd7e133bbf52b3120dbaa1e6d154361034b93513be360a3aa8a4198d9af5dfdca'),
}
REGION_MAPS['InsideTheDekuTree'] = {
    '1F': ('field-atlas-deku-1f', 'c684d6513a4111b0a45269a559d5cb8bfc04a3925cebd947847548329c0b745d'),
    '2F': ('field-atlas-deku-2f', '96a996b80bff76a7f76b4e117b87ee89e9a946babcb16e96db20bf037c92d098'),
    '3F': ('field-atlas-deku-3f', '7131d6d95fc34dc18df9590c8cac2584e01526cb96579682ba45ea3abe67e72e'),
    'S1': ('field-atlas-deku-s1', 'f997dee7cf0824c342246bec941e98bac8e7e1c1377d59e36aabfc661d738ca5'),
    'S2': ('field-atlas-deku-s2', '70efa8003bf43468ef3efe598bcf756ced7dacbf1d203657b1f5bb554df4cb50'),
}
REGION_MAPS['ForestTemple'] = {
    '1F': ('field-atlas-forest-1f', 'dd87dda0d106bc26d59b87841d6e52f5a5d5d9bfa1d16d35820af1ab8674eae2'),
    '2F': ('field-atlas-forest-2f', '79bf55e5fd3ac9baa5ac97a8f813af5ce2d66ff3766737856b39020b7f5a132d'),
    '3F': ('field-atlas-forest-3f', '4ae5a5642885668f29d466cea5d7716b7d09526bad1f30f5ee1305b04e86367a'),
    'S1': ('field-atlas-forest-s1', '6cbf450c90cd3ed53dfe3249f7775c4b34eb3dae5419c2d380b8acde5afb0c07'),
    'S2': ('field-atlas-forest-s2', '3f1bf57ae45da9a1d0c7b9b3752290d36957d6144716f69e0d35d29bb8624a56'),
}
REGION_MAPS['BottomOfTheWell'] = {
    'S1': ('field-atlas-well-s1', 'b68501c771ee8c193ed6bf8ac11339f3dd8b4bcdad4aa2b8b0034e4680eadd58'),
    'S2': ('field-atlas-well-s2', '4235409bd4f77a4b1067d80c1f2544a9978ab5bb528fbeeae03e0aa9d35c5f59'),
}
REGION_MAPS['ShadowTemple'] = {
    'S1': ('field-atlas-shadow-s1', '31084ef4a53b848aeabc274c8ed170eb13b427365d29d52d849b10d0e03bb286'),
    'S2': ('field-atlas-shadow-s2', '1706f580e2ba0f5fec806e3e3e131ddc09014ac453f9c0f9d840153369342bb3'),
    'S3': ('field-atlas-shadow-s3', '1e8a9e584a5012aa8e41bb2f9037751ec6ca09a18615fd140860281964fc0d87'),
    'S4': ('field-atlas-shadow-s4', 'a551de4d49cb4a18b6a4ec401c90dc484d16dee5ab2bee6886058c1718139f8a'),
}
REGION_MAPS['SpiritTemple'] = {
    '1F': ('field-atlas-spirit-1f', '6d90d5af6d3d02186251ba6c7241f92819e448e9876ba640c7ea279ec9b96da9'),
    '2F': ('field-atlas-spirit-2f', 'ff599955dbdf9fe3dd5ea1f01b77d641d8a098b70feb94389a377d8f7be4ef1f'),
    '3F': ('field-atlas-spirit-3f', 'a73b491afd39f0769279d5955fd1201a0c66e207fe373b9353ab67037268e6df'),
    '4F': ('field-atlas-spirit-4f', '9c0b60900300576f24c7281d377894f7f7f37e942f6c79ac0f2f9701ec36bd98'),
}
REGION_MAPS['WaterTemple'] = {
    '3F': ('field-atlas-water-3f', '091eed0c6c8fcc7e3891f5e4e0d69f597543d485c11288ebdaf0bd2cea7832d3'),
    '2F': ('field-atlas-water-2f', '2b63f4367c0d4722e97e7e51b95a7cac91e3beaf0e02e981617719715750ff90'),
    '1F': ('field-atlas-water-1f', '07612eaffa38f40cb9609af14eceed934a01567094f1950d9ea15c3f7d83b374'),
    'S1': ('field-atlas-water-s1', '748961d436e3d9082623eb7d595bf0f6565fa5ea06cbd922485dccc5e7bcb61e'),
}
REGION_MAPS['Market'] = {
    'Child': ('field-atlas-market-child', '44d0923e6fd7b7bcf0f77a90c43ff41bd8fe8fe8954bea1e3914c35e837cf8f7'),
    'Adult': ('field-atlas-market-adult', '0565ce9e3947134f48f704e0b83266b1400c6ff469c5c08e634444653c6c5b6b'),
}
REGION_MAPS['HyruleCastle'] = {
    'Child': ('field-atlas-hyrule-castle', 'f8d68c05a87801ca77933c810dd31f1ae032d770e2c866a77e99b29508ef036f'),
}
REGION_MAPS['GanonCastle'] = {
    'Adult': ('field-atlas-ganon-castle', 'a30a638cbcac739ff725ad832e8d98e4eef85b979d38016f4b33291cc8c9c3c6'),
}
REGION_MAPS['GerudoFortress'] = {
    'Adult': ('field-atlas-gerudo-fortress', '9070082489c25351045761a308aa95f8270233f85476ec158c01a04849d0ae73'),
}
REGION_CALIBRATION = 1


def align_capture(image, viewbox, frame, source):
    """Place a crop of a calibrated orthographic capture in X/Z."""
    left, top, width, height = viewbox
    scale = image.width / width
    if abs(height * scale - image.height) > 1:
        raise ValueError('Les dimensions du plan sont incompatibles.')
    sx, ox, sz, oz, *cross = frame
    x_from_z, z_from_x = cross or (0, 0)
    matrix = (sx * scale, x_from_z * scale, (ox - left) * scale,
              z_from_x * scale, sz * scale, (oz - top) * scale)
    basis = [(0, 0), (50, 0), (0, 50)]
    return AerialImage(image, [apply(matrix, point) for point in basis], basis,
                       source=source, calibration=REGION_CALIBRATION)


def align_region_image(image, references, region, age):
    from .map_projection import registered_background

    source = REGION_MAPS[region][age][0]
    if region in FIELD_FRAMES:
        return align_capture(image, *FIELD_FRAMES[region][age], source)
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
    elif region == 'DeathMountainCrater':
        controls = {
            'Vers le mont du Péril': (486, 609),
            'Repère Goron depuis le cratère': (65, 169),
            'Temple du Feu': (396, 65),
            'Pied du Temple du Feu': (398, 138),
            'Pont sud-ouest': (191, 368),
        }
        holdout = {'Corniche sud': (338, 486)}
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
