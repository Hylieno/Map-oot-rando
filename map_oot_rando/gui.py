"""Local Tk map. Importing this module never starts a tracker or memory reader."""
from collections import Counter
import json
from math import cos, radians, sin
from pathlib import Path
from queue import Empty, Queue
from threading import Event, Lock, Thread
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageTk

from .aerial import AerialImage
from .field_atlas import (CALIBRATION, FIELD_FRAMES, REGION_CALIBRATION, REGION_MAPS, align_region_image,
                           align_kokiri_image, load_atlas_image, load_kokiri_image)
from .lost_woods import (BRIDGE_CALIBRATION, BRIDGE_SOURCE, CALIBRATION as LOST_CALIBRATION,
                         SOURCE as LOST_SOURCE, kokiri_bridge_plan, lost_woods_plan)
from .export import import_seed
from .import_dialog import ImportDialog
from .model import Location, REGION_NAMES, SURFACE_MIN_Y, load_metadata, resource_region, select
from .state import StateStore
from .save_profiles import SaveProfiles, local_tracker_dir
from .save_tracking import SaveConnection, SaveUpdate, apply_save_update
from .scene import (BURNT_VILLAGE, CASTLE_COURT, DAMPE_ROUTES, DREAM_BATTLE_VIEWS, DREAM_SCENE_VIEWS,
                    DUNGEON_ATLAS_KEYS, DUNGEON_FLOORS,
                    FIRE_KAKARIKO_ARRIVAL, FIRE_KAKARIKO_CONTINUE, FIRE_VIEWS, FLOOR_OPTIONS,
                    FOUNTAIN_DUNGEON_AGES, GANON_DUNGEON_VIEWS, GANON_ESCAPE, GANON_ESCAPE_ROUTE, GANON_FINAL,
                    GANONDORF_TILE, GANON_TRIAL_ROOM_CENTER, GANON_TRIAL_VIEWS,
                    MARKET_CASTLE_AGES, MARKET_TREASURE_VIEW,
                    GORON_CRATER_FLOOR, GORON_FLOORS, GORON_LOST_WOODS_FLOOR,
                    GORON_LEVELS, GORON_VIEWS, GUIDE_ROUTE, LOST_WOOD_RESET,
                    NEIGHBORS, PORTAL_ARRIVAL_STARTS, PORTAL_START_NAMES, REGION_VIEWS, SHARED_DUNGEONS,
                    SHADOW_SHIP_ROUTE, SIDE_PORTALS, TRAINING_LOCKED_DOOR, TRAINING_VIEWS,
                    UNDERGROUND_LABELS, UNDERGROUND_VIEWS, UNPOSITIONED_CHECK_AREAS, VIEWS, WATER_CONTROL_LABELS,
                    castle_view, field_area, field_atlas_scene, group_scenes, kokiri_bridge_position,
                    location_view, read_scenes, temple_position, treasure_game_at, view_name)
from .simulation import Simulation
from . import theme
from .view import Viewport
from .welcome import Welcome
from .world_map import WORLD_PIN_PARENTS, WORLD_PINS, WORLD_SIZE, load_world_map

ATLAS_BACKGROUND = '#0d1f2e'
ATLAS_FAILURE_DETAILS = {
    'missing_reference_points': 'Repères d’alignement insuffisants.',
    'asset_unavailable': 'Image Field Atlas inaccessible.',
    'asset_invalid': 'Image Field Atlas invalide ou modifiée.',
    'alignment_failed': 'L’image Field Atlas n’a pas pu être alignée.',
}
WORLD_BACKGROUND = '#47351c'
OVERVIEW_SCALE = 0.42
AGE_LABELS = {'Child': 'Enfant', 'Adult': 'Adulte'}

COLORS = dict(available='#37b76b', blocked='#e45c5c', unknown='#e6c548', completed='#929ba5', partial='#ed9f57')
LABELS = dict(available='Accessible', blocked='Bloqué', unknown='Inconnu', completed='Récupéré', partial='Partiellement accessible')


def view_contains(view, local_view):
    return view == local_view or (view == GANON_DUNGEON_VIEWS[0] and local_view in GANON_TRIAL_VIEWS)


def background_spec(view):
    region, age = VIEWS.get(view, (None, None))
    if (view in (CASTLE_COURT, MARKET_TREASURE_VIEW, GANON_ESCAPE, GANON_FINAL) or view in UNDERGROUND_LABELS
            or GORON_FLOORS.get(view) == len(GORON_LEVELS) - 1):
        return None
    if region == 'KokiriForest':
        return 'field-atlas', CALIBRATION, None
    if region == 'LostWood':
        return LOST_SOURCE, LOST_CALIBRATION, None
    if region == 'KokiriBridge':
        return BRIDGE_SOURCE, BRIDGE_CALIBRATION, None
    entry = REGION_MAPS.get(region, {}).get(DUNGEON_ATLAS_KEYS.get(view, age))
    if entry:
        return entry[0], REGION_CALIBRATION, entry[1]
    return None


