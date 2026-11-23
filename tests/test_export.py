import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

from map_oot_rando.export import main
from map_oot_rando.metadata import add_surface_entrances, bind_catalogue, event_check_rows, export_scan
from map_oot_rando.model import load_metadata, select


class ExportTests(unittest.TestCase):
    def setUp(self):
        self.groups = {'KokiriForest#123': [dict(
            resource='Banc/KokiriForest/Test', position=[1, 2, 3], label='KF_example')]}
        self.catalogue = dict(schema_version=1, seed_id='synthetic-seed', checks=[
            dict(id='123', name='Seed chest', category='chest', region='Kokiri Forest'),
            dict(id='ap#event', name='Event', category='npc', zone='KokiriForest'),
            dict(id='ap#other', name='Other', category='npc', zone='LostWood'),
        ])
        self.document = export_scan(self.groups, {}, provenance='synthetic')

    def test_join_preserves_seed_identity_and_search_alias(self):
        result = bind_catalogue(self.document, self.catalogue)
        self.assertEqual(result['seed_id'], 'synthetic-seed')
        chest, event = load_metadata(result)
        self.assertEqual((chest.id, chest.name, chest.position), ('123', 'Seed chest', (1, 2, 3)))
        self.assertEqual(select((chest, event), {}, 'KF_example'), (chest,))
        self.assertIsNone(event.project())
        self.assertEqual(len(result['diagnostics']), 1)

    def test_cli_creates_loadable_file_and_refuses_overwrite(self):
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp)
            checks = directory / 'checks.json'
            checks.write_text(json.dumps(self.catalogue), encoding='utf-8')
            output = directory / 'map.json'
            argv = ['export', '--ootrr', tmp, '--nup', 'test.nup',
                    '--checks', str(checks), '--output', str(output)]
            with (patch.object(sys, 'argv', argv), patch.object(sys, 'path', list(sys.path)),
                  patch('map_oot_rando.export.verify_checkout'),
                  patch('map_oot_rando.export.scan_game', return_value=self.document) as scan,
                  patch('sys.stdout'), patch('sys.stderr')):
                main()
                payload = output.read_bytes()
                self.assertEqual(len(load_metadata(json.loads(payload))), 2)
                with self.assertRaises(SystemExit):
                    main()
                scan.assert_called_once()
                self.assertEqual(output.read_bytes(), payload)

    def test_import_keeps_multiple_positions_of_one_check_in_one_resource(self):
        group = self.groups['KokiriForest#123']
        group.append(dict(group[0], position=[10, 20, 30]))
        group.append(dict(group[0]))
        scanned = export_scan(self.groups, {}, provenance='ootrr-scan')
        saved = json.loads(json.dumps(bind_catalogue(scanned, self.catalogue)))
        rows = load_metadata(saved)
        matches = select(rows, {'123': 'available'}, statuses={'available'})
        self.assertEqual([row.id for row in matches], ['123', '123'])
        self.assertEqual(len({row.resource for row in matches}), 1)
        self.assertEqual([row.project() for row in matches], [(1, 3), (10, 30)])

    def test_shared_check_has_one_id_and_two_separate_region_frames(self):
        ident = 'LostWood#456'
        groups = {ident: [
            dict(resource='Banc/KokiriForest/Child', position=[1, 2, 3]),
            dict(resource='Banc/LostWood/Child', position=[4, 5, 6]),
        ]}
        catalogue = dict(self.catalogue, checks=self.catalogue['checks'] + [
            dict(id=ident, name='Shared', category='chest', zone='LostWood')])
        document = export_scan(groups, {}, provenance='synthetic', regions=('KokiriForest', 'LostWood'))
        rows = load_metadata(bind_catalogue(document, catalogue))
        self.assertEqual([(row.region, row.project()) for row in rows if row.id == ident],
                         [('KokiriForest', (1, 3)), ('LostWood', (4, 6))])
        self.assertEqual(next(row.region for row in rows if row.id == 'ap#other'), 'LostWood')

    def test_lost_woods_event_match_rejects_ambiguous_npc_and_wrong_talk(self):
        child = 'Banc/LostWood/LostWood_Child_Static.bcett.byml.zs'
        adult = child.replace('_Child_', '_Adult_')
        npc = dict(Gyaml='Npc_SkullKid_Child', Translate=[1, 2, 3])
        wrong_scrub = dict(Gyaml='Enemy_Scrub_Business', Translate=[7, 8, 9],
                           Dynamic={'TalkEventName': 'Enemy_Scrub_Business_Refill'})
        maps = {child: {'root': {'Actors': [npc, wrong_scrub]}},
                adult: {'root': {'Actors': [npc, dict(npc, Translate=[4, 5, 6])]}}}
        self.assertEqual([(row['id'], row['resource']) for row in event_check_rows(maps, lambda *_: True)],
                         [('npc#LW Skull Kid', child)])

    def test_grotto_keeps_xyz_and_uses_only_matching_age_entrance(self):
        child = 'Banc/SacredForestMeadow/SacredForestMeadow_Child_Dynamic.bcett.byml.zs'
        adult = child.replace('_Child_', '_Adult_')
        ident = 'SacredForestMeadow#7995233962349162969'
        document = export_scan({ident: [dict(resource=child, position=[2, 3, 4]),
                                       dict(resource=adult, position=[2, 3, 4])]}, {},
                               provenance='synthetic', regions=('KokiriForest', 'SacredForestMeadow'))
        cover = dict(Hash=8456945034417122929, Gyaml='Land_Kokiri_HidingHoleCover_A_01', Translate=[6, 7, 8])
        maps = {child.replace('Dynamic', 'Static'): {'root': {'Actors': [cover]}},
                adult.replace('Dynamic', 'Static'): {'root': {'Actors': [dict(cover, Gyaml='Other')]}}}
        add_surface_entrances(document['locations'], maps)
        child_row, adult_row = load_metadata(json.loads(json.dumps(document)))
        self.assertEqual(child_row.position, (2, 3, 4))
        self.assertEqual(child_row.project(), (6, 8))
        self.assertEqual(adult_row.project(), (2, 4))

    def test_deku_theater_keeps_both_child_checks_at_one_entrance(self):
        child = 'Banc/LostWood/LostWood_Child_Static.bcett.byml.zs'
        adult = child.replace('_Child_', '_Adult_')
        elder = dict(Gyaml='Enemy_Scrub_ForestStage_Elder', Name='ScrubForestStageElder',
                     Translate=[4, 81, 6])
        entrance = dict(Gyaml='DestinationAnchor', Hash=4876738002315557989, Translate=[1, 100, 2])
        resource = {'root': {'Actors': [elder, entrance]}}
        maps = {child: resource, adult: resource}
        rows = event_check_rows(maps, lambda *_: True)
        add_surface_entrances(rows, maps)
        self.assertEqual({row['id'] for row in rows}, {'npc#Deku Theater Skull Mask',
                                                      'npc#Deku Theater Mask of Truth'})
        self.assertTrue(all(row['resource'] == child and row['entrance'] == (1, 100, 2) for row in rows))

    def test_legacy_world_id_requires_hash_field_and_eligible_variant(self):
        from map_oot_rando.metadata import world_check_rows
        actor = dict(Hash=123, Gyaml='Item', Dynamic={'Drop__DropActor': 'Drop'}, Translate=[1, 2, 3])
        maps = {
            'Banc/KokiriForest/Child': {'root': {'Actors': [actor]}},
            'Banc/KokiriForest/Adult': {'root': {'Actors': [actor]}},
            'Banc/LostWood/Staging': {'root': {'Actors': [actor]}},
        }
        checks = [dict(id=f'KokiriForest#123#{field}', name=field, category='item')
                  for field in ('Drop__DropActor', 'DoesNotExist')]
        result = world_check_rows(maps, checks, lambda path, actor: path.endswith('Adult'))
        self.assertEqual([(row['id'], row['resource'], row['position']) for row in result],
                         [('KokiriForest#123#Drop__DropActor', 'Banc/KokiriForest/Adult', [1, 2, 3])])

    def test_capture_catalogue_reports_only_candidate_paths(self):
        from map_oot_rando.export import map_capture_catalogue
        result = map_capture_catalogue({
            'Game/UI/MapMenuInfo.game__ui__MapMenuInfo.bgyml': object(),
            'UI/Texture/MiniMapTest.bntx': object(),
            'Banc/KokiriForest/Room': object(),
        })
        self.assertEqual(result, ['Game/UI/MapMenuInfo.game__ui__MapMenuInfo.bgyml',
                                  'UI/Texture/MiniMapTest.bntx'])
