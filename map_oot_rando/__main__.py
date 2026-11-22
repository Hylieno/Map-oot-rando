"""Launch locally: python -m map_oot_rando [metadata.json]."""
import argparse
import json
import tkinter as tk
from .gui import MapApplication
from .model import load_metadata


def main():
    parser = argparse.ArgumentParser(description='Carte locale — simulation par défaut')
    parser.add_argument('metadata', nargs='?', help='Métadonnées de carte v1')
    args = parser.parse_args()
    document = None
    if args.metadata:
        try:
            with open(args.metadata, encoding='utf-8') as stream:
                document = json.load(stream)
            load_metadata(document)
        except (OSError, ValueError, KeyError, TypeError, AttributeError) as error:
            parser.error(str(error))
    root = tk.Tk()
    MapApplication(root, document)
    root.mainloop()


if __name__ == '__main__':
    main()
