"""Prepare a separate seed with independent trigger flags (OotrR 0.8.4 prototype)."""
from collections import defaultdict
from copy import copy
from hashlib import sha256
from io import BytesIO
from pathlib import Path
from tempfile import TemporaryDirectory
import argparse
import json
import shutil


def trigger_flag_name(ident):
    digest = sha256(ident.encode('utf-8')).hexdigest()[:20]
    return f'RandoMap.Trigger.{digest}'


def add_event_triggers(raw, hooks):
    """Insert a setter on entry to the exact reward event patched by OotrR."""
    from evfl.container import Container
    from evfl.event import ActionEvent, Event
    from evfl.util import make_index
    from oot_rando.patching.event_patch import _flow

    flow = _flow(raw)
    events = {event.name: event for event in flow.flowchart.events}
    for hook, flag in hooks:
        reward = events.get(hook['event'])
        original = events.get(hook['marker'])
        name = 'RandoMapTrigger_' + hook['event']
        if (not reward or not original or name in events or not hasattr(reward.data, 'nxt')
                or reward.data.nxt.v is not original or not isinstance(original.data, ActionEvent)
                or str(original.data.actor.v.identifier) != 'GameDataActor'
                or original.data.actor_action.v.v != 'EventTriggerSetGameDataBool'
                or original.data.params.data != {'GameDataName': hook['flag'], 'Index': -1, 'Value': True}):
            raise ValueError(f'Événement de récompense inattendu : {hook["event"]}')
        # Existing branches and entry points target this object. Keep those
        # references and move the reward action just after the new setter.
        payout = Event()
        payout.name, payout.data = reward.name, reward.data
        reward.name = name
        reward.data = copy(original.data)
        reward.data.params = Container()
        reward.data.params.data = {'GameDataName': flag, 'Index': -1, 'Value': True}
        reward.data.nxt = make_index(payout)
        flow.flowchart.events.append(payout)
    stream = BytesIO()
    flow.write(stream)
    return stream.getvalue()


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


def prepare_trigger_resources(manifest, tracking, read_raw):
    """Build only resources with an exact, seed-specific OotrR hook."""
    from oot_rando.formats.byml_codec import build_sarc
    from oot_rando.formats.inspect_resources import sarc
    from oot_rando.game.tracking_metadata import GAMEDATA, add_saved_flags
    from oot_rando.patching.soul_adapter import murmur3

    checks = tracking['checks']
    by_collection = {row['collection']['hash']: ident for ident, row in checks.items()
                     if (row.get('collection') or {}).get('type') == 'bool'}
    events = defaultdict(list)
    flags = {}
    resources = {}
    for resource, markers in tracking.get('event_markers', {}).items():
        if resource not in manifest['files']:
            continue
        for marker in markers:
            original = marker['flag']
            ident = by_collection.get(str(murmur3(original)))
            if ident and original.endswith('.' + ident):
                trigger = flags.setdefault(ident, trigger_flag_name(ident))
                events[resource].append((marker, trigger))
    for resource, hooks in events.items():
        resources[resource] = add_event_triggers(read_raw(resource), hooks)

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


def prepare_seed(nup_path, source, output):
    """Copy the mod with its tracking metadata and adjusted resource checksums."""
    from oot_rando.formats.inspect_nup import Nup
    from oot_rando.formats.inspect_resources import decompress, dictionaries
    from oot_rando.randomizer.randomizer_core import recompress
    from oot_rando.randomizer.randomizer_services import read_artifact

    source, output = Path(source).resolve(), Path(output).absolute()
    if output.exists() or output.is_symlink() or output.resolve().is_relative_to(source):
        raise ValueError('Choisis un nouveau dossier de sortie hors de la seed d’origine.')
    manifest, _ = read_artifact(source)
    if manifest.get('generator_version') != '0.12.18' or not manifest.get('tracking'):
        raise ValueError('Ce prototype nécessite une seed OotrR 0.8.4 avec suivi.')
    tracking = json.loads((source / 'tracking.json').read_bytes())
    if tracking.get('trigger_flags'):
        raise ValueError('Cette seed contient déjà des indicateurs de déclenchement.')
    nup = Nup(nup_path)
    with nup.stream:
        compression = dictionaries(nup)

    def original(path):
        if path not in manifest['files']:
            raise ValueError(f'Ressource absente de la seed : {path}')
        return (source / 'romfs' / path).read_bytes()

    resources, flags = prepare_trigger_resources(manifest, tracking, lambda path: decompress(original(path), compression))
    tracking['trigger_flags'] = flags
    payload = json.dumps(tracking, ensure_ascii=False, indent=2).encode('utf-8')
    manifest['tracking']['sha256'] = sha256(payload).hexdigest()

    with TemporaryDirectory(prefix='map-trigger-', dir=output.parent) as temporary:
        staged = Path(temporary) / 'seed'
        for resource, info in manifest['files'].items():
            path = staged / 'romfs' / resource
            path.parent.mkdir(parents=True, exist_ok=True)
            if resource in resources:
                binary = recompress(resources[resource], original(resource), compression)
                path.write_bytes(binary)
                info.update(size=len(binary), sha256=sha256(binary).hexdigest())
            else:
                shutil.copyfile(source / 'romfs' / resource, path)
        shutil.copyfile(source / 'checks.json', staged / 'checks.json')
        (staged / 'tracking.json').write_bytes(payload)
        (staged / 'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding='utf-8')
        read_artifact(staged)
        staged.rename(output)
    return len(flags)


def main():
    parser = argparse.ArgumentParser(description='Prototype pour une nouvelle partie avec des indicateurs de déclenchement.')
    parser.add_argument('nup', type=Path)
    parser.add_argument('seed', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    try:
        count = prepare_seed(args.nup, args.seed, args.output)
    except (OSError, ValueError, KeyError) as error:
        parser.error(str(error))
    print(f'{count} checks instrumentés dans {args.output}. À utiliser avec une nouvelle partie.')


if __name__ == '__main__':
    main()
