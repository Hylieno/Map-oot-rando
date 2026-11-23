"""Map symbols derived from OotrR landmarks in the active resource's coordinates."""
from math import isfinite

KOKIRI = 'Banc/KokiriForest/'
MAP_SUFFIX = '.bcett.byml.zs'


def extract_scenes(maps, landmarks):
    scenes = {}
    for path in sorted(maps):
        if not path.startswith(KOKIRI) or not path.endswith(MAP_SUFFIX):
            continue
        # Static and dynamic resources with the same scene and age use one frame.
        # Keep generic resource names and the other age independent.
        stem = path.removesuffix(MAP_SUFFIX)
        base, _, layer = stem.rpartition('_')
        sources = {path: maps[path]}
        if layer in {'Static', 'Dynamic'}:
            sibling = base + ('_Static' if layer == 'Dynamic' else '_Dynamic') + MAP_SUFFIX
            if sibling in maps:
                sources[sibling] = maps[sibling]
        marks = landmarks(sources).get('KokiriForest', {})
        rooms = sorted({(name, (low[0], low[2]), (high[0], high[2]))
                        for name, low, high in marks.get('rooms', ())})
        points = sorted({(name, (position[0], position[2]))
                         for name, position in marks.get('points', ())})
        if rooms or points:
            scenes[path] = {'rooms': rooms, 'points': points}
    return scenes


def read_scenes(document):
    """Validate optional scene data while accepting older saved maps."""
    scenes = document.get('scenes', {})
    if not isinstance(scenes, dict):
        raise ValueError('Fond de carte invalide')
    for scene in scenes.values():
        for entries, size in ((scene['rooms'], 3), (scene['points'], 2)):
            for entry in entries:
                if (len(entry) != size or not isinstance(entry[0], str)
                        or any(len(point) != 2 or any(type(v) not in (int, float)
                               or not isfinite(v) for v in point) for point in entry[1:])):
                    raise ValueError('Repère de carte invalide')
    return scenes


AGE_VIEWS = {'Child': 'Kokiri Forest · Enfant', 'Adult': 'Kokiri Forest · Adulte'}


def view_name(resource):
    """Group the known Kokiri layers without mixing different ages."""
    for age, label in AGE_VIEWS.items():
        if resource in (f'{KOKIRI}KokiriForest_{age}_{layer}{MAP_SUFFIX}'
                        for layer in ('Static', 'Dynamic')):
            return label
    return resource


def group_scenes(scenes):
    grouped = {}
    for resource, scene in scenes.items():
        view = grouped.setdefault(view_name(resource), {'rooms': set(), 'points': set()})
        view['rooms'].update((name, tuple(low), tuple(high)) for name, low, high in scene['rooms'])
        view['points'].update((name, tuple(point)) for name, point in scene['points'])
    return {key: {kind: sorted(rows) for kind, rows in scene.items()}
            for key, scene in grouped.items()}
