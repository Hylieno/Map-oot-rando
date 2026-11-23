import json
import unittest

from map_oot_rando.scene import extract_scenes, read_scenes


class SceneTests(unittest.TestCase):
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
