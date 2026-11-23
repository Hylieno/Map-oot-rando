"""Export already-labelled OotrR scan results without reading or copying game assets."""
from .model import REGION_NAMES, UPSTREAM_REVISION, load_metadata, resource_region

LOST_WOOD_EVENT_ACTORS = {
    'npc#LW Skull Kid': ('Npc_SkullKid_Child', None),
    'npc#LW Ocarina Memory Game': ('Npc_SkullKid_Child_02', None),
    'npc#LW Target in Woods': ('NPC_Scrub_Deku_TargetPractice', None),
    'scrub#LW Deku Scrub Near Bridge': ('Enemy_Scrub_Business', 'Enemy_Scrub_Business_DekuStickPouch_01'),
    'scrub#LW Deku Scrub Grotto Front': ('Enemy_Scrub_Business', 'Enemy_Scrub_Business_DekuNutsPouch_01'),
}
EVENT_ACTORS = {
    'LostWood': {actor: ident for ident, actor in LOST_WOOD_EVENT_ACTORS.items()},
    'GoronCity': {('Npc_Goron_Darunia_Child', None): 'npc#GC Darunias Joy'},
}
DEKU_THEATER_CHECKS = ('npc#Deku Theater Skull Mask', 'npc#Deku Theater Mask of Truth')
GROTTO_ENTRANCE_ACTORS = {
    'SacredForestMeadow#7995233962349162969': (8456945034417122929, 'Land_Kokiri_HidingHoleCover_A_01'),
    'SacredForestMeadow#1764383515296652106': (15024208487326008169, 'Land_SacredForest_HidingHoleCover_A_02'),
    **dict.fromkeys(DEKU_THEATER_CHECKS, (4876738002315557989, 'DestinationAnchor')),
}


def add_surface_entrances(rows, maps):
    """Place the surface marker at the known entrance of a buried check."""
    entrance_ids = set(GROTTO_ENTRANCE_ACTORS.values())
    candidates = {}
    for path, source in maps.items():
        if resource_region(path) not in {'SacredForestMeadow', 'LostWood'}:
            continue
        age_frame = path.rsplit('_', 1)[0]
        for actor in source['root'].get('Actors', ()):
            key = (actor.get('Hash'), actor.get('Gyaml'))
            if key in entrance_ids and actor.get('Translate'):
                candidates.setdefault((age_frame, key), set()).add(tuple(actor['Translate']))
    for row in rows:
        key = GROTTO_ENTRANCE_ACTORS.get(row['id'])
        if key and row['position'] is not None:
            points = candidates.get((row['resource'].rsplit('_', 1)[0], key), ())
            if len(points) == 1:
                row['entrance'] = next(iter(points))


def export_scan(groups, extra, *, provenance, regions=('KokiriForest',)):
    """Consume scan_world chest groups and extra sources; never generate labels.

    Caller must scan the full world before restricting the regions so OotrR
    numbering remains authoritative. No positions are inferred for event checks.
    """
    rows, diagnostics = [], []
    entries = [(gid, 'chest', variants) for gid, variants in groups.items()]
    entries += [(gid, entry['source'], entry['variants']) for gid, entry in extra.items()]
    for gid, category, variants in entries:
        for variant in variants:
            resource = variant.get('resource', '')
            if resource_region(resource) not in regions:
                continue
            position = variant.get('position')
            if position is None:
                diagnostics.append(f'{gid}: missing coordinates in {resource}')
            rows.append(dict(id=gid, name=variant.get('label') or gid,
                             category=category, resource=resource, position=position))
        if not variants and gid.partition('#')[0] in regions:
            diagnostics.append(f'{gid}: no positioned variants')
    document = dict(schema_version=1, region='KokiriForest',
                    upstream_revision=UPSTREAM_REVISION, provenance=provenance,
                    locations=rows, diagnostics=diagnostics)
    if tuple(regions) != ('KokiriForest',):
        document['regions'] = list(regions)
    load_metadata(document)
    return document



