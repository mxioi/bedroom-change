"""
Bedroom layout - parametric CAD.

Coordinates are in mm, matching "Room layout.step":
  origin  = front-left floor corner (front wall = wall opposite the window)
  +x      = towards the TV wall (right wall)
  +y      = towards the window wall
  +z      = up

Run:  pip install cadquery matplotlib && python concepts/build_concepts.py
Outputs a STEP file (room + furniture) and PNG renders per concept.
"""
import os
import cadquery as cq
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Arc
from mpl_toolkits.mplot3d.art3d import Poly3DCollection

HERE = os.path.dirname(os.path.abspath(__file__))
ROOM_STEP = os.path.join(HERE, "..", "Room layout.step")

# --------------------------------------------------------------------------
# Room (read from the STEP file; walls are not modelled there, the left wall
# is assumed to be at x=0)
# --------------------------------------------------------------------------
ROOM_W, ROOM_D, ROOM_H = 3404, 3150, 2400

FIXED = {
    # name: (x0, y0, z0, x1, y1, z1)
    "Radiator": (864, 3040, 119, 1981, 3150, 577),
    "Window sill": (452, 3111, 686, 2362, 3150, 724),
    "TV (wall mounted)": (3327, 309, 1359, 3404, 1537, 2045),
    # racks 51W x 58.5D; main one (20U, 98.2 cm) under the TV, a 6U one
    # (same footprint, ~37 cm tall) to its left towards the main door
    "Rack 1 (under TV)": (2819, 668, 0, 3404, 1178, 982),
    "Rack 2 (6U)": (2819, 1178, 0, 3404, 1688, 370),
}

DOORS = {
    # name: (wall, start, end, swings_in)
    "Bathroom door": ("front", 813, 1651, False),   # opens away from bedroom
    "Wardrobe door": ("front", 2591, 3404, True),
    "Main door": ("right", 1892, 2806, True),
}

SHELF_Z = 1500           # top of the existing BERGSHULT shelves (assumed)
WINDOW_X = (521, 2286)   # window recess on the window wall
WINDOW_Z = (724, 2181)


def door_zone(wall, a, b, swings_in):
    """Floor rectangle (x0, y0, x1, y1) that must stay clear for a door."""
    depth = (b - a) if swings_in else 600  # walk-through approach otherwise
    if wall == "front":
        return (a, 0, b, depth)
    if wall == "right":
        return (ROOM_W - depth, a, ROOM_W, b)
    raise ValueError(wall)


# --------------------------------------------------------------------------
# Furniture catalogue  (W along its own x, D along its own y, H)
# --------------------------------------------------------------------------
CAT = {
    "HEMNES double bed": (1490, 2010, 1270),       # given by you
    "TRAVSPORT desk 120x70 (sit/stand 72-117cm)": (1200, 700, 720),
    "MITTZON laptop table w/ castors 66x50": (660, 500, 720),
    "TONSTAD bookcase 81x37x201": (810, 370, 2010),
    "BILLY bookcase 80x28x202": (800, 280, 2020),
    "BILLY bookcase 40x28x202": (400, 280, 2020),
    "GERSBY bookcase 60x24x180": (600, 240, 1800),
    "BROR wall shelf combo 88x30x90": (880, 300, 900),
    "BROR pegboard": (1000, 20, 600),
    "Rail + hanging bins": (800, 120, 450),
    "Bedside": (400, 400, 500),
}

COLORS = {
    "bed": "#b5835a", "mattress": "#f2efe8", "desk": "#d2b48c",
    "books": "#e07a8f", "tech": "#4a7bd0", "fixed": "#8a8f98",
    "tv": "#222222", "zone": "#f5c542", "boxes": "#9ccc65", "chair": "#666666",
    "neutral": "#c9c3b8",
}


class Item:
    def __init__(self, name, x0, y0, z0, x1, y1, z1, color, owner="", label=True,
                 solid=True):
        self.name, self.color, self.owner = name, color, owner
        self.b = (x0, y0, z0, x1, y1, z1)
        self.label, self.solid = label, solid

    @property
    def fp(self):
        x0, y0, _, x1, y1, _ = self.b
        return (x0, y0, x1, y1)


def box(name, x, y, w, d, h, color, z=0, owner="", **kw):
    return Item(name, x, y, z, x + w, y + d, z + h, color, owner, **kw)


