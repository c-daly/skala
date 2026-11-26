"""Render the actual SH1 CAD and retained robot, without generated geometry."""
import argparse
import hashlib
import json
import sys
import zipfile
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT / 'docs/assembly/figures'))
import make_completed_sensor_view as R
import shell_s1 as H


def add_shapes(scene, shapes):
    vertices, faces, colours, groups = [a.copy() for a in scene]
    for i, (name, shape) in enumerate(shapes.items()):
        v, f = shape.tessellate(.1, .2)
        v = np.array([tuple(p) for p in v], dtype=np.float32)
        f = np.array(f, dtype=np.int32)
        colour = (85, 95, 106) if 'bracket' not in name else (180, 65, 48)
        faces = np.concatenate((faces, f + len(vertices)))
        vertices = np.concatenate((vertices, v))
        colours = np.concatenate((colours, np.tile(colour, (len(f), 1))))
        groups = np.concatenate((groups, np.full(len(f), 1000+i, dtype=np.int32)))
    return vertices, faces, colours, groups


def font(size):
    return ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', size)


def print_sheet():
    """Inspect the exported STL bytes, including their actual bed orientation."""
    receipt = json.loads((HERE/'review/shell/audit.json').read_text())
    canvas = Image.new('RGB',(1500,960),'#f4f6f8')
    draw = ImageDraw.Draw(canvas)
    draw.text((30,20),'SH1 / FIRST LEFT-SIDE PRINT SET',font=font(30),fill='#172b3a')
    draw.text((30,65),'Rendered from the exported STL files, in their supplied bed orientations',font=font(19),fill='#526473')
    sources = {}
    for i,(name,record) in enumerate(receipt['parts'].items()):
        path = HERE/'review/shell'/(name+'.stl')
        sources[str(path.relative_to(ROOT))] = hashlib.sha256(path.read_bytes()).hexdigest()
        raw = path.read_bytes()
        count = int.from_bytes(raw[80:84],'little')
        dtype = np.dtype([('normal','<f4',3),('vertices','<f4',(3,3)),('attribute','<u2')])
        vertices = np.frombuffer(raw,dtype=dtype,offset=84,count=count)['vertices'].reshape(-1,3)
        faces = np.arange(len(vertices),dtype=np.int32).reshape(-1,3)
        scene = (vertices,faces,np.tile((90,106,120),(count,1)),np.zeros(count,dtype=np.int32))
        pic,_ = R.render(scene,(1,-1,1.3),460,290)
        x,y = 20+(i%3)*500,130+(i//3)*400
        canvas.paste(pic,(x,y),pic)
        label = name.removeprefix('shell_').removesuffix('_s1_L').removesuffix('_s1').replace('_',' ')
        draw.text((x+12,y-25),label.upper(),font=font(18),fill='#172b3a')
        qty = 2 if name=='shell_deck_bracket_s1' else 1
        sizes = ' x '.join(f'{v:g}' for v in record['size_mm'])
        draw.text((x+12,y+296),f'Print {qty} | {sizes} mm',font=font(18),fill='#526473')
    draw.text((1030,590),'6 pieces / 5 files',font=font(25),fill='#172b3a')
    draw.text((1030,640),'Black filament; fit one side first.',font=font(19),fill='#526473')
    draw.text((1030,680),'All pieces have a flat bed face.',font=font(19),fill='#526473')
    draw.text((30,915),'Fit candidates. Inspect the slicer preview and verify fasteners, plugs, camera images and removal on the actual assembly.',font=font(18),fill='#526473')
    path = ROOT/'docs/concept/2026-11-26-shell-fit-parts.png'
    canvas.save(path)
    return path,sources


def package(images):
    """Make the downloadable fit guide and its links usable outside the repo."""
    folder = HERE/'review/shell'
    audit = json.loads((folder/'audit.json').read_text())
    if audit['failures']:
        raise ValueError('Refusing to package a failed shell audit')
    for name,expected in audit['source_sha256'].items():
        if hashlib.sha256((ROOT/name).read_bytes()).hexdigest()!=expected:
            raise ValueError('Stale shell audit: '+name)
    guide = (ROOT/'docs/design/shell-first-fit.md').read_text()
    guide = guide.replace('../../cad/review/shell/','')
    guide = guide.replace('[first-fit package](shell-first-fit-s1.zip)', 'first-fit package')
    guide = guide.replace('../concept/','images/')
    guide = guide.replace('(exterior-shell-concept.md)',
                          '(https://github.com/c-daly/skala/blob/main/docs/design/exterior-shell-concept.md)')
    target = folder/'shell-first-fit-s1.zip'
    with zipfile.ZipFile(target,'w',zipfile.ZIP_DEFLATED) as z:
        for name,record in audit['parts'].items():
            for ext in ('step','stl'):
                path = folder/(name+'.'+ext)
                if hashlib.sha256(path.read_bytes()).hexdigest()!=record[ext+'_sha256']:
                    raise ValueError('Export changed: '+path.name)
                z.write(path,path.name)
        z.write(folder/'shell_installed_s1.step','shell_installed_s1.step')
        z.write(folder/'audit.json','audit.json')
        z.writestr('FIT-GUIDE.md',guide)
        for path in images:z.write(path,'images/'+path.name)
    return target


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--output', type=Path, default=ROOT/'docs/concept/2026-11-26-shell-cad.png')
    args = p.parse_args()
    sources = R.source_hashes()
    base = list(R.mesh_scene(Path('/tmp/skala-assembly-render-cache'), sources))
    base[2] = base[2].copy()
    for category in ('structure', 'mount'):
        mask = np.all(base[2] == R.COLOURS[category], axis=1)
        base[2][mask] = (48, 52, 58)
    parts = H.installed()
    scene = add_shapes(base, parts)
    removed = dict(parts)
    for name in ('side_cover_L', 'cheek_L'):
        removed[name] = removed[name].translate((0, 70, 0))
    exploded = add_shapes(base, removed)
    canvas = Image.new('RGB', (1600, 1280), '#f4f6f8')
    draw = ImageDraw.Draw(canvas)
    draw.text((35, 24), 'SKALA / FIRST SHELL CAD', font=font(34), fill='#172b3a')
    draw.text((35, 72), 'SH1: cut-back cheeks + removable side covers | actual CAD, nominal geometry', font=font(20), fill='#526473')
    views = [(scene,(1.25,1.5,.9),(10,135),'FRONT THREE-QUARTER'),
             (scene,(0,1,0),(810,135),'LEFT SIDE / FRONT TO LEFT'),
             (scene,(1,0,0),(10,655),'FRONT / SYMMETRIC OPENING'),
             (exploded,(1.25,1.5,.9),(810,655),'LEFT COVERS REMOVED / BRACKETS STAY')]
    for data,eye,xy,label in views:
        pic,_ = R.render(data, eye, 780, 460)
        canvas.paste(pic, xy, pic)
        draw.text((xy[0]+24,xy[1]-28),label,font=font(19),fill='#172b3a')
    draw.text((35,1170),'Grey: new cover geometry. Red: fixed brackets highlighted for identification; print black.',font=font(19),fill='#172b3a')
    draw.text((35,1202),'Roof trim, rear hatch and lower nose are not modeled. Existing printed structure remains black.',font=font(18),fill='#526473')
    draw.text((35,1232),'CAD clearance is not physical fit, cooling, strength or camera-image qualification.',font=font(18),fill='#526473')
    args.output.parent.mkdir(parents=True,exist_ok=True)
    canvas.save(args.output)
    sheet,stl_sources = print_sheet()
    sources.update(stl_sources)
    sources['docs/design/shell-first-fit.md'] = hashlib.sha256((ROOT/'docs/design/shell-first-fit.md').read_bytes()).hexdigest()
    bundle = package((args.output,sheet))
    sources.update({str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest()
                    for p in (HERE/'shell_s1.py',Path(__file__),ROOT/'docs/assembly/figures/make_completed_sensor_view.py')})
    receipt={'sources':sources,'outputs':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest()
                                          for p in (args.output,sheet,bundle)}}
    (HERE/'review/shell').mkdir(parents=True,exist_ok=True)
    (HERE/'review/shell/preview.json').write_text(json.dumps(receipt,indent=2)+'\n')
    print(args.output,flush=True)


if __name__ == '__main__':
    main()
