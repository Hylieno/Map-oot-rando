"""Round-trip the prototype's two trigger hooks through the actual game formats."""
from hashlib import sha256
from importlib.util import find_spec
from io import BytesIO
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import Mock, patch

from map_oot_rando.trigger_seed import prepare_seed, prepare_trigger_resources, trigger_flag_name


@unittest.skipUnless(find_spec('oot_rando') and find_spec('evfl') and find_spec('ainb'),
                     'Pinned OotrR and binary format readers are required')
class TriggerSeedTests(unittest.TestCase):
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
        from oot_rando.patching.event_patch import _flow, add_collection_markers
        from oot_rando.patching.soul_adapter import murmur3

        tree = 'KokiriForest#trees#77'
        song = 'song#Song from Saria'
        actor = 'Obj_RandoOnce_' + sha256(tree.encode()).hexdigest()[:16]
        pack_path = f'Pack/Actor/{actor}.pack.zs'
        root = f'AI/{actor}.root.ainb'
        event_path = 'Event/EventFlow/Fixture.bfevfl.zs'
        tree_collection = 'Rando.Check.fixture-tree'
        song_collection = f'RandoCheck.fixture.{song}'

        def ainb_node(index, node_type, children=()):
            return {'Node Type': node_type, 'Node Index': index, 'Name': '',
                    'GUID': f'00000000-0000-0000-0000-{index:012d}', 'Flags': [], 'Queries': [], 'Attachments': [],
                    'Properties': {}, 'Parameters': {'Inputs': {}, 'Outputs': {}}, 'XLink Actions': [],
                    'Plugs': {'Child': [{'Node Index': i, 'Name': ''} for i in children]} if children else {}}

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

        chart = _flow(resources[event_path]).flowchart
        first = chart.entry_points[0].main_event.v
        self.assertEqual(first.data.params.data['GameDataName'], trigger_flag_name(song))
        self.assertEqual(first.data.nxt.v.name, 'EventReward')
        self.assertEqual(first.data.nxt.v.data.nxt.v.data.params.data['GameDataName'], song_collection)

        import zstandard
        from oot_rando.randomizer.randomizer_services import read_artifact
        from map_oot_rando.save_tracking import SaveConnection
        from map_oot_rando.state import StateStore
        from test_save_tracking import write_save, write_seed

        with TemporaryDirectory() as directory:
            folder = Path(directory)
            source = folder / 'original'
            source.mkdir()
            seed_id = write_seed(source)
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