def bed(x, y, headboard, prefix=""):
    """HEMNES bed. headboard: 'left' (on x=0 wall) or 'window' (on y=ROOM_D side)."""
    L, W = 2010, 1490
    items = []
    if headboard == "left":
        items += [
            box("HEMNES bed", x, y, L, W, 400, COLORS["bed"]),
            box("mattress", x + 50, y + 20, L - 100, W - 40, 220, COLORS["mattress"], z=400, label=False),
            box("headboard", x, y, 50, W, 1270, COLORS["bed"], label=False),
            box("footboard", x + L - 50, y, 50, W, 660, COLORS["bed"], label=False),
        ]
    else:  # window
        items += [
            box("HEMNES bed", x, y, W, L, 400, COLORS["bed"]),
            box("mattress", x + 20, y + 50, W - 40, L - 100, 220, COLORS["mattress"], z=400, label=False),
            box("headboard", x, y + L - 50, W, 50, 1270, COLORS["bed"], label=False),
            box("footboard", x, y, W, 50, 660, COLORS["bed"], label=False),
        ]
    return items


def mittzon(x, y, label="DESK: MITTZON sit/stand 66x50 (72-116 cm)", top_z=740):
    """IKEA MITTZON laptop table with castors: 660 x 500 top, gas-spring
    column, castor base. (x, y) = front-left corner of the tabletop."""
    W, D = 660, 500
    c = COLORS["desk"]
    it = [
        box(label, x, y, W, D, 25, c, z=top_z - 25, owner="tech"),
        box("desk column", x + W / 2 - 40, y + D / 2 - 40, 80, 80, top_z - 85, "#9a9a9a", z=60, label=False),
        box("desk base", x + 40, y + D / 2 - 30, W - 80, 60, 40, "#555555", z=20, label=False),
        box("desk feet", x + 40, y + 15, 60, D - 30, 40, "#555555", z=20, label=False),
        box("desk feet", x + W - 100, y + 15, 60, D - 30, 40, "#555555", z=20, label=False),
    ]
    for cx, cy in ((x + 50, y + 15), (x + 50, y + D - 55), (x + W - 90, y + 15), (x + W - 90, y + D - 55)):
        it.append(box("castor", cx, cy, 40, 40, 20, "#333333", label=False))
    return it


def chair(cx, cy, facing):
    """Simple desk chair centred at (cx, cy). facing: direction the person
    looks ('-y' = towards front wall, '-x' = towards left wall)."""
    s, c = 460, COLORS["chair"]
    it = [
        box("chair seat", cx - s / 2, cy - s / 2, s, s, 60, c, z=440, label=False),
        box("chair column", cx - 30, cy - 30, 60, 60, 400, "#999999", z=40, label=False),
        box("chair base", cx - 300, cy - 300, 600, 600, 40, "#444444", label=False),
    ]
    if facing == "-y":
        it.append(box("chair back", cx - s / 2, cy + s / 2 - 50, s, 50, 450, c, z=500, label=False))
    else:
        it.append(box("chair back", cx + s / 2 - 50, cy - s / 2, 50, s, 450, c, z=500, label=False))
    return it


