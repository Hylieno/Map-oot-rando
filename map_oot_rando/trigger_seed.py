"""Prepare a seed with independent trigger flags (OotrR 0.8.4 prototype)."""
from collections import defaultdict
from contextlib import contextmanager
from copy import copy
from hashlib import sha256
from io import BytesIO
from pathlib import Path
from tempfile import TemporaryDirectory
import argparse
import json
import os
import re
import shutil


SEED_BACKUP = 'map-oot-rando-backup'


def trigger_flag_name(ident):
    digest = sha256(ident.encode('utf-8')).hexdigest()[:20]
    return f'RandoMap.Trigger.{digest}'


def add_event_triggers(raw, hooks):
    """Insert a setter before each verified reward, returning the flags added."""
    from evfl.container import Container
    from evfl.event import ActionEvent, Event, SubFlowEvent
    from evfl.util import make_index
    from oot_rando.patching.event_patch import _flow
    from oot_rando.patching.progressive import ACTION_GUIDE, AFTER_PREFIX, CONVERTER_ENTRY
    from oot_rando.patching.qol_patches import _predecessors
    from oot_rando.patching.song_adapter import DISPLAY_ENTRY, GET_FLOW, display_event_name

    flow = _flow(raw)
    chart = flow.flowchart
    events = {event.name: event for event in chart.events}
    added = set()
    for hook, flag in hooks:
        event_name = hook['event']
        reward = events.get(event_name)
        original = events.get(hook['marker'])
        name = 'RandoMapTrigger_' + event_name
        if (not reward or not original or name in events or not isinstance(original.data, ActionEvent)
                or str(original.data.actor.v.identifier) != 'GameDataActor'
                or original.data.actor_action.v.v != 'EventTriggerSetGameDataBool'
                or original.data.params is None
                or original.data.params.data != {'GameDataName': hook['flag'], 'Index': -1, 'Value': True}):
            continue
        # OotrR can insert these subflows after adding the collection marker.
        wrappers = {
            display_event_name(event_name): (GET_FLOW, DISPLAY_ENTRY),
            AFTER_PREFIX + event_name: (ACTION_GUIDE, CONVERTER_ENTRY),
        }
        following = getattr(getattr(reward.data, 'nxt', None), 'v', None)
        while following is not None and isinstance(following.data, SubFlowEvent):
            if wrappers.pop(following.name, None) != (following.data.res_flowchart_name,
                                                      following.data.entry_point_name):
                break
            following = following.data.nxt.v
        if following is not original:
            continue
        links = _predecessors(chart, reward)
        if not links:
            continue
        trigger = Event()
        trigger.name, trigger.data = name, copy(original.data)
        trigger.data.params = Container()
        trigger.data.params.data = {'GameDataName': flag, 'Index': -1, 'Value': True}
        trigger.data.nxt = make_index(reward)
        # Keep all existing subflow indices intact by appending only the setter.
        for source, kind, key in links:
            target = make_index(trigger)
            if kind == 'entry':
                source.main_event = target
            elif kind == 'nxt':
                source.data.nxt = target
            elif kind == 'case':
                source.data.cases[key] = target
            else:
                source.data.forks[key] = target
        chart.events.append(trigger)
        events[name] = trigger
        added.add(flag)
    if not added:
        return raw, added
    stream = BytesIO()
    flow.write(stream)
    return stream.getvalue(), added


