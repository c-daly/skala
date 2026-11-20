"""Print plate of ICT-01 links: 80 if they fit on the bed, otherwise 40.

    uv run python cad/plate_ict01.py          # tries 80, then 40
    uv run python cad/plate_ict01.py 60       # tries 60 only

Tessellates one link (parts/ict01_link.py) and copies the mesh, so the plate STL is
N x one link rather than one huge B-rep. Layout: a grid of links in print orientation,
then a strip of links turned 90 deg in whatever bed is left over. Writes
cad/out/stl/ict01_plate_<n>.stl.
"""
import sys, pathlib, tempfile
HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import numpy as np
from build123d import export_stl
import params as P
from parts.ict01_link import link

GAP = 1.5                 # between links
TRY = (80, 40)


def read_stl(path):
    data = path.read_bytes()
    n = int(np.frombuffer(data, np.uint32, 1, 80)[0])
    rec = np.frombuffer(data, np.dtype([("n", "<f4", 3), ("v", "<f4", (3, 3)), ("a", "<u2")]), n, 84)
    return rec["v"].astype(np.float64)


def write_stl(path, tris):
    rec = np.zeros(len(tris), np.dtype([("n", "<f4", 3), ("v", "<f4", (3, 3)), ("a", "<u2")]))
    e1, e2 = tris[:, 1] - tris[:, 0], tris[:, 2] - tris[:, 0]
    nrm = np.cross(e1, e2)
    nrm /= np.maximum(np.linalg.norm(nrm, axis=1, keepdims=True), 1e-12)
    rec["n"], rec["v"] = nrm, tris
    with open(path, "wb") as f:
        f.write(b"ict01 plate".ljust(80, b" "))
        f.write(np.uint32(len(tris)).tobytes())
        f.write(rec.tobytes())


def layout(w, h, n, limit=P.MAX_PART, gap=GAP):
    """Centres and rotations for n links of footprint w x h (X x Y), or None if they don't fit."""
    fit = lambda size, span=limit: int((span + gap) // (size + gap))
    cols, rows = fit(w), fit(h)
    spots = [(i * (w + gap) + w / 2, j * (h + gap) + h / 2, 0)
             for j in range(rows) for i in range(cols)]
    # turned links (h along X, w along Y) in the strip above the grid
    y0 = rows * (h + gap)
    if limit - y0 >= w:
        tcols, trows = fit(h), fit(w, limit - y0)
        spots += [(i * (h + gap) + h / 2, y0 + j * (w + gap) + w / 2, 90)
                  for j in range(trows) for i in range(tcols)]
    if len(spots) < n:
        return None
    spots = spots[:n]
    xs = [x for x, _, _ in spots]; ys = [y for _, y, _ in spots]
    cx, cy = (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2
    return [(x - cx, y - cy, r) for x, y, r in spots]


def main():
    counts = [int(a) for a in sys.argv[1:]] or TRY
    one = link()
    with tempfile.TemporaryDirectory() as d:
        tmp = pathlib.Path(d) / "link.stl"
        export_stl(one, str(tmp), tolerance=0.02, angular_tolerance=0.1)
        tris = read_stl(tmp)
    lo, hi = tris.reshape(-1, 3).min(0), tris.reshape(-1, 3).max(0)
    tris -= [(lo[0] + hi[0]) / 2, (lo[1] + hi[1]) / 2, lo[2]]
    w, h = hi[0] - lo[0], hi[1] - lo[1]
    for n in counts:
        spots = layout(w, h, n)
        if spots is None:
            print(f"{n} links: do not fit in {P.MAX_PART:.0f} x {P.MAX_PART:.0f} mm")
            continue
        rot = {0: np.eye(3), 90: np.array([[0, -1, 0], [1, 0, 0], [0, 0, 1]], float)}
        plate = np.concatenate([tris @ rot[r].T + [x, y, 0] for x, y, r in spots])
        pts = plate.reshape(-1, 3); size = pts.max(0) - pts.min(0)
        out = HERE / "out" / "stl" / f"ict01_plate_{n}.stl"
        write_stl(out, plate)
        print(f"{n} links: {size[0]:.1f} x {size[1]:.1f} x {size[2]:.1f} mm -> {out.relative_to(HERE.parent)}")
        return
    sys.exit("nothing fits; lower the count or GAP")


if __name__ == "__main__":
    main()
