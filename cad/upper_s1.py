"""Unpowered deck and board mounts, U1. No sensor or power-system release.

Robot frame: X forward, Y left, chassis top Z=0. Printed adapters use their
hole-pattern centre as origin and bottom Z=0; STL exports are bed-translated.
"""
from functools import lru_cache
from pathlib import Path
from math import sqrt
from build123d import (Align, Axis, Box, BuildPart, BuildSketch, Cylinder,
                      Locations, Mode, Plane, RectangleRounded, RegularPolygon,
                      SlotCenterToCenter, extrude, fillet, import_step)

HERE = Path(__file__).resolve().parent
REVISION = 'P0-U1-2026-11-03'
DECK_COLUMNS = [(x,y) for x in (-80,24) for y in (-32,32)]
OPENCR_BASE = [(x,y) for x in (-104,-24) for y in (-32,32)]
OPENCR_BOARD = [(x,y) for x in (-97,-31) for y in (-48,48)]
PI_BASE = [(x,y) for x in (-8,40) for y in (-40,40)]
PI_BOARD = [(x,y) for x in (-8.5,40.5) for y in (-29,29)]
DECK_BOTTOM, DECK_TOP = 60,64
ADAPTER_BOTTOM, ADAPTER_TOP, BOARD_BOTTOM = 76,79,85
OPENCR_NATIVE_CENTRE = (.94461168041071,-1.65309900983864)

def cylinder(r,h,xyz=(0,0,0)):
    return Cylinder(r,h,align=(Align.CENTER,Align.CENTER,Align.MIN)).translate(xyz)

def ring(od,inside,h,xyz):
    return (cylinder(od/2,h)-cylinder(inside/2,h+2,(0,0,-1))).translate(xyz)

def standoff(h,xy,z,af=5):
    with BuildPart() as part:
        with BuildSketch():
            RegularPolygon(af/sqrt(3),6)
        extrude(amount=h)
        Cylinder(1.25,h+2,align=(Align.CENTER,Align.CENTER,Align.MIN),mode=Mode.SUBTRACT)
    return part.part.translate((*xy,z))

def opencr_adapter():
    # Legacy 84 mm width left only 0.3 mm beyond the deck-hole bores.
    # 92 mm gives 4.3 mm of material and a fully supported Ø7 washer.
    with BuildPart() as p:
        Box(92,112,3,align=(Align.CENTER,Align.CENTER,Align.MIN))
        fillet(p.edges().filter_by(Axis.Z),4)
        for x in (-33,33):
            for y in (-48,48):
                with BuildSketch(Plane.XY):
                    with Locations((x,y)):
                        SlotCenterToCenter(2,3.4,rotation=90)
                extrude(amount=5,both=True,mode=Mode.SUBTRACT)
        with Locations(*[(x,y) for x in (-40,40) for y in (-32,32)]):
            Cylinder(1.7,10,mode=Mode.SUBTRACT)
        with BuildSketch():
            RectangleRounded(44,60,6)
        extrude(amount=5,both=True,mode=Mode.SUBTRACT)
    p.part.label='opencr_adapter_s1'
    return p.part

def pi_adapter():
    # Pi 4B USB/Ethernet toward +Y; 58 mm pitch along Y, 49 along X.
    # Base holes are separate from board holes and future sensor fixings.
    with BuildPart() as p:
        Box(64,96,3,align=(Align.CENTER,Align.CENTER,Align.MIN))
        fillet(p.edges().filter_by(Axis.Z),4)
        with Locations(*[(x,y) for x in (-24.5,24.5) for y in (-29,29)]):
            Cylinder(1.35,10,mode=Mode.SUBTRACT)
        with Locations(*[(x,y) for x in (-24,24) for y in (-40,40)]):
            Cylinder(1.7,10,mode=Mode.SUBTRACT)
        with BuildSketch():
            RectangleRounded(34,50,5)
        extrude(amount=5,both=True,mode=Mode.SUBTRACT)
    p.part.label='pi4_adapter_s1'
    return p.part

@lru_cache
def opencr():
    p=import_step(str(HERE/'vendor/robotis/opencr_rev_h.step'))
    return p.translate((-64-OPENCR_NATIVE_CENTRE[0],-OPENCR_NATIVE_CENTRE[1],86.65))

def pi_pcb():
    # Official 85 x 56 outline, offset 10 mm from mounting-pattern centre.
    # 1.6 mm thickness is a nominal envelope; check the owned board.
    p=Box(56,85,1.6,align=(Align.CENTER,Align.CENTER,Align.MIN)).translate((16,10,85))
    for x,y in PI_BOARD:
        p-=cylinder(1.35,4,(x,y,84))
    return p

def installed():
    out={
        'chassis':import_step(str(HERE/'out/step/chassis_p0.step')).translate((0,0,-6)),
        'deck':import_step(str(HERE/'out/step/deck_p0.step')).translate((-28,0,60)),
        'opencr_adapter':opencr_adapter().translate((-64,0,76)),
        'pi_adapter':pi_adapter().translate((16,0,76)),
        'pi_pcb_envelope':pi_pcb(),
    }
    for name,points,height,z in [('deck',DECK_COLUMNS,60,0),('opencr',OPENCR_BASE,12,64),('pi',PI_BASE,12,64)]:
        for i,xy in enumerate(points):
            out[f'{name}_column_{i}']=standoff(height,xy,z)
    for name,points in [('opencr',OPENCR_BOARD),('pi',PI_BOARD)]:
        for i,(x,y) in enumerate(points):
            out[f'{name}_board_spacer_{i}']=ring(5,3.2,6,(x,y,79))
    return out
