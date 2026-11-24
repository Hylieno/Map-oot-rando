import json
import unittest

from map_oot_rando.scene import extract_scenes, read_scenes


class SceneTests(unittest.TestCase):
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
        from map_oot_rando.scene import TRAINING_VIEWS, group_scenes, location_view

        region = 'GerudoTrainingGround'
        path = f'Banc/{region}/{region}_Static.bcett.byml.zs'
        actors = [
            dict(Gyaml='DungeonRoomCenterAnchor', Hash=13588342684847587321, Translate=(-1.42, 98.01, -47.96)),
            dict(Gyaml='DungeonRoomIdAnchor', Hash=11618577540114259236, Translate=(-2.36, 106.24, -55.67)),
        ]
        raw = extract_scenes({path: {'root': {'Actors': actors}}}, lambda _: {})
        grouped = group_scenes(read_scenes(json.loads(json.dumps({'scenes': raw}))))
        self.assertEqual(grouped[TRAINING_VIEWS[0]]['points'], [('Labyrinthe', (-1.42, -47.96))])
        self.assertEqual(grouped[TRAINING_VIEWS[1]]['points'], [('Passerelle nord', (-2.36, -55.67))])
        for height, floor in ((98.03, 0), (105, 1)):
            with self.subTest(height=height):
                row = Location('test', 'Chest', 'test', path, (-1.5, height, -48), region=region, dungeon_room=8)
                self.assertEqual(location_view(row), TRAINING_VIEWS[floor])

    def test_ganon_tower_preserves_separate_landmarks_at_the_same_xz(self):
        from map_oot_rando.scene import GANON_DUNGEON_VIEWS, group_scenes

        path = 'Banc/InsideGanonCastle/InsideGanonCastle_Static.bcett.byml.zs'
        actors = [
            dict(Gyaml='Land_InsideGanonCastle_Room20_A_01', Translate=(0, 136.25, -24.65)),
            dict(Gyaml='Land_InsideGanonCastle_Room24_A_01', Translate=(0, 149.65, -24.65)),
            dict(Gyaml='EventRequestActor', Translate=(-40, 141, -79),
                 Dynamic={'RequestEventName': 'InsideGanonCastle_Dungeon_BarrierRemove_Fire'}),
        ]
        raw = extract_scenes({path: {'root': {'Actors': actors}}}, lambda _: {})
        grouped = group_scenes(read_scenes(json.loads(json.dumps({'scenes': raw}))))
        self.assertEqual(grouped[GANON_DUNGEON_VIEWS[0]]['points'], [('Épreuve · Feu', (-40, -79))])
        self.assertEqual(grouped[GANON_DUNGEON_VIEWS[2]]['points'], [('Salle du premier étage', (0, -24.65))])
        self.assertEqual(grouped[GANON_DUNGEON_VIEWS[4]]['points'], [('Salle du troisième étage', (0, -24.65))])

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
        maps = {adult: 'adult', static: 'static', child: 'child', other: 'other'}
        room = ('house', [1, 80, 2], [8, 90, 12])

        def landmarks(resources):
            return {'KokiriForest': {'rooms': [room] if static in resources else [],
                                     'points': [(value, [10, 99, 20])
                                                for value in resources.values()]}}

        scenes = read_scenes(json.loads(json.dumps({'scenes': extract_scenes(maps, landmarks)})))
        self.assertEqual(scenes[adult]['rooms'], [['house', [1, 2], [8, 12]]])
        self.assertEqual(scenes[adult]['points'], [['adult', [10, 20]], ['static', [10, 20]]])
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
