"""Map symbols derived from OotrR landmarks in the active resource's coordinates."""
from math import atan2, isfinite

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
DODONGO_LEVEL_CROSSINGS = (
    ((0, 'Escalier ouest · vers l’étage', 'Obj_DodongoCave_BrokenStair_A_01', 900149935771582689),
     (1, 'Escalier ouest · vers le rez-de-chaussée', 'Land_DodongoCave_Ladder_A_04', 1553792366831309427)),
    ((0, 'Porte vers le Roi Dodongo', 'Obj_DodongoCave_SwitchShutter_A_01', 16871561526373450485),
     (2, 'Voir l’accès à l’arène de Dodongo', 'StartPos', 7367191043734907309)),
)
FIRE_LEVELS = ('Rez-de-chaussée', '1er étage', '2e étage', '3e étage', '4e étage', 'Arène du boss')
FIRE_VIEWS = tuple(f'{REGION_NAMES["FireTemple"]} · {level}' for level in FIRE_LEVELS)
FIRE_BOSS_CROSSING = (
    (0, 'Porte vers Volvagia', 'Obj_FireTemple_SwitchShutter_A_02', 7971893604208202501),
    (5, 'Voir l’accès à Volvagia', 'StartPos', 4368300544097029137),
)
FIRE_LEVEL_CROSSINGS = (
    FIRE_BOSS_CROSSING,
    ((0, 'Ascenseur est · vers le 1er étage', 'Obj_Gimmick_AnswerPosAnchor', 16087633202058987797),
     (1, 'Ascenseur est · vers le rez-de-chaussée', 'DungeonRoomArea', 6331941358227428102)),
    ((1, 'Passage vers le labyrinthe', 'DungeonRoomArea', 17572016124561474933),
     (2, 'Passage vers le 1er étage', 'DungeonRoomArea', 10946843903591013285)),
    ((2, 'Passage vers le 3e étage', 'DungeonRoomArea', 3166794335041927387),
     (3, 'Passage vers le 2e étage', 'DungeonRoomArea', 1428609598790894168)),
    ((3, 'Montée vers le 4e étage', 'DungeonRoomArea', 6017864338550927060),
     (4, 'Descente vers le 3e étage', 'DungeonRoomArea', 4525650555869086110)),
    ((2, 'Pilier du marteau · vers le rez-de-chaussée', 'Obj_FireTemple_HammerDropPillar_A_01', 8177655486739024991),
     (0, 'Pilier du marteau · voir le 2e étage', 'Obj_FireTemple_HammerDropPillar_A_01', 6957196851887297580)),
)
JABU_LEVELS = ('Rez-de-chaussée', 'Sous-sol', 'Étage', 'Arène de Barinade')
JABU_VIEWS = tuple(f'{REGION_NAMES["InsideJabuJabuBelly"]} · {level}' for level in JABU_LEVELS)
JABU_LEVEL_CROSSINGS = (
    ((0, 'Salle des fosses · vers le sous-sol', 'DungeonRoomCenterAnchor', 15514577878712490971),
     (1, 'Sous les fosses · voir le rez-de-chaussée', 'DungeonRoomCenterAnchor', 4161188942676563767)),
    ((1, 'Ascenseur d’Octo · vers l’étage', 'Obj_InsideJabu_Jabu_ElevatorLift_A_02', 5914032013565537495),
     (2, 'Ascenseur d’Octo · voir le sous-sol', 'Obj_InsideJabu_Jabu_ElevatorLift_A_01', 5186749243682591245)),
    ((2, 'Porte vers Barinade', 'Obj_InsideJabu_Jabu_SwitchShutter_A_01', 8015922362823848795),
     (3, 'Voir l’accès à l’arène de Barinade', 'StartPos', 7558908200776400959)),
)
DEKU_LEVELS = ('Rez-de-chaussée', '1er étage', '2e étage', 'Sous-sol', 'Sous-sol profond', 'Arène de Gohma')
DEKU_VIEWS = tuple(f'{REGION_NAMES["InsideTheDekuTree"]} · {level}' for level in DEKU_LEVELS)
DEKU_LEVEL_CROSSINGS = (
    ((0, 'Lierre du hall · vers le 1er étage', 'Land_IvyClimbable_A_03', 18344093377455157970),
     (1, 'Lierre du hall · vers le rez-de-chaussée', 'Land_IvyClimbable_A_02', 7917179443911583089)),
    ((1, 'Mur de lierre · vers le 2e étage', 'Land_IvyClimbable_A_10', 10820675793917272290),
     (2, 'Mur de lierre · vers le 1er étage', 'Land_IvyClimbable_A_10', 10820675793917272290)),
    ((0, 'Toile du hall · vers le sous-sol', 'Obj_InsideTheDekuTree_SpiderWeb_A_01', 278772661473487189),
     (3, 'Sous la toile · voir le hall', 'Obj_InsideTheDekuTree_SpiderWeb_A_01', 278772661473487189)),
    ((3, 'Seconde toile · vers le sous-sol profond', 'Obj_InsideTheDekuTree_SpiderWeb_A_01', 9217804728253310381),
     (4, 'Seconde toile · voir le sous-sol', 'Obj_InsideTheDekuTree_SpiderWeb_A_01', 9217804728253310381)),
    ((4, 'Accès à Gohma', 'DestinationAnchor', 3293306439425436286),
     (5, 'Voir l’accès à l’arène de Gohma', 'DestinationAnchor', 5506988010884496464)),
)
FOREST_LEVELS = ('Rez-de-chaussée', '1er étage', '2e étage', 'Sous-sol', 'Sous-sol profond', 'Arène du boss')
FOREST_VIEWS = tuple(f'{REGION_NAMES["ForestTemple"]} · {level}' for level in FOREST_LEVELS)
FOREST_LEVEL_CROSSINGS = (
    ((0, 'Ascenseur du hall', 'Obj_ForestTemple_Elevator_A_01', 9015988562326766070),
     (4, 'Ascenseur vers le hall', 'Obj_ForestTemple_Elevator_A_01', 9015988562326766070)),
    ((0, 'Puits de la cour est', 'Land_ForestTemple_Well_A_01', 11088284189308826273),
     (3, 'Échelle vers la cour est', 'Obj_ForestTemple_Ladder_A_01', 6306446343189810327)),
    ((0, 'Ascenseur ouest', 'Obj_ForestTemple_Elevator_A_01', 13316454886115529094),
     (2, 'Ascenseur vers le rez-de-chaussée', 'Obj_ForestTemple_Elevator_A_01', 13316454886115529094)),
    ((4, 'Porte vers Ganon spectral', 'Obj_ForestTemple_SwitchShutter_A_04', 11429592239509371885),
     (5, 'Voir l’accès à l’arène', 'StartPos', 7330387629530333392)),
)
WELL_LEVELS = ('Sous-sol', 'Sous-sol profond')
WELL_VIEWS = tuple(f'{REGION_NAMES["BottomOfTheWell"]} · {level}' for level in WELL_LEVELS)
WELL_LEVEL_CROSSINGS = (
    ((0, 'Échelle ouest · vers le sous-sol profond', 'Land_Well_Ladder_A_05', 12953344658999400023),
     (1, 'Échelle ouest · vers le sous-sol', 'Land_Well_Ladder_A_05', 12953344658999400023)),
    ((0, 'Sol illusoire · vers la salle du Poigneur', 'Obj_Well_GlassTruth_A_30', 4334615211939361328),
     (1, 'Voir le sol illusoire au-dessus', 'StartPos', 2376828317386419701)),
)
SHADOW_LEVELS = ('Sous-sol 1', 'Sous-sol 2', 'Sous-sol 3', 'Sous-sol 4', 'Arène de Bongo Bongo')
SHADOW_VIEWS = tuple(f'{REGION_NAMES["ShadowTemple"]} · {level}' for level in SHADOW_LEVELS)
SHADOW_SHIP_ROUTE = 'Trajet du bateau'
SHADOW_BOSS_DOOR = 'Porte vers Bongo Bongo'
SHADOW_BOSS_LANDING = 'Arrivée dans l’arène'
SHADOW_LEVEL_CROSSINGS = (
    ((0, 'Escalier vers le sous-sol 2', 13641591313020446364),
     (1, 'Escalier vers le sous-sol 1', 6139920143353312087)),
    ((1, 'Passage vers le sous-sol 3', 9500101214674922945),
     (2, 'Passage vers le sous-sol 2', 13181701853631283711)),
    ((2, 'Passage vers le bateau', 17002384234813722769),
     (3, 'Passage vers le couloir des vents', 8392133095956232092)),
)
SPIRIT_LEVELS = ('Rez-de-chaussée', '1er étage', '2e étage', '3e étage', 'Arène de Twinrova', 'Couloir de Twinrova')
SPIRIT_VIEWS = tuple(f'{REGION_NAMES["SpiritTemple"]} · {level}' for level in SPIRIT_LEVELS)
# Each link pairs two map views with native actors at the crossing.
SPIRIT_INTERIOR_LINKS = (
    ((0, 'Montée ouest', 'Land_SpiritTemple_ClimbWall_A_01', 11669494390516371978),
     (1, 'Descente ouest', 'Land_SpiritTemple_ClimbWall_A_01', 11669494390516371978)),
    ((0, 'Montée est', 'Land_SpiritTemple_ClimbWall_A_05', 7986637982941605251),
     (1, 'Descente est', 'Land_SpiritTemple_ClimbWall_A_05', 7986637982941605251)),
    ((1, 'Mur vers le balcon', 'Land_SpiritTemple_ClimbWall_A_02', 14644254544870263426),
     (2, 'Mur vers la salle de la statue', 'Land_SpiritTemple_ClimbWall_A_02', 14644254544870263426)),
    ((2, 'Montée par les murs mobiles', 'Land_SpiritTemple_ClimbWall_A_06', 10843425050371611115),
     (3, 'Porte des murs mobiles', 'Obj_SpiritTemple_SwitchShutter_A_01', 11229157323951127269)),
    ((2, 'Porte derrière le visage de la statue', 'Obj_SpiritTemple_SwitchShutter_A_03', 16853997340662105473),
     (5, 'Porte vers la salle de la statue', 'Obj_SwitchShutter_A_06', 11880473245622015774)),
    ((5, 'Porte vers Twinrova', 'Obj_SpiritTemple_SwitchShutter_A_04', 8544696912463075599),
     (4, 'Porte vers le couloir', 'Obj_SwitchShutter_A_06', 17726959485897113740)),
)
WATER_LEVELS = ('2e étage', '1er étage', 'Rez-de-chaussée', 'Sous-sol')
WATER_VIEWS = tuple(f'{REGION_NAMES["WaterTemple"]} · {level}' for level in WATER_LEVELS)
WATER_CONTROLS = {
    'Obj_WaterTemple_StoneTablet_A_01': (0, 'Tablette · niveau bas'),
    'Obj_WaterTemple_StoneTablet_A_03': (1, 'Tablette · niveau intermédiaire'),
    'Obj_WaterTemple_StoneTablet_A_02': (0, 'Tablette · niveau haut'),
}
WATER_CONTROL_LABELS = frozenset(label for _, label in WATER_CONTROLS.values())
WATER_LEVEL_CROSSINGS = (
    ((0, 'Plateformes · vers le 1er étage', 'Obj_WaterTemple_FloatFloor_A_02', 9370949986696443983),
     (1, 'Plateformes · vers le 2e étage', 'Obj_WaterTemple_FloatFloor_A_02', 3421458343789916518)),
    ((1, 'Pilier central · vers le rez-de-chaussée', 'Obj_WaterTemple_SwitchShutter_A_01', 1311186950182408800),
     (2, 'Pilier central · vers le 1er étage', 'Obj_WaterTemple_SwitchShutter_A_01', 15319553007255647544)),
    ((2, 'Pilier central · vers le sous-sol', 'DungeonRoomArea', 8677578349467245137),
     (3, 'Sous le pilier · vers le rez-de-chaussée', 'DungeonRoomArea', 3854827355659673893)),
)
GANON_DUNGEON_LEVELS = ('Épreuves', 'Accès à la tour', 'Tour · 1er étage',
                        'Tour · 2e étage', 'Tour · 3e étage', 'Sommet')
