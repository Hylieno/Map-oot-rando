"""Windows application entry point and offline packaging smoke test."""
from pathlib import Path
import sys

from map_oot_rando.__main__ import main
from map_oot_rando.export import import_seed
from map_oot_rando.model import load_metadata
from map_oot_rando.scene import AGE_VIEWS, location_view


if __name__ == '__main__':
    if len(sys.argv) == 4 and sys.argv[1] == '--check-bundled-import':
        # Decode both scene layers and join them to a synthetic checks catalogue.
        import evfl  # Include support for event parsing in the frozen build.
        from oot_rando.logic.world import World
        from oot_rando.tracker.auto_tracker import TrackerSession
        assert World().fingerprint()
        document = import_seed(Path(sys.argv[2]), Path(sys.argv[3]))
        checks = [(row.id, row.position, location_view(row)) for row in load_metadata(document)]
        expected = [('KokiriForest#123', (12.5, 106, -4.5), AGE_VIEWS['Child']),
                    ('KokiriForest#pots#321', (14, 106, -3), AGE_VIEWS['Child'])]
        sys.exit(0 if checks == expected and not document['diagnostics'] else 1)
    if sys.argv[1:] == ['--check-bundled-gui']:
        from tkinter import Tk
        from map_oot_rando.gui import MapApplication

        root = Tk()
        callback_errors = []
        root.report_callback_exception = lambda *error: callback_errors.append(error)
        try:
            app = MapApplication(root)
            root.update()
            app.query.set('SIMULATED#0')
            app.choose_first()
            app.simulate('completed')
            if (app.selected is None or app.store.states.get(app.selected.id) != 'completed'
                    or not app.markers or callback_errors):
                sys.exit(1)
        finally:
            root.destroy()
        sys.exit(0)
    main()
