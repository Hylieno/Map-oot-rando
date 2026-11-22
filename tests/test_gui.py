"""Tk integration checks; require a desktop (or Xvfb on CI)."""
import os
import tkinter as tk
import unittest
from types import SimpleNamespace
from map_oot_rando.gui import MapApplication, COLORS
from map_oot_rando.simulation import demo_document


class GuiTests(unittest.TestCase):
    def setUp(self):
        try:
            self.root = tk.Tk()
        except tk.TclError as error:
            if os.environ.get('MAP_REQUIRE_DISPLAY') == '1':
                raise
            self.skipTest(f'No Tk display: {error}')
        self.errors = []
        self.root.report_callback_exception = lambda *args: self.errors.append(args)
        self.app = MapApplication(self.root)
        self.root.update()

    def tearDown(self):
        if hasattr(self, 'root'):
            self.root.destroy()
            self.assertEqual(self.errors, [])

    def test_search_selection_marker_update_and_filters(self):
        app = self.app
        points = [app.viewport.screen(r.project()) for r in app.visible
                  if r.position is not None and r.resource == app.resource.get()]
        self.assertGreater(max(x for x, y in points) - min(x for x, y in points), 100)
        for x, y in points:
            self.assertTrue(0 <= x <= app.canvas.winfo_width())
            self.assertTrue(0 <= y <= app.canvas.winfo_height())
        app.query.set('SIMULATED#0')
        app.choose_first()
        self.assertEqual(app.selected.id, 'SIMULATED#0')
        self.assertEqual(len(app.visible), 1)
        app.simulate('completed')
        ovals = [i for i in app.markers if app.canvas.type(i) == 'oval']
        self.assertEqual(len(ovals), 1)
        self.assertEqual(app.canvas.itemcget(ovals[0], 'fill'), COLORS['completed'])
        app.status_vars['completed'].set(False)
        app.render()
        self.assertEqual(app.visible, ())
        self.assertFalse(app.markers)

    def test_resource_search_missing_and_disconnect(self):
        app = self.app
        app.query.set('interior')
        app.choose_first()
        self.assertEqual(app.resource.get(), 'SIMULATION / intérieur')
        app.toggle_connection()
        app.simulate('completed')
        self.assertIn('Déconnecté', app.connection.get())
        app.toggle_connection()
        self.assertEqual(app.store.states[app.selected.id], 'completed')
        app.query.set('SIMULATED#4')
        app.choose_first()
        self.assertIn('inconnues', app.details.get())
        self.assertFalse(app.markers)

    def test_pan_zoom_and_import_isolation(self):
        app = self.app
        app.query.set('aucun résultat')
        app.press(SimpleNamespace(x=300, y=300))
        old_x = app.viewport.x
        app.pan(SimpleNamespace(x=320, y=310))
        self.assertEqual(app.viewport.x, old_x + 20)
        scale = app.viewport.scale
        app.zoom(1.2, 400, 300)
        self.assertAlmostEqual(app.viewport.scale, scale * 1.2)
        doc = demo_document()
        doc['provenance'] = 'ootrr-scan'  # Synthetic fixture exercising import mode only.
        app.load(doc)
        self.assertIsNone(app.simulation)
        self.assertEqual(set(app.store.states.values()), {'unknown'})
        self.assertEqual(app.store.connection, 'disconnected')
        self.assertIsNone(app.store.last_success)
        app.load(demo_document())
        self.assertIsNotNone(app.simulation)

    def test_seed_import_loads_map_without_export_dialog(self):
        from threading import Event
        from unittest.mock import patch

        app = self.app
        finished = Event()
        document = demo_document()
        document.update(provenance='ootrr-scan', seed_id='test-seed', diagnostics=[])

        def fake_import(nup, checks, progress):
            progress('Lecture des cartes')
            return document

        original_put = app.import_events.put

        def signal_result(result):
            original_put(result)
            if result[0] == 'done':
                finished.set()

        with (patch.object(app.import_events, 'put', side_effect=signal_result),
              patch('map_oot_rando.gui.filedialog.askopenfilename', side_effect=['game.nup', 'checks.json']),
              patch('map_oot_rando.gui.import_seed', side_effect=fake_import) as importer):
            app.choose_seed()
            self.assertTrue(finished.wait(3))
            app.poll_import()
        importer.assert_called_once()
        self.assertEqual(app.store.seed_id, 'test-seed')
        self.assertIsNone(app.simulation)
        self.assertIn('Carte chargée', app.import_status.get())
        self.assertFalse(app.import_button.instate(['disabled']))
