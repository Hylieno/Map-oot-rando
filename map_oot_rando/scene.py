"""Map symbols derived from OotrR landmarks in the active resource's coordinates."""
from math import isfinite

from .model import REGION_NAMES, resource_region

MAP_SUFFIX = '.bcett.byml.zs'
REGION_VIEWS = {region: {'Child': f'{name} · Enfant', 'Adult': f'{name} · Adulte'}
                for region, name in REGION_NAMES.items()}
AGE_VIEWS = REGION_VIEWS['KokiriForest']
VIEWS = {label: (region, age) for region, ages in REGION_VIEWS.items()
         for age, label in ages.items()}
NEIGHBORS = {
    'KokiriForest': {'LostWood': 'front_of_lost_wood_entrance',
                     'HyruleField': 'front_of_hyrule_field_entrance'},
    'LostWood': {'KokiriForest': 'arrivee_de_kokiri'},
    'HyruleField': {'KokiriForest': 'front_of_lost_wood_bridge_entrance'},
}
LOST_WOOD_POINT_LABELS = {
    'front_of_sacred_forest_meadow_entrance': 'Vers le Bosquet sacré',
    'goron_city_side_before_entrance': 'Vers le Village Goron',
    'goron_city_side_after_entrance': 'Vers le Village Goron',
    'zora_river_entrance': 'Vers la Rivière Zora',
}
HYRULE_ANCHORS = {
    'Market': 'Porte de la Citadelle',
    'KakarikoVillage': 'Vers Cocorico',
    'GerudoValley': 'Vers la Vallée Gerudo',
    'LakeHylia': 'Vers le Lac Hylia',
}


def projection_points(region, sources):
    points = set()
    for source in sources.values():
        for actor in source['root'].get('Actors', ()):
            position = actor.get('Translate')
            if not position:
                continue
            gyaml = actor.get('Gyaml')
            label = None
            if region == 'LostWood':
                if gyaml == 'StartPos' and actor.get('Name') == 'LostWood_Entrance':
                    label = 'arrivee_de_kokiri'
            elif gyaml == 'MapIconEntranceAnchor':
                dynamic = actor.get('Dynamic')
                if isinstance(dynamic, dict) and dynamic.get('IsVisible') is not False:
                    label = HYRULE_ANCHORS.get(dynamic.get('Location'))
            elif gyaml == 'Land_HrlField_Bridge_A_01':
                label = 'Pont de la rivière'
            elif gyaml == 'Enemy_Skulltula_Gold' and actor.get('Hash') == 2177746409373494991:
                label = 'Arbre isolé près de Kokiri'
            if label:
                points.add((label, (position[0], position[2])))
    return points


def extract_scenes(maps, landmarks):
    scenes = {}
    for path in sorted(maps):
        region = resource_region(path)
        if region is None or not path.endswith(MAP_SUFFIX):
            continue
        if region != 'KokiriForest' and view_name(path) not in VIEWS:
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
        marks = landmarks(sources).get(region, {})
        rooms = sorted({(name, (low[0], low[2]), (high[0], high[2]))
                        for name, low, high in marks.get('rooms', ())})
        labels = LOST_WOOD_POINT_LABELS if region == 'LostWood' else {}
        points = {(labels.get(name, name), (position[0], position[2]))
                  for name, position in marks.get('points', ())}
        if region in {'LostWood', 'HyruleField'}:
            points.update(projection_points(region, sources))
        if rooms or points:
            scenes[path] = {'rooms': rooms, 'points': sorted(points)}
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


def view_name(resource):
    """Group scene layers within a region and age."""
    region = resource_region(resource)
    for age, label in REGION_VIEWS.get(region, {}).items():
        if resource in (f'Banc/{region}/{region}_{age}_{layer}{MAP_SUFFIX}'
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


SHARED_ENTRANCES = (
    'front_deku_tree_entrance',
    'front_of_hyrule_field_entrance',
    'front_of_lost_wood_entrance',
)


def field_atlas_scene(scenes, view):
    """Use adult house labels for a child map only in a confirmed shared frame."""
    from math import dist

    scene = scenes.get(view, {})
    if view != AGE_VIEWS['Child'] or AGE_VIEWS['Adult'] not in scenes:
        return scene
    adult = scenes[AGE_VIEWS['Adult']]

    def entrance(scene, name):
        points = {tuple(point) for label, point in scene.get('points', ()) if label == name}
        return next(iter(points)) if len(points) == 1 else None

    for name in SHARED_ENTRANCES:
        child_pos, adult_pos = entrance(scene, name), entrance(adult, name)
        if child_pos is None or adult_pos is None or dist(child_pos, adult_pos) > 0.5:
            return scene
    # OotrR numbers some unnamed rooms independently by age. Child numbering
    # can shift even when the same physical houses are in the same frame.
    return adult
