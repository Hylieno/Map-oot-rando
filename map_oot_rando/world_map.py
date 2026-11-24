"""Published Hyrule overview and its geographic zone anchors."""
from io import BytesIO

from PIL import Image

from .background_assets import verified_asset

WORLD_URL = 'https://oot.gousse.cool/content/maps/hyrule-full.webp'
WORLD_DIGEST = '68000e926626d82e35bdd7186f0d8984de988244f37b9a7931adee838e60f5cb'
WORLD_SIZE = (6000, 4364)
# Fractions of the Hyrule artwork as published by Ocarina Atlas.
WORLD_PINS = {
    'KokiriForest': (.5913, .6740),
    'LostWood': (.6947, .6392),
    'SacredForestMeadow': (.7774, .6745),
    'HyruleField': (.4475, .6267),
    'KakarikoVillage': (.5815, .4426),
    'Graveyard': (.7398, .3872),
    'DeathMountainTrail': (.5774, .3015),
    'GoronCity': (.6998, .3015),
    'DodongoCavern': (.5250, .2207),
    'DeathMountainCrater': (.6556, .1237),
    'FireTemple': (.6251, .1952),
    'ZoraRiver': (.5803, .5244),
    'ZoraDomain': (.6859, .4747),
    'ZoraFountain': (.8030, .5223),
    'IceCavern': (.8637, .4540),
    'InsideJabuJabuBelly': (.7673, .4510),
    'InsideTheDekuTree': (.6835, .7656),
    'ForestTemple': (.8656, .6039),
    'BottomOfTheWell': (.6610, .3741),
    'Market': (.4333, .3850),
    'HyruleCastle': (.4259, .3128),
    'GanonCastle': (.4259, .3128),
    'InsideGanonCastle': (.4092, .2333),
    'ShadowTemple': (.8012, .3182),
}


def load_world_map():
    data = verified_asset(WORLD_URL, WORLD_DIGEST, provider='Field Atlas', extension='webp',
                          limit=4_000_000)
    with Image.open(BytesIO(data), formats=['WEBP']) as image:
        if image.size != WORLD_SIZE:
            raise ValueError('Les dimensions de la carte d’Hyrule ont changé.')
        image.thumbnail((2100, 1600), Image.Resampling.LANCZOS)
        return image.convert('RGB')
