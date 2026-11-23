"""Versioned coordinate metadata and renderer-independent queries."""
from dataclasses import dataclass
import math

UPSTREAM_REVISION = 'eb6682704f7589b5a0c07ac0e49d89fef4108545'
OLDER_EXPORT_REVISIONS = frozenset({'283d3ec0f161d32e168afac45e502442c1ffb081'})
STATUSES = frozenset({'available', 'blocked', 'unknown', 'completed', 'partial'})
REGION_NAMES = {
    'KokiriForest': 'Kokiri Forest',
    'LostWood': 'Bois Perdus',
    'HyruleField': 'Plaine d’Hyrule',
    'SacredForestMeadow': 'Bosquet sacré',
    'KakarikoVillage': 'Cocorico',
}


def resource_region(resource):
    banc, _, remainder = resource.partition('/')
    region, separator, _ = remainder.partition('/')
    return region if banc == 'Banc' and separator and region in REGION_NAMES else None


@dataclass(frozen=True)
class Location:
    id: str
    name: str
    category: str
    resource: str
    position: tuple[float, float, float] | None

    alias: str = ''
    region: str = 'KokiriForest'
    entrance: tuple[float, float, float] | None = None

    def project(self):
        """Raw X/Z plan, +Z downward; Y retained, orientation unverified in game."""
        point = self.entrance or self.position
        return None if point is None else (point[0], point[2])


def read_position(position):
    if position is None:
        return None
    if (not isinstance(position, (list, tuple)) or len(position) != 3
            or any(type(v) not in (int, float) or not math.isfinite(v) for v in position)):
        raise ValueError('Expected three finite coordinates')
    return tuple(position)


def load_metadata(document):
    if document.get('schema_version') != 1 or document.get('region') != 'KokiriForest':
        raise ValueError('Unsupported metadata schema or region')
    if document.get('upstream_revision') not in OLDER_EXPORT_REVISIONS | {UPSTREAM_REVISION}:
        raise ValueError('Unsupported upstream revision')
    if document.get('provenance') not in {'synthetic', 'ootrr-scan'}:
        raise ValueError('Explicit coordinate provenance required')
    regions = document.get('regions', ('KokiriForest',))
    if (not isinstance(regions, (list, tuple)) or not regions or regions[0] != document['region']
            or any(not isinstance(region, str) or region not in REGION_NAMES for region in regions)
            or len(set(regions)) != len(regions)):
        raise ValueError('Régions de la carte invalides')
    result, seen = [], set()
    for row in document['locations']:
        for field in ('id', 'name', 'category', 'resource'):
            if not isinstance(row.get(field), str) or not row[field]:
                raise ValueError('Missing location field: ' + field)
        position = read_position(row.get('position'))
        entrance = read_position(row.get('entrance'))
        if entrance is not None and position is None:
            raise ValueError('Une entrée requiert les coordonnées du check')
        alias = row.get('alias', '')
        if not isinstance(alias, str):
            raise ValueError('Invalid search alias')
        frame = resource_region(row['resource'])
        region = row.get('region', frame or document['region'])
        if region not in regions or (frame is not None and frame != region):
            raise ValueError('Région de l’emplacement invalide')
        location = Location(row['id'], row['name'], row['category'], row['resource'],
                            position, alias, region, entrance)
        # The tracker identifies the check, while the scan may report multiple
        # placements in a single resource. Collapse only identical records.
        if location not in seen:
            seen.add(location)
            result.append(location)
    return tuple(result)


def select(locations, states, query='', statuses=STATUSES, categories=None, resource=None):
    query = query.strip().casefold()
    return tuple(row for row in locations
                 if any(query in value.casefold() for value in (row.id, row.name, row.alias))
                 and states.get(row.id, 'unknown') in statuses
                 and (categories is None or row.category in categories)
                 and (resource is None or row.resource == resource))