def add_drop_trigger(raw, flag):
    """Add a setter to the private drop AI's one-time startup sequence."""
    import ainb
    from oot_rando.patching.ap_mailbox import ainb_to_binary
    from oot_rando.patching.repeatable_adapter import _flag_setter, _guid

    script = ainb.AINB.from_binary(raw)
    document = script.as_dict()
    nodes = document['Nodes']
    roots = [c['Root Node Index'] for c in document['Commands'] if c['Name'] == 'Root']
    if document['Version'] != 0x408 or len(roots) != 1 or nodes[roots[0]]['Node Type'] != 'Element_Simultaneous':
        raise ValueError('Graphe de récompense inattendu.')
    starts = [nodes[p['Node Index']] for p in nodes[roots[0]]['Plugs']['Child']
              if nodes[p['Node Index']]['Node Type'] == 'Element_Sequential']
    if len(starts) != 1 or any(p['Name'] == 'IsLoop' and p['Default Value']
                               for p in starts[0].get('Properties', {}).get('Bool', ())):
        raise ValueError('Démarrage de la récompense ambigu ou absent.')
    children = starts[0]['Plugs']['Child']
    index = len(nodes)
    children.insert(0, {'Node Index': index, 'Name': ''})
    nodes.append(_flag_setter(index, flag, _guid(flag + '/map-trigger')))
    patched = ainb.AINB.from_dict(document)
    patched.blackboard = script.blackboard
    binary = patched.to_binary() if script.blackboard else ainb_to_binary(document)
    if ainb.AINB.from_binary(binary).as_dict() != document:
        raise ValueError('Le graphe modifié diffère après relecture.')
    return binary


def add_skulltula_drop_trigger(raw, filename, flag):
    """Start the original token AI and record this private drop's creation."""
    import ainb
    from oot_rando.patching.ap_mailbox import ainb_to_binary
    from oot_rando.patching.repeatable_adapter import _flag_setter, _guid

    script = ainb.AINB.from_binary(raw)
    document = script.as_dict()
    commands = document['Commands']
    nodes = document['Nodes']
    if (document['Version'] != 0x408 or document['Category'] != 'AI'
            or len(commands) != 1 or commands[0]['Name'] != 'Root'
            or not 0 <= commands[0]['Root Node Index'] < len(nodes)):
        raise ValueError('Graphe de récompense de Skulltula inattendu.')
    root = nodes[commands[0]['Root Node Index']]
    root_flags = root['Flags']
    root['Flags'] = [value for value in root_flags if value != 'Is Root Node']
    setter = _flag_setter(len(nodes), flag, _guid(flag + '/skulltula/spawn'))
    nodes.append(setter)
    index = len(nodes)
    nodes.append({
        'Node Type': 'Element_Simultaneous', 'Node Index': index, 'Name': '',
        'GUID': _guid(flag + '/skulltula/root'), 'Flags': ['Is Root Node'],
        'Queries': [], 'Attachments': [], 'Properties': {}, 'XLink Actions': [],
        'Parameters': {'Inputs': {}, 'Outputs': {}},
        'Plugs': {'Child': [{'Node Index': child['Node Index'], 'Name': ''} for child in (setter, root)]},
    })
    commands[0]['Root Node Index'] = index
    document['Filename'] = filename
    patched = ainb.AINB.from_dict(document)
    patched.blackboard = script.blackboard
    binary = patched.to_binary() if script.blackboard else ainb_to_binary(document)
    if ainb.AINB.from_binary(binary).as_dict() != document:
        raise ValueError('Le graphe de Skulltula diffère après relecture.')
    return binary


