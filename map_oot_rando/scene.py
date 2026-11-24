"""Map symbols derived from OotrR landmarks in the active resource's coordinates."""
from math import isfinite

from .model import REGION_NAMES, SURFACE_MIN_Y, read_position, resource_region

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
JABU_LEVELS = ('Rez-de-chaussée', 'Sous-sol', 'Étage', 'Arène de Barinade')
JABU_VIEWS = tuple(f'{REGION_NAMES["InsideJabuJabuBelly"]} · {level}' for level in JABU_LEVELS)
DEKU_LEVELS = ('Rez-de-chaussée', '1er étage', '2e étage', 'Sous-sol', 'Sous-sol profond', 'Arène de Gohma')
DEKU_VIEWS = tuple(f'{REGION_NAMES["InsideTheDekuTree"]} · {level}' for level in DEKU_LEVELS)
FOREST_LEVELS = ('Rez-de-chaussée', '1er étage', '2e étage', 'Sous-sol', 'Sous-sol profond', 'Arène du boss')
FOREST_VIEWS = tuple(f'{REGION_NAMES["ForestTemple"]} · {level}' for level in FOREST_LEVELS)
WELL_LEVELS = ('Sous-sol', 'Sous-sol profond')
WELL_VIEWS = tuple(f'{REGION_NAMES["BottomOfTheWell"]} · {level}' for level in WELL_LEVELS)
SHADOW_LEVELS = ('Sous-sol 1', 'Sous-sol 2', 'Sous-sol 3', 'Sous-sol 4', 'Arène de Bongo Bongo')
SHADOW_VIEWS = tuple(f'{REGION_NAMES["ShadowTemple"]} · {level}' for level in SHADOW_LEVELS)
SPIRIT_LEVELS = ('Rez-de-chaussée', '1er étage', '2e étage', '3e étage', 'Arène de Twinrova')
SPIRIT_VIEWS = tuple(f'{REGION_NAMES["SpiritTemple"]} · {level}' for level in SPIRIT_LEVELS)
WATER_LEVELS = ('2e étage', '1er étage', 'Rez-de-chaussée', 'Sous-sol')
WATER_VIEWS = tuple(f'{REGION_NAMES["WaterTemple"]} · {level}' for level in WATER_LEVELS)
GANON_DUNGEON_LEVELS = ('Épreuves', 'Accès à la tour', 'Tour · 1er étage',
                        'Tour · 2e étage', 'Tour · 3e étage', 'Sommet')
GANON_DUNGEON_VIEWS = tuple(f'{REGION_NAMES["InsideGanonCastle"]} · {level}' for level in GANON_DUNGEON_LEVELS)
TRAINING_LEVELS = ('Salles et labyrinthe', 'Passerelle du labyrinthe')
TRAINING_VIEWS = tuple(f'{REGION_NAMES["GerudoTrainingGround"]} · {level}' for level in TRAINING_LEVELS)
TRAINING_WALKWAY_GATE = 18314542979296415492
TRAINING_TO_WALKWAY = 'Vers la passerelle'
TRAINING_TO_STATUE = 'Vers la salle de la statue'
DUNGEON_FLOORS = {
    'DodongoCavern': tuple(zip(DODONGO_LEVELS, DODONGO_VIEWS)),
    'FireTemple': tuple(zip(FIRE_LEVELS, FIRE_VIEWS)),
    'InsideJabuJabuBelly': tuple(zip(JABU_LEVELS, JABU_VIEWS)),
    'InsideTheDekuTree': tuple(zip(DEKU_LEVELS, DEKU_VIEWS)),
    'ForestTemple': tuple(zip(FOREST_LEVELS, FOREST_VIEWS)),
    'BottomOfTheWell': tuple(zip(WELL_LEVELS, WELL_VIEWS)),
    'ShadowTemple': tuple(zip(SHADOW_LEVELS, SHADOW_VIEWS)),
    'SpiritTemple': tuple(zip(SPIRIT_LEVELS, SPIRIT_VIEWS)),
    'WaterTemple': tuple(zip(WATER_LEVELS, WATER_VIEWS)),
    'InsideGanonCastle': tuple(zip(GANON_DUNGEON_LEVELS, GANON_DUNGEON_VIEWS)),
    'GerudoTrainingGround': tuple(zip(TRAINING_LEVELS, TRAINING_VIEWS)),
}
DUNGEON_ATLAS_KEYS = {
    **dict(zip(DODONGO_VIEWS, ('1F', '2F'))),
    **dict(zip(FIRE_VIEWS, ('1F', '2F', '3F', '4F', '5F'))),
    **dict(zip(JABU_VIEWS, ('1F', 'S1', '2F'))),
    **dict(zip(DEKU_VIEWS, ('1F', '2F', '3F', 'S1', 'S2'))),
    **dict(zip(FOREST_VIEWS, ('1F', '2F', '3F', 'S1', 'S2'))),
    **dict(zip(WELL_VIEWS, ('S1', 'S2'))),
    **dict(zip(SHADOW_VIEWS, ('S1', 'S2', 'S3', 'S4'))),
    **dict(zip(SPIRIT_VIEWS, ('1F', '2F', '3F', '4F'))),
    **dict(zip(WATER_VIEWS, ('3F', '2F', '1F', 'S1'))),
}
FOUNTAIN_DUNGEON_AGES = {'IceCavern': 'Adult', 'InsideJabuJabuBelly': 'Child'}
JABU_ROOM_VIEWS = {
    **dict.fromkeys((9, 12), JABU_VIEWS[0]),
    **dict.fromkeys((3, 13, 14), JABU_VIEWS[1]),
    **dict.fromkeys((5, 6, 17), JABU_VIEWS[2]),
    15: JABU_VIEWS[3],
}
DEKU_ROOM_VIEWS = {
    **dict.fromkeys((1, 2), DEKU_VIEWS[1]),
    3: DEKU_VIEWS[2],
    **dict.fromkeys((4, 5, 11), DEKU_VIEWS[3]),
    9: DEKU_VIEWS[4],
    10: DEKU_VIEWS[5],
}
FOREST_ROOM_VIEWS = {
    **dict.fromkeys((2, 4, 6, 12, 14, 22), FOREST_VIEWS[0]),
    **dict.fromkeys((0, 8, 16, 17, 18), FOREST_VIEWS[1]),
    15: FOREST_VIEWS[3],
    27: FOREST_VIEWS[4],
    29: FOREST_VIEWS[5],
}
SHADOW_ROOM_VIEWS = {
    **dict.fromkeys((0, 2, 3, 4, 30), SHADOW_VIEWS[0]),
    **dict.fromkeys((6, 7), SHADOW_VIEWS[1]),
    **dict.fromkeys((9, 10, 11, 14, 15, 16, 31), SHADOW_VIEWS[2]),
    **dict.fromkeys((17, 19, 20, 21), SHADOW_VIEWS[3]),
    24: SHADOW_VIEWS[4],
}
SPIRIT_ROOM_FLOORS = {
    **dict.fromkeys((0, 2, 3, 4, 5, 14, 15, 16), 0),
    **dict.fromkeys((6, 7, 18), 1),
    **dict.fromkeys((9, 10, 22, 23, 26), 2),
    **dict.fromkeys((27, 29, 31), 3),
    33: 4,
}
WATER_ROOM_FLOORS = {
    **dict.fromkeys((1, 7, 17), 0),
    **dict.fromkeys((0, 4, 20, 21, 25), 1),
    **dict.fromkeys((3, 8, 15, 18, 23, 24), 2),
    2: 3,
}
for region, floors in DUNGEON_FLOORS.items():
    REGION_VIEWS[region] = {None: floors[0][1]}
