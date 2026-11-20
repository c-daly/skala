"""Constant-length lead geometry for P0-R1's bounded +/-50 degree pitch.

An elliptical wrap and an outboard return keep a finite bend radius without
stretching the cable. The moving lead is three 22 AWG wires, dressed <=4.5 mm.
These are geometry checks, not fatigue or electrical qualification.
"""
import math
import numpy as np
from scipy.optimize import brentq
from build123d import *
import reduction_p0 as R
from parts import pitch_reduction_p0 as C


def bezier_points(controls,count=151):
    c=np.asarray(controls);t=np.linspace(0,1,count)[:,None]
    return (1-t)**3*c[0]+3*(1-t)**2*t*c[1]+3*(1-t)*t*t*c[2]+t**3*c[3]


def route(pitch,radius,geometry=False):
    def ell(a):
        return np.array([1.35*radius*math.cos(a),.95*radius*math.sin(a),R.CABLE_PLANE])
    def tangent(a):
        t=np.array([-1.35*math.sin(a),.95*math.cos(a),0.])
        return t/np.linalg.norm(t)
    a=math.radians(135);b=math.radians(360-pitch)
    w=np.array([math.cos(b),math.sin(b),0.]);v=np.array([-math.sin(b),math.cos(b),0.])
    c0=ell(a);c1=ell(b)
    entry=np.array([[0,52,R.CABLE_PLANE],[0,37,R.CABLE_PLANE],c0-15*tangent(a),c0])
    width=float(c1@w)
    return_start=width*w+32*v+np.array([0,0,R.CABLE_RETURN_PLANE])
    bridge=np.array([c1,c1+12*tangent(b),return_start-12*v,return_start])
    centre=width*w/2+32*v+np.array([0,0,R.CABLE_RETURN_PLANE])
    arc_points=np.array([centre+width/2*(math.cos(t)*w+math.sin(t)*v) for t in np.linspace(0,math.pi,201)])
    ellipse_points=np.array([ell(t) for t in np.linspace(a,b,401)])
    pts=np.vstack([bezier_points(entry)[:-1],ellipse_points[:-1],bezier_points(bridge)[:-1],arc_points])
    if not geometry:
        return pts,None
    paths=[Bezier(*map(tuple,entry)),Edge.make_ellipse(1.35*radius,.95*radius,Plane(origin=(0,0,R.CABLE_PLANE)),135,360-pitch),
           Bezier(*map(tuple,bridge)),ThreePointArc(tuple(arc_points[0]),tuple(arc_points[100]),tuple(arc_points[-1]))]
    return pts,Wire([e for path in paths for e in path.edges()])


def curve_length(pts):
    return float(np.linalg.norm(np.diff(pts,axis=0),axis=1).sum())


def loop(pitch,geometry=True):
    target=curve_length(route(0,R.CABLE_NOMINAL_R)[0])
    r=brentq(lambda r:curve_length(route(pitch,r)[0])-target,15,50)
    return route(pitch,r,geometry)


def tube(path):
    return sweep(Plane(origin=path.position_at(0),z_dir=path.tangent_at(0))*Circle(R.CABLE_DIAMETER/2),path=path)


def moving_tail():
    z=R.CABLE_RETURN_PLANE
    entry=ThreePointArc((0,32,z),(0,32-10/math.sqrt(2),z+10-10/math.sqrt(2)),(0,22,z+10))
    rest=FilletPolyline((0,22,z+10),(0,22,R.ARM_FACE+27.5),(0,46,R.ARM_FACE+27.5),
                       (55,46,R.ARM_FACE+27.5),(55,46,R.ARM_FACE-12.5),
                       (55,0,R.ARM_FACE-12.5),(55,0,R.ARM_FACE+1.9),radius=10)
    return Wire([*entry.edges(),*rest.edges()])


def fixed_tail():
    # Ends tangent downward into the wrap. Final socket dressing is inside
    # the open rear-case plenum; no undimensioned socket centre is invented.
    # Pass below the retained deck, then rise beyond its outboard edge.
    return FilletPolyline((0,39,-48),(0,39,-5),(0,66,-5),
                          (0,66,R.CABLE_PLANE),(0,52,R.CABLE_PLANE),radius=10)


def parts(pitch=0):
    pts,path=loop(pitch)
    return [('lead_service_loop',tube(path)),('lead_fixed_tail',tube(fixed_tail())),
            ('lead_moving_tail',tube(moving_tail()).rotate(Axis.Z,-pitch))]


def metrics(pitch):
    pts,_=loop(pitch,geometry=False)
    a=pts[1:-1]-pts[:-2];b=pts[2:]-pts[1:-1]
    radius=np.linalg.norm(a,axis=1)*np.linalg.norm(b,axis=1)*np.linalg.norm(a+b,axis=1)/np.maximum(2*np.linalg.norm(np.cross(a,b),axis=1),1e-12)
    s=np.r_[0,np.cumsum(np.linalg.norm(np.diff(pts,axis=0),axis=1))]
    distances=np.linalg.norm(pts[:,None]-pts[None,:],axis=2)
    distances[np.abs(s[:,None]-s[None,:])<15]=np.inf
    return curve_length(pts),float(radius.min()),float(distances.min()),pts


def rear_plenums():
    # Covers seated connectors anywhere on the complete rear face, plus bends.
    return [('pitch_socket_plenum',C.box(28.5,46.5,19,(0,12,-45.5))),
            ('drive_socket_plenum',C.box(46.5,28.5,18,(58,0,R.ARM_FACE+1)))]