GANON_DUNGEON_VIEWS = tuple(f'{REGION_NAMES["InsideGanonCastle"]} · {level}' for level in GANON_DUNGEON_LEVELS)
GANON_TRIALS = {
    'Forest': (2419854912261814384, 'Forêt'),
    'Water': (7124800717538768497, 'Eau'),
    'Shadow': (8495610940054253979, 'Ombre'),
    'Fire': (399054663657392680, 'Feu'),
    'Light': (936558425084482814, 'Lumière'),
    'Spirit': (609021425778003787, 'Esprit'),
}
GANON_TRIAL_DOORS = {ident: f'Entrée · {trial}' for ident, trial in GANON_TRIALS.values()}
GANON_TRIAL_LEVELS = tuple(f'Épreuve · {trial}' for _, trial in GANON_TRIALS.values())
GANON_TRIAL_VIEWS = tuple(f'{REGION_NAMES["InsideGanonCastle"]} · {level}' for level in GANON_TRIAL_LEVELS)
# Door centres in X/Z and outward unit normals from their native rotations.
GANON_TRIAL_DOOR_PLANES = (
    (16.120, 7.842, 0.499, 0.867),
    (33.032, -21.001, 1.0, 0.0),
    (16.111, -49.841, 0.496, -0.869),
    (-16.136, -49.862, -0.513, -0.858),
    (-33.050, -21.004, -1.0, 0.0),
    (-16.099, 7.805, -0.501, 0.866),
)
GANON_TRIAL_VIEW_POINTS = {
    label: (view, detail)
    for (_, trial), view in zip(GANON_TRIALS.values(), GANON_TRIAL_VIEWS)
    for label, detail in ((f'Entrée · {trial}', f'Retour · {trial}'),
                          (f'Épreuve · {trial}', f'Épreuve · {trial}'))
}
GANON_TRIAL_ROOM_VIEWS = {
    room: view for view, rooms in zip(GANON_TRIAL_VIEWS, (range(2, 5), range(5, 8), (8, 9), (10, 11),
                                                        range(12, 16), range(16, 19)))
    for room in rooms
}
GANON_TOWER_CROSSINGS = (
    ((0, 'Barrière de la tour', 'Obj_GanonCastle_Barrier_A_01', 7855099293663223240),
     (1, 'Retour vers les épreuves', 'DungeonRoomArea', 4106367990015143384)),
    ((1, 'Passage ouest · vers le 1er étage', 'DungeonRoomArea', 11647715588683698854),
     (2, 'Passage ouest · vers l’accès à la tour', 'DungeonRoomArea', 10067400039182610770)),
    ((2, 'Passage est · vers le 2e étage', 'DungeonRoomArea', 11929116091605019809),
     (3, 'Porte nord · vers le 1er étage', 'Obj_SwitchShutter_A_02', 11571952824815752314)),
    ((3, 'Passage sud · vers le 3e étage', 'DungeonRoomArea', 4240549581105894524),
     (4, 'Porte est · vers le 2e étage', 'Obj_SwitchShutter_A_02', 8600111735198502624)),
    ((4, 'Escalier vers Ganondorf', 'DungeonRoomArea', 8255735152900358871),
     (5, 'Voir l’accès à la salle de Ganondorf', 'StartPos', 11474052871889909221)),
)
TRAINING_LEVELS = ('Salles et labyrinthe', 'Passerelle du labyrinthe')
TRAINING_VIEWS = tuple(f'{REGION_NAMES["GerudoTrainingGround"]} · {level}' for level in TRAINING_LEVELS)
TRAINING_WALKWAY_GATE = 18314542979296415492
TRAINING_CEILING_CLIMB = 18344474415563430437
TRAINING_TO_WALKWAY = 'Vers la passerelle'
TRAINING_TO_STATUE = 'Vers la salle de la statue'
TRAINING_TO_CEILING = 'Vers l’alcôve du plafond'
TRAINING_TO_MAZE = 'Vers le labyrinthe inférieur'
TRAINING_SCARECROW = 'Épouvantail'
UNPOSITIONED_CHECK_AREAS = {
    'ap#Gerudo Training Ground Near Scarecrow Chest': (TRAINING_VIEWS[1], 'Salle de la statue · niveau supérieur'),
    'ap#Gerudo Training Ground Freestanding Key': (TRAINING_VIEWS[0], 'Labyrinthe central · côté droit'),
    'ap#Gift from Sages': (None, 'Temple du Temps · récompense de scénario'),
}
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
    'InsideGanonCastle': tuple(zip((*GANON_DUNGEON_LEVELS, *GANON_TRIAL_LEVELS),
                                  (*GANON_DUNGEON_VIEWS, *GANON_TRIAL_VIEWS))),
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
DREAM_BATTLES = {
    'GohmaStage': ('Gohma', 'Enemy_DungeonBoss_Gohma'),
    'WolfosStage': ('Lobo', 'Enemy_Wolfos'),
    'LizalfosStage': ('Lizalfos', 'Enemy_MiddleBoss_Lizalfos'),
    'DodongoStage': ('Roi Dodongo', 'Enemy_DungeonBoss_Dodongo'),
    'BigOctoStage': ('Bigocto', 'Enemy_MiddleBoss_BigOcto'),
    'BarinadeStage': ('Barinade', 'Enemy_DungeonBoss_Barinade'),
    'StalfosWeakStage': ('Stalfos du Temple de la Forêt', 'Enemy_Stalfos_Weak'),
    'MegStage': ('Meg', 'Enemy_MiddleBoss_Poe_Meg'),
    'PhantomGanonStage': ('Ganon spectral', 'Enemy_DungeonBoss_PhantomGanon'),
    'FlareDancerStage': ('Danseur de feu', 'Enemy_MiddleBoss_FlareDancer'),
    'VolvagiaStage': ('Volvagia', 'Enemy_DungeonBoss_Volvagia'),
    'WolfosWhiteStage': ('Lobo blanc', 'Enemy_Wolfos_White'),
    'DarkLinkStage': ('Link noir', 'Enemy_MiddleBoss_DarkLink'),
    'MorphaStage': ('Morpha', 'Enemy_DungeonBoss_Morpha'),
    'DeadHandStage': ('Poigneur', 'Enemy_DeadHand'),
    'StalfosStage': ('Stalfos du Temple de l’Ombre', 'Enemy_Stalfos_AlwaysRespawn'),
    'BongoBongoStage': ('Bongo Bongo', 'Enemy_DungeonBoss_BongoBongo'),
    'GerudoThiefStage': ('Guerrière Gerudo', 'Enemy_MiddleBoss_GerudoThief'),
    'IronKnuckleWhiteStage': ('Hache-viande blanc', 'Enemy_IronKnuckle_Silver'),
    'NaboruStage': ('Nabooru', 'Enemy_MiddleBoss_IronKnuckle_Nabooru'),
    'TwinrovaStage': ('Twinrova', 'Enemy_DungeonBoss_Twinrova'),
    'DinolfosStage': ('Dinolfos', 'Enemy_Dinolfos'),
    'IronKnuckleBlackStage': ('Hache-viande noir', 'Enemy_IronKnuckle_Black'),
    'GanondorfStage': ('Ganondorf', 'Enemy_DungeonBoss_Ganondorf'),
    'GanonStage': ('Ganon', 'Enemy_DungeonBoss_Ganon_SecondHalfBattle'),
}
DREAM_AREAS = {'EnemyMuseum': 'Musée', 'BossRushIntervalRoom': 'Salle intermédiaire',
               **{scene: name for scene, (name, _) in DREAM_BATTLES.items()}}
