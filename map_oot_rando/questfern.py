"""Kokiri pause-map background, served from Questfern on demand."""
from hashlib import sha256
from io import BytesIO
from urllib.request import Request, urlopen

from .aerial import read_image
from .map_projection import registered_background

SOURCE_ID = 'questfern-kokiri'
CALIBRATION = 1
SOURCE = 'https://questfern.com/maps/oot/kokiri.jpg'
DIGEST = '4fcc36b84e2f9d17c56591e57d9e77cbefd0604bc3cb5b0071136cdc798d235b'
SIZE = (1400, 709)
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


def load_pause_map():
    request = Request(SOURCE, headers={'User-Agent': 'Map-oot-rando/1.0'})
    with urlopen(request, timeout=8) as response:
        if response.url != SOURCE:
            raise ValueError('Adresse Questfern modifiée.')
        data = response.read(2_000_001)
    if sha256(data).hexdigest() != DIGEST:
        raise ValueError('Le fond Questfern a changé. Sa projection doit être vérifiée.')
    return read_image(BytesIO(data))


def align_pause_map(image, references, details=()):
    if image.size != SIZE:
        raise ValueError('Dimensions inattendues pour le fond de Kokiri.')
    return registered_background(image, references + list(details), LANDMARKS, HOLDOUT,
                                 source=SOURCE_ID, calibration=CALIBRATION)
