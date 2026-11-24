import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

from map_oot_rando.export import main
from map_oot_rando.metadata import (add_dungeon_rooms, add_native_dungeon_floors, add_surface_entrances, bind_catalogue,
                                   event_check_rows, export_scan, placed_check_rows)
from map_oot_rando.model import load_metadata, select


class ExportTests(unittest.TestCase):
    def test_native_floor_overrides_the_room_only_for_unique_actor_matches(self):
        from map_oot_rando.scene import WATER_VIEWS, location_view

        region = 'WaterTemple'
        path = f'Banc/{region}/{region}_Static.bcett.byml.zs'
        document = export_scan({
            f'{region}#{suffix}': [dict(resource=path, position=(35, 120, -5))]
            for suffix in ('1#Drop__DropActor', '2', '3', 'gs#4')
        }, {}, provenance='ootrr-scan', regions=('KokiriForest', region))
        for row in document['locations']:
            row['dungeon_room'] = 17
        add_native_dungeon_floors(document['locations'], {region: {
            'MinFloor': -1,
            'Floor': [{'TBox': [{'InstanceID': 1}, {'InstanceID': 2}]},
                      {'CollectSign': [{'InstanceID': 4}]}, {'TBox': [{'InstanceID': 2}]}],
        }})
        rows = load_metadata(document)
        self.assertEqual([row.dungeon_floor for row in rows], [-1, None, None, 0])
        self.assertEqual([location_view(row) for row in rows],
                         [WATER_VIEWS[3], WATER_VIEWS[0], WATER_VIEWS[0], WATER_VIEWS[2]])
        self.assertEqual({row.position for row in rows}, {(35, 120, -5)})

    def test_gerudo_card_retains_multiple_award_sites_and_archery_retains_both_rewards(self):
        region = 'GerudoFortress'
        path = f'Banc/{region}/{region}_Adult_Static.bcett.byml.zs'
        maps = {path: {'root': {'Actors': [
            dict(Gyaml='Npc_Gerudo_008', Translate=(69, 115, 36)),
            dict(Gyaml='DestinationAnchor', Name='Dm_Gerudo_0023_LinkEndPosition',
                 Hash=2581536444609170668, Translate=(30, 102.5, -71.5)),
            dict(Gyaml='DestinationAnchor', Name='Dm_Gerudo_0023_LinkEndPosition',
                 Hash=15652772230412420096, Translate=(15, 110, -75.5)),
        ]}}}
        document = export_scan({}, {}, provenance='ootrr-scan', regions=('KokiriForest', region))
        document['locations'].extend(event_check_rows(maps, lambda *_: True))
        checks = [dict(id=ident, name=ident.split('#')[1], category='test', zone=region)
                  for ident in ('gerudo_card#Hideout Gerudo Membership Card',
                                'npc#GF HBA 1000 Points', 'npc#GF HBA 1500 Points')]
        rows = load_metadata(bind_catalogue(document, dict(self.catalogue, checks=checks)))
        self.assertEqual({r.position for r in rows if r.id == checks[0]['id']},
                         {(28.79, 102.5, -71.60), (15.83, 110, -76.06)})
        self.assertEqual([r.id for r in rows if r.position == (69, 115, 36)],
                         [check['id'] for check in checks[1:]])

    def test_market_bowling_uses_one_location_and_two_tracker_ids(self):
        path = 'Banc/Market/Market_Child_Static.bcett.byml.zs'
        anchor = dict(Gyaml='MapIconFacilityAnchor', Translate=(-25, 116, 8),
                      Dynamic={'MapIconFacilityIsOpen': 'Market_MiniGame_BombchuBowling_FirstTalk'})
        maps = {path: {'root': {'Actors': [anchor]}}}
        rows = event_check_rows(maps, lambda *_: True)
        self.assertEqual({row['id'] for row in rows},
                         {'npc#Market Bombchu Bowling First Prize', 'npc#Market Bombchu Bowling Second Prize'})
        self.assertEqual({row['position'] for row in rows}, {(-25, 116, 8)})

    def test_rolling_goron_uses_the_quest_actor_among_the_adult_models(self):
        from map_oot_rando.model import Location
        from map_oot_rando.scene import GORON_VIEWS, location_view

        path = 'Banc/GoronCity/GoronCity_Adult_Static.bcett.byml.zs'
        rolling = dict(Gyaml='Npc_Goron_DaruniaJr_Adult', Translate=(5.75, 109.9, -12.1),
                       Dynamic={'ActorDeleteSetGameDataBool': 'SageOfFire_Step01_DaruniaJr_BombHit'})
        scenes = {path: {'root': {'Actors': [
            rolling, dict(Gyaml=rolling['Gyaml'], Name='demo1', Translate=(-11.77, 114.92, 24.61)),
        ]}}}
        row, = event_check_rows(scenes, lambda *_: True)
        self.assertEqual(row['id'], 'npc#GC Rolling Goron as Adult')
        self.assertEqual(row['position'], rolling['Translate'])
        self.assertEqual(location_view(Location(**row)), GORON_VIEWS['Adult'][1])

    def test_crater_scrub_uses_the_child_event_actor(self):
        from map_oot_rando.scene import REGION_VIEWS, location_view

        region = 'DeathMountainCrater'
        child = f'Banc/{region}/{region}_Child_Static.bcett.byml.zs'
        adult = child.replace('_Child_', '_Adult_')
        scrub = dict(Gyaml='Enemy_Scrub_Business', Translate=(-23, 119.1, 33),
                     Dynamic={'TalkEventName': 'Enemy_Scrub_Business_Heart_02'})
        fairy = dict(Gyaml='MapIconFacilityAnchor', Translate=(5, 128, 24),
                     Dynamic={'MapIconFacilityIsOpen': 'HavePlayedEvent.Dm_FairyFountain_Wisdom'})
        maps = {path: {'root': {'Actors': [scrub, fairy]}} for path in (child, adult)}
        document = export_scan({}, {}, provenance='ootrr-scan', regions=('KokiriForest', region))
        document['locations'].extend(event_check_rows(maps, lambda path, _: path == adult))
        self.assertEqual([(row['id'], row['resource']) for row in document['locations']],
                         [('scrub#DMC Deku Scrub', child), ('fairy#DMC Great Fairy Reward', adult)])
        catalogue = dict(self.catalogue, checks=[
            dict(id='scrub#DMC Deku Scrub', name='Marchand Mojo', category='full_scrub', zone=region),
        ])
        row, = load_metadata(bind_catalogue(document, catalogue))
        self.assertEqual(row.position, scrub['Translate'])
        self.assertEqual(location_view(row), REGION_VIEWS[region]['Child'])

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

    def test_training_catalogue_alias_uses_native_position_and_retains_its_id(self):
        region = 'GerudoTrainingGround'
        path = f'Banc/{region}/{region}_Static.bcett.byml.zs'
        original = 'ap#Gerudo Training Ground Stalfos Chest'
        native = f'{region}#13501407288943710656'
        checks = [dict(id=ident, name=ident, category='chest', zone=region)
                  for ident in (original, native)]
        catalogue = dict(self.catalogue, checks=checks)
        placement = dict(id=native, name='GTG_room1_chest_1', category='chest', resource=path,
                         position=(-50.25, 98.13, -15.59), dungeon_room=1)
        doc = dict(self.document, locations=[placement], regions=['KokiriForest', region])
        rows = load_metadata(bind_catalogue(doc, catalogue))
        self.assertEqual([row.id for row in rows], [original, native])
        self.assertEqual([row.position for row in rows], [placement['position']] * 2)
        self.assertEqual(rows[0].dungeon_room, 1)

        doc['locations'].append(dict(placement, id=original, position=(-51, 98, -15)))
        rows = load_metadata(bind_catalogue(doc, catalogue))
        self.assertEqual(rows[0].position, (-51, 98, -15))
        doc['locations'].clear()
        rows = load_metadata(bind_catalogue(doc, catalogue))
        self.assertIsNone(rows[0].position)

    def test_jabu_native_room_overrides_height_and_survives_reload(self):
        from map_oot_rando.scene import JABU_VIEWS, location_view

        region = 'InsideJabuJabuBelly'
        path = f'Banc/{region}/{region}_Static.bcett.byml.zs'
        actors = [
            dict(Hash=11, Gyaml='Enemy_Skulltula_Gold', Translate=(-15, 90, -83),
                 Dynamic={'DefaultDungeonRoomIndex': 3}),
            dict(Hash=12, Gyaml='Obj_Pot_A_04', Translate=(34, 102, -126),
                 Dynamic={'DefaultDungeonRoomIndex': 15}),
        ]
        checks = [dict(id=f'{region}#gs#11', category='full_skulltula', name='Skulltula'),
                  dict(id=f'{region}#pots#12', category='full_pots', name='Pot')]
        maps = {path: {'root': {'Actors': actors}}}
        document = export_scan({}, {}, provenance='ootrr-scan', regions=('KokiriForest', region))
        document['locations'].extend(placed_check_rows(maps, checks, (), lambda *_: True))
        add_dungeon_rooms(document['locations'], maps)
        saved = bind_catalogue(document, dict(self.catalogue, checks=checks))
        rows = load_metadata(json.loads(json.dumps(saved)))
        self.assertEqual([row.dungeon_room for row in rows], [3, 15])
        self.assertEqual([location_view(row) for row in rows], [JABU_VIEWS[1], JABU_VIEWS[3]])

    def test_hash_fallback_checks_actor_type_and_keeps_scanner_result_in_all_regions(self):
        for region, suffix in (('FireTemple', ''), ('KokiriForest', '_Child')):
            with self.subTest(region=region):
                path = f'Banc/{region}/{region}{suffix}_Static.bcett.byml.zs'
                maps = {path: {'root': {'Actors': [
                    dict(Hash=1, Gyaml='Obj_Pot_A_03', Translate=[3, 145, 2]),
                    dict(Hash=2, Gyaml='Obj_Heart_Container', Translate=[0, 100, 0]),
                    dict(Hash=3, Gyaml='Obj_TBox_A_01_NoBake', Translate=[0, 102, 0]),
                ]}}}
                checks = [
                    dict(id=f'{region}#pots#1', category='full_pots', name='Pot'),
                    dict(id=f'{region}#free#2', category='full_freestanding', name='Heart'),
                    dict(id=f'{region}#3', category='full_chests', name='Chest'),
                ]
                existing = [dict(checks[2], resource=path, position=[2, 102, 4])]
                rows = list(placed_check_rows(maps, checks, existing, lambda *_: True))
                self.assertEqual(rows, [dict(checks[0], resource=path, position=[3, 145, 2])])

    def test_colossus_chest_uses_its_surface_anchor_in_both_ages(self):
        region = 'DesertColossus'
        position, entrance = (-129, 76, -36), (-115, 94, -27)
        maps, rows = {}, []
        for age, actor_hash in (('Child', 1089669422726566991), ('Adult', 6814744896634068027)):
            base = f'Banc/{region}/{region}_{age}'
            maps[f'{base}_Static.bcett.byml.zs'] = {'root': {'Actors': [
                dict(Hash=actor_hash, Gyaml='DestinationAnchor', Translate=entrance),
            ]}}
            rows.append(dict(id=f'{region}#1186167733408299582',
                             resource=f'{base}_Dynamic.bcett.byml.zs', position=position))
        add_surface_entrances(rows, maps)
        self.assertEqual([(r['position'], r['entrance']) for r in rows], [(position, entrance)] * 2)

    def test_gerudo_grottos_keep_two_distinct_access_points(self):
        maps, rows = {}, []
        for age, anchor in [('Child', 2898121583347267819), ('Adult', 15684957330767796996)]:
            path = f'Banc/GerudoValley/GerudoValley_{age}'
            maps[f'{path}_Static.bcett.byml.zs'] = {'root': {'Actors': [
                dict(Hash=anchor, Gyaml='DestinationAnchor', Translate=(11, 90, 36)),
                dict(Hash=12817575131469044248, Gyaml='Land_Gerudo_HidingHoleCover_A_02',
                     Translate=(-45, 101, -29)),
            ]}}
            rows.append(dict(id='GerudoValley#6463521162691873710',
                             resource=f'{path}_Dynamic.bcett.byml.zs', position=(31, -22, 37)))
        rows.append(dict(id='GerudoValley#pots#6896071498853277403', resource=rows[-1]['resource'],
                         position=(-48, 84, -46)))
        add_surface_entrances(rows, maps)
        self.assertEqual([r['entrance'] for r in rows], [(11, 90, 36), (11, 90, 36), (-45, 101, -29)])
        self.assertEqual([r['position'] for r in rows], [(31, -22, 37), (31, -22, 37), (-48, 84, -46)])

    def test_zora_grotto_keeps_exact_coordinates_with_age_specific_access(self):
        def path(age, layer):
            return f'Banc/ZoraRiver/ZoraRiver_{age}_{layer}.bcett.byml.zs'

        chest = dict(Hash=8838426083116998768, Gyaml='Obj_TBox_A_01', Translate=(-16, 75, 30))
        frogs = dict(Gyaml='OcarinaPoint_MiniGame_FrogTenors', Translate=(9, 102, -55))
        maps = {}
        entrances = {'Child': (15446115664186718191, (-15, 115, 15)),
                     'Adult': (17321193928923817093, (-16, 115, 15))}
        for age, (hash_id, point) in entrances.items():
            maps[path(age, 'Static')] = {'root': {'Actors': [
                dict(Hash=hash_id, Gyaml='DestinationAnchor', Translate=point),
                *([frogs] if age == 'Child' else []),
            ]}}
            maps[path(age, 'Dynamic')] = {'root': {'Actors': [chest]}}
        catalogue = dict(self.catalogue, checks=[
            dict(id=f"ZoraRiver#{chest['Hash']}", name='Chest', category='full_chests', zone='ZoraRiver'),
            dict(id='npc#ZR Frogs Ocarina Game', name='Frogs', category='full_npc', zone='ZoraRiver'),
        ])
        document = export_scan({}, {}, provenance='ootrr-scan', regions=('KokiriForest', 'ZoraRiver'))
        existing = [dict(catalogue['checks'][0], resource=path('Child', 'Dynamic'), position=chest['Translate'])]
        document['locations'].extend(existing)
        document['locations'].extend(placed_check_rows(maps, catalogue['checks'], existing, lambda *_: True))
        document['locations'].extend(event_check_rows(maps, lambda *_: True))
        add_surface_entrances(document['locations'], maps)
        child, adult, event = load_metadata(bind_catalogue(document, catalogue))
        self.assertEqual(child.position, adult.position)
        self.assertEqual((child.project(), adult.project()), ((-15, 15), (-16, 15)))
        self.assertEqual((event.position, event.resource), (frogs['Translate'], path('Child', 'Static')))

    def test_zora_domain_combines_adult_scenes_without_duplicate_placements(self):
        from map_oot_rando.scene import REGION_VIEWS, location_view

        ident = 'ZoraDomain#free#1056'
        path = 'Banc/ZoraDomain/ZoraDomain_Adult_{}.bcett.byml.zs'
        document = export_scan({}, {}, provenance='ootrr-scan', regions=('KokiriForest', 'ZoraDomain'))
        document['locations'] = [
            dict(id=ident, name='Rupee', category='full_freestanding', resource=path.format(layer), position=point)
            for layer, point in [('Dynamic', (12, 60, -16)), ('Alternative_Dynamic', (12.02, 60, -16)),
                                 ('Alternative_Dynamic', (30, 100, 0))]
        ]
        catalogue = dict(self.catalogue, checks=[dict(id=ident, name='Rupee', category='full_freestanding')])
        rows = load_metadata(bind_catalogue(document, catalogue))
        self.assertEqual([row.position for row in rows], [(12, 60, -16), (30, 100, 0)])
        self.assertTrue(all(location_view(row) == REGION_VIEWS['ZoraDomain']['Adult'] for row in rows))

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
