"""Versioned coordinate metadata and renderer-independent queries."""
from dataclasses import dataclass
import math

UPSTREAM_REVISION = '283d3ec0f161d32e168afac45e502442c1ffb081'
STATUSES = frozenset({'available', 'blocked', 'unknown', 'completed'})


@dataclass(frozen=True)
class Location:
    id: str
    name: str
    category: str
    resource: str
    position: tuple[float, float, float] | None

    alias: str = ''

    def project(self):
        """Raw X/Z plan, +Z downward; Y retained, orientation unverified in game."""
        return None if self.position is None else (self.position[0], self.position[2])


def load_metadata(document):
    if document.get('schema_version') != 1 or document.get('region') != 'KokiriForest':
        raise ValueError('Unsupported metadata schema or region')
    if document.get('upstream_revision') != UPSTREAM_REVISION:
        raise ValueError('Unsupported upstream revision')
    if document.get('provenance') not in {'synthetic', 'ootrr-scan'}:
        raise ValueError('Explicit coordinate provenance required')
    result, seen = [], set()
    for row in document['locations']:
        for field in ('id', 'name', 'category', 'resource'):
            if not isinstance(row.get(field), str) or not row[field]:
                raise ValueError('Missing location field: ' + field)
        key = (row['id'], row['resource'])
        if key in seen:
            raise ValueError('Duplicate check/resource pair')
        seen.add(key)
        position = row.get('position')
        if position is not None:
            if (not isinstance(position, (list, tuple)) or len(position) != 3
                    or any(type(v) not in (int, float) or not math.isfinite(v) for v in position)):
                raise ValueError('Expected three finite coordinates')
            position = tuple(position)
        alias = row.get('alias', '')
        if not isinstance(alias, str):
            raise ValueError('Invalid search alias')
        result.append(Location(row['id'], row['name'], row['category'], row['resource'], position, alias))
    return tuple(result)


def select(locations, states, query='', statuses=STATUSES, categories=None, resource=None):
    query = query.strip().casefold()
    return tuple(row for row in locations
                 if any(query in value.casefold() for value in (row.id, row.name, row.alias))
                 and states.get(row.id, 'unknown') in statuses
                 and (categories is None or row.category in categories)
                 and (resource is None or row.resource == resource))