REGION_VIEWS['IceCavern'] = {None: REGION_NAMES['IceCavern']}
REGION_VIEWS['SageRoom'] = {None: REGION_NAMES['SageRoom']}
DREAM_SCENE_VIEWS = {
    'EnemyMuseum': 'Monde des rêves · Musée',
    'BossRushIntervalRoom': 'Monde des rêves · Salle intermédiaire',
}
REGION_VIEWS['DreamWorld'] = {None: DREAM_SCENE_VIEWS['EnemyMuseum']}
CASTLE_VIEWS = tuple(f'{REGION_NAMES["HyruleCastle"]} · {area}' for area in ('Abords', 'Cour'))
CASTLE_OUTSKIRTS, CASTLE_COURT = CASTLE_VIEWS
REGION_VIEWS['HyruleCastle'] = {'Child': CASTLE_OUTSKIRTS}
GANON_AREAS = ('Abords', 'Effondrement')
GANON_OUTSKIRTS, GANON_ESCAPE = (f'{REGION_NAMES["GanonCastle"]} · {area}' for area in GANON_AREAS)
REGION_VIEWS['GanonCastle'] = {'Adult': GANON_OUTSKIRTS}
del REGION_VIEWS['GerudoFortress']['Child']
MARKET_CASTLE_AGES = {'HyruleCastle': 'Child', 'GanonCastle': 'Adult'}
SHARED_DUNGEONS = frozenset(region for region, views in REGION_VIEWS.items() if None in views)
FLOOR_OPTIONS = {
    **{view: tuple(zip(GORON_LEVELS, views)) for views in GORON_VIEWS.values() for view in views},
    **{view: floors for floors in DUNGEON_FLOORS.values() for _, view in floors},
    **dict.fromkeys(CASTLE_VIEWS, tuple(zip(('Abords', 'Cour'), CASTLE_VIEWS))),
    **dict.fromkeys((GANON_OUTSKIRTS, GANON_ESCAPE),
                    tuple(zip(GANON_AREAS, (GANON_OUTSKIRTS, GANON_ESCAPE)))),
    **dict.fromkeys(DREAM_SCENE_VIEWS.values(),
                    tuple(zip(('Musée', 'Salle intermédiaire'), DREAM_SCENE_VIEWS.values()))),
}
AGE_VIEWS = REGION_VIEWS['KokiriForest']
VIEWS = {label: (region, age) for region, ages in REGION_VIEWS.items()
         for age, label in ages.items()}
BURNT_VILLAGE = 'Cocorico · Après l’incendie'
VIEWS[BURNT_VILLAGE] = ('KakarikoVillage', 'Adult')
VIEWS[CASTLE_COURT] = ('HyruleCastle', 'Child')
VIEWS[GANON_ESCAPE] = ('GanonCastle', 'Adult')
VIEWS.update({view: ('DreamWorld', None) for view in DREAM_SCENE_VIEWS.values()})
UNDERGROUND_VIEWS = {region: {age: f'{view} · Souterrains' for age, view in REGION_VIEWS[region].items()}
                     for region in SURFACE_MIN_Y}
UNDERGROUND_LABELS = {view for ages in UNDERGROUND_VIEWS.values() for view in ages.values()}
VIEWS.update({view: (region, age) for region, ages in UNDERGROUND_VIEWS.items()
              for age, view in ages.items()})