# --------------------------------------------------------------------------
# CONCEPTS
# --------------------------------------------------------------------------
def concept_D():
    """Final layout: bed faces the TV, desk by the window, BILLY with drawer
    in the main-door corner and LILLBERGET in the bathroom-door corner."""
    it = []
    it += bed(0, 900, "left")                   # bed: x 0-2010, y 900-2390
    it.append(box("Under-bed box pull-out zone", 100, 2390, 1860, 640, 5, COLORS["boxes"], solid=False))
    # desk by the window, 30 mm off the left wall so the top clears the
    # pegboard, centred under it (y 2420-2920)
    it += mittzon(30, 2420, label="DESK: MITTZON (rolls aside for boxes)")
    it.append(box("chair zone", 690, 2400, 600, 630, 5, COLORS["chair"], solid=False, label=False))
    it += chair(990, 2690, "-x")
    # existing BERGSHULT shelves (120x20) at each end of the headboard wall.
    # Height assumed: top at 1500 mm, i.e. above the 1270 headboard.
    for y0 in (0, ROOM_D - 1200):
        it.append(box("BERGSHULT shelf 120x20 (existing)", 0, y0, 200, 1200, 25, COLORS["neutral"], z=SHELF_Z - 25))
    # desk shelf brackets 640 apart; the 600x600 pegboard fits between them,
    # right under the shelf, so the two don't clash
    for yb in (2320, 2980):
        it.append(box("bracket", 0, yb - 10, 190, 20, 180, "#bbbbbb", z=SHELF_Z - 205, label=False))
    it.append(box("BROR pegboard (desk)", 0, 2370, 20, 600, 600, COLORS["tech"], z=SHELF_Z - 640, owner="tech"))
    # main-door corner: BILLY with drawer, pegboard + bins above it.
    # Pegboard and bins were inside the window wall -> on the wall face,
    # and raised so they sit above the 106 cm BILLY
    it.append(box("BILLY w/ drawer 80x30x106", 2390, 2850, 800, 300, 1060, COLORS["tech"], owner="tech"))
    it.append(box("BROR pegboard (door)", 2390, 3130, 800, 20, 600, COLORS["tech"], z=1100, owner="tech"))
    it.append(box("Rail + bins (cables/solder)", 2490, 3030, 600, 120, 450, COLORS["tech"], z=1720, owner="tech"))
    # bathroom-door corner
    it.append(box("LILLBERGET 5 drawers 70x43x108", 0, 0, 700, 430, 1080, COLORS["neutral"]))
    it.append(box("drawers open", 0, 430, 700, 400, 5, COLORS["neutral"], solid=False, label=False))
    # books & display
    it.append(box("TONSTAD 81x37", 1720, 0, 810, 370, 2010, COLORS["books"], owner="books"))
    return it


CONCEPTS = {
    "D": ("Final layout", concept_D),
}


# --------------------------------------------------------------------------
# Clearance checks
# --------------------------------------------------------------------------
def overlap(a, b):
    return min(a[2], b[2]) - max(a[0], b[0]) > 1 and min(a[3], b[3]) - max(a[1], b[1]) > 1


def check(items):
    issues = []
    floor = [i for i in items if i.b[2] < 300 and i.solid]   # floor-standing
    keep_clear = [(n, door_zone(*d)) for n, d in DOORS.items()]
    keep_clear += [(n, (f[0], f[1], f[3], f[4])) for n, f in FIXED.items()
                   if n.startswith("Rack") or n == "Radiator"]
    zones = [i for i in items if not i.solid]
    for i in floor:
        if i.name in ("HEMNES bed",) or i.solid:
            for n, z in keep_clear:
                if overlap(i.fp, z):
                    issues.append(f"{i.name} overlaps {n}")
    for z in zones:
        if "pull-out" in z.name:
            for i in floor:
                if i.name not in ("HEMNES bed", "headboard", "footboard") and overlap(z.fp, i.fp):
                    who = "desk + chair (on castors - roll aside)" if any(k in i.name for k in ("desk", "castor", "chair", "DESK")) else i.name
                    issues.append(f"Under-bed boxes blocked by {who}")
        if "chair" in z.name:
            depth = min(z.b[3] - z.b[0], z.b[4] - z.b[1])
            if depth < 550:
                issues.append(f"Only {depth:.0f} mm to sit at the desk - tight seated, fine standing")
            for n, k in keep_clear:
                if overlap(z.fp, k):
                    issues.append(f"Desk chair (when pulled out) sits in {n} approach")
    # radiator gap
    for i in floor:
        if i.name == "HEMNES bed":
            gap = FIXED["Radiator"][1] - i.b[4]
            if gap < 80 and overlap(i.fp, (864, 0, 1981, 3150)):
                issues.append(f"Bed only {gap:.0f} mm from radiator (blocks heat)")
    for i in items:
        if i.solid and (i.b[3] > ROOM_W + 1 or i.b[4] > ROOM_D + 1 or i.b[0] < -1 or i.b[1] < -1):
            issues.append(f"{i.name} outside room")
    return sorted(set(issues))


