import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

from map_oot_rando.export import main
from map_oot_rando.metadata import bind_catalogue, export_scan
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
