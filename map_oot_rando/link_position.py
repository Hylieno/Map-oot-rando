"""Decode Link's position through OotrR's already attached game-memory reader."""
from dataclasses import dataclass
from math import atan2, degrees, hypot, isfinite
import re
import struct


@dataclass(frozen=True)
class LinkPosition:
    scene: str
    age: str
    x: float
    y: float
    z: float
    yaw: float


# Position and scene layout documented by Ocarina Atlas for this NSO.
MAIN_HEADER = struct.pack('<II', 1, 0x03C4705C)
PLAYER_SINGLETONS = (0x04E6C7A8, 0x04E6C938)
PLAYER_VTABLE = 0x04BA27C8
POSITION_VTABLES = (0x04BA1818, 0x03EE4F8C)
SCENE_PATH = re.compile(rb'Work/Banc/Scene/([A-Za-z0-9_]+)/([A-Za-z0-9_]+)\.bcett\b')
SCENE_SUFFIX = re.compile(r'(?:_(Child|Adult)(?:_Alternative)?)?(?:_(?:Static|Dynamic))?$')


def _pointer(blob, offset=0):
    address = struct.unpack_from('<Q', blob, offset)[0]
    return address if 0x10000 <= address < 1 << 48 and address % 8 == 0 else 0


def read_link_position(memory, age):
    # OotrR uses the validated GameData slot to locate the module under ASLR.
    from oot_rando.tracker.live_memory import GAMEDATA_SLOT, HOOKSHOT_MAIN, LiveUnavailable

    main = memory.slot - GAMEDATA_SLOT + HOOKSHOT_MAIN
    if memory.read(main, len(MAIN_HEADER)) != MAIN_HEADER:
        return None

    for slot in PLAYER_SINGLETONS:
        try:
            position = _read_player(memory.read, main, slot, age)
        except (LiveUnavailable, OSError, struct.error):
            continue
        if position:
            return position
    return None


def _read_player(read, main, slot, age):
    singleton = _pointer(read(main + slot, 8))
    if not singleton:
        return None
    player = _pointer(read(singleton + 0x10, 8))
    if not player:
        return None
    header = read(player, 0x60)
    if _pointer(header) != main + PLAYER_VTABLE:
        return None
    count = struct.unpack_from('<I', header, 0x50)[0]
    components = _pointer(header, 0x58)
    if not 36 < count <= 128 or not components:
        return None
    table = read(components, 37 * 8)
    pose, scene_record = _pointer(table, 36 * 8), _pointer(table, 7 * 8)
    if not pose:
        return None
    data = read(pose, 0x34)
    vtables = tuple(main + offset for offset in POSITION_VTABLES)
    if struct.unpack_from('<QQ', data) != vtables or _pointer(data, 0x10) != player:
        return None
    x, y, z, dx, _, dz = struct.unpack_from('<6f', data, 0x1C)
    if not all(isfinite(coord) and abs(coord) < 15_000 for coord in (x, y, z)):
        return None
    if max(abs(x), abs(y), abs(z)) < 0.001:
        return None
    scene = _find_scene(read, player, scene_record)
    if not scene:
        return None
    region = scene[1].decode('ascii')
    resource = scene[2].decode('ascii')
    suffix = SCENE_SUFFIX.search(resource)
    age = suffix[1] or age
    if age not in {'Child', 'Adult'}:
        return None
    yaw = degrees(atan2(dx, -dz)) % 360 if isfinite(dx) and isfinite(dz) and hypot(dx, dz) > 0.01 else 0
    return LinkPosition(region, age, x, y, z, yaw)


def _find_scene(read, player, scene_record):
    from oot_rando.tracker.live_memory import LiveUnavailable

    if scene_record:
        try:
            scene = SCENE_PATH.search(read(scene_record + 0x34, 0x80))
        except (LiveUnavailable, OSError):
            pass
        else:
            if scene:
                return scene
    return SCENE_PATH.search(read(player + 0x768, 0x480))
