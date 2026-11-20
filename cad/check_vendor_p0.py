"""Check purchased-part dimensions against the retained source geometry.

The wheel STL has separate tyre/sprocket components. Never infer caterpillar
pitch from the tyre diameter or a firmware rolling-radius constant.
"""
from pathlib import Path
import math
import numpy as np
from build123d import import_step
from OCP.BRepAdaptor import BRepAdaptor_Surface
from OCP.GeomAbs import GeomAbs_Cylinder
import params as P

HERE = Path(__file__).parent


def wheel_components():
    """Read the retained binary STL; return vertices, faces and connected labels."""
    data = (HERE / 'vendor/robotis/tb3_left_tire.stl').read_bytes()
    count = int.from_bytes(data[80:84], 'little')
    dtype = np.dtype([('normal', '<f4', 3), ('vertices', '<f4', (3,3)), ('attribute', '<u2')])
    assert len(data) == 84 + count*50
    triangles = np.frombuffer(data, dtype, count, 84)['vertices'].astype(float)
    vertices, inverse = np.unique(triangles.reshape(-1,3), axis=0, return_inverse=True)
    faces = inverse.reshape(-1,3)
    parent = list(range(len(vertices)))
    def root(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i
    for a,b,c in faces:
        ra,rb,rc = root(a), root(b), root(c)
        parent[rb] = ra
        parent[rc] = ra
    labels = np.array([root(i) for i in range(len(vertices))])
    components = sorted(set(labels), key=lambda k: np.ptp(vertices[labels == k,0]))
    assert len(components) == 2, 'expected separate bare sprocket and tyre'
    return vertices, faces, labels, components


def main():
    link = import_step(str(HERE / 'vendor/robotis/ict01_caterpillar.step'))
    assert link.is_valid and len(link.solids()) == 1
    axes = set()
    for face in link.faces():
        adaptor = BRepAdaptor_Surface(face.wrapped)
        if adaptor.GetType() == GeomAbs_Cylinder:
            cylinder = adaptor.Cylinder()
            if abs(cylinder.Axis().Direction().Z()) > .99:
                point = cylinder.Axis().Location()
                axes.add((round(cylinder.Radius(), 2), round(point.X(), 2), round(point.Y(), 2)))
    assert (2.0, 0.0, 0.0) in axes and (2.05, P.ICT01_PITCH, 0.0) in axes, axes
    assert abs(link.bounding_box().size.Z-P.ICT01_WIDTH) < 1e-5
    print(f'ICT-01 source: pin/socket pitch {P.ICT01_PITCH:g}, width {P.ICT01_WIDTH:g} mm')

    vertices, faces, labels, components = wheel_components()
    sprocket = vertices[labels == components[0]]
    tyre = vertices[labels == components[1]]
    assert abs(np.ptp(tyre[:,0])-P.TB3_WHEEL_D) < .01
    assert abs(np.ptp(sprocket[:,1])-P.TB3_SPROCKET_W) < .01
    assert abs(sprocket[:,1].min()+P.TB3_SPROCKET_CENTER) < .01
    # Intersect bare-sprocket triangles with its axial mid-plane Y=0.
    points = []
    for tri in vertices[faces[labels[faces[:,0]] == components[0]]]:
        for i,j in ((0,1),(1,2),(2,0)):
            a,b = tri[i],tri[j]
            if a[1]*b[1] < 0:
                points.append(a+(b-a)*(-a[1]/(b[1]-a[1])))
    points = np.array(points)
    angles = np.sort(np.mod(np.degrees(np.arctan2(points[:,2],points[:,0])),360)[np.hypot(points[:,0],points[:,2]) > 30.5])
    gaps = np.diff(np.r_[angles, angles[0]+360])
    teeth = int(np.sum(gaps > 2))
    assert teeth == P.TB3_SPROCKET_TEETH, (teeth, P.TB3_SPROCKET_TEETH)
    print(f'ISW-01 source: {teeth} teeth; bare width {np.ptp(sprocket[:,1]):g} mm; rubber tyre diameter {np.ptp(tyre[:,0]):g} mm')
    print(f'Nominal pin radius {P.ICT01_PITCH_R:.3f} mm; {P.ICT01_LINKS} links -> {P.ARM_CENTER_DIST:g} mm centres')
    print('Tooth/link engagement and print fit remain separate qualification requirements.')


if __name__ == '__main__':
    main()
