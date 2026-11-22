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
