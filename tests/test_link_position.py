import unittest

from map_oot_rando.link_position import LinkPosition, parse_position


class LinkPositionTests(unittest.TestCase):
    def test_live_position_requires_current_memory_sample(self):
        payload = dict(source='memory', connected=True, updatedAt=12_000,
                       scene='KokiriForest', age='child', mapId='principal',
                       position=dict(x=1.5, y=99.0, z=-2, yaw=90))
        self.assertEqual(parse_position(payload, 12.5),
                         LinkPosition('KokiriForest', 'Child', 'principal', 1.5, 99, -2, 90))
        self.assertIsNone(parse_position(payload, 18))
        self.assertIsNone(parse_position(dict(payload, source='save'), 12.5))
        self.assertIsNone(parse_position(dict(payload, connected=False), 12.5))
        self.assertIsNone(parse_position(dict(payload, position=dict(payload['position'], x=float('nan'))), 12.5))
