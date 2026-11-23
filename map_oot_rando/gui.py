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
from .field_atlas import align_kokiri_image, load_kokiri_image
from .export import import_seed
from .model import load_metadata, select
from .state import StateStore
from .save_tracking import SaveConnection, SaveUpdate, apply_save_update
from .scene import AGE_VIEWS, field_atlas_scene, group_scenes, read_scenes, view_name
from .simulation import Simulation, demo_document
from .view import Viewport

COLORS = dict(available='#37b76b', blocked='#e45c5c', unknown='#e6c548', completed='#929ba5', partial='#ed9f57')
LABELS = dict(available='Accessible', blocked='Bloqué', unknown='Inconnu', completed='Récupéré', partial='Partiellement accessible')


class MapApplication:
    def __init__(self, root, document=None):
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
        self.atlas_image = None
        self.atlas_generation = 0
        self.save_generation = 0
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
        ttk.Button(tools, text='Ajouter une vue aérienne…',
                   command=self.choose_aerial).pack(side='left', padx=5)
        self.atlas_button = ttk.Button(tools, text='Fond Field Atlas…', command=self.choose_field_atlas)
        self.atlas_button.pack(side='left', padx=(0, 5))
        ttk.Button(tools, text='Retirer le fond image',
                   command=self.remove_aerial).pack(side='left')
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
        self.atlas_button.configure(text='Fond Field Atlas…')
        self.scenes = scenes
        self.aerial = aerial
        self.document = document
        self.seed_folder = seed_folder
        self.save_generation += 1
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
        folder = self.seed_folder
        if folder is None:
            checks = filedialog.askopenfilename(parent=self.root, title='Choisir le checks.json de cette seed',
                                                filetypes=[('Catalogue JSON', '*.json')])
            if not checks:
                return
            folder = Path(checks).resolve().parent
        save_path = filedialog.askopenfilename(parent=self.root, title='Choisir progress.sav',
                                              filetypes=[('Sauvegarde', '*.sav')])
        if not save_path:
            return
        self.follow_save(folder, save_path)

    def stop_tracking(self):
        self.save_generation += 1
        self.store.disconnect()
        self.stop_track_button.state(['disabled'])
        self.save_detail = ''
        self.render()

    def follow_save(self, folder, save_path):
        self.save_generation += 1
        generation = self.save_generation
        store = self.store
        store.reset(store.seed_id, store.states)
        self.tracked_rows = {}
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
                    result.put((active, active.refresh()))
                except Exception as error:
                    result.put((connection, SaveUpdate(str(error))))

            def publish():
                if generation != self.save_generation:
                    return
                try:
                    active, update = result.get_nowait()
                except Empty:
                    self.root.after(100, publish)
                    return
                apply_save_update(store, update)
                if update.rows is not None or update.reset:
                    self.tracked_rows = update.rows or {}
                self.save_detail = update.detail
                self.render()
                if active:
                    self.root.after(2000, refresh, active)
                else:
                    self.stop_track_button.state(['disabled'])

            Thread(target=read, daemon=True).start()
            self.root.after(100, publish)

        refresh()

    def save_diagnostic(self):
        path = filedialog.asksaveasfilename(parent=self.root, initialfile='kokiri-diagnostic.json',
                                            defaultextension='.json', filetypes=[('Diagnostic JSON', '*.json')])
        if not path:
            return
        # Keep only map metadata. No image, save bytes, local path or item rewards.
        diagnostic = {key: self.document[key] for key in (
            'schema_version', 'region', 'upstream_revision', 'provenance',
            'locations', 'scenes', 'diagnostics') if key in self.document}
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
                    json.dump(dict(self.document, aerial={k: v.to_document() for k, v in self.aerial.items()}),
                              stream, ensure_ascii=False, indent=2)
            except OSError as error:
                messagebox.showerror('Enregistrement impossible', str(error), parent=self.root)

    def aerial_references(self, resource, *, include_checks=True, quiet=False):
        scene = (self.scenes.get(resource, {}) if include_checks
                 else field_atlas_scene(self.scenes, resource))
        references = [(name.replace('_', ' '), tuple(point))
                      for name, point in scene.get('points', ())]
        for name, low, high in scene.get('rooms', ()):
            references.append((name.replace('_', ' '), ((low[0] + high[0])/2, (low[1] + high[1])/2)))
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
        references = self.aerial_references(resource)
        if references is None:
            return
        path = filedialog.askopenfilename(parent=self.root, title='Choisir une image vue du ciel',
                                          filetypes=[('PNG ou JPEG', '*.png *.jpg *.jpeg')])
        if not path:
            return
        try:
            image = read_image(path)
        except (OSError, ValueError, Image.DecompressionBombError) as error:
            messagebox.showerror('Image impossible à ouvrir', str(error), parent=self.root)
            return

        self.align_background(resource, image, references)

    def choose_field_atlas(self):
        self.ensure_atlas(manual=True)

    def ensure_atlas(self, *, manual=False):
        resource = self.resource.get()
        if self.simulation or resource not in AGE_VIEWS.values():
            if manual:
                messagebox.showinfo('Field Atlas', 'Choisis la vue enfant ou adulte de Kokiri Forest.',
                                    parent=self.root)
            return
        if (self.atlas_loading or not manual and
                resource in self.aerial.keys() | self.atlas_disabled | self.atlas_failed):
            return
        references = self.aerial_references(resource, include_checks=False, quiet=not manual)
        if references is None:
            return
        generation = self.atlas_generation
        cached = self.atlas_image
        result = Queue()
        self.atlas_loading = resource
        self.atlas_button.state(['disabled'])
        self.atlas_button.configure(text='Chargement Field Atlas…')

        def load():
            image = cached
            try:
                image = image or load_kokiri_image()
                result.put((image, align_kokiri_image(image, references), None))
            except (OSError, ValueError) as error:
                result.put((image, None, str(error)))

        def finish():
            if generation != self.atlas_generation:
                return
            try:
                image, background, error = result.get_nowait()
            except Empty:
                self.root.after(100, finish)
                return
            self.atlas_loading = None
            self.atlas_image = image
            self.atlas_button.state(['!disabled'])
            self.atlas_button.configure(text='Fond Field Atlas…')
            if error:
                self.atlas_failed.add(resource)
                if self.resource.get() == resource:
                    self.import_status.set('Fond indisponible. Vue schématique affichée.')
                    if manual:
                        messagebox.showerror('Field Atlas indisponible', error, parent=self.root)
            elif resource not in self.atlas_disabled or manual:
                self.atlas_disabled.discard(resource)
                self.atlas_failed.discard(resource)
                self.aerial[resource] = background
                if self.resource.get() == resource:
                    self.render()
                    self.fit()
                    self.import_status.set('Fond Field Atlas aligné sur les maisons. Position approximative.')
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

    def resource_changed(self):
        self.selected = None
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

    def fit(self):
        self.fit_pending = self.canvas.winfo_width() <= 1 or self.canvas.winfo_height() <= 1
        if self.fit_pending:
            return
        points = [r.project() for r in self.visible if view_name(r.resource) == self.resource.get() and r.position is not None
                  and (self.show_outside.get() or not self.outside(r))]
        aerial = self.aerial.get(self.resource.get())
        scene = self.scenes.get(self.resource.get(), {}) if not aerial else {}
        if aerial:
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
        if aerial:
            self.canvas.configure(background='#18252b')
            self.background_photo = ImageTk.PhotoImage(aerial.render(self.viewport, (width, height)),
                                                       master=self.canvas)
            self.canvas.create_image(0, 0, image=self.background_photo, anchor='nw', tags='aerial')
            heading = 'Kokiri Forest | Vue aérienne calibrée'
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
        self.canvas.create_text(12, 12, anchor='nw', fill='#d2e1da', text=heading)
        rows = [row for row in self.visible if view_name(row.resource) == self.resource.get()
                and row.position is not None
                and (self.show_outside.get() or row == self.selected or not self.outside(row))]
        rows.sort(key=lambda row: row == self.selected)
        labels = []
        for row in rows:
            x, y = self.viewport.screen(row.project())
            color = COLORS[self.store.states.get(row.id, 'unknown')]
            item = self.canvas.create_oval(x-7, y-7, x+7, y+7, fill=color,
                                          outline='white' if row == self.selected else color, width=2)
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
        if not self.markers:
            self.canvas.create_text(25, 35, anchor='nw', text='Aucun marqueur positionné pour cette vue.', fill='white')

    def choose(self, row):
        self.selected = row
        if row.position is not None:
            if self.resource.get() != view_name(row.resource):
                self.resource.set(view_name(row.resource))
                self.ensure_atlas()
            self.viewport.center(row.project(), self.canvas.winfo_width(), self.canvas.winfo_height())
        self.show_details()
        self.draw()

    def show_details(self):
        row = self.selected
        tracker = self.tracked_rows.get(row.id, {})
        self.details.set(f'{row.name}\nID : {row.id}\n{row.category}\n{view_name(row.resource)}\n'
                         f'XYZ : {row.position if row.position is not None else "inconnues"}\n'
                         f'État : {LABELS[self.store.states.get(row.id, "unknown")]}'
                         + ('\nHors du dessin Field Atlas' if self.outside(row) else '')
                         + (f'\nObjet obtenu : {tracker["reward"]}' if tracker.get('reward') else '')
                         + ('\nCollecte sans indicateur de sauvegarde' if tracker.get('untracked') else '')
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
