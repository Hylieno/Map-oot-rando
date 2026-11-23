"""Read player telemetry from the local Ocarina Atlas companion."""
from dataclasses import dataclass
from http.client import HTTPConnection, HTTPException
import json
from math import isfinite
from time import time


@dataclass(frozen=True)
class LinkPosition:
    scene: str
    age: str
    map_id: str | None
    x: float
    y: float
    z: float
    yaw: float


def parse_position(payload, now):
    if not isinstance(payload, dict) or payload.get('source') != 'memory' or payload.get('connected') is not True:
        return None
    updated = payload.get('updatedAt')
    if type(updated) not in (int, float) or not (now - 5) * 1000 <= updated <= (now + 1) * 1000:
        return None
    scene, age, map_id = (payload.get(key) for key in ('scene', 'age', 'mapId'))
    position = payload.get('position')
    if not isinstance(scene, str) or not scene or age not in ('child', 'adult') or not isinstance(position, dict):
        return None
    values = [position.get(key) for key in ('x', 'y', 'z', 'yaw')]
    if any(type(value) not in (int, float) or abs(value) > 100_000 or not isfinite(value) for value in values):
        return None
    return LinkPosition(scene, age.capitalize(), map_id if isinstance(map_id, str) else None, *values)


def read_link_position():
    # A fixed loopback GET never follows redirects or sends seed/save data.
    connection = HTTPConnection('127.0.0.1', 3000, timeout=0.65)
    try:
        connection.request('GET', '/api/lichii/state', headers={'Accept': 'application/json'})
        with connection.getresponse() as response:
            if response.status == 200:
                return parse_position(json.loads(response.read(256_000)), time())
    except (OSError, HTTPException, ValueError):
        pass
    finally:
        connection.close()
    return None
