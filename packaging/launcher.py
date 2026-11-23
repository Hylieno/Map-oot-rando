"""Windows application entry point and offline packaging smoke test."""
from pathlib import Path
import sys

from map_oot_rando.__main__ import main
from map_oot_rando.export import scan_game


if __name__ == '__main__':
    if len(sys.argv) == 3 and sys.argv[1] == '--check-bundled-import':
        # Exercise the frozen scanner imports and parser with a harmless invalid file.
        import evfl  # The real scanner imports this lazily when parsing events.
        from oot_rando.logic.world import World
        from oot_rando.tracker.auto_tracker import TrackerSession
        assert World().fingerprint()
        try:
            scan_game(Path(sys.argv[2]))
        except ValueError as error:
            if str(error) == 'Not a NUP container':
                sys.exit(0)
            raise
        sys.exit(1)
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
