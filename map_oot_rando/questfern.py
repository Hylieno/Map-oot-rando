"""Pause-map backgrounds served from Questfern on demand."""
from dataclasses import dataclass
from io import BytesIO

from .aerial import read_image
from .background_assets import verified_asset
from .map_projection import registered_background

MAX_ASSET_BYTES = 2_000_000

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
GROVE_LANDMARKS = {
    'Plateforme de téléportation': (147, 165),
    'Seuil du temple': (146, 69),
    'Escalier haut ouest': (135, 224),
    'Escalier haut est': (157, 224),
    'Escalier bas ouest': (128, 505),
    'Escalier bas est': (163, 505),
}
GROVE_HOLDOUT = {'Souche': (172, 133), 'Dernier mur au sud': (144, 866)}


@dataclass(frozen=True)
class PauseMap:
    source: str
    calibration: int
    url: str
    digest: str
    size: tuple
    landmarks: dict
    holdout: dict
    require_validation: bool = True


PAUSE_MAPS = {
    'KokiriForest': PauseMap(SOURCE_ID, CALIBRATION, SOURCE, DIGEST, SIZE, LANDMARKS, HOLDOUT, False),
    'HyruleField': PauseMap(FIELD_SOURCE_ID, FIELD_CALIBRATION, FIELD_URL, FIELD_DIGEST,
                            FIELD_SIZE, FIELD_LANDMARKS, FIELD_HOLDOUT),
    'SacredForestMeadow': PauseMap(
        'questfern-sacred-forest-meadow', 1, 'https://questfern.com/maps/oot/grove.jpg',
        'd0295e822b542e81486066711bfc84e09ca2cca701daa28173fec935d67e44b6',
        (300, 1080), GROVE_LANDMARKS, GROVE_HOLDOUT),
}


def load_pause_map(region='KokiriForest'):
    config = PAUSE_MAPS[region]
    data = verified_asset(config.url, config.digest, provider='Questfern',
                          extension='jpg', limit=MAX_ASSET_BYTES)
    return read_image(BytesIO(data))


def align_pause_map(image, references, details=(), *, region='KokiriForest'):
    config = PAUSE_MAPS[region]
    if image.size != config.size:
        raise ValueError('Dimensions inattendues pour le fond Questfern.')
    return registered_background(image, [*references, *details] if region == 'KokiriForest' else references,
                                 config.landmarks, config.holdout, source=config.source,
                                 calibration=config.calibration, require_validation=config.require_validation)