# --------------------------------------------------------------------------
# Rendering
# --------------------------------------------------------------------------
def draw_plan(ax, items, title):
    ax.set_title(title, fontsize=12, weight="bold")
    ax.add_patch(Rectangle((0, 0), ROOM_W, ROOM_D, fill=False, lw=3, ec="k"))
    # window
    ax.plot(WINDOW_X, [ROOM_D, ROOM_D], color="#5ab0e8", lw=6, solid_capstyle="butt")
    ax.text(sum(WINDOW_X) / 2, ROOM_D + 60, "WINDOW", ha="center", fontsize=7, color="#2a7ab8")
    # doors
    for n, (wall, a, b, sw) in DOORS.items():
        z = door_zone(wall, a, b, sw)
        ax.add_patch(Rectangle((z[0], z[1]), z[2] - z[0], z[3] - z[1], fc=COLORS["zone"],
                               alpha=0.18, ec=COLORS["zone"], hatch="//", lw=0.5))
        if wall == "front":
            ax.plot([a, b], [0, 0], color="white", lw=5)
            if sw:
                ax.add_patch(Arc((b, 0), 2 * (b - a), 2 * (b - a), theta1=90, theta2=180, ls="--", lw=0.8))
            ax.text((a + b) / 2, -110, n, ha="center", fontsize=7)
        else:
            ax.plot([ROOM_W, ROOM_W], [a, b], color="white", lw=5)
            ax.add_patch(Arc((ROOM_W, b), 2 * (b - a), 2 * (b - a), theta1=180, theta2=270, ls="--", lw=0.8))
            ax.text(ROOM_W + 60, (a + b) / 2, n, rotation=90, va="center", fontsize=7)
    for n, f in FIXED.items():
        c = COLORS["tv"] if n.startswith("TV") else COLORS["fixed"]
        ax.add_patch(Rectangle((f[0], f[1]), f[3] - f[0], f[4] - f[1], fc=c, alpha=0.8, ec="k", lw=0.5))
        if n.startswith("Rack") or n == "Radiator":
            ax.text((f[0] + f[3]) / 2, (f[1] + f[4]) / 2, n.replace(" (under TV)", ""),
                    ha="center", va="center", fontsize=6, color="white")
    ax.text(ROOM_W - 30, 1537 + 20, "TV", fontsize=7, ha="right", color="k")
    for i in sorted(items, key=lambda i: i.b[2]):
        x0, y0, x1, y1 = i.fp
        if not i.solid:
            ax.add_patch(Rectangle((x0, y0), x1 - x0, y1 - y0, fc=i.color, alpha=0.25,
                                   ec=i.color, ls="--", lw=1))
            if i.label:
                ax.text((x0 + x1) / 2, (y0 + y1) / 2, i.name, ha="center", va="center",
                        fontsize=6, style="italic", rotation=90 if (y1 - y0) > 2 * (x1 - x0) else 0)
            continue
        wall_mounted = i.b[2] >= 900
        if i.name.startswith("chair") and i.name != "chair seat":
            continue
        is_desk = i.name.startswith("DESK")
        if i.name == "chair seat":
            ax.add_patch(Rectangle((x0, y0), x1 - x0, y1 - y0, fc=i.color, ec="k", lw=0.8, alpha=0.8))
            ax.text((x0 + x1) / 2, (y0 + y1) / 2, "chair", ha="center", va="center", fontsize=7, color="white")
            continue
        if is_desk:
            ax.add_patch(Rectangle((x0, y0), x1 - x0, y1 - y0, fc=i.color, ec="#7a4b00", lw=2.5, zorder=5))
            ax.text((x0 + x1) / 2, (y0 + y1) / 2, i.name.replace(": ", "\n").replace(" (", "\n("),
                    ha="center", va="center", fontsize=6.5, weight="bold", zorder=6)
            continue
        ax.add_patch(Rectangle((x0, y0), x1 - x0, y1 - y0, fc=i.color, ec="k", lw=0.6,
                               alpha=0.45 if wall_mounted else 0.9,
                               ls=":" if wall_mounted else "-"))
        if i.label:
            rot = 90 if (y1 - y0) > 1.6 * (x1 - x0) else 0
            txt = i.name + (" (on wall)" if wall_mounted else "")
            ax.text((x0 + x1) / 2, (y0 + y1) / 2, txt, ha="center", va="center", fontsize=6.5,
                    rotation=rot, weight="bold" if i.name == "HEMNES bed" else "normal")
    ax.set_xlim(-250, ROOM_W + 250)
    ax.set_ylim(-250, ROOM_D + 200)
    ax.set_aspect("equal")
    ax.set_xticks(range(0, ROOM_W + 1, 500))
    ax.set_yticks(range(0, ROOM_D + 1, 500))
    ax.tick_params(labelsize=6)
    ax.grid(alpha=0.2)


