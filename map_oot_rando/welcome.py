"""Empty map workspace shown before a seed or a saved map is loaded."""
from pathlib import Path
import tkinter as tk
from tkinter import ttk

from PIL import Image, ImageOps, ImageTk

from .theme import INK


class Welcome(tk.Canvas):
    def __init__(self, parent, command, status):
        super().__init__(parent, background=INK, highlightthickness=0)
        artwork = Path(__file__).with_name('assets') / 'welcome.jpg'
        with Image.open(artwork) as source:
            self.artwork = source.convert('RGB')
        self.photo = None
        self.cover = self.create_image(0, 0, anchor='nw')
        self.frame_line = self.create_rectangle(0, 0, 0, 0, outline='#536750')

        card = tk.Frame(self, background=INK, highlightthickness=1, highlightbackground='#536750',
                        padx=28, pady=26)
        self.card_window = self.create_window(0, 0, window=card, anchor='w')
        ttk.Label(card, text='En attente de données', style='WelcomeStatus.TLabel').pack(anchor='w')
        ttk.Label(card, text='Carte d’Hyrule', style='WelcomeTitle.TLabel').pack(anchor='w', pady=(9, 10))
        ttk.Label(card, text='Importe le fichier du jeu (.nup) et le checks.json de ta seed pour afficher tes checks sur la carte.',
                  style='WelcomeText.TLabel', wraplength=310, justify='left').pack(anchor='w')
        self.import_button = ttk.Button(card, text='Importer mon jeu et ma seed...', style='Accent.TButton',
                                        command=command)
        self.import_button.pack(anchor='w', pady=(22, 0))
        ttk.Label(card, textvariable=status, style='WelcomeStatus.TLabel', wraplength=310,
                  justify='left').pack(anchor='w', pady=(8, 0))
        self.bind('<Configure>', self.resize)

    def resize(self, event):
        image = ImageOps.fit(self.artwork, (event.width, event.height), method=Image.Resampling.BILINEAR,
                             centering=(0.63, 0.45))
        self.photo = ImageTk.PhotoImage(image, master=self)
        self.itemconfigure(self.cover, image=self.photo)
        self.coords(self.frame_line, 9, 9, event.width - 10, event.height - 10)
        self.coords(self.card_window, max(28, round(event.width * .075)), round(event.height * .50))
