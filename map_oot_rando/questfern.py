"""Pause-map backgrounds served from Questfern on demand."""
from hashlib import sha256
from io import BytesIO
from urllib.request import Request, urlopen

from .aerial import read_image
from .map_projection import registered_background

SOURCE_ID = 'questfern-kokiri'
CALIBRATION = 2
SOURCE = 'https://questfern.com/maps/oot/kokiri.jpg'
DIGEST = '4fcc36b84e2f9d17c56591e57d9e77cbefd0604bc3cb5b0071136cdc798d235b'
SIZE = (1400, 709)
FIELD_SOURCE_ID = 'questfern-hyrule-field'
FIELD_CALIBRATION = 1
FIELD_URL = 'https://questfern.com/maps/oot/field.jpg'
FIELD_DIGEST = '7025de639dfdfba2f99d80ac7be94d02ab8b23ad486dec5778e6bb614c1b8a06'
FIELD_SIZE = (1400, 1075)
LANDMARKS = {
    'know it all house': (313, 327),
    'midos house': (440, 204),
    'links house': (484, 492),
    'sarias house': (658, 495),
    'twins house': (773, 496),
    'KF Kokiri Sword Chest': (289, 575),
}
# Independent validation point, excluded from the fit.
HOLDOUT = {'shop room': (692, 277)}
FIELD_LANDMARKS = {
    'Porte de la Citadelle': (840, 20),
    'Vers Cocorico': (1388, 20),
    'Vers la Vallée Gerudo': (12, 402),
    'Vers le Lac Hylia': (580, 1056),
    'Pont de la rivière': (1132, 136),
}
FIELD_HOLDOUT = {'Arbre isolé près de Kokiri': (1018, 673)}


def load_pause_map():
    return load_questfern_asset(SOURCE, DIGEST)


def load_field_map():
    return load_questfern_asset(FIELD_URL, FIELD_DIGEST)


def load_questfern_asset(url, digest):
    request = Request(url, headers={'User-Agent': 'Map-oot-rando/1.0'})
    with urlopen(request, timeout=8) as response:
        if response.url != url:
            raise ValueError('Adresse Questfern modifiée.')
        data = response.read(2_000_001)
    if sha256(data).hexdigest() != digest:
        raise ValueError('Le fond Questfern a changé. Sa projection doit être vérifiée.')
    return read_image(BytesIO(data))


def align_pause_map(image, references, details=()):
    if image.size != SIZE:
        raise ValueError('Dimensions inattendues pour le fond de Kokiri.')
    return registered_background(image, references + list(details), LANDMARKS, HOLDOUT,
                                 source=SOURCE_ID, calibration=CALIBRATION)


def align_field_map(image, references, details=()):
    if image.size != FIELD_SIZE:
        raise ValueError('Dimensions inattendues pour le fond de la plaine d’Hyrule.')
    return registered_background(image, references, FIELD_LANDMARKS, FIELD_HOLDOUT,
                                 source=FIELD_SOURCE_ID, calibration=FIELD_CALIBRATION,
                                 require_validation=True)