def draw_dims(ax, items, title):
    """Plan with wall-to-object distances (mm) for measuring up."""
    ax.set_title(title, fontsize=12, weight="bold")
    W, D = ROOM_W, ROOM_D
    ax.add_patch(Rectangle((-WALL_T, -WALL_T), W + 2 * WALL_T, D + WALL_T + WINDOW_WALL_T, fc="#d9d4ca", ec="k"))
    ax.add_patch(Rectangle((0, 0), W, D, fc="white", ec="k", lw=1.5))
    ax.plot(WINDOW_X, [D, D], color="#5ab0e8", lw=6, solid_capstyle="butt")
    for n, (wall, a, b, _) in DOORS.items():
        if wall == "front":
            ax.plot([a, b], [0, 0], color="white", lw=6)
            ax.text((a + b) / 2, -60, n, ha="center", va="top", fontsize=6)
        else:
            ax.plot([W, W], [a, b], color="white", lw=6)
            ax.text(W + 60, (a + b) / 2, n, rotation=90, va="center", fontsize=6)

    def dim(p0, p1, txt, off=(0, 0), color="#c0392b", fs=6.5):
        ax.annotate("", xy=p1, xytext=p0, arrowprops=dict(arrowstyle="<->", color=color, lw=0.8))
        ax.text((p0[0] + p1[0]) / 2 + off[0], (p0[1] + p1[1]) / 2 + off[1], txt, fontsize=fs, color=color,
                ha="center", va="center", bbox=dict(fc="white", ec="none", pad=0.4, alpha=0.85))

    # overall room + openings along the walls
    dim((0, -330), (W, -330), f"{W}", color="k", fs=7.5)
    dim((-330, 0), (-330, D), f"{D}", color="k", fs=7.5)
    for x0, x1, lab in ((0, 813, ""), (813, 1651, ""), (1651, 2591, ""), (2591, W, "")):
        dim((x0, -200), (x1, -200), f"{x1 - x0}", color="#555", fs=6)
    for y0, y1 in ((0, 1892), (1892, 2806), (2806, D)):
        dim((W + 230, y0), (W + 230, y1), f"{y1 - y0}", color="#555", fs=6)
    for x0, x1 in ((0, WINDOW_X[0]), WINDOW_X, (WINDOW_X[1], W)):
        dim((x0, D + 230), (x1, D + 230), f"{x1 - x0}", color="#2a7ab8", fs=6)

    fixed = [Item(n, *f, COLORS["tv"] if n.startswith("TV") else COLORS["fixed"])
             for n, f in FIXED.items() if not n.startswith("Window")]
    show = [i for i in items if i.solid and (i.label or i.name == "HEMNES bed")]
    wall_items = []
    for i in fixed + show:
        x0, y0, x1, y1 = i.fp
        wall_mounted = i.b[2] >= 900
        ax.add_patch(Rectangle((x0, y0), x1 - x0, y1 - y0, fc=i.color, ec="k", lw=0.6,
                               alpha=0.35 if wall_mounted else 0.75, ls=":" if wall_mounted else "-"))
        nm = i.name.split(" (")[0].replace("DESK: ", "") if not i.name.startswith("BROR") else i.name
        if wall_mounted:
            wall_items.append(i)
            ax.text((x0 + x1) / 2, (y0 + y1) / 2, f"W{len(wall_items)}", fontsize=6, weight="bold",
                    ha="center", va="center", color="#1d3f7a")
            continue
        ax.text((x0 + x1) / 2, (y0 + y1) / 2, f"{nm}\n{x1 - x0:.0f}x{y1 - y0:.0f}",
                ha="center", va="center", fontsize=5.5, rotation=90 if (y1 - y0) > 1.6 * (x1 - x0) else 0)

    floor = [i for i in fixed + show if i.b[2] < 900 and not i.name.startswith(("TV", "Radiator"))]

    def blocked(a, b, axis, lo, hi):
        # any floor item strictly between a and b along axis within the shared band
        for o in floor:
            if o in (a, b):
                continue
            if axis == "x" and o.fp[0] >= lo - 1 and o.fp[2] <= hi + 1:
                return True
            if axis == "y" and o.fp[1] >= lo - 1 and o.fp[3] <= hi + 1:
                return True
        return False

    # wall gaps (only where nothing sits between the object and the wall)
    for i in floor:
        x0, y0, x1, y1 = i.fp
        cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
        for g, a, b, ax_ in ((x0, 0, x0, "x"), (W - x1, x1, W, "x"), (y0, 0, y0, "y"), (D - y1, y1, D, "y")):
            if not 5 < g < 1300:
                continue
            band = [o for o in floor if o is not i and (
                (ax_ == "x" and o.fp[1] < y1 and o.fp[3] > y0 and o.fp[0] >= a - 1 and o.fp[2] <= b + 1) or
                (ax_ == "y" and o.fp[0] < x1 and o.fp[2] > x0 and o.fp[1] >= a - 1 and o.fp[3] <= b + 1))]
            if band:
                continue
            if ax_ == "x":
                dim((a, cy), (b, cy), f"{g:.0f}")
            else:
                dim((cx, a), (cx, b), f"{g:.0f}")
    # object-to-object gaps (blue)
    for a in floor:
        for b in floor:
            if a is b:
                continue
            ylo, yhi = max(a.fp[1], b.fp[1]), min(a.fp[3], b.fp[3])
            xlo, xhi = max(a.fp[0], b.fp[0]), min(a.fp[2], b.fp[2])
            if yhi - ylo > 50 and b.fp[0] - a.fp[2] > 5:
                g = b.fp[0] - a.fp[2]
                if g < 1300:
                    y = (ylo + yhi) / 2
                    dim((a.fp[2], y), (b.fp[0], y), f"{g:.0f}", color="#1f6fbf")
            if xhi - xlo > 50 and b.fp[1] - a.fp[3] > 5:
                g = b.fp[1] - a.fp[3]
                if g < 1300:
                    x = (xlo + xhi) / 2
                    dim((x, a.fp[3]), (x, b.fp[1]), f"{g:.0f}", color="#1f6fbf")
    # legend of wall-mounted items
    wall_of = lambda i: ("left wall" if i.fp[0] < 5 else "right wall" if i.fp[2] > W - 5
                         else "front wall" if i.fp[1] < 5 else "window wall" if i.fp[3] > D - 5 else "")
    lines = ["Wall-mounted (dotted):"] + [
        f"W{k + 1}  {i.name}: {max(i.fp[2] - i.fp[0], i.fp[3] - i.fp[1]):.0f} wide, "
        f"{i.b[2]:.0f}-{i.b[5]:.0f} mm off floor, {wall_of(i)}" for k, i in enumerate(wall_items)]
    ax.text(-430, -560, "\n".join(lines), fontsize=6.5, va="top", family="monospace")
    ax.set_xlim(-450, W + 400)
    ax.set_ylim(-1150, D + 400)
    ax.set_aspect("equal")
    ax.set_xticks([]); ax.set_yticks([])
    ax.text(-430, D + 360, "Red = object to wall, blue = object to object (touching not shown).  "
            "Dotted = wall-mounted.  Walls assumed 100 mm thick, ceiling 2400.", fontsize=6.5, va="top")