DREAM_SCENE_VIEWS = {scene: f'Monde des rêves · {area}' for scene, area in DREAM_AREAS.items()}
DREAM_BATTLE_VIEWS = {DREAM_SCENE_VIEWS[scene] for scene in DREAM_BATTLES}
REGION_VIEWS['DreamWorld'] = {None: DREAM_SCENE_VIEWS['EnemyMuseum']}
CASTLE_VIEWS = tuple(f'{REGION_NAMES["HyruleCastle"]} · {area}' for area in ('Abords', 'Cour'))
CASTLE_OUTSKIRTS, CASTLE_COURT = CASTLE_VIEWS
REGION_VIEWS['HyruleCastle'] = {'Child': CASTLE_OUTSKIRTS}
GANON_AREAS = ('Abords', 'Effondrement', 'Arène de Ganon')
GANON_VIEWS = tuple(f'{REGION_NAMES["GanonCastle"]} · {area}' for area in GANON_AREAS)
GANON_OUTSKIRTS, GANON_ESCAPE, GANON_FINAL = GANON_VIEWS
REGION_VIEWS['GanonCastle'] = {'Adult': GANON_OUTSKIRTS}
del REGION_VIEWS['GerudoFortress']['Child']
MARKET_CASTLE_AGES = {'HyruleCastle': 'Child', 'GanonCastle': 'Adult'}
SHARED_DUNGEONS = frozenset(region for region, views in REGION_VIEWS.items() if None in views)
FLOOR_OPTIONS = {
    **{view: tuple(zip(GORON_LEVELS, views)) for views in GORON_VIEWS.values() for view in views},
    **{view: floors for floors in DUNGEON_FLOORS.values() for _, view in floors},
    **dict.fromkeys(SPIRIT_VIEWS, (*DUNGEON_FLOORS['SpiritTemple'][:4], *DUNGEON_FLOORS['SpiritTemple'][4:][::-1])),
    **dict.fromkeys(CASTLE_VIEWS, tuple(zip(('Abords', 'Cour'), CASTLE_VIEWS))),
    **dict.fromkeys(GANON_VIEWS, tuple(zip(GANON_AREAS, GANON_VIEWS))),
    **dict.fromkeys(DREAM_SCENE_VIEWS.values(),
                    tuple((area, DREAM_SCENE_VIEWS[scene]) for scene, area in DREAM_AREAS.items())),
}
AGE_VIEWS = REGION_VIEWS['KokiriForest']
VIEWS = {label: (region, age) for region, ages in REGION_VIEWS.items()
         for age, label in ages.items()}