def prepare_skulltula_resources(tracking, map_paths, read_raw):
    """Clone each Skulltula's actual reward and retarget only its own placements."""
    from oot_rando.formats import byml_codec
    from oot_rando.formats.byml_writer import patch_strings
    from oot_rando.formats.inspect_resources import Byml, sarc
    from oot_rando.game.item_forms import resolve_components
    from oot_rando.patching.repeatable_adapter import EVENT_PACK
    from oot_rando.patching.soul_adapter import RSDB_FILES
    from oot_rando.patching.source_textures import _merged

    checks = {}
    for ident, record in tracking['checks'].items():
        match = re.fullmatch(r'([A-Za-z0-9_]+)#gs#([0-9]+)', ident)
        if match and record.get('collection') == {'type': 'bool64', 'hash': match[2]}:
            checks[ident] = record
    resources, templates, flags, member_sizes = {}, {}, {}, {}
    if not checks:
        return resources, templates, flags, member_sizes
    folders = {ident.partition('#')[0] for ident in checks}
    aliases = {}
    for path in sorted(set(map_paths)):
        _, folder, _ = path.split('/', 2)
        if folder not in folders:
            continue
        raw = read_raw(path)
        edits = []
        for index, placement in enumerate(Byml(raw).root.get('Actors', ())):
            ident = f'{folder}#gs#{placement.get("Hash")}'
            if ident not in checks or placement.get('Gyaml') != 'Enemy_Skulltula_Gold':
                continue
            actor = checks[ident]['actor']
            original = (placement.get('Dynamic') or {}).get('Drop__DropActor')
            if (original if original is not None else 'Obj_Token_Gold') != actor:
                raise ValueError(f'Récompense de Skulltula inattendue pour {ident} dans {path}.')
            flag = flags[ident] = trigger_flag_name(ident)
            # The game limits actor names to 25 characters.
            alias = 'Obj_MapG_' + flag.rsplit('.', 1)[1][:16]
            if alias in aliases and aliases[alias][0] != ident:
                raise ValueError(f'Identifiant de récompense de Skulltula ambigu : {alias}')
            aliases[alias] = (ident, actor)
            edits.append({'path': ('Actors', index, 'Dynamic', 'Drop__DropActor'),
                          'before': original, 'after': alias})
        if edits:
            resources[path] = patch_strings(raw, edits)

    missing = sorted(checks.keys() - flags.keys())
    if missing:
        raise ValueError('Placements de Skulltula introuvables : ' + ', '.join(missing))

    tables = {path: byml_codec.load(read_raw(path)) for path in RSDB_FILES.values()}
    rows = {path: {row['__RowId']: row for row in document['root']} for path, document in tables.items()}
    originals = {}
    global_ai = None
    for alias, (ident, actor) in aliases.items():
        if not re.fullmatch(r'[A-Za-z0-9_]+', actor):
            raise ValueError(f'Nom de récompense de Skulltula invalide pour {ident}.')
        source = f'Pack/Actor/{actor}.pack.zs'
        param = f'Actor/{actor}.engine__actor__ActorParam.bgyml'
        if actor not in originals:
            pack = sarc(read_raw(source))
            components = resolve_components(pack, actor, byml_codec)
            info = _merged(pack, components['AIInfoRef'])
            root_ref = re.fullmatch(r'Work/AI/Root/([A-Za-z0-9_.]+\.ain)', info['RootAIRef'])
            if not root_ref:
                raise ValueError(f'Référence au graphe de récompense inattendue pour {ident}.')
            member = 'AI/' + root_ref[1] + 'b'
            if member in pack:
                graph = pack[member]
            else:
                if global_ai is None:
                    global_ai = sarc(read_raw(EVENT_PACK))
                graph = global_ai[member]
            originals[actor] = pack, info, graph
        pack, info, graph = originals[actor]
        clone = dict(pack)
        document = byml_codec.load(clone.pop(param))
        filename = alias + '.root'
        ai_info = f'AI/AIInfo/{alias}.engine__actor__AIInfo.bgyml'
        ai = f'AI/{filename}.ainb'
        actor_param = f'Actor/{alias}.engine__actor__ActorParam.bgyml'
        clone[ai] = add_skulltula_drop_trigger(graph, filename, flags[ident])
        clone[ai_info] = byml_codec.dump({'endian': '<', 'version': 7, 'root': {
            **info, 'RootAIRef': f'Work/AI/Root/{filename}.ain',
        }})
        document['root'].setdefault('Components', {})['AIInfoRef'] = '?' + ai_info
        clone[actor_param] = byml_codec.dump(document)
        for member in (ai, ai_info, actor_param):
            member_sizes[member] = (len(clone[member]) + 8191) & ~4095
        path = f'Pack/Actor/{alias}.pack.zs'
        resources[path] = byml_codec.build_sarc(clone)
        templates[path] = source
        for table in tables:
            row = rows[table].get(actor)
            if row is None:
                # Native actors need no PouchActorInfo alias when they have no such row.
                if table == RSDB_FILES['PouchActorInfo']:
                    continue
                raise ValueError(f'Entrée de récompense absente dans {table} pour {ident}.')
            if alias in rows[table]:
                raise ValueError(f'Entrée de récompense déjà présente pour {alias}.')
            tables[table]['root'].append({**row, '__RowId': alias})

    for path, document in tables.items():
        document['root'].sort(key=lambda row: row['__RowId'])
        resources[path] = byml_codec.dump(document)
    return resources, templates, flags, member_sizes


