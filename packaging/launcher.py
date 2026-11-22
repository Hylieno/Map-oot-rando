"""Windows application entry point and offline packaging smoke test."""
from pathlib import Path
import sys

from map_oot_rando.__main__ import main
from map_oot_rando.export import scan_game


if __name__ == '__main__':
    if len(sys.argv) == 3 and sys.argv[1] == '--check-bundled-import':
        # Exercise the frozen scanner imports and parser with a harmless invalid file.
        import evfl  # The real scanner imports this lazily when parsing events.
        try:
            scan_game(Path(sys.argv[2]))
        except ValueError as error:
            if str(error) == 'Not a NUP container':
                sys.exit(0)
            raise
        sys.exit(1)
    main()