def world_check_rows(maps, checks, eligible):
    """Resolve legacy world-map check IDs by the actor hash and exact patch field."""
    requested = {check['id']: check for check in checks}
    rows = []
    for path, resource in maps.items():
        region = resource_region(path)
        if region is None:
            continue
        for actor in resource['root'].get('Actors', ()):
            if type(actor.get('Hash')) is not int or not eligible(path, actor):
                continue
            prefix = f"{region}#{actor['Hash']}#"
            dynamic = actor.get('Dynamic')
            fields = ['Gyaml', *(dynamic if isinstance(dynamic, dict) else ())]
            for field in fields:
                ident = prefix + field
                if ident in requested:
                    check = requested[ident]
                    rows.append(dict(id=ident, name=check['name'], category=check['category'],
                                     resource=path, position=actor.get('Translate')))
    return rows


def event_check_rows(maps, eligible):
    """Locate event rewards at their unique NPC in each age."""
    candidates = {}
    for path, source in maps.items():
        region = resource_region(path)
        ids = EVENT_ACTORS.get(region)
        if ids is None:
            continue
        age_frame = path.removesuffix('.bcett.byml.zs').rsplit('_', 1)[0]
        for actor in source['root'].get('Actors', ()):
            dynamic = actor.get('Dynamic')
            event = dynamic.get('TalkEventName') if isinstance(dynamic, dict) else None
            ident = ids.get((actor.get('Gyaml'), event))
            position = actor.get('Translate')
            checks = (ident,) if ident else ()
            if (region == 'LostWood' and actor.get('Gyaml') == 'Enemy_Scrub_ForestStage_Elder'
                    and actor.get('Name') == 'ScrubForestStageElder' and age_frame.endswith('_Child')):
                checks = DEKU_THEATER_CHECKS
            if position and checks and eligible(path, actor):
                for check in checks:
                    candidates.setdefault((check, age_frame), []).append(
                        dict(id=check, name=check.partition('#')[2], category='event',
                             resource=path, position=position))
    return [rows[0] for rows in candidates.values() if len(rows) == 1]


def bind_catalogue(document, catalogue):
    """Use the seed's names and IDs and keep unmatched entries searchable."""
    if (catalogue.get('schema_version') != 1 or not isinstance(catalogue.get('seed_id'), str)
            or not catalogue['seed_id']):
        raise ValueError('Catalogue OotrR v1 avec seed_id requis')
    by_id = {}
    for row in document['locations']:
        by_id.setdefault(row['id'], []).append(row)
    regions = document.get('regions', ('KokiriForest',))
    names = {name: region for region, name in REGION_NAMES.items()}
    names.update({'Lost Woods': 'LostWood', 'the Lost Woods': 'LostWood', 'Hyrule Field': 'HyruleField',
                  'Sacred Forest Meadow': 'SacredForestMeadow', 'Kakariko Village': 'KakarikoVillage',
                  'Death Mountain Trail': 'DeathMountainTrail', 'Goron City': 'GoronCity'})
    locations, diagnostics, seen = [], [], set()
    for check in catalogue['checks']:
        ident = check['id']
        if ident in seen:
            raise ValueError(f'Identifiant en double dans le catalogue : {ident}')
        seen.add(ident)
        matches = by_id.get(ident, ())
        if not matches and ident.isdecimal():
            # OotrR's original Kokiri chest mode uses the bare actor hash.
            matches = by_id.get('KokiriForest#' + ident, ())
        if not matches:
            candidates = (check.get('zone'), names.get(check.get('region'), check.get('region')),
                          ident.partition('#')[0])
            region = next((value for value in candidates if value in regions), None)
            if region is None:
                continue
            matches = [dict(resource='Emplacements sans position', position=None, region=region)]
        if all(row['position'] is None for row in matches):
            diagnostics.append(f'{ident}: coordonnées absentes pour ce check')
        for row in matches:
            locations.append(dict(row, id=ident, name=check['name'],
                                  alias=row.get('name', ''), category=check['category']))
    result = dict(document, seed_id=catalogue['seed_id'], locations=locations,
                  diagnostics=diagnostics)
    load_metadata(result)
    return result
