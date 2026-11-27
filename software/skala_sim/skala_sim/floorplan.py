"""Local multi-room teleoperation world; coordinates are metres, X forward/Y left."""
from collections import deque
import json
from pathlib import Path
from xml.sax.saxutils import escape


ROOMS = [('Office', -4, 2.9), ('Studio', 0, 2.9), ('Workshop', 4, 2.9),
         ('Lounge', -3, -2.9), ('Storage', 3, -2.9)]


def objects():
    result = []
    wall = [.48, .55, .61, 1]
    wood = [.50, .31, .15, 1]

    def box(name, size, xyz, colour=wall):
        result.append((name, size, xyz, colour, (0, 0, 0)))

    def horizontal(name, y, start, end, colour=wall):
        box(name, [end-start, .12, .85], [(start+end)/2, y, .425], colour)

    def vertical(name, x, start, end, colour=wall):
        box(name, [.12, end-start, .85], [x, (start+end)/2, .425], colour)

    box('floor', [12.2, 10.2, .1], [0, 0, -.05], [.58, .61, .63, 1])
    horizontal('north_wall', 5, -6, 6)
    horizontal('south_wall', -5, -6, 6)
    vertical('west_wall', -6, -5, 5)
    vertical('east_wall', 6, -5, 5)
    # Hallway 1.48 m clear; three northern doors and two southern doors, 1 m clear.
    for i, (start, end) in enumerate([(-6, -4.5), (-3.5, -.5), (.5, 3.5), (4.5, 6)]):
        horizontal('north_hall_'+str(i), .8, start, end, [.27, .43, .59, 1])
    for i, (start, end) in enumerate([(-6, -3.5), (-2.5, 2.5), (3.5, 6)]):
        horizontal('south_hall_'+str(i), -.8, start, end, [.48, .38, .29, 1])
    # Interconnecting doors create loops, rather than five isolated dead ends.
    for x in (-2, 2):
        vertical('north_partition_lower_'+str(x), x, .8, 2.5)
        vertical('north_partition_upper_'+str(x), x, 3.5, 5)
    vertical('south_partition_lower', 0, -5, -3.5)
    vertical('south_partition_upper', 0, -2.5, -.8)

    box('office_cabinet', [.45, 1.5, .65], [-5.65, 3.8, .325], [.15, .31, .47, 1])
    box('studio_cabinet', [1.3, .45, .65], [0, 4.65, .325], [.20, .43, .31, 1])
    box('workshop_cabinet', [1.4, .5, .65], [4.5, 4.6, .325], [.64, .22, .12, 1])
    box('sofa', [1.6, .75, .42], [-4.5, -4.1, .21], [.19, .35, .46, 1])
    box('sofa_back', [1.6, .15, .26], [-4.5, -4.4, .55], [.19, .35, .46, 1])
    box('lounge_low_table', [.8, .6, .25], [-3.8, -2.7, .125], wood)
    for i, (x, y) in enumerate([(2, -4), (3.4, -4.1), (4.8, -3.5), (4.7, -1.8)]):
        box('storage_crate_'+str(i), [.65, .6, .45], [x, y, .225], [.62, .43, .19, 1])
    for name, x, y in [('office_desk', -4.3, 4.1), ('studio_table', .7, 1.9), ('workbench', 4.8, 2.8)]:
        box(name+'_top', [1.2, .7, .08], [x, y, .72], wood)
        for i, (dx, dy) in enumerate([(-.5, -.25), (-.5, .25), (.5, -.25), (.5, .25)]):
            box(name+'_leg_'+str(i), [.08, .08, .68], [x+dx, y+dy, .34], wood)
    return result


def write_reference(package: Path):
    """Draw the same boxes as the world, and check room access with clearance."""
    boxes = objects()
    # A 0.23 m disc conservatively encloses Skala's plan view, including turns.
    # Planar, axis-aligned boxes only; elevated table tops are passable underneath.
    radius, step = .23, .05
    obstacles = [(xyz[0]-size[0]/2-radius, xyz[0]+size[0]/2+radius,
                  xyz[1]-size[1]/2-radius, xyz[1]+size[1]/2+radius)
                 for name, size, xyz, _, _ in boxes
                 if name != 'floor' and xyz[2]-size[2]/2 < .3 and xyz[2]+size[2]/2 > .01]

    def clear(cell):
        x, y = cell[0]*step, cell[1]*step
        return (-6 < x < 6 and -5 < y < 5 and
                not any(lo_x <= x <= hi_x and lo_y <= y <= hi_y for lo_x, hi_x, lo_y, hi_y in obstacles))

    visited, queue = {(0, 0)}, deque([(0, 0)])
    assert clear((0, 0)), 'Spawn is obstructed'
    while queue:
        x, y = queue.popleft()
        for cell in ((x+1, y), (x-1, y), (x, y+1), (x, y-1)):
            if cell not in visited and clear(cell):
                visited.add(cell)
                queue.append(cell)
    reach = {name: (round(x/step), round(y/step)) in visited for name, x, y in ROOMS}
    assert all(reach.values()), f'Room unreachable with robot clearance: {reach}'
    audit = {'status': 'passed', 'clearance_disc_radius_m': radius, 'grid_step_m': step,
             'room_centers_reachable_from_spawn': reach, 'reachable_grid_cells': len(visited),
             'hall_clear_width_m': 1.48, 'door_clear_width_m': 1.0,
             'method': 'Planar box inflation and four-neighbor flood fill; not a dynamic driving test'}
    (package/'worlds/floorplan-access.json').write_text(json.dumps(audit, indent=2)+'\n')
    svg = ['<svg xmlns="http://www.w3.org/2000/svg" width="900" height="800" viewBox="0 0 900 800">',
           '<rect width="900" height="800" fill="#101419"/>',
           '<g font-family="sans-serif" fill="#e8edf2"><text x="40" y="40" font-size="25">Skala • multi-room floorplan</text>',
           '<text x="40" y="68" font-size="15">12 × 10 m · five rooms · connecting loops · 1 m doorways</text></g>',
           '<g transform="translate(450 425) scale(62 -62)">']
    for name, size, xyz, colour, _ in boxes:
        rgb = '#'+''.join(f'{round(v*255):02x}' for v in colour[:3])
        svg.append(f'<rect x="{xyz[0]-size[0]/2}" y="{xyz[1]-size[1]/2}" width="{size[0]}" height="{size[1]}" fill="{rgb}" stroke="#26313a" stroke-width=".015"/>')
    svg += ['<circle cx="0" cy="0" r=".18" fill="#f46f50"/>',
            '<path d="M .25 0 L .85 0 M .62 .14 L .85 0 L .62 -.14" fill="none" stroke="#d45136" stroke-width=".06"/>', '</g>',
            '<g font-family="sans-serif" fill="#18232b" font-size="17" text-anchor="middle">']
    for name, x, y in ROOMS:
        svg.append(f'<text x="{450+x*62}" y="{425-y*62}">{escape(name)}</text>')
    svg += ['<text x="360" y="431">Start →</text></g>',
            '<text x="40" y="765" fill="#a1adba" font-family="sans-serif" font-size="14">Layout reference only. SLAM starts without this floorplan and builds its own map.</text>', '</svg>']
    (package/'web/floorplan.svg').write_text('\n'.join(svg)+'\n')
