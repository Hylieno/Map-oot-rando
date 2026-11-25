"""Tk integration checks; require a desktop (or Xvfb on CI)."""
import os
from pathlib import Path
from tempfile import TemporaryDirectory
import tkinter as tk
import unittest
from types import SimpleNamespace
from map_oot_rando.gui import MapApplication, COLORS
from map_oot_rando.save_profiles import SaveProfiles
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
        self.profiles_path = Path(self.enterContext(TemporaryDirectory())) / 'profiles.json'
        self.app = MapApplication(self.root, profiles=SaveProfiles(self.profiles_path))
        self.root.update()

    def tearDown(self):
        if hasattr(self, 'root'):
            self.app.close_window()
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

    def test_search_opens_the_known_zone_of_an_unpositioned_check(self):
        from unittest.mock import patch
        from map_oot_rando.scene import REGION_VIEWS, TRAINING_VIEWS

        app = self.app
        forest, training, temple = 'KokiriForest', 'GerudoTrainingGround', 'TempleOfTime'
        scenes = {view: {'rooms': [], 'points': []} for view in (REGION_VIEWS[forest]['Child'], *TRAINING_VIEWS)}
        missing = dict(id='training#unpositioned', name='Clé du labyrinthe', category='key',
                       resource='Emplacements sans position', position=None, region=training)
        gift = dict(missing, id='ap#Gift from Sages', name='Don des Sages', region=temple)
        doc = dict(demo_document(), provenance='ootrr-scan', regions=[forest, training, temple],
                   locations=[missing, gift], scenes=scenes)
        self.enterContext(patch.object(app, 'ensure_atlas'))
        app.load(doc)
        self.assertEqual(app.resource.get(), REGION_VIEWS[forest]['Child'])
        app.query.set(missing['name'])
        app.choose_first()
        self.assertEqual(app.resource.get(), TRAINING_VIEWS[0])
        self.assertIn('Centre d’entraînement Gerudo', app.details.get())
        self.assertIn('inconnues', app.details.get())
        self.assertFalse(app.canvas.find_withtag('check-pin'))

        app.resource.set(TRAINING_VIEWS[1])
        app.resource_changed(manual=False)
        app.choose_first()
        self.assertEqual(app.resource.get(), TRAINING_VIEWS[1])

        app.query.set(gift['name'])
        app.choose_first()
        self.assertEqual(app.selected.id, gift['id'])
        self.assertIn('Temple du Temps · récompense de scénario', app.details.get())
        self.assertEqual(app.resource.get(), TRAINING_VIEWS[1])

    def test_navigation_and_tracking_remain_available_in_a_narrow_window(self):
        from unittest.mock import patch
        from map_oot_rando.scene import NEIGHBORS, REGION_NAMES, REGION_VIEWS

        app = self.app
        forest = 'KokiriForest'
        destinations = ('LostWood', 'KokiriBridge', 'HyruleField', 'InsideTheDekuTree')
        scenes = {REGION_VIEWS[region].get('Child', REGION_VIEWS[region].get(None)):
                  {'rooms': [], 'points': []} for region in (forest, *destinations)}
        doc = dict(demo_document(), provenance='ootrr-scan', regions=[forest, *destinations],
                   locations=[], scenes=scenes)
        self.enterContext(patch.object(app, 'ensure_atlas'))
        app.load(doc)
        self.root.update()
        self.assertEqual(app.resource.get(), REGION_VIEWS[forest]['Child'])
        self.assertTrue(all(app.neighbor_buttons[target].winfo_ismapped() for target in destinations))

        self.root.geometry('690x700')
        self.root.update()
        self.assertTrue(app.overview_button.winfo_ismapped())
        self.assertTrue(app.neighbor_menu_button.winfo_ismapped())
        for widget in (app.import_button, app.track_button, app.stop_track_button, app.live_check):
            self.assertTrue(widget.winfo_ismapped())
            self.assertGreaterEqual(widget.winfo_width(), widget.winfo_reqwidth())
        available = [region for region in NEIGHBORS[forest] if region in destinations]
        labels = [app.neighbor_menu.entrycget(i, 'label') for i in range(len(available))]
        self.assertEqual(labels, [REGION_NAMES[region] for region in available])

        self.root.geometry('1180x760')
        self.root.update()
        self.assertFalse(app.neighbor_menu_button.winfo_ismapped())
        self.assertTrue(all(app.neighbor_buttons[target].winfo_ismapped() for target in destinations))
        self.assertGreater(app.track_button.winfo_rootx(), app.import_button.winfo_rootx())

        self.root.geometry('690x700')
        self.root.update()
        app.neighbor_menu.invoke(labels.index(REGION_NAMES['InsideTheDekuTree']))
        self.assertEqual(app.resource.get(), REGION_VIEWS['InsideTheDekuTree'][None])
        self.root.geometry('760x700')
        self.root.update()
        destination = app.neighbor_menu_button if app.neighbor_menu_button.winfo_ismapped() else (
            app.neighbor_buttons[forest])
        for widget in (app.overview_button, app.floor_picker, destination):
            self.assertTrue(widget.winfo_ismapped(), str(widget))
            self.assertGreaterEqual(widget.winfo_width(), widget.winfo_reqwidth(), str(widget))

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
            self.assertIsNotNone(app.import_callback)
            app.poll_import()
        self.assertIsNone(app.import_callback)
        importer.assert_called_once()
        self.assertEqual(app.store.seed_id, 'test-seed')
        self.assertIsNone(app.simulation)
        self.assertIn('Carte chargée', app.import_status.get())
        self.assertFalse(app.import_button.instate(['disabled']))

    def test_reimport_keeps_same_seed_view_manual_age_and_last_snapshot(self):
        from unittest.mock import patch
        from map_oot_rando.scene import REGION_VIEWS

        app = self.app
        doc = dict(demo_document(), provenance='ootrr-scan', seed_id='same-seed',
                   regions=['KokiriForest', 'LostWood'])
        template = doc['locations'][0]
        doc['locations'] = [
            dict(template, id='forest', resource='Banc/KokiriForest/KokiriForest_Child_Static.bcett.byml.zs'),
            dict(template, id='woods', resource='Banc/LostWood/LostWood_Adult_Static.bcett.byml.zs'),
        ]
        self.enterContext(patch.object(app, 'ensure_atlas'))
        app.load(doc)
        app.resource.set(REGION_VIEWS['LostWood']['Adult'])
        app.resource_changed()
        app.follow_age.set(False)
        stamp = '2026-11-24T11:00:00+00:00'
        app.store.publish(doc['seed_id'], {'forest': 'available', 'woods': 'completed'},
                          mode='save', timestamp=stamp)
        moved = dict(doc['locations'][1], position=(2, 100, 4))
        updated = dict(doc, locations=[dict(doc['locations'][0], id='new'), moved])
        app.load(updated)
        self.assertEqual(app.resource.get(), REGION_VIEWS['LostWood']['Adult'])
        self.assertEqual([row.position for row in app.visible], [(2, 100, 4)])
        self.assertFalse(app.follow_age.get())
        self.assertEqual(app.store.states, {'new': 'unknown', 'woods': 'completed'})
        self.assertEqual(app.store.last_success, stamp)
        self.assertEqual(app.store.connection, 'disconnected')
        app.load(dict(updated, seed_id='another-seed'))
        self.assertEqual(app.resource.get(), REGION_VIEWS['KokiriForest']['Child'])
        self.assertTrue(app.follow_age.get())
        self.assertEqual(app.store.states, {'new': 'unknown', 'woods': 'unknown'})
        self.assertIsNone(app.store.last_success)

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

    def test_diagnostic_distinguishes_plan_edges_from_undrawn_checks(self):
        import json
        from pathlib import Path
        from tempfile import TemporaryDirectory
        from unittest.mock import patch

        from PIL import Image, ImageDraw
        from map_oot_rando.aerial import AerialImage

        app = self.app
        doc = demo_document()
        resource = doc['locations'][0]['resource']
        doc['locations'][0]['position'] = (20, 0, 20)
        doc['locations'][1]['position'] = (45, 0, 45)
        doc['locations'][2]['position'] = (105, 0, 50)
        doc['locations'][3].update(position=(150, -6, 92), entrance=(22, 0, 22))
        app.load(doc)
        plan = Image.new('RGB', (100, 100), '#0d1f2e')
        ImageDraw.Draw(plan).rectangle((10, 10, 30, 30), fill='#1f5577')
        points = [(0, 0), (100, 0), (0, 100)]
        app.aerial[resource] = AerialImage(plan, points, points, source='field-atlas-fixture')

        with TemporaryDirectory() as folder:
            path = Path(folder) / 'diagnostic.json'
            with patch('map_oot_rando.gui.filedialog.asksaveasfilename', return_value=path):
                app.save_diagnostic()
            diagnostic = json.loads(path.read_text(encoding='utf-8'))

        self.assertNotIn('aerial', diagnostic)
        self.assertEqual(set(diagnostic['atlas_coverage']), {resource})
        coverage = diagnostic['atlas_coverage'][resource]
        self.assertEqual(coverage['image_size'], [100, 100])
        self.assertEqual(coverage['checked'], 4)
        self.assertEqual([(row['id'], row['pixel'], row['reason']) for row in coverage['outside']],
                         [('SIMULATED#1', [45, 45], 'outside_drawing'),
                          ('SIMULATED#2', [105, 50], 'outside_image')])

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

    def test_import_automatically_loads_field_atlas_over_legacy_preference(self):
        from unittest.mock import patch
        from PIL import Image
        from map_oot_rando.field_atlas import HOUSE_PIXELS
        from map_oot_rando.scene import AGE_VIEWS

        resource = 'Banc/KokiriForest/KokiriForest_Adult_Dynamic.bcett.byml.zs'
        doc = demo_document()
        doc['provenance'] = 'ootrr-scan'
        doc['locations'] = [
            dict(doc['locations'][0], id='adult-check', resource=resource, position=[900, 0, 400]),
            dict(doc['locations'][1], resource=resource.replace('Adult', 'Child')),
        ]
        doc['preferred_background'] = 'questfern-kokiri'
        doc['aerial'] = {resource: {'source': 'questfern-kokiri', 'calibration': 1}}
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

        with patch('map_oot_rando.gui.load_kokiri_image',
                   return_value=Image.new('RGB', (1800, 996), '#1f5577')) as download:
            app.load(doc)
            self.assertEqual(app.resource.get(), AGE_VIEWS['Child'])
            app.query.set('adult-check')
            self.assertIn(AGE_VIEWS['Adult'], app.results.get(0))
            app.choose_first()
            self.assertEqual(app.resource.get(), AGE_VIEWS['Adult'])
            self.root.after(20, wait_for_background)
            deadline = self.root.after(2000, self.root.quit)
            self.root.mainloop()
            self.root.after_cancel(deadline)
            self.assertTrue(app.canvas.find_withtag('aerial'))
            self.assertEqual(app.aerial[app.resource.get()].source, 'field-atlas')
            x, z = app.viewport.screen(app.selected.project())
            self.assertAlmostEqual(x, app.canvas.winfo_width() / 2)
            self.assertAlmostEqual(z, app.canvas.winfo_height() / 2)
            self.assertEqual(app.results.curselection(), (0,))
            download.assert_called_once()

    def test_atlas_uses_world_coordinates_and_a_uniform_canvas(self):
        from PIL import Image
        from map_oot_rando.aerial import AerialImage
        from map_oot_rando.gui import ATLAS_BACKGROUND

        doc = demo_document()
        row = doc['locations'][0]
        a = AerialImage(Image.new('RGB', (200, 160), '#26774a'),
                        [(0, 0), (200, 0), (0, 160)], [(-50, -50), (50, -40), (-40, 50)],
                        source='field-atlas')
        doc['aerial'] = {row['resource']: a.to_document()}
        app = self.app
        app.load(doc)
        app.simulation.change(row['id'], 'unknown')
        app.render()
        loc = next(loc for loc in app.visible if loc.id == row['id'])
        app.choose(loc)
        marker = next(item for item, r in app.markers.items()
                      if r == loc and app.canvas.type(item) == 'oval')
        self.assertEqual(app.canvas.cget('background'), ATLAS_BACKGROUND)
        self.assertEqual(app.canvas.itemcget(marker, 'fill'), COLORS['unknown'])
        x1, y1, x2, y2 = app.canvas.coords(marker)
        self.assertAlmostEqual((x1 + x2) / 2, app.canvas.winfo_width() / 2)
        self.assertAlmostEqual((y1 + y2) / 2, app.canvas.winfo_height() / 2)

    def test_reopens_saved_tracking_profile_only_for_matching_seed(self):
        from pathlib import Path
        from tempfile import TemporaryDirectory
        from unittest.mock import patch
        from map_oot_rando.save_profiles import SaveProfiles

        app = self.app
        doc = demo_document()
        doc.update(provenance='ootrr-scan', seed_id='seed-resume')
        with TemporaryDirectory() as directory:
            tmp = Path(directory).resolve()
            (tmp / 'manifest.json').write_text('{}')
            save = tmp / 'progress.sav'
            save.touch()
            app.save_profiles = SaveProfiles(tmp / 'profiles.json')
            app.save_profiles.remember(doc['seed_id'], tmp, save)
            with patch.object(app, 'follow_save') as follow:
                app.load(doc)
                follow.assert_called_once_with(tmp, tmp, preserve_snapshot=False)
                follow.reset_mock()
                app.store.publish(doc['seed_id'], dict.fromkeys(app.store.states, 'completed'),
                                  mode='save', timestamp='2026-11-24T11:00:00+00:00')
                app.load(doc)
                follow.assert_called_once_with(tmp, tmp, preserve_snapshot=True)
                follow.reset_mock()
                app.stop_tracking()
                app.load(doc)
                follow.assert_not_called()
                app.load(dict(doc, seed_id='another-seed'))
                follow.assert_not_called()

    def test_reopen_map_keeps_follow_link_choice_separate_from_the_marker(self):
        from unittest.mock import patch
        from map_oot_rando.link_position import LinkPosition
        from map_oot_rando.scene import REGION_VIEWS

        forest, woods = 'KokiriForest', 'LostWood'
        forest_view, woods_view = (REGION_VIEWS[region]['Child'] for region in (forest, woods))
        doc = dict(demo_document(), provenance='ootrr-scan', regions=[forest, woods], locations=[],
                   scenes={view: {'rooms': [], 'points': []} for view in (forest_view, woods_view)})
        self.enterContext(patch.object(MapApplication, 'ensure_atlas'))
        app = self.app
        app.load(doc)
        app.link_check.invoke()
        self.assertTrue(app.follow_link.get())
        app.follow_link_check.invoke()
        self.assertFalse(app.follow_link.get())
        self.assertTrue(app.show_link.get())
        self.assertFalse(self.profiles_path.exists())

        app.close_window()
        self.root = tk.Tk()
        self.root.report_callback_exception = lambda *args: self.errors.append(args)
        self.app = app = MapApplication(self.root, doc, profiles=SaveProfiles(self.profiles_path))
        self.root.update()
        self.assertFalse(app.follow_link.get())
        app.link_check.invoke()
        app.update_link(LinkPosition(forest, 'Child', 0, 100, 0, 0))
        self.assertTrue(app.canvas.find_withtag('player-pin'))
        app.update_link(LinkPosition(woods, 'Child', 0, 100, 0, 0))
        self.assertEqual(app.resource.get(), forest_view)
        self.assertIn(woods_view, app.link_status.get())
        self.assertEqual(app.link_zone_button.winfo_manager(), 'pack')
        app.link_zone_button.invoke()
        self.assertEqual(app.resource.get(), woods_view)
        self.assertFalse(app.follow_link.get())
        self.assertTrue(app.canvas.find_withtag('player-pin'))
        app.update_link(LinkPosition(forest, 'Child', 0, 100, 0, 0))
        self.assertEqual(app.resource.get(), woods_view)
        self.assertTrue(app.use_live.is_set())
        self.assertTrue(app.show_link.get())
        app.follow_link_check.invoke()
        self.assertEqual(app.resource.get(), forest_view)
        self.assertTrue(app.canvas.find_withtag('player-pin'))
        self.assertTrue(SaveProfiles(self.profiles_path).follow_link_enabled())
        app.update_link(None)
        self.assertFalse(app.link_zone_button.winfo_manager())

    def test_automatic_reconnect_keeps_snapshot_and_manual_choice_resets_it(self):
        from pathlib import Path
        from unittest.mock import patch

        app = self.app
        app.load(dict(demo_document(), provenance='ootrr-scan', seed_id='choose-another-slot'))
        app.store.publish(app.store.seed_id, dict.fromkeys(app.store.states, 'completed'),
                          mode='save', timestamp='2026-11-24T11:00:00+00:00')
        with patch('map_oot_rando.gui.Thread'), patch.object(app.root, 'after'):
            app.follow_save(Path('.'), Path('.'), preserve_snapshot=True)
            self.assertEqual(set(app.store.states.values()), {'completed'})
            self.assertEqual(app.store.connection, 'disconnected')
            app.follow_save(Path('.'), Path('.'))
        self.assertEqual(set(app.store.states.values()), {'unknown'})
        self.assertIsNone(app.store.last_success)

    def test_follow_age_switches_only_until_user_chooses_a_view(self):
        from map_oot_rando.scene import AGE_VIEWS

        doc = demo_document()
        for row, age in zip(doc['locations'], ('Child', 'Adult')):
            row['resource'] = f'Banc/KokiriForest/KokiriForest_{age}_Dynamic.bcett.byml.zs'
        app = self.app
        app.load(doc)
        app.save_age = 'Adult'
        app.sync_age()
        self.assertEqual(app.resource.get(), AGE_VIEWS['Adult'])
        app.resource.set(AGE_VIEWS['Child'])
        app.resource_changed()
        app.sync_age()
        self.assertEqual(app.resource.get(), AGE_VIEWS['Child'])
        app.follow_age.set(True)
        app.sync_age()
        self.assertEqual(app.resource.get(), AGE_VIEWS['Adult'])

    def test_adjacent_zone_preserves_age_and_shared_check_state(self):
        from PIL import Image
        from map_oot_rando.scene import REGION_VIEWS

        app = self.app
        doc = dict(demo_document(), provenance='ootrr-scan', regions=list(REGION_VIEWS))
        row = doc['locations'][0]
        doc['locations'] = [
            dict(row, resource=f'Banc/{region}/{region}_{age}_Static.bcett.byml.zs')
            for region in REGION_VIEWS for age in ('Child', 'Adult')
        ] + [dict(id='lost-event', name='Lost event', category='npc',
                  region='LostWood', resource='Emplacements sans position', position=None)]
        child_resource = doc['locations'][0]['resource']
        doc['scenes'] = {child_resource: {'rooms': [], 'points': [('front_of_lost_wood_entrance', (10, 20))]}}
        app.load(doc)
        self.assertEqual({r.id for r in app.visible}, {row['id']})
        portal, = app.canvas.find_withtag('zone-navigation')
        left, top, right, bottom = app.canvas.bbox(portal)
        app.press(SimpleNamespace(x=(left + right) // 2, y=(top + bottom) // 2))
        self.assertEqual(app.resource.get(), REGION_VIEWS['LostWood']['Child'])
        self.assertEqual({r.id for r in app.visible}, {row['id'], 'lost-event'})
        self.assertTrue(app.canvas.find_withtag('aerial'))
        app.store.states[row['id']] = 'completed'
        app.save_age = 'Adult'
        app.sync_age()
        self.assertEqual(app.resource.get(), REGION_VIEWS['LostWood']['Adult'])
        app.neighbor_buttons['KokiriForest'].invoke()
        self.assertEqual(app.resource.get(), REGION_VIEWS['KokiriForest']['Adult'])
        self.assertEqual(app.store.states[row['id']], 'completed')

        app.world_image = Image.new('RGB', (600, 436), '#d8c9a3')
        for _ in range(5):
            app.zoom(1 / 1.2, 100, 100)
        self.assertTrue(app.overview_open)
        self.assertTrue(app.canvas.find_withtag('world-map'))
        self.assertIn('Graveyard', app.navigation_markers.values())
        self.assertIn('DeathMountainCrater', app.navigation_markers.values())
        field = next(item for item, name in app.navigation_markers.items() if name == 'HyruleField')
        left, top, right, bottom = app.canvas.bbox(field)
        app.press(SimpleNamespace(x=(left + right) // 2, y=(top + bottom) // 2))
        self.assertEqual(app.resource.get(), REGION_VIEWS['HyruleField']['Adult'])
        self.assertFalse(app.overview_open)

    def test_world_pin_opens_subzone_menu_for_the_selected_age(self):
        from PIL import Image
        from unittest.mock import patch
        from map_oot_rando.link_position import LinkPosition
        from map_oot_rando.scene import REGION_VIEWS

        app = self.app
        all_regions = ('KokiriForest', 'KokiriBridge', 'Market', 'TempleOfTime', 'SageRoom')
        doc = dict(demo_document(), provenance='ootrr-scan', regions=all_regions)
        template = doc['locations'][0]
        doc['locations'] = [
            dict(template, id=f'{region}{age}', resource=f'Banc/{region}/{region}_{age}_Static.bcett.byml.zs',
                 position=(1, 100, 2))
            for region in all_regions[:-1] for age in ('Child', 'Adult')
        ] + [dict(template, id='Sages', resource='Banc/SageRoom/SageRoom_Static.bcett.byml.zs',
                  position=(1, 100, 2))]
        self.enterContext(patch.object(app, 'ensure_atlas'))
        app.load(doc)
        original = app.resource.get()
        app.world_image = Image.new('RGB', (60, 44), '#d8c9a3')
        app.show_world()
        app.age_buttons['Adult'].invoke()
        self.assertTrue(app.overview_open)
        self.assertEqual(app.resource.get(), original)
        item = next(item for item, targets in app.world_menus.items()
                    if [region for region, _ in targets] == ['Market', 'TempleOfTime', 'SageRoom'])
        left, top, right, bottom = app.canvas.bbox(item)
        with patch.object(app, 'post_marker_menu'):
            app.press(SimpleNamespace(x=(left+right)//2, y=(top+bottom)//2, x_root=100, y_root=100))
        self.assertEqual(app.marker_menu.entrycget(1, 'label'), 'Temple du Temps')
        app.marker_menu.invoke(1)
        self.assertFalse(app.overview_open)
        self.assertEqual(app.resource.get(), REGION_VIEWS['TempleOfTime']['Adult'])
        app.follow_link.set(False)
        app.show_world()
        app.age_buttons['Child'].invoke()
        app.update_link(LinkPosition('SageRoom', 'Adult', 0, 100, 0, 0))
        self.assertTrue(app.overview_open)
        ring, _ = app.canvas.find_withtag('player-pin')
        left, top, right, bottom = app.canvas.bbox(ring)
        event = SimpleNamespace(x=(left+right)//2, y=(top+bottom)//2)
        app.world_hover(event)
        self.assertEqual(app.canvas.itemcget('world-heading', 'text'), 'Link · Chambre des Sages')
        app.press(event)
        self.assertFalse(app.overview_open)
        self.assertEqual(app.resource.get(), REGION_VIEWS['SageRoom'][None])
        self.assertFalse(app.follow_link.get())
        self.assertTrue(app.canvas.find_withtag('player-pin'))

    def test_kakariko_story_variant_stays_separate_and_follows_snapshot(self):
        from map_oot_rando.scene import BURNT_VILLAGE, REGION_VIEWS

        app = self.app
        doc = dict(demo_document(), provenance='ootrr-scan', regions=list(REGION_VIEWS))
        prefix = 'Banc/KakarikoVillage/KakarikoVillage_'
        doc['locations'] = [
            dict(row, resource=prefix + suffix + '.bcett.byml.zs')
            for row, suffix in zip(doc['locations'], ('Adult_Static', 'Adult_Alternative_Dynamic'))
        ]
        app.load(doc)
        self.assertEqual(app.resource.get(), REGION_VIEWS['KakarikoVillage']['Adult'])
        self.assertEqual({r.id for r in app.visible}, {doc['locations'][0]['id']})
        app.save_age = 'Adult'
        app.kakariko_burned = True
        app.sync_age()
        self.assertEqual(app.resource.get(), BURNT_VILLAGE)
        self.assertEqual({r.id for r in app.visible}, {doc['locations'][1]['id']})
        app.kakariko_burned = False
        app.sync_age()
        self.assertEqual(app.resource.get(), REGION_VIEWS['KakarikoVillage']['Adult'])

    def test_graveyard_floor_filters_checks_and_search_opens_the_right_floor(self):
        from map_oot_rando.scene import REGION_VIEWS, UNDERGROUND_VIEWS

        app = self.app
        doc = dict(demo_document(), provenance='ootrr-scan', regions=list(REGION_VIEWS))
        resource = 'Banc/Graveyard/Graveyard_Child_Static.bcett.byml.zs'
        surface, buried = doc['locations'][:2]
        doc['locations'] = [dict(surface, resource=resource),
                            dict(buried, resource=resource, underground=True)]
        app.load(doc)
        self.assertEqual({row.id for row in app.visible}, {surface['id']})
        app.floor_button.invoke()
        self.assertEqual(app.resource.get(), UNDERGROUND_VIEWS['Graveyard']['Child'])
        self.assertEqual({row.id for row in app.visible}, {buried['id']})
        app.floor_button.invoke()
        self.assertEqual(app.resource.get(), REGION_VIEWS['Graveyard']['Child'])
        app.query.set(buried['id'])
        app.choose_first()
        self.assertEqual(app.resource.get(), UNDERGROUND_VIEWS['Graveyard']['Child'])
        self.assertEqual(app.selected.id, buried['id'])

    def test_goron_floor_picker_keeps_age_and_tracker_following(self):
        from map_oot_rando.scene import GORON_LEVELS, GORON_VIEWS, REGION_VIEWS

        app = self.app
        doc = dict(demo_document(), provenance='ootrr-scan', regions=list(REGION_VIEWS))
        row = doc['locations'][0]
        doc['locations'] = [
            dict(row, id=f'{age}-{level}', position=(0, height, 0),
                 resource=f'Banc/GoronCity/GoronCity_{age}_Static.bcett.byml.zs')
            for age in ('Child', 'Adult')
            for level, height in enumerate((114, 110.8, 103.3, 98.4, 94.8))
        ]
        app.load(doc)
        self.assertEqual(app.resource.get(), GORON_VIEWS['Child'][0])
        self.assertEqual(tuple(app.floor_picker['values']), GORON_LEVELS)
        app.floor_picker.set(GORON_LEVELS[2])
        app.choose_floor(None)
        self.assertEqual({row.id for row in app.visible}, {'Child-2'})
        app.save_age = 'Adult'
        app.sync_age()
        self.assertEqual(app.resource.get(), GORON_VIEWS['Adult'][2])
        self.assertEqual({row.id for row in app.visible}, {'Adult-2'})

    def test_dodongo_shared_floors_follow_age_only_on_exit(self):
        from map_oot_rando.scene import DODONGO_LEVELS, DODONGO_VIEWS, REGION_VIEWS

        app = self.app
        doc = dict(demo_document(), provenance='ootrr-scan', regions=list(REGION_VIEWS))
        row = doc['locations'][0]
        doc['locations'] = [
            dict(row, id=f'dodongo-{index}', position=(0, height, 0),
                 resource='Banc/DodongoCavern/DodongoCavern_Static.bcett.byml.zs')
            for index, height in enumerate((100, 113, 73))
        ] + [
            dict(row, id=age, resource=f'Banc/DeathMountainTrail/DeathMountainTrail_{age}_Static.bcett.byml.zs')
            for age in ('Child', 'Adult')
        ]
        app.load(doc)
        app.resource.set(REGION_VIEWS['DeathMountainTrail']['Adult'])
        app.resource_changed()
        app.open_neighbor('DodongoCavern')
        self.assertEqual(app.resource.get(), DODONGO_VIEWS[0])
        app.floor_picker.set(DODONGO_LEVELS[2])
        app.choose_floor(None)
        self.assertEqual({row.id for row in app.visible}, {'dodongo-2'})
        self.assertEqual(app.view_for_region('DeathMountainTrail'), REGION_VIEWS['DeathMountainTrail']['Adult'])
        app.save_age = 'Child'
        app.sync_age()
        self.assertEqual(app.resource.get(), DODONGO_VIEWS[2])
        app.open_neighbor('DeathMountainTrail')
        self.assertEqual(app.resource.get(), REGION_VIEWS['DeathMountainTrail']['Child'])

    def test_adult_windmill_opens_the_graveyard_underground_view(self):
        from unittest.mock import patch
        from map_oot_rando.link_position import LinkPosition
        from map_oot_rando.scene import DAMPE_ROUTES, REGION_VIEWS, UNDERGROUND_VIEWS, extract_scenes

        app = self.app
        village, graveyard = 'KakarikoVillage', 'Graveyard'
        names = {village: 'KakarikoWindmill_GraveYardSide', graveyard: 'GraveYard_KakarikoWindmillSide'}
        gates = {village: (29, 113, 44), graveyard: (-41, 99, 78)}
        spawns = {village: (13, 108, 44), graveyard: (-29, 88, 78)}
        maps = {f'Banc/{region}/{region}_Adult_Static.bcett.byml.zs': {'root': {'Actors': [
            dict(Gyaml='FieldAndDungeonEntranceEventRequestActor', Name=names[region], Translate=gates[region]),
            dict(Gyaml='StartPos', Name=names[region], Translate=spawns[region]),
        ]}} for region in names}
        tomb = maps[f'Banc/{graveyard}/{graveyard}_Adult_Static.bcett.byml.zs']['root']
        tomb['Actors'].append(dict(Gyaml='Npc_Hylia_Dampe_002', Rails=[dict(Dst=1), dict(Dst=2)]))
        tomb['Rails'] = [
            dict(Name='Playing', Gyaml='Guide', Hash=1, Points=[dict(Translate=point)
                 for point in ((22, 79, -11), (34, 81, 0), (12, 82, 57))]),
            dict(Name='PlayingSecond', Gyaml='Guide', Hash=2, Points=[dict(Translate=point)
                 for point in ((22, 79, -11), (40, 80, 5), (12, 82, 57))]),
            dict(Name='Playing', Gyaml='Guide', Hash=3, Points=[dict(Translate=point)
                 for point in ((0, 99, 0), (0, 99, 40))]),
        ]
        scenes = extract_scenes(maps, lambda _: {})
        scenes[REGION_VIEWS[village]['Child']] = {'rooms': [], 'points': []}
        doc = dict(demo_document(), provenance='ootrr-scan', regions=['KokiriForest', village, graveyard],
                   locations=[], scenes=scenes)
        self.enterContext(patch.object(app, 'ensure_atlas'))
        app.load(doc)
        self.assertEqual(app.resource.get(), REGION_VIEWS[village]['Child'])
        self.assertFalse(app.canvas.find_withtag('zone-navigation'))
        app.age_buttons['Adult'].invoke()
        self.assertFalse(app.canvas.find_withtag('scene-route'))

        def cross(target):
            marker, = app.canvas.find_withtag('zone-navigation')
            left, top, right, bottom = app.canvas.bbox(marker)
            self.assertEqual(app.navigation_markers[marker], target)
            app.press(SimpleNamespace(x=(left+right)//2, y=(top+bottom)//2))
            line, = app.canvas.find_withtag('portal-approach')
            x, _, z = spawns[target]
            self.assertEqual(tuple(app.canvas.coords(line)[-2:]), app.viewport.screen((x, z)))

        cross(graveyard)
        self.assertEqual(app.resource.get(), UNDERGROUND_VIEWS[graveyard]['Adult'])
        self.assertEqual([app.canvas.itemcget(item, 'text') for item in app.canvas.find_withtag('race-legend')],
                         list(DAMPE_ROUTES.values()))
        route_items = app.canvas.find_withtag('scene-route')
        self.assertEqual(len(route_items), 4)
        self.assertNotEqual(app.canvas.itemcget(route_items[-2], 'fill'), app.canvas.itemcget(route_items[-1], 'fill'))
        self.assertTrue(app.canvas.itemcget(route_items[-1], 'dash'))
        app.update_link(LinkPosition(graveyard, 'Adult', *spawns[graveyard], 0))
        self.assertTrue(app.canvas.find_withtag('player-pin'))
        cross(village)
        self.assertEqual(app.resource.get(), REGION_VIEWS[village]['Adult'])

    def test_dampe_grave_links_the_surface_to_its_underground_entrance(self):
        from unittest.mock import patch
        from map_oot_rando.scene import REGION_VIEWS, UNDERGROUND_VIEWS, extract_scenes

        app = self.app
        region = 'Graveyard'
        surface = REGION_VIEWS[region]['Adult']
        underground = UNDERGROUND_VIEWS[region]['Adult']
        path = f'Banc/{region}/{region}_Adult_Static.bcett.byml.zs'
        anchors = [
            ('HidingHole_FieldEntranceGo', 14429999406297140688, (-4, 103, -11)),
            ('HidingHole_FieldExitGo', 13508899304624178854, (-4, 84, -11)),
            ('HidingHole_HoleExit', 16657254736794208888, (-4, 103, -11)),
            ('HidingHole_HoleEntrance', 6836600866498450360, (-4, 87, -11)),
            ('HidingHole_FieldEntranceGo', 100, (-40, 103, -50)),
        ]
        root = {'Actors': [dict(Gyaml='DestinationAnchor', Name=name, Hash=ident, Translate=point)
                           for name, ident, point in anchors]}
        scenes = extract_scenes({p: {'root': root} for p in (path, path.replace('_Adult_', '_Child_'))}, lambda _: {})
        scenes.setdefault(path.replace('_Adult_', '_Child_'), {'rooms': [], 'points': []})
        doc = dict(demo_document(), provenance='ootrr-scan', regions=['KokiriForest', region],
                   locations=[], scenes=scenes)
        self.enterContext(patch.object(app, 'ensure_atlas'))
        app.load(doc)
        self.assertEqual(app.resource.get(), REGION_VIEWS[region]['Child'])
        self.assertFalse(app.canvas.find_withtag('zone-navigation'))
        app.age_buttons['Adult'].invoke()
        self.assertEqual(app.resource.get(), surface)
        for target in (underground, surface):
            marker, = app.canvas.find_withtag('zone-navigation')
            left, top, right, bottom = app.canvas.bbox(marker)
            app.press(SimpleNamespace(x=(left+right)//2, y=(top+bottom)//2))
            self.assertEqual(app.resource.get(), target)
            ring, = app.canvas.find_withtag('portal-arrival')
            left, top, right, bottom = app.canvas.coords(ring)
            self.assertEqual(((left+right)/2, (top+bottom)/2), app.viewport.screen((-4, -11)))

    def test_crater_link_returns_to_goron_ground_floor(self):
        from map_oot_rando.scene import GORON_CRATER_FLOOR, GORON_VIEWS, REGION_VIEWS

        app = self.app
        doc = dict(demo_document(), provenance='ootrr-scan', regions=list(REGION_VIEWS))
        row = doc['locations'][0]
        crater = 'Banc/DeathMountainCrater/DeathMountainCrater_Adult_Static.bcett.byml.zs'
        goron = 'Banc/GoronCity/GoronCity_Adult_Static.bcett.byml.zs'
        doc['locations'] = [dict(row, resource=crater)]
        goron_spawn = (-0.15, -47.35)
        crater_exit = (-55, -20)
        doc['scenes'] = {
            crater: {'rooms': [], 'points': [('goron_city_entrance', crater_exit)]},
            goron: {'rooms': [], 'points': [('Repère nord Goron', (10, 15)), ('GoronCity_CraterSide', goron_spawn)]},
        }
        app.load(doc)
        app.resource.set(REGION_VIEWS['DeathMountainCrater']['Adult'])
        app.resource_changed()
        x, y = app.viewport.screen(crater_exit)
        app.press(SimpleNamespace(x=round(x), y=round(y)))
        self.assertEqual(app.resource.get(), GORON_VIEWS['Adult'][GORON_CRATER_FLOOR])
        self.assertEqual(set(app.navigation_markers.values()), {'DeathMountainCrater'})
        line, = app.canvas.find_withtag('portal-approach')
        self.assertEqual(tuple(app.canvas.coords(line)[-2:]), app.viewport.screen(goron_spawn))

    def test_fire_temple_groups_layers_and_retains_empty_floor(self):
        from unittest.mock import patch
        from map_oot_rando.scene import FIRE_LEVELS, FIRE_VIEWS, REGION_VIEWS

        app = self.app
        load_background = self.enterContext(patch.object(app, 'ensure_atlas'))
        doc = dict(demo_document(), provenance='ootrr-scan', regions=list(REGION_VIEWS))
        row = doc['locations'][0]
        crater = 'Banc/DeathMountainCrater/DeathMountainCrater_Adult_Static.bcett.byml.zs'
        fire = 'Banc/FireTemple/FireTemple_{}.bcett.byml.zs'
        doc['locations'] = [
            dict(row, id='crater', resource=crater),
            dict(row, id='lower', resource=fire.format('Static'), position=(77, 141.1, 0)),
            dict(row, id='upper', resource=fire.format('Dynamic'), position=(8, 145, 0)),
            dict(row, id='boss#Volvagia', resource=fire.format('Static'), position=(-80, 102, 0)),
            dict(row, id='boss-heart', category='full_bossheart',
                 resource=fire.format('Dynamic'), position=(-76, 102, 0)),
        ]
        doc['scenes'] = {fire.format('Dynamic'): {'rooms': [], 'points': [('Vers le cratère', (0, 29.65))]}}
        app.load(doc)
        app.resource.set(REGION_VIEWS['DeathMountainCrater']['Adult'])
        app.resource_changed()
        app.open_neighbor('FireTemple')
        self.assertEqual(app.resource.get(), FIRE_VIEWS[0])
        self.assertEqual(tuple(app.floor_picker['values']), FIRE_LEVELS)
        self.assertEqual(set(app.navigation_markers.values()), {'DeathMountainCrater'})
        for floor, ids in [(1, {'lower'}), (2, {'upper'}), (3, set()),
                           (5, {'boss#Volvagia', 'boss-heart'})]:
            load_background.reset_mock()
            app.floor_picker.set(FIRE_LEVELS[floor])
            app.choose_floor(None)
            self.assertEqual({item.id for item in app.visible}, ids)
            load_background.assert_called_once_with()
        app.open_neighbor('DeathMountainCrater')
        self.assertEqual(app.resource.get(), REGION_VIEWS['DeathMountainCrater']['Adult'])

    def test_lost_woods_shortcuts_and_age_buttons(self):
        from unittest.mock import patch
        from map_oot_rando.scene import GORON_LOST_WOODS_FLOOR, GORON_VIEWS, LOST_WOOD_RESET, NEIGHBORS, REGION_VIEWS

        app = self.app
        regions = ('KokiriForest', 'LostWood', 'GoronCity', 'ZoraRiver', 'HyruleField', 'ZoraDomain', 'ZoraFountain')

        def resource(region, age):
            return f'Banc/{region}/{region}_{age}_Static.bcett.byml.zs'

        doc = dict(demo_document(), provenance='ootrr-scan', regions=list(regions), locations=[])
        points = {
            'KokiriForest': [('front_of_lost_wood_entrance', (0, 0)), ('KokiriForest_FrontOfLostWood', (0, 5))],
            'LostWood': [('Vers le Village Goron', (24, -35.66)), ('Vers la Rivière Zora', (68.5, -25.6)),
                         (LOST_WOOD_RESET, (0, -9.5)),
                         ('LostWood_ZoraRiverSide', (64.5, -25.6)),
                         ('LostWood_GoronCitySide_before', (24, -29.15)),
                         ('LostWood_GoronCitySide_after', (24, -29.15))],
            'GoronCity': [('Repère des Bois Perdus', (26.7, -3.18)),
                          ('GoronCity_LostWoodSide_before', (21.7, -2.54)),
                          ('GoronCity_LostWoodSide_after', (15.2, -1.39))],
            'ZoraRiver': [('Vers les Bois Perdus', (122.57, -11.8)), ('Vers la plaine d’Hyrule', (-98, 28)),
                          ('Vers le Domaine Zora', (150, -40)), ('ZoraRiver_LostWoodSide', (122.57, -14.09))],
            'HyruleField': [('Vers la Rivière Zora', (211, 148))],
            'ZoraDomain': [('Vers la Rivière Zora', (3.54, -42.38)), ('Vers la Fontaine Zora', (92.58, 15.57))],
            'ZoraFountain': [('Vers le Domaine Zora', (-19, -24.54))],
        }
        doc['scenes'] = {resource(region, age): {'rooms': [], 'points': points[region]}
                         for region in points for age in ('Child', 'Adult')}
        self.enterContext(patch.object(app, 'ensure_atlas'))
        app.load(doc)
        app.open_neighbor('LostWood')
        self.assertEqual(app.zones.get(), 'Bois Perdus')
        self.assertIn('Village Goron', app.zones['values'])
        self.assertFalse(any('Adulte' in label for label in app.zones['values']))
        app.age_buttons['Adult'].invoke()
        self.assertEqual(app.resource.get(), REGION_VIEWS['LostWood']['Adult'])

        def click_portal(target):
            exits = app.canvas.find_withtag('zone-navigation')
            pin = next(item for item in exits if app.navigation_markers[item] == target)
            l, t, r, b = app.canvas.bbox(pin)
            app.press(SimpleNamespace(x=(l+r)//2, y=(t+b)//2))

        def check_spawns(*points):
            lines = app.canvas.find_withtag('portal-approach')
            self.assertEqual({tuple(app.canvas.coords(line)[-2:]) for line in lines},
                             {app.viewport.screen(point) for point in points})
            self.assertEqual(len(app.canvas.find_withtag('portal-arrival')), len(points))

        for target, view in [('GoronCity', GORON_VIEWS['Adult'][GORON_LOST_WOODS_FLOOR]),
                             ('ZoraRiver', REGION_VIEWS['ZoraRiver']['Adult'])]:
            click_portal(target)
            self.assertEqual(app.resource.get(), view)
            self.assertIn('LostWood', app.navigation_markers.values())
            self.assertEqual(app.arrival, NEIGHBORS[target]['LostWood'])
            self.assertTrue(app.canvas.find_withtag('portal-arrival'))
            if target == 'ZoraRiver':
                check_spawns((122.57, -14.09))
                self.assertIn('HyruleField', app.navigation_markers.values())
                app.open_neighbor('HyruleField')
                self.assertEqual(app.resource.get(), REGION_VIEWS['HyruleField']['Adult'])
                self.assertIn('ZoraRiver', app.navigation_markers.values())
                app.open_neighbor('ZoraRiver')
                self.assertIn('ZoraDomain', app.navigation_markers.values())
                app.open_neighbor('ZoraDomain')
                self.assertEqual(app.resource.get(), REGION_VIEWS['ZoraDomain']['Adult'])
                self.assertIn('ZoraRiver', app.navigation_markers.values())
                self.assertIn('ZoraFountain', app.navigation_markers.values())
                app.open_neighbor('ZoraFountain')
                self.assertEqual(app.resource.get(), REGION_VIEWS['ZoraFountain']['Adult'])
                self.assertIn('ZoraDomain', app.navigation_markers.values())
                app.open_neighbor('ZoraDomain')
                app.open_neighbor('ZoraRiver')
            else:
                check_spawns((21.7, -2.54), (15.2, -1.39))
            click_portal('LostWood')
            self.assertEqual(app.resource.get(), REGION_VIEWS['LostWood']['Adult'])
            self.assertEqual(app.arrival, NEIGHBORS['LostWood'][target])
            self.assertTrue(app.canvas.find_withtag('portal-arrival'))
            if target == 'ZoraRiver':
                check_spawns((64.5, -25.6))
            else:
                check_spawns((24, -29.15))

        reset, = app.canvas.find_withtag('lost-wood-reset')
        x, y = app.canvas.coords(reset)
        app.press(SimpleNamespace(x=round(x), y=round(y)))
        self.assertEqual(app.resource.get(), REGION_VIEWS['KokiriForest']['Adult'])
        check_spawns((0, 5))

    def test_kokiri_bridge_routes_field_and_link_to_the_right_scene_view(self):
        from unittest.mock import patch
        from map_oot_rando.link_position import LinkPosition
        from map_oot_rando.lost_woods import kokiri_bridge_plan, lost_woods_plan
        from map_oot_rando.metadata import add_surface_entrances
        from map_oot_rando.scene import NEIGHBORS, REGION_VIEWS, location_view

        app = self.app
        forest, bridge, woods, field = 'KokiriForest', 'KokiriBridge', 'LostWood', 'HyruleField'
        forest_path, woods_path, field_path = (
            f'Banc/{region}/{region}_Child_Static.bcett.byml.zs' for region in (forest, woods, field))
        chest = 'LostWood#17479747339356189279'
        grotto = 'KokiriForest#14818888396401495482'
        template = demo_document()
        locations = [
            dict(template['locations'][0], id=chest, region=forest, resource=forest_path,
                 position=(-132.18, 123.89, -16.01)),
            dict(template['locations'][0], id=chest, region=woods, resource=woods_path,
                 position=(-49.40, 104.53, 71.85)),
            dict(template['locations'][0], id=grotto, region=forest, resource=forest_path,
                 position=(-70.84, 103.58, -63.39)),
        ]
        entrance = (-51.93, 121.57, -62.82)
        cover = dict(Hash=389687166017056250, Gyaml='Land_Kokiri_HidingHoleCover_A_01', Translate=entrance)
        add_surface_entrances(locations, {forest_path: {'root': {'Actors': [cover]}}})
        bridge_door, bridge_spawn = (-127.94, -38.36), (-126.50, -38.40)
        field_door, field_spawn = (200.10, 309.06), (198.22, 309.55)
        doc = dict(template, provenance='ootrr-scan', regions=[forest, woods, field],
                   locations=locations, scenes={
                       forest_path: {'rooms': [], 'points': [(NEIGHBORS[forest][field], bridge_door),
                                                             ('LostWoodBridge_FrontOfHyruleField', bridge_spawn)]},
                       field_path: {'rooms': [], 'points': [(NEIGHBORS[field][forest], field_door),
                                                            ('HyruleField_FrontOfLostWoodBridge', field_spawn)]},
                   })
        self.enterContext(patch.object(app, 'ensure_atlas'))
        app.load(doc)
        first, duplicate, underground = app.locations
        self.assertEqual(location_view(first), REGION_VIEWS[bridge]['Child'])
        self.assertEqual(location_view(duplicate), REGION_VIEWS[woods]['Child'])
        self.assertEqual(location_view(underground), REGION_VIEWS[forest]['Child'])
        self.assertEqual(underground.entrance, entrance)
        self.assertEqual(underground.position, (-70.84, 103.58, -63.39))
        self.assertTrue(kokiri_bridge_plan().covers(first.project()))
        self.assertTrue(all(lost_woods_plan().covers(point) for point in
                            (duplicate.project(), (-45.24, 72.55), (-33.19, 31.42))))
        app.update_link(LinkPosition(field, 'Child', 199, 163, 309, 0))
        def click_door(point, arrival):
            x, y = app.viewport.screen(point)
            app.press(SimpleNamespace(x=round(x), y=round(y)))
            line, = app.canvas.find_withtag('portal-approach')
            self.assertEqual(tuple(app.canvas.coords(line)[-2:]), app.viewport.screen(arrival))

        click_door(field_door, bridge_spawn)
        self.assertEqual(app.resource.get(), REGION_VIEWS[bridge]['Child'])
        self.assertIn(field, app.navigation_markers.values())
        self.assertIn(forest, app.navigation_markers.values())
        click_door(bridge_door, field_spawn)
        self.assertEqual(app.resource.get(), REGION_VIEWS[field]['Child'])
        app.update_link(LinkPosition(forest, 'Child', -126, 114, -38, 0))
        self.assertTrue(app.canvas.find_withtag('player-pin'))
        app.update_link(LinkPosition(forest, 'Child', -80, 115, -39, 0))
        self.assertEqual(app.resource.get(), REGION_VIEWS[forest]['Child'])
        self.assertIn(bridge, app.navigation_markers.values())

    def test_link_pin_and_zone_follow_can_be_used_independently(self):
        from dataclasses import replace
        from unittest.mock import patch
        from map_oot_rando.link_position import LinkPosition
        from map_oot_rando.scene import REGION_VIEWS

        app = self.app
        regions = ('KokiriForest', 'LostWood', 'HyruleField')
        doc = dict(demo_document(), provenance='ootrr-scan', regions=list(regions), locations=[])
        doc['scenes'] = {f'Banc/{region}/{region}_Child_Static.bcett.byml.zs':
                         {'rooms': [], 'points': [('Centre', (0, 0))]} for region in regions}
        self.enterContext(patch.object(app, 'ensure_atlas'))
        app.load(doc)
        app.show_link.set(True)
        app.configure_link()
        self.assertTrue(app.live_requested.get())
        self.assertTrue(app.use_live.is_set())
        self.assertIn('dossier de sauvegardes', app.link_status.get())
        sample = LinkPosition('KokiriForest', 'Child', 0, 100, 0, 90)
        app.update_link(sample)
        self.assertTrue(app.canvas.find_withtag('player-pin'))
        app.update_link(replace(sample, scene='LostWoods'))
        self.assertEqual(app.resource.get(), REGION_VIEWS['LostWood']['Child'])
        app.follow_link.set(False)
        app.update_link(replace(sample, scene='HyruleField'))
        self.assertEqual(app.current_region(), 'LostWood')
        self.assertFalse(app.canvas.find_withtag('player-pin'))
        app.open_neighbor('HyruleField')
        self.assertTrue(app.canvas.find_withtag('player-pin'))
        app.live_requested.set(False)
        app.configure_live()
        self.assertFalse(app.canvas.find_withtag('player-pin'))
        self.assertIn('dossier de sauvegardes', app.link_status.get())

    def test_ice_cavern_has_one_view_and_uses_adult_fountain_portal(self):
        from unittest.mock import patch
        from map_oot_rando.scene import (FOUNTAIN_ICE_BACKDOOR, ICE_CAVERN_BACKDOOR,
                                        NEIGHBORS, REGION_VIEWS, extract_scenes)

        app = self.app
        fountain, cavern = 'ZoraFountain', 'IceCavern'
        doc = dict(demo_document(), provenance='ootrr-scan', locations=[], regions=['KokiriForest', fountain, cavern])
        native = f'Banc/{fountain}/{fountain}_{{}}_Static.bcett.byml.zs'
        maps = {
            native.format('Adult'): {'root': {'Actors': [
                dict(Gyaml='FieldAndDungeonEntranceEventRequestActor', Name='ZoraFountain_FromIceCavern',
                     Translate=(47, 120, -70)),
                dict(Gyaml='FieldAndDungeonEntranceEventRequestActor', Name='ZoraFountain_FromIceCavern_Backdoor',
                     Translate=(53, 99, -56)),
                dict(Gyaml='StartPos', Name='ZoraFountain_FromIceCavern', Translate=(47, 108, -63)),
                dict(Gyaml='StartPos', Name='ZoraFountain_FromIceCavern_Backdoor', Translate=(42, 88, -54)),
            ]}},
            f'Banc/{cavern}/{cavern}_Dynamic.bcett.byml.zs': {'root': {'Actors': [
                dict(Gyaml='MapIconEntranceAnchor', Dynamic={'Location': fountain}, Translate=(17, 102, 105)),
                dict(Gyaml='MapIconEntranceAnchor', Hash=17335166050006259965, Translate=(-48, 97, 78)),
                dict(Gyaml='StartPos', Name='IceCavern_FromZoraFountain', Translate=(17, 102, 99)),
                dict(Gyaml='StartPos', Name='IceCavern_FromZoraFountain_Backdoor', Translate=(-47, 98, 69)),
            ]}},
        }
        doc['scenes'] = extract_scenes(maps, lambda _: {})
        doc['scenes'][native.format('Child')] = {'rooms': [], 'points': [('Rive', (0, 0))]}
        self.enterContext(patch.object(app, 'ensure_atlas'))
        app.load(doc)
        self.assertNotIn(cavern, app.available_neighbors())
        self.assertNotIn(cavern, app.navigation_markers.values())
        self.assertIn(cavern, app.world_targets())
        app.age_buttons['Adult'].invoke()

        def click_portal(target, arrival, spawn):
            marker, = (item for item in app.canvas.find_withtag('zone-navigation')
                       if any(action[1] == target and action[3] == arrival for action in app.local_portals[item]))
            left, top, right, bottom = app.canvas.bbox(marker)
            app.press(SimpleNamespace(x=(left+right)//2, y=(top+bottom)//2))
            line, = app.canvas.find_withtag('portal-approach')
            self.assertEqual(tuple(app.canvas.coords(line)[-2:]), app.viewport.screen(spawn))

        for to_cavern, to_fountain, cavern_spawn, fountain_spawn in (
                (NEIGHBORS[cavern][fountain], NEIGHBORS[fountain][cavern], (17, 99), (47, -63)),
                (ICE_CAVERN_BACKDOOR, FOUNTAIN_ICE_BACKDOOR, (-47, 69), (42, -54))):
            click_portal(cavern, to_cavern, cavern_spawn)
            self.assertEqual(app.resource.get(), REGION_VIEWS[cavern][None])
            self.assertFalse(app.floor_picker.winfo_ismapped())
            click_portal(fountain, to_fountain, fountain_spawn)
            self.assertEqual(app.resource.get(), REGION_VIEWS[fountain]['Adult'])

    def test_castle_child_passage_and_courtyard_survive_following_age(self):
        from unittest.mock import patch
        from map_oot_rando.scene import CASTLE_COURT, CASTLE_OUTSKIRTS, REGION_VIEWS

        app = self.app
        template = demo_document()
        doc = dict(template, provenance='ootrr-scan', regions=['KokiriForest', 'Market', 'HyruleCastle'])
        market = 'Banc/Market/Market_{}_Static.bcett.byml.zs'
        castle = 'Banc/HyruleCastle/HyruleCastle_Static.bcett.byml.zs'
        doc['locations'] = [dict(template['locations'][0], id='letter', resource=castle, position=(5, 128, -256))]
        doc['scenes'] = {
            market.format('Child'): {'rooms': [], 'points': [('Vers le Château d’Hyrule', (-2, -36))]},
            market.format('Adult'): {'rooms': [], 'points': [('Place', (-2, -36))]},
            castle: {'rooms': [], 'points': [('Vers la Citadelle d’Hyrule', (12, -10))]},
        }
        self.enterContext(patch.object(app, 'ensure_atlas'))
        app.load(doc)
        app.age_buttons['Adult'].invoke()
        self.assertNotIn('HyruleCastle', app.available_neighbors())
        self.assertIn('HyruleCastle', app.world_targets())
        app.age_buttons['Child'].invoke()
        app.open_neighbor('HyruleCastle')
        self.assertEqual(app.resource.get(), CASTLE_OUTSKIRTS)
        self.assertIn('Market', app.navigation_markers.values())
        self.assertTrue(app.age_buttons['Adult'].instate(['disabled']))
        app.floor_picker.set('Cour')
        app.choose_floor(None)
        app.save_age = 'Child'
        app.sync_age()
        self.assertEqual(app.resource.get(), CASTLE_COURT)
        self.assertEqual([row.id for row in app.visible], ['letter'])
        app.open_neighbor('Market')
        self.assertEqual(app.resource.get(), REGION_VIEWS['Market']['Child'])

    def test_shared_gerudo_check_search_keeps_the_current_age_and_return_route(self):
        from unittest.mock import patch
        from map_oot_rando.scene import REGION_VIEWS

        app = self.app
        template = demo_document()
        doc = dict(template, provenance='ootrr-scan', regions=['KokiriForest', 'HyruleField', 'GerudoValley'])
        valley = 'Banc/GerudoValley/GerudoValley_{}_Dynamic.bcett.byml.zs'
        field = 'Banc/HyruleField/HyruleField_{}_Static.bcett.byml.zs'
        doc['locations'] = [
            dict(template['locations'][0], id='shared-grotto', name='Grotto Chest',
                 resource=valley.format(age), position=(31, -22, 37), entrance=(11, 90, 36))
            for age in ('Adult', 'Child')
        ]
        doc['scenes'] = {
            **{field.format(age): {'rooms': [], 'points': [('Vers la Vallée Gerudo', (-312, 163))]}
               for age in ('Adult', 'Child')},
            **{valley.format(age): {'rooms': [], 'points': [('Vers la plaine d’Hyrule', (79, 30))]}
               for age in ('Adult', 'Child')},
        }
        self.enterContext(patch.object(app, 'ensure_atlas'))
        app.load(doc)
        app.resource.set(REGION_VIEWS['HyruleField']['Child'])
        app.resource_changed()
        self.assertIn('GerudoValley', app.navigation_markers.values())
        app.open_neighbor('GerudoValley')
        app.query.set('shared-grotto')
        self.assertEqual(len(app.visible), 2)
        self.assertIn(REGION_VIEWS['GerudoValley']['Adult'], app.results.get(0))
        self.assertIn('grotte', app.results.get(0))
        app.choose_first()
        self.assertEqual(app.selected.resource, valley.format('Child'))
        self.assertEqual(app.resource.get(), REGION_VIEWS['GerudoValley']['Child'])
        app.open_neighbor('HyruleField')
        self.assertEqual(app.resource.get(), REGION_VIEWS['HyruleField']['Child'])

    def test_gerudo_fortress_portal_only_opens_as_adult(self):
        from unittest.mock import patch
        from map_oot_rando.scene import REGION_VIEWS

        app = self.app
        valley = 'GerudoValley'
        fortress = 'GerudoFortress'
        doc = dict(demo_document(), provenance='ootrr-scan', regions=['KokiriForest', valley, fortress],
                   locations=[], scenes={
                       'Banc/GerudoValley/GerudoValley_Child_Static.bcett.byml.zs':
                           {'rooms': [], 'points': [('Vers la Forteresse Gerudo', (-67, -6))]},
                       'Banc/GerudoValley/GerudoValley_Adult_Static.bcett.byml.zs':
                           {'rooms': [], 'points': [('Vers la Forteresse Gerudo', (-67, -6))]},
                       'Banc/GerudoFortress/GerudoFortress_Adult_Static.bcett.byml.zs':
                           {'rooms': [], 'points': [('Vers la Vallée Gerudo', (-31, -16))]},
                   })
        self.enterContext(patch.object(app, 'ensure_atlas'))
        app.load(doc)
        app.resource.set(REGION_VIEWS[valley]['Child'])
        app.resource_changed()
        self.assertNotIn(fortress, app.navigation_markers.values())
        self.assertIn(fortress, app.world_targets())
        app.choose_age('Adult')
        self.assertIn(fortress, app.navigation_markers.values())
        app.open_neighbor(fortress)
        self.assertEqual(app.resource.get(), REGION_VIEWS[fortress]['Adult'])
        self.assertTrue(app.age_buttons['Child'].instate(['disabled']))
        self.assertIn(valley, app.navigation_markers.values())
        app.open_neighbor(valley)
        self.assertEqual(app.resource.get(), REGION_VIEWS[valley]['Adult'])

    def test_gerudo_training_ground_returns_to_the_adult_fortress(self):
        from unittest.mock import patch
        from map_oot_rando.link_position import LinkPosition
        from map_oot_rando.scene import (REGION_VIEWS, TRAINING_TO_CEILING, TRAINING_TO_MAZE,
                                        TRAINING_TO_STATUE, TRAINING_TO_WALKWAY, TRAINING_VIEWS)

        app = self.app
        fortress, ground = 'GerudoFortress', 'GerudoTrainingGround'
        checks = ('Gerudo Training Ground Near Scarecrow Chest', 'Gerudo Training Ground Freestanding Key')
        doc = dict(demo_document(), provenance='ootrr-scan', regions=['KokiriForest', fortress, ground],
                   locations=[dict(id=f'ap#{name}', name=name, category='vanilla', region=ground,
                                   resource='Emplacements sans position', position=None) for name in checks], scenes={
                       'Banc/GerudoFortress/GerudoFortress_Adult_Static.bcett.byml.zs':
                           {'rooms': [], 'points': [('Vers le centre d’entraînement', (5, 3))]},
                       'Banc/GerudoTrainingGround/GerudoTrainingGround_Static.bcett.byml.zs':
                           {'rooms': [], 'points': [('Vers la Forteresse Gerudo', (-1.75, 6.91)),
                                                    (TRAINING_TO_WALKWAY, (-2.34, -58.92)),
                                                    (TRAINING_TO_CEILING, (-7.76, -35.45))],
                            'level_points': [(1, 'Passerelle nord', (-2.36, -55.67)),
                                             (1, 'Épouvantail', (1.5, -63.14)),
                                             (1, TRAINING_TO_STATUE, (-2.34, -58.92)),
                                             (1, TRAINING_TO_MAZE, (-7.76, -35.45))]},
                   })
        self.enterContext(patch.object(app, 'ensure_atlas'))
        app.load(doc)
        app.resource.set(REGION_VIEWS[fortress]['Adult'])
        app.resource_changed()
        self.assertIn(ground, app.navigation_markers.values())
        app.open_neighbor(ground)
        self.assertEqual(app.resource.get(), TRAINING_VIEWS[0])
        for target, arrival in ((TRAINING_VIEWS[1], TRAINING_TO_STATUE), (TRAINING_VIEWS[0], TRAINING_TO_WALKWAY),
                                (TRAINING_VIEWS[1], TRAINING_TO_MAZE), (TRAINING_VIEWS[0], TRAINING_TO_CEILING)):
            item, = [item for item in app.canvas.find_withtag('zone-navigation')
                     if any(action[2:] == (target, arrival) for action in app.local_portals[item])]
            x1, y1, x2, y2 = app.canvas.bbox(item)
            app.press(SimpleNamespace(x=(x1+x2)//2, y=(y1+y2)//2))
            self.assertEqual(app.resource.get(), target)
            self.assertTrue(app.canvas.find_withtag('portal-arrival'))
        app.query.set('Near Scarecrow')
        app.choose_first()
        self.assertEqual(app.resource.get(), TRAINING_VIEWS[1])
        self.assertIn('Salle de la statue · niveau supérieur', app.details.get())
        self.assertFalse(app.canvas.find_withtag('check-pin'))
        self.assertIn('Épouvantail', dict(app.scenes[TRAINING_VIEWS[1]]['points']))
        app.query.set('Freestanding Key')
        app.choose_first()
        self.assertEqual(app.resource.get(), TRAINING_VIEWS[0])
        self.assertIn('Labyrinthe central · côté droit', app.details.get())
        self.assertFalse(app.canvas.find_withtag('check-pin'))
        app.update_link(LinkPosition(ground, 'Adult', -1.5, 98, -48, 0))
        app.update_link(LinkPosition(ground, 'Adult', -1.5, 105, -48, 0))
        self.assertEqual(app.resource.get(), TRAINING_VIEWS[1])
        self.assertNotIn(fortress, app.available_neighbors())
        app.floor_picker.set('Salles et labyrinthe')
        app.choose_floor(None)
        app.choose_age('Child')
        self.assertIn(fortress, app.navigation_markers.values())
        app.open_neighbor(fortress)
        self.assertEqual(app.resource.get(), REGION_VIEWS[fortress]['Adult'])

    def test_wasteland_draws_the_guide_and_hides_the_child_fortress_portal(self):
        from unittest.mock import patch
        from map_oot_rando.scene import GUIDE_ROUTE, REGION_VIEWS

        app = self.app
        fortress, desert, colossus = 'GerudoFortress', 'HountedWasteland', 'DesertColossus'
        scenes = {
            'Banc/GerudoFortress/GerudoFortress_Adult_Dynamic.bcett.byml.zs':
                {'rooms': [], 'points': [('Vers le Désert hanté', (-45, -117))]},
        }
        for age in ('Child', 'Adult'):
            scenes[f'Banc/HountedWasteland/HountedWasteland_{age}_Static.bcett.byml.zs'] = {
                'rooms': [], 'points': [('Vers la Forteresse Gerudo', (123, 58)),
                                         ('Vers le Colosse du désert', (-107, -56))],
                'routes': [(GUIDE_ROUTE, [(14, -93), (-33, -100), (-92, -56)])],
            }
            scenes[f'Banc/DesertColossus/DesertColossus_{age}_Dynamic.bcett.byml.zs'] = {
                'rooms': [], 'points': [('Vers le Désert hanté', (4, 0))],
            }
        doc = dict(demo_document(), provenance='ootrr-scan', regions=['KokiriForest', fortress, desert, colossus],
                   locations=[], scenes=scenes)
        self.enterContext(patch.object(app, 'ensure_atlas'))
        app.load(doc)
        app.resource.set(REGION_VIEWS[fortress]['Adult'])
        app.resource_changed()
        self.assertIn(desert, app.navigation_markers.values())
        app.open_neighbor(desert)
        self.assertEqual(app.resource.get(), REGION_VIEWS[desert]['Adult'])
        self.assertEqual(len(app.canvas.find_withtag('scene-route')), 2)
        self.assertIn(fortress, app.navigation_markers.values())
        app.choose_age('Child')
        self.assertEqual(len(app.canvas.find_withtag('scene-route')), 2)
        self.assertNotIn(fortress, app.navigation_markers.values())
        for age in ('Child', 'Adult'):
            app.choose_age(age)
            self.assertIn(colossus, app.navigation_markers.values())
            app.open_neighbor(colossus)
            self.assertEqual(app.resource.get(), REGION_VIEWS[colossus][age])
            self.assertIn(desert, app.navigation_markers.values())
            app.open_neighbor(desert)
            self.assertEqual(app.resource.get(), REGION_VIEWS[desert][age])

    def test_lake_view_follows_link_inside_the_same_native_scene(self):
        from unittest.mock import patch
        from map_oot_rando.link_position import LinkPosition
        from map_oot_rando.scene import REGION_VIEWS

        app = self.app
        field, lake, domain = 'HyruleField', 'LakeHylia', 'ZoraDomain'
        template = demo_document()
        doc = dict(template, provenance='ootrr-scan', regions=['KokiriForest', field, lake, domain])
        doc['locations'] = [
            dict(template['locations'][0], id='lake', resource='Banc/HyruleField/HyruleField_Child_Static.bcett.byml.zs',
                 position=(-151, 125, 461)),
        ]
        doc['scenes'] = {
            f'Banc/HyruleField/HyruleField_{age}_Static.bcett.byml.zs': {
                'rooms': [], 'points': [('Vers le Lac Hylia', (-93, 398)),
                                         ('Vers la plaine d’Hyrule', (-89, 396)),
                                         ('Vers le Domaine Zora', (-139, 446))],
            }
            for age in ('Child', 'Adult')
        }
        doc['scenes']['Banc/ZoraDomain/ZoraDomain_Child_Static.bcett.byml.zs'] = {
            'rooms': [], 'points': [('Vers le Lac Hylia', (0, -3))],
        }
        self.enterContext(patch.object(app, 'ensure_atlas'))
        app.load(doc)
        app.update_link(LinkPosition(field, 'Child', -93, 144, 382, 0))
        self.assertEqual(app.resource.get(), REGION_VIEWS[field]['Child'])
        self.assertIn(lake, app.navigation_markers.values())
        app.update_link(LinkPosition(field, 'Child', -93, 143, 402, 0))
        self.assertEqual(app.resource.get(), REGION_VIEWS[lake]['Child'])
        self.assertEqual([row.id for row in app.visible], ['lake'])
        self.assertIn(domain, app.navigation_markers.values())
        app.update_link(LinkPosition(field, 'Adult', -253, 134, 402, 0))
        self.assertEqual(app.resource.get(), REGION_VIEWS[lake]['Adult'])
        self.assertNotIn(domain, app.available_neighbors())

    def test_ranch_portal_and_link_switch_the_local_view_without_a_scene_change(self):
        from unittest.mock import patch
        from map_oot_rando.link_position import LinkPosition
        from map_oot_rando.scene import REGION_VIEWS

        app = self.app
        field, ranch = 'HyruleField', 'LonLonRanch'
        path = 'Banc/HyruleField/HyruleField_Child_Static.bcett.byml.zs'
        template = demo_document()
        doc = dict(template, provenance='ootrr-scan', regions=['KokiriForest', field, ranch], locations=[
            dict(template['locations'][0], id='talon', resource=path, position=(-53.58, 151, 197.81)),
        ], scenes={
            path: {'rooms': [], 'points': [('Vers le ranch Lon Lon', (-61.8, 184.2)),
                                           ('Sortie du ranch', (-61.8, 184.2))]},
        })
        self.enterContext(patch.object(app, 'ensure_atlas'))
        app.load(doc)
        app.update_link(LinkPosition(field, 'Child', -62, 151, 177, 0))
        self.assertEqual(app.resource.get(), REGION_VIEWS[field]['Child'])
        self.assertIn(ranch, app.navigation_markers.values())
        app.update_link(LinkPosition(field, 'Child', -62, 151, 196, 0))
        self.assertEqual(app.resource.get(), REGION_VIEWS[ranch]['Child'])
        self.assertEqual([row.id for row in app.visible], ['talon'])
        self.assertIn(field, app.navigation_markers.values())
        app.open_neighbor(field)
        self.assertEqual(app.resource.get(), REGION_VIEWS[field]['Child'])

    def test_temple_of_time_follows_market_coordinates_and_sage_scene(self):
        from unittest.mock import patch
        from map_oot_rando.link_position import LinkPosition
        from map_oot_rando.scene import REGION_NAMES, REGION_VIEWS, extract_scenes

        app = self.app
        market, temple, sages = 'Market', 'TempleOfTime', 'SageRoom'
        market_path = 'Banc/Market/Market_Adult_Static.bcett.byml.zs'
        sage_path = 'Banc/SageRoom/SageRoom_Dynamic.bcett.byml.zs'
        child_path = 'Banc/Market/Market_Child_Static.bcett.byml.zs'
        pedestal = (137.67, 104.86, -34)
        platform = (0.09, 100.16, 0)
        market_scene = {'root': {'Actors': [
            dict(Gyaml='LocationArea', Dynamic={'Location': 'TimeTemple'}, Translate=(105, 103, -34)),
            dict(Gyaml='Obj_TimeTemple_MasterSwordBase_A_01', Translate=pedestal),
        ]}}
        sage_scene = {'root': {'Actors': [
            dict(Gyaml='StartPos', Translate=platform),
            dict(Gyaml='EftLoc_SageRoom_LightPillar_00', Translate=(21, 100, 12)),
            dict(Gyaml='EftLoc_SageRoom_LightPillar_00', Translate=(-16, 100, -14)),
        ]}}
        scenes = extract_scenes({market_path: market_scene, child_path: market_scene,
                                 sage_path: sage_scene}, lambda _: {})
        template = demo_document()
        doc = dict(template, provenance='ootrr-scan', regions=['KokiriForest', market, temple, sages],
                   locations=[
                       dict(template['locations'][0], id='sword', resource=market_path,
                            region=market, position=(137.6, 106, -34)),
                       dict(template['locations'][0], id='pocket', resource=sage_path,
                            region=sages, position=(0, 100, 0)),
                   ], scenes=scenes)
        self.enterContext(patch.object(app, 'ensure_atlas'))
        app.load(doc)
        app.update_link(LinkPosition(market, 'Adult', 64, 103, -34, 0))
        self.assertEqual(app.resource.get(), REGION_VIEWS[market]['Adult'])
        self.assertIn(temple, app.navigation_markers.values())
        app.follow_link.set(False)
        app.update_link(LinkPosition(market, 'Adult', 81, 103, -34, 0))
        self.assertEqual(app.resource.get(), REGION_VIEWS[market]['Adult'])
        app.follow_link.set(True)
        app.resume_follow_link()
        self.assertEqual(app.resource.get(), REGION_VIEWS[temple]['Adult'])
        self.assertEqual([row.id for row in app.visible], ['sword'])
        self.assertIn(market, app.navigation_markers.values())

        def click_portal(point, target, arrival):
            x, y = app.viewport.screen((point[0], point[2]))
            with patch.object(app, 'post_marker_menu') as popup:
                app.press(SimpleNamespace(x=round(x), y=round(y), x_root=50, y_root=50))
            popup.assert_called_once_with(50, 50)
            self.assertEqual(app.marker_menu.entrycget(1, 'label'), REGION_NAMES[target])
            app.marker_menu.invoke(1)
            ring, = app.canvas.find_withtag('portal-arrival')
            left, top, right, bottom = app.canvas.coords(ring)
            x, y = app.viewport.screen(arrival)
            self.assertAlmostEqual((left + right) / 2, x)
            self.assertAlmostEqual((top + bottom) / 2, y)

        click_portal(pedestal, sages, (-0.029999999329447746, 0))
        self.assertEqual(app.resource.get(), REGION_VIEWS[sages][None])
        app.update_link(LinkPosition(sages, 'Adult', 0, 100, 0, 0))
        self.assertEqual(app.resource.get(), REGION_VIEWS[sages][None])
        self.assertEqual([row.id for row in app.visible], ['pocket'])
        click_portal(platform, temple, (120.91000366210938, -26.65999984741211))
        self.assertEqual(app.resource.get(), REGION_VIEWS[temple]['Adult'])
        app.update_link(LinkPosition(market, 'Child', 64, 103, -34, 0))
        self.assertEqual(app.resource.get(), REGION_VIEWS[temple]['Child'])

    def test_dream_world_tracks_the_museum_and_keeps_coincident_chests_distinct(self):
        from unittest.mock import patch
        from map_oot_rando.link_position import LinkPosition
        from map_oot_rando.scene import DREAM_SCENE_VIEWS, REGION_VIEWS, extract_scenes

        app = self.app
        region = 'DreamWorld'
        museum, interval = 'EnemyMuseum', 'BossRushIntervalRoom'
        forest_path = 'Banc/KokiriForest/KokiriForest_Child_Static.bcett.byml.zs'
        museum_path = f'Banc/{region}/{museum}_Static.bcett.byml.zs'
        interval_path = f'Banc/{region}/{interval}_Static.bcett.byml.zs'
        maps = {
            forest_path: {'root': {'Actors': [
                {'Gyaml': 'Obj_Kokiri_Bed_A_01', 'Translate': [-48, 118, 15]},
                {'Gyaml': 'StartPos', 'Name': 'ReturnFromDreamWorld', 'Translate': [-46.5, 118.5, 15.4]},
            ]}},
            museum_path: {'root': {'Actors': [
                {'Gyaml': 'Npc_Dream', 'Translate': [3.5, 1.5, -2]},
                {'Gyaml': 'StartPos', 'Name': 'EnemyMusuem'},
            ]}},
            interval_path: {'root': {'Actors': [
                {'Gyaml': 'DungeonRoomArea', 'Translate': [-1, -1, -12], 'Scale': [20, 12, 32]},
                {'Gyaml': 'StartPos', 'Name': 'BossRush', 'Translate': [0, .2, 4.27]},
            ]}},
        }
        template = demo_document()
        doc = dict(template, provenance='ootrr-scan', regions=['KokiriForest', region], locations=[
            dict(template['locations'][0], id=f'chest{i}', name=f'Coffre {i}',
                 resource=interval_path, region=region, position=(0, .2, -6.45))
            for i in range(1, 11)
        ], scenes=extract_scenes(maps, lambda _: {}))
        self.enterContext(patch.object(app, 'ensure_atlas'))
        app.load(doc)
        app.update_link(LinkPosition('KokiriForest', 'Child', -48, 118, 15, 0))
        self.assertEqual(app.resource.get(), REGION_VIEWS['KokiriForest']['Child'])
        marker = next(item for item, target in app.navigation_markers.items() if target == region)
        x1, y1, x2, y2 = app.canvas.bbox(marker)
        app.press(SimpleNamespace(x=(x1+x2)//2, y=(y1+y2)//2))
        self.assertEqual(app.resource.get(), DREAM_SCENE_VIEWS[museum])
        self.assertFalse(app.visible)
        self.assertEqual(len(app.canvas.find_withtag('zone-navigation')), 1)

        def choose_organizer(destination, *, caption=False):
            if caption:
                label, = (item for item in app.canvas.find_all() if app.canvas.type(item) == 'text'
                          and app.canvas.itemcget(item, 'text') == 'Kokiri Forest · Défi des boss ▾')
                x, y = app.canvas.coords(label)
            else:
                x, y = app.viewport.screen((3.5, -2))
            with patch.object(app, 'post_marker_menu') as popup:
                app.press(SimpleNamespace(x=round(x), y=round(y), x_root=50, y_root=50))
            popup.assert_called_once_with(50, 50)
            labels = [app.marker_menu.entrycget(i, 'label') for i in range(2)]
            self.assertEqual(set(labels), {'Kokiri Forest', 'Défi des boss'})
            app.marker_menu.invoke(labels.index(destination))

        def arrived_at(point):
            ring, = app.canvas.find_withtag('portal-arrival')
            left, top, right, bottom = app.canvas.coords(ring)
            x, y = app.viewport.screen(point)
            self.assertAlmostEqual((left + right) / 2, x)
            self.assertAlmostEqual((top + bottom) / 2, y)

        arrived_at((0, 0))
        choose_organizer('Kokiri Forest')
        self.assertEqual(app.resource.get(), REGION_VIEWS['KokiriForest']['Child'])
        arrived_at((-46.5, 15.4))
        app.update_link(LinkPosition(region, 'Child', 3.5, 1.5, -2, 0, museum))
        self.assertEqual(app.resource.get(), DREAM_SCENE_VIEWS[museum])
        choose_organizer('Défi des boss', caption=True)
        self.assertEqual(app.resource.get(), DREAM_SCENE_VIEWS[interval])
        arrived_at((0, 4.27))
        self.assertFalse(app.canvas.find_withtag('zone-navigation'))
        app.update_link(LinkPosition(region, 'Child', 0, .2, 4.27, 0, interval))
        self.assertEqual(app.resource.get(), DREAM_SCENE_VIEWS[interval])
        self.assertEqual(len(app.visible), 10)
        x, y = app.viewport.screen((0, -6.45))
        with patch.object(app, 'choose_overlapping') as choose:
            app.press(SimpleNamespace(x=round(x), y=round(y), x_root=50, y_root=50))
        self.assertEqual({row.id for row in choose.call_args.args[0]}, {row.id for row in app.visible})
        app.update_link(LinkPosition(region, 'Child', 4, 1, 5, 0, 'GohmaStage'))
        self.assertIsNone(app.link_view())
        gohma = 'Banc/DreamWorld/GohmaStage_Dynamic.bcett.byml.zs'
        maps[gohma] = {'root': {'Actors': [
            dict(Gyaml='StartPos', Name='StartPos_SubEvent_AllBossBattle', Translate=(4.5, 47, 67.7)),
            dict(Gyaml='Enemy_DungeonBoss_Gohma', Translate=(17.2, 47, 60.6)),
        ]}}
        app.load(dict(doc, scenes=extract_scenes(maps, lambda _: {})))
        app.update_link(LinkPosition(region, 'Child', 4.5, 47, 67.7, 0, 'GohmaStage'))
        self.assertEqual(app.resource.get(), DREAM_SCENE_VIEWS['GohmaStage'])
        self.assertTrue(app.canvas.find_withtag('player-pin'))
        self.assertEqual(app.visible, ())
        self.assertIn('Gohma', app.floor_picker['values'])
        self.assertEqual(dict(app.scenes[DREAM_SCENE_VIEWS['GohmaStage']]['points'])['Arrivée pendant le défi'],
                         (4.5, 67.7))
        app.update_link(LinkPosition(region, 'Child', 0, .2, 4.27, 0, interval))
        self.assertEqual(len(app.visible), 10)

    def test_water_temple_opens_from_the_adult_lake_at_the_top(self):
        from unittest.mock import patch
        from map_oot_rando.link_position import LinkPosition
        from map_oot_rando.scene import REGION_VIEWS, WATER_LEVEL_CROSSINGS, WATER_VIEWS, extract_scenes

        app = self.app
        lake, temple = 'LakeHylia', 'WaterTemple'
        interior = 'Banc/WaterTemple/WaterTemple_Static.bcett.byml.zs'
        points = ((-4.5, 119.5, -11.56), (-1.55, 115.4, -4.5), (0.5, 111.41, -4.5),
                  (-9.55, 100.76, -4.5), (-1.5, 99.5, -4.41), (-4, 95.5, -4.41))
        ends = [end for crossing in WATER_LEVEL_CROSSINGS for end in crossing]
        actors = [dict(Gyaml=kind, Hash=ident, Translate=point)
                  for (_, _, kind, ident), point in zip(ends, points)]
        scenes = extract_scenes({interior: {'root': {'Actors': actors}}}, lambda _: {})
        scenes[interior]['points'].append(('Vers le Lac Hylia', (-4.5, 47)))
        doc = dict(demo_document(), provenance='ootrr-scan',
                   regions=['KokiriForest', 'HyruleField', lake, temple], locations=[], scenes={
                       **{f'Banc/HyruleField/HyruleField_{age}_Static.bcett.byml.zs':
                          {'rooms': [], 'points': [('Vers le Temple de l’Eau', (-186, 499))]}
                          for age in ('Adult', 'Child')},
                       **scenes,
                   })
        self.enterContext(patch.object(app, 'ensure_atlas'))
        app.load(doc)
        app.resource.set(REGION_VIEWS[lake]['Child'])
        app.resource_changed()
        self.assertNotIn(temple, app.available_neighbors())
        app.choose_age('Adult')
        self.assertIn(temple, app.navigation_markers.values())
        app.open_neighbor(temple)
        self.assertEqual(app.resource.get(), WATER_VIEWS[0])
        for index in (0, 2, 4, 5, 3, 1):
            title, floor = ends[index][1], ends[index ^ 1][0]
            marker, = [i for i in app.canvas.find_withtag('zone-navigation')
                       if any(t == title for t, *_ in app.local_portals[i])]
            x0, y0, x1, y1 = app.canvas.bbox(marker)
            app.press(SimpleNamespace(x=(x0+x1)//2, y=(y0+y1)//2))
            self.assertEqual(app.resource.get(), WATER_VIEWS[floor])
            ring, = app.canvas.find_withtag('portal-arrival')
            x0, y0, x1, y1 = app.canvas.coords(ring)
            x, _, z = points[index ^ 1]
            self.assertAlmostEqual((x0+x1)/2, app.viewport.screen((x, z))[0])
            self.assertAlmostEqual((y0+y1)/2, app.viewport.screen((x, z))[1])
        app.update_link(LinkPosition(temple, 'Adult', -4.5, 118.6, 43.61, 0))
        self.assertEqual(app.resource.get(), WATER_VIEWS[0])
        app.update_link(LinkPosition(temple, 'Adult', 56.87, 118.39, -28.12, 0))
        self.assertEqual(app.resource.get(), WATER_VIEWS[1])
        self.assertTrue(app.canvas.find_withtag('player-pin'))
        app.update_link(LinkPosition(temple, 'Adult', 36.75, 119.51, -4.49, 0))
        self.assertEqual(app.resource.get(), WATER_VIEWS[0])
        app.update_link(LinkPosition(temple, 'Adult', -4.62, 131.10, -69.58, 0))
        self.assertEqual(app.resource.get(), WATER_VIEWS[2])
        app.update_link(LinkPosition(temple, 'Adult', -4.5, 124.46, -83.65, 0))
        self.assertEqual(app.resource.get(), WATER_VIEWS[2])
        self.assertTrue(app.canvas.find_withtag('player-pin'))
        app.update_link(LinkPosition(temple, 'Adult', 12, 93, -4.5, 0))
        self.assertEqual(app.resource.get(), WATER_VIEWS[3])
        app.choose_age('Child')
        app.open_neighbor(lake)
        self.assertEqual(app.resource.get(), REGION_VIEWS[lake]['Adult'])

    def test_shadow_passages_connect_the_four_basements_and_boss_arena(self):
        from unittest.mock import patch
        from map_oot_rando.link_position import LinkPosition
        from map_oot_rando.scene import SHADOW_BOSS_DOOR, SHADOW_BOSS_LANDING, SHADOW_VIEWS, extract_scenes

        app = self.app
        region = 'ShadowTemple'
        path = f'Banc/{region}/{region}_Static.bcett.byml.zs'
        door, landing = (-138.51, 42, 19.05), (-138.33, -11.46, 22.02)
        crossings = [
            ('Escalier vers le sous-sol 2', 'Escalier vers le sous-sol 1',
             (13641591313020446364, (61.4, 90.56, 1.3)), (6139920143353312087, (63.89, 90.43, 1.34))),
            ('Passage vers le sous-sol 3', 'Passage vers le sous-sol 2',
             (9500101214674922945, (94.66, 75.42, 47.19)), (13181701853631283711, (94.52, 72.77, 47.28))),
            ('Passage vers le bateau', 'Passage vers le couloir des vents',
             (17002384234813722769, (109.64, 52, -25.6)), (8392133095956232092, (109.7, 48.22, -37.07))),
        ]
        actors = [
            *(dict(Gyaml='DungeonRoomArea', Hash=ident, Translate=point)
              for _, _, source, target in crossings for ident, point in (source, target)),
            dict(Gyaml='Obj_ShadowTemple_SwitchShutter_A_01', Hash=12557339757091997106, Translate=door),
            dict(Gyaml='StartPos', Hash=15657470794246498904, Translate=landing, Name='StartPos_SageOfShadow'),
            dict(Gyaml='StartPos', Hash=10000120391812373223, Translate=(-137, -11, 22), Name='StartPos_SageOfShadow'),
            dict(Gyaml='Obj_WarpPoint_A_01', Hash=15240382889320952895, Translate=(-138, -11, 30)),
        ]
        scenes = extract_scenes({path: {'root': {'Actors': actors}}}, lambda _: {})
        self.enterContext(patch.object(app, 'ensure_atlas'))
        app.load(dict(demo_document(), provenance='ootrr-scan', regions=['KokiriForest', region],
                      locations=[], scenes=scenes))
        def cross(title, view, position):
            marker, = [i for i in app.canvas.find_withtag('zone-navigation')
                       if any(t == title for t, *_ in app.local_portals[i])]
            x0, y0, x1, y1 = app.canvas.bbox(marker)
            app.press(SimpleNamespace(x=(x0+x1)//2, y=(y0+y1)//2))
            self.assertEqual(app.resource.get(), view)
            ring, = app.canvas.find_withtag('portal-arrival')
            x0, y0, x1, y1 = app.canvas.coords(ring)
            self.assertEqual(((x0+x1)/2, (y0+y1)/2), app.viewport.screen((position[0], position[2])))

        app.open_neighbor(region, view=SHADOW_VIEWS[0])
        for floor, (down, _, _, (_, point)) in enumerate(crossings, start=1):
            cross(down, SHADOW_VIEWS[floor], point)
        cross(SHADOW_BOSS_DOOR, SHADOW_VIEWS[4], landing)
        cross('Voir l’accès supérieur', SHADOW_VIEWS[3], door)
        for floor in reversed(range(len(crossings))):
            _, up, (_, point), _ = crossings[floor]
            cross(up, SHADOW_VIEWS[floor], point)
        self.assertEqual(dict(app.scenes[SHADOW_VIEWS[4]]['points'])[SHADOW_BOSS_LANDING],
                         (landing[0], landing[2]))
        app.update_link(LinkPosition(region, 'Adult', *door, 0))
        self.assertEqual(app.resource.get(), SHADOW_VIEWS[3])
        app.update_link(LinkPosition(region, 'Adult', *landing, 0))
        self.assertEqual(app.resource.get(), SHADOW_VIEWS[4])
        self.assertTrue(app.canvas.find_withtag('player-pin'))

    def test_twinrova_warp_opens_the_adult_colossus_directly_or_via_the_sages(self):
        from unittest.mock import patch
        from map_oot_rando.scene import REGION_VIEWS, SPIRIT_VIEWS, extract_scenes

        app = self.app
        sage_view = REGION_VIEWS['SageRoom'][None]
        colossus_view = REGION_VIEWS['DesertColossus']['Adult']
        warp, requiem = (0.012, 142.16, -157.86), (-125.95, 94.36, 10.47)
        maps = {
            'Banc/SpiritTemple/SpiritTemple_Static.bcett.byml.zs': {'root': {'Actors': [
                dict(Gyaml='Obj_WarpPoint_A_01', Hash=11243501154977749945, Translate=warp),
            ]}},
            'Banc/SageRoom/SageRoom_Dynamic.bcett.byml.zs': {'root': {'Actors': [
                dict(Gyaml='StartPos', Translate=(0.09, 100.16, 0)),
            ]}},
            'Banc/DesertColossus/DesertColossus_Adult_Dynamic.bcett.byml.zs': {'root': {'Actors': [
                dict(Gyaml='StartPos', Name='SpiritRequiem', Translate=requiem),
            ]}},
        }
        doc = dict(demo_document(), provenance='ootrr-scan',
                   regions=['KokiriForest', 'SpiritTemple', 'SageRoom', 'DesertColossus'],
                   scenes=extract_scenes(maps, lambda _: {}), locations=[])
        self.enterContext(patch.object(app, 'ensure_atlas'))
        app.load(doc)

        def choose(marker, title):
            l, t, r, b = app.canvas.bbox(marker)
            with patch.object(app, 'post_marker_menu') as popup:
                app.press(SimpleNamespace(x=(l+r)//2, y=(t+b)//2, x_root=50, y_root=50))
            if popup.called:
                index, = [i for i in range(app.marker_menu.index('end') + 1)
                          if app.marker_menu.entrycget(i, 'label') == title]
                app.marker_menu.invoke(index)

        def arrival(point):
            ring, = app.canvas.find_withtag('portal-arrival')
            l, t, r, b = app.canvas.coords(ring)
            x, y = app.viewport.screen(point)
            self.assertAlmostEqual((l+r)/2, x)
            self.assertAlmostEqual((t+b)/2, y)

        for via_sages in (False, True):
            app.resource.set(SPIRIT_VIEWS[4])
            app.resource_changed(manual=False)
            app.navigation_age = 'Child'
            marker, = app.canvas.find_withtag('zone-navigation')
            choose(marker, 'Chambre des Sages · cinématique' if via_sages else 'Colosse du désert')
            if via_sages:
                self.assertEqual(app.resource.get(), sage_view)
                arrival((0, 0))
                marker, = app.canvas.find_withtag('zone-navigation')
                choose(marker, 'Colosse du désert · suite de la cinématique')
            self.assertEqual(app.resource.get(), colossus_view)
            arrival((requiem[0], requiem[2]))

    def test_volvagia_cutscene_continues_from_kakariko_through_the_sages(self):
        from unittest.mock import patch
        from map_oot_rando.link_position import LinkPosition
        from map_oot_rando.scene import FIRE_VIEWS, REGION_VIEWS, extract_scenes

        app = self.app
        village = REGION_VIEWS['KakarikoVillage']['Adult']
        crater = REGION_VIEWS['DeathMountainCrater']['Adult']
        sages = REGION_VIEWS['SageRoom'][None]
        maps = {
            'Banc/FireTemple/FireTemple_Static.bcett.byml.zs': {'root': {'Actors': [
                dict(Gyaml='Obj_FireTemple_SwitchShutter_A_02', Hash=7971893604208202501, Translate=(-39, 105, 0)),
                dict(Gyaml='StartPos', Hash=4368300544097029137, Translate=(-64.5, 102.5, 0)),
                dict(Gyaml='Obj_WarpPoint_A_01', Hash=14585775662663687502, Translate=(-80.25, 102.46, .08)),
            ]}},
            'Banc/KakarikoVillage/KakarikoVillage_Adult_Dynamic.bcett.byml.zs': {'root': {'Actors': [
                dict(Gyaml='StartPos', Name='KakarikoVillage_Entrance', Translate=(-119.77, 96.63, 58.7)),
            ]}},
            'Banc/SageRoom/SageRoom_Dynamic.bcett.byml.zs': {'root': {'Actors': [
                dict(Gyaml='StartPos', Translate=(.09, 100.16, 0)),
            ]}},
            'Banc/DeathMountainCrater/DeathMountainCrater_Adult_Dynamic.bcett.byml.zs': {'root': {'Actors': [
                dict(Gyaml='StartPos', Name='FireBolero', Hash=9678098360451750149, Translate=(.39, 111.84, -8.63)),
                dict(Gyaml='StartPos', Name='FireBolero', Hash=9726922324643513629, Translate=(.38, 111.69, -8.68)),
            ]}},
        }
        doc = dict(demo_document(), provenance='ootrr-scan', locations=[], scenes=extract_scenes(maps, lambda _: {}),
                   regions=['KokiriForest', 'FireTemple', 'KakarikoVillage', 'SageRoom', 'DeathMountainCrater'])
        self.enterContext(patch.object(app, 'ensure_atlas'))
        app.load(doc)
        app.resource.set(village)
        app.resource_changed(manual=False)
        self.assertNotIn('SageRoom', app.navigation_markers.values())
        app.open_neighbor('FireTemple', view=FIRE_VIEWS[0])
        marker, = app.canvas.find_withtag('zone-navigation')
        l, t, r, b = app.canvas.bbox(marker)
        app.press(SimpleNamespace(x=(l+r)//2, y=(t+b)//2))
        self.assertEqual(app.resource.get(), FIRE_VIEWS[-1])
        self.assertTrue(app.canvas.find_withtag('portal-arrival'))
        for target, view in (('KakarikoVillage', village), ('SageRoom', sages), ('DeathMountainCrater', crater)):
            marker, = [i for i in app.canvas.find_withtag('zone-navigation')
                       if any(action[1] == target for action in app.local_portals[i])]
            option, = [action[0] for action in app.local_portals[marker] if action[1] == target]
            l, t, r, b = app.canvas.bbox(marker)
            with patch.object(app, 'post_marker_menu') as popup:
                app.press(SimpleNamespace(x=(l+r)//2, y=(t+b)//2, x_root=50, y_root=50))
            if popup.called:
                index, = [i for i in range(app.marker_menu.index('end') + 1)
                          if app.marker_menu.entrycget(i, 'label') == option]
                app.marker_menu.invoke(index)
            self.assertEqual(app.resource.get(), view)
            self.assertEqual(len(app.canvas.find_withtag('portal-arrival')), 1)
        app.update_link(LinkPosition('FireTemple', 'Adult', -64.5, 102.5, 0, 0))
        self.assertEqual(app.resource.get(), FIRE_VIEWS[-1])
        self.assertTrue(app.canvas.find_withtag('player-pin'))

    def test_spirit_temple_hand_portal_opens_the_upper_floor(self):
        from unittest.mock import patch
        from map_oot_rando.link_position import LinkPosition
        from map_oot_rando.scene import PORTAL_ARRIVAL_STARTS, REGION_VIEWS, SPIRIT_VIEWS, extract_scenes

        app = self.app
        outside, temple = 'DesertColossus', 'SpiritTemple'
        colossus = 'Banc/DesertColossus/DesertColossus_Adult_Dynamic.bcett.byml.zs'
        interior = 'Banc/SpiritTemple/SpiritTemple_Dynamic.bcett.byml.zs'
        hands = {'left': ((-165, -16), (56, 44)), 'right': ((-164, 37), (-56, 44))}
        spawns = {'left': ((-165, -12), (56, 39)), 'right': ((-164, 33), (-56, 39))}
        doors = {
            'Porte derrière le visage de la statue': ('Obj_SpiritTemple_SwitchShutter_A_03', 16853997340662105473, -76.7),
            'Porte vers la salle de la statue': ('Obj_SwitchShutter_A_06', 11880473245622015774, -77.05),
            'Porte vers Twinrova': ('Obj_SpiritTemple_SwitchShutter_A_04', 8544696912463075599, -119.32),
            'Porte vers le couloir': ('Obj_SwitchShutter_A_06', 17726959485897113740, -119.67),
        }
        actors = [dict(Gyaml=kind, Hash=ident, Translate=(0, 135, z)) for kind, ident, z in doors.values()]
        native = extract_scenes({interior: {'root': {'Actors': actors}}}, lambda _: {})
        doc = dict(demo_document(), provenance='ootrr-scan', regions=['KokiriForest', outside, temple],
                   locations=[], scenes={
                       colossus: {'rooms': [], 'points': [
                           ('Vers le Temple de l’Esprit', (-161, 10)),
                           *((f'spirit_temple_{hand}_hand_entrance', entry)
                             for hand, (entry, _) in hands.items()),
                           *((PORTAL_ARRIVAL_STARTS[outside, f'spirit_temple_{hand}_hand_entrance'][0], spawn)
                             for hand, (spawn, _) in spawns.items()),
                       ]},
                       interior: {'rooms': [], 'points': [('Vers le Colosse du désert', (0, 13))],
                                  'level_points': [
                                      *native[interior]['level_points'],
                                      (4, 'Arène de Twinrova', (0, -158)),
                                      *((2, f'{hand}_hand_entrance', entry)
                                        for hand, (_, entry) in hands.items()),
                                      *((2, PORTAL_ARRIVAL_STARTS[temple, f'{hand}_hand_entrance'][0], spawn)
                                        for hand, (_, spawn) in spawns.items()),
                                  ]},
                   })
        self.enterContext(patch.object(app, 'ensure_atlas'))
        app.load(doc)
        app.resource.set(REGION_VIEWS[outside]['Adult'])
        app.resource_changed()
        def click(point):
            x, y = app.viewport.screen(point)
            app.press(SimpleNamespace(x=round(x), y=round(y)))

        def check_arrival(point):
            marker, = app.canvas.find_withtag('portal-arrival')
            x0, y0, x1, y1 = app.canvas.coords(marker)
            x, y = app.viewport.screen(point)
            self.assertAlmostEqual((x0 + x1) / 2, x)
            self.assertAlmostEqual((y0 + y1) / 2, y)

        for hand, (exterior, entrance) in hands.items():
            click(exterior)
            self.assertEqual(app.resource.get(), SPIRIT_VIEWS[2])
            check_arrival(spawns[hand][1])
            click(entrance)
            self.assertEqual(app.resource.get(), REGION_VIEWS[outside]['Adult'])
            check_arrival(spawns[hand][0])
        app.open_neighbor(temple)
        self.assertEqual(app.resource.get(), SPIRIT_VIEWS[0])
        self.assertFalse(app.canvas.find_withtag('portal-arrival'))
        app.update_link(LinkPosition(temple, 'Adult', 0, 100, 0, 0))
        app.update_link(LinkPosition(temple, 'Adult', 0, 135, -70, 0))
        for door, target, landing in (
            ('Porte derrière le visage de la statue', 5, 'Porte vers la salle de la statue'),
            ('Porte vers Twinrova', 4, 'Porte vers le couloir'),
            ('Porte vers le couloir', 5, 'Porte vers Twinrova'),
            ('Porte vers la salle de la statue', 2, 'Porte derrière le visage de la statue'),
        ):
            click((0, doors[door][2]))
            self.assertEqual(app.resource.get(), SPIRIT_VIEWS[target])
            check_arrival((0, doors[landing][2]))
        app.update_link(LinkPosition(temple, 'Adult', 0, 135, -114, 0))
        self.assertEqual(app.resource.get(), SPIRIT_VIEWS[5])
        app.update_link(LinkPosition(temple, 'Adult', 0, 145, -157, 0))
        self.assertEqual(app.resource.get(), SPIRIT_VIEWS[4])

    def test_ganon_castle_switches_scene_without_mixing_coordinates(self):
        from unittest.mock import patch
        from map_oot_rando.link_position import LinkPosition
        from map_oot_rando.scene import (GANON_DUNGEON_VIEWS, GANON_ESCAPE, GANON_ESCAPE_ROUTE, GANON_FINAL,
                                        GANON_OUTSKIRTS, REGION_VIEWS, extract_scenes)

        app = self.app
        template = demo_document()
        doc = dict(template, provenance='ootrr-scan',
                   regions=['KokiriForest', 'Market', 'HyruleCastle', 'GanonCastle', 'InsideGanonCastle'])
        market = 'Banc/Market/Market_{}_Static.bcett.byml.zs'
        hyrule = 'Banc/HyruleCastle/HyruleCastle_Static.bcett.byml.zs'
        ganon = 'Banc/GanonCastle/GanonCastle_Static.bcett.byml.zs'
        escape = 'Banc/GanonCastle/CrumblingGanonCastle_Dynamic.bcett.byml.zs'
        doc['locations'] = [
            dict(template['locations'][0], id='exterior', resource=ganon, position=(78, 94, 328)),
            dict(template['locations'][0], id='pot', resource=escape, position=(-4, 192, -22)),
        ]
        doc['scenes'] = {
            market.format('Child'): {'rooms': [], 'points': [('Vers le Château d’Hyrule', (-2, -36))]},
            market.format('Adult'): {'rooms': [], 'points': [('Vers le Château de Ganon', (-2, -36))]},
            hyrule: {'rooms': [], 'points': []},
            ganon: {'rooms': [], 'points': [('Vers la Citadelle d’Hyrule', (60, 369))]},
        }
        arena = 'Banc/GanonCastle/FinalBattleField_Static.bcett.byml.zs'
        tower = 'Banc/InsideGanonCastle/InsideGanonCastle_Static.bcett.byml.zs'
        maps = {
            escape: {'root': {
                'Actors': [
                    dict(Gyaml='StartPos', Name='CrumblingGanonCastle_StartPos', Translate=(-6.59, 230.3, 0)),
                    dict(Gyaml='FieldAndDungeonEntranceEventRequestActor', Translate=(-92, 178, 0),
                         Dynamic={'NextBancParamNameAdult': 'FinalBattleField'}),
                    dict(Gyaml='Npc_Hylia_Zelda_Adult', Rails=[dict(Dst=1), dict(Dst=2)]),
                ],
                'Rails': [
                    dict(Gyaml='Guide', Name=name, Hash=i, Points=[dict(Translate=point) for point in points])
                    for i, name, points in (
                        (1, 'Step01', ((-8, 230, 0), (12, 213, -2))),
                        (2, 'Step13', ((-99, 166, 0), (-113, 165, 0))),
                    )
                ],
            }},
            arena: {'root': {'Actors': [
                dict(Gyaml='StartPos', Name='FinalBattleField_Entrance', Translate=(28.18, 99.98, -.81)),
                dict(Gyaml='Enemy_DungeonBoss_Ganon_SecondHalfBattle', Translate=(-1.37, 99.98, -1.03)),
            ]}},
            tower: {'root': {'Actors': [
                dict(Gyaml='Enemy_DungeonBoss_Ganondorf', Hash=15798214583796164285, Translate=(0, 174, -24.6)),
                dict(Gyaml='Obj_InsideGanonCastle_BrokenFloor_A_01', Translate=(3, 171, -25)),
            ]}},
        }
        doc['scenes'].update(extract_scenes(maps, lambda _: {}))
        self.enterContext(patch.object(app, 'ensure_atlas'))
        app.load(doc)
        self.assertIn('HyruleCastle', app.world_targets())
        self.assertNotIn('GanonCastle', app.world_targets())
        app.age_buttons['Adult'].invoke()
        self.assertNotIn('HyruleCastle', app.world_targets())
        self.assertIn('GanonCastle', app.world_targets())
        self.assertIn('GanonCastle', app.navigation_markers.values())
        app.open_neighbor('GanonCastle')
        self.assertEqual(app.resource.get(), GANON_OUTSKIRTS)
        self.assertEqual([row.id for row in app.visible], ['exterior'])
        app.open_neighbor('Market')
        self.assertEqual(app.resource.get(), REGION_VIEWS['Market']['Adult'])
        app.open_neighbor('GanonCastle')
        app.floor_picker.set('Effondrement')
        app.choose_floor(None)
        app.save_age = 'Adult'
        app.sync_age()
        self.assertEqual(app.resource.get(), GANON_ESCAPE)
        self.assertEqual([row.id for row in app.visible], ['pot'])
        self.assertNotIn('Market', app.available_neighbors())
        app.update_link(LinkPosition('GanonCastle', 'Adult', 78, 94, 328, 0, 'GanonCastle'))
        self.assertEqual(app.resource.get(), GANON_OUTSKIRTS)
        app.update_link(LinkPosition('GanonCastle', 'Adult', -4, 192, -22, 0, 'CrumblingGanonCastle'))
        self.assertEqual(app.resource.get(), GANON_ESCAPE)
        app.resource.set(GANON_DUNGEON_VIEWS[-1])
        app.resource_changed(manual=False)
        tile, = app.canvas.find_withtag('ganondorf-tile')
        x1, y1, x2, y2 = app.canvas.coords(tile)
        self.assertAlmostEqual(x2-x1, 3*app.viewport.scale)
        self.assertAlmostEqual(y2-y1, 3*app.viewport.scale)
        portal, = app.canvas.find_withtag('zone-navigation')
        l, t, r, b = app.canvas.bbox(portal)
        app.press(SimpleNamespace(x=(l+r)//2, y=(t+b)//2))
        self.assertEqual(app.resource.get(), GANON_ESCAPE)
        self.assertTrue(app.canvas.find_withtag('portal-arrival'))
        (name, route), = app.scenes[GANON_ESCAPE]['routes']
        self.assertEqual((name, route[0], route[-1]), (GANON_ESCAPE_ROUTE, (-8, 0), (12, -2)))
        portal, = app.canvas.find_withtag('zone-navigation')
        l, t, r, b = app.canvas.bbox(portal)
        app.press(SimpleNamespace(x=(l+r)//2, y=(t+b)//2))
        self.assertEqual(app.resource.get(), GANON_FINAL)
        self.assertTrue(app.canvas.find_withtag('portal-arrival'))
        self.assertFalse(app.canvas.find_withtag('zone-navigation'))
        app.update_link(LinkPosition('GanonCastle', 'Adult', -4, 192, -22, 0, 'CrumblingGanonCastle'))
        self.assertEqual(app.resource.get(), GANON_FINAL)
        app.update_link(LinkPosition('GanonCastle', 'Adult', 30, 100, 20, 0, 'FinalBattleField'))
        self.assertEqual(app.link_view(), GANON_FINAL)
        self.assertTrue(app.canvas.find_withtag('player-pin'))

    def test_fire_temple_follow_tracks_floors_within_one_game_scene(self):
        from unittest.mock import patch
        from map_oot_rando.link_position import LinkPosition
        from map_oot_rando.scene import FIRE_VIEWS

        app = self.app
        region = 'FireTemple'
        path = f'Banc/{region}/{region}_Static.bcett.byml.zs'
        doc = dict(demo_document(), provenance='ootrr-scan', regions=['KokiriForest', region],
                   locations=[], scenes={path: {'rooms': [], 'points': [('Entrée', (0, 30))]}})
        self.enterContext(patch.object(app, 'ensure_atlas'))
        app.load(doc)
        app.update_link(LinkPosition(region, 'Adult', 10, 105, 0, 0))
        self.assertEqual(app.resource.get(), FIRE_VIEWS[0])
        app.update_link(LinkPosition(region, 'Adult', 10, 145, 0, 0))
        self.assertEqual(app.resource.get(), FIRE_VIEWS[2])
        app.resource.set(FIRE_VIEWS[1])
        app.resource_changed()
        app.update_link(None)
        app.update_link(LinkPosition(region, 'Adult', 12, 145, 0, 0))
        self.assertEqual(app.resource.get(), FIRE_VIEWS[1])
        app.update_link(LinkPosition(region, 'Adult', 12, 166, 0, 0))
        self.assertEqual(app.resource.get(), FIRE_VIEWS[3])
        self.assertTrue(app.canvas.find_withtag('player-pin'))

    def test_ganon_tower_follow_tracks_floors_and_respects_manual_browsing(self):
        from unittest.mock import patch
        from map_oot_rando.link_position import LinkPosition
        from map_oot_rando.scene import GANON_DUNGEON_VIEWS, GANON_OUTSKIRTS

        app = self.app
        region = 'InsideGanonCastle'
        path = f'Banc/{region}/{region}_Static.bcett.byml.zs'
        ganon = 'Banc/GanonCastle/GanonCastle_Static.bcett.byml.zs'
        template = demo_document()
        doc = dict(template, provenance='ootrr-scan', regions=['KokiriForest', 'GanonCastle', region])
        doc['locations'] = [
            dict(template['locations'][0], id='trial', resource=path, position=(48, 104, -105), dungeon_room=8),
            dict(template['locations'][0], id='boss-key', resource=path, position=(0, 149.7, -24.7), dungeon_room=24),
        ]
        doc['scenes'] = {
            ganon: {'rooms': [], 'points': [('Entrée du château', (40.61, 220.77))]},
            path: {'rooms': [], 'points': [('Vers les abords', (0, 97))],
                   'level_points': [(2, 'Salle du premier étage', (0, -24.7))]},
        }
        self.enterContext(patch.object(app, 'ensure_atlas'))
        app.load(doc)
        app.update_link(LinkPosition('GanonCastle', 'Adult', 40, 99, 221, 0))
        self.assertEqual(app.resource.get(), GANON_OUTSKIRTS)
        self.assertIn(region, app.navigation_markers.values())
        app.open_neighbor(region)
        self.assertEqual(app.resource.get(), GANON_DUNGEON_VIEWS[0])
        self.assertIn('GanonCastle', app.navigation_markers.values())
        self.assertEqual([r.id for r in app.visible], ['trial'])
        app.update_link(LinkPosition(region, 'Adult', 0, 128, 97, 0))
        self.assertEqual(app.resource.get(), GANON_DUNGEON_VIEWS[0])
        app.update_link(LinkPosition(region, 'Adult', 0, 136.25, -24.7, 0))
        self.assertEqual(app.resource.get(), GANON_DUNGEON_VIEWS[2])
        self.assertFalse(app.available_neighbors())
        app.follow_link.set(False)
        app.update_link(LinkPosition(region, 'Adult', 0, 149.7, -24.7, 0))
        self.assertEqual(app.resource.get(), GANON_DUNGEON_VIEWS[2])
        app.follow_link.set(True)
        self.assertTrue(app.resume_follow_link())
        self.assertEqual(app.resource.get(), GANON_DUNGEON_VIEWS[4])
        self.assertEqual([r.id for r in app.visible], ['boss-key'])

    def test_jabu_fountain_portal_and_room_selection(self):
        from unittest.mock import patch
        from map_oot_rando.scene import JABU_LEVELS, JABU_VIEWS, REGION_VIEWS

        app = self.app
        region = 'InsideJabuJabuBelly'
        template = demo_document()
        doc = dict(template, provenance='ootrr-scan', regions=['KokiriForest', 'ZoraFountain', region])
        path = f'Banc/{region}/{region}_Static.bcett.byml.zs'
        doc['locations'] = [dict(template['locations'][0], resource=path, id='arena-pot',
                                 position=(34, 102, -126), dungeon_room=15)]
        doc['scenes'] = {
            path: {'rooms': [], 'points': [('Vers la Fontaine Zora', (0, 4))]},
            'Banc/ZoraFountain/ZoraFountain_Child_Static.bcett.byml.zs':
                {'rooms': [], 'points': [('Vers Jabu-Jabu', (20, -24))]},
            'Banc/ZoraFountain/ZoraFountain_Adult_Static.bcett.byml.zs':
                {'rooms': [], 'points': [('Rive', (20, -24))]},
        }
        self.enterContext(patch.object(app, 'ensure_atlas'))
        app.load(doc)
        self.assertIn(region, app.navigation_markers.values())
        app.open_neighbor(region)
        self.assertEqual(app.resource.get(), JABU_VIEWS[0])
        self.assertEqual(tuple(app.floor_picker['values']), JABU_LEVELS)
        app.floor_picker.set(JABU_LEVELS[-1])
        app.choose_floor(None)
        self.assertEqual([row.id for row in app.visible], ['arena-pot'])
        app.open_neighbor('ZoraFountain')
        self.assertEqual(app.resource.get(), REGION_VIEWS['ZoraFountain']['Child'])
        app.age_buttons['Adult'].invoke()
        self.assertNotIn(region, app.available_neighbors())
        self.assertIn(region, app.world_targets())

    def test_deku_opens_from_kokiri_even_with_no_check_on_entrance_floor(self):
        from unittest.mock import patch
        from map_oot_rando.scene import DEKU_LEVELS, DEKU_VIEWS, REGION_VIEWS

        app = self.app
        region = 'InsideTheDekuTree'
        template = demo_document()
        doc = dict(template, provenance='ootrr-scan', regions=['KokiriForest', region])
        path = f'Banc/{region}/{region}_Static.bcett.byml.zs'
        kokiri = 'Banc/KokiriForest/KokiriForest_Child_Static.bcett.byml.zs'
        doc['locations'] = [dict(template['locations'][0], resource=path, id='gohma',
                                 position=(18, 47, 68), dungeon_room=10)]
        doc['scenes'] = {
            path: {'rooms': [], 'points': [('Vers la forêt Kokiri', (0, 18))]},
            kokiri: {'rooms': [], 'points': [('front_deku_tree_entrance', (92, -28))]},
        }
        self.enterContext(patch.object(app, 'ensure_atlas'))
        app.load(doc)
        self.assertIn(region, app.navigation_markers.values())
        app.open_neighbor(region)
        self.assertEqual(app.resource.get(), DEKU_VIEWS[0])
        self.assertEqual(tuple(app.floor_picker['values']), DEKU_LEVELS)
        app.floor_picker.set(DEKU_LEVELS[-1])
        app.choose_floor(None)
        self.assertEqual([row.id for row in app.visible], ['gohma'])
        app.open_neighbor('KokiriForest')
        self.assertEqual(app.resource.get(), REGION_VIEWS['KokiriForest']['Child'])

    def test_overlapping_markers_can_both_be_selected(self):
        from unittest.mock import patch

        app = self.app
        document = demo_document()
        first, second = document['locations'][:2]
        second['position'] = first['position']
        document['locations'] = [first, second]
        app.load(document)
        x, y = app.viewport.screen((first['position'][0], first['position'][2]))
        event = SimpleNamespace(x=round(x), y=round(y), x_root=50, y_root=50)
        with patch.object(app.marker_menu, 'tk_popup') as popup:
            app.press(event)
        popup.assert_called_once_with(50, 50)
        app.marker_menu.invoke(0)
        first_choice = app.selected.id
        app.marker_menu.invoke(1)
        self.assertEqual({first_choice, app.selected.id}, {first['id'], second['id']})

    def test_portal_remains_clickable_under_a_check(self):
        from unittest.mock import patch
        from map_oot_rando.scene import NEIGHBORS, REGION_NAMES, REGION_VIEWS

        app = self.app
        forest, woods = 'KokiriForest', 'LostWood'
        resource = 'Banc/KokiriForest/KokiriForest_Child_Static.bcett.byml.zs'
        document = dict(demo_document(), provenance='ootrr-scan', regions=[forest, woods])
        row = dict(document['locations'][0], name='Pot près du passage',
                   resource=resource, position=(10, 0, 20))
        document['locations'] = [row]
        document['scenes'] = {
            resource: {'rooms': [], 'points': [(NEIGHBORS[forest][woods], (10, 20))]},
            'Banc/LostWood/LostWood_Child_Static.bcett.byml.zs': {
                'rooms': [], 'points': [(NEIGHBORS[woods][forest], (-30, 15))],
            },
        }
        self.enterContext(patch.object(app, 'ensure_atlas'))
        app.load(document)
        x, y = app.viewport.screen((10, 20))
        event = SimpleNamespace(x=round(x), y=round(y), x_root=50, y_root=50)
        with patch.object(app, 'post_marker_menu') as popup:
            app.press(event)
        popup.assert_called_once_with(50, 50)
        self.assertEqual(app.marker_menu.entrycget(0, 'label'), row['name'])
        self.assertEqual(app.marker_menu.entrycget(1, 'label'), REGION_NAMES[woods])
        app.marker_menu.invoke(0)
        self.assertEqual(app.selected.id, row['id'])
        app.marker_menu.invoke(1)
        self.assertEqual(app.resource.get(), REGION_VIEWS[woods]['Child'])

        row['position'] = (-15, 0, 20)
        app.load(document)
        width, height = app.canvas.winfo_width(), app.canvas.winfo_height()
        app.viewport.scale = 1
        app.viewport.center((10, 20), width, height)
        app.draw()
        self.assertTrue(app.canvas.find_withtag('check-pin'))
        self.assertFalse(any(app.canvas.type(item) == 'text' for item in app.markers))
        app.press(SimpleNamespace(x=round(width/2), y=round(height/2)))
        self.assertEqual(app.resource.get(), REGION_VIEWS[woods]['Child'])

    def test_choose_save_uses_a_directory_picker(self):
        from pathlib import Path
        from tempfile import TemporaryDirectory
        from unittest.mock import patch

        app = self.app
        with TemporaryDirectory() as directory:
            seed_dir = Path(directory).resolve()
            (seed_dir / 'manifest.json').write_text('{}')
            saves = seed_dir / 'saves'
            saves.mkdir()
            app.seed_folder = seed_dir
            with (patch('map_oot_rando.gui.filedialog.askdirectory', return_value=str(saves)) as picker,
                  patch('map_oot_rando.gui.filedialog.askopenfilename') as file_picker,
                  patch.object(app, 'follow_save') as follow):
                app.choose_save()
                picker.assert_called_once()
                file_picker.assert_not_called()
                follow.assert_called_once_with(seed_dir, saves)
