"""Export already-labelled OotrR scan results without reading or copying game assets."""
from .model import UPSTREAM_REVISION, load_metadata


def export_scan(groups, extra, *, provenance):
    """Consume scan_world chest groups and extra sources; never generate labels.

    Caller must scan the full world before restricting to Kokiri Forest so OotrR
    numbering remains authoritative. No positions are inferred for event checks.
    """
    rows, diagnostics = [], []
    entries = [(gid, 'chest', variants) for gid, variants in groups.items()]
    entries += [(gid, entry['source'], entry['variants']) for gid, entry in extra.items()]
    for gid, category, variants in entries:
        for variant in variants:
            resource = variant.get('resource', '')
            if not resource.startswith('Banc/KokiriForest/'):
                continue
            position = variant.get('position')
            if position is None:
                diagnostics.append(f'{gid}: missing coordinates in {resource}')
            rows.append(dict(id=gid, name=variant.get('label') or gid,
                             category=category, resource=resource, position=position))
        if not variants and gid.startswith('KokiriForest#'):
            diagnostics.append(f'{gid}: no positioned variants')
    document = dict(schema_version=1, region='KokiriForest',
                    upstream_revision=UPSTREAM_REVISION, provenance=provenance,
                    locations=rows, diagnostics=diagnostics)
    load_metadata(document)
    return document



def world_check_rows(maps, checks, eligible):
    """Resolve legacy world-map check IDs by the actor hash and exact patch field."""
    requested = {check['id']: check for check in checks}
    rows = []
    for path, resource in maps.items():
        if not path.startswith('Banc/KokiriForest/'):
            continue
        for actor in resource['root'].get('Actors', ()):
            if type(actor.get('Hash')) is not int or not eligible(path, actor):
                continue
            prefix = f"KokiriForest#{actor['Hash']}#"
            dynamic = actor.get('Dynamic')
            fields = ['Gyaml', *(dynamic if isinstance(dynamic, dict) else ())]
            for field in fields:
                ident = prefix + field
                if ident in requested:
                    check = requested[ident]
                    rows.append(dict(id=ident, name=check['name'], category=check['category'],
                                     resource=path, position=actor.get('Translate')))
    return rows

def bind_catalogue(document, catalogue):
    """Use the seed's names and IDs; keep unmatched Kokiri entries searchable."""
    if (catalogue.get('schema_version') != 1 or not isinstance(catalogue.get('seed_id'), str)
            or not catalogue['seed_id']):
        raise ValueError('Catalogue OotrR v1 avec seed_id requis')
    by_id = {}
    for row in document['locations']:
        by_id.setdefault(row['id'], []).append(row)
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
        if not matches and (check.get('zone') != 'KokiriForest'
                            and check.get('region') not in {'Kokiri Forest', 'KokiriForest'}
                            and not ident.startswith('KokiriForest#')):
            continue
        if not matches:
            matches = [dict(resource='Emplacements sans position', position=None)]
        if all(row['position'] is None for row in matches):
            diagnostics.append(f'{ident}: coordonnées absentes pour ce check')
        for row in matches:
            locations.append(dict(row, id=ident, name=check['name'],
                                  alias=row.get('name', ''), category=check['category']))
    result = dict(document, seed_id=catalogue['seed_id'], locations=locations,
                  diagnostics=diagnostics)
    load_metadata(result)
    return result