def cuboid_faces(b):
    x0, y0, z0, x1, y1, z1 = b
    P = [(x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0),
         (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)]
    F = [(0, 1, 2, 3), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]
    return [[P[k] for k in f] for f in F]


def draw_3d(ax, items, title, elev=38, azim=-58):
    ax.set_title(title, fontsize=11, weight="bold")
    # floor + two back walls (left + window) for context
    ax.add_collection3d(Poly3DCollection([[(0, 0, 0), (ROOM_W, 0, 0), (ROOM_W, ROOM_D, 0), (0, ROOM_D, 0)]],
                                         fc="#e9e4da", ec="none", alpha=0.6))
    walls = [[(0, 0, 0), (0, ROOM_D, 0), (0, ROOM_D, ROOM_H), (0, 0, ROOM_H)],
             [(0, ROOM_D, 0), (ROOM_W, ROOM_D, 0), (ROOM_W, ROOM_D, ROOM_H), (0, ROOM_D, ROOM_H)]]
    ax.add_collection3d(Poly3DCollection(walls, fc="#f7f5f0", ec="#bbb", alpha=0.35))
    ax.add_collection3d(Poly3DCollection(
        [[(WINDOW_X[0], ROOM_D - 1, WINDOW_Z[0]), (WINDOW_X[1], ROOM_D - 1, WINDOW_Z[0]),
          (WINDOW_X[1], ROOM_D - 1, WINDOW_Z[1]), (WINDOW_X[0], ROOM_D - 1, WINDOW_Z[1])]],
        fc="#9fd3f5", ec="#5ab0e8", alpha=0.7))
    allb = [(f, COLORS["tv"] if n.startswith("TV") else COLORS["fixed"]) for n, f in FIXED.items()
            if not n.startswith("Rack")]
    for n, f in FIXED.items():
        if n.startswith("Rack"):
            allb += [(b, c) for _, b, c in rack_parts(f, n)]
    allb += [(i.b, i.color) for i in items if i.solid]
    for b, c in allb:
        ax.add_collection3d(Poly3DCollection(cuboid_faces(b), fc=c, ec="#333", lw=0.3, alpha=0.95))
    for i in items:
        if not i.solid:
            x0, y0, x1, y1 = i.fp
            ax.add_collection3d(Poly3DCollection([[(x0, y0, 2), (x1, y0, 2), (x1, y1, 2), (x0, y1, 2)]],
                                                 fc=i.color, alpha=0.35, ec=i.color))
    ax.set_xlim(0, ROOM_W); ax.set_ylim(0, ROOM_D); ax.set_zlim(0, ROOM_H)
    ax.set_box_aspect((ROOM_W, ROOM_D, ROOM_H))
    ax.view_init(elev=elev, azim=azim)
    ax.set_axis_off()


