"""Local Tk map. Importing this module never starts a tracker or memory reader."""
from collections import Counter
import json
from pathlib import Path
from queue import Empty, Queue
from threading import Thread
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageTk

from .aerial import AerialImage, read_image
from .aerial_dialog import align_image
from .field_atlas import CALIBRATION, align_kokiri_image, load_kokiri_image
from .map_projection import georeferenced_background
from .questfern import CALIBRATION as PAUSE_CALIBRATION, SOURCE_ID as PAUSE_SOURCE
from .questfern import align_pause_map, load_pause_map
from .export import import_seed
from .model import load_metadata, select
from .state import StateStore
from .save_profiles import SaveProfiles, local_tracker_dir
from .save_tracking import SaveConnection, SaveUpdate, apply_save_update
from .scene import AGE_VIEWS, field_atlas_scene, group_scenes, read_scenes, view_name
from .simulation import Simulation, demo_document
from .view import Viewport

PARCHMENT = '#d1bc80'
PAPER_COLORS = dict(available='#176346', blocked='#aa2540', unknown='#40359b',
                    completed='#535b6a', partial='#8a450d')

COLORS = dict(available='#37b76b', blocked='#e45c5c', unknown='#e6c548', completed='#929ba5', partial='#ed9f57')
LABELS = dict(available='Accessible', blocked='Bloqué', unknown='Inconnu', completed='Récupéré', partial='Partiellement accessible')


