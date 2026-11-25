"""Windows application entry point and offline packaging smoke test."""
from pathlib import Path
import sys

from map_oot_rando.__main__ import main
from map_oot_rando.export import import_seed
from map_oot_rando.model import load_metadata
from map_oot_rando.scene import AGE_VIEWS, WATER_VIEWS, location_view


if __name__ == '__main__':
    if len(sys.argv) == 4 and sys.argv[1] == '--check-bundled-import':
        # Decode the base and update scenes and join them to the checks catalogue.
        import evfl  # Include support for event parsing in the frozen build.
        from oot_rando.logic.world import World
        from oot_rando.tracker.auto_tracker import TrackerSession
        assert World().fingerprint()
        document = import_seed(Path(sys.argv[2]), Path(sys.argv[3]))
        checks = [(row.id, row.position, location_view(row)) for row in load_metadata(document)]
        expected = [('KokiriForest#123', (18, 107, -7.5), AGE_VIEWS['Child']),
                    ('KokiriForest#pots#321', (14, 106, -3), AGE_VIEWS['Child']),
                    ('KokiriForest#pots#322', (16, 108, -8), AGE_VIEWS['Adult']),
                    ('WaterTemple#987', (55.5, 119, -9.5), WATER_VIEWS[1]),
                    ('WaterTemple#gs#988', (50, 120, -13.5), WATER_VIEWS[3])]
        sys.exit(0 if checks == expected and not document['diagnostics'] else 1)
    if len(sys.argv) == 4 and sys.argv[1] == '--check-bundled-gui':
        import json
        from tempfile import TemporaryDirectory
        from tkinter import Tk
        from map_oot_rando.gui import COLORS, MapApplication
        from map_oot_rando.save_profiles import SaveProfiles

        root = Tk()
        callback_errors = []
        root.report_callback_exception = lambda *error: callback_errors.append(error)
        workspace = TemporaryDirectory()
        folder = Path(workspace.name)
        try:
            app = MapApplication(root, profiles=SaveProfiles(folder / 'profiles.json'))
            root.update()
            if app.document is not None or app.visible or not app.welcome.winfo_ismapped() or callback_errors:
                sys.exit(1)
            dialog = app.choose_seed()
            if not dialog.start_button.instate(['disabled']):
                sys.exit(1)
            dialog.destroy()

            app.load(import_seed(Path(sys.argv[2]), Path(sys.argv[3])))
            root.update()
            if app.welcome.winfo_ismapped() or not app.body.winfo_ismapped():
                sys.exit(1)
            child_markers = {app.markers[item].id: app.markers[item].position
                             for item in app.canvas.find_withtag('check-pin')}
            if child_markers != {'KokiriForest#123': (18, 107, -7.5), 'KokiriForest#pots#321': (14, 106, -3)}:
                sys.exit(1)
            app.age_buttons['Adult'].invoke()
            root.update()
            adult_markers = {app.markers[item].id for item in app.canvas.find_withtag('check-pin')}
            if app.resource.get() != AGE_VIEWS['Adult'] or adult_markers != {'KokiriForest#pots#322'} or callback_errors:
                sys.exit(1)
            for ident, view in (('WaterTemple#987', WATER_VIEWS[1]), ('WaterTemple#gs#988', WATER_VIEWS[3])):
                app.query.set(ident)
                app.choose_first()
                root.update()
                dungeon_markers = {app.markers[item].id for item in app.canvas.find_withtag('check-pin')}
                if app.resource.get() != view or dungeon_markers != {ident} or callback_errors:
                    sys.exit(1)

            report = folder / 'diagnostic.json'
            app.save_diagnostic(path=report)
            diagnostic = json.loads(report.read_text(encoding='utf-8'))
            for age, count in (('Child', 2), ('Adult', 1)):
                view = diagnostic['map_views'][AGE_VIEWS[age]]
                if view != {'source': 'field-atlas', 'status': 'unavailable',
                            'placements': count, 'reason': 'missing_reference_points'}:
                    sys.exit(1)
            if {'seed_id', 'aerial'} & diagnostic.keys() or callback_errors:
                sys.exit(1)

            fixture = Path(sys.argv[3]).resolve().parent
            save = folder / 'progress.sav'
            save.write_bytes((fixture / 'before.sav').read_bytes())
            app.query.set('KokiriForest#123')
            app.choose_first()
            app.follow_save(fixture, folder)

            def wait_for_chest(state):
                def synchronized():
                    return app.store.connection == 'save' and app.store.states['KokiriForest#123'] == state

                def poll():
                    if synchronized() or callback_errors:
                        root.quit()
                    else:
                        root.after(30, poll)

                root.after(30, poll)
                timeout = root.after(10000, root.quit)
                root.mainloop()
                root.after_cancel(timeout)
                return synchronized() and not callback_errors

            if not wait_for_chest('unknown'):
                sys.exit(1)
            collected_save = (fixture / 'after.sav').read_bytes()
            save.write_bytes(collected_save)
            if not wait_for_chest('completed') or save.read_bytes() != collected_save:
                sys.exit(1)
            pins = app.canvas.find_withtag('check-pin')
            if len(pins) != 1 or app.canvas.itemcget(pins[0], 'fill') != COLORS['completed']:
                sys.exit(1)
        finally:
            if 'app' in locals():
                app.close_window()
            else:
                root.destroy()
            workspace.cleanup()
        sys.exit(0)
    main()
