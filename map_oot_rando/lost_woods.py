"""Original navigation plan of the Lost Woods in game X/Z coordinates."""
from PIL import Image, ImageDraw

from .aerial import AerialImage

SOURCE = 'lost-woods-plan'
CALIBRATION = 1
# Ground-level junctions and crossings from the LostWood scene resources.
# The isolated branches end at reset exits, or lead to the two shortcuts.
SAFE_ROUTE = ((0, 7), (0, 0), (24, 0), (24, -24), (47.9, -24),
              (47.9, -48.1), (47.9, -72), (24, -72), (24, -83.7))
BRANCHES = (
    ((0, 0), (-31, 0)), ((0, 0), (0, -9.5)),
    ((24, 0), (24, 9.5)), ((24, 0), (48, 0), (48, 21)),
    ((24, -24), (14.5, -24)), ((24, -24), (24, -35.66)),
    ((47.9, -24), (47.9, -14.5)), ((47.9, -24), (58, -25.6), (68.5, -25.6)),
    ((47.9, -48.1), (57.5, -48.1)), ((47.9, -48.1), (23.8, -48.1), (4, -48.1)),
    ((47.9, -72), (57.5, -72)), ((47.9, -72), (47.9, -81.5)),
    ((24, -72), (14.5, -72)), ((24, -72), (24, -62.5)),
)


def lost_woods_plan():
    """Draw the clearings, tunnels and the usual route to the Sacred Meadow."""
    low, high, scale = (-43, -95), (78, 30), 6
    size = tuple((b - a) * scale for a, b in zip(low, high))
    image = Image.new('RGB', size, '#0d1f2e')
    draw = ImageDraw.Draw(image)

    def pixel(point):
        x, z = point
        return (x - low[0]) * scale, (z - low[1]) * scale

    for color, width in (('#7bb6ce', 6), ('#1f5577', 5)):
        for path in (SAFE_ROUTE, *BRANCHES):
            draw.line([pixel(point) for point in path], fill=color, width=width * scale, joint='curve')
    for x, z in (*SAFE_ROUTE[1:-1], (-28, 0), (48, 12), (6, -48)):
        draw.ellipse((*pixel((x-5.5, z-5.5)), *pixel((x+5.5, z+5.5))),
                     fill='#1f5577', outline='#7bb6ce', width=2)
    route = [pixel(point) for point in SAFE_ROUTE]
    draw.line(route, fill='#0c2631', width=11, joint='curve')
    draw.line(route, fill='#ffe388', width=5, joint='curve')
    return AerialImage(image, [(0, 0), (size[0], 0), (0, size[1])],
                       [low, (high[0], low[1]), (low[0], high[1])], source=SOURCE,
                       calibration=CALIBRATION)
