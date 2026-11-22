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