def prepare_trigger_resources(manifest, tracking, read_raw, extra_flags=None):
    """Build only resources with an exact, seed-specific OotrR hook."""
    from oot_rando.formats.byml_codec import build_sarc
    from oot_rando.formats.inspect_resources import sarc
    from oot_rando.game.tracking_metadata import GAMEDATA, add_saved_flags
    from oot_rando.patching.soul_adapter import murmur3

    checks = tracking['checks']
    by_collection = {row['collection']['hash']: ident for ident, row in checks.items()
                     if (row.get('collection') or {}).get('type') == 'bool'}
    events = defaultdict(list)
    flags = dict(extra_flags or {})
    event_candidates = {}
    resources = {}
    for resource, markers in tracking.get('event_markers', {}).items():
        if resource not in manifest['files']:
            continue
        for marker in markers:
            original = marker['flag']
            ident = by_collection.get(str(murmur3(original)))
            if ident and original.endswith('.' + ident):
                trigger = trigger_flag_name(ident)
                event_candidates[trigger] = ident
                events[resource].append((marker, trigger))
    for resource, hooks in events.items():
        patched, added = add_event_triggers(read_raw(resource), hooks)
        if added:
            resources[resource] = patched
            flags.update((event_candidates[flag], flag) for flag in added)

    for record in tracking.get('repeatables', ()):
        ident = record['id']
        actor = record['actor']
        if (record.get('kind') != 'pickup' or not actor.startswith('Obj_RandoOnce_')
                or actor != 'Obj_RandoOnce_' + sha256(ident.encode('utf-8')).hexdigest()[:16]
                or checks.get(ident, {}).get('collection') != {'type': 'bool', 'hash': str(record['flag_hash'])}):
            continue
        path = f'Pack/Actor/{actor}.pack.zs'
        if path not in manifest['files']:
            continue
        pack = sarc(read_raw(path))
        root = f'AI/{actor}.root.ainb'
        flag = flags.setdefault(ident, trigger_flag_name(ident))
        pack[root] = add_drop_trigger(pack[root], flag)
        resources[path] = build_sarc(pack)

    if not flags:
        raise ValueError('Aucun déclencheur compatible dans cette seed.')
    resources[GAMEDATA] = add_saved_flags(read_raw(GAMEDATA), dict.fromkeys(flags.values(), False))
    return resources, {ident: murmur3(flag) for ident, flag in flags.items()}


def _seed_metadata(source):
    from oot_rando.randomizer.randomizer_services import read_artifact

    manifest, _ = read_artifact(source)
    return manifest, json.loads((source / 'tracking.json').read_bytes()) if manifest.get('tracking') else {}