VIEWS.update({view: ('GoronCity', age) for age, views in GORON_VIEWS.items() for view in views})
VIEWS.update({view: (region, None) for region, floors in DUNGEON_FLOORS.items() for _, view in floors})
NATIVE_FLOOR_VIEWS = {(VIEWS[view][0], key): view for view, key in DUNGEON_ATLAS_KEYS.items()}
NEIGHBORS = {
    'KokiriForest': {'LostWood': 'front_of_lost_wood_entrance',
                     'HyruleField': 'front_of_hyrule_field_entrance',
                     'KokiriBridge': 'Vers le pont de Kokiri',
                     'InsideTheDekuTree': 'front_deku_tree_entrance', 'DreamWorld': 'Lit de Link'},
    'KokiriBridge': {'KokiriForest': 'Vers le village Kokiri', 'HyruleField': 'front_of_hyrule_field_entrance'},
    'DreamWorld': {'KokiriForest': 'Retour à la forêt Kokiri'},
    'LostWood': {'KokiriForest': 'arrivee_de_kokiri', 'SacredForestMeadow': 'Vers le Bosquet sacré',
                 'GoronCity': 'Vers le Village Goron', 'ZoraRiver': 'Vers la Rivière Zora'},
    'HyruleField': {'KokiriForest': 'front_of_lost_wood_bridge_entrance',
                    'KakarikoVillage': 'Vers Cocorico', 'ZoraRiver': 'Vers la Rivière Zora',
                    'Market': 'Porte de la Citadelle', 'GerudoValley': 'Vers la Vallée Gerudo',
                    'LakeHylia': 'Vers le Lac Hylia', 'LonLonRanch': 'Vers le ranch Lon Lon'},
    'LonLonRanch': {'HyruleField': 'Sortie du ranch'},
    'LakeHylia': {'HyruleField': 'Vers la plaine d’Hyrule', 'GerudoValley': 'Vers la Vallée Gerudo',
                  'ZoraDomain': 'Vers le Domaine Zora', 'WaterTemple': 'Vers le Temple de l’Eau'},
    'WaterTemple': {'LakeHylia': 'Vers le Lac Hylia'},
    'GerudoValley': {'HyruleField': 'Vers la plaine d’Hyrule', 'GerudoFortress': 'Vers la Forteresse Gerudo',
                    'LakeHylia': 'Vers le Lac Hylia'},
    'GerudoFortress': {'GerudoValley': 'Vers la Vallée Gerudo',
                       'GerudoTrainingGround': 'Vers le centre d’entraînement',
                       'HountedWasteland': 'Vers le Désert hanté'},
    'GerudoTrainingGround': {'GerudoFortress': 'Vers la Forteresse Gerudo'},
    'HountedWasteland': {'GerudoFortress': 'Vers la Forteresse Gerudo',
                        'DesertColossus': 'Vers le Colosse du désert'},
    'DesertColossus': {'HountedWasteland': 'Vers le Désert hanté',
                      'SpiritTemple': 'Vers le Temple de l’Esprit'},
    'SpiritTemple': {'DesertColossus': 'Vers le Colosse du désert'},
    'Market': {'HyruleField': 'Vers la plaine d’Hyrule', 'HyruleCastle': 'Vers le Château d’Hyrule',
               'GanonCastle': 'Vers le Château de Ganon', 'TempleOfTime': 'Vers le Temple du Temps'},
    'TempleOfTime': {'Market': 'Sortie du temple', 'SageRoom': 'Piédestal de l’épée'},
    'SageRoom': {'TempleOfTime': 'Temple du Temps'},
    'HyruleCastle': {'Market': 'Vers la Citadelle d’Hyrule'},
    'GanonCastle': {'Market': 'Vers la Citadelle d’Hyrule',
                    'InsideGanonCastle': 'Entrée du château'},
    'InsideGanonCastle': {'GanonCastle': 'Vers les abords'},
    'SacredForestMeadow': {'LostWood': 'front_of_lost_wood_entrance',
                           'ForestTemple': 'outside_of_forest_temple_entrance'},
    'ForestTemple': {'SacredForestMeadow': 'Vers le Bosquet sacré'},
    'KakarikoVillage': {'HyruleField': 'Vers la plaine d’Hyrule', 'Graveyard': 'Vers le cimetière',
                        'DeathMountainTrail': 'Vers le Mont du Péril', 'BottomOfTheWell': 'Puits'},
    'BottomOfTheWell': {'KakarikoVillage': 'Vers Cocorico'},
    'Graveyard': {'KakarikoVillage': 'Vers Cocorico', 'ShadowTemple': 'Vers le Temple de l’Ombre'},
    'ShadowTemple': {'Graveyard': 'Vers le cimetière'},
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
    'ZoraDomain': {'ZoraRiver': 'Vers la Rivière Zora', 'ZoraFountain': 'Vers la Fontaine Zora',
                   'LakeHylia': 'Vers le Lac Hylia'},
    'ZoraFountain': {'ZoraDomain': 'Vers le Domaine Zora', 'IceCavern': 'Vers la Caverne de glace',
                     'InsideJabuJabuBelly': 'Vers Jabu-Jabu'},
    'IceCavern': {'ZoraFountain': 'Vers la Fontaine Zora'},
    'InsideJabuJabuBelly': {'ZoraFountain': 'Vers la Fontaine Zora'},
    'InsideTheDekuTree': {'KokiriForest': 'Vers la forêt Kokiri'},
}
SIDE_PORTALS = {
    'GerudoTrainingGround': {
        TRAINING_TO_WALKWAY: ('GerudoTrainingGround', TRAINING_VIEWS[1], 'Passerelle', TRAINING_TO_STATUE),
        TRAINING_TO_STATUE: ('GerudoTrainingGround', TRAINING_VIEWS[0], 'Salle de la statue', TRAINING_TO_WALKWAY),
    },
    'DreamWorld': {
        'Organisateur du défi': ('DreamWorld', DREAM_SCENE_VIEWS['BossRushIntervalRoom'], 'Défi des boss', None),
    },
    'DesertColossus': {
        'spirit_temple_left_hand_entrance': ('SpiritTemple', SPIRIT_VIEWS[2], 'Temple · main gauche', 'left_hand_entrance'),
        'spirit_temple_right_hand_entrance': ('SpiritTemple', SPIRIT_VIEWS[2], 'Temple · main droite', 'right_hand_entrance'),
    },
    'SpiritTemple': {
        'left_hand_entrance': ('DesertColossus', None, 'Colosse · main gauche', 'spirit_temple_left_hand_entrance'),
        'right_hand_entrance': ('DesertColossus', None, 'Colosse · main droite', 'spirit_temple_right_hand_entrance'),
    },
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
    'GerudoValley': NEIGHBORS['HyruleField']['GerudoValley'],
    'LakeHylia': NEIGHBORS['HyruleField']['LakeHylia'],
    'ZoraRiver': 'Vers la Rivière Zora',
}
LAKE_FIELD_RETURN_ANCHORS = {14388254154737389511, 12222278877302081165}
FIELD_VIEW_AGES = {view: age for age, view in REGION_VIEWS['HyruleField'].items()}
KOKIRI_VIEW_AGES = {view: age for age, view in AGE_VIEWS.items()}
KOKIRI_BRIDGE_GATE = (-90.0, -38.4)
MARKET_VIEW_AGES = {view: age for age, view in REGION_VIEWS['Market'].items()}
# The TimeTemple LocationArea uses different horizontal bounds at each age.
TEMPLE_BOUNDS = {
    'Child': ((60.45223236083984, -44.86612129211426), (156.45223236083984, -8.866121292114258)),
    'Adult': ((66.6098403930664, -52.0), (156.6098403930664, -16.0)),
}
TEMPLE_LANDMARKS = {
    'Obj_TimeTemple_SpiritStoneBase_A_01': 'Autel des pierres',
    'Obj_TimeTemple_Door_A_01': 'Porte du Temps',
    'Obj_TimeTemple_MasterSwordBase_A_01': 'Piédestal de l’épée',
}
FIELD_PORTAL_AREAS = {
    NEIGHBORS['HyruleField']['LakeHylia']: 'HyruleField',
    NEIGHBORS['HyruleField']['LonLonRanch']: 'HyruleField',
    NEIGHBORS['LakeHylia']['HyruleField']: 'LakeHylia',
    NEIGHBORS['LonLonRanch']['HyruleField']: 'LonLonRanch',
}
RANCH_PERIMETER = (
    (-102, 178), (-67, 185), (-65, 182), (-58, 183), (-57, 187),
    (-34, 192), (-43, 222), (-22, 244), (-18, 262), (-26, 290),
    (-44, 300), (-70, 304), (-121, 291), (-136, 280), (-162, 279),
    (-163, 259), (-141, 257), (-131, 219), (-118, 209), (-108, 208),
)
ZORA_RIVER_EXITS = {
    'ZoraRiver_LostWoodSide': NEIGHBORS['ZoraRiver']['LostWood'],
    'ZoraRiver_Entrance': NEIGHBORS['ZoraRiver']['HyruleField'],
}
ENTRANCE_LABELS = {
    'KakarikoVillage': KAKARIKO_ENTRANCES,
    'Graveyard': NEIGHBORS['Graveyard'],
    'ShadowTemple': NEIGHBORS['ShadowTemple'],
    'HyruleField': HYRULE_ANCHORS,
    'GerudoValley': NEIGHBORS['GerudoValley'],
    'GerudoFortress': NEIGHBORS['GerudoFortress'],
    'DesertColossus': NEIGHBORS['DesertColossus'],
    'Market': NEIGHBORS['Market'],
    'HyruleCastle': NEIGHBORS['HyruleCastle'],
    'GanonCastle': NEIGHBORS['GanonCastle'],
    'ZoraRiver': {'ZoraDomain': NEIGHBORS['ZoraRiver']['ZoraDomain']},
    'ZoraDomain': NEIGHBORS['ZoraDomain'],
    'ZoraFountain': {'ZoraDomain': NEIGHBORS['ZoraFountain']['ZoraDomain']},
    'IceCavern': NEIGHBORS['IceCavern'],
    'InsideJabuJabuBelly': NEIGHBORS['InsideJabuJabuBelly'],
    'InsideTheDekuTree': NEIGHBORS['InsideTheDekuTree'],
    'ForestTemple': NEIGHBORS['ForestTemple'],
    'BottomOfTheWell': NEIGHBORS['BottomOfTheWell'],
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
GANON_TRIALS = {
    'Forest': 'Forêt', 'Water': 'Eau', 'Shadow': 'Ombre',
    'Fire': 'Feu', 'Light': 'Lumière', 'Spirit': 'Esprit',
}
GANON_TOWER_ANCHORS = {
    'Land_InsideGanonCastle_Room19_A_01': 'Pied de la tour',
    'Land_InsideGanonCastle_Room20_A_01': 'Salle du premier étage',
    'Land_InsideGanonCastle_Room22_A_01': 'Salle du deuxième étage',
    'Land_InsideGanonCastle_Room24_A_01': 'Salle du troisième étage',
    'Land_InsideGanonCastle_Room26_A_01': 'Salle de Ganondorf',
}
GANON_ESCAPE_ANCHORS = {
    'CrumblingGanonCastle_StartPos': 'Début de la fuite',
    'BackEntrance': 'Sortie du château',
    **{f'RestartPos{i}': f'Passage {i}' for i in range(1, 8)},
}
TRAINING_ROOM_ANCHORS = {
    3761826239942057234: 'Hall d’entrée',
    327131091130935122: 'Salle des Stalfos',
    9317343157379008028: 'Galerie ouest',
    11763036527684746970: 'Salle des Loups',
    7291217069696259205: 'Salle des Like Like',
    9501065223924577612: 'Salle de la statue',
    1504970528840633775: 'Salle du marteau',
    12371614488659450539: 'Galerie est',
    13258869565676702196: 'Salle du Beamos',
    12866839950667688328: 'Bassin',
    13588342684847587321: 'Labyrinthe',
}
TRAINING_WALKWAY_ANCHORS = {
    11618577540114259236: 'Passerelle nord',
}
# Door actors between the corresponding native room centers. The elevated
# door from the statue room to the maze walkway is outside this ground plan.
TRAINING_DOORS = {
    17271596773795074407: (3761826239942057234, 327131091130935122),
    4403590790470660495: (327131091130935122, 9317343157379008028),
    10001376845054106600: (9317343157379008028, 11763036527684746970),
    2287906140519484787: (11763036527684746970, 7291217069696259205),
    6126832166241244381: (11763036527684746970, 9501065223924577612),
    2835828381713371595: (9501065223924577612, 1504970528840633775),
    13905333383293071313: (1504970528840633775, 12371614488659450539),
    14579251759478588816: (12371614488659450539, 12866839950667688328),
    9340986794564645500: (12371614488659450539, 13258869565676702196),
    1845019500144608623: (13258869565676702196, 3761826239942057234),
    5885932930990178582: (12371614488659450539, 13588342684847587321),
    2788856171788874734: (13588342684847587321, 3761826239942057234),
}


def training_connections(sources):
    anchors = {}
    for source in sources.values():
        for actor in source['root'].get('Actors', ()):
            ident = actor.get('Hash')
            kind = actor.get('Gyaml')
            if ((kind == 'DungeonRoomCenterAnchor' and ident in TRAINING_ROOM_ANCHORS)
                    or (kind == 'Obj_Gerudo_SwitchShutter_A_04' and ident in TRAINING_DOORS)):
                if position := actor.get('Translate'):
                    anchors.setdefault(ident, set()).add((position[0], position[2]))
    unique = {ident: next(iter(points)) for ident, points in anchors.items() if len(points) == 1}
    return {('Liaisons entre les salles', (unique[start], unique[door], unique[end]))
            for door, (start, end) in TRAINING_DOORS.items() if {start, door, end} <= unique.keys()}


def ganon_dungeon_floor(position):
    x, y, z = position
    # The entry bridge and trial rooms use the base view, including raised areas.
    if abs(x) > 32 or not -59 <= z <= 28:
        return 0
    return sum(y >= boundary for boundary in (126, 133, 140, 147, 161))


def ganon_tower_points(sources):
    points = set()
    for source in sources.values():
        for actor in source['root'].get('Actors', ()):
            position = actor.get('Translate')
            gyaml = actor.get('Gyaml')
            if not position:
                continue
            label = GANON_TOWER_ANCHORS.get(gyaml)
            if gyaml == 'DungeonRoomCenterAnchor' and 133 <= position[1] < 161:
                x, _, z = position
                if abs(x) > 12 or abs(z + 25) > 12:
                    label = 'Passage de la tour'
            if label and (floor := ganon_dungeon_floor(position)):
                points.add((floor, label, (position[0], position[2])))
    return points


def training_level_points(sources):
    anchors = {('DungeonRoomIdAnchor', ident): label for ident, label in TRAINING_WALKWAY_ANCHORS.items()}
    anchors['Obj_Gerudo_SwitchShutter_A_04', TRAINING_WALKWAY_GATE] = TRAINING_TO_STATUE
    return {(1, anchors[key], (position[0], position[2]))
            for source in sources.values() for actor in source['root'].get('Actors', ())
            if (key := (actor.get('Gyaml'), actor.get('Hash'))) in anchors
            and (position := actor.get('Translate'))}


def spirit_level_points(sources):
    anchors = {
        ('MapIconEntranceAnchor', 452821593555612172): (2, 'right_hand_entrance'),
        ('MapIconEntranceAnchor', 17977111214894828225): (2, 'left_hand_entrance'),
        ('DungeonRoomCenterAnchor', 8163808957952677095): (4, 'Arène de Twinrova'),
    }
    return {(*anchors[key], (position[0], position[2]))
            for source in sources.values() for actor in source['root'].get('Actors', ())
            if (key := (actor.get('Gyaml'), actor.get('Hash'))) in anchors
            and (position := actor.get('Translate'))}


LEVEL_POINT_EXTRACTORS = {
    'InsideGanonCastle': ganon_tower_points,
    'GerudoTrainingGround': training_level_points,
    'SpiritTemple': spirit_level_points,
}

GUIDE_ROUTE = 'Trajet du guide'
WASTELAND_PORTALS = {
    13756540388226076963: 'GerudoFortress',
    10151104999260881916: 'DesertColossus',
    1770868348614838942: 'DesertColossus',
}


def lake_position(point):
    x, z = point
    # The main gate lies at Z=396. The canyon passage enters farther north.
    return (x <= -35 and z >= 396) or (x <= -230 and z >= 385)


def field_area(point):
    """Choose the local map without changing the native Hyrule Field frame."""
    if lake_position(point):
        return 'LakeHylia'
    x, z = point
    inside = False
    for (x1, z1), (x2, z2) in zip(RANCH_PERIMETER, (*RANCH_PERIMETER[1:], RANCH_PERIMETER[0])):
        if (z1 > z) != (z2 > z) and x < x1 + (x2-x1) * (z-z1) / (z2-z1):
            inside = not inside
    return 'LonLonRanch' if inside else 'HyruleField'


def temple_position(point, age):
    (west, north), (east, south) = TEMPLE_BOUNDS[age]
    x, z = point
    return west <= x <= east and north <= z <= south


def kokiri_bridge_position(point):
    x, z = point
    # The field-side ravine lies west of the village approach.
    return x <= KOKIRI_BRIDGE_GATE[0] and -83 <= z <= 0


def guide_routes(sources):
    """Project the native Guide rail, including its Bézier handles, onto X/Z."""
    routes = set()
    for source in sources.values():
        for rail in source['root'].get('Rails', ()):
            if rail.get('Name') != 'Guide' or rail.get('Gyaml') != 'Guide' or rail.get('IsClosed'):
                continue
            knots = rail.get('Points', ())
            if len(knots) < 2:
                continue
            points = []
            for left, right in zip(knots, knots[1:]):
                start = read_position(left['Translate'])
                end = read_position(right['Translate'])
                takeoff = read_position(left.get('Control1')) or start
                arrival = read_position(right.get('Control0')) or end
                for step in range(12):
                    t = step / 12
                    u = 1 - t
                    points.append(tuple(u**3 * start[axis] + 3*u*u*t * takeoff[axis]
                                        + 3*u*t*t * arrival[axis] + t**3 * end[axis] for axis in (0, 2)))
            points.append((end[0], end[2]))
            routes.add((GUIDE_ROUTE, tuple(points)))
    return routes


def projection_points(region, sources):
    points = set()
    for path, source in sources.items():
        for actor in source['root'].get('Actors', ()):
            position = actor.get('Translate')
            if not position:
                continue
            gyaml = actor.get('Gyaml')
            label = None
            if region == 'KokiriForest':
                if gyaml == 'Obj_Kokiri_Bed_A_01':
                    label = NEIGHBORS[region]['DreamWorld']
            elif region == 'LostWood':
                if gyaml == 'StartPos' and actor.get('Name') == 'LostWood_Entrance':
                    label = 'arrivee_de_kokiri'
            elif region == 'ZoraRiver' and gyaml == 'FieldAndDungeonEntranceEventRequestActor':
                label = ZORA_RIVER_EXITS.get(actor.get('Name'))
            elif region == 'ZoraFountain' and gyaml == 'FieldAndDungeonEntranceEventRequestActor':
                target = {'ZoraFountain_FromIceCavern': 'IceCavern',
                          'ZoraFountain_FromInsideJabuJabuBelly': 'InsideJabuJabuBelly'}.get(actor.get('Name'))
                label = NEIGHBORS[region].get(target)
            elif region == 'SacredForestMeadow':
                label = GROVE_ANCHORS.get(gyaml)
                if gyaml in {'Land_SacredForest_Prop_A_33', 'Land_SacredForest_Prop_A_41'}:
                    label = GROVE_STAIRS.get(actor.get('Hash'))
            elif region == 'InsideGanonCastle':
                dynamic = actor.get('Dynamic')
                if not isinstance(dynamic, dict):
                    dynamic = {}
                if gyaml == 'FieldAndDungeonEntranceEventRequestActor' and dynamic.get('NextBancParamNameAdult') == 'GanonCastle':
                    label = NEIGHBORS[region]['GanonCastle']
                elif gyaml == 'EventRequestActor':
                    prefix = 'InsideGanonCastle_Dungeon_BarrierRemove_'
                    event = dynamic.get('RequestEventName', '')
                    if isinstance(event, str) and event.startswith(prefix) and (trial := GANON_TRIALS.get(event.removeprefix(prefix))):
                        label = f'Épreuve · {trial}'
                elif gyaml == 'Obj_GanonCastle_Barrier_A_01':
                    label = 'Barrière de la tour'
            elif region == 'GanonCastle' and gyaml == 'StartPos':
                label = GANON_ESCAPE_ANCHORS.get(actor.get('Name'))
            elif region == 'GerudoFortress' and gyaml == 'MapIconFacilityAnchor':
                dynamic = actor.get('Dynamic')
                if isinstance(dynamic, dict) and dynamic.get('MapIconFacilityIsOpen') == 'GerudoTrainingGround_MapIcon_Flag':
                    label = NEIGHBORS[region]['GerudoTrainingGround']
            elif region == 'GerudoTrainingGround' and gyaml == 'DungeonRoomCenterAnchor':
                label = TRAINING_ROOM_ANCHORS.get(actor.get('Hash'))
            elif (region == 'GerudoTrainingGround' and gyaml == 'Obj_Gerudo_SwitchShutter_A_04'
                  and actor.get('Hash') == TRAINING_WALKWAY_GATE):
                label = TRAINING_TO_WALKWAY
            elif region == 'GerudoTrainingGround' and gyaml == 'FieldAndDungeonEntranceEventRequestActor':
                dynamic = actor.get('Dynamic')
                if isinstance(dynamic, dict) and dynamic.get('NextStartPosName') == 'GerudoFortress_FromGerudoTrainingGround':
                    label = NEIGHBORS[region]['GerudoFortress']
            elif region == 'HountedWasteland':
                if gyaml == 'MapIconEntranceAnchor':
                    label = NEIGHBORS[region].get(WASTELAND_PORTALS.get(actor.get('Hash')))
                elif gyaml == 'Land_Desert_Ruin_A_01':
                    label = 'Ruines du guide'
                elif gyaml == 'DestinationAnchor':
                    label = {'GuideStartPos': 'Départ du guide',
                             'GuidePoeComplete': 'Fin du trajet'}.get(actor.get('Name'))
            elif region == 'SpiritTemple' and gyaml == 'MapIconEntranceAnchor' and actor.get('Hash') == 4365488265954739873:
                label = NEIGHBORS[region]['DesertColossus']
            elif region == 'WaterTemple' and gyaml == 'MapIconEntranceAnchor' and actor.get('Hash') == 18222828140606986520:
                label = NEIGHBORS[region]['LakeHylia']
            elif region == 'HyruleField' and gyaml == 'Land_LonLon_Gate_B_01':
                point = position[0], position[2]
                points.add((NEIGHBORS[region]['LonLonRanch'], point))
                label = NEIGHBORS['LonLonRanch'][region]
            elif (region == 'Market' and gyaml == 'LocationArea'
                  and isinstance(actor.get('Dynamic'), dict)
                  and actor['Dynamic'].get('Location') == 'TimeTemple'):
                age = MARKET_VIEW_AGES.get(view_name(path))
                if age is not None:
                    # The entrance shares the axis of the Door of Time at Z=-34.
                    point = TEMPLE_BOUNDS[age][0][0], -34.0
                    points.add((NEIGHBORS[region]['TempleOfTime'], point))
                    points.add((NEIGHBORS['TempleOfTime'][region], point))
            elif region == 'Market' and gyaml in TEMPLE_LANDMARKS:
                label = TEMPLE_LANDMARKS[gyaml]
            elif region == 'SageRoom':
                if gyaml == 'EftLoc_SageRoom_LightPillar_00':
                    label = 'Pilier de lumière'
                elif gyaml == 'StartPos' and not actor.get('Name'):
                    label = NEIGHBORS[region]['TempleOfTime']
            elif region == 'DreamWorld':
                if gyaml == 'StartPos' and actor.get('Name') == 'BossRush':
                    label = 'Arrivée du défi'
                elif gyaml == 'Land_Dream_BossPedestal_A_Interval_02':
                    label = 'Piédestal du boss'
                elif gyaml == 'Npc_Dream':
                    label = 'Organisateur du défi'
                    # The same character starts the challenge and offers to wake Link.
                    points.add((NEIGHBORS[region]['KokiriForest'], (position[0], position[2])))
                elif gyaml in {'Land_Dream_EnemyMuseum_B_01', 'Land_Dream_EnemyMuseum_B_02',
                               'Land_Dream_EnemyMuseum_B_03', 'Land_Dream_EnemyMuseum_B_04'}:
                    label = 'Galerie'
            elif gyaml == 'MapIconEntranceAnchor':
                dynamic = actor.get('Dynamic')
                if isinstance(dynamic, dict):
                    target = dynamic.get('Location')
                    if region == 'HyruleField' and actor.get('Hash') in LAKE_FIELD_RETURN_ANCHORS:
                        label = NEIGHBORS['LakeHylia']['HyruleField']
                    elif (region == 'HyruleField' and target in {'GerudoValley', 'ZoraDomain', 'WaterTemple'}
                          and lake_position((position[0], position[2]))):
                        label = NEIGHBORS['LakeHylia'][target]
                    entrances = ENTRANCE_LABELS.get(region, {})
                    if label is None and (region in {'GoronCity', 'DeathMountainCrater'}
                                          or dynamic.get('IsVisible') is not False
                                          or (target == 'LakeHylia' and region in {'GerudoValley', 'ZoraDomain'})):
                        label = entrances.get(target)
                        if region == 'DesertColossus' and target == 'SpiritTemple' and position[1] > 100:
                            label = None  # The two upper entrances lead to the side galleries.
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
    has_dream_museum = any(path in maps for path in (
        f'Banc/DreamWorld/EnemyMuseum_{layer}{MAP_SUFFIX}' for layer in ('Static', 'Dynamic')
    ))
    for path in sorted(maps):
        region = resource_region(path)
        if region is None or not path.endswith(MAP_SUFFIX):
            continue
        frame = view_name(path)
        if region != 'KokiriForest' and frame not in VIEWS:
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
                  for name, position in marks.get('points', ())
                  if region != 'SpiritTemple' or name not in SIDE_PORTALS['SpiritTemple']}
        if region != 'KokiriForest' or has_dream_museum:
            points.update(projection_points(region, sources))
        if frame == DREAM_SCENE_VIEWS['BossRushIntervalRoom']:
            room_areas = [actor for source in sources.values() for actor in source['root'].get('Actors', ())
                          if actor.get('Gyaml') == 'DungeonRoomArea'
                          and actor.get('Translate') and actor.get('Scale')]
            if len(room_areas) == 1:
                x, _, z = room_areas[0]['Translate']
                dx, _, dz = room_areas[0]['Scale']
                rooms.append(('Salle intermédiaire', (x - dx, z - dz), (x + dx, z + dz)))
        extract_levels = LEVEL_POINT_EXTRACTORS.get(region)
        levels = extract_levels(sources) if extract_levels else ()
        route_extractor = {'HountedWasteland': guide_routes, 'GerudoTrainingGround': training_connections}.get(region)
        routes = route_extractor(sources) if route_extractor else ()
        if rooms or points or levels or routes:
            scene = {'rooms': rooms, 'points': sorted(points)}
            if levels:
                scene['level_points'] = sorted(levels)
            if routes:
                scene['routes'] = sorted(routes)
            scenes[path] = scene
    return scenes