class MapApplication:
    def __init__(self, root, document=None, *, profiles=None):
        self.root = root
        root.title('Map-oot-rando - Kokiri Forest')
        root.geometry('1180x760')
        self.viewport = Viewport()
        self.selected = None
        self.drag = None
        self.query = tk.StringVar()
        self.resource = tk.StringVar()
        self.category = tk.StringVar(value='Toutes')
        self.status_vars = {key: tk.BooleanVar(value=True) for key in COLORS}
        self.banner = tk.StringVar()
        self.import_status = tk.StringVar()
        self.import_events = Queue()
        self.atlas_images = {}
        self.atlas_generation = 0
        self.save_generation = 0
        self.save_profiles = profiles if profiles is not None else SaveProfiles(local_tracker_dir() / 'profiles.json')
        self.save_commands = None
        self.follow_age = tk.BooleanVar(value=True)
        self.save_age = None
        self.show_outside = tk.BooleanVar(value=False)
        self.connection = tk.StringVar()
        self.details = tk.StringVar(value='Sélectionnez un emplacement.')
        self.count = tk.StringVar()
        top = ttk.Frame(root, padding=10)
        top.pack(fill='x')
        ttk.Label(top, textvariable=self.banner).pack(side='left')
        ttk.Button(top, text='Ouvrir métadonnées...', command=self.open_metadata).pack(side='right')
        ttk.Button(top, text='Simulation', command=lambda: self.load(demo_document())).pack(side='right')
        self.report_button = ttk.Button(top, text='Diagnostic de la carte…', command=self.save_diagnostic)
        self.report_button.pack(side='right', padx=(0, 8))
        import_bar = ttk.Frame(root, padding=(10, 0, 10, 0))
        import_bar.pack(fill='x')
        self.import_button = ttk.Button(import_bar, text='Importer mon jeu et ma seed…',
                                        command=self.choose_seed)
        self.import_button.pack(side='left')
        self.save_button = ttk.Button(import_bar, text='Enregistrer la carte…',
                                      command=self.save_map)
        self.save_button.pack(side='left', padx=8)
        self.track_button = ttk.Button(import_bar, text='Suivre ma sauvegarde…', command=self.choose_save)
        self.track_button.pack(side='left')
        self.stop_track_button = ttk.Button(import_bar, text='Arrêter le suivi', command=self.stop_tracking)
        self.stop_track_button.pack(side='left', padx=(6, 0))
        ttk.Label(import_bar, textvariable=self.import_status).pack(side='left', padx=8)
        ttk.Label(root, textvariable=self.connection, padding=8).pack(fill='x')
        body = ttk.Panedwindow(root, orient='horizontal')
        body.pack(fill='both', expand=True)
        sidebar = ttk.Frame(body, padding=10)
        body.add(sidebar, weight=0)
        ttk.Label(sidebar, text='Recherche : nom ou identifiant').pack(anchor='w')
        search = ttk.Entry(sidebar, textvariable=self.query, width=38)
        search.pack(fill='x')
        search.bind('<Return>', lambda e: self.choose_first())
        ttk.Label(sidebar, text='Vue de la forêt').pack(anchor='w', pady=(10, 0))
        self.resources = ttk.Combobox(sidebar, textvariable=self.resource, state='readonly', width=38)
        self.resources.pack(fill='x')
        self.resources.bind('<<ComboboxSelected>>', lambda e: self.resource_changed())
        self.follow_age_check = ttk.Checkbutton(sidebar, text='Suivre l’âge sauvegardé',
                                                variable=self.follow_age, command=self.sync_age)
        self.follow_age_check.pack(anchor='w')
        ttk.Label(sidebar, text='Catégorie').pack(anchor='w', pady=(10, 0))
        self.categories = ttk.Combobox(sidebar, textvariable=self.category, state='readonly')
        self.categories.pack(fill='x')
        self.categories.bind('<<ComboboxSelected>>', lambda e: self.render())
        for key in COLORS:
            ttk.Checkbutton(sidebar, text=LABELS[key], variable=self.status_vars[key],
                            command=self.render).pack(anchor='w')
        ttk.Checkbutton(sidebar, text='Afficher les checks hors du fond',
                        variable=self.show_outside, command=self.render).pack(anchor='w')
        results_panel = ttk.Frame(sidebar)
        results_panel.pack(fill='both', expand=True, pady=8)
        self.results = tk.Listbox(results_panel, height=10, exportselection=False)
        scrollbar = ttk.Scrollbar(results_panel, orient='vertical', command=self.results.yview)
        self.results.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side='right', fill='y')
        self.results.pack(side='left', fill='both', expand=True)
        self.results.bind('<<ListboxSelect>>', self.choose_list)
        ttk.Label(sidebar, textvariable=self.details, wraplength=300, justify='left').pack(fill='x')
        self.manual_button = ttk.Button(sidebar, text='Cocher manuellement', command=self.toggle_manual)
        self.sim_controls = ttk.LabelFrame(sidebar, text='Actions simulées', padding=6)
        for key in COLORS:
            ttk.Button(self.sim_controls, text=LABELS[key],
                       command=lambda s=key: self.simulate(s)).pack(fill='x')
        ttk.Button(self.sim_controls, text='Déconnecter / reconnecter',
                   command=self.toggle_connection).pack(fill='x')
        panel = ttk.Frame(body)
        body.add(panel, weight=1)
        tools = ttk.Frame(panel)
        tools.pack(fill='x')
        ttk.Button(tools, text='Ajuster la vue', command=self.fit).pack(side='left')
        self.atlas_button = ttk.Menubutton(tools, text='Fond de carte ▾')
        self.atlas_button.pack(side='left', padx=5)
        backgrounds = tk.Menu(self.atlas_button, tearoff=False)
        backgrounds.add_command(label='Carte du jeu (Questfern)',
                                command=lambda: self.choose_atlas(PAUSE_SOURCE))
        backgrounds.add_command(label='Field Atlas', command=lambda: self.choose_atlas('field-atlas'))
        backgrounds.add_command(label='Ouvrir une image locale…', command=self.choose_aerial)
        backgrounds.add_command(label='Afficher le schéma', command=self.remove_aerial)
        self.atlas_button.configure(menu=backgrounds)
        self.canvas = tk.Canvas(panel, background='#18252b', highlightthickness=0)
        self.canvas.pack(fill='both', expand=True)
        self.canvas.bind('<Configure>', self.resized)
        self.canvas.bind('<ButtonPress-1>', self.press)
        self.canvas.bind('<B1-Motion>', self.pan)
        self.canvas.bind('<MouseWheel>', lambda e: self.zoom(1.2 if e.delta > 0 else 1 / 1.2, e.x, e.y))
        self.canvas.bind('<Button-4>', lambda e: self.zoom(1.2, e.x, e.y))
        self.canvas.bind('<Button-5>', lambda e: self.zoom(1 / 1.2, e.x, e.y))
        ttk.Label(root, textvariable=self.count, padding=8).pack(fill='x')
        self.query.trace_add('write', lambda *args: self.render())
        self.load(document if document is not None else demo_document())
        root.after_idle(self.fit)

    def load(self, document, *, seed_folder=None):
        locations = load_metadata(document)  # Validate before replacing current state.
        scenes = group_scenes(read_scenes(document))
        aerial = {view_name(resource): AerialImage.from_document(row)
                  for resource, row in sorted(document.get('aerial', {}).items())}
        self.atlas_disabled = set()
        self.atlas_failed = set()
        self.atlas_loading = None
        self.atlas_generation += 1
        self.atlas_button.state(['!disabled'])
        self.atlas_button.configure(text='Fond de carte ▾')
        self.scenes = scenes
        self.aerial = aerial
        self.preferred_background = ('field-atlas' if document.get('preferred_background') == 'field-atlas'
                                     else PAUSE_SOURCE)
        self.document = document
        self.seed_folder = seed_folder
        self.save_generation += 1
        self.save_commands = None
        self.save_age = None
        self.follow_age.set(True)
        self.follow_age_check.state(['disabled'])
        self.manual_button.pack_forget()
        self.stop_track_button.state(['disabled'])
        self.tracked_rows = {}
        self.save_detail = ''
        self.locations = locations
        self.simulation = Simulation(locations) if document['provenance'] == 'synthetic' else None
        self.save_button.state(['disabled' if self.simulation else '!disabled'])
        self.track_button.state(['disabled' if self.simulation or not document.get('seed_id') else '!disabled'])
        self.report_button.state(['disabled' if self.simulation else '!disabled'])
        self.store = self.simulation.store if self.simulation else StateStore(document.get('seed_id', ''), [r.id for r in locations])
        self.selected = None
        self.details.set('Sélectionnez un emplacement.')
        self.banner.set('SIMULATION - noms et positions fictifs' if self.simulation else
                        'Kokiri Forest - seed importée')
        views = {view_name(row.resource) for row in locations if row.position is not None}
        prefer = [label for label in AGE_VIEWS.values() if label in views]
        self.resources['values'] = prefer + sorted(views - set(prefer))
        first_positioned = next((view_name(r.resource) for r in locations if r.position is not None), '')
        self.resource.set(prefer[0] if prefer else first_positioned or next(iter(sorted(views)), ''))
        self.categories['values'] = ['Toutes'] + sorted({r.category for r in locations})
        self.category.set('Toutes')
        if self.simulation:
            self.sim_controls.pack(fill='x', pady=8)
        else:
            self.sim_controls.pack_forget()
        self.query.set('')
        self.render()
        self.fit()
        self.ensure_atlas()
        if not self.simulation:
            resume = self.save_profiles.get(self.store.seed_id, automatic=True)
            if resume:
                folder, path = resume
                if seed_folder is not None:
                    folder = seed_folder
                if (folder / 'manifest.json').is_file() and path.is_file():
                    self.follow_save(folder, path)
                else:
                    self.save_detail = 'Sauvegarde ou dossier de seed déplacé.'
                    self.render()

    def choose_seed(self):
        nup = filedialog.askopenfilename(parent=self.root, title='Choisir le fichier NUP du jeu',
                                         filetypes=[('Jeu NUP', '*.nup')])
        if not nup:
            return
        checks = filedialog.askopenfilename(parent=self.root, title='Choisir le checks.json de la seed OotrR',
                                            filetypes=[('Catalogue JSON', '*.json')])
        if not checks:
            return
        self.import_button.state(['disabled'])
        self.import_status.set('Analyse locale du jeu en cours…')

        def scan():
            try:
                document = import_seed(nup, checks, lambda msg: self.import_events.put(('progress', msg)))
                self.import_events.put(('done', (document, Path(checks).resolve().parent)))
            except Exception as error:
                self.import_events.put(('error', str(error)))

        Thread(target=scan, daemon=True).start()
        self.root.after(100, self.poll_import)

    def poll_import(self):
        try:
            while True:
                event, value = self.import_events.get_nowait()
                if event == 'progress':
                    self.import_status.set(value)
                    continue
                self.import_button.state(['!disabled'])
                if event == 'done':
                    document, folder = value
                    self.load(document, seed_folder=folder)
                    missing = len(document['diagnostics'])
                    self.import_status.set(f'Carte chargée. {missing} check(s) sans position.')
                else:
                    self.import_status.set('Import interrompu.')
                    messagebox.showerror('Import impossible', value, parent=self.root)
                return
        except Empty:
            self.root.after(100, self.poll_import)

    def choose_save(self):
        previous = self.save_profiles.get(self.store.seed_id)
        folder = self.seed_folder or (previous[0] if previous else None)
        if folder is None or not (folder / 'manifest.json').is_file():
            checks = filedialog.askopenfilename(parent=self.root, title='Choisir le checks.json de cette seed',
                                                filetypes=[('Catalogue JSON', '*.json')])
            if not checks:
                return
            folder = Path(checks).resolve().parent
        initial = {'initialdir': previous[1].parent, 'initialfile': previous[1].name} if previous else {}
        save_path = filedialog.askopenfilename(parent=self.root, title='Choisir progress.sav',
                                              filetypes=[('Sauvegarde', '*.sav')], **initial)
        if not save_path:
            return
        self.follow_save(folder, save_path)

    def stop_tracking(self):
        self.save_generation += 1
        self.save_commands = None
        self.save_detail = ''
        try:
            self.save_profiles.pause(self.store.seed_id)
        except OSError:
            self.save_detail = 'Impossible de mémoriser l’arrêt du suivi.'
        self.store.disconnect()
        self.follow_age_check.state(['disabled'])
        self.stop_track_button.state(['disabled'])
        self.render()

    def follow_save(self, folder, save_path):
        self.save_generation += 1
        generation = self.save_generation
        store = self.store
        store.reset(store.seed_id, store.states)
        self.save_age = None
        self.follow_age_check.state(['disabled'])
        self.tracked_rows = {}
        commands = self.save_commands = Queue()
        remembered = False
        self.stop_track_button.state(['!disabled'])
        self.save_detail = 'Lecture de la sauvegarde…'
        self.render()

        def refresh(connection=None):
            if generation != self.save_generation:
                return
            result = Queue()

            def read():
                try:
                    active = connection or SaveConnection(folder, save_path, store)
                    changes = []
                    while True:
                        try:
                            changes.append(commands.get_nowait())
                        except Empty:
                            break
                    result.put((active, active.refresh(changes)))
                except Exception as error:
                    result.put((connection, SaveUpdate(str(error))))

            def publish():
                nonlocal remembered
                if generation != self.save_generation:
                    return
                try:
                    active, update = result.get_nowait()
                except Empty:
                    self.root.after(100, publish)
                    return
                apply_save_update(store, update)
                self.save_age = update.age
                self.follow_age_check.state(['!disabled' if update.age else 'disabled'])
                self.sync_age()
                if update.rows is not None or update.reset:
                    self.tracked_rows = update.rows or {}
                self.save_detail = update.detail
                if update.states is not None and not remembered:
                    remembered = True
                    try:
                        self.save_profiles.remember(store.seed_id, folder, save_path)
                    except OSError:
                        self.save_detail += ' | Le chemin n’a pas pu être mémorisé.'
                self.render()
                if update.action_error:
                    messagebox.showerror('Marquage manuel', update.action_error, parent=self.root)
                if active:
                    self.root.after(2000, refresh, active)
                else:
                    self.stop_track_button.state(['disabled'])

            Thread(target=read, daemon=True).start()
            self.root.after(100, publish)

        refresh()

    def toggle_manual(self):
        row = self.selected
        if self.save_commands is None or row is None or self.store.connection != 'save':
            return
        info = self.tracked_rows.get(row.id, {})
        if info.get('untracked'):
            self.save_commands.put((row.id, info.get('source') != 'manual'))
            self.manual_button.state(['disabled'])

    def save_diagnostic(self):
        path = filedialog.asksaveasfilename(parent=self.root, initialfile='kokiri-diagnostic.json',
                                            defaultextension='.json', filetypes=[('Diagnostic JSON', '*.json')])
        if not path:
            return
        # Keep only map metadata. No image, save bytes, local path or item rewards.
        diagnostic = {key: self.document[key] for key in (
            'schema_version', 'region', 'upstream_revision', 'provenance',
            'locations', 'scenes', 'diagnostics', 'map_capture_candidates') if key in self.document}
        try:
            Path(path).write_text(json.dumps(diagnostic, ensure_ascii=False, indent=2), encoding='utf-8')
        except OSError as error:
            messagebox.showerror('Enregistrement impossible', str(error), parent=self.root)

    def save_map(self):
        path = filedialog.asksaveasfilename(parent=self.root, initialfile='kokiri.json',
                                            defaultextension='.json', filetypes=[('Carte JSON', '*.json')])
        if path:
            try:
                with open(path, 'w', encoding='utf-8') as stream:
                    json.dump(dict(self.document, preferred_background=self.preferred_background,
                                   aerial={k: v.to_document() for k, v in self.aerial.items()}),
                              stream, ensure_ascii=False, indent=2)
            except OSError as error:
                messagebox.showerror('Enregistrement impossible', str(error), parent=self.root)

    def aerial_references(self, resource, *, include_checks=True, quiet=False):
        scene = (self.scenes.get(resource, {}) if include_checks
                 else field_atlas_scene(self.scenes, resource))
        references = [(name.replace('_', ' '), tuple(point))
                      for name, point in scene.get('points', ())]
        for name, low, high in scene.get('rooms', ()):
            label = 'shop room' if name == 'shop' else name.replace('_', ' ')
            references.append((label, ((low[0] + high[0])/2, (low[1] + high[1])/2)))
        if include_checks:
            references.extend((row.name, row.project()) for row in self.locations
                              if view_name(row.resource) == resource and row.position is not None)
        if len({point for _, point in references}) < 3:
            if quiet:
                return None
            messagebox.showinfo('Vue aérienne', 'Cette vue doit avoir au moins trois repères positionnés.',
                                parent=self.root)
            return None
        return references

    def choose_aerial(self):
        resource = self.resource.get()
        path = filedialog.askopenfilename(parent=self.root, title='Choisir une image vue du ciel',
                                          filetypes=[('PNG ou JPEG', '*.png *.jpg *.jpeg')])
        if not path:
            return
        try:
            background = georeferenced_background(path)
            if background:
                self.aerial[resource] = background
                self.render()
                self.fit()
                self.import_status.set('Fond aligné sur le fichier de coordonnées.')
                return
            image = read_image(path)
        except (OSError, ValueError, Image.DecompressionBombError) as error:
            messagebox.showerror('Image impossible à ouvrir', str(error), parent=self.root)
            return

        references = self.aerial_references(resource)
        if references is not None:
            self.align_background(resource, image, references)

    def choose_atlas(self, source):
        self.preferred_background = source
        self.ensure_atlas(manual=True)

    def ensure_atlas(self, *, manual=False):
        resource = self.resource.get()
        if self.simulation or resource not in AGE_VIEWS.values():
            if manual:
                messagebox.showinfo('Field Atlas', 'Choisis la vue enfant ou adulte de Kokiri Forest.',
                                    parent=self.root)
            return
        saved = self.aerial.get(resource)
        preferred = self.preferred_background
        current = saved and (saved.source not in {'field-atlas', PAUSE_SOURCE}
                             or (saved.source == preferred and saved.calibration ==
                                 (PAUSE_CALIBRATION if preferred == PAUSE_SOURCE else CALIBRATION)))
        if (self.atlas_loading or not manual and
                (current or resource in self.atlas_disabled | self.atlas_failed)):
            return
        references = self.aerial_references(resource, include_checks=False, quiet=not manual)
        if references is None:
            return
        generation = self.atlas_generation
        # Older Field Atlas JSON saved the original, unwarped raster. Reuse it
        # for an offline upgrade, but never warp a processed image twice.
        cached = dict(self.atlas_images)
        if saved and saved.source == 'field-atlas' and saved.calibration is None:
            cached.setdefault('field-atlas', saved.image)
        details = [(row.name, row.project()) for row in self.locations
                   if view_name(row.resource) == resource and row.position is not None]
        result = Queue()
        self.atlas_loading = resource
        self.atlas_button.state(['disabled'])
        self.atlas_button.configure(text='Chargement du fond…')

        def load():
            sources = [preferred] if manual or preferred == 'field-atlas' else [PAUSE_SOURCE, 'field-atlas']
            for source in sources:
                try:
                    loader, align = ((load_pause_map, align_pause_map) if source == PAUSE_SOURCE
                                     else (load_kokiri_image, align_kokiri_image))
                    if source not in cached:
                        cached[source] = loader()
                    result.put((cached, align(cached[source], references, details), None))
                    return
                except (OSError, ValueError) as error:
                    problem = str(error)
            result.put((cached, None, problem))

        def finish():
            if generation != self.atlas_generation:
                return
            try:
                images, background, error = result.get_nowait()
            except Empty:
                self.root.after(100, finish)
                return
            self.atlas_loading = None
            self.atlas_images = images
            self.atlas_button.state(['!disabled'])
            self.atlas_button.configure(text='Fond de carte ▾')
            if error:
                self.atlas_failed.add(resource)
                if self.resource.get() == resource:
                    self.import_status.set('Mise à jour du fond indisponible.' if saved else
                                           'Fond indisponible. Vue schématique affichée.')
                    if manual:
                        messagebox.showerror('Fond indisponible', error, parent=self.root)
            elif resource not in self.atlas_disabled or manual:
                self.atlas_disabled.discard(resource)
                if background.source == preferred:
                    self.atlas_failed.discard(resource)
                else:
                    self.atlas_failed.add(resource)
                self.aerial[resource] = background
                if self.resource.get() == resource:
                    self.render()
                    self.fit()
                    label = 'Questfern' if background.source == PAUSE_SOURCE else 'Field Atlas'
                    self.import_status.set(f'Fond {label} aligné.')
            if self.resource.get() != resource:
                self.ensure_atlas()

        Thread(target=load, daemon=True).start()
        self.root.after(100, finish)

    def align_background(self, resource, image, references):
        def install(background):
            self.aerial[resource] = background
            self.fit()

        align_image(self.root, image, references, install)

    def remove_aerial(self):
        view = self.resource.get()
        self.atlas_disabled.add(view)
        if self.aerial.pop(view, None) is not None:
            self.render()
            self.fit()

    def open_metadata(self):
        path = filedialog.askopenfilename(filetypes=[('Métadonnées JSON', '*.json')])
        if not path:
            return
        try:
            with open(path, encoding='utf-8') as stream:
                document = json.load(stream)
            self.load(document)
        except (OSError, ValueError, KeyError, TypeError, AttributeError, Image.DecompressionBombError) as error:
            messagebox.showerror('Métadonnées invalides', str(error))

    def render(self):
        if not hasattr(self, 'locations'):
            return
        view = self.resource.get()
        searching = bool(self.query.get().strip())
        rows = [row for row in self.locations
                if searching or view_name(row.resource) == view or row.position is None]
        unique = {(row.id, view_name(row.resource), row.position): row for row in rows}
        self.visible = select(unique.values(), self.store.states, self.query.get(),
                              {k for k, v in self.status_vars.items() if v.get()},
                              None if self.category.get() == 'Toutes' else {self.category.get()})
        list_position = self.results.yview()[0]
        self.results.delete(0, 'end')
        placements = Counter(row.id for row in self.visible)
        for row in self.visible:
            label = row.name
            if row.position is None:
                label += ' [sans coordonnées]'
            elif self.outside(row):
                label += ' [hors du fond]'
            elif placements[row.id] > 1:
                coordinates = ', '.join(f'{value:g}' for value in row.position)
                label += f' [{coordinates}]'
            self.results.insert('end', label)
        if self.selected in self.visible:
            self.results.selection_set(self.visible.index(self.selected))
        self.results.yview_moveto(list_position)
        missing = sum(r.position is None for r in self.visible)
        outside = sum(self.outside(row) for row in self.visible)
        self.count.set(f'{len(self.visible)} résultat(s) | {missing} sans coordonnées | {outside} hors du fond | '
                       'Molette : zoom ; glisser le fond : déplacer ; Entrée : premier résultat')
        mode = {'simulation': 'SIMULATION connectée', 'disconnected': 'Déconnecté - dernier état conservé',
                'save': 'Sauvegarde uniquement', 'live': 'Mémoire du jeu'}[self.store.connection]
        self.connection.set(f'{mode} | Dernière synchronisation (UTC) : {self.store.last_success or "aucune"}'
                            + (f' | {self.save_detail}' if self.save_detail else ''))
        if self.selected:
            self.show_details()
        self.draw()

    def sync_age(self):
        view = AGE_VIEWS.get(self.save_age)
        if (view and self.follow_age.get() and view != self.resource.get()
                and view in self.resources['values']):
            self.resource.set(view)
            self.resource_changed(manual=False)

    def resource_changed(self, *, manual=True):
        if manual and self.save_age is not None:
            self.follow_age.set(False)
        self.selected = None
        self.manual_button.pack_forget()
        self.details.set('Sélectionnez un emplacement.')
        self.render()
        self.fit()
        self.ensure_atlas()

    def outside(self, row):
        background = self.aerial.get(view_name(row.resource))
        return bool(background and row.position is not None and not background.covers(row.project()))

    def resized(self, event):
        if getattr(self, 'fit_pending', False):
            self.fit()
        else:
            self.draw()

    def display_point(self, point):
        aerial = self.aerial.get(self.resource.get())
        return aerial.image_point(point) if aerial and aerial.source == PAUSE_SOURCE else point

    def fit(self):
        self.fit_pending = self.canvas.winfo_width() <= 1 or self.canvas.winfo_height() <= 1
        if self.fit_pending:
            return
        points = [self.display_point(r.project()) for r in self.visible if view_name(r.resource) == self.resource.get() and r.position is not None
                  and (self.show_outside.get() or not self.outside(r))]
        aerial = self.aerial.get(self.resource.get())
        scene = self.scenes.get(self.resource.get(), {}) if not aerial else {}
        if aerial:
            if aerial.source == PAUSE_SOURCE:
                points.extend(((0, 0), aerial.image.size))
            else:
                points.extend(aerial.corners())
        points.extend(point for _, point in scene.get('points', ()))
        for _, low, high in scene.get('rooms', ()):
            points.extend((low, high))
        self.viewport.fit(points, self.canvas.winfo_width(), self.canvas.winfo_height())
        self.draw()

    def draw(self):
        if not hasattr(self, 'visible'):
            return
        self.canvas.delete('all')
        self.background_photo = None
        self.markers = {}
        width, height = self.canvas.winfo_width(), self.canvas.winfo_height()
        scene = self.scenes.get(self.resource.get())
        captions = []
        aerial = self.aerial.get(self.resource.get())
        parchment = bool(aerial and aerial.source == PAUSE_SOURCE)
        heading_color = '#292019' if parchment else '#d2e1da'
        if aerial:
            self.canvas.configure(background=PARCHMENT if parchment else '#18252b')
            raster = (aerial.render_image_view(self.viewport, (width, height), fillcolor=PARCHMENT, blend_paper=True)
                      if parchment else aerial.render(self.viewport, (width, height)))
            self.background_photo = ImageTk.PhotoImage(raster, master=self.canvas)
            self.canvas.create_image(0, 0, image=self.background_photo, anchor='nw', tags='aerial')
            heading = ('Kokiri Forest | Carte du jeu · Questfern' if aerial.source == PAUSE_SOURCE
                       else 'Kokiri Forest | Vue aérienne calibrée')
        elif scene:
            self.canvas.configure(background='#263c34')
            for name, low, high in scene['rooms']:
                x1, y1 = self.viewport.screen(low)
                x2, y2 = self.viewport.screen(high)
                self.canvas.create_rectangle(x1, y1, x2, y2, fill='#466356',
                                             outline='#aacbb4', width=2, tags='scene')
                captions.append((name, (x1 + x2) / 2, min(y1, y2) - 10))
            for name, point in scene['points']:
                x, y = self.viewport.screen(point)
                self.canvas.create_polygon(x, y-5, x+5, y, x, y+5, x-5, y,
                                           fill='#b4dec0', tags='scene')
                captions.append((name, x, y - 13))
            heading = 'Kokiri Forest | Maisons et repères (schéma)'
        else:
            self.canvas.configure(background='#18252b')
            step, xs, ys = self.viewport.grid(width, height)
            for x in xs:
                self.canvas.create_line(x, 0, x, height, fill='#2c414a')
            for y in ys:
                self.canvas.create_line(0, y, width, y, fill='#2c414a')
            heading = f'Schéma X/Z | Grille : {step:g} unités'
        self.canvas.create_text(12, 12, anchor='nw', fill=heading_color, text=heading)
        rows = [row for row in self.visible if view_name(row.resource) == self.resource.get()
                and row.position is not None
                and (self.show_outside.get() or row == self.selected or not self.outside(row))]
        rows.sort(key=lambda row: row == self.selected)
        labels = []
        for row in rows:
            x, y = self.viewport.screen(self.display_point(row.project()))
            palette = PAPER_COLORS if parchment else COLORS
            color = palette[self.store.states.get(row.id, 'unknown')]
            radius = 5.5 if parchment else 7
            outline = '#fff9ea' if parchment or row == self.selected else color
            if parchment and row == self.selected:
                ring = radius + 3
                self.canvas.create_oval(x-ring, y-ring, x+ring, y+ring, outline='#252038', width=2)
            item = self.canvas.create_oval(x-radius, y-radius, x+radius, y+radius,
                                          fill=color, outline=outline, width=2)
            self.markers[item] = row
            right = x <= width * 0.7
            labels.append((row.name, x + (12 if right else -12), y,
                           'w' if right else 'e', '#edf2f4', row))
        # Give the selected check first claim on label space, then the landmarks.
        used = [(0, 0, width, 30)]
        foreground = [label for label in labels if label[-1] == self.selected]
        background = [label for label in labels if label[-1] != self.selected]
        landmarks = [(name.replace('_', ' '), x, y, 'center', '#d0e8d8', None)
                     for name, x, y in captions]
        for name, x, y, anchor, color, row in foreground + landmarks + background:
            label = self.canvas.create_text(x, y, anchor=anchor, text=name, fill=color)
            left, top, right, bottom = self.canvas.bbox(label)
            if (any(left < r and right > l and top < b and bottom > t for l, t, r, b in used)
                    or right < 0 or bottom < 0 or left > width or top > height):
                self.canvas.delete(label)
                continue
            used.append((left, top, right, bottom))
            if row is not None:
                self.markers[label] = row
                if parchment:
                    box = self.canvas.create_rectangle(left-2, top-1, right+2, bottom+1,
                                                       fill='#2d263b', outline='', tags='check-label')
                    self.canvas.tag_lower(box, label)
                    self.markers[box] = row
        if not self.markers:
            self.canvas.create_text(25, 35, anchor='nw', text='Aucun marqueur positionné pour cette vue.', fill=heading_color)

    def choose(self, row):
        self.selected = row
        if row.position is not None:
            if self.resource.get() != view_name(row.resource):
                if self.save_age is not None:
                    self.follow_age.set(False)
                self.resource.set(view_name(row.resource))
                self.ensure_atlas()
            self.viewport.center(self.display_point(row.project()), self.canvas.winfo_width(),
                                 self.canvas.winfo_height())
        self.show_details()
        self.draw()

    def show_details(self):
        row = self.selected
        tracker = self.tracked_rows.get(row.id, {})
        if tracker.get('untracked') and self.store.connection == 'save':
            self.manual_button.configure(text=('Annuler le marquage manuel' if tracker.get('source') == 'manual'
                                               else 'Marquer comme récupéré'))
            self.manual_button.state(['!disabled'])
            self.manual_button.pack(fill='x', pady=(5, 0))
        else:
            self.manual_button.pack_forget()
        self.details.set(f'{row.name}\nID : {row.id}\n{row.category}\n{view_name(row.resource)}\n'
                         f'XYZ : {row.position if row.position is not None else "inconnues"}\n'
                         f'État : {LABELS[self.store.states.get(row.id, "unknown")]}'
                         + ('\nHors du fond de carte' if self.outside(row) else '')
                         + (f'\nObjet obtenu : {tracker["reward"]}' if tracker.get('reward') else '')
                         + ('\nCollecte sans indicateur de sauvegarde' if tracker.get('untracked') else '')
                         + ('\nMarqué manuellement' if tracker.get('source') == 'manual' else '')
                         + ('\nÂmes manquantes : ' + ', '.join(tracker['missing_souls'])
                            if tracker.get('missing_souls') else ''))

    def choose_first(self):
        if self.visible:
            self.choose(self.visible[0])

    def choose_list(self, event=None):
        indexes = self.results.curselection()
        if indexes:
            self.choose(self.visible[indexes[0]])

    def press(self, event):
        self.drag = None
        for item in reversed(self.canvas.find_overlapping(event.x-3, event.y-3, event.x+3, event.y+3)):
            if item in self.markers:
                self.choose(self.markers[item])
                return
        self.drag = (event.x, event.y)

    def pan(self, event):
        if self.drag:
            self.viewport.x += event.x - self.drag[0]
            self.viewport.y += event.y - self.drag[1]
            self.drag = (event.x, event.y)
            self.draw()

    def zoom(self, factor, x, y):
        self.viewport.zoom(factor, (x, y))
        self.draw()

    def simulate(self, status):
        if self.simulation and self.selected:
            self.simulation.change(self.selected.id, status)
            self.render()

    def toggle_connection(self):
        if self.simulation:
            self.simulation.toggle_connection()
            self.render()
