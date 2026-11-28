"""File selection for a local OotrR import."""
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, ttk

from .theme import PANEL


class ImportDialog(tk.Toplevel):
    def __init__(self, parent, on_import, *, prepare=False):
        super().__init__(parent)
        self.transient(parent)
        title = 'Préparer une seed de test' if prepare else 'Importer mon jeu et ma seed'
        self.title(title)
        self.configure(background=PANEL)
        self.resizable(False, False)
        self.bind('<Escape>', lambda _: self.destroy())
        self.on_import = on_import
        self.paths = {}
        self.filenames = {}

        content = ttk.Frame(self, padding=24)
        content.pack(fill='both', expand=True)
        ttk.Label(content, text=title, style='Title.TLabel').pack(anchor='w')
        self.add_picker(content, 'nup', '1. Le fichier du jeu (.nup)',
                        'Choisis le NUP d’Ocarina of Time Remake contenant le jeu et sa mise à jour.')
        instructions = ('Choisis le checks.json de ta seed OotrR 0.8.4 complète, avec son dossier romfs. '
                        'La copie sert à tester le suivi des actions, dont les Skulltulas, sur une nouvelle partie.'
                        if prepare else 'Dans le dossier généré par OotrR, choisis checks.json et laisse '
                        'manifest.json et tracking.json dans le même dossier pour le suivi.')
        self.add_picker(content, 'checks', '2. Le catalogue de la seed (checks.json)', instructions)
        actions = ttk.Frame(content)
        actions.pack(fill='x', pady=(22, 0))
        self.start_button = ttk.Button(actions, text='Préparer la copie' if prepare else 'Importer la carte',
                                       style='Accent.TButton',
                                       command=self.submit, state='disabled')
        self.start_button.pack(side='right')
        ttk.Button(actions, text='Annuler', command=self.destroy).pack(side='right', padx=(0, 8))
        self.update_idletasks()
        x = parent.winfo_rootx() + (parent.winfo_width() - self.winfo_reqwidth()) // 2
        y = parent.winfo_rooty() + (parent.winfo_height() - self.winfo_reqheight()) // 2
        self.geometry(f'+{max(0, x)}+{max(0, y)}')
        self.wait_visibility()
        self.grab_set()
        self.nup_button.focus_set()

    def add_picker(self, parent, key, label, instructions):
        ttk.Label(parent, text=label, style='Section.TLabel').pack(anchor='w', pady=(16, 3))
        ttk.Label(parent, text=instructions, style='Muted.TLabel', wraplength=435,
                  justify='left').pack(anchor='w')
        row = ttk.Frame(parent)
        row.pack(fill='x', pady=(7, 0))
        button = ttk.Button(row, text='Parcourir...', command=lambda: self.pick(key))
        button.pack(side='left')
        if key == 'nup':
            self.nup_button = button
        filename = self.filenames[key] = tk.StringVar(master=self, value='Aucun fichier sélectionné')
        ttk.Label(row, textvariable=filename, wraplength=335).pack(side='left', padx=10)

    def pick(self, key):
        title, filetype = {
            'nup': ('Choisir le fichier NUP du jeu', ('Jeu NUP', '*.nup')),
            'checks': ('Choisir le checks.json de la seed OotrR', ('Catalogue de seed', '*.json')),
        }[key]
        path = filedialog.askopenfilename(parent=self, title=title, filetypes=[filetype])
        if path:
            self.paths[key] = path
            self.filenames[key].set(Path(path).name)
            if len(self.paths) == 2:
                self.start_button.state(['!disabled'])

    def submit(self):
        nup, checks = self.paths['nup'], self.paths['checks']
        self.destroy()
        self.on_import(nup, checks)