WALL_T = 100           # assumed wall thickness for the measuring walls
WINDOW_WALL_T = 140    # window reveal in the original model is ~137 deep


def rack_parts(f, name):
    """Open-frame rack, 51W x 58.5D: 4 posts, top and bottom frames and a
    block of kit every ~300 mm. f = (x0, y0, z0, x1, y1, z1)."""
    x0, y0, z0, x1, y1, z1 = f
    p, c, k = 30, "#3a3d42", "#5d6168"
    parts = [(name + "_post", (x, y, z0, x + p, y + p, z1), c)
             for x in (x0, x1 - p) for y in (y0, y1 - p)]
    parts.append((name + "_base", (x0, y0, z0 + 30, x1, y1, z0 + 55), c))
    parts.append((name + "_top", (x0, y0, z1 - 25, x1, y1, z1), c))
    z = z0 + 75
    while z + 150 < z1 - 30:
        top = min(z + 220, z1 - 40)
        parts.append((name + "_kit", (x0 + 40, y0 + 40, z, x1 - 40, y1 - 40, top), k))
        if top + 25 < z1 - 30:
            parts.append((name + "_shelf", (x0, y0, top + 5, x1, y1, top + 30), c))
        z = top + 50
    return parts


def walls_solids():
    """Walls around the room interior (x 0..ROOM_W, y 0..ROOM_D, z 0..ROOM_H)
    with the door and window openings cut, plus a floor slab - one solid per
    wall so they can be hidden separately."""
    T, TW = WALL_T, WINDOW_WALL_T
    B = lambda x0, y0, z0, x1, y1, z1: cq.Workplane("XY").box(
        x1 - x0, y1 - y0, z1 - z0, centered=False).translate((x0, y0, z0))
    w = {
        "left": B(-T, -T, 0, 0, ROOM_D + TW, ROOM_H),
        "front": B(0, -T, 0, ROOM_W + T, 0, ROOM_H),
        "right": B(ROOM_W, 0, 0, ROOM_W + T, ROOM_D + TW, ROOM_H),
        "window": B(0, ROOM_D, 0, ROOM_W, ROOM_D + TW, ROOM_H),
        "floor": B(-T, -T, -20, ROOM_W + T, ROOM_D + TW, 0),
    }
    for n, (wall, a, b, _) in DOORS.items():
        if wall == "front":
            w["front"] = w["front"].cut(B(a, -T - 1, 0, b, 1, 2032))
        else:
            w["right"] = w["right"].cut(B(ROOM_W - 1, a, 0, ROOM_W + T + 1, b, 2032))
    w["window"] = w["window"].cut(B(WINDOW_X[0], ROOM_D - 1, WINDOW_Z[0], WINDOW_X[1], ROOM_D + TW + 1, WINDOW_Z[1]))
    return w


def export_step(items, path):
    asm = build_assembly(items)
    asm.save(path)
    return asm