def read_scenes(document):
    """Validate optional scene data while accepting older saved maps."""
    scenes = document.get('scenes', {})
    if not isinstance(scenes, dict):
        raise ValueError('Fond de carte invalide')
    for resource, scene in scenes.items():
        level_points = []
        for entry in scene.get('level_points', ()):
            region = resource_region(resource)
            if (len(entry) != 3 or region not in LEVEL_POINT_EXTRACTORS
                    or type(entry[0]) is not int or not 0 < entry[0] < len(DUNGEON_FLOORS[region])):
                raise ValueError('Niveau de carte invalide')
            level_points.append(entry[1:])
        for entries, size in ((scene['rooms'], 3), (scene['points'], 2), (level_points, 2)):
            for entry in entries:
                if (len(entry) != size or not isinstance(entry[0], str)
                        or any(len(point) != 2 or any(type(v) not in (int, float)
                               or not isfinite(v) for v in point) for point in entry[1:])):
                    raise ValueError('Repère de carte invalide')
        for route in scene.get('routes', ()):
            if (len(route) != 2 or not isinstance(route[0], str) or not 2 <= len(route[1]) <= 4096
                    or any(len(point) != 2 or any(type(v) not in (int, float) or not isfinite(v)
                                                  for v in point) for point in route[1])):
                raise ValueError('Trajet de carte invalide')
    return scenes


