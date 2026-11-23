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

    def test_scene_follows_resource_and_stays_behind_checks(self):
        app = self.app
        doc = demo_document()
        doc['scenes'] = {'SIMULATION / extérieur': {
            'points': [('entrée', [30, 30])],
            'rooms': [('maison', [20, 20], [40, 40])],
        }}
        app.load(doc)
        self.assertEqual(len(app.canvas.find_withtag('scene')), 2)
        self.assertLess(max(app.canvas.find_withtag('scene')), min(app.markers))
        app.resource.set('SIMULATION / intérieur')
        app.resource_changed()
        self.assertFalse(app.canvas.find_withtag('scene'))
        self.assertTrue(app.markers)

    def test_aerial_image_is_drawn_below_checks_for_its_resource(self):
        from PIL import Image
        from map_oot_rando.aerial import AerialImage

        doc = demo_document()
        background = AerialImage(Image.new('RGB', (32, 32), 'green'),
                                 [(0, 0), (32, 0), (0, 32)], [(0, 0), (100, 0), (0, 100)])
        doc['aerial'] = {'SIMULATION / extérieur': background.to_document()}
        app = self.app
        app.load(doc)
        image, = app.canvas.find_withtag('aerial')
        self.assertLess(image, min(app.markers))
        app.resource.set('SIMULATION / intérieur')
        app.resource_changed()
        self.assertFalse(app.canvas.find_withtag('aerial'))

    def test_kokiri_age_merges_layers_and_lists_uncovered_checks(self):
        from PIL import Image
        from map_oot_rando.aerial import AerialImage
        from map_oot_rando.scene import AGE_VIEWS

        child = 'Banc/KokiriForest/KokiriForest_Child_Dynamic.bcett.byml.zs'
        static = child.replace('Dynamic', 'Static')
        adult = child.replace('Child', 'Adult')
        doc = demo_document()
        doc['locations'] = [
            dict(doc['locations'][0], resource=child, position=[50, 0, 50]),
            dict(doc['locations'][1], resource=static, position=[170, 0, 30]),
            dict(doc['locations'][2], resource=adult, position=[10, 0, 10]),
        ]
        background = AerialImage(Image.new('RGB', (100, 100), 'green'),
                                 [(0, 0), (100, 0), (0, 100)], [(0, 0), (100, 0), (0, 100)])
        doc['aerial'] = {child: background.to_document()}
        app = self.app
        app.load(doc)
        self.assertEqual(app.resource.get(), AGE_VIEWS['Child'])
        self.assertEqual(len(app.visible), 2)
        self.assertIn('hors du fond', app.results.get(1))
        visible_pins = lambda: {row.id for row in app.markers.values()}
        self.assertEqual(visible_pins(), {app.visible[0].id})
        app.choose(app.visible[1])
        self.assertEqual(visible_pins(), {row.id for row in app.visible})
        app.resource.set(AGE_VIEWS['Adult'])
        app.resource_changed()
        self.assertEqual(len(app.visible), 1)
        self.assertFalse(app.canvas.find_withtag('aerial'))

    def test_import_automatically_loads_field_atlas_without_dialog(self):
        from unittest.mock import patch
        from PIL import Image
        from map_oot_rando.field_atlas import HOUSE_PIXELS

        resource = 'Banc/KokiriForest/KokiriForest_Adult_Dynamic.bcett.byml.zs'
        doc = demo_document()
        doc['provenance'] = 'ootrr-scan'
        doc['locations'] = [dict(doc['locations'][0], resource=resource)]
        doc['scenes'] = {resource: dict(
            rooms=[(name.replace(' ', '_'), [x-1, y-1], [x+1, y+1])
                   for name, (x, y) in HOUSE_PIXELS.items()],
            points=[],
        )}
        app = self.app

        def wait_for_background():
            if app.canvas.find_withtag('aerial'):
                self.root.quit()
            else:
                self.root.after(20, wait_for_background)

        with (patch('map_oot_rando.gui.load_kokiri_image',
                    return_value=Image.new('RGB', (900, 498), 'white')) as download,
              patch('map_oot_rando.gui.align_image') as manual):
            app.load(doc)
            self.root.after(20, wait_for_background)
            deadline = self.root.after(2000, self.root.quit)
            self.root.mainloop()
            self.root.after_cancel(deadline)
            self.assertTrue(app.canvas.find_withtag('aerial'))
            download.assert_called_once()
            manual.assert_not_called()