def build_assembly(items):
    asm = cq.Assembly(name="bedroom")
    room = cq.importers.importStep(ROOM_STEP)
    asm.add(room, name="existing_room", color=cq.Color(0.55, 0.56, 0.6))
    for wn, ws in walls_solids().items():
        col = cq.Color(0.80, 0.78, 0.74) if wn == "floor" else cq.Color(0.93, 0.92, 0.88, 0.35)
        asm.add(ws, name=f"room_walls_{wn}", color=col)
    for n, f in FIXED.items():
        if n.startswith("Rack"):
            for k, (pn, b, col) in enumerate(rack_parts(f, n.split(" (")[0].replace(" ", "_"))):
                x0, y0, z0, x1, y1, z1 = b
                h = col.lstrip("#")
                asm.add(cq.Workplane("XY").box(x1 - x0, y1 - y0, z1 - z0, centered=False).translate((x0, y0, z0)),
                        name=f"{pn}_{k}", color=cq.Color(*(int(h[j:j + 2], 16) / 255 for j in (0, 2, 4))))
    for k, i in enumerate(items):
        if not i.solid:
            continue
        x0, y0, z0, x1, y1, z1 = i.b
        solid = cq.Workplane("XY").box(x1 - x0, y1 - y0, z1 - z0, centered=False).translate((x0, y0, z0))
        h = i.color.lstrip("#")
        rgb = tuple(int(h[j:j + 2], 16) / 255 for j in (0, 2, 4))
        safe = "".join(ch if ch.isalnum() else "_" for ch in i.name)
        asm.add(solid, name=f"{k:02d}_{safe}", color=cq.Color(*rgb))
    return asm


NOTES = {
    "D": ["Bed faces the TV; MITTZON by the window under the existing BERGSHULT shelf, "
          "with the BROR pegboard fitted between the shelf brackets.",
          "Main-door corner: BILLY with drawer (80x30x106), pegboard and bins above it. Bathroom-door corner: "
          "LILLBERGET 5 drawers (470 mm to the bed - enough to open the drawers).",
          "Racks: 20U under the TV, 6U beside it. BERGSHULT shelf height is assumed (top at 1500 mm)."],
}


def export_viewer(summary):
    """Copy models, images and STEP files into viewer/ for GitHub Pages."""
    import json, shutil
    vdir = os.path.join(HERE, "..", "viewer")
    for sub in ("models", "img", "step"):
        os.makedirs(os.path.join(vdir, sub), exist_ok=True)
    data = {}
    for key, (title, _) in CONCEPTS.items():
        for src, sub in ((f"concept_{key}.glb", "models"), (f"concept_{key}.png", "img"),
                         (f"concept_{key}_dimensions.png", "img"), (f"concept_{key}.step", "step")):
            shutil.copy(os.path.join(HERE, src), os.path.join(vdir, sub, src))
        data[key] = {"title": title, "glb": f"models/concept_{key}.glb", "plan": f"img/concept_{key}.png",
                     "dims": f"img/concept_{key}_dimensions.png", "step": f"step/concept_{key}.step",
                     "notes": NOTES.get(key, []), "checks": summary[key]}
    with open(os.path.join(vdir, "concepts.json"), "w") as f:
        json.dump(data, f, indent=2)


def main():
    out = HERE
    summary = {}
    for key, (title, fn) in CONCEPTS.items():
        items = fn()
        issues = check(items)
        summary[key] = issues
        fig = plt.figure(figsize=(15, 7.2))
        ax1 = fig.add_subplot(1, 2, 1)
        draw_plan(ax1, items, f"Concept {key}: {title} - plan (mm)")
        ax2 = fig.add_subplot(1, 2, 2, projection="3d")
        draw_3d(ax2, items, "3D view (from front-right, main door side)")
        txt = "Checks: " + ("all clear" if not issues else "; ".join(issues))
        fig.text(0.02, 0.02, txt, fontsize=9, color="green" if not issues else "#b00020", wrap=True)
        fig.text(0.02, 0.955, "Pink = books & display   Blue = tech storage   Grey = fixed (TV, racks, radiator)   "
                 "Yellow hatch = door clearance   Green = under-bed box pull-out", fontsize=8)
        fig.tight_layout(rect=(0, 0.04, 1, 0.95))
        fig.savefig(os.path.join(out, f"concept_{key}.png"), dpi=130)
        plt.close(fig)
        fig = plt.figure(figsize=(10, 11.5))
        draw_dims(fig.add_subplot(1, 1, 1), items, f"Concept {key}: {title} - measurements (mm)")
        fig.tight_layout()
        fig.savefig(os.path.join(out, f"concept_{key}_dimensions.png"), dpi=140)
        plt.close(fig)
        asm = export_step(fn(), os.path.join(out, f"concept_{key}.step"))
        asm.save(os.path.join(out, f"concept_{key}.glb"), tolerance=0.5, angularTolerance=0.3)
        print(key, title, "->", issues or "all clear")
    export_viewer(summary)
    return summary


if __name__ == "__main__":
    main()
