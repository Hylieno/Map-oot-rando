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

    def test_import_automatically_loads_field_atlas_over_legacy_preference(self):
        from unittest.mock import patch
        from PIL import Image
        from map_oot_rando.field_atlas import HOUSE_PIXELS

        resource = 'Banc/KokiriForest/KokiriForest_Adult_Dynamic.bcett.byml.zs'
        doc = demo_document()
        doc['provenance'] = 'ootrr-scan'
        doc['locations'] = [dict(doc['locations'][0], resource=resource)]
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
            self.root.after(20, wait_for_background)
            deadline = self.root.after(2000, self.root.quit)
            self.root.mainloop()
            self.root.after_cancel(deadline)
            self.assertTrue(app.canvas.find_withtag('aerial'))
            self.assertEqual(app.aerial[app.resource.get()].source, 'field-atlas')
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
                follow.assert_called_once_with(tmp, tmp)
                follow.reset_mock()
                app.stop_tracking()
                app.load(doc)
                follow.assert_not_called()
                app.load(dict(doc, seed_id='another-seed'))
                follow.assert_not_called()

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

    def test_crater_link_returns_to_goron_ground_floor(self):
        from map_oot_rando.scene import GORON_CRATER_FLOOR, GORON_VIEWS, REGION_VIEWS

        app = self.app
        doc = dict(demo_document(), provenance='ootrr-scan', regions=list(REGION_VIEWS))
        row = doc['locations'][0]
        crater = 'Banc/DeathMountainCrater/DeathMountainCrater_Adult_Static.bcett.byml.zs'
        goron = 'Banc/GoronCity/GoronCity_Adult_Static.bcett.byml.zs'
        doc['locations'] = [dict(row, resource=crater)]
        doc['scenes'] = {goron: {'rooms': [], 'points': [('Repère nord Goron', (10, 15))]}}
        app.load(doc)
        app.resource.set(REGION_VIEWS['DeathMountainCrater']['Adult'])
        app.resource_changed()
        app.open_neighbor('GoronCity')
        self.assertEqual(app.resource.get(), GORON_VIEWS['Adult'][GORON_CRATER_FLOOR])
        self.assertEqual(set(app.navigation_markers.values()), {'DeathMountainCrater'})

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
        from map_oot_rando.scene import GORON_LOST_WOODS_FLOOR, GORON_VIEWS, REGION_VIEWS

        app = self.app
        regions = ('KokiriForest', 'LostWood', 'GoronCity', 'ZoraRiver', 'HyruleField', 'ZoraDomain', 'ZoraFountain')

        def resource(region, age):
            return f'Banc/{region}/{region}_{age}_Static.bcett.byml.zs'

        doc = dict(demo_document(), provenance='ootrr-scan', regions=list(regions), locations=[])
        points = {
            'LostWood': [('Vers le Village Goron', (24, -35.66)), ('Vers la Rivière Zora', (68.5, -25.6))],
            'GoronCity': [('Repère des Bois Perdus', (26.7, -3.18))],
            'ZoraRiver': [('Vers les Bois Perdus', (122.57, -11.8)), ('Vers la plaine d’Hyrule', (-98, 28)),
                          ('Vers le Domaine Zora', (150, -40))],
            'HyruleField': [('Vers la Rivière Zora', (211, 148))],
            'ZoraDomain': [('Vers la Rivière Zora', (3.54, -42.38)), ('Vers la Fontaine Zora', (92.58, 15.57))],
            'ZoraFountain': [('Vers le Domaine Zora', (-19, -24.54))],
        }
        doc['scenes'] = {resource(region, age): {'rooms': [], 'points': points[region]}
                         for region in points for age in ('Child', 'Adult')}
        self.enterContext(patch.object(app, 'ensure_atlas'))
        app.load(doc)
        self.assertEqual(app.zones.get(), 'Bois Perdus')
        self.assertIn('Village Goron', app.zones['values'])
        self.assertFalse(any('Adulte' in label for label in app.zones['values']))
        app.age_buttons['Adult'].invoke()
        self.assertEqual(app.resource.get(), REGION_VIEWS['LostWood']['Adult'])
        for target, view in [('GoronCity', GORON_VIEWS['Adult'][GORON_LOST_WOODS_FLOOR]),
                             ('ZoraRiver', REGION_VIEWS['ZoraRiver']['Adult'])]:
            exits = app.canvas.find_withtag('zone-navigation')
            pin = next(item for item in exits if app.navigation_markers[item] == target)
            l, t, r, b = app.canvas.bbox(pin)
            app.press(SimpleNamespace(x=(l+r)//2, y=(t+b)//2))
            self.assertEqual(app.resource.get(), view)
            self.assertIn('LostWood', app.navigation_markers.values())
            if target == 'ZoraRiver':
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
            app.open_neighbor('LostWood')
            self.assertEqual(app.resource.get(), REGION_VIEWS['LostWood']['Adult'])

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
        from map_oot_rando.scene import REGION_VIEWS

        app = self.app
        doc = dict(demo_document(), provenance='ootrr-scan', locations=[],
                   regions=['KokiriForest', 'ZoraFountain', 'IceCavern'])
        native = 'Banc/ZoraFountain/ZoraFountain_{}_Static.bcett.byml.zs'
        doc['scenes'] = {
            native.format('Child'): {'rooms': [], 'points': [('Rive', (0, 0))]},
            native.format('Adult'): {'rooms': [], 'points': [('Vers la Caverne de glace', (47, -66))]},
            'Banc/IceCavern/IceCavern_Static.bcett.byml.zs':
                {'rooms': [], 'points': [('Vers la Fontaine Zora', (0, 105))]},
        }
        self.enterContext(patch.object(app, 'ensure_atlas'))
        app.load(doc)
        self.assertNotIn('IceCavern', app.available_neighbors())
        self.assertIn('IceCavern', app.world_targets())
        app.age_buttons['Adult'].invoke()
        self.assertIn('IceCavern', app.navigation_markers.values())
        app.open_neighbor('IceCavern')
        self.assertEqual(app.resource.get(), REGION_VIEWS['IceCavern'][None])
        self.assertFalse(app.floor_picker.winfo_ismapped())
        app.open_neighbor('ZoraFountain')
        self.assertEqual(app.resource.get(), REGION_VIEWS['ZoraFountain']['Adult'])

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
        from map_oot_rando.scene import REGION_VIEWS, TRAINING_VIEWS

        app = self.app
        fortress, ground = 'GerudoFortress', 'GerudoTrainingGround'
        doc = dict(demo_document(), provenance='ootrr-scan', regions=['KokiriForest', fortress, ground],
                   locations=[], scenes={
                       'Banc/GerudoFortress/GerudoFortress_Adult_Static.bcett.byml.zs':
                           {'rooms': [], 'points': [('Vers le centre d’entraînement', (5, 3))]},
                       'Banc/GerudoTrainingGround/GerudoTrainingGround_Static.bcett.byml.zs':
                           {'rooms': [], 'points': [('Vers la Forteresse Gerudo', (-1.75, 6.91))],
                            'level_points': [(1, 'Passerelle nord', (-2.36, -55.67))]},
                   })
        self.enterContext(patch.object(app, 'ensure_atlas'))
        app.load(doc)
        app.resource.set(REGION_VIEWS[fortress]['Adult'])
        app.resource_changed()
        self.assertIn(ground, app.navigation_markers.values())
        app.open_neighbor(ground)
        self.assertEqual(app.resource.get(), TRAINING_VIEWS[0])
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

    def test_water_temple_opens_from_the_adult_lake_at_the_top(self):
        from unittest.mock import patch
        from map_oot_rando.link_position import LinkPosition
        from map_oot_rando.scene import REGION_VIEWS, WATER_VIEWS

        app = self.app
        lake, temple = 'LakeHylia', 'WaterTemple'
        doc = dict(demo_document(), provenance='ootrr-scan',
                   regions=['KokiriForest', 'HyruleField', lake, temple], locations=[], scenes={
                       **{f'Banc/HyruleField/HyruleField_{age}_Static.bcett.byml.zs':
                          {'rooms': [], 'points': [('Vers le Temple de l’Eau', (-186, 499))]}
                          for age in ('Adult', 'Child')},
                       'Banc/WaterTemple/WaterTemple_Static.bcett.byml.zs':
                           {'rooms': [], 'points': [('Vers le Lac Hylia', (-4.5, 47))]},
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
        app.update_link(LinkPosition(temple, 'Adult', -4.5, 118.6, 43.61, 0))
        app.update_link(LinkPosition(temple, 'Adult', 12, 93, -4.5, 0))
        self.assertEqual(app.resource.get(), WATER_VIEWS[3])
        app.choose_age('Child')
        app.open_neighbor(lake)
        self.assertEqual(app.resource.get(), REGION_VIEWS[lake]['Adult'])

    def test_spirit_temple_hand_portal_opens_the_upper_floor(self):
        from unittest.mock import patch
        from map_oot_rando.link_position import LinkPosition
        from map_oot_rando.scene import REGION_VIEWS, SPIRIT_VIEWS

        app = self.app
        outside, temple = 'DesertColossus', 'SpiritTemple'
        colossus = 'Banc/DesertColossus/DesertColossus_Adult_Dynamic.bcett.byml.zs'
        interior = 'Banc/SpiritTemple/SpiritTemple_Dynamic.bcett.byml.zs'
        doc = dict(demo_document(), provenance='ootrr-scan', regions=['KokiriForest', outside, temple],
                   locations=[], scenes={
                       colossus: {'rooms': [], 'points': [('Vers le Temple de l’Esprit', (-161, 10)),
                                                         ('spirit_temple_right_hand_entrance', (-165, 36))]},
                       interior: {'rooms': [], 'points': [('Vers le Colosse du désert', (0, 13))],
                                  'level_points': [(2, 'right_hand_entrance', (-56, 44)),
                                                   (4, 'Arène de Twinrova', (0, -158))]},
                   })
        self.enterContext(patch.object(app, 'ensure_atlas'))
        app.load(doc)
        app.resource.set(REGION_VIEWS[outside]['Adult'])
        app.resource_changed()
        x, y = app.viewport.screen((-165, 36))
        app.press(SimpleNamespace(x=round(x), y=round(y)))
        self.assertEqual(app.resource.get(), SPIRIT_VIEWS[2])
        self.assertIn(outside, app.navigation_markers.values())
        app.open_neighbor(outside)
        self.assertEqual(app.resource.get(), REGION_VIEWS[outside]['Adult'])
        app.open_neighbor(temple)
        self.assertEqual(app.resource.get(), SPIRIT_VIEWS[0])
        app.update_link(LinkPosition(temple, 'Adult', 0, 100, 0, 0))
        app.update_link(LinkPosition(temple, 'Adult', 0, 145, -157, 0))
        self.assertEqual(app.resource.get(), SPIRIT_VIEWS[4])

    def test_ganon_castle_switches_scene_without_mixing_coordinates(self):
        from unittest.mock import patch
        from map_oot_rando.link_position import LinkPosition
        from map_oot_rando.scene import GANON_ESCAPE, GANON_OUTSKIRTS, REGION_VIEWS

        app = self.app
        template = demo_document()
        doc = dict(template, provenance='ootrr-scan',
                   regions=['KokiriForest', 'Market', 'HyruleCastle', 'GanonCastle'])
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
        app.update_link(LinkPosition('GanonCastle', 'Adult', 30, 100, 20, 0, 'FinalBattleField'))
        self.assertIsNone(app.link_view())

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
