import json
import unittest

from map_oot_rando.scene import extract_scenes, read_scenes


class SceneTests(unittest.TestCase):
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
