"""Read-only local export using a clean checkout of the supported OotrR revision."""
import argparse
import json
import re
from pathlib import Path
import struct
import subprocess
import sys

from .metadata import add_surface_entrances, bind_catalogue, event_check_rows, export_scan, world_check_rows
from .model import REGION_NAMES, SURFACE_MIN_Y, UPSTREAM_REVISION, resource_region
from .scene import extract_scenes


def verify_checkout(directory):
    def git(*args):
        return subprocess.check_output(['git', '-C', str(directory), *args], text=True).strip()

    if (Path(git('rev-parse', '--show-toplevel')).resolve() != directory
            or git('rev-parse', 'HEAD') != UPSTREAM_REVISION
            or git('status', '--porcelain', '--untracked-files=all', '--', 'src/oot_rando')):
        raise ValueError(f'Copie OotrR propre à la révision {UPSTREAM_REVISION} requise')


def map_capture_catalogue(members):
    """Report candidate image/projection resource names, without exporting assets."""
    candidates = re.compile(r'mapcapture|mapmenu|minimap|areamap|fieldmap', re.IGNORECASE)
    return sorted(path for path in members if candidates.search(path))


def scan_game(path, progress=None, world_checks=()):
    from oot_rando.formats.inspect_nup import Nup
    from oot_rando.formats.inspect_resources import dictionaries
    from oot_rando.game.check_names import landmarks
    from oot_rando.game.extra_sources import scan_world
    from oot_rando.game.world_maps import effective_members
    from oot_rando.game.remake_world import inaccessible_child_actor

    nup = Nup(path)
    with nup.stream:
        members = effective_members(nup)
        maps, groups, _, extra = scan_world(nup, dictionaries(nup), members, progress)
    document = export_scan(groups, extra, provenance='ootrr-scan', regions=tuple(REGION_NAMES))

    def eligible(path, actor):
        return not inaccessible_child_actor(path, actor)

    document['locations'].extend(event_check_rows(maps, eligible))
    if world_checks:
        document['locations'].extend(world_check_rows(maps, world_checks, eligible))
    add_surface_entrances(document['locations'], maps)
    for row in document['locations']:
        level = SURFACE_MIN_Y.get(resource_region(row['resource']))
        if level is not None and row['position'] is not None and row['position'][1] < level:
            row['underground'] = True
    document['scenes'] = extract_scenes(maps, landmarks)
    document['map_capture_candidates'] = map_capture_catalogue(members)
    return document


def import_seed(nup, checks, progress=None):
    """Read local inputs and prepare the map document shared by both entry points."""
    catalogue = json.loads(Path(checks).read_text(encoding='utf-8-sig'))
    world_checks = [check for check in catalogue['checks']
                    if check['id'].partition('#')[0] in REGION_NAMES
                    and check['id'].count('#') == 2 and check['id'].split('#', 2)[1].isdecimal()]
    scanned = scan_game(nup, progress, world_checks)
    document = bind_catalogue(scanned, catalogue)
    if not document['locations']:
        raise ValueError('Aucun check des zones prises en charge dans le catalogue')
    if not any(row['position'] is not None for row in document['locations']):
        raise ValueError('Aucun point du NUP ne correspond à cette seed. Vérifie le NUP et le checks.json.')
    return document


def main():
    parser = argparse.ArgumentParser(description='Exporter les points des zones prises en charge')
    parser.add_argument('--ootrr', type=Path, required=True, help='Copie locale du dépôt OotrR')
    parser.add_argument('--nup', type=Path, required=True, help='NUP local du jeu mis à jour')
    parser.add_argument('--checks', type=Path, required=True, help='checks.json de la seed OotrR')
    parser.add_argument('--output', type=Path, required=True, help='Nouveau fichier JSON')
    args = parser.parse_args()
    try:
        directory = args.ootrr.resolve()
        verify_checkout(directory)
        if args.output.exists():
            raise FileExistsError(f'Le fichier de sortie existe déjà : {args.output}')
        sys.path.insert(0, str(directory / 'src'))
        document = import_seed(args.nup, args.checks, lambda message: print(message, file=sys.stderr))
        payload = json.dumps(document, ensure_ascii=False, indent=2, allow_nan=False)
        with args.output.open('x', encoding='utf-8') as stream:
            stream.write(payload + '\n')
    except (OSError, ValueError, KeyError, TypeError, AttributeError,
            struct.error, ImportError, subprocess.CalledProcessError) as error:
        parser.exit(1, f'Export impossible : {error}\n')
    print(f'{len(document["locations"])} entrées, {len(document["diagnostics"])} checks sans position')
    for diagnostic in document['diagnostics']:
        print(diagnostic)


if __name__ == '__main__':
    main()