def _prepare_files(nup_path, source, manifest, tracking, skulltulas):
    """Build the changed resources and metadata before touching the seed."""
    from oot_rando.formats.inspect_nup import Nup
    from oot_rando.formats.inspect_resources import decompress, dictionaries
    from oot_rando.game.resource_allocations import allocation
    from oot_rando.game.world_maps import effective_members
    from oot_rando.patching.randomize_kokiri import RESTBL, check_supported_game
    from oot_rando.randomizer.randomizer_core import grow_resource_table, recompress

    if manifest.get('generator_version') != '0.12.18' or not manifest.get('tracking'):
        raise ValueError('Ce prototype nécessite une seed OotrR 0.8.4 avec suivi.')
    if tracking.get('trigger_flags'):
        raise ValueError('Cette seed contient déjà des indicateurs de déclenchement.')
    nup = Nup(nup_path)
    files = manifest['files']
    with nup.stream:
        compression = dictionaries(nup)
        members = {}
        if skulltulas:
            check_supported_game(nup)
            members = effective_members(nup)

        def original(path):
            if path in files:
                return (source / 'romfs' / path).read_bytes()
            return nup.read(members[path])

        def read_raw(path):
            return decompress(original(path), compression)

        resources, templates, extra_flags, new_sizes = {}, {}, {}, {}
        if skulltulas:
            map_paths = [path for path in members.keys() | files.keys()
                         if path.startswith('Banc/') and path.endswith('.bcett.byml.zs')]
            resources, templates, extra_flags, new_sizes = prepare_skulltula_resources(tracking, map_paths, read_raw)
        other, flags = prepare_trigger_resources(manifest, tracking, read_raw, extra_flags)
        resources.update(other)
        encoded = {path: recompress(raw, original(templates.get(path, path)), compression)
                   for path, raw in resources.items()}
        if RESTBL in files or skulltulas:
            rest = read_raw(RESTBL)
            for path, template in templates.items():
                new_sizes[path] = max((len(resources[path]) + 8191) & ~4095, allocation(rest, template) or 0)
            growth = {path: max(len(raw) - len(read_raw(path)), 0)
                      for path, raw in resources.items() if path not in templates}
            allocations = grow_resource_table(encoded, growth, new_sizes, original, compression)
            previous = {entry['path']: entry for entry in manifest.get('resource_allocations', ())}
            for entry in allocations:
                path = entry['path']
                if path in previous:
                    previous[path]['after'] = entry['after']
                else:
                    previous[path] = entry
            manifest['resource_allocations'] = list(previous.values())
    tracking['trigger_flags'] = flags
    payload = json.dumps(tracking, ensure_ascii=False, indent=2).encode('utf-8')
    manifest['tracking']['sha256'] = sha256(payload).hexdigest()
    for resource, binary in encoded.items():
        files[resource] = {'size': len(binary), 'sha256': sha256(binary).hexdigest()}
    changed = {f'romfs/{resource}': binary for resource, binary in sorted(encoded.items())}
    changed['tracking.json'] = payload
    # Publish the manifest last, after the resources it describes.
    changed['manifest.json'] = json.dumps(manifest, ensure_ascii=False, indent=2).encode('utf-8')
    return changed, len(flags)


def prepare_seed(nup_path, source, output, skulltulas=False):
    """Copy the mod with its tracking metadata and adjusted resource checksums."""
    from oot_rando.randomizer.randomizer_services import read_artifact

    source, output = Path(source).resolve(), Path(output).absolute()
    if output.exists() or output.is_symlink() or output.resolve().is_relative_to(source):
        raise ValueError('Choisis un nouveau dossier de sortie hors de la seed d’origine.')
    manifest, tracking = _seed_metadata(source)
    changed, count = _prepare_files(nup_path, source, manifest, tracking, skulltulas)
    with TemporaryDirectory(prefix='map-trigger-', dir=output.parent) as temporary:
        staged = Path(temporary) / 'seed'
        for relative in ('checks.json', *(f'romfs/{resource}' for resource in manifest['files'])):
            path = staged / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            if relative not in changed:
                shutil.copyfile(source / relative, path)
        for relative, binary in changed.items():
            (staged / relative).write_bytes(binary)
        read_artifact(staged)
        staged.rename(output)
    return count


def _seed_file(root, relative):
    path = root / relative
    if (not path.is_relative_to(root) or path.resolve() != path or '..' in Path(relative).parts
            or any(part.is_symlink() for part in (path, *path.parents) if part != root
                   and part.is_relative_to(root))):
        raise ValueError(f'Chemin de seed non pris en charge : {relative}')
    return path


