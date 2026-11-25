import json
import unittest

from map_oot_rando.scene import extract_scenes, read_scenes


class SceneTests(unittest.TestCase):
    def test_lost_woods_distinguishes_the_entrance_from_reset_paths(self):
        from map_oot_rando.scene import LOST_WOOD_RESET, NEIGHBORS

        path = 'Banc/LostWood/LostWood_Child_Static.bcett.byml.zs'
        actors = [
            dict(Gyaml='StartPos', Name='LostWood_Entrance', Translate=(0, 100, 5)),
            dict(Gyaml='FieldAndDungeonEntranceEventRequestActor', Name='LostWood_Entrance',
                 Translate=(0, 112, 7)),
            dict(Gyaml='FieldAndDungeonEntranceEventRequestActor', Translate=(0, 112, -9.5),
                 Dynamic={'FirstEventName': 'Dm_SY_BancChangeGo_LostWood',
                          'NextStartPosName': 'KokiriForest_FrontOfLostWood'}),
            dict(Gyaml='FieldAndDungeonEntranceEventRequestActor', Translate=(24, 110, -35.66),
                 Dynamic={'FirstEventName': 'Dm_SY_BancChangeGo',
                          'NextStartPosName': 'GoronCity_LostWoodSide_after'}),
        ]
        scene = extract_scenes({path: {'root': {'Actors': actors}}}, lambda _: {})[path]
        self.assertEqual(dict(scene['points']), {
            NEIGHBORS['LostWood']['KokiriForest']: (0, 7),
            'LostWood_Entrance': (0, 5),
            LOST_WOOD_RESET: (0, -9.5),
        })
    def test_training_routes_require_both_centers_and_the_native_door(self):
        from map_oot_rando.scene import (TRAINING_TO_STATUE, TRAINING_TO_WALKWAY, TRAINING_VIEWS,
                                        TRAINING_WALKWAY_GATE, group_scenes)

        path = 'Banc/GerudoTrainingGround/GerudoTrainingGround_Static.bcett.byml.zs'
        actors = [
            dict(Hash=3761826239942057234, Gyaml='DungeonRoomCenterAnchor', Translate=(-1.83, 99.25, -6.09)),
            dict(Hash=327131091130935122, Gyaml='DungeonRoomCenterAnchor', Translate=(-47.05, 97.75, -5.13)),
            dict(Hash=17271596773795074407, Gyaml='Obj_Gerudo_SwitchShutter_A_04', Translate=(-28.39, 98, -5.39)),
            dict(Hash=TRAINING_WALKWAY_GATE, Gyaml='Obj_Gerudo_SwitchShutter_A_04', Translate=(-2.34, 106, -58.92)),
        ]
        maps = {path: {'root': {'Actors': actors}}}
        document = {'scenes': extract_scenes(maps, lambda _: {})}
        scenes = group_scenes(read_scenes(json.loads(json.dumps(document))))
        self.assertEqual(scenes[TRAINING_VIEWS[0]]['routes'], [
            ('Liaisons entre les salles', ((-1.83, -6.09), (-28.39, -5.39), (-47.05, -5.13))),
        ])
        self.assertIn((TRAINING_TO_WALKWAY, (-2.34, -58.92)), scenes[TRAINING_VIEWS[0]]['points'])
        self.assertIn((TRAINING_TO_STATUE, (-2.34, -58.92)), scenes[TRAINING_VIEWS[1]]['points'])
        actors.append(dict(actors[2], Translate=(-30, 98, -5.39)))
        self.assertNotIn('routes', extract_scenes(maps, lambda _: {})[path])

    def test_water_temple_preserves_the_pool_and_its_submerged_rooms(self):
        from map_oot_rando.model import Location
        from map_oot_rando.scene import WATER_VIEWS, location_view

        region = 'WaterTemple'
        path = f'Banc/{region}/{region}_Static.bcett.byml.zs'
        for point, room, floor in (((-4.5, 118.6, 43.61), None, 0),
                                   ((-4.5, 124.36, -88.05), 23, 2),
                                   ((-4.5, 125, -88), None, 2),
                                   ((12, 92.71, -4.5), 2, 3),
                                   ((-54.54, 114.01, -59.25), 21, 1)):
            with self.subTest(point=point):
                row = Location('test', 'Check', 'test', path, point, region=region, dungeon_room=room)
                self.assertEqual(location_view(row), WATER_VIEWS[floor])

    def test_water_temple_arrival_at_lake_uses_the_shared_field_scene(self):
        from map_oot_rando.scene import REGION_VIEWS, WATER_VIEWS, group_scenes

        field = 'Banc/HyruleField/HyruleField_Adult_Dynamic.bcett.byml.zs'
        water = 'Banc/WaterTemple/WaterTemple_Dynamic.bcett.byml.zs'
        maps = {
            field: {'root': {'Actors': [
                dict(Gyaml='StartPos', Name='OutsideOfWaterTemple', Translate=(-183.1, 103.5, 496.2)),
            ]}},
            water: {'root': {'Actors': [
                dict(Gyaml='StartPos', Name='WaterTemple_FromLakeHylia', Translate=(-4.5, 118.6, 43.61)),
            ]}},
        }
        scenes = group_scenes(extract_scenes(maps, lambda _: {}))
        self.assertEqual(scenes[REGION_VIEWS['LakeHylia']['Adult']]['points'],
                         [('OutsideOfWaterTemple', (-183.1, 496.2))])
        self.assertEqual(scenes[REGION_VIEWS['HyruleField']['Adult']]['points'], [])
        self.assertEqual(scenes[WATER_VIEWS[0]]['points'], [('WaterTemple_FromLakeHylia', (-4.5, 43.61))])

    def test_spirit_temple_separates_the_statue_balcony_from_the_lower_room(self):
        from map_oot_rando.model import Location
        from map_oot_rando.scene import SPIRIT_VIEWS, location_view

        path = 'Banc/SpiritTemple/SpiritTemple_Static.bcett.byml.zs'
        for point, floor in (((0, 114.15, -57.58), 1), ((-23.09, 129.67, -66.68), 2)):
            with self.subTest(point=point):
                row = Location('test', 'Check', 'test', path, point, region='SpiritTemple', dungeon_room=7)
                self.assertEqual(location_view(row), SPIRIT_VIEWS[floor])

    def test_jabu_lift_connects_the_basement_and_upper_floor(self):
        from map_oot_rando.scene import JABU_VIEWS, SIDE_PORTALS, group_scenes

        region = 'InsideJabuJabuBelly'
        path = f'Banc/{region}/{region}_Static.bcett.byml.zs'
        actors = [
            dict(Gyaml='Obj_InsideJabu_Jabu_ElevatorLift_A_02', Hash=5914032013565537495,
                 Translate=(-32.36, 81.75, -93.31)),
            dict(Gyaml='Obj_InsideJabu_Jabu_ElevatorLift_A_01', Hash=5186749243682591245,
                 Translate=(-32.36, 83, -93.31)),
        ]
        scenes = extract_scenes({path: {'root': {'Actors': actors}}}, lambda _: {})
        grouped = group_scenes(read_scenes({'scenes': scenes}))
        lower = 'Ascenseur d’Octo · vers l’étage'
        upper = 'Ascenseur d’Octo · voir le sous-sol'
        self.assertEqual(dict(grouped[JABU_VIEWS[1]]['points']), {lower: (-32.36, -93.31)})
        self.assertEqual(dict(grouped[JABU_VIEWS[2]]['points']), {upper: (-32.36, -93.31)})
        self.assertEqual(SIDE_PORTALS[region][lower][1:], (JABU_VIEWS[2], lower, upper))

    def test_deku_webs_connect_separate_levels_without_mixing_the_two_drops(self):
        from map_oot_rando.scene import DEKU_VIEWS, group_scenes

        path = 'Banc/InsideTheDekuTree/InsideTheDekuTree_Static.bcett.byml.zs'
        actors = [
            dict(Gyaml='Obj_InsideTheDekuTree_SpiderWeb_A_01', Hash=278772661473487189, Translate=(0, 100, 0)),
            dict(Gyaml='Obj_InsideTheDekuTree_SpiderWeb_A_01', Hash=9217804728253310381, Translate=(-29, 80, 0)),
        ]
        scenes = extract_scenes({path: {'root': {'Actors': actors}}}, lambda _: {})
        grouped = group_scenes(read_scenes({'scenes': scenes}))
        self.assertEqual(dict(grouped[DEKU_VIEWS[0]]['points']), {'Toile du hall · vers le sous-sol': (0, 0)})
        self.assertEqual(dict(grouped[DEKU_VIEWS[3]]['points']),
                         {'Sous la toile · voir le hall': (0, 0),
                          'Seconde toile · vers le sous-sol profond': (-29, 0)})
        self.assertEqual(dict(grouped[DEKU_VIEWS[4]]['points']), {'Seconde toile · voir le sous-sol': (-29, 0)})

    def test_fire_hammer_pillar_has_its_own_anchor_on_each_floor(self):
        from map_oot_rando.scene import FIRE_VIEWS, SIDE_PORTALS, group_scenes

        path = 'Banc/FireTemple/FireTemple_Static.bcett.byml.zs'
        actors = [
            dict(Gyaml='Obj_FireTemple_HammerDropPillar_A_01', Hash=8177655486739024991,
                 Translate=(-25.46, 145.95, 0.03)),
            dict(Gyaml='Obj_FireTemple_HammerDropPillar_A_01', Hash=6957196851887297580,
                 Translate=(-25.48, 105.19, 0.03)),
        ]
        scenes = extract_scenes({path: {'root': {'Actors': actors}}}, lambda _: {})
        grouped = group_scenes(read_scenes({'scenes': scenes}))
        down = 'Pilier du marteau · vers le rez-de-chaussée'
        up = 'Pilier du marteau · voir le 2e étage'
        self.assertEqual(dict(grouped[FIRE_VIEWS[2]]['points']), {down: (-25.46, 0.03)})
        self.assertEqual(dict(grouped[FIRE_VIEWS[0]]['points']), {up: (-25.48, 0.03)})
        self.assertEqual(SIDE_PORTALS['FireTemple'][down][1:], (FIRE_VIEWS[0], down, up))

    def test_forest_main_elevator_connects_the_hall_and_deep_basement(self):
        from map_oot_rando.scene import FOREST_VIEWS, SIDE_PORTALS, group_scenes

        path = 'Banc/ForestTemple/ForestTemple_Static.bcett.byml.zs'
        actors = [
            dict(Gyaml='Obj_ForestTemple_Elevator_A_01', Hash=9015988562326766070,
                 Translate=(0, 100, -3.5)),
            dict(Gyaml='Obj_WarpPoint_A_01', Hash=7322827475260825437, Translate=(0, 75, -62)),
        ]
        scenes = extract_scenes({path: {'root': {'Actors': actors}}}, lambda _: {})
        grouped = group_scenes(read_scenes({'scenes': scenes}))
        self.assertEqual(dict(grouped[FOREST_VIEWS[0]]['points'])['Ascenseur du hall'], (0, -3.5))
        self.assertEqual(dict(grouped[FOREST_VIEWS[4]]['points'])['Ascenseur vers le hall'], (0, -3.5))
        self.assertEqual(SIDE_PORTALS['ForestTemple']['Ascenseur du hall'][1], FOREST_VIEWS[4])
        self.assertEqual(set(dict(grouped[FOREST_VIEWS[5]]['points'])),
                         {'Retour après Ganon spectral', 'Sages · Ganon spectral'})

    def test_water_tablets_use_the_floor_where_they_can_be_reached(self):
        from map_oot_rando.scene import WATER_VIEWS, group_scenes

        path = 'Banc/WaterTemple/WaterTemple_Static.bcett.byml.zs'
        positions = [(39.9, 121.05, -4.5), (-26, 124.415, 5), (-7.567, 107.55, -4.5)]
        actors = [dict(Gyaml=f'Obj_WaterTemple_StoneTablet_A_0{number}', Translate=point)
                  for number, point in enumerate(positions, start=1)]
        scenes = extract_scenes({path: {'root': {'Actors': actors}}}, lambda _: {})
        grouped = group_scenes(read_scenes({'scenes': scenes}))
        self.assertEqual(dict(grouped[WATER_VIEWS[0]]['points']), {
            'Tablette · niveau bas': (39.9, -4.5),
            'Tablette · niveau haut': (-26, 5),
        })
        self.assertEqual(dict(grouped[WATER_VIEWS[1]]['points']), {
            'Tablette · niveau intermédiaire': (-7.567, -4.5),
        })

    def test_shadow_ship_uses_its_own_rail_on_the_fourth_basement(self):
        from map_oot_rando.scene import SHADOW_SHIP_ROUTE, SHADOW_VIEWS, group_scenes

        path = 'Banc/ShadowTemple/ShadowTemple_Static.bcett.byml.zs'
        ship = dict(Gyaml='Obj_ShadowTemple_PaddleShip_A_01', Rails=[dict(Dst=1)])
        rail = dict(Name='Guide', Gyaml='Guide', Hash=1, Points=[
            dict(Translate=(136, 39, -62)), dict(Translate=(-135, 39, -62)),
        ])
        unrelated = dict(rail, Hash=2, Points=list(reversed(rail['Points'])))
        scenes = extract_scenes({path: {'root': {'Actors': [ship], 'Rails': [rail, unrelated]}}}, lambda _: {})
        grouped = group_scenes(read_scenes({'scenes': scenes}))
        self.assertNotIn('routes', grouped[SHADOW_VIEWS[0]])
        (label, points), = grouped[SHADOW_VIEWS[3]]['routes']
        self.assertEqual((label, points[0], points[-1]), (SHADOW_SHIP_ROUTE, (136, -62), (-135, -62)))

    def test_wasteland_route_keeps_native_curve_and_deduplicates_scene_layers(self):
        from map_oot_rando.scene import GUIDE_ROUTE, REGION_VIEWS, group_scenes

        region = 'HountedWasteland'
        path = f'Banc/{region}/{region}_Adult_Static.bcett.byml.zs'
        guide = dict(Name='Guide', Gyaml='Guide', IsClosed=False, Points=[
            dict(Translate=(0, 100, 0), Control1=(0, 110, -8)),
            dict(Translate=(12, 100, 0), Control0=(12, 110, -8)),
        ])
        maps = {path: {'root': {'Rails': [guide]}},
                path.replace('_Static', '_Dynamic'): {'root': {'Actors': []}}}
        document = {'scenes': extract_scenes(maps, lambda _: {})}
        grouped = group_scenes(read_scenes(json.loads(json.dumps(document))))
        (name, route), = grouped[REGION_VIEWS[region]['Adult']]['routes']
        self.assertEqual(name, GUIDE_ROUTE)
        self.assertEqual((route[0], route[6], route[-1]), ((0, 0), (6, -6), (12, 0)))

    def test_gerudo_training_ground_preserves_the_walkway_above_the_maze(self):
        from map_oot_rando.model import Location
        from map_oot_rando.scene import TRAINING_TO_CEILING, TRAINING_TO_MAZE, TRAINING_VIEWS, group_scenes, location_view

        region = 'GerudoTrainingGround'
        path = f'Banc/{region}/{region}_Static.bcett.byml.zs'
        actors = [
            dict(Gyaml='DungeonRoomCenterAnchor', Hash=13588342684847587321, Translate=(-1.42, 98.01, -47.96)),
            dict(Gyaml='DungeonRoomIdAnchor', Hash=11618577540114259236, Translate=(-2.36, 106.24, -55.67)),
            dict(Gyaml='DungeonRoomArea', Hash=18344474415563430437, Translate=(-7.76, 102.77, -35.45)),
            dict(Gyaml='Obj_ScarecrowMarker_B_00', Hash=6572899987226388103, Translate=(1.5, 105.97, -63.14)),
        ]
        raw = extract_scenes({path: {'root': {'Actors': actors}}}, lambda _: {})
        grouped = group_scenes(read_scenes(json.loads(json.dumps({'scenes': raw}))))
        self.assertEqual(dict(grouped[TRAINING_VIEWS[0]]['points']), {
            'Labyrinthe': (-1.42, -47.96), TRAINING_TO_CEILING: (-7.76, -35.45),
        })
        self.assertEqual(dict(grouped[TRAINING_VIEWS[1]]['points']), {
            'Passerelle nord': (-2.36, -55.67), TRAINING_TO_MAZE: (-7.76, -35.45), 'Épouvantail': (1.5, -63.14),
        })
        for height, floor in ((98.03, 0), (105, 1)):
            with self.subTest(height=height):
                row = Location('test', 'Chest', 'test', path, (-1.5, height, -48), region=region, dungeon_room=8)
                self.assertEqual(location_view(row), TRAINING_VIEWS[floor])

    def test_legacy_ganon_trials_restore_only_matching_stock_geometry(self):
        from map_oot_rando.scene import GANON_TRIAL_ROOM_CENTER, GANON_TRIAL_VIEWS, group_scenes

        path = 'Banc/InsideGanonCastle/InsideGanonCastle_Static.bcett.byml.zs'
        points = [
            ('Entrée · Feu', (-16.136, -49.862)), ('Épreuve · Feu', (-40.047, -78.928)),
            ('Entrée · Eau', (33.032, -21.001)), ('Épreuve · Eau', (70, -26.799)),
        ]
        saved = {'rooms': [], 'points': points}
        fire, water = GANON_TRIAL_VIEWS[3], GANON_TRIAL_VIEWS[1]
        grouped = group_scenes(read_scenes({'scenes': {path: saved}}))
        self.assertEqual({xy for label, xy in grouped[fire]['points'] if label == GANON_TRIAL_ROOM_CENTER},
                         {(-30.464, -73.805), (-52.592, -103.921)})
        self.assertEqual(len(grouped[fire]['routes']), 2)
        self.assertNotIn('routes', grouped[water])
        self.assertNotIn('routes', saved)

        internal = ((-30.464, -73.805), (-49.4931, -98.6521), (-52.592, -103.921))
        intermediate = dict(saved, routes=[('Épreuve · Feu', internal)])
        grouped = group_scenes(read_scenes({'scenes': {path: intermediate}}))
        self.assertEqual({xy for _, xy in grouped[fire]['routes']},
                         {internal, ((-16.136, -49.862), (-30.464, -73.805))})
        moved_door = (internal[0], (-48, -98.6521), internal[2])
        customized = dict(saved, routes=[('Épreuve · Feu', moved_door)])
        grouped = group_scenes(read_scenes({'scenes': {path: customized}}))
        self.assertEqual([xy for _, xy in grouped[fire]['routes']], [moved_door])

    def test_early_ganon_maps_require_all_barriers_to_restore_the_six_entrances(self):
        from map_oot_rando.scene import (GANON_DUNGEON_VIEWS, GANON_TRIAL_LEVELS, GANON_TRIAL_REFERENCE_BARRIERS,
                                        GANON_TRIAL_VIEWS, group_scenes)

        path = 'Banc/InsideGanonCastle/InsideGanonCastle_Static.bcett.byml.zs'
        barriers = list(zip(GANON_TRIAL_LEVELS, GANON_TRIAL_REFERENCE_BARRIERS))
        saved = {'rooms': [], 'points': [('Barrière de la tour', (0, -21.02)), *barriers]}
        grouped = group_scenes(read_scenes({'scenes': {path: saved}}))
        hall = grouped[GANON_DUNGEON_VIEWS[0]]
        self.assertEqual(sum(label.startswith('Entrée · ') for label, _ in hall['points']), 6)
        self.assertEqual(sum(len(grouped[view]['routes']) for view in GANON_TRIAL_VIEWS), 17)

        incomplete = dict(saved, points=saved['points'][:-1])
        grouped = group_scenes(read_scenes({'scenes': {path: incomplete}}))
        self.assertFalse(any(label.startswith('Entrée · ') for label, _ in grouped[GANON_DUNGEON_VIEWS[0]]['points']))

    def test_ganon_trial_tracking_switches_at_the_six_angled_doors(self):
        from map_oot_rando.scene import GANON_DUNGEON_VIEWS, GANON_TRIAL_VIEWS, ganon_trial_view

        door_steps = (
            ((16.45, 104, 7.25), (17.4, 104, 7.45)),
            ((32.5, 100, -21), (33.6, 100, -21)),
            ((16.45, 104, -49.25), (17.4, 104, -49.45)),
            ((-16.45, 104, -49.25), (-17.4, 104, -49.45)),
            ((-32.5, 100, -21), (-33.6, 100, -21)),
            ((-16.45, 104, 7.25), (-17.4, 104, 7.45)),
        )
        for view, (hall_side, trial_side) in zip(GANON_TRIAL_VIEWS, door_steps):
            with self.subTest(view=view):
                self.assertEqual(ganon_trial_view(hall_side), GANON_DUNGEON_VIEWS[0])
                self.assertEqual(ganon_trial_view(trial_side), view)
        self.assertEqual(ganon_trial_view((0, 104, 30)), GANON_DUNGEON_VIEWS[0])

    def test_ganon_tower_preserves_separate_landmarks_at_the_same_xz(self):
        from map_oot_rando.scene import GANON_DUNGEON_VIEWS, group_scenes

        path = 'Banc/InsideGanonCastle/InsideGanonCastle_Static.bcett.byml.zs'
        actors = [
            dict(Gyaml='Land_InsideGanonCastle_Room20_A_01', Translate=(0, 136.25, -24.65)),
            dict(Gyaml='Land_InsideGanonCastle_Room24_A_01', Translate=(0, 149.65, -24.65)),
            dict(Gyaml='Obj_GanonCastle_Barrier_A_01', Hash=7855099293663223240, Translate=(0, 97.25, -21.02)),
            dict(Gyaml='DungeonRoomArea', Hash=4106367990015143384, Translate=(0.03, 129.41, -25.42)),
            dict(Gyaml='DungeonRoomArea', Hash=8255735152900358871, Translate=(0.05, 156.22, -6.29)),
            dict(Gyaml='StartPos', Hash=11474052871889909221, Translate=(0.02, 171.05, -11.31)),
            dict(Gyaml='EventRequestActor', Translate=(-40, 141, -79),
                 Dynamic={'RequestEventName': 'InsideGanonCastle_Dungeon_BarrierRemove_Fire'}),
        ]
        raw = extract_scenes({path: {'root': {'Actors': actors}}}, lambda _: {})
        grouped = group_scenes(read_scenes(json.loads(json.dumps({'scenes': raw}))))
        self.assertEqual(dict(grouped[GANON_DUNGEON_VIEWS[0]]['points']), {
            'Épreuve · Feu': (-40, -79), 'Barrière de la tour': (0, -21.02),
        })
        self.assertEqual(dict(grouped[GANON_DUNGEON_VIEWS[1]]['points']),
                         {'Retour vers les épreuves': (0.03, -25.42)})
        self.assertEqual(grouped[GANON_DUNGEON_VIEWS[2]]['points'], [('Salle du premier étage', (0, -24.65))])
        self.assertEqual(dict(grouped[GANON_DUNGEON_VIEWS[4]]['points']), {
            'Salle du troisième étage': (0, -24.65), 'Escalier vers Ganondorf': (0.05, -6.29),
        })
        self.assertEqual(dict(grouped[GANON_DUNGEON_VIEWS[5]]['points']),
                         {'Voir l’accès à la salle de Ganondorf': (0.02, -11.31)})

    def test_shadow_temple_keeps_raised_targets_on_their_room_floor(self):
        from map_oot_rando.model import Location
        from map_oot_rando.scene import SHADOW_VIEWS, location_view

        region = 'ShadowTemple'
        path = f'Banc/{region}/{region}_Static.bcett.byml.zs'
        for room, point, floor in (
            (7, (84.1, 87.3, 22.9), 1),
            (11, (33.4, 73.8, 86.2), 2),
            (17, (104.6, 52, -39.8), 3),
            (24, (-138.3, -11.5, 26), 4),
        ):
            with self.subTest(room=room):
                row = Location('test', 'Check', 'test', path, point, region=region, dungeon_room=room)
                self.assertEqual(location_view(row), SHADOW_VIEWS[floor])

    def test_well_places_the_illusory_floor_and_landing_on_distinct_views(self):
        from map_oot_rando.scene import WELL_VIEWS, group_scenes

        path = 'Banc/BottomOfTheWell/BottomOfTheWell_Static.bcett.byml.zs'
        actors = [
            dict(Gyaml='Obj_Well_GlassTruth_A_30', Hash=4334615211939361328,
                 Translate=(-0.01, 102.17, -97.56)),
            dict(Gyaml='StartPos', Hash=2376828317386419701, Translate=(3.61, 92.37, -97.19)),
        ]
        scenes = extract_scenes({path: {'root': {'Actors': actors}}}, lambda _: {})
        grouped = group_scenes(read_scenes({'scenes': scenes}))
        self.assertEqual(dict(grouped[WELL_VIEWS[0]]['points']),
                         {'Sol illusoire · vers la salle du Poigneur': (-0.01, -97.56)})
        self.assertEqual(dict(grouped[WELL_VIEWS[1]]['points']),
                         {'Voir le sol illusoire au-dessus': (3.61, -97.19)})

    def test_well_uses_the_native_room_before_the_height_cutoff(self):
        from map_oot_rando.model import Location
        from map_oot_rando.scene import WELL_VIEWS, location_view

        region = 'BottomOfTheWell'
        path = f'Banc/{region}/{region}_Static.bcett.byml.zs'
        for room, height, floor in ((1, 96.2, 0), (8, 98, 1), (9, 87, 1), (None, 92, 1)):
            with self.subTest(room=room, height=height):
                row = Location('test', 'Check', 'test', path, (0, height, 0), region=region, dungeon_room=room)
                self.assertEqual(location_view(row), WELL_VIEWS[floor])

    def test_forest_temple_distinguishes_raised_checks_from_their_rooms(self):
        from map_oot_rando.model import Location
        from map_oot_rando.scene import FOREST_VIEWS, location_view

        region = 'ForestTemple'
        path = f'Banc/{region}/{region}_Static.bcett.byml.zs'
        for room, point, floor in (
            (0, (11.28, 119.84, 64), 1),
            (14, (44.27, 112.07, -38.24), 0),
            (27, (-3.43, 65.6, 17.17), 4),
            (29, (-3.24, 74.73, -64.43), 5),
            (None, (-49.46, 129.5, -63.71), 2),
        ):
            with self.subTest(room=room, point=point):
                row = Location('test', 'Check', 'test', path, point, region=region, dungeon_room=room)
                self.assertEqual(location_view(row), FOREST_VIEWS[floor])

    def test_deku_uses_room_for_checks_and_height_for_open_entrance_hall(self):
        from map_oot_rando.model import Location
        from map_oot_rando.scene import DEKU_VIEWS, location_view

        region = 'InsideTheDekuTree'
        path = f'Banc/{region}/{region}_Static.bcett.byml.zs'
        for room, point, floor in (
            (0, (6.5, 108.4, 7.25), 1),
            (0, (-4.18, 121.38, -12.36), 2),
            (2, (-42.92, 116.2, 19.35), 1),
            (10, (5.76, 47.06, 82.97), 5),
        ):
            with self.subTest(room=room, point=point):
                row = Location('test', 'Check', 'test', path, point, region=region, dungeon_room=room)
                self.assertEqual(location_view(row), DEKU_VIEWS[floor])

    def test_combine_layers_only_for_the_same_age_and_project_landmarks(self):
        adult = 'Banc/KokiriForest/KokiriForest_Adult_Dynamic.bcett.byml.zs'
        static = adult.replace('_Dynamic', '_Static')
        child = adult.replace('_Adult', '_Child')
        other = adult.replace('/KokiriForest/', '/LostWood/')
        labels = {adult: 'adult', static: 'static', child: 'child', other: 'other'}
        maps = {path: {'label': label, 'root': {'Actors': []}} for path, label in labels.items()}
        maps[static]['root']['Actors'] = [
            {'Gyaml': 'StartPos', 'Name': 'KokiriForest_FrontOfLostWood', 'Translate': [-32, 121, -66]},
            {'Gyaml': 'Obj_Kokiri_Bed_A_01', 'Translate': [-48, 118, 15]},
        ]
        room = ('house', [1, 80, 2], [8, 90, 12])

        def landmarks(resources):
            return {'KokiriForest': {'rooms': [room] if static in resources else [],
                                     'points': [(value['label'], [10, 99, 20])
                                                for value in resources.values()]}}

        scenes = read_scenes(json.loads(json.dumps({'scenes': extract_scenes(maps, landmarks)})))
        self.assertEqual(scenes[adult]['rooms'], [['house', [1, 2], [8, 12]]])
        self.assertEqual(scenes[adult]['points'], [
            ['KokiriForest_FrontOfLostWood', [-32, -66]], ['adult', [10, 20]], ['static', [10, 20]],
        ])
        self.assertEqual(scenes[child]['points'], [['child', [10, 20]]])
        self.assertNotIn(other, scenes)
        self.assertEqual(read_scenes({}), {})

    def test_child_uses_adult_house_names_only_when_entrances_align(self):
        from map_oot_rando.scene import AGE_VIEWS, SHARED_ENTRANCES, field_atlas_scene

        child, adult = AGE_VIEWS['Child'], AGE_VIEWS['Adult']
        entrances = list(zip(SHARED_ENTRANCES, [(82, -20), (-120, -30), (-30, -60)]))
        adult_scene = dict(points=entrances, rooms=[('links_house', (-46, 13), (-42, 17))])
        child_scene = dict(points=entrances.copy(), rooms=[('sarias_house', (-46, 13), (-42, 17))])
        scenes = {child: child_scene, adult: adult_scene}
        self.assertIs(field_atlas_scene(scenes, child), adult_scene)
        self.assertIs(field_atlas_scene(scenes, adult), adult_scene)
        child_scene['points'][0] = (SHARED_ENTRANCES[0], (82, -22))
        self.assertIs(field_atlas_scene(scenes, child), child_scene)
        child_scene['points'].pop()
        self.assertIs(field_atlas_scene(scenes, child), child_scene)
