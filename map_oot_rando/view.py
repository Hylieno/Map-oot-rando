"""Coordinate navigation independent of Tk and game data."""
from dataclasses import dataclass


@dataclass
class Viewport:
    scale: float = 1.0
    x: float = 0.0
    y: float = 0.0

    def screen(self, point):
        return point[0] * self.scale + self.x, point[1] * self.scale + self.y

    def center(self, point, width, height):
        self.x = width / 2 - point[0] * self.scale
        self.y = height / 2 - point[1] * self.scale

    def zoom(self, factor, anchor):
        old = self.scale
        self.scale = min(1000, max(0.001, old * factor))
        self.x = anchor[0] - (anchor[0] - self.x) * self.scale / old
        self.y = anchor[1] - (anchor[1] - self.y) * self.scale / old

    def fit(self, points, width, height, *, min_extent=1):
        if not points:
            return
        low = tuple(min(p[i] for p in points) for i in (0, 1))
        high = tuple(max(p[i] for p in points) for i in (0, 1))
        self.scale = min(1000, max(0.001, min(
            max(width - 80, 1) / max(high[0] - low[0], min_extent),
            max(height - 80, 1) / max(high[1] - low[1], min_extent))))
        self.center(tuple((low[i] + high[i]) / 2 for i in (0, 1)), width, height)

    def grid(self, width, height):
        """Return a world-aligned grid and its spacing in world units."""
        from math import ceil, log10

        step = 10 ** ceil(log10(35 / self.scale))
        if step * self.scale > 140:
            step /= 5
        pixels = step * self.scale
        xs = range(ceil(width / pixels))
        ys = range(ceil(height / pixels))
        return (step, [self.x % pixels + i * pixels for i in xs],
                [self.y % pixels + i * pixels for i in ys])
