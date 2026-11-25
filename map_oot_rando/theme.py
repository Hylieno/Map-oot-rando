"""The desktop map's colours, typography and Tk widget styles."""
import tkinter as tk
from tkinter import font, ttk

INK = '#101b19'
PANEL = '#192a25'
FIELD = '#11211c'
EDGE = '#3c5146'
GOLD = '#e1ba73'
CREAM = '#f1e8d4'
MUTED = '#adc0b2'
SELECTION = '#345746'


def install(root):
    root.configure(background=INK)
    default = font.nametofont('TkDefaultFont', root)
    default.configure(size=10)
    heading = font.nametofont('TkHeadingFont', root)
    heading.configure(family=default.actual('family'), size=10, weight='bold')
    families = {family.casefold(): family for family in font.families(root)}
    serif = next((families[name] for name in ('georgia', 'palatino linotype', 'palatino', 'times')
                  if name in families), default.actual('family'))
    root.option_add('*TCombobox*Listbox.background', FIELD)
    root.option_add('*TCombobox*Listbox.foreground', CREAM)
    root.option_add('*TCombobox*Listbox.selectBackground', SELECTION)
    root.option_add('*TCombobox*Listbox.selectForeground', CREAM)
    root.option_add('*TCombobox*Listbox.font', 'TkDefaultFont')

    style = ttk.Style(root)
    style.theme_use('clam')
    style.configure('.', background=PANEL, foreground=CREAM, bordercolor=EDGE,
                    lightcolor=PANEL, darkcolor=PANEL, troughcolor=FIELD,
                    focuscolor=GOLD, font='TkDefaultFont')
    style.configure('Shell.TFrame', background=INK)
    style.configure('Divider.TFrame', background=EDGE)
    style.configure('Title.TLabel', foreground=CREAM, font=(serif, 19, 'bold'))
    style.configure('Section.TLabel', foreground=GOLD, font='TkHeadingFont')
    style.configure('Muted.TLabel', foreground=MUTED)
    style.configure('WelcomeTitle.TLabel', background=INK, font=(serif, 35, 'bold'))
    style.configure('WelcomeText.TLabel', background=INK)
    style.configure('WelcomeStatus.TLabel', background=INK, foreground=GOLD, font='TkHeadingFont')
    style.configure('TButton', padding=(11, 6), relief='flat', anchor='center')
    style.configure('TMenubutton', padding=(11, 6), relief='flat', arrowcolor=GOLD)
    for widget in ('TButton', 'TMenubutton'):
        style.map(widget, background=[('pressed', SELECTION), ('active', '#2a4539'), ('!disabled', '#233b31')],
                  foreground=[('disabled', '#92a096')], bordercolor=[('focus', GOLD)])
    style.configure('Accent.TButton', background=GOLD, foreground=INK, padding=(16, 8),
                    font='TkHeadingFont')
    style.map('Accent.TButton', background=[('disabled', EDGE), ('pressed', '#cfa358'), ('active', '#f3d293')],
              foreground=[('disabled', MUTED), ('!disabled', INK)])
    style.configure('Age.TButton', padding=(11, 3))
    style.configure('Current.Age.TButton', background=SELECTION)
    style.map('Current.Age.TButton', foreground=[('disabled', GOLD)])
    style.configure('TEntry', padding=(7, 5), fieldbackground=FIELD, insertcolor=CREAM)
    style.configure('TCombobox', padding=(7, 4), fieldbackground=FIELD, arrowcolor=GOLD, selectforeground=CREAM)
    style.map('TCombobox', fieldbackground=[('readonly', FIELD)], selectbackground=[('readonly', FIELD)],
              foreground=[('readonly', CREAM)], arrowcolor=[('disabled', MUTED)])
    style.configure('TCheckbutton', padding=(0, 1), indicatorbackground=FIELD, indicatorforeground=GOLD)
    style.map('TCheckbutton', foreground=[('disabled', '#92a096')], background=[('active', '#21382e')],
              indicatorbackground=[('selected', SELECTION)])
    style.configure('Vertical.TScrollbar', width=11, arrowsize=10, background=EDGE, arrowcolor=CREAM)
    style.configure('TPanedwindow', background=INK, sashthickness=6)


def menu(parent):
    return tk.Menu(parent, tearoff=False, background=PANEL, foreground=CREAM,
                   activebackground=SELECTION, activeforeground=CREAM, selectcolor=GOLD,
                   borderwidth=1, relief='solid', font='TkDefaultFont')