@contextmanager
def _lock_seed(source):
    lock = _seed_file(source, '.map-oot-rando.lock')
    with lock.open('a+b') as stream:
        try:
            if os.name == 'nt':
                import msvcrt
                stream.seek(0)
                msvcrt.locking(stream.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl
                fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError as error:
            raise ValueError('Une préparation utilise déjà ce dossier de seed.') from error
        yield


def _rollback_seed(source, backup, temporary):
    journal = json.loads(_seed_file(backup, 'pending.json').read_bytes())
    for relative, (had_original, digest) in reversed(tuple(journal.items())):
        if relative not in ('manifest.json', 'tracking.json') and not relative.startswith('romfs/'):
            raise ValueError(f'Chemin de sauvegarde inattendu : {relative}')
        path = _seed_file(source, relative)
        current = sha256(path.read_bytes()).hexdigest() if path.exists() else None
        if had_original:
            original = _seed_file(backup, f'originaux/{relative}')
            if current == sha256(original.read_bytes()).hexdigest():
                continue
            if current not in (None, digest):
                raise ValueError(f'Fichier modifié depuis la préparation : {relative}')
            restored = temporary / 'restore'
            shutil.copy2(original, restored)
            restored.replace(path)
        elif current == digest:
            path.unlink()
        elif current is not None:
            raise ValueError(f'Fichier modifié depuis la préparation : {relative}')
    shutil.rmtree(backup)


def prepare_seed_in_place(nup_path, source):
    """Prepare the selected mod once. Recover interrupted updates on retry."""
    from oot_rando.randomizer.randomizer_services import read_artifact

    source = Path(source).resolve()
    with _lock_seed(source), TemporaryDirectory(prefix='.map-trigger-', dir=source) as work:
        temporary = Path(work)
        backup = _seed_file(source, SEED_BACKUP)
        if (backup / 'pending.json').exists():
            _rollback_seed(source, backup, temporary)
        manifest, tracking = _seed_metadata(source)
        if tracking.get('trigger_flags'):
            return len(tracking['trigger_flags']), False
        if backup.exists():
            raise ValueError(f'Un dossier de sauvegarde existe déjà : {backup}')
        known_files = {'manifest.json', 'tracking.json'} | {f'romfs/{name}' for name in manifest['files']}
        changed, count = _prepare_files(nup_path, source, manifest, tracking, skulltulas=True)

        journal = {}
        staged_backup = temporary / 'backup'
        for relative, binary in changed.items():
            path = _seed_file(source, relative)
            had_original = relative in known_files
            if path.exists() != had_original:
                raise ValueError(f'Le dossier du mod a changé ou un fichier existe déjà : {relative}')
            if had_original:
                original = staged_backup / 'originaux' / relative
                original.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(path, original)
            staged = temporary / 'nouveaux' / relative
            staged.parent.mkdir(parents=True, exist_ok=True)
            staged.write_bytes(binary)
            journal[relative] = (had_original, sha256(binary).hexdigest())
        (staged_backup / 'pending.json').write_text(json.dumps(journal), encoding='utf-8')
        staged_backup.rename(backup)

        try:
            for relative in changed:
                path = _seed_file(source, relative)
                path.parent.mkdir(parents=True, exist_ok=True)
                (temporary / 'nouveaux' / relative).replace(path)
            read_artifact(source)
            (backup / 'pending.json').rename(backup / 'changes.json')
        except (OSError, ValueError, KeyError):
            _rollback_seed(source, backup, temporary)
            raise
        return count, True


def main():
    parser = argparse.ArgumentParser(description='Prototype pour une nouvelle partie avec des indicateurs de déclenchement.')
    parser.add_argument('nup', type=Path)
    parser.add_argument('seed', type=Path)
    parser.add_argument('output', type=Path)
    parser.add_argument('--skulltulas', action='store_true',
                        help='Ajoute aussi les Skulltulas avec le suivi expérimental du lâcher.')
    args = parser.parse_args()
    try:
        count = prepare_seed(args.nup, args.seed, args.output, skulltulas=args.skulltulas)
    except (OSError, ValueError, KeyError) as error:
        parser.error(str(error))
    print(f'{count} checks instrumentés dans {args.output}. À utiliser avec une nouvelle partie.')


if __name__ == '__main__':
    main()
