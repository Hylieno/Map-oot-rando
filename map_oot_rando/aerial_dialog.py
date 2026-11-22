"""Pick three matching control points in a local image and the game's map."""
import tkinter as tk
from tkinter import ttk
from PIL import ImageTk

from .aerial import AerialImage


def align_image(root, image, references, apply_background):
    dialog = tk.Toplevel(root)
    dialog.title('Aligner la vue aérienne')
    dialog.transient(root)
    dialog.grab_set()
    preview = image.copy()
    preview.thumbnail((min(root.winfo_screenwidth() - 120, 960),
                       min(root.winfo_screenheight() - 250, 640)))
    photo = ImageTk.PhotoImage(preview, master=dialog)
    selected = tk.StringVar(dialog)
    status = tk.StringVar(dialog)
    pairs = []
    choices = {f'{name} [X {x:.1f}, Z {z:.1f}]': (x, z) for name, (x, z) in references}
    ttk.Label(dialog, text='Choisis un repère, puis clique au même endroit sur l’image. '
                          'Fais-le pour trois repères bien espacés.').pack(padx=8, pady=8)
    selector = ttk.Combobox(dialog, textvariable=selected, state='readonly',
                            values=list(choices), width=65)
    selector.current(0)
    selector.pack(padx=8, pady=(0, 8))
    canvas = tk.Canvas(dialog, width=photo.width(), height=photo.height(), highlightthickness=0)
    canvas.pack(padx=8)
    canvas.create_image(0, 0, image=photo, anchor='nw')
    canvas.image = photo
    ttk.Label(dialog, textvariable=status).pack(padx=8, pady=6)
    buttons = ttk.Frame(dialog)
    buttons.pack(padx=8, pady=(0, 8))

    def update():
        canvas.delete('anchor')
        for i, (x, y, _) in enumerate(pairs, 1):
            canvas.create_oval(x-10, y-10, x+10, y+10, fill='#ffdd79',
                               outline='#233027', tags='anchor')
            canvas.create_text(x, y, text=str(i), tags='anchor')
        status.set(f'{len(pairs)} / 3 repères alignés')
        apply_button.state(['!disabled' if len(pairs) == 3 else 'disabled'])

    def add(event):
        if len(pairs) == 3:
            return
        world = choices[selected.get()]
        if any(previous == world for _, _, previous in pairs):
            status.set('Choisis un autre repère dans la liste.')
            return
        pairs.append((event.x, event.y, world))
        update()

    def undo():
        if pairs:
            pairs.pop()
            update()

    def finish():
        try:
            pixels = [(x * image.width / photo.width(), y * image.height / photo.height())
                      for x, y, _ in pairs]
            background = AerialImage(image, pixels, [world for _, _, world in pairs])
        except ValueError as error:
            status.set(str(error))
            return
        apply_background(background)
        dialog.destroy()

    ttk.Button(buttons, text='Annuler le dernier repère', command=undo).pack(side='left', padx=4)
    apply_button = ttk.Button(buttons, text='Afficher la carte', command=finish)
    apply_button.pack(side='left', padx=4)
    canvas.bind('<Button-1>', add)
    update()
