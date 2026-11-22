"""Passive sink for a single authoritative tracker owner; never refreshes memory."""
from .model import STATUSES


def tracker_states(session, identifiers):
    """Call after the owner's refresh completes; session is an OotrR TrackerSession.

    The owner must serialize publication with refresh to obtain one coherent batch.
    Connection mode is deliberately not guessed from upstream English messages.
    """
    result = {}
    for ident in identifiers:
        row = session.check_state(ident)
        access = row.get('access', 'unknown')
        result[ident] = 'completed' if row.get('completed') else (
            access if access in {'available', 'blocked'} else 'unknown')
    return result


class StateStore:
    def __init__(self, seed_id, identifiers, *, simulated=False):
        self.simulated = simulated
        self.reset(seed_id, identifiers)

    def reset(self, seed_id, identifiers):
        self.seed_id = seed_id
        self.states = dict.fromkeys(identifiers, 'unknown')
        self.connection = 'disconnected'
        self.last_success = None

    def publish(self, seed_id, states, *, mode, timestamp):
        if seed_id != self.seed_id:
            raise ValueError('Seed mismatch; reset explicitly before publishing')
        if mode not in {'live', 'save', 'simulation'} or (mode == 'simulation') != self.simulated:
            raise ValueError('Invalid connection mode or mixed simulation/real data')
        if set(states) != set(self.states) or any(s not in STATUSES for s in states.values()):
            raise ValueError('Expected a complete authoritative state snapshot')
        if not isinstance(timestamp, str) or not timestamp:
            raise ValueError('Successful synchronization timestamp required')
        self.states = dict(states)
        self.connection, self.last_success = mode, timestamp

    def disconnect(self):
        self.connection = 'disconnected'