BURNT_VILLAGE = 'Cocorico · Après l’incendie'
VIEWS[BURNT_VILLAGE] = ('KakarikoVillage', 'Adult')
VIEWS[CASTLE_COURT] = ('HyruleCastle', 'Child')
VIEWS.update(dict.fromkeys((GANON_ESCAPE, GANON_FINAL), ('GanonCastle', 'Adult')))
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
FOUNTAIN_ICE_BACKDOOR = 'Accès secondaire à la caverne'
ICE_CAVERN_BACKDOOR = 'Sortie secondaire de la caverne'
WINDMILL_TO_GRAVE = 'Passage vers la tombe de Dampé'
GRAVE_TO_WINDMILL = 'Passage vers le moulin'
GRAVE_TO_TOMB = 'Entrée de la tombe de Dampé'
TOMB_TO_GRAVE = 'Remontée vers le cimetière'
DREAM_CHALLENGE_ARRIVAL = 'Arrivée du défi'
SAGE_ROOM_ARRIVAL = 'Arrivée dans la Chambre des Sages'
TEMPLE_SAGE_RETURN = 'Retour de la Chambre des Sages'
SPIRIT_BOSS_TO_COLOSSUS = 'Sortie de Twinrova vers le Colosse'
SPIRIT_BOSS_TO_SAGES = 'Sortie de Twinrova vers les Sages'
SPIRIT_SAGE_CONTINUE = 'Suite de la cinématique de Twinrova'
SPIRIT_COLOSSUS_ARRIVAL = 'Arrivée au Requiem des Esprits'
DEKU_BOSS_EXIT = 'Portail de Gohma'
DODONGO_BOSS_EXIT = 'Portail du Roi Dodongo'
JABU_BOSS_EXIT = 'Portail de Barinade'
GANON_ESCAPE_TO_FINAL = 'Sortie vers l’arène de Ganon'
GANON_FINAL_ARRIVAL = 'Arrivée dans l’arène de Ganon'
GANONDORF_TO_ESCAPE = 'Début de l’effondrement'
GANON_ESCAPE_ARRIVAL = 'Arrivée au début de la fuite'
GANONDORF_TILE = 'Dalle de Ganondorf'
GANONDORF_TILE_ACTOR = 'Obj_InsideGanonCastle_BrokenFloor_A_01'
FIRE_KAKARIKO_ARRIVAL = 'Arrivée à Cocorico après Volvagia'
FIRE_KAKARIKO_CONTINUE = 'Suite de la cinématique de Volvagia'
FIRE_SAGE_SCENE = 'Sages · Volvagia'
# The fire cutscene passes through Kakariko before entering the Sage Room.
ADULT_BOSS_RETURNS = {
    'ForestTemple': ('Ganon spectral', 'KokiriForest', 'WarpFromForestTemple'),
    'FireTemple': ('Volvagia', 'DeathMountainCrater', 'FireBolero'),
    'WaterTemple': ('Morpha', 'LakeHylia', 'WaterSerenade'),
    'ShadowTemple': ('Bongo Bongo', 'Graveyard', 'ShadowNocturne'),
}
SIDE_PORTALS = {
    'BottomOfTheWell': {
        label: ('BottomOfTheWell', WELL_VIEWS[destination], label, arrival)
        for ends in WELL_LEVEL_CROSSINGS
        for (_, label, _, _), (destination, arrival, _, _) in (ends, ends[::-1])
    },
    'GanonCastle': {
        GANON_ESCAPE_TO_FINAL: ('GanonCastle', GANON_FINAL, 'Arène de Ganon', GANON_FINAL_ARRIVAL),
    },
    'InsideGanonCastle': {
        GANONDORF_TO_ESCAPE: ('GanonCastle', GANON_ESCAPE, 'Fuite du château', GANON_ESCAPE_ARRIVAL),
        **{source: ('InsideGanonCastle', destination, title, arrival)
           for (_, trial), view in zip(GANON_TRIALS.values(), GANON_TRIAL_VIEWS)
           for source, destination, title, arrival in (
               (f'Entrée · {trial}', view, f'Épreuve · {trial}', f'Retour · {trial}'),
               (f'Retour · {trial}', GANON_DUNGEON_VIEWS[0], 'Salle des épreuves', f'Entrée · {trial}'),
           )},
        **{label: ('InsideGanonCastle', GANON_DUNGEON_VIEWS[destination], label, arrival)
           for ends in GANON_TOWER_CROSSINGS
           for (_, label, _, _), (destination, arrival, _, _) in (ends, ends[::-1])},
    },
    'GerudoTrainingGround': {
        TRAINING_TO_WALKWAY: ('GerudoTrainingGround', TRAINING_VIEWS[1], 'Passerelle', TRAINING_TO_STATUE),
        TRAINING_TO_STATUE: ('GerudoTrainingGround', TRAINING_VIEWS[0], 'Salle de la statue', TRAINING_TO_WALKWAY),
        TRAINING_TO_CEILING: ('GerudoTrainingGround', TRAINING_VIEWS[1], 'Alcôve du plafond', TRAINING_TO_MAZE),
        TRAINING_TO_MAZE: ('GerudoTrainingGround', TRAINING_VIEWS[0], 'Labyrinthe inférieur', TRAINING_TO_CEILING),
    },
    'DreamWorld': {
        'Organisateur du défi': ('DreamWorld', DREAM_SCENE_VIEWS['BossRushIntervalRoom'],
                                 'Défi des boss', DREAM_CHALLENGE_ARRIVAL),
    },
    'DesertColossus': {
        'spirit_temple_left_hand_entrance': ('SpiritTemple', SPIRIT_VIEWS[2], 'Temple · main gauche', 'left_hand_entrance'),
        'spirit_temple_right_hand_entrance': ('SpiritTemple', SPIRIT_VIEWS[2], 'Temple · main droite', 'right_hand_entrance'),
    },
    'SpiritTemple': {
        **{label: ('SpiritTemple', SPIRIT_VIEWS[destination], label, arrival)
           for ends in SPIRIT_INTERIOR_LINKS
           for (_, label, _, _), (destination, arrival, _, _) in (ends, ends[::-1])},
        'left_hand_entrance': ('DesertColossus', None, 'Colosse · main gauche', 'spirit_temple_left_hand_entrance'),
        'right_hand_entrance': ('DesertColossus', None, 'Colosse · main droite', 'spirit_temple_right_hand_entrance'),
        SPIRIT_BOSS_TO_COLOSSUS: ('DesertColossus', REGION_VIEWS['DesertColossus']['Adult'],
                                  'Colosse du désert', SPIRIT_COLOSSUS_ARRIVAL),
        SPIRIT_BOSS_TO_SAGES: ('SageRoom', None, 'Chambre des Sages · cinématique', SPIRIT_SAGE_CONTINUE),
    },
    'SageRoom': {
        SPIRIT_SAGE_CONTINUE: ('DesertColossus', REGION_VIEWS['DesertColossus']['Adult'],
                               'Colosse du désert · suite de la cinématique', SPIRIT_COLOSSUS_ARRIVAL),
    },
    'InsideTheDekuTree': {
        **{label: ('InsideTheDekuTree', DEKU_VIEWS[destination], label, arrival)
           for ends in DEKU_LEVEL_CROSSINGS
           for (_, label, _, _), (destination, arrival, _, _) in (ends, ends[::-1])},
        DEKU_BOSS_EXIT: ('KokiriForest', REGION_VIEWS['KokiriForest']['Child'],
                         'Kokiri Forest · sortie de Gohma', DEKU_BOSS_EXIT),
    },
    'DodongoCavern': {
        **{label: ('DodongoCavern', DODONGO_VIEWS[destination], label, arrival)
           for ends in DODONGO_LEVEL_CROSSINGS
           for (_, label, _, _), (destination, arrival, _, _) in (ends, ends[::-1])},
        DODONGO_BOSS_EXIT: ('DeathMountainTrail', None, 'Mont du Péril · sortie du boss', DODONGO_BOSS_EXIT),
    },
    'InsideJabuJabuBelly': {
        **{label: ('InsideJabuJabuBelly', JABU_VIEWS[destination], label, arrival)
           for ends in JABU_LEVEL_CROSSINGS
           for (_, label, _, _), (destination, arrival, _, _) in (ends, ends[::-1])},
        JABU_BOSS_EXIT: ('ZoraFountain', REGION_VIEWS['ZoraFountain']['Child'],
                         'Fontaine Zora · sortie de Barinade', JABU_BOSS_EXIT),
    },
    'ZoraFountain': {
        FOUNTAIN_ICE_BACKDOOR: ('IceCavern', None, 'Caverne de glace · passage secondaire', ICE_CAVERN_BACKDOOR),
    },
    'IceCavern': {
        ICE_CAVERN_BACKDOOR: ('ZoraFountain', None, 'Fontaine Zora · passage secondaire', FOUNTAIN_ICE_BACKDOOR),
    },
    'KakarikoVillage': {
        WINDMILL_TO_GRAVE: ('Graveyard', UNDERGROUND_VIEWS['Graveyard']['Adult'], 'Tombe de Dampé', GRAVE_TO_WINDMILL),
        FIRE_KAKARIKO_CONTINUE: ('SageRoom', None, 'Chambre des Sages · cinématique de Volvagia', FIRE_SAGE_SCENE),
    },
    'Graveyard': {
        GRAVE_TO_WINDMILL: ('KakarikoVillage', None, 'Moulin de Cocorico', WINDMILL_TO_GRAVE),
        GRAVE_TO_TOMB: ('Graveyard', UNDERGROUND_VIEWS['Graveyard']['Adult'], 'Tombe de Dampé', TOMB_TO_GRAVE),
        TOMB_TO_GRAVE: ('Graveyard', REGION_VIEWS['Graveyard']['Adult'], 'Remonter à la surface', GRAVE_TO_TOMB),
    },
}
PORTAL_ARRIVAL_STARTS = {
    ('SpiritTemple', 'left_hand_entrance'): ('SpiritTemple_FromLeftHand',),
    ('SpiritTemple', 'right_hand_entrance'): ('SpiritTemple_FromRightHand',),
    ('DesertColossus', 'spirit_temple_left_hand_entrance'): ('DesertColossus_FromSpiritTempleLeftHand',),
    ('DesertColossus', 'spirit_temple_right_hand_entrance'): ('DesertColossus_FromSpiritTempleRightHand',),
    ('DesertColossus', SPIRIT_COLOSSUS_ARRIVAL): ('SpiritRequiem',),
    ('SageRoom', SPIRIT_SAGE_CONTINUE): ('Arrivée après Twinrova',),
    ('GanonCastle', GANON_FINAL_ARRIVAL): ('FinalBattleField_Entrance',),
    ('GanonCastle', GANON_ESCAPE_ARRIVAL): ('CrumblingGanonCastle_StartPos',),
    ('KakarikoVillage', FIRE_KAKARIKO_ARRIVAL): ('KakarikoVillage_Entrance',),
    ('KokiriForest', DEKU_BOSS_EXIT): ('WarpFromDekuTree', 'WarpFromDekuTree_2'),
    ('DeathMountainTrail', DODONGO_BOSS_EXIT): ('DodongoCavernFront',),
    ('ZoraFountain', JABU_BOSS_EXIT): ('ClearJabuJabu',),
    ('LostWood', NEIGHBORS['LostWood']['ZoraRiver']): ('LostWood_ZoraRiverSide',),
    ('ZoraRiver', NEIGHBORS['ZoraRiver']['LostWood']): ('ZoraRiver_LostWoodSide',),
    ('LostWood', NEIGHBORS['LostWood']['GoronCity']): ('LostWood_GoronCitySide_before', 'LostWood_GoronCitySide_after'),
    ('GoronCity', NEIGHBORS['GoronCity']['LostWood']): ('GoronCity_LostWoodSide_before', 'GoronCity_LostWoodSide_after'),
    ('KokiriForest', NEIGHBORS['KokiriForest']['LostWood']): ('KokiriForest_FrontOfLostWood',),
    ('LostWood', NEIGHBORS['LostWood']['KokiriForest']): ('LostWood_Entrance',),
    ('LostWood', NEIGHBORS['LostWood']['SacredForestMeadow']): ('LostWood_FrontOfSacredForestMeadow',),
    ('SacredForestMeadow', NEIGHBORS['SacredForestMeadow']['LostWood']): ('SacredForestMeadow_FrontOfLostWood',),
    ('KokiriForest', NEIGHBORS['KokiriForest']['InsideTheDekuTree']): ('FrontDekuTree',),
    ('InsideTheDekuTree', NEIGHBORS['InsideTheDekuTree']['KokiriForest']): ('Entrance',),
    ('KokiriForest', NEIGHBORS['KokiriForest']['DreamWorld']): ('ReturnFromDreamWorld',),
    ('DreamWorld', NEIGHBORS['DreamWorld']['KokiriForest']): ('EnemyMusuem',),
    ('DreamWorld', DREAM_CHALLENGE_ARRIVAL): ('BossRush',),
    ('SageRoom', NEIGHBORS['SageRoom']['TempleOfTime']): (SAGE_ROOM_ARRIVAL,),
    ('TempleOfTime', NEIGHBORS['TempleOfTime']['SageRoom']): (TEMPLE_SAGE_RETURN,),
    ('SacredForestMeadow', NEIGHBORS['SacredForestMeadow']['ForestTemple']): ('OutsideOfForestTemple',),
    ('ForestTemple', NEIGHBORS['ForestTemple']['SacredForestMeadow']): ('ForestTemple',),
    ('DesertColossus', NEIGHBORS['DesertColossus']['SpiritTemple']): ('DesertColossus_FromSpiritTempleEntrance',),
    ('SpiritTemple', NEIGHBORS['SpiritTemple']['DesertColossus']): ('SpiritTemple_Entrance',),
    ('LakeHylia', NEIGHBORS['LakeHylia']['WaterTemple']): ('OutsideOfWaterTemple',),
    ('WaterTemple', NEIGHBORS['WaterTemple']['LakeHylia']): ('WaterTemple_FromLakeHylia',),
    ('DeathMountainTrail', NEIGHBORS['DeathMountainTrail']['DodongoCavern']): ('MountainTrail_DodongoCavernSide',),
    ('DodongoCavern', NEIGHBORS['DodongoCavern']['DeathMountainTrail']): ('DodongoCavern_MountainTrailSide',),
    ('DeathMountainCrater', NEIGHBORS['DeathMountainCrater']['FireTemple']): ('OutsideOfFireTemple',),
    ('FireTemple', NEIGHBORS['FireTemple']['DeathMountainCrater']): ('FireTemple',),
    ('Graveyard', NEIGHBORS['Graveyard']['ShadowTemple']): ('GraveYard_ShadowTempleSide',),
    ('ShadowTemple', NEIGHBORS['ShadowTemple']['Graveyard']): ('Entrance',),
    ('KakarikoVillage', NEIGHBORS['KakarikoVillage']['BottomOfTheWell']): ('Kakariko_WellSide',),
    ('BottomOfTheWell', NEIGHBORS['BottomOfTheWell']['KakarikoVillage']): ('Well_KakarikoSide',),
    ('ZoraFountain', NEIGHBORS['ZoraFountain']['InsideJabuJabuBelly']): ('ZoraFountain_FromInsideJabuJabuBelly',),
    ('InsideJabuJabuBelly', NEIGHBORS['InsideJabuJabuBelly']['ZoraFountain']): ('InsideJabuJabuBelly_FromZoraFountain',),
    ('ZoraFountain', NEIGHBORS['ZoraFountain']['IceCavern']): ('ZoraFountain_FromIceCavern',),
    ('IceCavern', NEIGHBORS['IceCavern']['ZoraFountain']): ('IceCavern_FromZoraFountain',),
    ('ZoraFountain', FOUNTAIN_ICE_BACKDOOR): ('ZoraFountain_FromIceCavern_Backdoor',),
    ('IceCavern', ICE_CAVERN_BACKDOOR): ('IceCavern_FromZoraFountain_Backdoor',),
    ('KokiriBridge', NEIGHBORS['KokiriBridge']['HyruleField']): ('LostWoodBridge_FrontOfHyruleField',),
    ('HyruleField', NEIGHBORS['HyruleField']['KokiriForest']): ('HyruleField_FrontOfLostWoodBridge',),
    ('Market', NEIGHBORS['Market']['HyruleField']): ('Market_Entrance',),
    ('HyruleField', NEIGHBORS['HyruleField']['Market']): ('HyruleField_FrontOfMarket',),
    ('KakarikoVillage', NEIGHBORS['KakarikoVillage']['HyruleField']): ('KakarikoVillage_Entrance',),
    ('HyruleField', NEIGHBORS['HyruleField']['KakarikoVillage']): ('HyruleField_FrontOfKakarikoVillage',),
    ('ZoraRiver', NEIGHBORS['ZoraRiver']['HyruleField']): ('ZoraRiver_Entrance',),
    ('HyruleField', NEIGHBORS['HyruleField']['ZoraRiver']): ('HyruleField_FrontOfZoraRiver',),
    ('GerudoValley', NEIGHBORS['GerudoValley']['HyruleField']): ('GerudoValley_Entrance',),
    ('HyruleField', NEIGHBORS['HyruleField']['GerudoValley']): ('HyruleField_FrontOfGerudoValley',),
    ('GerudoValley', NEIGHBORS['GerudoValley']['LakeHylia']): ('GerudoValley_FromLakeHylia',),
    ('LakeHylia', NEIGHBORS['LakeHylia']['GerudoValley']): ('LakeHylia_FromGerudoValley',),
    ('DesertColossus', NEIGHBORS['DesertColossus']['HountedWasteland']): ('DesertColossus_FromHountedWasteland',),
    ('HountedWasteland', NEIGHBORS['HountedWasteland']['DesertColossus']): ('HountedWasteland_FromDesertColossus',),
    ('HountedWasteland', NEIGHBORS['HountedWasteland']['GerudoFortress']): ('HountedWasteland_FromGerudoFortress',),
    ('GerudoFortress', NEIGHBORS['GerudoFortress']['HountedWasteland']): ('GerudoFortress_FromHountedWasteland',),
    ('GerudoFortress', NEIGHBORS['GerudoFortress']['GerudoValley']): ('GerudoFortress_FromGerudoValley',),
    ('GerudoValley', NEIGHBORS['GerudoValley']['GerudoFortress']): ('GerudoValley_FromGerudoFortress',),
    ('GerudoFortress', NEIGHBORS['GerudoFortress']['GerudoTrainingGround']): ('GerudoFortress_FromGerudoTrainingGround',),
    ('GerudoTrainingGround', NEIGHBORS['GerudoTrainingGround']['GerudoFortress']): ('GerudoTrainingGround_FromGerudoFortress',),
    ('ZoraRiver', NEIGHBORS['ZoraRiver']['ZoraDomain']): ('ZoraRiver_FromZoraDomain',),
    ('ZoraDomain', NEIGHBORS['ZoraDomain']['ZoraRiver']): ('ZoraDomain_FromZoraRiver',),
    ('ZoraFountain', NEIGHBORS['ZoraFountain']['ZoraDomain']): ('ZoraFountain_FromZoraDomain',),
    ('ZoraDomain', NEIGHBORS['ZoraDomain']['ZoraFountain']): ('ZoraDomain_FromZoraFountain',),
    ('LakeHylia', NEIGHBORS['LakeHylia']['ZoraDomain']): ('ZoraLakeHylia_FromZoraDomain',),
    ('ZoraDomain', NEIGHBORS['ZoraDomain']['LakeHylia']): ('ZoraDomain_FromLakeHylia',),
    ('KakarikoVillage', NEIGHBORS['KakarikoVillage']['Graveyard']): ('Kakariko_GraveYardSide',),
    ('Graveyard', NEIGHBORS['Graveyard']['KakarikoVillage']): ('GraveYard_KakarikoSide',),
    ('KakarikoVillage', NEIGHBORS['KakarikoVillage']['DeathMountainTrail']): ('Kakariko_MountainTrailSide',),
    ('DeathMountainTrail', NEIGHBORS['DeathMountainTrail']['KakarikoVillage']): ('MountainTrail_KakarikoSide',),
    ('DeathMountainTrail', NEIGHBORS['DeathMountainTrail']['GoronCity']): ('MountainTrail_GoronCitySide',),
    ('GoronCity', NEIGHBORS['GoronCity']['DeathMountainTrail']): ('GoronCity_MountainTrailSide',),
    ('DeathMountainTrail', NEIGHBORS['DeathMountainTrail']['DeathMountainCrater']): ('MountainTrail_CraterSide',),
    ('DeathMountainCrater', NEIGHBORS['DeathMountainCrater']['DeathMountainTrail']): ('Crater_MountainTrailSide',),
    ('DeathMountainCrater', NEIGHBORS['DeathMountainCrater']['GoronCity']): ('Crater_GoronCitySide',),
    ('GoronCity', NEIGHBORS['GoronCity']['DeathMountainCrater']): ('GoronCity_CraterSide',),
    ('Market', NEIGHBORS['Market']['HyruleCastle']): ('Market_FrontOfHyruleCastle',),
    ('HyruleCastle', NEIGHBORS['HyruleCastle']['Market']): ('HyruleCastle_Entrance',),
    ('Market', NEIGHBORS['Market']['GanonCastle']): ('Market_Entrance_FromCastle',),
    ('GanonCastle', NEIGHBORS['GanonCastle']['Market']): ('GanonCastleEntrance',),
    ('GanonCastle', NEIGHBORS['GanonCastle']['InsideGanonCastle']): ('GanonCastleEntrance_FromInside',),
    ('InsideGanonCastle', NEIGHBORS['InsideGanonCastle']['GanonCastle']): ('Entrance',),
    ('KakarikoVillage', WINDMILL_TO_GRAVE): ('KakarikoWindmill_GraveYardSide',),
    ('Graveyard', GRAVE_TO_WINDMILL): ('GraveYard_KakarikoWindmillSide',),
    ('Graveyard', GRAVE_TO_TOMB): ('HidingHole_HoleExit',),
    ('Graveyard', TOMB_TO_GRAVE): ('HidingHole_HoleEntrance',),
}
for temple, (boss, outside, start) in ADULT_BOSS_RETURNS.items():
    arrival = f'Arrivée après {boss}'
    return_portal = f'Retour après {boss}'
    sage_portal = f'Sages · {boss}'
    outside_view = REGION_VIEWS[outside]['Adult']
    PORTAL_ARRIVAL_STARTS[outside, arrival] = (start,)
    PORTAL_ARRIVAL_STARTS['SageRoom', sage_portal] = ('Plateforme des Sages',)
    SIDE_PORTALS[temple] = {
        return_portal: (outside, outside_view, REGION_NAMES[outside], arrival),
        sage_portal: ('SageRoom', None, 'Chambre des Sages · cinématique', sage_portal),
    }
    SIDE_PORTALS['SageRoom'][sage_portal] = (outside, outside_view, f'{REGION_NAMES[outside]} · après {boss}', arrival)