def view_name(resource):
    """Group scene layers within a region and age."""
    region = resource_region(resource)
    if region == 'DreamWorld':
        for scene, view in DREAM_SCENE_VIEWS.items():
            if resource in (f'Banc/{region}/{scene}_{layer}{MAP_SUFFIX}' for layer in ('Static', 'Dynamic')):
                return view
    if region == 'HyruleCastle' and resource in (
            f'Banc/{region}/{region}_{layer}{MAP_SUFFIX}' for layer in ('Static', 'Dynamic')):
        return CASTLE_OUTSKIRTS
    if region == 'GanonCastle':
        for scene, view in (('GanonCastle', GANON_OUTSKIRTS), ('CrumblingGanonCastle', GANON_ESCAPE)):
            if resource in (f'Banc/{region}/{scene}_{layer}{MAP_SUFFIX}' for layer in ('Static', 'Dynamic')):
                return view
    if region in SHARED_DUNGEONS and resource in (
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
    if row.dungeon_floor is not None and view in VIEWS:
        floor = row.dungeon_floor
        key = f'{floor + 1}F' if floor >= 0 else f'S{-floor}'
        native_view = NATIVE_FLOOR_VIEWS.get((VIEWS[view][0], key))
        if native_view:
            return native_view
    if view in KOKIRI_VIEW_AGES and row.position is not None and kokiri_bridge_position(row.project()):
        return REGION_VIEWS['KokiriBridge'][KOKIRI_VIEW_AGES[view]]
    if view in FIELD_VIEW_AGES and row.position is not None:
        return REGION_VIEWS[field_area(row.project())][FIELD_VIEW_AGES[view]]
    if (view in MARKET_VIEW_AGES and row.position is not None
            and temple_position(row.project(), MARKET_VIEW_AGES[view])):
        return REGION_VIEWS['TempleOfTime'][MARKET_VIEW_AGES[view]]
    if view == CASTLE_OUTSKIRTS and row.position is not None:
        return castle_view(row.position[2])
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
    if view == JABU_VIEWS[0] and row.position is not None:
        if row.dungeon_room in JABU_ROOM_VIEWS:
            return JABU_ROOM_VIEWS[row.dungeon_room]
        x, y, z = row.position
        # Native arena bounds for live positions without a room index.
        if row.id == 'boss#Barinade' or row.category == 'full_bossheart' or (
                row.dungeon_room is None and 20 <= x <= 64 and -136 <= z <= -98 and 98 <= y <= 113):
            return JABU_VIEWS[3]
        if y < 85:
            return JABU_VIEWS[1]
        if y >= 94:
            return JABU_VIEWS[2]
    if view == DEKU_VIEWS[0] and row.position is not None:
        if row.dungeon_room in DEKU_ROOM_VIEWS:
            return DEKU_ROOM_VIEWS[row.dungeon_room]
        x, y, z = row.position
        if row.id == 'boss#Queen Gohma' or row.category == 'full_bossheart' or (
                row.dungeon_room is None and 1 <= x <= 27 and 47 <= z <= 89 and 45 <= y <= 62):
            return DEKU_VIEWS[5]
        if y < 70:
            return DEKU_VIEWS[4]
        if y < 90:
            return DEKU_VIEWS[3]
        if y >= 115:
            return DEKU_VIEWS[2]
        if y >= 104:
            return DEKU_VIEWS[1]
    if view == FOREST_VIEWS[0] and row.position is not None:
        if row.dungeon_room in FOREST_ROOM_VIEWS:
            return FOREST_ROOM_VIEWS[row.dungeon_room]
        x, y, z = row.position
        if row.id == 'boss#Phantom Ganon' or row.category == 'full_bossheart' or (
                row.dungeon_room is None and -15 <= x <= 15 and -79 <= z <= -48 and 72 <= y <= 83):
            return FOREST_VIEWS[5]
        if y < 66:
            return FOREST_VIEWS[4]
        if y < 90:
            return FOREST_VIEWS[3]
        if y >= 120:
            return FOREST_VIEWS[2]
        if y >= 109:
            return FOREST_VIEWS[1]
    if view == WELL_VIEWS[0] and row.position is not None:
        if row.dungeon_room in {8, 9} or (row.dungeon_room is None and row.position[1] < 94):
            return WELL_VIEWS[1]
    if view == SHADOW_VIEWS[0] and row.position is not None:
        if row.dungeon_room in SHADOW_ROOM_VIEWS:
            return SHADOW_ROOM_VIEWS[row.dungeon_room]
        x, y, z = row.position
        if row.id == 'boss#Bongo Bongo' or row.category == 'full_bossheart' or (
                row.dungeon_room is None and -173 <= x <= -104 and 0 <= z <= 75 and y < 5):
            return SHADOW_VIEWS[4]
        if y < 45 or (45 <= y <= 53 and (x < 0 or (x >= 100 and z < -33))):
            return SHADOW_VIEWS[3]
        if y < 70:
            return SHADOW_VIEWS[2]
        if y < 87 or (y < 89 and x > 55):
            return SHADOW_VIEWS[1]
    if view == GANON_DUNGEON_VIEWS[0] and row.position is not None:
        floor = 4 if row.dungeon_room == 24 else ganon_dungeon_floor(row.position)
        return GANON_DUNGEON_VIEWS[floor]
    if view == SPIRIT_VIEWS[0] and row.position is not None:
        x, y, z = row.position
        if row.id == 'boss#Twinrova' or row.category == 'full_bossheart' or (abs(x) <= 36 and z < -125):
            return SPIRIT_VIEWS[4]
        if row.dungeon_room == 7 and y >= 127:
            return SPIRIT_VIEWS[2]
        floor = SPIRIT_ROOM_FLOORS.get(row.dungeon_room, sum(y >= cutoff for cutoff in (111, 127, 149)))
        return SPIRIT_VIEWS[floor]
    if view == WATER_VIEWS[0] and row.position is not None:
        x, y, z = row.position
        # The entrance and Morpha's pool belong to different plans despite their elevations.
        if row.id == 'boss#Morpha' or row.category == 'full_bossheart':
            return WATER_VIEWS[2]
        if row.dungeon_room in WATER_ROOM_FLOORS:
            return WATER_VIEWS[WATER_ROOM_FLOORS[row.dungeon_room]]
        # The high walkway into Morpha's room and its basin share the same plan.
        if y >= 119 and -18 <= x <= 9 and -107 <= z <= -69:
            return WATER_VIEWS[2]
        # The eastern chest has native FloorNumber 1 even though its raised
        # platform is above the usual height boundary for that floor.
        if 116 <= y <= 120 and 31 <= x <= 60 and -30 <= z <= -17:
            return WATER_VIEWS[1]
        floor = sum(y < cutoff for cutoff in (116, 106.5, 97.5))
        return WATER_VIEWS[floor]
    if view == TRAINING_VIEWS[0] and row.position is not None:
        x, y, z = row.position
        if y >= 103 and (row.dungeon_room == 8 or (
                row.dungeon_room is None and -25 <= x <= 24 and -67 <= z <= -33)):
            return TRAINING_VIEWS[1]
    if view == DODONGO_VIEWS[0] and row.position is not None:
        y = row.position[1]
        if y < 82:
            return DODONGO_VIEWS[2]
        if y >= 105:
            return DODONGO_VIEWS[1]
    return view


def castle_view(z):
    """The courtyard is loaded in the castle scene beyond the outdoor map."""
    return CASTLE_COURT if z < -170 else CASTLE_OUTSKIRTS


def group_scenes(scenes):
    grouped = {}
    for resource, scene in scenes.items():
        name = view_name(resource)
        view = grouped.setdefault(name, {'rooms': set(), 'points': set()})
        view['rooms'].update((name, tuple(low), tuple(high)) for name, low, high in scene['rooms'])
        for label, point in scene['points']:
            target = view
            if (name in KOKIRI_VIEW_AGES and label == NEIGHBORS['KokiriBridge']['HyruleField']
                    and kokiri_bridge_position(point)):
                bridge = REGION_VIEWS['KokiriBridge'][KOKIRI_VIEW_AGES[name]]
                target = grouped.setdefault(bridge, {'rooms': set(), 'points': set()})
                view['points'].add((NEIGHBORS['KokiriForest']['KokiriBridge'], KOKIRI_BRIDGE_GATE))
                target['points'].add((NEIGHBORS['KokiriBridge']['KokiriForest'], KOKIRI_BRIDGE_GATE))
            elif name in FIELD_VIEW_AGES:
                area = FIELD_PORTAL_AREAS.get(label) or field_area(point)
                local_view = REGION_VIEWS[area][FIELD_VIEW_AGES[name]]
                target = grouped.setdefault(local_view, {'rooms': set(), 'points': set()})
            elif (name in MARKET_VIEW_AGES and temple_position(point, MARKET_VIEW_AGES[name])
                  and label != NEIGHBORS['Market']['TempleOfTime']):
                age = MARKET_VIEW_AGES[name]
                temple = REGION_VIEWS['TempleOfTime'][age]
                target = grouped.setdefault(temple, {'rooms': set(), 'points': set()})
                if label == NEIGHBORS['TempleOfTime']['Market']:
                    target['rooms'].add((REGION_NAMES['TempleOfTime'], *TEMPLE_BOUNDS[age]))
            target['points'].add((label, tuple(point)))
        if scene.get('routes'):
            view.setdefault('routes', set()).update((name, tuple(map(tuple, points))) for name, points in scene['routes'])
        for floor, name, point in scene.get('level_points', ()):
            _, view_name_for_floor = DUNGEON_FLOORS[resource_region(resource)][floor]
            level = grouped.setdefault(view_name_for_floor, {'rooms': set(), 'points': set()})
            level['points'].add((name, tuple(point)))
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
        if name == NEIGHBORS['KokiriBridge']['HyruleField'] and all(
                label in scenes for label in REGION_VIEWS['KokiriBridge'].values()):
            child_pos, adult_pos = (entrance(scenes[REGION_VIEWS['KokiriBridge'][age]], name)
                                    for age in ('Child', 'Adult'))
        else:
            child_pos, adult_pos = entrance(scene, name), entrance(adult, name)
        if child_pos is None or adult_pos is None or dist(child_pos, adult_pos) > 0.5:
            return scene
    # OotrR numbers some unnamed rooms independently by age. Child numbering
    # can shift even when the same physical houses are in the same frame.
    return adult
