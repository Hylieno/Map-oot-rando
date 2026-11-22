import unittest
from map_oot_rando.view import Viewport
from map_oot_rando.simulation import Simulation, demo_document
from map_oot_rando.model import load_metadata


class ViewTests(unittest.TestCase):
    def test_zoom_anchor_and_center(self):
        view = Viewport(2, 10, 20)
        point = (30, -40)
        anchor = view.screen(point)
        view.zoom(1.2, anchor)
        self.assertEqual(view.screen(point), anchor)
        view.center(point, 800, 600)
        self.assertEqual(view.screen(point), (400, 300))

    def test_fit_bounds_and_degenerate_point(self):
        for points in [[(0, 0)], [(-1000, -400), (200, 800)]]:
            view = Viewport()
            view.fit(points, 800, 600)
            for point in points:
                x, y = view.screen(point)
                self.assertTrue(0 <= x <= 800 and 0 <= y <= 600)

    def test_simulation_disconnect_preserves_then_reconnects(self):
        simulation = Simulation(load_metadata(demo_document()))
        key = next(iter(simulation.values))
        simulation.change(key, 'available')
        timestamp = simulation.store.last_success
        simulation.toggle_connection()
        simulation.change(key, 'completed')
        self.assertEqual(simulation.store.states[key], 'available')
        self.assertEqual(simulation.store.last_success, timestamp)
        simulation.toggle_connection()
        self.assertEqual(simulation.store.states[key], 'completed')
        self.assertEqual(simulation.store.connection, 'simulation')