SIDE_PORTALS['FireTemple'][FIRE_SAGE_SCENE] = (
    'KakarikoVillage', REGION_VIEWS['KakarikoVillage']['Adult'], 'Cocorico · cinématique', FIRE_KAKARIKO_ARRIVAL)
SIDE_PORTALS['FireTemple'].update({
    label: ('FireTemple', FIRE_VIEWS[destination], label, arrival)
    for ends in FIRE_LEVEL_CROSSINGS
    for (_, label, _, _), (destination, arrival, _, _) in (ends, ends[::-1])
})
SIDE_PORTALS['ShadowTemple'].update({
    **{label: ('ShadowTemple', SHADOW_VIEWS[destination], label, arrival)
       for ends in SHADOW_LEVEL_CROSSINGS
       for (_, label, _), (destination, arrival, _) in (ends, ends[::-1])},
    SHADOW_BOSS_DOOR: ('ShadowTemple', SHADOW_VIEWS[4], SHADOW_BOSS_DOOR, SHADOW_BOSS_LANDING),
    SHADOW_BOSS_LANDING: ('ShadowTemple', SHADOW_VIEWS[3], 'Voir l’accès supérieur', SHADOW_BOSS_DOOR),
})
SIDE_PORTALS['WaterTemple'].update({
    label: ('WaterTemple', WATER_VIEWS[destination], label, arrival)
    for ends in WATER_LEVEL_CROSSINGS
    for (_, label, _, _), (destination, arrival, _, _) in (ends, ends[::-1])
})
SIDE_PORTALS['ForestTemple'].update({
    label: ('ForestTemple', FOREST_VIEWS[destination], label, arrival)
    for ends in FOREST_LEVEL_CROSSINGS
    for (_, label, _, _), (destination, arrival, _, _) in (ends, ends[::-1])
})
GRAVE_TOMB_ANCHORS = {
    ('HidingHole_FieldEntranceGo', 14429999406297140688): GRAVE_TO_TOMB,
    ('HidingHole_FieldExitGo', 13508899304624178854): TOMB_TO_GRAVE,
    ('HidingHole_HoleExit', 16657254736794208888): 'HidingHole_HoleExit',
    ('HidingHole_HoleEntrance', 6836600866498450360): 'HidingHole_HoleEntrance',
}
GRAVE_UNDERGROUND_PORTAL_POINTS = {
    GRAVE_TO_WINDMILL, TOMB_TO_GRAVE,
    *PORTAL_ARRIVAL_STARTS['Graveyard', GRAVE_TO_WINDMILL],
    *PORTAL_ARRIVAL_STARTS['Graveyard', TOMB_TO_GRAVE],
}
PORTAL_START_NAMES = {}
for (zone, _), names in PORTAL_ARRIVAL_STARTS.items():
    PORTAL_START_NAMES.setdefault(zone, set()).update(names)
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
LOST_WOOD_RESET = 'Retour à Kokiri'
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
GANON_TOWER_ANCHORS = {
    'Land_InsideGanonCastle_Room19_A_01': 'Pied de la tour',
    'Land_InsideGanonCastle_Room20_A_01': 'Salle du premier étage',
    'Land_InsideGanonCastle_Room22_A_01': 'Salle du deuxième étage',
    'Land_InsideGanonCastle_Room24_A_01': 'Salle du troisième étage',
    'Land_InsideGanonCastle_Room26_A_01': 'Salle de Ganondorf',
    GANONDORF_TILE_ACTOR: GANONDORF_TILE,
}
GANON_ESCAPE_ANCHORS = {
    'CrumblingGanonCastle_StartPos': 'Début de la fuite',
    **{f'RestartPos{i}': f'Passage {i}' for i in range(1, 8)},
}
GANON_FINAL_LANDMARKS = {
    'Enemy_DungeonBoss_Ganon_SecondHalfBattle': 'Ganon',
    'Obj_GanonCastle_MasterSword_A_01': 'Épée de légende',
    'EftLoc_FinalBattleField_ZeldaMagic_Start_00': 'Zelda',
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


def ganon_trial_view(position):
    """Choose the wing beyond a hall door when a live position has no room ID."""
    x, _, z = position
    # The castle entrance is south of the hall, between the two southern wings.
    if z > 7.8 and abs(x) < 12:
        return GANON_DUNGEON_VIEWS[0]
    distances = [(x - door_x) * dx + (z - door_z) * dz for door_x, door_z, dx, dz in GANON_TRIAL_DOOR_PLANES]
    trial = max(range(len(distances)), key=distances.__getitem__)
    return GANON_TRIAL_VIEWS[trial] if distances[trial] > 0.2 else GANON_DUNGEON_VIEWS[0]


def ganon_tower_points(sources):
    points = crossing_level_points(sources, GANON_TOWER_CROSSINGS)
    for source in sources.values():
        for actor in source['root'].get('Actors', ()):
            position = actor.get('Translate')
            gyaml = actor.get('Gyaml')
            if not position:
                continue
            label = GANON_TOWER_ANCHORS.get(gyaml)
            if gyaml == 'Enemy_DungeonBoss_Ganondorf' and actor.get('Hash') == 15798214583796164285:
                label = GANONDORF_TO_ESCAPE
            if gyaml == 'DungeonRoomCenterAnchor' and 133 <= position[1] < 161:
                x, _, z = position
                if abs(x) > 12 or abs(z + 25) > 12:
                    label = 'Passage de la tour'
            if label and (floor := ganon_dungeon_floor(position)):
                points.add((floor, label, (position[0], position[2])))
    return points


def training_level_points(sources):
    anchors = {('DungeonRoomIdAnchor', ident): label for ident, label in TRAINING_WALKWAY_ANCHORS.items()}
    anchors['Obj_ScarecrowMarker_B_00', 6572899987226388103] = TRAINING_SCARECROW
    anchors['Obj_Gerudo_SwitchShutter_A_04', TRAINING_WALKWAY_GATE] = TRAINING_TO_STATUE
    anchors['DungeonRoomArea', TRAINING_CEILING_CLIMB] = TRAINING_TO_MAZE
    return {(1, anchors[key], (position[0], position[2]))
            for source in sources.values() for actor in source['root'].get('Actors', ())
            if (key := (actor.get('Gyaml'), actor.get('Hash'))) in anchors
            and (position := actor.get('Translate'))}


def spirit_level_points(sources):
    anchors = {
        ('MapIconEntranceAnchor', 452821593555612172): [(2, 'right_hand_entrance')],
        ('MapIconEntranceAnchor', 17977111214894828225): [(2, 'left_hand_entrance')],
        ('DungeonRoomCenterAnchor', 8163808957952677095): [(4, 'Arène de Twinrova')],
        ('DungeonRoomCenterAnchor', 2947018282879123924): [(5, 'Couloir derrière la statue')],
        ('Obj_SpiritTemple_SwitchShutter_A_05', 7552959510754997355): [(5, 'Porte intermédiaire')],
    }
    anchors.update({('StartPos', name): [(2, name)]
                    for (region, portal), names in PORTAL_ARRIVAL_STARTS.items()
                    if region == 'SpiritTemple' and portal in SIDE_PORTALS[region]
                    for name in names})
    for ends in SPIRIT_INTERIOR_LINKS:
        for floor, label, kind, ident in ends:
            anchors.setdefault((kind, ident), []).append((floor, label))
    return {(floor, label, (position[0], position[2]))
            for source in sources.values() for actor in source['root'].get('Actors', ())
            if (kind := actor.get('Gyaml'))
            and (key := (kind, actor.get('Name') if kind == 'StartPos' else actor.get('Hash'))) in anchors
            and (position := actor.get('Translate'))
            for floor, label in anchors[key]}


def shadow_level_points(sources):
    """Use room areas at floor changes and the StartPos of the boss entrance event."""
    anchors = {
        **{('DungeonRoomArea', ident): (floor, label)
           for ends in SHADOW_LEVEL_CROSSINGS for floor, label, ident in ends},
        ('Obj_ShadowTemple_SwitchShutter_A_01', 12557339757091997106): (3, SHADOW_BOSS_DOOR),
        ('StartPos', 15657470794246498904): (4, SHADOW_BOSS_LANDING),
    }
    return {(*anchors[key], (position[0], position[2]))
            for source in sources.values() for actor in source['root'].get('Actors', ())
            if (key := (actor.get('Gyaml'), actor.get('Hash'))) in anchors
            and (position := actor.get('Translate'))}


def water_level_points(sources):
    crossings = {(kind, ident): (floor, label) for ends in WATER_LEVEL_CROSSINGS for floor, label, kind, ident in ends}
    return {(*anchor, (position[0], position[2]))
            for source in sources.values() for actor in source['root'].get('Actors', ())
            if (kind := actor.get('Gyaml'))
            and (anchor := WATER_CONTROLS.get(kind) or crossings.get((kind, actor.get('Hash'))))
            and (position := actor.get('Translate'))}


def crossing_level_points(sources, crossings):
    anchors = {}
    for ends in crossings:
        for floor, label, kind, ident in ends:
            anchors.setdefault((kind, ident), []).append((floor, label))
    return {(floor, label, (position[0], position[2]))
            for source in sources.values() for actor in source['root'].get('Actors', ())
            if (key := (actor.get('Gyaml'), actor.get('Hash'))) in anchors
            and (position := actor.get('Translate'))
            for floor, label in anchors[key]}


LEVEL_POINT_EXTRACTORS = {
    'BottomOfTheWell': lambda sources: crossing_level_points(sources, WELL_LEVEL_CROSSINGS),
    'InsideJabuJabuBelly': lambda sources: crossing_level_points(sources, JABU_LEVEL_CROSSINGS),
    'DodongoCavern': lambda sources: crossing_level_points(sources, DODONGO_LEVEL_CROSSINGS),
    'InsideTheDekuTree': lambda sources: crossing_level_points(sources, DEKU_LEVEL_CROSSINGS),
    'FireTemple': lambda sources: crossing_level_points(sources, FIRE_LEVEL_CROSSINGS),
    'ForestTemple': lambda sources: crossing_level_points(sources, FOREST_LEVEL_CROSSINGS),
    'InsideGanonCastle': ganon_tower_points,
    'GerudoTrainingGround': training_level_points,
    'ShadowTemple': shadow_level_points,
    'SpiritTemple': spirit_level_points,
    'WaterTemple': water_level_points,
}
BOSS_WARP_ANCHORS = {
    'InsideTheDekuTree': (18328422019320660370, 5, (DEKU_BOSS_EXIT,)),
    'DodongoCavern': (13216581863777340373, 2, (DODONGO_BOSS_EXIT,)),
    'InsideJabuJabuBelly': (9190184471319613614, 3, (JABU_BOSS_EXIT,)),
    'SpiritTemple': (11243501154977749945, 4, (SPIRIT_BOSS_TO_COLOSSUS, SPIRIT_BOSS_TO_SAGES)),
    'ForestTemple': (7322827475260825437, 5, ('Retour après Ganon spectral', 'Sages · Ganon spectral')),
    'FireTemple': (14585775662663687502, 5, ('Retour après Volvagia', 'Sages · Volvagia', FIRE_SAGE_SCENE)),
    'WaterTemple': (9109272685779005276, 2, ('Retour après Morpha', 'Sages · Morpha')),
    'ShadowTemple': (15240382889320952895, 4, ('Retour après Bongo Bongo', 'Sages · Bongo Bongo')),
}

GUIDE_ROUTE = 'Trajet du guide'
DAMPE_ROUTES = {'Playing': 'Première course', 'PlayingSecond': 'Seconde course'}
GANON_ESCAPE_ROUTE = 'Trajet de Zelda'
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


def guide_routes(sources, labels=None, *, references=None):
    """Project the native Guide rail, including its Bézier handles, onto X/Z."""
    if labels is None:
        labels = {'Guide': GUIDE_ROUTE}
    routes = set()
    for source in sources.values():
        for rail in source['root'].get('Rails', ()):
            label = labels.get(rail.get('Name'))
            if (not label or rail.get('Gyaml') != 'Guide' or rail.get('IsClosed')
                    or (references is not None and rail.get('Hash') not in references)):
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
            routes.add((label, tuple(points)))
    return routes


def actor_guide_routes(sources, kind, labels):
    references = {link.get('Dst') for source in sources.values()
                  for actor in source['root'].get('Actors', ())
                  if actor.get('Gyaml') == kind
                  for link in actor.get('Rails', ()) if link.get('Dst') is not None}
    return guide_routes(sources, labels, references=references)


def final_battle_routes(sources):
    points = {(position[0], position[2]) for source in sources.values() for actor in source['root'].get('Actors', ())
              if actor.get('Gyaml') == 'AirWallEnemy' and (position := actor.get('Translate'))}
    if len(points) != 10:
        return ()
    x = sum(point[0] for point in points) / len(points)
    z = sum(point[1] for point in points) / len(points)
    ring = sorted(points, key=lambda point: atan2(point[1] - z, point[0] - x))
    return [('Périmètre de l’arène', (*ring, ring[0]))]


def projection_points(region, sources):
    points = set()
    arrivals = PORTAL_START_NAMES.get(region, set())
    if region == 'SpiritTemple':
        arrivals = set(PORTAL_ARRIVAL_STARTS[region, NEIGHBORS[region]['DesertColossus']])
    elif region == 'HyruleField':
        arrivals = arrivals | PORTAL_START_NAMES['LakeHylia']
    elif region == 'KokiriForest':
        arrivals = arrivals | PORTAL_START_NAMES['KokiriBridge']
    for path, source in sources.items():
        dream_scene = path.rsplit('/', 1)[-1].split('_', 1)[0] if region == 'DreamWorld' else None
        for actor in source['root'].get('Actors', ()):
            position = actor.get('Translate')
            gyaml = actor.get('Gyaml')
            if (position is None and region == 'DreamWorld' and gyaml == 'StartPos'
                    and actor.get('Name') == 'EnemyMusuem' and view_name(path) == DREAM_SCENE_VIEWS['EnemyMuseum']):
                # The museum's native StartPos omits Translate at the scene origin.
                position = (0, 0, 0)
            if not position:
                continue
            label = None
            if gyaml == 'StartPos' and actor.get('Name') in arrivals:
                # Two crater starts share this name and are less than 5 cm apart in X/Z.
                if (region != 'DeathMountainCrater' or actor.get('Name') != 'FireBolero'
                        or actor.get('Hash') == 9726922324643513629):
                    points.add((actor['Name'], (position[0], position[2])))
                if (region == 'KakarikoVillage' and actor.get('Name') == 'KakarikoVillage_Entrance'
                        and view_name(path) == REGION_VIEWS[region]['Adult']):
                    points.add((FIRE_KAKARIKO_CONTINUE, (position[0], position[2])))
            if region == 'KokiriForest':
                if gyaml == 'Obj_Kokiri_Bed_A_01':
                    label = NEIGHBORS[region]['DreamWorld']
            elif region == 'LostWood':
                if gyaml == 'FieldAndDungeonEntranceEventRequestActor':
                    if actor.get('Name') == 'LostWood_Entrance':
                        label = NEIGHBORS[region]['KokiriForest']
                    dynamic = actor.get('Dynamic')
                    if (isinstance(dynamic, dict) and dynamic.get('FirstEventName') == 'Dm_SY_BancChangeGo_LostWood'
                            and dynamic.get('NextStartPosName') == 'KokiriForest_FrontOfLostWood'):
                        label = LOST_WOOD_RESET
            elif region == 'ZoraRiver' and gyaml == 'FieldAndDungeonEntranceEventRequestActor':
                label = ZORA_RIVER_EXITS.get(actor.get('Name'))
            elif (region == 'KakarikoVillage' and gyaml == 'FieldAndDungeonEntranceEventRequestActor'
                  and actor.get('Name') == 'KakarikoWindmill_GraveYardSide'):
                label = WINDMILL_TO_GRAVE
            elif (region == 'Graveyard' and gyaml == 'FieldAndDungeonEntranceEventRequestActor'
                  and actor.get('Name') == 'GraveYard_KakarikoWindmillSide'):
                label = GRAVE_TO_WINDMILL
            elif region == 'Graveyard' and gyaml == 'DestinationAnchor' and view_name(path) == REGION_VIEWS[region]['Adult']:
                label = GRAVE_TOMB_ANCHORS.get((actor.get('Name'), actor.get('Hash')))
            elif region == 'ZoraFountain' and gyaml == 'FieldAndDungeonEntranceEventRequestActor':
                target = {'ZoraFountain_FromIceCavern': 'IceCavern',
                          'ZoraFountain_FromInsideJabuJabuBelly': 'InsideJabuJabuBelly'}.get(actor.get('Name'))
                label = NEIGHBORS[region].get(target)
                if actor.get('Name') == 'ZoraFountain_FromIceCavern_Backdoor':
                    label = FOUNTAIN_ICE_BACKDOOR
            elif (region == 'IceCavern' and gyaml == 'MapIconEntranceAnchor'
                  and actor.get('Hash') == 17335166050006259965):
                label = ICE_CAVERN_BACKDOOR
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
                        label = f'Épreuve · {trial[1]}'
                elif gyaml == 'Obj_InsideGanonCastle_SwitchShutter_A_01':
                    label = GANON_TRIAL_DOORS.get(actor.get('Hash'))
                elif gyaml == 'Obj_GanonCastle_Barrier_A_01':
                    label = 'Barrière de la tour'
            elif region == 'GanonCastle' and gyaml == 'StartPos':
                label = GANON_ESCAPE_ANCHORS.get(actor.get('Name'))
            elif (region == 'GanonCastle' and gyaml == 'FieldAndDungeonEntranceEventRequestActor'
                  and view_name(path) == GANON_ESCAPE):
                dynamic = actor.get('Dynamic')
                if isinstance(dynamic, dict) and dynamic.get('NextBancParamNameAdult') == 'FinalBattleField':
                    label = GANON_ESCAPE_TO_FINAL
            elif region == 'GanonCastle' and gyaml in GANON_FINAL_LANDMARKS and view_name(path) == GANON_FINAL:
                label = GANON_FINAL_LANDMARKS[gyaml]
            elif region == 'GerudoFortress' and gyaml == 'MapIconFacilityAnchor':
                dynamic = actor.get('Dynamic')
                if isinstance(dynamic, dict) and dynamic.get('MapIconFacilityIsOpen') == 'GerudoTrainingGround_MapIcon_Flag':
                    label = NEIGHBORS[region]['GerudoTrainingGround']
            elif region == 'GerudoTrainingGround' and gyaml == 'DungeonRoomCenterAnchor':
                label = TRAINING_ROOM_ANCHORS.get(actor.get('Hash'))
            elif (region == 'GerudoTrainingGround' and gyaml == 'Obj_Gerudo_SwitchShutter_A_04'
                  and actor.get('Hash') == TRAINING_WALKWAY_GATE):
                label = TRAINING_TO_WALKWAY
            elif (region == 'GerudoTrainingGround' and gyaml == 'DungeonRoomArea'
                  and actor.get('Hash') == TRAINING_CEILING_CLIMB):
                label = TRAINING_TO_CEILING
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
                if (gyaml == 'Obj_TimeTemple_MasterSwordBase_A_01'
                        and MARKET_VIEW_AGES.get(view_name(path)) == 'Adult'):
                    # DoorOfTime.SageRoom_MeetRauru returns Link inside the adult temple.
                    points.add((TEMPLE_SAGE_RETURN, (120.91000366210938, -26.65999984741211)))
            elif region == 'SageRoom':
                if gyaml == 'EftLoc_SageRoom_LightPillar_00':
                    label = 'Pilier de lumière'
                elif gyaml == 'StartPos' and not actor.get('Name'):
                    label = NEIGHBORS[region]['TempleOfTime']
                    # DoorOfTime_Draw has an explicit arrival, without a named StartPos.
                    points.add((SAGE_ROOM_ARRIVAL, (-0.029999999329447746, 0.0)))
                    # Dm_Awake_Spirit places Link at the center of the platform.
                    points.add(('Arrivée après Twinrova', (0.0, 0.0)))
                    points.add((SPIRIT_SAGE_CONTINUE, (position[0], position[2])))
                    points.add(('Plateforme des Sages', (0.0, 0.0)))
                    points.update((f'Sages · {boss}', (position[0], position[2]))
                                  for boss, _, _ in ADULT_BOSS_RETURNS.values())
            elif dream_scene in DREAM_BATTLES:
                boss, kind = DREAM_BATTLES[dream_scene]
                if gyaml == kind:
                    label = boss
                elif dream_scene == 'GanondorfStage' and gyaml == GANONDORF_TILE_ACTOR:
                    label = GANONDORF_TILE
                elif gyaml == 'StartPos':
                    label = {dream_scene: 'Arrivée en revanche',
                             'StartPos_SubEvent_AllBossBattle': 'Arrivée pendant le défi'}.get(actor.get('Name'))
            elif region == 'DreamWorld':
                if gyaml == 'StartPos' and actor.get('Name') == 'BossRush':
                    label = DREAM_CHALLENGE_ARRIVAL
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
    if region == 'LostWood':
        portal = NEIGHBORS[region]['KokiriForest']
        if not any(label == portal for label, _ in points):
            starts = {point for label, point in points if label == 'LostWood_Entrance'}
            points.update((portal, point) for point in starts)
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
        projected = projection_points(region, sources)
        if region == 'KokiriForest' and not has_dream_museum:
            projected = {point for point in projected if point[0] != NEIGHBORS[region]['DreamWorld']}
        points.update(projected)
        if frame in (DREAM_SCENE_VIEWS['BossRushIntervalRoom'], DREAM_SCENE_VIEWS['VolvagiaStage']):
            room_areas = [actor for source in sources.values() for actor in source['root'].get('Actors', ())
                          if actor.get('Gyaml') == 'DungeonRoomArea'
                          and actor.get('Translate') and actor.get('Scale')]
            if len(room_areas) == 1:
                x, _, z = room_areas[0]['Translate']
                dx, _, dz = room_areas[0]['Scale']
                label = DREAM_AREAS['BossRushIntervalRoom'] if frame == DREAM_SCENE_VIEWS['BossRushIntervalRoom'] else 'Arène'
                rooms.append((label, (x - dx, z - dz), (x + dx, z + dz)))
        extract_levels = LEVEL_POINT_EXTRACTORS.get(region)
        levels = extract_levels(sources) if extract_levels else set()
        points.update((label, position) for floor, label, position in levels if floor == 0)
        levels = {entry for entry in levels if entry[0] != 0}
        if region in BOSS_WARP_ANCHORS:
            actor_hash, floor, portals = BOSS_WARP_ANCHORS[region]
            levels.update((floor, portal, (position[0], position[2]))
                          for source in sources.values() for actor in source['root'].get('Actors', ())
                          if actor.get('Gyaml') == 'Obj_WarpPoint_A_01' and actor.get('Hash') == actor_hash
                          and (position := actor.get('Translate')) for portal in portals)
        route_extractor = {
            'HountedWasteland': guide_routes,
            'GerudoTrainingGround': training_connections,
        }.get(region)
        if frame in (GANON_FINAL, DREAM_SCENE_VIEWS['GanonStage']):
            route_extractor = final_battle_routes
        routes = route_extractor(sources) if route_extractor else ()
        if region == 'Graveyard':
            routes = actor_guide_routes(sources, 'Npc_Hylia_Dampe_002', DAMPE_ROUTES)
        elif region == 'ShadowTemple':
            routes = actor_guide_routes(sources, 'Obj_ShadowTemple_PaddleShip_A_01', {'Guide': SHADOW_SHIP_ROUTE})
        elif frame == GANON_ESCAPE:
            # Step05 is a pause. Step13 starts beyond the door to FinalBattleField.
            labels = {f'Step{i:02}': GANON_ESCAPE_ROUTE for i in range(1, 13) if i != 5}
            routes = actor_guide_routes(sources, 'Npc_Hylia_Zelda_Adult', labels)
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
            if (len(entry) != 3 or (region not in LEVEL_POINT_EXTRACTORS and region not in BOSS_WARP_ANCHORS)
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
        for scene, view in zip(('GanonCastle', 'CrumblingGanonCastle', 'FinalBattleField'), GANON_VIEWS):
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
    if row.position is None and row.id in UNPOSITIONED_CHECK_AREAS:
        target, _ = UNPOSITIONED_CHECK_AREAS[row.id]
        if target and VIEWS[target][0] == row.region:
            return target
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
        if row.dungeon_room in GANON_TRIAL_ROOM_VIEWS:
            return GANON_TRIAL_ROOM_VIEWS[row.dungeon_room]
        floor = 4 if row.dungeon_room == 24 else ganon_dungeon_floor(row.position)
        if floor == 0 and row.dungeon_room is None:
            return ganon_trial_view(row.position)
        return GANON_DUNGEON_VIEWS[floor]
    if view == SPIRIT_VIEWS[0] and row.position is not None:
        x, y, z = row.position
        if row.id == 'boss#Twinrova' or row.category == 'full_bossheart':
            return SPIRIT_VIEWS[4]
        if (row.dungeon_room in (32, 33, None) and abs(x) <= 10
                and 130 <= y <= 144 and -119.5 <= z < -76.7):
            return SPIRIT_VIEWS[5]
        if abs(x) <= 36 and z < -119.5:
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
            if name == GANON_DUNGEON_VIEWS[0] and label in GANON_TRIAL_VIEW_POINTS:
                trial_view, detail_label = GANON_TRIAL_VIEW_POINTS[label]
                detail = grouped.setdefault(trial_view, {'rooms': set(), 'points': set()})
                detail['points'].add((detail_label, tuple(point)))
            if (name in KOKIRI_VIEW_AGES
                    and (label == NEIGHBORS['KokiriBridge']['HyruleField'] or label in PORTAL_START_NAMES['KokiriBridge'])
                    and kokiri_bridge_position(point)):
                bridge = REGION_VIEWS['KokiriBridge'][KOKIRI_VIEW_AGES[name]]
                target = grouped.setdefault(bridge, {'rooms': set(), 'points': set()})
                if label == NEIGHBORS['KokiriBridge']['HyruleField']:
                    view['points'].add((NEIGHBORS['KokiriForest']['KokiriBridge'], KOKIRI_BRIDGE_GATE))
                    target['points'].add((NEIGHBORS['KokiriBridge']['KokiriForest'], KOKIRI_BRIDGE_GATE))
            elif name in FIELD_VIEW_AGES:
                area = FIELD_PORTAL_AREAS.get(label) or field_area(point)
                local_view = REGION_VIEWS[area][FIELD_VIEW_AGES[name]]
                target = grouped.setdefault(local_view, {'rooms': set(), 'points': set()})
            elif (name == REGION_VIEWS['Graveyard']['Adult']
                  and label in GRAVE_UNDERGROUND_PORTAL_POINTS):
                underground = UNDERGROUND_VIEWS['Graveyard']['Adult']
                target = grouped.setdefault(underground, {'rooms': set(), 'points': set()})
            elif (name in MARKET_VIEW_AGES and temple_position(point, MARKET_VIEW_AGES[name])
                  and label != NEIGHBORS['Market']['TempleOfTime']):
                age = MARKET_VIEW_AGES[name]
                temple = REGION_VIEWS['TempleOfTime'][age]
                target = grouped.setdefault(temple, {'rooms': set(), 'points': set()})
                if label == NEIGHBORS['TempleOfTime']['Market']:
                    target['rooms'].add((REGION_NAMES['TempleOfTime'], *TEMPLE_BOUNDS[age]))
            target['points'].add((label, tuple(point)))
        for label, points in scene.get('routes', ()):
            if name == REGION_VIEWS['Graveyard']['Adult'] and label in DAMPE_ROUTES.values():
                underground = UNDERGROUND_VIEWS['Graveyard']['Adult']
                route_view = grouped.setdefault(underground, {'rooms': set(), 'points': set()})
            elif name == SHADOW_VIEWS[0] and label == SHADOW_SHIP_ROUTE:
                route_view = grouped.setdefault(SHADOW_VIEWS[3], {'rooms': set(), 'points': set()})
            else:
                route_view = view
            route_view.setdefault('routes', set()).add((label, tuple(map(tuple, points))))
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
