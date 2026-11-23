"""Map symbols derived from OotrR landmarks in the active resource's coordinates."""
from math import isfinite

from .model import REGION_NAMES, SURFACE_MIN_Y, resource_region

MAP_SUFFIX = '.bcett.byml.zs'
REGION_VIEWS = {region: {'Child': f'{name} · Enfant', 'Adult': f'{name} · Adulte'}
                for region, name in REGION_NAMES.items()}
# The four galleries are centered on Y=115, 110, 105 and 100. The lava cave chests lie below them.
GORON_LEVELS = ('Galerie supérieure', 'Galerie intermédiaire haute', 'Galerie intermédiaire basse',
                'Rez-de-chaussée', 'Grotte')
GORON_CRATER_FLOOR = 3
GORON_LOST_WOODS_FLOOR = 2
GORON_VIEWS = {age: tuple(f'{view} · {level}' for level in GORON_LEVELS)
               for age, view in REGION_VIEWS['GoronCity'].items()}
REGION_VIEWS['GoronCity'] = {age: views[0] for age, views in GORON_VIEWS.items()}
GORON_FLOORS = {view: index for views in GORON_VIEWS.values() for index, view in enumerate(views)}
DODONGO_LEVELS = ('Rez-de-chaussée', 'Étage', 'Arène du boss')
DODONGO_VIEWS = tuple(f'{REGION_NAMES["DodongoCavern"]} · {level}' for level in DODONGO_LEVELS)
FIRE_LEVELS = ('Rez-de-chaussée', '1er étage', '2e étage', '3e étage', '4e étage', 'Arène du boss')
FIRE_VIEWS = tuple(f'{REGION_NAMES["FireTemple"]} · {level}' for level in FIRE_LEVELS)
DUNGEON_FLOORS = {
    'DodongoCavern': tuple(zip(DODONGO_LEVELS, DODONGO_VIEWS)),
    'FireTemple': tuple(zip(FIRE_LEVELS, FIRE_VIEWS)),
}
DUNGEON_ATLAS_KEYS = {view: f'{level}F' for floors in DUNGEON_FLOORS.values()
                      for level, (_, view) in enumerate(floors[:-1], start=1)}
for region, floors in DUNGEON_FLOORS.items():
    REGION_VIEWS[region] = {None: floors[0][1]}
FLOOR_OPTIONS = {
    **{view: tuple(zip(GORON_LEVELS, views)) for views in GORON_VIEWS.values() for view in views},
    **{view: floors for floors in DUNGEON_FLOORS.values() for _, view in floors},
}
AGE_VIEWS = REGION_VIEWS['KokiriForest']
VIEWS = {label: (region, age) for region, ages in REGION_VIEWS.items()
         for age, label in ages.items()}
BURNT_VILLAGE = 'Cocorico · Après l’incendie'
VIEWS[BURNT_VILLAGE] = ('KakarikoVillage', 'Adult')
UNDERGROUND_VIEWS = {region: {age: f'{view} · Souterrains' for age, view in REGION_VIEWS[region].items()}
                     for region in SURFACE_MIN_Y}
UNDERGROUND_LABELS = {view for ages in UNDERGROUND_VIEWS.values() for view in ages.values()}
VIEWS.update({view: (region, age) for region, ages in UNDERGROUND_VIEWS.items()
              for age, view in ages.items()})
