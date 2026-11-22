"""Local Tk map. Importing this module never starts a tracker or memory reader."""
import json
from queue import Empty, Queue
from threading import Thread
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from .export import import_seed
from .model import load_metadata, select
from .state import StateStore
from .simulation import Simulation, demo_document
from .view import Viewport

COLORS = dict(available='#37b76b', blocked='#e45c5c', unknown='#e6c548', completed='#929ba5')
LABELS = dict(available='Accessible', blocked='Bloqué', unknown='Inconnu', completed='Récupéré')


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
        self.connection = tk.StringVar()
        self.details = tk.StringVar(value='Sélectionnez un emplacement.')
        self.count = tk.StringVar()
        top = ttk.Frame(root, padding=10)
        top.pack(fill='x')
        ttk.Label(top, textvariable=self.banner).pack(side='left')
        ttk.Button(top, text='Ouvrir métadonnées...', command=self.open_metadata).pack(side='right')
        ttk.Button(top, text='Simulation', command=lambda: self.load(demo_document())).pack(side='right')
        import_bar = ttk.Frame(root, padding=(10, 0, 10, 0))
        import_bar.pack(fill='x')
        self.import_button = ttk.Button(import_bar, text='Importer mon jeu et ma seed…',
                                        command=self.choose_seed)
        self.import_button.pack(side='left')
        self.save_button = ttk.Button(import_bar, text='Enregistrer la carte…',
                                      command=self.save_map)
        self.save_button.pack(side='left', padx=8)
        ttk.Label(import_bar, textvariable=self.import_status).pack(side='left')
        ttk.Label(root, textvariable=self.connection, padding=8).pack(fill='x')
        body = ttk.Panedwindow(root, orient='horizontal')
        body.pack(fill='both', expand=True)
        sidebar = ttk.Frame(body, padding=10)
        body.add(sidebar, weight=0)
        ttk.Label(sidebar, text='Recherche : nom ou identifiant').pack(anchor='w')
        search = ttk.Entry(sidebar, textvariable=self.query, width=38)
        search.pack(fill='x')
        search.bind('<Return>', lambda e: self.choose_first())
        ttk.Label(sidebar, text='Ressource / variante').pack(anchor='w', pady=(10, 0))
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
        ttk.Label(sidebar, text='Décochez « Récupéré » pour les masquer.').pack(anchor='w')
        self.results = tk.Listbox(sidebar, height=10, exportselection=False)
        self.results.pack(fill='both', expand=True, pady=8)
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
        ttk.Button(panel, text='Ajuster la vue', command=self.fit).pack(anchor='w')
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

    def load(self, document):
        locations = load_metadata(document)  # Validate before replacing current state.
        self.document = document
        self.locations = locations
        self.simulation = Simulation(locations) if document['provenance'] == 'synthetic' else None
        self.save_button.state(['disabled' if self.simulation else '!disabled'])
        self.store = self.simulation.store if self.simulation else StateStore(document.get('seed_id', ''), [r.id for r in locations])
        self.selected = None
        self.details.set('Sélectionnez un emplacement.')
        self.banner.set('SIMULATION - noms et positions fictifs' if self.simulation else
                        'Kokiri Forest - métadonnées importées ; tracker non connecté')
        self.resources['values'] = sorted({r.resource for r in locations})
        first_positioned = next((r.resource for r in locations if r.position is not None), None)
        self.resource.set(first_positioned or (self.resources['values'][0] if locations else ''))
        self.categories['values'] = ['Toutes'] + sorted({r.category for r in locations})
        self.category.set('Toutes')
        if self.simulation:
            self.sim_controls.pack(fill='x', pady=8)
        else:
            self.sim_controls.pack_forget()
        self.query.set('')
        self.render()
        self.fit()

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
                self.import_events.put(('done', document))
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
                    self.load(value)
                    missing = len(value['diagnostics'])
                    self.import_status.set(f'Carte chargée. {missing} check(s) sans position.')
                else:
                    self.import_status.set('Import interrompu.')
                    messagebox.showerror('Import impossible', value, parent=self.root)
                return
        except Empty:
            self.root.after(100, self.poll_import)

    def save_map(self):
        path = filedialog.asksaveasfilename(parent=self.root, initialfile='kokiri.json',
                                            defaultextension='.json', filetypes=[('Carte JSON', '*.json')])
        if path:
            try:
                with open(path, 'w', encoding='utf-8') as stream:
                    json.dump(self.document, stream, ensure_ascii=False, indent=2)
            except OSError as error:
                messagebox.showerror('Enregistrement impossible', str(error), parent=self.root)

    def open_metadata(self):
        path = filedialog.askopenfilename(filetypes=[('Métadonnées JSON', '*.json')])
        if not path:
            return
        try:
            with open(path, encoding='utf-8') as stream:
                document = json.load(stream)
            self.load(document)
        except (OSError, ValueError, KeyError, TypeError, AttributeError) as error:
            messagebox.showerror('Métadonnées invalides', str(error))

    def render(self):
        if not hasattr(self, 'locations'):
            return
        self.visible = select(self.locations, self.store.states, self.query.get(),
                              {k for k, v in self.status_vars.items() if v.get()},
                              None if self.category.get() == 'Toutes' else {self.category.get()})
        self.results.delete(0, 'end')
        for row in self.visible:
            self.results.insert('end', row.name + (' [sans coordonnées]' if row.position is None else ''))
        missing = sum(r.position is None for r in self.locations)
        self.count.set(f'{len(self.visible)} résultat(s) | {missing} sans coordonnées | '
                       'Molette : zoom ; glisser le fond : déplacer ; Entrée : premier résultat')
        mode = {'simulation': 'SIMULATION connectée', 'disconnected': 'Déconnecté - dernier état conservé',
                'save': 'Sauvegarde uniquement', 'live': 'Mémoire du jeu'}[self.store.connection]
        self.connection.set(f'{mode} | Dernière synchronisation (UTC) : {self.store.last_success or "aucune"}')
        if self.selected:
            self.show_details()
        self.draw()

    def resource_changed(self):
        self.selected = None
        self.details.set('Sélectionnez un emplacement.')
        self.fit()

    def resized(self, event):
        if getattr(self, 'fit_pending', False):
            self.fit()
        else:
            self.draw()

    def fit(self):
        self.fit_pending = self.canvas.winfo_width() <= 1 or self.canvas.winfo_height() <= 1
        if self.fit_pending:
            return
        points = [r.project() for r in self.visible if r.resource == self.resource.get() and r.position is not None]
        self.viewport.fit(points, self.canvas.winfo_width(), self.canvas.winfo_height())
        self.draw()

    def draw(self):
        if not hasattr(self, 'visible'):
            return
        self.canvas.delete('all')
        self.markers = {}
        width, height = self.canvas.winfo_width(), self.canvas.winfo_height()
        step, xs, ys = self.viewport.grid(width, height)
        for x in xs:
            self.canvas.create_line(x, 0, x, height, fill='#2c414a')
        for y in ys:
            self.canvas.create_line(0, y, width, y, fill='#2c414a')
        self.canvas.create_text(12, 12, anchor='nw', fill='#adbfc4',
                                text=f'Schéma X/Z | Grille : {step:g} unités')
        for row in self.visible:
            if row.resource != self.resource.get() or row.position is None:
                continue
            x, y = self.viewport.screen(row.project())
            color = COLORS[self.store.states.get(row.id, 'unknown')]
            item = self.canvas.create_oval(x-7, y-7, x+7, y+7, fill=color,
                                          outline='white' if row == self.selected else color, width=2)
            self.markers[item] = row
            right = x <= width * 0.7
            label = self.canvas.create_text(x + (12 if right else -12), y,
                                            anchor='w' if right else 'e', text=row.name, fill='#edf2f4')
            self.markers[label] = row
        if not self.markers:
            self.canvas.create_text(25, 35, anchor='nw', text='Aucun marqueur positionné pour cette vue.', fill='white')

    def choose(self, row):
        self.selected = row
        self.resource.set(row.resource)
        if row.position is not None:
            self.viewport.center(row.project(), self.canvas.winfo_width(), self.canvas.winfo_height())
        self.show_details()
        self.draw()

    def show_details(self):
        row = self.selected
        self.details.set(f'{row.name}\nID : {row.id}\n{row.category}\n{row.resource}\n'
                         f'XYZ : {row.position if row.position is not None else "inconnues"}\n'
                         f'État : {LABELS[self.store.states.get(row.id, "unknown")]}')

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
