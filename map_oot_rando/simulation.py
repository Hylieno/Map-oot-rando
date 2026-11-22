"""Fictional fixtures: neither real check names nor real Kokiri coordinates."""
from datetime import datetime, timezone
from .model import UPSTREAM_REVISION
from .state import StateStore


def demo_document():
    rows = []
    for index, (kind, position) in enumerate([
        ('rock', [0, 0, 0]), ('pot', [100, 10, 80]),
        ('chest', [-80, 20, 100]), ('bush', [120, 0, -90]),
        ('chest', None),
    ]):
        rows.append(dict(id=f'SIMULATED#{index}', name=f'Exemple fictif {kind} {index}',
                         category=kind, resource='SIMULATION / extérieur', position=position))
    rows.append(dict(id='SIMULATED#interior', name='Intérieur fictif', category='pot',
                     resource='SIMULATION / intérieur', position=[0, 50, 0]))
    return dict(schema_version=1, upstream_revision=UPSTREAM_REVISION,
                region='KokiriForest', provenance='synthetic', locations=rows)


class Simulation:
    def __init__(self, locations):
        self.store = StateStore('simulation', [row.id for row in locations], simulated=True)
        statuses = ['available', 'blocked', 'unknown', 'completed']
        self.values = {key: statuses[i % 4] for i, key in enumerate(self.store.states)}
        self.connected = True
        self.publish()

    def publish(self):
        if self.connected:
            self.store.publish('simulation', self.values, mode='simulation',
                               timestamp=datetime.now(timezone.utc).isoformat(timespec='seconds'))

    def change(self, ident, status):
        if status not in {'available', 'blocked', 'unknown', 'completed'}:
            raise ValueError('Unknown simulation status')
        if ident not in self.values:
            raise ValueError('Unknown simulated check')
        self.values[ident] = status
        self.publish()

    def toggle_connection(self):
        self.connected = not self.connected
        if self.connected:
            self.publish()
        else:
            self.store.disconnect()