VIEWS.update({view: ('GoronCity', age) for age, views in GORON_VIEWS.items() for view in views})
VIEWS.update({view: (region, None) for region, floors in DUNGEON_FLOORS.items() for _, view in floors})
NEIGHBORS = {
    'KokiriForest': {'LostWood': 'front_of_lost_wood_entrance',
                     'HyruleField': 'front_of_hyrule_field_entrance'},
    'LostWood': {'KokiriForest': 'arrivee_de_kokiri', 'SacredForestMeadow': 'Vers le Bosquet sacré',
                 'GoronCity': 'Vers le Village Goron', 'ZoraRiver': 'Vers la Rivière Zora'},
    'HyruleField': {'KokiriForest': 'front_of_lost_wood_bridge_entrance',
                    'KakarikoVillage': 'Vers Cocorico', 'ZoraRiver': 'Vers la Rivière Zora'},
    'SacredForestMeadow': {'LostWood': 'front_of_lost_wood_entrance'},
    'KakarikoVillage': {'HyruleField': 'Vers la plaine d’Hyrule', 'Graveyard': 'Vers le cimetière',
                        'DeathMountainTrail': 'Vers le Mont du Péril'},
    'Graveyard': {'KakarikoVillage': 'Vers Cocorico'},
    'DeathMountainTrail': {'KakarikoVillage': 'Vers Cocorico', 'GoronCity': 'Repère Goron',
                           'DodongoCavern': 'Vers la Caverne Dodongo', 'DeathMountainCrater': 'Repère du cratère'},
    'GoronCity': {'DeathMountainTrail': 'Vers le mont du Péril', 'DeathMountainCrater': 'Repère nord Goron',
                  'LostWood': 'Repère des Bois Perdus'},
    'DodongoCavern': {'DeathMountainTrail': 'Vers le mont du Péril'},
    'DeathMountainCrater': {'DeathMountainTrail': 'Vers le mont du Péril', 'GoronCity': 'goron_city_entrance',
                           'FireTemple': 'Temple du Feu'},
    'FireTemple': {'DeathMountainCrater': 'Vers le cratère'},
    'ZoraRiver': {'LostWood': 'Vers les Bois Perdus', 'HyruleField': 'Vers la plaine d’Hyrule',
                  'ZoraDomain': 'Vers le Domaine Zora'},
    'ZoraDomain': {'ZoraRiver': 'Vers la Rivière Zora'},
}
KAKARIKO_ENTRANCES = {
    'HyruleField': 'Vers la plaine d’Hyrule',
    'DeathMountainTrail': 'Vers le Mont du Péril',
    'Graveyard': 'Vers le cimetière',
    'BottomOfTheWell': 'Puits',
}
KAKARIKO_BUILDINGS = {
    'Land_Kakariko_WindmillHouse_A_01': 'Moulin',
    'Land_Kakariko_House_A_01': 'Maison au sud',
}
GRAVEYARD_LANDMARKS = {
    'Obj_Graveyard_Tombstone_A_03': 'Monument royal',
    'Obj_Graveyard_Tombstone_A_02': 'Stèle royale sud',
    'Land_Graveyard_House_A_01': 'Maison du gardien',
}
GRAVEYARD_STONES = {
    3584790071721093975: 'Pilier nord du portail', 14138423618786081511: 'Pilier nord du portail',
    1477508902893678199: 'Première tombe au nord', 14062658801796005543: 'Première tombe au nord',
    17966403985780819162: 'Tombe au sud-est', 1899631685438434168: 'Tombe au sud-est',
    10113284509563176489: 'Tombe de la rangée centrale', 13948460953459451532: 'Tombe de la rangée centrale',
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
    'ZoraRiver': 'Vers la Rivière Zora',
}
ZORA_RIVER_EXITS = {
    'ZoraRiver_LostWoodSide': NEIGHBORS['ZoraRiver']['LostWood'],
    'ZoraRiver_Entrance': NEIGHBORS['ZoraRiver']['HyruleField'],
}
ENTRANCE_LABELS = {
    'KakarikoVillage': KAKARIKO_ENTRANCES,
    'Graveyard': {'KakarikoVillage': 'Vers Cocorico'},
    'HyruleField': HYRULE_ANCHORS,
    'ZoraRiver': {'ZoraDomain': NEIGHBORS['ZoraRiver']['ZoraDomain']},
    'ZoraDomain': NEIGHBORS['ZoraDomain'],
    'DeathMountainTrail': {
        'DeathMountainCrater': 'Repère du cratère',
        'DodongoCavern': 'Repère Dodongo',
        'GoronCity': 'Repère Goron',
        'KakarikoVillage': 'Repère Cocorico',
    },
    'GoronCity': {
        'DeathMountainCrater': 'Repère nord Goron',
        'DeathMountainTrail': 'Vers le mont du Péril',
        'LostWood': 'Repère des Bois Perdus',
    },
    'DodongoCavern': {'DeathMountainTrail': 'Vers le mont du Péril'},
    'FireTemple': NEIGHBORS['FireTemple'],
    'DeathMountainCrater': {
        'DeathMountainTrail': 'Vers le mont du Péril',
        'GoronCity': 'Repère Goron depuis le cratère',
        'FireTemple': 'Temple du Feu',
    },
}
CRATER_ANCHORS = {
    'Land_DeathMtCrater_Temple_A_01': 'Pied du Temple du Feu',
    'Land_DeathMtCrater_Prop_A_03': 'Pont sud-ouest',
    'Land_DeathMtCrater_Cliff_A_04': 'Corniche sud',
}
DODONGO_ANCHORS = {
    'Land_DodongoCave_01_Floor_A_04': 'Plateforme centrale Dodongo',
    'Land_DodongoCave_19_Floor_A_01': 'Escaliers nord Dodongo',
    'Land_DodongoCave_05_Floor_A_01': 'Plateforme nord-ouest Dodongo',
    'Land_DodongoCave_05_Floor_A_08': 'Plateforme nord-est Dodongo',
    'Land_DodongoCave_05_Floor_A_09': 'Plateforme sud-est Dodongo',
    'Land_DodongoCave_11_Floor_A_01': 'Salle ouest basse Dodongo',
    'Land_DodongoCave_05_Floor_A_06': 'Plateforme ouest Dodongo',
    'Land_DodongoCave_12_Floor_A_01': 'Salle ouest haute Dodongo',
    'Land_DodongoCave_05_Floor_A_03': 'Plateforme haute Dodongo',
    'Land_DodongoCave_16_Floor_A_06': 'Îlot nord-ouest Dodongo',
    'Land_DodongoCave_16_Floor_A_05': 'Îlot sud Dodongo',
    'Land_DodongoCave_16_Floor_A_01': 'Îlot est Dodongo',
    'Land_DodongoCave_16_Floor_A_07': 'Îlot nord Dodongo',
}
GORON_ANCHORS = {
    'Land_Goron_Ground_A_05': 'Place centrale Goron',
    'Land_Goron_Ground_A_31': 'Seuil nord Goron',
    'Land_Goron_Ground_A_11': 'Galerie est Goron',
}
TRAIL_LABELS = {
    'crater_entrance': 'Vers le cratère',
    'dodongo_cavern_entrance': 'Vers la Caverne Dodongo',
    'goron_city_entrance': 'Vers le Village Goron',
    'kakariko_entrance': 'Vers Cocorico',
}
GROVE_ANCHORS = {
    'Obj_WarpPoint_A_02': 'Plateforme de téléportation',
    'Land_ForestTemple_StoneFrame_A_01': 'Seuil du temple',
    'Land_SacredForest_TreeStump_A_01': 'Souche',
    'Land_SacredForest_MazesWall_A_01': 'Dernier mur au sud',
}
GROVE_STAIRS = {
    2413410251944505368: 'Escalier haut ouest', 17304470267011637740: 'Escalier haut ouest',
    6139890283971412623: 'Escalier haut est', 16934882182567342749: 'Escalier haut est',
    12781997514938194022: 'Escalier bas ouest', 7113370927714814423: 'Escalier bas ouest',
    16405524742880159804: 'Escalier bas est', 8098648085076932584: 'Escalier bas est',
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
            elif region == 'ZoraRiver' and gyaml == 'FieldAndDungeonEntranceEventRequestActor':
                label = ZORA_RIVER_EXITS.get(actor.get('Name'))
            elif region == 'SacredForestMeadow':
                label = GROVE_ANCHORS.get(gyaml)
                if gyaml in {'Land_SacredForest_Prop_A_33', 'Land_SacredForest_Prop_A_41'}:
                    label = GROVE_STAIRS.get(actor.get('Hash'))
            elif gyaml == 'MapIconEntranceAnchor':
                dynamic = actor.get('Dynamic')
                if isinstance(dynamic, dict) and (region in {'GoronCity', 'DeathMountainCrater'}
                                                  or dynamic.get('IsVisible') is not False):
                    entrances = ENTRANCE_LABELS.get(region, {})
                    label = entrances.get(dynamic.get('Location'))
            elif region == 'KakarikoVillage':
                label = KAKARIKO_BUILDINGS.get(gyaml)
            elif region == 'Graveyard':
                label = GRAVEYARD_LANDMARKS.get(gyaml)
                if gyaml in {'Land_Graveyard_Gate_A_09', 'Obj_Tombstone_A_01'}:
                    label = GRAVEYARD_STONES.get(actor.get('Hash'))
            elif region == 'DeathMountainTrail' and gyaml == 'Land_DeathMtTrail_Rock_A_06':
                label = 'Rocher au virage sud'
            elif region == 'GoronCity':
                label = GORON_ANCHORS.get(gyaml)
            elif region == 'DodongoCavern':
                label = DODONGO_ANCHORS.get(gyaml)
            elif region == 'DeathMountainCrater':
                label = CRATER_ANCHORS.get(gyaml)
            elif gyaml == 'Land_HrlField_Bridge_A_01':
                label = 'Pont de la rivière'
            elif gyaml == 'Enemy_Skulltula_Gold' and actor.get('Hash') == 2177746409373494991:
                label = 'Arbre isolé près de Kokiri'
            if label:
                x, z = position[0], position[2]
                if region == 'GoronCity' and gyaml == 'MapIconEntranceAnchor':
                    # The passage has two story variants with indistinguishable anchors.
                    x, z = round(x, 4), round(z, 4)
                points.add((label, (x, z)))
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
        labels = {'LostWood': LOST_WOOD_POINT_LABELS, 'DeathMountainTrail': TRAIL_LABELS}.get(region, {})
        points = {(labels.get(name, name), (position[0], position[2]))
                  for name, position in marks.get('points', ())}
        if region != 'KokiriForest':
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
    if region in DUNGEON_FLOORS and resource in (
            f'Banc/{region}/{region}_{layer}{MAP_SUFFIX}' for layer in ('Static', 'Dynamic')):
        return REGION_VIEWS[region][None]
    if region == 'KakarikoVillage' and resource in (
            f'Banc/{region}/{region}_Adult_Alternative_{layer}{MAP_SUFFIX}'
            for layer in ('Static', 'Dynamic')):
        return BURNT_VILLAGE
    if region == 'ZoraDomain' and resource in (
            f'Banc/{region}/{region}_Adult_Alternative_{layer}{MAP_SUFFIX}'
            for layer in ('Static', 'Dynamic')):
        return REGION_VIEWS[region]['Adult']
    for age, label in REGION_VIEWS.get(region, {}).items():
        if resource in (f'Banc/{region}/{region}_{age}_{layer}{MAP_SUFFIX}'
                        for layer in ('Static', 'Dynamic')):
            return label
    return resource


def location_view(row):
    view = view_name(row.resource)
    if row.underground and view in VIEWS:
        region, age = VIEWS[view]
        return UNDERGROUND_VIEWS[region][age]
    if view in GORON_FLOORS and row.position is not None:
        y = row.position[1]
        floor = sum(y < boundary for boundary in (112.5, 107.5, 101.5, 96.5))
        return GORON_VIEWS[VIEWS[view][1]][floor]
    if view == FIRE_VIEWS[0] and row.position is not None:
        if row.id == 'boss#Volvagia' or row.category == 'full_bossheart':
            return FIRE_VIEWS[-1]
        # Floor cuts follow the native minimap. The arena shares the ground-floor elevation.
        floor = sum(row.position[1] >= boundary for boundary in (124, 142, 164, 182))
        return FIRE_VIEWS[floor]
    if view == DODONGO_VIEWS[0] and row.position is not None:
        y = row.position[1]
        if y < 82:
            return DODONGO_VIEWS[2]
        if y >= 105:
            return DODONGO_VIEWS[1]
    return view


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
