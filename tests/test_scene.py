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
