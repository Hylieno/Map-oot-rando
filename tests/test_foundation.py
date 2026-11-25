import copy
import unittest
from map_oot_rando.metadata import export_scan
from map_oot_rando.model import load_metadata, select
from map_oot_rando.state import StateStore, tracker_states


class FoundationTests(unittest.TestCase):
    def setUp(self):
        self.gid = 'KokiriForest#rock#123'
        self.extra = {self.gid: {'source': 'rock', 'variants': [dict(
            resource='Banc/KokiriForest/Synthetic.bcett.byml.zs',
            label='KF_rock_1', position=[10, 20, -30])]}}
        self.document = export_scan({}, self.extra, provenance='synthetic')
        self.locations = load_metadata(self.document)

    def test_identity_and_projection(self):
        row = self.locations[0]
        self.assertEqual(row.id, self.gid)
        self.assertEqual(row.name, 'KF_rock_1')
        self.assertEqual(row.project(), (10, -30))
        self.assertEqual(row.position[1], 20)

    def test_invalid_metadata(self):
        for position in ([1, 2], [True, 2, 3], [float('nan'), 2, 3], [1, float('inf'), 3]):
            doc = copy.deepcopy(self.document)
            doc['locations'][0]['position'] = position
            with self.assertRaises(ValueError):
                load_metadata(doc)
        for field, value in [('schema_version', 2), ('upstream_revision', 'wrong'), ('provenance', 'guess')]:
            with self.assertRaises(ValueError):
                load_metadata(dict(self.document, **{field: value}))

    def test_missing_coordinates_and_separate_variants(self):
        variant = dict(self.extra[self.gid]['variants'][0], resource='Banc/KokiriForest/Interior', position=None)
        self.extra[self.gid]['variants'].append(variant)
        doc = export_scan({}, self.extra, provenance='synthetic')
        rows = load_metadata(doc)
        self.assertEqual(len(rows), 2)
        self.assertIsNone(rows[1].project())
        self.assertEqual(len(doc['diagnostics']), 1)
        self.assertEqual(select(rows, {}, resource=variant['resource']), (rows[1],))

    def test_identical_location_rows_collapse(self):
        self.document['locations'] *= 2
        self.assertEqual(load_metadata(self.document), self.locations)

    def test_search_filters(self):
        self.assertEqual(select(self.locations, {}, ' kf_ROCK_1 '), self.locations)
        self.assertEqual(select(self.locations, {}, '#123'), self.locations)
        self.assertEqual(select(self.locations, {}, categories={'pot'}), ())
        self.assertEqual(select(self.locations, {self.gid: 'completed'}, statuses={'available', 'unknown'}), ())

    def test_tracker_delegation(self):
        class Session:
            def check_state(self, ident):
                return dict(completed=ident == 'done', access=ident)
        self.assertEqual(tracker_states(Session(), ['done', 'available', 'blocked', 'unexpected']),
                         dict(done='completed', available='available', blocked='blocked', unexpected='unknown'))

    def test_sync_disconnect_reconnect_and_rollback(self):
        store = StateStore('seed', [self.gid])
        for status in ['available', 'completed', 'blocked']:
            store.publish('seed', {self.gid: status}, mode='save', timestamp=status)
            store.disconnect()
            self.assertEqual(store.states[self.gid], status)
            self.assertEqual(store.last_success, status)
            self.assertEqual(store.connection, 'disconnected')
        store.reset('new-seed', [self.gid])
        self.assertEqual(store.states[self.gid], 'unknown')
        self.assertIsNone(store.last_success)
        with self.assertRaises(ValueError):
            store.publish('seed', {self.gid: 'completed'}, mode='save', timestamp='now')

    def test_snapshot_validation_and_simulation_isolation(self):
        for simulated, mode in [(True, 'save'), (False, 'simulation')]:
            store = StateStore('seed', [self.gid], simulated=simulated)
            with self.assertRaises(ValueError):
                store.publish('seed', {self.gid: 'completed'}, mode=mode, timestamp='now')
            self.assertEqual(store.states[self.gid], 'unknown')
        store = StateStore('seed', [self.gid])
        for states in ({}, {self.gid: 'invented'}):
            with self.assertRaises(ValueError):
                store.publish('seed', states, mode='live', timestamp='now')


if __name__ == '__main__':
    unittest.main()
