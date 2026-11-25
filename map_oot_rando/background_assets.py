"""Fetch and cache the exact published bytes used for map calibration."""
from hashlib import sha256
from pathlib import Path
from tempfile import NamedTemporaryFile
from urllib.request import Request, urlopen

from .save_profiles import local_tracker_dir


def verified_asset(url, digest, *, provider, extension, limit):
    cached = local_tracker_dir() / 'backgrounds' / f'{digest}.{extension}'

    def matches(data):
        return len(data) <= limit and sha256(data).hexdigest() == digest

    try:
        with cached.open('rb') as stream:
            data = stream.read(limit + 1)
        if matches(data):
            return data
    except OSError:
        pass

    request = Request(url, headers={'User-Agent': 'Map-oot-rando/1.0'})
    with urlopen(request, timeout=8) as response:
        if response.url != url:
            raise ValueError(f'Adresse {provider} modifiée.')
        data = response.read(limit + 1)
    if not matches(data):
        raise ValueError(f'Le fond {provider} a changé. Sa projection doit être vérifiée.')

    temporary = None
    try:
        cached.parent.mkdir(parents=True, exist_ok=True)
        with NamedTemporaryFile(dir=cached.parent, prefix='map-', suffix='.tmp', delete=False) as stream:
            temporary = Path(stream.name)
            stream.write(data)
        temporary.replace(cached)
    except OSError:
        pass  # An unwritable cache must not prevent displaying the verified map.
    finally:
        if temporary is not None:
            try:
                temporary.unlink(missing_ok=True)
            except OSError:
                pass
    return data