class MapApplication:
    def __init__(self, root, document=None, *, profiles=None):
        self.root = root
        root.title('Map-oot-rando')
        root.geometry('1200x800')
        root.minsize(780, 660)
        theme.install(root)
        self.viewport = Viewport()
        self.viewport_adjusted = False
        self.overview_open = False
        self.world_loading = False
        self.world_callback = None
        self.world_image = None
        self.world_photo_size = None
        self.world_photo = None
        self.link = None
        self.link_area = None
        self.use_link = Event()
        self.fitted_scale = self.viewport.scale
        self.selected = None
        self.arrival = None
        self.drag = None
        self.query = tk.StringVar()
        self.resource = tk.StringVar()
        self.category = tk.StringVar(value='Toutes')
        self.status_vars = {key: tk.BooleanVar(value=True) for key in COLORS}
        self.banner = tk.StringVar()
        self.import_status = tk.StringVar()
        self.import_events = Queue()
        self.import_callback = None
        self.atlas_images = {}
        self.atlas_generation = 0
        self.atlas_callback = None
        self.save_generation = 0
        self.tracking_owner = Lock()
        self.tracking_stop = Event()
        self.use_live = Event()
        self.live_requested = tk.BooleanVar(value=False)
        self.show_link = tk.BooleanVar(value=False)
        self.save_profiles = profiles if profiles is not None else SaveProfiles(local_tracker_dir() / 'profiles.json')
        self.follow_link = tk.BooleanVar(value=self.save_profiles.follow_link_enabled())
        self.link_status = tk.StringVar()
        root.protocol('WM_DELETE_WINDOW', self.close_window)
        self.save_commands = None
        self.verified_save_source = None
        self.follow_age = tk.BooleanVar(value=True)
        self.save_age = None
        self.kakariko_burned = None
        self.show_outside = tk.BooleanVar(value=False)
        self.connection = tk.StringVar()
        self.details = tk.StringVar(value='Sélectionnez un emplacement.')
        self.count = tk.StringVar()
        header = ttk.Frame(root, padding=(20, 12))
        header.pack(fill='x')
        emblem = tk.Canvas(header, width=38, height=42, background=theme.PANEL, highlightthickness=0)
        emblem.create_polygon(19, 3, 36, 21, 19, 39, 2, 21, outline=theme.GOLD, fill=theme.FIELD)
        emblem.create_polygon(19, 9, 22, 18, 30, 21, 22, 24, 19, 33, 16, 24, 8, 21, 16, 18,
                              fill=theme.GOLD)
        emblem.create_oval(17, 19, 21, 23, fill=theme.FIELD, outline='')
        emblem.pack(side='left', padx=(0, 12))
        brand = ttk.Frame(header)
        brand.pack(side='left')
        ttk.Label(brand, text='Map-oot-rando', style='Title.TLabel').pack(anchor='w')
        ttk.Label(brand, textvariable=self.banner, style='Muted.TLabel').pack(anchor='w')

        tools_button = ttk.Menubutton(header, text='Carte')
        tools_button.pack(side='right', padx=(8, 0))
        self.file_menu = theme.menu(tools_button)
        tools_button.configure(menu=self.file_menu)
        self.file_menu.add_command(label='Ouvrir une carte enregistrée...', command=self.open_metadata)
        self.file_menu.add_command(label='Enregistrer la carte...', command=self.save_map, state='disabled')
        self.file_menu.add_separator()
        self.file_menu.add_command(label='Exporter le diagnostic...', command=self.save_diagnostic, state='disabled')
        self.import_button = ttk.Button(header, text='Importer mon jeu et ma seed...', style='Accent.TButton',
                                        command=self.choose_seed)
        ttk.Frame(root, style='Divider.TFrame', height=1).pack(fill='x')

        self.tracking_strip = ttk.Frame(root, padding=(20, 7))
        self.track_button = ttk.Button(self.tracking_strip, text='Dossier de sauvegardes...', command=self.choose_save)
        self.track_button.pack(side='left')
        self.stop_track_button = ttk.Button(self.tracking_strip, text='Arrêter le suivi', command=self.stop_tracking)
        self.stop_track_button.pack(side='left', padx=(6, 0))
        self.live_check = ttk.Checkbutton(self.tracking_strip, text='Mémoire du jeu',
                                          variable=self.live_requested, command=self.configure_live)
        self.live_check.pack(side='left', padx=(12, 15))
        connection_label = ttk.Label(self.tracking_strip, textvariable=self.connection, style='Muted.TLabel')
        connection_label.pack(side='left', fill='x', expand=True)
        connection_label.bind('<Configure>', lambda e: connection_label.configure(wraplength=max(1, e.width)))

        self.workspace = ttk.Frame(root, style='Shell.TFrame', padding=(14, 12, 14, 0))
        self.workspace.pack(fill='both', expand=True)
        self.welcome = Welcome(self.workspace, self.choose_seed, self.import_status)
        self.body = body = ttk.Panedwindow(self.workspace, orient='horizontal')
        sidebar = ttk.Frame(body, padding=(12, 10))
        body.add(sidebar, weight=0)
        ttk.Label(sidebar, text='Rechercher un check', style='Section.TLabel').pack(anchor='w')
        search = ttk.Entry(sidebar, textvariable=self.query, width=32)
        search.pack(fill='x')
        search.bind('<Return>', lambda e: self.choose_first())
        ttk.Label(sidebar, text='Zone', style='Section.TLabel').pack(anchor='w', pady=(9, 2))
        self.zones = ttk.Combobox(sidebar, state='readonly', width=29)
        self.zones.pack(fill='x')
        self.zones.bind('<<ComboboxSelected>>', self.choose_zone)
        ages = ttk.Frame(sidebar)
        ages.pack(fill='x', pady=(4, 2))
        self.age_buttons = {}
        for age, label in AGE_LABELS.items():
            button = ttk.Button(ages, text=label, style='Age.TButton', command=lambda value=age: self.choose_age(value))
            button.pack(side='left', padx=(0, 5))
            self.age_buttons[age] = button
        self.follow_age_check = ttk.Checkbutton(sidebar, text='Suivre l’âge sauvegardé',
                                                variable=self.follow_age, command=self.sync_age)
        self.follow_age_check.pack(anchor='w')
        self.link_check = ttk.Checkbutton(sidebar, text='Afficher la position de Link',
                                          variable=self.show_link, command=self.configure_link)
        self.link_check.pack(anchor='w')
        self.follow_link_check = ttk.Checkbutton(sidebar, text='Suivre Link entre les zones',
                                                 variable=self.follow_link, command=self.configure_follow_link)
        self.follow_link_check.pack(anchor='w')
        link_panel = ttk.Frame(sidebar)
        link_panel.pack(fill='x')
        self.link_status_label = ttk.Label(link_panel, textvariable=self.link_status, wraplength=245,
                                           style='Muted.TLabel')
        self.link_zone_button = tk.Button(link_panel, textvariable=self.link_status, wraplength=252,
                                          justify='left', anchor='w', cursor='hand2', bg=theme.FIELD, fg=theme.GOLD,
                                          activebackground=theme.SELECTION, activeforeground=theme.CREAM,
                                          highlightbackground=theme.PANEL, relief='flat', command=self.show_link_zone)
        ttk.Label(sidebar, text='Filtres', style='Section.TLabel').pack(anchor='w', pady=(8, 2))
        self.categories = ttk.Combobox(sidebar, textvariable=self.category, state='readonly')
        self.categories.pack(fill='x')
        self.categories.bind('<<ComboboxSelected>>', lambda e: self.render())
        statuses = ttk.Frame(sidebar)
        statuses.pack(fill='x', pady=(3, 0))
        for index, (key, color) in enumerate(COLORS.items()):
            label = 'Accès partiel' if key == 'partial' else LABELS[key]
            status_style = f'{key}.TCheckbutton'
            ttk.Style(root).configure(status_style, foreground=color)
            ttk.Checkbutton(statuses, text=label, style=status_style, variable=self.status_vars[key],
                            command=self.render).grid(row=index // 2, column=index % 2, sticky='w', padx=(0, 10))
        ttk.Checkbutton(sidebar, text='Afficher les checks hors du fond',
                        variable=self.show_outside, command=self.render).pack(anchor='w')
        detail_panel = ttk.Frame(sidebar)
        detail_panel.pack(side='bottom', fill='x')
        detail_scroll = ttk.Scrollbar(detail_panel, orient='vertical')
        detail_text = tk.Text(detail_panel, height=3, width=28, wrap='word', font='TkDefaultFont',
                              padx=7, pady=5, background=theme.FIELD, foreground=theme.CREAM,
                              highlightthickness=0, borderwidth=0, yscrollcommand=detail_scroll.set)
        detail_scroll.configure(command=detail_text.yview)
        detail_scroll.pack(side='right', fill='y')
        detail_text.pack(side='left', fill='x', expand=True)

        def update_details(*_):
            value = self.details.get()
            if detail_text.get('1.0', 'end-1c') == value:
                return
            detail_text.configure(state='normal')
            detail_text.replace('1.0', 'end', value)
            detail_text.configure(state='disabled')

        self.details.trace_add('write', update_details)
        self.manual_button = ttk.Button(sidebar, text='Cocher manuellement', command=self.toggle_manual)
        results_panel = ttk.Frame(sidebar)
        results_panel.pack(fill='both', expand=True, pady=(6, 4))
        scrollbar = ttk.Scrollbar(results_panel, orient='vertical')
        self.results = tk.Listbox(results_panel, height=1, exportselection=False, background=theme.FIELD,
                                  foreground=theme.CREAM, selectbackground=theme.SELECTION,
                                  selectforeground=theme.CREAM, highlightcolor=theme.GOLD,
                                  highlightbackground=theme.EDGE, highlightthickness=1, borderwidth=0,
                                  activestyle='none', font='TkDefaultFont', yscrollcommand=scrollbar.set)
        scrollbar.configure(command=self.results.yview)
        scrollbar.pack(side='right', fill='y')
        self.results.pack(side='left', fill='both', expand=True)
        self.results.bind('<<ListboxSelect>>', self.choose_list)
        panel = ttk.Frame(body)
        body.add(panel, weight=1)
        tool_rows = ttk.Frame(panel, padding=(8, 6))
        tool_rows.pack(fill='x')
        self.map_tools = tools = ttk.Frame(tool_rows)
        tools.pack(fill='x')
        ttk.Button(tools, text='Ajuster la vue', command=self.fit_detail).pack(side='left')
        self.neighbor_bar = ttk.Frame(tool_rows)
        self.neighbor_buttons = {
            region: ttk.Button(self.neighbor_bar, text=name, command=lambda target=region: self.open_neighbor(target))
            for region, name in REGION_NAMES.items()
        }
        self.neighbor_menu = theme.menu(self.neighbor_bar)
        self.neighbor_menu_button = ttk.Menubutton(self.neighbor_bar, text='Zones voisines', menu=self.neighbor_menu)
        self.neighbor_targets = ()
        self.neighbor_layout = None
        tools.bind('<Configure>', self.layout_neighbors)
        self.overview_button = ttk.Button(tools, text='Carte d’Hyrule', command=self.toggle_overview)
        self.floor_button = ttk.Button(tools, command=self.toggle_floor)
        self.floor_picker = ttk.Combobox(tools, state='readonly', width=27)
        self.floor_picker.bind('<<ComboboxSelected>>', self.choose_floor)
        self.canvas = tk.Canvas(panel, background='#18252b', highlightthickness=0)
        self.canvas_size = None
        self.canvas.pack(fill='both', expand=True)
        self.canvas.bind('<Configure>', self.resized)
        self.canvas.bind('<ButtonPress-1>', self.press)
        self.canvas.bind('<B1-Motion>', self.pan)
        self.canvas.bind('<Motion>', self.world_hover)
        self.canvas.bind('<Leave>', lambda _: self.world_hover(None))
        self.canvas.bind('<MouseWheel>', lambda e: self.zoom(1.2 if e.delta > 0 else 1 / 1.2, e.x, e.y))
        self.canvas.bind('<Button-4>', lambda e: self.zoom(1.2, e.x, e.y))
        self.canvas.bind('<Button-5>', lambda e: self.zoom(1 / 1.2, e.x, e.y))
        self.marker_menu = theme.menu(self.canvas)
        self.footer = ttk.Frame(root, padding=(20, 6))
        ttk.Label(self.footer, textvariable=self.count, style='Muted.TLabel').pack(side='left')
        ttk.Label(self.footer, textvariable=self.import_status, style='Muted.TLabel').pack(side='right')
        self.query.trace_add('write', lambda *args: self.render())
        self.document = None
        self.visible = ()
        self.banner.set('Compagnon Ocarina of Time Remake')
        if document is None:
            self.welcome.pack(fill='both', expand=True, pady=(0, 12))
        else:
            self.load(document)

    def load(self, document, *, seed_folder=None):
        locations = load_metadata(document)  # Validate before replacing current state.
        scenes = group_scenes(read_scenes(document))
        synthetic = document['provenance'] == 'synthetic'
        seed_id = document.get('seed_id', '')
        old_store = getattr(self, 'store', None)
        same_seed = (not synthetic and bool(seed_id) and old_store is not None
                     and not old_store.simulated and old_store.seed_id == seed_id)
        resume_snapshot = same_seed and old_store.last_success is not None
        if not resume_snapshot:
            self.verified_save_source = None
        previous_view = self.resource.get() if same_seed else ''
        previous_age = self.navigation_age if same_seed else None
        aerial = {}
        for resource, row in sorted(document.get('aerial', {}).items()):
            view = view_name(resource)
            spec = background_spec(view)
            if synthetic or spec and (row.get('source'), row.get('calibration')) == spec[:2]:
                aerial[view] = AerialImage.from_document(row)
        self.aerial = aerial
        self.atlas_failed = {}
        self.atlas_loading = None
        self.atlas_generation += 1
        if self.atlas_callback is not None:
            self.root.after_cancel(self.atlas_callback)
            self.atlas_callback = None
        self.scenes = scenes
        self.document = document
        self.seed_folder = seed_folder
        self.tracking_stop.set()
        self.save_generation += 1
        self.save_commands = None
        self.link = None
        self.link_area = None
        self.save_age = None
        self.kakariko_burned = None
        if not same_seed:
            self.follow_age.set(True)
        self.follow_age_check.state(['disabled'])
        self.manual_button.pack_forget()
        self.stop_track_button.state(['disabled'])
        self.tracked_rows = {}
        self.save_detail = ''
        self.locations = locations
        self.simulation = Simulation(locations) if document['provenance'] == 'synthetic' else None
        if self.simulation:
            self.show_link.set(False)
        self.link_check.state(['disabled' if self.simulation else '!disabled'])
        document_state = 'disabled' if synthetic else 'normal'
        self.file_menu.entryconfigure('Enregistrer la carte...', state=document_state)
        self.file_menu.entryconfigure('Exporter le diagnostic...', state=document_state)
        track_state = 'disabled' if self.simulation or not document.get('seed_id') else '!disabled'
        self.track_button.state([track_state])
        self.live_check.state([track_state])
        self.store = self.simulation.store if self.simulation else StateStore(seed_id, [r.id for r in locations])
        if resume_snapshot:
            self.store.states.update((ident, old_store.states[ident])
                                     for ident in self.store.states.keys() & old_store.states.keys())
            self.store.last_success = old_store.last_success
        self.selected = None
        self.details.set('Sélectionnez un emplacement.')
        views = {location_view(row) for row in locations if row.position is not None}
        views.update(self.scenes.keys() & VIEWS.keys())
        for floors in DUNGEON_FLOORS.values():
            if floors[0][1] in views:
                views.update(view for _, view in floors if view in DUNGEON_ATLAS_KEYS)
        for goron_views in GORON_VIEWS.values():
            points = {name for name, _ in self.scenes.get(goron_views[0], {}).get('points', ())}
            for target, floor in (('DeathMountainCrater', GORON_CRATER_FLOOR),
                                  ('LostWood', GORON_LOST_WOODS_FLOOR)):
                if NEIGHBORS['GoronCity'][target] in points:
                    views.add(goron_views[floor])
        prefer = [label for label in VIEWS if label in views]
        self.views = prefer + sorted(views - set(prefer))
        available_regions = {VIEWS[view][0] for view in self.views if view in VIEWS}
        self.zone_targets = {label: region for region, label in REGION_NAMES.items() if region in available_regions}
        if BURNT_VILLAGE in self.views:
            self.zone_targets[BURNT_VILLAGE] = None
        self.zone_targets.update((view, None) for view in self.views if view not in VIEWS)
        self.zones['values'] = tuple(self.zone_targets)
        first_positioned = next((location_view(r) for r in locations if r.position is not None), '')
        self.navigation_age = previous_age
        initial_view = prefer[0] if prefer else first_positioned or next(iter(sorted(views)), '')
        self.resource.set(previous_view if previous_view in views else initial_view)
        self.categories['values'] = ['Toutes'] + sorted({r.category for r in locations})
        self.category.set('Toutes')
        self.welcome.pack_forget()
        self.import_button.pack(side='right')
        self.tracking_strip.pack(fill='x', before=self.workspace)
        self.body.pack(fill='both', expand=True)
        self.footer.pack(side='bottom', fill='x', before=self.workspace)
        self.query.set('')
        self.resource_changed(manual=False)
        self.configure_link()
        if not self.simulation:
            resume = self.save_profiles.get(self.store.seed_id, automatic=True)
            if resume:
                folder, path = resume
                if seed_folder is not None:
                    folder = seed_folder
                path = self.save_root(path)
                if (folder / 'manifest.json').is_file() and path.is_dir():
                    self.follow_save(folder, path, preserve_snapshot=resume_snapshot)
                else:
                    self.save_detail = 'Sauvegarde ou dossier de seed déplacé.'
                    self.render()

    def choose_seed(self):
        return ImportDialog(self.root, self.start_import)

    def start_import(self, nup, checks):
        self.import_button.state(['disabled'])
        self.welcome.import_button.state(['disabled'])
        self.file_menu.entryconfigure('Ouvrir une carte enregistrée...', state='disabled')
        self.import_status.set('Analyse locale du jeu en cours…')

        def scan():
            try:
                document = import_seed(nup, checks, lambda msg: self.import_events.put(('progress', msg)))
                self.import_events.put(('done', (document, Path(checks).resolve().parent)))
            except Exception as error:
                self.import_events.put(('error', str(error)))

        Thread(target=scan, daemon=True).start()
        self.import_callback = self.root.after(100, self.poll_import)

    def poll_import(self):
        if self.import_callback is not None:
            self.root.after_cancel(self.import_callback)
            self.import_callback = None
        try:
            while True:
                event, value = self.import_events.get_nowait()
                if event == 'progress':
                    self.import_status.set(value)
                    continue
                self.import_button.state(['!disabled'])
                self.welcome.import_button.state(['!disabled'])
                self.file_menu.entryconfigure('Ouvrir une carte enregistrée...', state='normal')
                if event == 'done':
                    document, folder = value
                    self.load(document, seed_folder=folder)
                    if not self.import_status.get():
                        self.import_status.set('Carte chargée.')
                else:
                    self.import_status.set('Import interrompu.')
                    messagebox.showerror('Import impossible', value, parent=self.root)
                return
        except Empty:
            self.import_callback = self.root.after(100, self.poll_import)

    def choose_save(self):
        previous = self.save_profiles.get(self.store.seed_id)
        folder = self.seed_folder or (previous[0] if previous else None)
        if folder is None or not (folder / 'manifest.json').is_file():
            checks = filedialog.askopenfilename(parent=self.root, title='Choisir le checks.json de cette seed',
                                                filetypes=[('Catalogue JSON', '*.json')])
            if not checks:
                return
            folder = Path(checks).resolve().parent
        initial = {'initialdir': self.save_root(previous[1])} if previous else {}
        save_dir = filedialog.askdirectory(parent=self.root, title='Choisir le dossier des sauvegardes',
                                          mustexist=True, **initial)
        if save_dir:
            self.follow_save(folder, Path(save_dir).resolve())

    @staticmethod
    def save_root(path):
        # Migrate profiles that remember one file rather than a directory.
        return path.parent if path.suffix.casefold() == '.sav' else path

    def configure_live(self):
        if self.live_requested.get():
            self.use_live.set()
        else:
            self.use_live.clear()
            self.link_area = None
        if self.use_link.is_set():
            self.update_link(None)

    def configure_link(self):
        self.link_area = None
        enabled = self.show_link.get() and not self.simulation
        if enabled:
            self.use_link.set()
            self.live_requested.set(True)
            self.configure_live()
        else:
            self.use_link.clear()
            self.update_link(None)
        self.follow_link_check.state(['!disabled' if enabled else 'disabled'])

    def link_message(self):
        if not self.use_link.is_set():
            return ''
        if self.save_commands is None:
            return 'Choisis le dossier de sauvegardes pour suivre Link.'
        if not self.use_live.is_set():
            return 'Active « Mémoire du jeu » pour afficher Link.'
        if self.store.connection == 'live':
            return 'Mémoire connectée · En attente de la position de Link'
        return 'En attente d’une partie en mémoire liée à cette seed.'

    def configure_follow_link(self):
        self.resume_follow_link()
        try:
            self.save_profiles.remember_follow_link(self.follow_link.get())
        except OSError:
            self.import_status.set('Le choix de suivi de Link n’a pas pu être mémorisé.')

    def link_region(self):
        scene = self.link.scene
        if scene == 'HyruleField':
            area = field_area((self.link.x, self.link.z))
            if REGION_VIEWS[area].get(self.link.age) in self.views:
                return area
        if scene == 'Market' and temple_position((self.link.x, self.link.z), self.link.age):
            if REGION_VIEWS['TempleOfTime'].get(self.link.age) in self.views:
                return 'TempleOfTime'
        if (scene == 'KokiriForest' and kokiri_bridge_position((self.link.x, self.link.z))
                and REGION_VIEWS['KokiriBridge'].get(self.link.age) in self.views):
            return 'KokiriBridge'
        return {'LostWoods': 'LostWood', 'DekuTree': 'InsideTheDekuTree',
                'CastleGrounds': 'HyruleCastle',
                'ZorasRiver': 'ZoraRiver', 'ZorasDomain': 'ZoraDomain',
                'ZorasFountain': 'ZoraFountain', 'JabuJabusBelly': 'InsideJabuJabuBelly'}.get(scene, scene)

    def link_view(self):
        region = self.link_region()
        age = self.link.age
        position = self.link.x, self.link.y, self.link.z
        if region not in REGION_VIEWS:
            return None
        if region == 'KakarikoVillage' and age == 'Adult':
            burned = self.link.scene_alternative
            if burned is None:
                burned = self.kakariko_burned
            view = BURNT_VILLAGE if burned else REGION_VIEWS[region][age]
            return view if view in self.views else None
        view = self.view_for_region(region, age=age, from_portal=False)
        if region == 'Market' and age == 'Child' and MARKET_TREASURE_VIEW in self.views and treasure_game_at(position):
            return MARKET_TREASURE_VIEW
        if region == 'HyruleCastle':
            subarea = castle_view(self.link.z)
            return subarea if subarea in self.views else view
        if region == 'GanonCastle':
            if self.link.scene_resource == 'CrumblingGanonCastle':
                return GANON_ESCAPE if GANON_ESCAPE in self.views else None
            if self.link.scene_resource == 'FinalBattleField':
                return GANON_FINAL if GANON_FINAL in self.views else None
        if region == 'DreamWorld':
            scene_view = DREAM_SCENE_VIEWS.get(self.link.scene_resource)
            return scene_view if scene_view in self.views else None
        if region in DUNGEON_FLOORS or region == 'GoronCity' or region in SURFACE_MIN_Y:
            suffix = 'Static' if region in DUNGEON_FLOORS else f'{age}_Static'
            path = f'Banc/{region}/{region}_{suffix}.bcett.byml.zs'
            underground = region in SURFACE_MIN_Y and self.link.y < SURFACE_MIN_Y[region]
            row = Location('', '', '', path, position, region=region, underground=underground)
            level = location_view(row)
            if region == 'FireTemple' and self.link.x <= -64.5 and -15 < self.link.z < 15 and 95 < self.link.y < 112:
                level = FIRE_VIEWS[-1]
            if level in self.views:
                return level
        return view

    def update_link(self, position):
        changed = self.link != position
        self.link = position
        if position is None and self.store.connection != 'live':
            # Reacquire the map after a real disconnect, even in the same area.
            self.link_area = None
        view = self.link_view() if position else None
        if view:
            self.link_status.set(f'Link · {view}')
            if not self.link_zone_button.winfo_manager():
                self.link_status_label.pack_forget()
                self.link_zone_button.pack(fill='x')
        else:
            self.link_status.set('Zone de Link hors carte' if position else self.link_message())
            self.link_zone_button.pack_forget()
            if self.link_status.get():
                self.link_status_label.pack(anchor='w')
            else:
                self.link_status_label.pack_forget()
        area = (position.scene, position.age, view) if position else None
        if area is not None and area != self.link_area:
            self.link_area = area
            if view and self.resume_follow_link():
                return
        if changed:
            self.draw()

    def show_link_zone(self, view=None):
        if self.link and (view := view or self.link_view()):
            self.navigation_age = self.link.age
            self.resource.set(view)
            self.resource_changed(manual=False)
            return True
        return False

    def resume_follow_link(self):
        if self.follow_link.get() and self.link:
            view = self.link_view()
            if view and (self.resource.get() != view or self.overview_open):
                return self.show_link_zone(view)
            if view and self.navigation_age != self.link.age:
                self.navigation_age = self.link.age
                self.refresh_navigation()
        return False

    def draw_link_pin(self, x, y, yaw):
        angle = radians(yaw)
        axis_x, axis_y = sin(angle), -cos(angle)
        arrow = (x + 12*axis_x, y + 12*axis_y,
                 x - 5*axis_x - 7*axis_y, y - 5*axis_y + 7*axis_x,
                 x - 2*axis_x, y - 2*axis_y,
                 x - 5*axis_x + 7*axis_y, y - 5*axis_y - 7*axis_x)
        ring = self.canvas.create_oval(x-11, y-11, x+11, y+11, fill='#0a332f',
                                       outline='#9df4b4', width=2, tags='player-pin')
        heading = self.canvas.create_polygon(*arrow, fill='#9df4b4', outline='#0a332f', tags='player-pin')
        return ring, heading

    def close_window(self):
        self.tracking_stop.set()
        for callback in (self.atlas_callback, self.world_callback, self.import_callback):
            if callback is not None:
                self.root.after_cancel(callback)
        self.root.destroy()

    def stop_tracking(self):
        self.tracking_stop.set()
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
        self.link_area = None
        self.update_link(None)
        self.render()

    def follow_save(self, folder, save_path, *, preserve_snapshot=False):
        self.tracking_stop.set()
        cancel = self.tracking_stop = Event()
        self.save_generation += 1
        generation = self.save_generation
        store = self.store
        preferred_save = None
        if preserve_snapshot:
            store.disconnect()
            if self.verified_save_source and self.verified_save_source[0] == save_path:
                preferred_save = self.verified_save_source[1]
        else:
            store.reset(store.seed_id, store.states)
            self.verified_save_source = None
        self.save_age = None
        self.kakariko_burned = None
        self.follow_age_check.state(['disabled'])
        self.tracked_rows = {}
        commands = self.save_commands = Queue()
        results = Queue()
        remembered = False
        self.stop_track_button.state(['!disabled'])
        self.save_detail = 'Recherche d’une sauvegarde liée à la seed…'
        self.link_area = None
        self.update_link(None)
        self.render()

        def read():
            with self.tracking_owner:
                if cancel.is_set():
                    return
                try:
                    active = SaveConnection(folder, save_path, store, preferred_save=preferred_save)
                except Exception as error:
                    results.put((SaveUpdate(str(error), reset=isinstance(error, ValueError)), False))
                    return
                try:
                    while not cancel.is_set():
                        changes = []
                        while True:
                            try:
                                changes.append(commands.get_nowait())
                            except Empty:
                                break
                        try:
                            update = active.refresh(changes, live=self.use_live.is_set(), show_link=self.use_link.is_set())
                        except Exception as error:
                            update = SaveUpdate(str(error))
                        results.put((update, True))
                        cancel.wait(1 if self.use_live.is_set() else 2)
                finally:
                    active.close()

        def publish():
            nonlocal remembered
            if generation != self.save_generation:
                return
            try:
                update, active = results.get_nowait()
            except Empty:
                self.root.after(100, publish)
                return
            apply_save_update(store, update)
            if update.save_path is not None:
                self.verified_save_source = (save_path, update.save_path)
            elif update.reset:
                self.verified_save_source = None
            self.save_age = update.age
            self.kakariko_burned = update.kakariko_burned
            if not active:
                self.save_commands = None
            self.update_link(update.link if self.use_link.is_set() and self.use_live.is_set() else None)
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
                self.root.after(100, publish)
            else:
                self.stop_track_button.state(['disabled'])

        Thread(target=read, daemon=True).start()
        self.root.after(100, publish)

    def toggle_manual(self):
        row = self.selected
        if self.save_commands is None or row is None or self.store.connection not in {'save', 'live'}:
            return
        info = self.tracked_rows.get(row.id, {})
        if info.get('untracked'):
            self.save_commands.put((row.id, info.get('source') != 'manual'))
            self.manual_button.state(['disabled'])

    def save_diagnostic(self, *, path=None):
        if path is None:
            path = filedialog.asksaveasfilename(parent=self.root, initialfile='diagnostic-carte.json',
                                                defaultextension='.json', filetypes=[('Diagnostic JSON', '*.json')])
        if not path:
            return
        # Keep only map metadata. No image, save bytes, local path or item rewards.
        diagnostic = {key: self.document[key] for key in (
            'schema_version', 'region', 'regions', 'upstream_revision', 'provenance',
            'locations', 'scenes', 'diagnostics', 'map_capture_candidates') if key in self.document}
        coverage = {view: {'source': background.source, 'image_size': background.image.size,
                           'checked': 0, 'outside': []}
                    for view, background in self.aerial.items()
                    if (background.source or '').startswith('field-atlas')}
        placements = Counter()
        for row in self.locations:
            if row.position is None:
                continue
            view = location_view(row)
            placements[view] += 1
            if view not in coverage:
                continue
            report = coverage[view]
            background = self.aerial[view]
            pixel = background.image_point(row.project())
            outcome = background.atlas_coverage(pixel)
            report['checked'] += 1
            if outcome != 'drawn':
                report['outside'].append(dict(id=row.id, position=row.position, entrance=row.entrance,
                                              pixel=tuple(round(value, 2) for value in pixel),
                                              reason=outcome))
        diagnostic['atlas_coverage'] = coverage
        views = {}
        for view in sorted(set(self.views) | placements.keys() | coverage.keys()):
            spec = background_spec(view)
            if view in coverage:
                status = 'checked'
            elif view in self.aerial:
                status = 'local_plan'
            elif view == self.atlas_loading:
                status = 'loading'
            elif view in self.atlas_failed:
                status = 'unavailable'
            else:
                status = 'not_loaded' if spec else 'schematic'
            source = self.aerial[view].source if view in self.aerial else (spec[0] if spec else None)
            views[view] = {'source': source, 'status': status, 'placements': placements[view]}
            if status == 'unavailable':
                views[view]['reason'] = self.atlas_failed[view]
        diagnostic['map_views'] = views
        try:
            Path(path).write_text(json.dumps(diagnostic, ensure_ascii=False, indent=2), encoding='utf-8')
        except OSError as error:
            messagebox.showerror('Enregistrement impossible', str(error), parent=self.root)

    def save_map(self):
        path = filedialog.asksaveasfilename(parent=self.root, initialfile='carte.json',
                                            defaultextension='.json', filetypes=[('Carte JSON', '*.json')])
        if path:
            try:
                with open(path, 'w', encoding='utf-8') as stream:
                    document = dict(self.document, aerial={k: v.to_document() for k, v in self.aerial.items()})
                    document.pop('preferred_background', None)
                    json.dump(document, stream, ensure_ascii=False, indent=2)
            except OSError as error:
                messagebox.showerror('Enregistrement impossible', str(error), parent=self.root)

    def aerial_references(self, resource):
        reference_view = FLOOR_OPTIONS[resource][0][1] if resource in FLOOR_OPTIONS else resource
        scene = field_atlas_scene(self.scenes, reference_view)
        references = [(name.replace('_', ' '), tuple(point))
                      for name, point in scene.get('points', ())]
        for name, low, high in scene.get('rooms', ()):
            label = 'shop room' if name == 'shop' else name.replace('_', ' ')
            references.append((label, ((low[0] + high[0])/2, (low[1] + high[1])/2)))
        return references

    def note_atlas_failure(self, view, reason):
        self.atlas_failed[view] = reason
        if self.resource.get() == view:
            self.import_status.set(f'{ATLAS_FAILURE_DETAILS[reason]} Vue schématique affichée.')

    def ensure_atlas(self):
        view = self.resource.get()
        if self.simulation or view in self.aerial or view in self.atlas_failed:
            return
        spec = background_spec(view)
        if spec is None:
            return
        source, _, digest = spec
        region, age = VIEWS[view]
        if region in {'LostWood', 'KokiriBridge'}:
            self.aerial[view] = (lost_woods_plan if region == 'LostWood' else kokiri_bridge_plan)()
            self.render()
            self.fit()
            return
        if self.atlas_loading:
            return
        atlas_key = DUNGEON_ATLAS_KEYS.get(view, age)
        references = self.aerial_references(view)
        if region not in FIELD_FRAMES and len({point for _, point in references}) < 3:
            self.note_atlas_failure(view, 'missing_reference_points')
            return
        details = [(row.name, row.project()) for row in self.locations
                   if location_view(row) == view and row.position is not None]
        generation = self.atlas_generation
        cached = self.atlas_images.get(source)
        result = Queue()
        self.atlas_loading = view

        def load():
            try:
                image = cached
                if image is None:
                    if region == 'KokiriForest':
                        image = load_kokiri_image()
                    else:
                        width = 700 if view in DUNGEON_ATLAS_KEYS else 650
                        image = load_atlas_image(digest, width=width)
            except (ValueError, Image.DecompressionBombError):
                result.put((None, None, 'asset_invalid'))
                return
            except OSError:
                result.put((None, None, 'asset_unavailable'))
                return
            try:
                background = (align_kokiri_image(image, references, details) if region == 'KokiriForest'
                              else align_region_image(image, references, region, atlas_key))
            except ValueError:
                result.put((image, None, 'alignment_failed'))
            else:
                result.put((image, background, None))

        def finish():
            self.atlas_callback = None
            if generation != self.atlas_generation:
                return
            try:
                image, background, failure = result.get_nowait()
            except Empty:
                self.atlas_callback = self.root.after(100, finish)
                return
            self.atlas_loading = None
            if image is not None:
                self.atlas_images[source] = image
            if failure:
                self.note_atlas_failure(view, failure)
            else:
                self.aerial[view] = background
                if self.resource.get() == view:
                    self.import_status.set('')
                    self.render()
                    selected = self.selected
                    focus = (selected.project() if selected and selected.position is not None
                             and location_view(selected) == view else None)
                    self.fit(focus=focus, preserve_viewport=self.viewport_adjusted)
            if self.resource.get() != view:
                self.ensure_atlas()

        Thread(target=load, daemon=True).start()
        self.atlas_callback = self.root.after(100, finish)

    def open_metadata(self):
        path = filedialog.askopenfilename(parent=self.root, title='Ouvrir une carte enregistrée',
                                          filetypes=[('Carte JSON', '*.json')])
        if not path:
            return
        try:
            with open(path, encoding='utf-8') as stream:
                document = json.load(stream)
            self.load(document)
        except (OSError, ValueError, KeyError, TypeError, AttributeError, Image.DecompressionBombError) as error:
            messagebox.showerror('Carte invalide', str(error), parent=self.root)

    def render(self):
        if not hasattr(self, 'locations'):
            return
        view = self.resource.get()
        region = self.current_region()
        searching = bool(self.query.get().strip())
        rows = [row for row in self.locations
                if searching or view_contains(view, location_view(row))
                or (row.position is None and row.region == region)]
        unique = {(row.id, row.region, location_view(row), row.position, row.entrance): row for row in rows}
        self.visible = select(unique.values(), self.store.states, self.query.get(),
                              {k for k, v in self.status_vars.items() if v.get()},
                              None if self.category.get() == 'Toutes' else {self.category.get()})
        list_position = self.results.yview()[0]
        self.results.delete(0, 'end')
        result_views = [location_view(row) for row in self.visible]
        placements = Counter((row.id, target) for row, target in zip(self.visible, result_views))
        for row, target in zip(self.visible, result_views):
            label = row.name
            if searching and target != view:
                destination = target if target in self.views else REGION_NAMES.get(row.region)
                if destination:
                    label += f' · {destination}'
            if row.position is None:
                label += ' [sans coordonnées]'
            elif self.outside(row):
                label += ' [hors du fond]'
            elif row.entrance:
                label += ' [grotte]'
            elif placements[row.id, target] > 1:
                coordinates = ', '.join(f'{value:g}' for value in row.position)
                label += f' [{coordinates}]'
            self.results.insert('end', label)
        if self.selected in self.visible:
            self.results.selection_set(self.visible.index(self.selected))
        self.results.yview_moveto(list_position)
        missing = sum(r.position is None for r in self.visible)
        outside = sum(self.outside(row) for row in self.visible)
        counters = [f'{len(self.visible)} résultat(s)']
        if missing:
            counters.append(f'{missing} sans coordonnées')
        if outside:
            counters.append(f'{outside} hors du fond')
        self.count.set('   ·   '.join(counters))
        mode = {'simulation': 'SIMULATION connectée', 'disconnected': 'Déconnecté - dernier état conservé',
                'save': 'Sauvegarde uniquement', 'live': 'Mémoire du jeu'}[self.store.connection]
        self.connection.set(f'{mode} | Dernière synchronisation (UTC) : {self.store.last_success or "aucune"}'
                            + (f' | {self.save_detail}' if self.save_detail else ''))
        if self.selected:
            self.show_details()
        self.draw()

    def sync_age(self):
        if not self.save_age or not self.follow_age.get():
            return
        if self.overview_open:
            if self.navigation_age != self.save_age:
                self.navigation_age = self.save_age
                self.refresh_age_buttons()
                self.draw()
            return
        if self.follow_link.get() and self.link and self.link_region() == self.current_region():
            return
        if self.current_region() in SHARED_DUNGEONS:
            self.navigation_age = self.save_age
            self.refresh_navigation()
            return
        if self.resource.get() == BURNT_VILLAGE and self.save_age == 'Adult' and self.kakariko_burned is None:
            return
        view = self.view_for_age(self.save_age)
        if view and view != self.resource.get():
            self.resource.set(view)
            self.resource_changed(manual=False)

    def view_for_age(self, age):
        region = self.current_region()
        if age not in REGION_VIEWS[region]:
            return None
        if self.resource.get() in (CASTLE_COURT, GANON_ESCAPE, GANON_FINAL):
            return self.resource.get()
        view = self.view_for_region(region, age=age, from_portal=False)
        if self.resource.get() in GORON_FLOORS:
            same_floor = GORON_VIEWS[age][GORON_FLOORS[self.resource.get()]]
            if same_floor in self.views:
                view = same_floor
        if self.resource.get() in UNDERGROUND_LABELS:
            underground = UNDERGROUND_VIEWS[self.current_region()][age]
            if underground in self.views:
                view = underground
        return view

    def choose_age(self, age):
        if self.overview_open or self.current_region() in SHARED_DUNGEONS:
            self.navigation_age = age
            self.follow_age.set(False)
            self.refresh_navigation()
            self.draw()
            return
        view = self.view_for_age(age)
        if view:
            self.resource.set(view)
            self.resource_changed()

    def choose_zone(self, _event):
        target = self.zones.get()
        region = self.zone_targets.get(target)
        view = self.browse_view(region) if region else target
        if view in self.views:
            self.resource.set(view)
            self.resource_changed(manual=False)
        else:
            self.refresh_navigation()

    def current_region(self):
        view = self.resource.get()
        return VIEWS[view][0] if view in VIEWS else resource_region(view) or 'KokiriForest'

    def view_for_region(self, region, *, age=None, from_portal=True):
        if age is None:
            _, age = VIEWS.get(self.resource.get(), (self.current_region(), self.save_age))
        if age is None:
            age = self.navigation_age
        if from_portal:
            origin = self.current_region()
            if origin == 'HyruleField' and region == 'KokiriForest':
                bridge = REGION_VIEWS['KokiriBridge'].get(age)
                if bridge in self.views:
                    return bridge
            if origin == 'SageRoom' and region == 'TempleOfTime':
                age = 'Adult'
            if {origin, region} == {'LakeHylia', 'ZoraDomain'} and age != 'Child':
                return None
            if region == 'WaterTemple' and origin == 'LakeHylia' and age != 'Adult':
                return None
            if region == 'LakeHylia' and origin == 'WaterTemple':
                age = 'Adult'
            if origin == 'GerudoTrainingGround' and region == 'GerudoFortress':
                if self.resource.get() != TRAINING_VIEWS[0]:
                    return None
                age = 'Adult'
            if region == 'GerudoFortress' and age != 'Adult':
                return None
            if origin == 'Market' and region in MARKET_CASTLE_AGES and age != MARKET_CASTLE_AGES[region]:
                return None
            if self.resource.get() in (GANON_ESCAPE, GANON_FINAL):
                return None
            if origin == 'InsideGanonCastle' and region == 'GanonCastle' and self.resource.get() != GANON_DUNGEON_VIEWS[0]:
                return None
            if origin == 'ZoraFountain' and region in FOUNTAIN_DUNGEON_AGES and age != FOUNTAIN_DUNGEON_AGES[region]:
                return None
            if region == 'ZoraFountain' and origin in FOUNTAIN_DUNGEON_AGES:
                age = FOUNTAIN_DUNGEON_AGES[origin]
        # A known age must be preserved across the transition.
        ages = REGION_VIEWS[region]
        candidates = (ages[age],) if age in ages else ages.values()
        if from_portal and region == 'GoronCity' and age in GORON_VIEWS:
            floor = {'DeathMountainCrater': GORON_CRATER_FLOOR,
                     'LostWood': GORON_LOST_WOODS_FLOOR}.get(origin)
            if floor is not None:
                candidates = (GORON_VIEWS[age][floor], *candidates)
        if (region == 'KakarikoVillage' and age == 'Adult' and self.follow_age.get()
                and self.kakariko_burned):
            candidates = (BURNT_VILLAGE, *candidates)
        return next((view for view in candidates if view in self.views), None)

    def open_neighbor(self, region, *, view=None, arrival=None):
        if view is None:
            view = self.browse_view(region) if self.overview_open else self.view_for_region(region)
        if view:
            self.resource.set(view)
            self.resource_changed(manual=False, arrival=arrival)

    def browse_view(self, region):
        age = self.navigation_age if self.overview_open else None
        view = self.view_for_region(region, age=age, from_portal=False)
        return view or next((label for label in self.views if VIEWS.get(label, (None, None))[0] == region), None)

    def world_targets(self):
        targets = {region: view for region in (*WORLD_PINS, *WORLD_PIN_PARENTS)
                   if (view := self.browse_view(region))}
        if MARKET_CASTLE_AGES.keys() <= targets.keys():
            _, view_age = VIEWS.get(self.resource.get(), (None, None))
            age = (self.navigation_age if self.overview_open else view_age) or self.navigation_age or 'Child'
            for region, castle_age in MARKET_CASTLE_AGES.items():
                if castle_age != age:
                    del targets[region]
        return targets

    def available_neighbors(self):
        region = self.current_region()
        return [neighbor for neighbor in NEIGHBORS[region] if self.view_for_region(neighbor)]

    def floor_target(self):
        view = self.resource.get()
        region, age = VIEWS.get(view, (None, None))
        if region not in UNDERGROUND_VIEWS:
            return None
        underground = UNDERGROUND_VIEWS[region][age]
        target = REGION_VIEWS[region][age] if view == underground else underground
        return target if target in self.views else None

    def toggle_floor(self):
        view = self.floor_target()
        if view:
            self.resource.set(view)
            self.resource_changed(manual=False)

    def choose_floor(self, _event):
        options = dict(FLOOR_OPTIONS[self.resource.get()])
        self.resource.set(options[self.floor_picker.get()])
        self.resource_changed(manual=False)

    def refresh_age_buttons(self):
        region = self.current_region()
        _, age = VIEWS.get(self.resource.get(), (None, None))
        if age is not None and not self.overview_open:
            self.navigation_age = age
        for choice, button in self.age_buttons.items():
            supported = self.overview_open or region in SHARED_DUNGEONS or self.view_for_age(choice)
            active = choice == self.navigation_age
            button.configure(style='Current.Age.TButton' if active else 'Age.TButton')
            button.state(['disabled' if self.simulation or active or not supported else '!disabled'])

    def refresh_navigation(self):
        region = self.current_region()
        name = REGION_NAMES[region]
        view = self.resource.get()
        self.zones.set(view if view == BURNT_VILLAGE or view not in VIEWS else name)
        self.refresh_age_buttons()
        self.banner.set('SIMULATION - noms et positions fictifs' if self.simulation else
                        f'{name}  ·  Carte chargée')
        self.neighbor_bar.pack_forget()
        self.neighbor_layout = None
        if not self.simulation and self.world_targets():
            self.overview_button.pack(side='left', padx=5)
        else:
            self.overview_button.pack_forget()
        floor = self.floor_target()
        if floor:
            text = 'Souterrains' if floor in UNDERGROUND_LABELS else 'Surface'
            self.floor_button.configure(text=text)
            self.floor_button.pack(side='left', padx=5)
        else:
            self.floor_button.pack_forget()
        view = self.resource.get()
        if view in FLOOR_OPTIONS:
            self.floor_picker.configure(values=tuple(level for level, floor_view in FLOOR_OPTIONS[view]
                                                    if floor_view in self.views))
            self.floor_picker.set(next(level for level, floor_view in FLOOR_OPTIONS[view] if floor_view == view))
            self.floor_picker.pack(side='left', padx=5)
        else:
            self.floor_picker.pack_forget()
        self.neighbor_targets = tuple(self.available_neighbors()) if not self.simulation else ()
        self.layout_neighbors()

    def layout_neighbors(self, _event=None):
        fixed_width = sum(widget.winfo_reqwidth() + 2 * int(widget.pack_info()['padx'])
                          for widget in self.map_tools.pack_slaves() if widget is not self.neighbor_bar)
        requested = sum(self.neighbor_buttons[target].winfo_reqwidth() + 8
                        for target in self.neighbor_targets)
        remaining_width = self.map_tools.winfo_width() - fixed_width
        compact = requested > remaining_width
        second_row = compact and self.neighbor_menu_button.winfo_reqwidth() + 8 > remaining_width
        layout = self.neighbor_targets, compact, second_row
        if layout == self.neighbor_layout:
            return
        self.neighbor_layout = layout
        self.neighbor_bar.pack_forget()
        for widget in self.neighbor_bar.pack_slaves():
            widget.pack_forget()
        if not self.neighbor_targets:
            return
        if compact:
            self.neighbor_menu.delete(0, 'end')
            for target in self.neighbor_targets:
                self.neighbor_menu.add_command(label=REGION_NAMES[target],
                                               command=lambda region=target: self.open_neighbor(region))
            self.neighbor_menu_button.pack(side='left', padx=4)
        else:
            for target in self.neighbor_targets:
                self.neighbor_buttons[target].pack(side='left', padx=4)
        if second_row:
            self.neighbor_bar.pack(side='top', anchor='w')
        else:
            self.neighbor_bar.pack(in_=self.map_tools, side='left')

    def resource_changed(self, *, manual=True, arrival=None):
        self.overview_open = False
        self.arrival = arrival
        if manual and self.save_age is not None:
            self.follow_age.set(False)
        self.selected = None
        self.manual_button.pack_forget()
        self.details.set('Sélectionnez un emplacement.')
        self.refresh_navigation()
        self.import_status.set('')
        self.render()
        self.fit()
        self.atlas_failed.pop(self.resource.get(), None)
        self.ensure_atlas()

    def outside(self, row):
        background = self.aerial.get(location_view(row))
        return bool(background and row.position is not None and not background.covers(row.project()))

    def resized(self, event):
        previous = self.canvas_size
        self.canvas_size = (event.width, event.height)
        if getattr(self, 'fit_pending', False):
            self.fit()
        else:
            if previous and not self.overview_open:
                self.viewport.x += (event.width - previous[0]) / 2
                self.viewport.y += (event.height - previous[1]) / 2
            self.draw()

    def fit_detail(self):
        self.overview_open = False
        self.refresh_age_buttons()
        self.fit()

    def toggle_overview(self):
        if self.overview_open:
            self.fit_detail()
        elif not self.simulation and self.world_targets():
            self.show_world()

    def show_world(self):
        self.overview_open = True
        self.refresh_age_buttons()
        self.draw()
        if self.world_image is not None or self.world_loading is True:
            return
        self.world_loading = True
        result = Queue()

        def prepare():
            try:
                result.put(load_world_map())
            except (OSError, ValueError):
                result.put(None)

        def finish():
            self.world_callback = None
            try:
                self.world_image = result.get_nowait()
            except Empty:
                self.world_callback = self.root.after(100, finish)
                return
            self.world_loading = 'unavailable' if self.world_image is None else False
            if self.overview_open:
                self.draw()

        Thread(target=prepare, daemon=True).start()
        self.world_callback = self.root.after(100, finish)

    def fit(self, *, focus=None, preserve_viewport=False):
        if self.document is None:
            return
        self.fit_pending = self.canvas.winfo_width() <= 1 or self.canvas.winfo_height() <= 1
        if self.fit_pending:
            return
        points = [r.project() for r in self.visible if view_contains(self.resource.get(), location_view(r)) and r.position is not None
                  and (self.show_outside.get() or not self.outside(r))]
        aerial = self.aerial.get(self.resource.get())
        scene = self.scenes.get(self.resource.get(), {}) if not aerial else {}
        if aerial:
            points.extend(aerial.corners())
        points.extend(point for _, point in scene.get('points', ()))
        for _, route in scene.get('routes', ()):
            points.extend(route)
        for _, low, high in scene.get('rooms', ()):
            points.extend((low, high))
        local_arena = self.resource.get() in DREAM_BATTLE_VIEWS or self.resource.get() in GANON_TRIAL_VIEWS
        if self.link and view_contains(self.resource.get(), self.link_view()):
            points.append((self.link.x, self.link.z))
        width, height = self.canvas.winfo_width(), self.canvas.winfo_height()
        viewport = Viewport() if preserve_viewport else self.viewport
        viewport.fit(points, width, height, min_extent=36 if local_arena else 1)
        self.fitted_scale = viewport.scale
        if not preserve_viewport:
            self.viewport_adjusted = False
            if focus is not None:
                self.viewport.center(focus, width, height)
        self.draw()

    def draw_overview(self, width, height):
        self.canvas.configure(background=WORLD_BACKGROUND)
        map_w, map_h = WORLD_SIZE
        scale = min(width / map_w, height / map_h)
        size = max(1, round(map_w * scale)), max(1, round(map_h * scale))
        left, top = (width - size[0])/2, (height - size[1])/2
        if self.world_image is not None:
            if self.world_photo_size != size:
                self.world_photo = ImageTk.PhotoImage(self.world_image.resize(size, Image.Resampling.LANCZOS),
                                                      master=self.canvas)
                self.world_photo_size = size
            self.canvas.create_image(left, top, anchor='nw', image=self.world_photo, tags='world-map')
        region = self.current_region()
        region = WORLD_PIN_PARENTS.get(region, region)
        link_view = self.link_view() if self.link else None
        link_region = VIEWS.get(link_view, (None, None))[0]
        link_anchor = WORLD_PIN_PARENTS.get(link_region, link_region)
        pins = {}
        for target, view in self.world_targets().items():
            pins.setdefault(WORLD_PIN_PARENTS.get(target, target), []).append((target, view))
        positions = {anchor: (left + WORLD_PINS[anchor][0] * size[0], top + WORLD_PINS[anchor][1] * size[1])
                     for anchor in pins}
        heading = self.canvas.create_text(12, 12, anchor='nw', text=self.world_heading(), fill='#fff7de',
                                          tags='world-heading')
        occupied = [self.canvas.bbox(heading)]
        occupied.extend((x-9, y-9, x+9, y+9) for x, y in positions.values())
        if link_anchor in WORLD_PINS:
            link_x = left + WORLD_PINS[link_anchor][0] * size[0] + 12
            link_y = top + WORLD_PINS[link_anchor][1] * size[1] - 12
            occupied.append((link_x-12, link_y-12, link_x+12, link_y+12))
        for anchor, destinations in pins.items():
            x, y = positions[anchor]
            color = '#8ae8c1' if anchor == region else '#ffca91' if anchor in SHARED_DUNGEONS else '#fff3ca'
            if anchor in SHARED_DUNGEONS:
                pin = self.canvas.create_polygon(x, y-7, x+7, y, x, y+7, x-7, y,
                                                 fill=color, outline='#2e2718', width=2)
            else:
                pin = self.canvas.create_oval(x-6, y-6, x+6, y+6, fill=color, outline='#2e2718', width=2)
            target, view = destinations[0]
            title = f'{REGION_NAMES[anchor]} ▾' if len(destinations) > 1 else REGION_NAMES[target]
            labels = self.draw_world_label(title, x, y, width, height, occupied)
            for item in (pin, *labels):
                if len(destinations) > 1:
                    self.world_menus[item] = destinations
                else:
                    self.navigation_markers[item] = target
                    self.portal_views[item] = view
        if link_anchor in WORLD_PINS:
            for item in self.draw_link_pin(link_x, link_y, self.link.yaw):
                self.navigation_markers[item] = link_region
                self.portal_views[item] = link_view

    def draw_world_label(self, title, x, y, width, height, occupied):
        label = self.canvas.create_text(x, y, text=title, fill='#fff7de')
        candidates = (('n', x, y+11), ('s', x, y-11), ('w', x+12, y), ('e', x-12, y),
                      ('nw', x+12, y+11), ('ne', x-12, y+11), ('sw', x+12, y-11), ('se', x-12, y-11))
        for anchor, lx, ly in candidates:
            self.canvas.coords(label, lx, ly)
            self.canvas.itemconfigure(label, anchor=anchor)
            l, t, r, b = self.canvas.bbox(label)
            bounds = l-3, t-1, r+3, b+1
            left, top, right, bottom = bounds
            if not (0 <= left < right <= width and 0 <= top < bottom <= height):
                continue
            if any(left < br and bl < right and top < bb and bt < bottom for bl, bt, br, bb in occupied):
                continue
            occupied.append(bounds)
            box = self.canvas.create_rectangle(*bounds, outline='#9a7947', fill='#342615', tags='world-label')
            self.canvas.tag_lower(box, label)
            if len(anchor) == 2:
                line = self.canvas.create_line(x, y, lx, ly, fill='#6d5330')
                self.canvas.tag_lower(line, box)
            return label, box
        self.canvas.delete(label)
        return ()

    def world_heading(self):
        return ('Hyrule · Illustration indisponible' if self.world_loading == 'unavailable'
                else 'Hyrule · Choisis une zone')

    def world_hover(self, event):
        if not self.overview_open:
            return
        text = self.world_heading()
        if event is not None:
            for item in reversed(self.canvas.find_overlapping(event.x-2, event.y-2, event.x+2, event.y+2)):
                if item in self.world_menus:
                    region = self.world_menus[item][0][0]
                    text = REGION_NAMES[WORLD_PIN_PARENTS.get(region, region)]
                    text += ' · Choisis une destination'
                    break
                if item in self.navigation_markers:
                    text = REGION_NAMES[self.navigation_markers[item]]
                    if 'player-pin' in self.canvas.gettags(item):
                        text = f'Link · {self.portal_views[item]}'
                    break
        self.canvas.itemconfigure('world-heading', text=text)

    def draw(self):
        if not hasattr(self, 'visible'):
            return
        self.canvas.delete('all')
        self.background_photo = None
        self.markers = {}
        self.navigation_markers = {}
        self.portal_views = {}
        self.local_portals = {}
        self.world_menus = {}
        width, height = self.canvas.winfo_width(), self.canvas.winfo_height()
        if self.overview_open:
            self.draw_overview(width, height)
            return
        scene = self.scenes.get(self.resource.get())
        captions = []
        aerial = self.aerial.get(self.resource.get())
        region = self.current_region()
        name = REGION_NAMES[region]
        reset_points = [point for label, point in (scene or {}).get('points', ())
                        if region == 'LostWood' and label == LOST_WOOD_RESET]
        if self.resource.get() in GORON_FLOORS:
            name = f'{name} · {GORON_LEVELS[GORON_FLOORS[self.resource.get()]]}'
        elif self.resource.get() in FLOOR_OPTIONS:
            name = self.resource.get()
        exits = {}
        arrival_scene = scene or {}
        if not self.simulation:
            for neighbor, portal in NEIGHBORS[region].items():
                portal_scene = scene or {}
                if region == 'GoronCity' and neighbor in {'DeathMountainCrater', 'LostWood'}:
                    floor = GORON_CRATER_FLOOR if neighbor == 'DeathMountainCrater' else GORON_LOST_WOODS_FLOOR
                    if GORON_FLOORS.get(self.resource.get()) != floor:
                        continue
                    age = VIEWS[self.resource.get()][1]
                    portal_scene = self.scenes.get(GORON_VIEWS[age][0], {})
                points = {tuple(p) for label, p in portal_scene.get('points', ()) if label == portal}
                if len(points) != 1:
                    continue
                destination = self.view_for_region(neighbor)
                if destination:
                    destination_region = VIEWS[destination][0]
                    # The plain labels this connection Kokiri, via the bridge view.
                    origin = 'KokiriForest' if region == 'KokiriBridge' and destination_region == 'HyruleField' else region
                    arrival = NEIGHBORS[destination_region].get(origin)
                    exits[portal] = (neighbor, points.pop(), REGION_NAMES[neighbor], None, arrival)
                    if portal == self.arrival:
                        arrival_scene = portal_scene
            for portal, (neighbor, floor, title, arrival) in SIDE_PORTALS.get(region, {}).items():
                if portal == FIRE_KAKARIKO_CONTINUE and self.arrival != FIRE_KAKARIKO_ARRIVAL:
                    continue
                if region == 'SageRoom' and self.arrival in SIDE_PORTALS[region] and portal != self.arrival:
                    continue
                points = {tuple(p) for label, p in (scene or {}).get('points', ()) if label == portal}
                destination = floor if floor is not None else self.view_for_region(neighbor)
                if destination == self.resource.get():
                    landing_points = {tuple(p) for label, p in (scene or {}).get('points', ()) if label == arrival}
                    if len(landing_points) != 1:
                        continue
                if len(points) == 1 and destination in self.views:
                    exits[portal] = (neighbor, points.pop(), title, floor, arrival)
        heading_color = '#d2e1da'
        if aerial:
            self.canvas.configure(background=ATLAS_BACKGROUND)
            raster = aerial.render(self.viewport, (width, height), fillcolor=ATLAS_BACKGROUND)
            self.background_photo = ImageTk.PhotoImage(raster, master=self.canvas)
            self.canvas.create_image(0, 0, image=self.background_photo, anchor='nw', tags='aerial')
            attribution = {LOST_SOURCE: 'Itinéraire vers le Bosquet sacré',
                           BRIDGE_SOURCE: 'Repères du jeu (schéma)'}.get(aerial.source, 'Field Atlas')
            heading = f'{name} | {attribution}'
            if region == 'WaterTemple':
                for label, point in (scene or {}).get('points', ()):
                    if label in WATER_CONTROL_LABELS and aerial.covers(point):
                        x, y = self.viewport.screen(point)
                        self.canvas.create_polygon(x, y-6, x+6, y, x, y+6, x-6, y,
                                                   fill='#8ce2ed', outline='#123d4b', tags='water-control')
                        captions.append((label, x, y-14))
            for label, points in (scene or {}).get('routes', ()):
                if label == SHADOW_SHIP_ROUTE:
                    coordinates = [coord for point in points for coord in self.viewport.screen(point)]
                    self.canvas.create_line(*coordinates, fill='#332d25', width=6, tags='scene-route')
                    self.canvas.create_line(*coordinates, fill='#ffe19b', width=3, dash=(5, 3),
                                            arrow='last', tags='scene-route')
                    x, y = self.viewport.screen(points[len(points) // 2])
                    captions.append((label, x, y - 14))
        elif scene:
            self.canvas.configure(background=ATLAS_BACKGROUND)
            # The native floor actors are spaced three world units apart.
            tile_radius = self.viewport.scale * 1.5
            for label, point in scene['points']:
                if label == GANONDORF_TILE:
                    x, y = self.viewport.screen(point)
                    self.canvas.create_rectangle(x-tile_radius, y-tile_radius, x+tile_radius, y+tile_radius,
                                                 fill='#1f5577', outline='#527f98', tags='ganondorf-tile')
            for label, low, high in scene['rooms']:
                x1, y1 = self.viewport.screen(low)
                x2, y2 = self.viewport.screen(high)
                self.canvas.create_rectangle(x1, y1, x2, y2, fill='#1f5577',
                                             outline='#7bb6ce', width=2, tags='scene')
                captions.append((label, (x1 + x2) / 2, min(y1, y2) - 10))
            routes = scene.get('routes', ())
            race_colors = {DAMPE_ROUTES['Playing']: '#ffe19b', DAMPE_ROUTES['PlayingSecond']: '#76ddf1'}
            race_tracks = [(title, race_colors[title]) for title, _ in routes if title in race_colors]
            paths = [(title, [c for point in route for c in self.viewport.screen(point)])
                     for title, route in routes]
            locks = [coordinates for title, coordinates in paths if title == TRAINING_LOCKED_DOOR]
            paths = [(title, coordinates) for title, coordinates in paths if title != TRAINING_LOCKED_DOOR]
            for title, coordinates in paths:
                guide = title in (GUIDE_ROUTE, GANON_ESCAPE_ROUTE, SHADOW_SHIP_ROUTE) or title in race_colors
                self.canvas.create_line(*coordinates, fill='#332d25' if guide else '#7bb6ce', width=8,
                                        capstyle='round', joinstyle='round', tags='scene-route')
            for title, coordinates in paths:
                guide = title in (GUIDE_ROUTE, GANON_ESCAPE_ROUTE, SHADOW_SHIP_ROUTE) or title in race_colors
                self.canvas.create_line(*coordinates, fill=race_colors.get(title, '#ffe19b' if guide else '#1f5577'),
                                        width=3 if guide else 6, arrow='last' if guide else 'none',
                                        dash=(5, 3) if title == DAMPE_ROUTES['PlayingSecond'] else (),
                                        capstyle='round', joinstyle='round', tags='scene-route')
            for coordinates in locks:
                self.canvas.create_line(*coordinates, fill='#0d1f2e', width=7, tags='maze-door-outline')
                self.canvas.create_line(*coordinates, fill='#f5ad80', width=3, tags='maze-door')
            if locks:
                self.canvas.create_text(12, 30, anchor='nw', fill='#f5ad80', text=f'━  {TRAINING_LOCKED_DOOR}')
            for label, point in scene['points']:
                sage_exit = region == 'SageRoom' and label in SIDE_PORTALS[region]
                if (label in exits or sage_exit or label in (GANONDORF_TILE, LOST_WOOD_RESET, FIRE_KAKARIKO_CONTINUE)
                        or label in PORTAL_START_NAMES.get(region, ())):
                    continue
                x, y = self.viewport.screen(point)
                if label == GANON_TRIAL_ROOM_CENTER:
                    self.canvas.create_oval(x-4, y-4, x+4, y+4, outline='#7bb6ce', width=2, tags='trial-room-center')
                    continue
                self.canvas.create_polygon(x, y-5, x+5, y, x, y+5, x-5, y,
                                           fill='#b4dec0', tags='scene')
                captions.append((label, x, y - 13))
            topic = paths[0][0] if paths else 'Repères du jeu'
            if race_tracks:
                topic = 'Course de Dampé'
            heading = f'{name} | {topic} (schéma)'
            legend_x = 12
            for title, color in race_tracks:
                item = self.canvas.create_text(legend_x, 30, anchor='nw', fill=color, text=title, tags='race-legend')
                legend_x = self.canvas.bbox(item)[2] + 16
        else:
            self.canvas.configure(background=ATLAS_BACKGROUND)
            step, xs, ys = self.viewport.grid(width, height)
            for x in xs:
                self.canvas.create_line(x, 0, x, height, fill='#2c414a')
            for y in ys:
                self.canvas.create_line(0, y, width, y, fill='#2c414a')
            heading = (f'{self.resource.get()} | Schéma X/Z'
                       if self.resource.get() in UNDERGROUND_LABELS or self.resource.get() in FLOOR_OPTIONS
                       else f'Schéma X/Z | Grille : {step:g} unités')
        spawn_labels = PORTAL_ARRIVAL_STARTS.get((region, self.arrival), ())
        named_spawns = {(name, point) for name, point in arrival_scene.get('points', ()) if name in spawn_labels}
        complete_spawns = (len(named_spawns) == len(spawn_labels)
                           and {name for name, _ in named_spawns} == set(spawn_labels))
        spawns = sorted({point for _, point in named_spawns}) if complete_spawns else []
        if len(spawns) > 1:
            heading += ' · Deux arrivées possibles'
        self.canvas.create_text(12, 12, anchor='nw', fill=heading_color, text=heading)
        if reset_points:
            self.canvas.create_text(12, 30, anchor='nw', fill='#f5ad80', text=f'×  {LOST_WOOD_RESET}')
        exit_names = {}
        exit_bounds = []
        exits_by_point = {}
        for portal, (neighbor, exit_point, exit_name, floor, arrival) in exits.items():
            if aerial and not aerial.covers(exit_point):
                continue
            exits_by_point.setdefault(exit_point, []).append((portal, (exit_name, neighbor, floor, arrival)))
        arrival_exit = next((point for point, group in exits_by_point.items()
                             if any(portal == self.arrival for portal, _ in group)), None)
        if not spawns and arrival_exit is not None:
            spawns = [arrival_exit]
        for spawn in spawns:
            ax, ay = self.viewport.screen(spawn)
            if arrival_exit is not None and spawn != arrival_exit:
                x, y = self.viewport.screen(arrival_exit)
                self.canvas.create_line(x, y, ax, ay, fill='#ffe19b', width=2, dash=(3, 3), tags='portal-approach')
            self.canvas.create_oval(ax-14, ay-14, ax+14, ay+14, outline='#ffe19b', width=2, tags='portal-arrival')
        for exit_point, group in exits_by_point.items():
            actions = tuple(action for _, action in group)
            exit_name, neighbor, floor, _ = actions[0]
            x, y = self.viewport.screen(exit_point)
            marker = self.canvas.create_polygon(x, y-9, x+9, y, x, y+9, x-9, y,
                                                fill='#147c82', outline='#ebfbef', width=2,
                                                tags=('zone-navigation',))
            exit_bounds.append(self.canvas.bbox(marker))
            self.navigation_markers[marker] = neighbor
            self.local_portals[marker] = actions
            if floor:
                self.portal_views[marker] = floor
            title = ' · '.join(action[0] for action in actions) + ' ▾' if len(actions) > 1 else exit_name
            exit_names[title] = actions
            captions.append((title, x, y - 16))
        kokiri = self.view_for_region('KokiriForest') if reset_points and not self.simulation else None
        for point in reset_points:
            x, y = self.viewport.screen(point)
            marker = self.canvas.create_text(x, y, text='×', fill='#f5ad80',
                                             font=('TkDefaultFont', 13, 'bold'), tags='lost-wood-reset')
            exit_bounds.append(self.canvas.bbox(marker))
            if kokiri:
                self.navigation_markers[marker] = 'KokiriForest'
                self.local_portals[marker] = (
                    (LOST_WOOD_RESET, 'KokiriForest', kokiri, NEIGHBORS['KokiriForest']['LostWood']),
                )
                self.portal_views[marker] = kokiri
        rows = [row for row in self.visible if view_contains(self.resource.get(), location_view(row))
                and row.position is not None
                and (self.show_outside.get() or row == self.selected or not self.outside(row))]
        rows.sort(key=lambda row: row == self.selected)
        labels = []
        for row in rows:
            x, y = self.viewport.screen(row.project())
            color = COLORS[self.store.states.get(row.id, 'unknown')]
            radius = 7
            outline = '#fff9ea' if row == self.selected else color
            item = self.canvas.create_oval(x-radius, y-radius, x+radius, y+radius,
                                          fill=color, outline=outline, width=2, tags='check-pin')
            self.markers[item] = row
            right = x <= width * 0.7
            title = f'{row.name} · entrée' if row.entrance else row.name
            labels.append((title, x + (12 if right else -12), y,
                           'w' if right else 'e', '#edf2f4', row))
        # Give the selected check first claim on label space, then the landmarks.
        heading_height = 50 if reset_points or self.canvas.find_withtag('race-legend') else 30
        used = [(0, 0, width, heading_height)]
        foreground = [label for label in labels if label[-1] == self.selected]
        background = [label for label in labels if label[-1] != self.selected]
        landmarks = [(name.replace('_', ' '), x, y, 'center', '#d0e8d8', None)
                     for name, x, y in captions]
        for name, x, y, anchor, color, row in foreground + landmarks + background:
            label = self.canvas.create_text(x, y, anchor=anchor, text=name, fill=color)
            left, top, right, bottom = self.canvas.bbox(label)
            occupied = used if row is None else used + exit_bounds
            if (any(left < r and right > l and top < b and bottom > t for l, t, r, b in occupied)
                    or right < 0 or bottom < 0 or left > width or top > height):
                self.canvas.delete(label)
                continue
            used.append((left, top, right, bottom))
            if row is not None:
                self.markers[label] = row
            elif name in exit_names:
                _, neighbor, floor, _ = exit_names[name][0]
                self.navigation_markers[label] = neighbor
                self.local_portals[label] = exit_names[name]
                if floor:
                    self.portal_views[label] = floor
        if self.link and view_contains(self.resource.get(), self.link_view()):
            x, y = self.viewport.screen((self.link.x, self.link.z))
            self.draw_link_pin(x, y, self.link.yaw)
        if not self.markers and self.resource.get() not in DREAM_BATTLE_VIEWS:
            self.canvas.create_text(25, heading_height + 5, anchor='nw',
                                    text='Aucun check affiché sur cette vue.', fill=heading_color)

    def choose(self, row):
        self.selected = row
        target = location_view(row)
        if row.position is None and target not in self.views:
            target = None
            if row.region in REGION_VIEWS and (self.overview_open or row.region != self.current_region()):
                target = self.browse_view(row.region)
        point = row.project()
        if target and (self.resource.get() != target or self.overview_open):
            self.arrival = None
            self.overview_open = False
            _, age = VIEWS.get(target, (None, None))
            if self.save_age is not None and age is not None and age != self.save_age:
                self.follow_age.set(False)
            self.resource.set(target)
            self.refresh_navigation()
            self.ensure_atlas()
            self.render()
            self.fit(focus=point)
            return
        if point is not None:
            self.arrival = None
            self.viewport.center(point, self.canvas.winfo_width(), self.canvas.winfo_height())
        self.show_details()
        self.draw()

    def show_details(self):
        row = self.selected
        tracker = self.tracked_rows.get(row.id, {})
        if tracker.get('untracked') and self.store.connection in {'save', 'live'}:
            self.manual_button.configure(text=('Annuler le marquage manuel' if tracker.get('source') == 'manual'
                                               else 'Marquer comme récupéré'))
            self.manual_button.state(['!disabled'])
            self.manual_button.pack(side='bottom', fill='x', pady=(4, 0))
        else:
            self.manual_button.pack_forget()
        view = location_view(row)
        if row.position is None and view not in self.views:
            view = REGION_NAMES.get(row.region, view)
        area = UNPOSITIONED_CHECK_AREAS.get(row.id) if row.position is None else None
        self.details.set(f'{row.name}\nÉtat : {LABELS[self.store.states.get(row.id, "unknown")]}\n'
                         f'{view}\n{row.category}\nID : {row.id}\n'
                         f'XYZ : {row.position if row.position is not None else "inconnues"}'
                         + (f'\nSecteur indiqué par OotrR : {area[1]}' if area else '')
                         + (f'\nEntrée affichée (XYZ) : {row.entrance}' if row.entrance else '')
                         + ('\nHors du fond de carte' if self.outside(row) else '')
                         + (f'\nObjet obtenu : {tracker["reward"]}' if tracker.get('reward') else '')
                         + ('\nCollecte sans indicateur de sauvegarde' if tracker.get('untracked') else '')
                         + ('\nMarqué manuellement' if tracker.get('source') == 'manual' else '')
                         + ('\nValidé par la destruction de la source' if tracker.get('source') == 'source_break' else '')
                         + ('\nValidé par l’événement de la chanson' if tracker.get('source') == 'event_played' else '')
                         + ('\nÂmes manquantes : ' + ', '.join(tracker['missing_souls'])
                            if tracker.get('missing_souls') else ''))

    def choose_first(self):
        if self.visible:
            first = self.visible[0]
            view = self.resource.get()
            self.choose(next((row for row in self.visible if row.id == first.id and location_view(row) == view),
                             first))

    def choose_list(self, event=None):
        indexes = self.results.curselection()
        if indexes:
            self.choose(self.visible[indexes[0]])

    def press(self, event):
        self.drag = None
        hits = self.canvas.find_overlapping(event.x-3, event.y-3, event.x+3, event.y+3)
        checks = dict.fromkeys(self.markers[item] for item in reversed(hits)
                               if item in self.markers and 'check-pin' in self.canvas.gettags(item))
        portals = dict.fromkeys(action for item in reversed(hits) for action in self.local_portals.get(item, ()))
        if portals and len(checks) + len(portals) > 1:
            self.choose_overlapping(checks, event.x_root, event.y_root, portals=portals)
            return
        for item in reversed(hits):
            if item in self.world_menus:
                self.choose_world_destination(self.world_menus[item], event.x_root, event.y_root)
                return
            if item in self.navigation_markers:
                arrival = self.local_portals[item][0][3] if item in self.local_portals else None
                self.open_neighbor(self.navigation_markers[item], view=self.portal_views.get(item), arrival=arrival)
                return
            if item in self.markers:
                if len(checks) > 1 and 'check-pin' in self.canvas.gettags(item):
                    self.choose_overlapping(checks, event.x_root, event.y_root)
                    return
                self.choose(self.markers[item])
                return
        if not self.overview_open:
            self.drag = (event.x, event.y)

    def choose_overlapping(self, rows, x, y, *, portals=()):
        self.marker_menu.delete(0, 'end')
        names = Counter(row.name for row in rows)
        for row in rows:
            label = row.name if names[row.name] == 1 else f'{row.name} · {row.id}'
            self.marker_menu.add_command(label=label, command=lambda result=row: self.choose(result))
        for title, region, view, arrival in portals:
            self.marker_menu.add_command(label=title,
                                         command=lambda target=region, floor=view, anchor=arrival:
                                         self.open_neighbor(target, view=floor, arrival=anchor))
        self.post_marker_menu(x, y)

    def choose_world_destination(self, destinations, x, y):
        self.marker_menu.delete(0, 'end')
        for region, view in destinations:
            self.marker_menu.add_command(label=REGION_NAMES[region],
                                         command=lambda target=region, label=view: self.open_neighbor(target, view=label))
        self.post_marker_menu(x, y)

    def post_marker_menu(self, x, y):
        try:
            self.marker_menu.tk_popup(x, y)
        finally:
            self.marker_menu.grab_release()

    def pan(self, event):
        if self.drag:
            self.viewport_adjusted = True
            self.viewport.x += event.x - self.drag[0]
            self.viewport.y += event.y - self.drag[1]
            self.drag = (event.x, event.y)
            self.draw()

    def zoom(self, factor, x, y):
        if self.overview_open:
            if factor > 1:
                self.fit_detail()
            return
        self.viewport_adjusted = True
        self.viewport.zoom(factor, (x, y))
        if (factor < 1 and self.viewport.scale < self.fitted_scale * OVERVIEW_SCALE
                and not self.simulation and self.world_targets()):
            self.show_world()
        else:
            self.draw()

    def simulate(self, status):
        if self.simulation and self.selected:
            self.simulation.change(self.selected.id, status)
            self.render()

    def toggle_connection(self):
        if self.simulation:
            self.simulation.toggle_connection()
            self.render()
