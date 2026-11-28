"""Round-trip the prototype's two trigger hooks through the actual game formats."""
from hashlib import sha256
from importlib.util import find_spec
from io import BytesIO
import json
from pathlib import Path
import struct
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import Mock, patch
import zlib

from map_oot_rando.trigger_seed import (
    SEED_BACKUP, add_event_triggers, prepare_seed, prepare_seed_in_place,
    prepare_skulltula_resources, prepare_trigger_resources, trigger_flag_name,
)


def ainb_node(index, node_type, children=()):
    return {'Node Type': node_type, 'Node Index': index, 'Name': '',
            'GUID': f'00000000-0000-0000-0000-{index:012d}', 'Flags': [], 'Queries': [], 'Attachments': [],
            'Properties': {}, 'Parameters': {'Inputs': {}, 'Outputs': {}}, 'XLink Actions': [],
            'Plugs': {'Child': [{'Node Index': i, 'Name': ''} for i in children]} if children else {}}


@unittest.skipUnless(find_spec('oot_rando') and find_spec('evfl') and find_spec('ainb'),
                     'Pinned OotrR and binary format readers are required')
class TriggerSeedTests(unittest.TestCase):
    def test_fairy_reward_keeps_ootrr_song_display_and_collection(self):
        from evfl.container import Container
        from evfl.entry_point import EntryPoint
        from evfl.event import Event, SubFlowEvent
        from evfl.evfl import EventFlow
        from evfl.flowchart import Flowchart
        from evfl.util import make_index
        from oot_rando.formats.evfl_tools import parse_flow
        from oot_rando.patching.event_patch import add_collection_markers
        from oot_rando.patching.progressive import add_converter_calls
        from oot_rando.patching.song_adapter import patch_flow

        ident = 'fairy#ZF Great Fairy Reward'
        native_flag = 'RandoCheck.a94180032dd00924.' + ident
        trigger_flag = trigger_flag_name(ident)
        actor = 'Item_Melody_WaterSerenade'
        flow = EventFlow()
        flow.name = 'Dm_FairyFountain_Frore'
        flow.flowchart = chart = Flowchart()
        chart.name = flow.name
        reward = Event()
        reward.name, reward.data = 'Event174', SubFlowEvent()
        reward.data.res_flowchart_name, reward.data.entry_point_name = 'Dm_SY_GetInEvent', 'GetInEvent'
        reward.data.params = Container()
        reward.data.params.data = {'ActorName': actor}
        chart.events.append(reward)
        entry = EntryPoint('Main')
        entry.main_event = make_index(reward)
        chart.entry_points.append(entry)
        stream = BytesIO()
        flow.write(stream)
        marked, hooks = add_collection_markers(stream.getvalue(), {reward.name: native_flag})
        displayed = patch_flow(marked, {'text_get': [(reward.name, actor, True)]})
        converted = add_converter_calls(displayed, [reward.name], flow.name)

        for raw, expected in ((displayed, ['RandoTextGet_Event174']),
                              (converted, ['RandoProgAfter_Event174', 'RandoTextGet_Event174'])):
            with self.subTest(chain=expected):
                patched, added = add_event_triggers(raw, [(hooks[0], trigger_flag)])
                self.assertEqual(added, {trigger_flag})
                before = parse_flow(raw).flowchart
                after = parse_flow(patched).flowchart
                self.assertEqual([event.name for event in after.events[:-1]],
                                 [event.name for event in before.events])
                event = after.entry_points[0].main_event.v
                self.assertEqual(event.data.params.data['GameDataName'], trigger_flag)
                event = event.data.nxt.v
                self.assertEqual(event.name, 'Event174')
                for name in expected:
                    event = event.data.nxt.v
                    self.assertEqual(event.name, name)
                self.assertEqual(event.data.nxt.v.data.params.data['GameDataName'], native_flag)

        unexpected = parse_flow(displayed)
        unexpected.flowchart.events[0].data.nxt.v.data.entry_point_name = 'OtherSubflow'
        stream = BytesIO()
        unexpected.write(stream)
        raw = stream.getvalue()
        self.assertEqual(add_event_triggers(raw, [(hooks[0], trigger_flag)]), (raw, set()))

    def test_private_drop_and_event_get_independent_saved_flags(self):
        import ainb
        from evfl.actor import Actor
        from evfl.common import ActorIdentifier, StringHolder
        from evfl.container import Container
        from evfl.entry_point import EntryPoint
        from evfl.event import ActionEvent, Event
        from evfl.evfl import EventFlow
        from evfl.flowchart import Flowchart
        from evfl.util import make_index, make_rindex
        from oot_rando.formats import byml_codec
        from oot_rando.formats.inspect_resources import sarc
        from oot_rando.game.tracking_metadata import GAMEDATA
        from oot_rando.patching.ap_mailbox import ainb_to_binary
        from oot_rando.formats.evfl_tools import parse_flow
        from oot_rando.patching.event_patch import add_collection_markers
        from oot_rando.patching.soul_adapter import murmur3

        tree = 'KokiriForest#trees#77'
        song = 'song#Song from Saria'
        actor = 'Obj_RandoOnce_' + sha256(tree.encode()).hexdigest()[:16]
        pack_path = f'Pack/Actor/{actor}.pack.zs'
        root = f'AI/{actor}.root.ainb'
        event_path = 'Event/EventFlow/Fixture.bfevfl.zs'
        tree_collection = 'Rando.Check.fixture-tree'
        song_collection = f'RandoCheck.fixture.{song}'

        drop = ainb_to_binary({
            'Version': 0x408, 'Filename': actor + '.root', 'Category': 'AI', 'Blackboard ID': 0,
            'Parent Blackboard ID': 0, 'Commands': [{'Name': 'Root', 'Root Node Index': 0,
                                                     'GUID': '00000000-0000-0000-0000-000000000010'}],
            'Nodes': [ainb_node(0, 'Element_Simultaneous', (1,)),
                      ainb_node(1, 'Element_Sequential', (2,)), ainb_node(2, 'Element_Sequential')],
            'Replacement Table': [], 'Modules': [], 'Has Section 0x6C': True,
        })

        flow = EventFlow()
        flow.name = 'Fixture'
        flow.flowchart = chart = Flowchart()
        chart.name = flow.name
        giver = Actor()
        giver.identifier = ActorIdentifier('PouchSystemActor')
        giver.actions.append(StringHolder('EventTriggerAddOrRemovePouchContent'))
        giver.params = Container()
        giver.params.data = {'Fixture': True}
        chart.actors.append(giver)
        payout = Event()
        payout.name, payout.data = 'EventReward', ActionEvent()
        payout.data.actor = make_rindex(giver)
        payout.data.actor_action = make_rindex(giver.actions[0])
        chart.events.append(payout)
        entry = EntryPoint('Main')
        entry.main_event = make_index(payout)
        chart.entry_points.append(entry)
        stream = BytesIO()
        flow.write(stream)
        marked, markers = add_collection_markers(stream.getvalue(), {payout.name: song_collection})

        flags = [tree_collection, song_collection]
        raw = {
            event_path: marked,
            pack_path: byml_codec.build_sarc({root: drop, 'keep.bin': b'unchanged'}),
            GAMEDATA: byml_codec.dump({'endian': '<', 'version': 7, 'root': {
                'Data': {'Bool': [{'Hash': byml_codec.U32(murmur3(flag)), 'DefaultValue': False,
                                  'ResetTypeValue': 8, 'SaveFileIndex': 0} for flag in flags]},
                'MetaData': {'AllDataSaveSize': 16, 'AllDataSaveOffset': 16,
                             'SaveDataSize': [16], 'SaveDataOffsetPos': [16]},
            }}),
        }
        tracking = {
            'checks': {
                tree: {'collection': {'type': 'bool', 'hash': str(murmur3(tree_collection))}},
                song: {'collection': {'type': 'bool', 'hash': str(murmur3(song_collection))}},
                'unrelated': {'collection': None},
            },
            'repeatables': [{'id': tree, 'actor': actor, 'kind': 'pickup', 'flag_hash': murmur3(tree_collection)}],
            'event_markers': {event_path: markers},
        }
        resources, triggers = prepare_trigger_resources({'files': dict.fromkeys(raw)}, tracking, raw.__getitem__)
        self.assertEqual(triggers, {ident: murmur3(trigger_flag_name(ident)) for ident in (tree, song)})
        data = byml_codec.load(resources[GAMEDATA])['root']
        self.assertEqual(data['MetaData']['AllDataSaveSize'], 32)
        self.assertEqual({int(row['Hash']) for row in data['Data']['Bool']},
                         {murmur3(flag) for flag in flags} | set(triggers.values()))
        self.assertTrue(all(row['DefaultValue'] is False for row in data['Data']['Bool']))

        pack = sarc(resources[pack_path])
        self.assertEqual(pack['keep.bin'], b'unchanged')
        ai = ainb.AINB.from_binary(pack[root]).as_dict()
        children = ai['Nodes'][1]['Plugs']['Child']
        setter = ai['Nodes'][children[0]['Node Index']]
        self.assertEqual(setter['Parameters']['Inputs']['String'][0]['Default Value'], trigger_flag_name(tree))
        self.assertEqual(children[1]['Node Index'], 2)

        chart = parse_flow(resources[event_path]).flowchart
        first = chart.entry_points[0].main_event.v
        self.assertEqual(first.data.params.data['GameDataName'], trigger_flag_name(song))
        self.assertEqual(first.data.nxt.v.name, 'EventReward')
        self.assertEqual(first.data.nxt.v.data.nxt.v.data.params.data['GameDataName'], song_collection)

        import zstandard
        from oot_rando.randomizer.artifact import read_artifact
        from map_oot_rando.save_tracking import SaveConnection
        from map_oot_rando.state import StateStore
        from test_save_tracking import write_save, write_seed

        with TemporaryDirectory() as directory:
            folder = Path(directory)
            source = folder / 'original'
            source.mkdir()
            seed_id = write_seed(source, generator_version='0.12.18')
            manifest = json.loads((source / 'manifest.json').read_bytes())
            original_tracking = json.loads((source / 'tracking.json').read_bytes())
            original_tracking.update(tracking)
            payload = json.dumps(original_tracking).encode()
            (source / 'tracking.json').write_bytes(payload)
            catalogue = {'seed_id': seed_id, 'checks': [dict(id=ident, name=ident, region='Kokiri Forest')
                                                        for ident in (tree, song)]}
            (source / 'checks.json').write_text(json.dumps(catalogue), encoding='utf-8')
            manifest['tracking']['sha256'] = sha256(payload).hexdigest()
            compressor = zstandard.ZstdCompressor()
            for path, binary in raw.items():
                data = compressor.compress(binary)
                file = source / 'romfs' / path
                file.parent.mkdir(parents=True, exist_ok=True)
                file.write_bytes(data)
                manifest['files'][path] = {'size': len(data), 'sha256': sha256(data).hexdigest()}
            (source / 'manifest.json').write_text(json.dumps(manifest), encoding='utf-8')

            output = folder / 'prepared'
            with (patch('oot_rando.formats.inspect_nup.Nup'),
                  patch('oot_rando.formats.inspect_resources.dictionaries', return_value={})):
                self.assertEqual(prepare_seed(folder / 'fixture.nup', source, output), 2)
            self.assertEqual((source / 'tracking.json').read_bytes(), payload)
            self.assertEqual(read_artifact(output)[0]['seed_id'], seed_id)
            save = folder / 'progress.sav'
            write_save(save, flags=tuple(sorted(triggers.values())))
            reader = Mock()
            session = SaveConnection(output, save, StateStore(seed_id, (tree, song)), manual_dir=folder / 'manual',
                                     live_factory=lambda: reader)
            update = session.refresh()
            self.assertEqual(set(update.states.values()), {'completed'})
            self.assertTrue(all(row['source'] == 'instrumented_trigger' and row['reward'] == ''
                                for row in update.rows.values()))
            write_save(save)
            self.assertEqual(set(session.refresh().states.values()), {'unknown'})
            reader.snapshot.return_value = dict(bool={100: True, triggers[tree]: True},
                                                bool64_complete=False, sha256='tree-drop')
            self.assertEqual(session.refresh(live=True).states[tree], 'completed')

    def test_shared_skulltula_drops_are_isolated_in_the_mod_and_tracker(self):
        import ainb
        import zstandard
        from oot_rando.catalog.traps import trap_actor, trap_item
        from oot_rando.formats import byml_codec as codec
        from oot_rando.formats.inspect_resources import sarc
        from oot_rando.game.item_forms import form_actor
        from oot_rando.game.resource_allocations import allocation
        from oot_rando.game.tracking_metadata import GAMEDATA
        from oot_rando.patching.ap_mailbox import ainb_to_binary
        from oot_rando.patching.randomize_kokiri import RESTBL
        from oot_rando.patching.repeatable_adapter import EVENT_PACK
        from oot_rando.patching.soul_adapter import RSDB_FILES, murmur3
        from oot_rando.randomizer.artifact import read_artifact

        from map_oot_rando.save_tracking import SaveConnection
        from map_oot_rando.state import StateStore
        from test_save_tracking import write_save, write_seed

        def byml(root):
            return codec.dump({'endian': '<', 'version': 7, 'root': root})

        first, second, token = ('KokiriForest#gs#' + str(key) for key in (71, 72, 73))
        trap = trap_item('Bow')
        reward, native = form_actor(trap_actor(trap), 'world', skulltula_drop=True), 'Obj_Token_Gold'
        tracking = {'checks': {ident: {'collection': {'type': 'bool64', 'hash': ident.rsplit('#', 1)[1]},
                                       'reward': item, 'actor': actor}
                               for ident, actor, item in ((first, reward, trap),
                                                          (second, reward, trap),
                                                          (token, native, 'Gold Skulltula Token'))},
                    'known_bool64': ['71', '72', '73']}
        first_map = 'Banc/KokiriForest/KokiriForest_Child_Static.bcett.byml.zs'
        second_map = 'Banc/KokiriForest/KokiriForest_Adult_Static.bcett.byml.zs'
        third_map = 'Banc/KokiriForest/KokiriForest_Adult_Dynamic.bcett.byml.zs'
        spider = {'Gyaml': 'Enemy_Skulltula_Gold', 'Hash': codec.U64(71),
                  'Dynamic': {'Drop__DropActor': reward, 'Enemy_Skulltula_Gold_Nocturnal': True}}
        other = {'Gyaml': reward, 'Hash': codec.U64(74)}
        native_spider = {'Gyaml': spider['Gyaml'], 'Hash': codec.U64(73)}
        root = ainb_node(0, 'Element_Sequential')
        root['Flags'] = ['Is Root Node']
        graph = ainb_to_binary({
            'Version': 0x408, 'Filename': 'Token.root', 'Category': 'AI', 'Blackboard ID': 0,
            'Parent Blackboard ID': 0, 'Commands': [{'Name': 'Root', 'Root Node Index': 0,
                                                     'GUID': '00000000-0000-0000-0000-000000000010'}],
            'Nodes': [root], 'Replacement Table': [], 'Modules': [], 'Has Section 0x6C': True,
        })
        raw = {
            first_map: byml({'Actors': [spider, {**spider, 'Hash': codec.U64(72)}, other]}),
            second_map: byml({'Actors': [spider]}),
            third_map: byml({'Actors': [native_spider]}),
            EVENT_PACK: codec.build_sarc({'AI/Token.root.ainb': graph}),
            GAMEDATA: byml({'Data': {'Bool': [{'Hash': codec.U32(100), 'DefaultValue': False,
                                              'ResetTypeValue': 8, 'SaveFileIndex': 0}]}, 'MetaData': {
                'AllDataSaveSize': 16, 'AllDataSaveOffset': 16, 'SaveDataSize': [16], 'SaveDataOffsetPos': [16],
            }}),
        }
        for actor in (reward, native):
            raw[f'Pack/Actor/{actor}.pack.zs'] = codec.build_sarc({
                f'Actor/{actor}.engine__actor__ActorParam.bgyml': byml({'Components': {
                    'AIInfoRef': '?AI/Token.bgyml', 'PouchContentRef': '?Component/Reward.bgyml',
                }}),
                'AI/Token.bgyml': byml({'RootAIRef': 'Work/AI/Root/Token.root.ain', 'OtherSetting': True}),
                'Component/Reward.bgyml': byml({'PouchActor': 'unchanged'}),
            })
        for table, path in RSDB_FILES.items():
            actors = (reward,) if table == 'PouchActorInfo' else tuple(sorted((reward, native)))
            raw[path] = byml([{'__RowId': actor, 'Unchanged': actor} for actor in actors])
        allocations = sorted(zlib.crc32(path.removesuffix('.zs').encode()) for path in raw)
        raw[RESTBL] = b'RESTBL' + struct.pack('<IIII', 1, 160, len(allocations), 0) + b''.join(
            struct.pack('<II', key, 4096) for key in allocations)
        maps = (first_map, second_map, third_map)
        with self.assertRaisesRegex(ValueError, token):
            prepare_skulltula_resources(tracking, maps[:2], raw.__getitem__)
        wrong = dict(raw)
        wrong[first_map] = byml({'Actors': [{**spider, 'Dynamic': {'Drop__DropActor': native}}]})
        with self.assertRaisesRegex(ValueError, first):
            prepare_skulltula_resources(tracking, maps, wrong.__getitem__)

        with TemporaryDirectory() as directory:
            folder = Path(directory)
            source = folder / 'original'
            source.mkdir()
            seed_id = write_seed(source, app_version='0.8.5+fixture')
            manifest = json.loads((source / 'manifest.json').read_bytes())
            original_tracking = json.loads((source / 'tracking.json').read_bytes())
            original_tracking.update(tracking)
            payload = json.dumps(original_tracking).encode()
            (source / 'tracking.json').write_bytes(payload)
            catalogue = {'seed_id': seed_id, 'checks': [dict(id=ident, name=ident, region='Kokiri Forest')
                                                        for ident in (first, second, token)]}
            (source / 'checks.json').write_text(json.dumps(catalogue), encoding='utf-8')
            manifest['tracking']['sha256'] = sha256(payload).hexdigest()
            compressor = zstandard.ZstdCompressor()
            stock = {}
            for path, binary in raw.items():
                data = compressor.compress(binary)
                if path in (third_map, EVENT_PACK) or native in path:
                    stock[path] = data
                    continue
                file = source / 'romfs' / path
                file.parent.mkdir(parents=True, exist_ok=True)
                file.write_bytes(data)
                manifest['files'][path] = {'size': len(data), 'sha256': sha256(data).hexdigest()}
            (source / 'manifest.json').write_text(json.dumps(manifest), encoding='utf-8')
            output = folder / 'prepared'
            original_map = (source / 'romfs' / first_map).read_bytes()
            original_manifest = (source / 'manifest.json').read_bytes()
            backup = source / SEED_BACKUP
            with (patch('oot_rando.formats.inspect_nup.Nup') as nup,
                  patch('oot_rando.formats.inspect_resources.dictionaries', return_value={}),
                  patch('oot_rando.patching.randomize_kokiri.check_supported_game'),
                  patch('oot_rando.game.world_maps.effective_members', return_value={key: key for key in stock})):
                nup.return_value.read.side_effect = stock.__getitem__
                nup_path = folder / 'fixture.nup'
                self.assertEqual(prepare_seed(nup_path, source, output, skulltulas=True), 3)
                self.assertEqual((source / 'tracking.json').read_bytes(), payload)
                self.assertFalse((source / 'romfs' / third_map).exists())

                verifier = 'oot_rando.randomizer.artifact.read_artifact'
                with patch(verifier, side_effect=[read_artifact(source), ValueError('validation refusée')]):
                    with self.assertRaisesRegex(ValueError, 'validation refusée'):
                        prepare_seed_in_place(nup_path, source)
                self.assertFalse(backup.exists())
                self.assertEqual((source / 'romfs' / first_map).read_bytes(), original_map)
                self.assertEqual((source / 'manifest.json').read_bytes(), original_manifest)
                self.assertFalse((source / 'romfs' / third_map).exists())
                read_artifact(source)

                with patch(verifier, side_effect=[read_artifact(source), KeyboardInterrupt]):
                    with self.assertRaises(KeyboardInterrupt):
                        prepare_seed_in_place(nup_path, source)
                self.assertTrue((backup / 'pending.json').is_file())
                self.assertEqual(prepare_seed_in_place(nup_path, source), (3, True))
            self.assertEqual(prepare_seed_in_place('unused.nup', source), (3, False))
            self.assertTrue((backup / 'changes.json').is_file())
            self.assertEqual((backup / 'originaux' / 'tracking.json').read_bytes(), payload)
            self.assertEqual((backup / 'originaux' / 'manifest.json').read_bytes(), original_manifest)
            self.assertEqual((backup / 'originaux' / 'romfs' / first_map).read_bytes(), original_map)
            self.assertFalse((backup / 'originaux' / 'romfs' / third_map).exists())
            self.assertFalse((backup / 'originaux' / 'checks.json').exists())
            self.assertEqual(read_artifact(source), read_artifact(output))
            self.assertEqual(read_artifact(output)[0]['seed_id'], seed_id)

            def prepared(path):
                return zstandard.ZstdDecompressor().decompress((output / 'romfs' / path).read_bytes())

            def actors(path):
                return codec.load(prepared(path))['root']['Actors']

            record = json.loads((output / 'tracking.json').read_bytes())
            flags = {ident: murmur3(trigger_flag_name(ident)) for ident in (first, second, token)}
            self.assertEqual(record['trigger_flags'], flags)
            self.assertEqual(record['checks'], tracking['checks'])
            self.assertEqual(actors(first_map)[2], other)
            self.assertTrue(actors(first_map)[0]['Dynamic']['Enemy_Skulltula_Gold_Nocturnal'])
            name = 'Drop__DropActor'
            aliases = [entry['Dynamic'][name] for entry in (*actors(first_map)[:2], *actors(third_map))]
            self.assertEqual(actors(second_map)[0]['Dynamic'][name], aliases[0])
            self.assertEqual(len(set(aliases)), 3)

            for ident, alias in zip((first, second, token), aliases):
                path = f'Pack/Actor/{alias}.pack.zs'
                files = sarc(prepared(path))
                self.assertLessEqual(len(alias), 25)
                member = f'AI/{alias}.root.ainb'
                self.assertGreater(allocation(prepared(RESTBL), member), len(files[member]))
                self.assertGreater(allocation(prepared(RESTBL), path), len(prepared(path)))
                script = ainb.AINB.from_binary(files[member]).as_dict()
                nodes = script['Nodes']
                wrapper = nodes[script['Commands'][0]['Root Node Index']]
                setter, original = (nodes[child['Node Index']] for child in wrapper['Plugs']['Child'])
                self.assertEqual(setter['Parameters']['Inputs']['String'][0]['Default Value'], trigger_flag_name(ident))
                self.assertEqual(original, {**root, 'Flags': []})
                self.assertEqual(files['Component/Reward.bgyml'], byml({'PouchActor': 'unchanged'}))
                row = next(row for row in codec.load(prepared(RSDB_FILES['ActorInfo']))['root']
                           if row['__RowId'] == alias)
                self.assertEqual(row['Unchanged'], tracking['checks'][ident]['actor'])

            save = folder / 'progress.sav'
            write_save(save, flags=(flags[first],))
            reader = Mock()
            session = SaveConnection(output, save, StateStore(seed_id, flags), manual_dir=folder / 'manual',
                                     live_factory=lambda: reader)
            update = session.refresh()
            self.assertEqual(update.states, {first: 'completed', second: 'unknown', token: 'unknown'})
            self.assertEqual(update.rows[first]['source'], 'instrumented_trigger')
            self.assertEqual(update.rows[first]['reward'], '')
            reader.snapshot.return_value = dict(bool={100: True, flags[second]: True},
                                                bool64_complete=False, sha256='second-skulltula-drop')
            live = session.refresh(live=True)
            self.assertEqual(live.states[second], 'completed')
            self.assertEqual(live.states[token], 'unknown')
