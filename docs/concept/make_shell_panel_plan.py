"""Draw proposed service groups within the selected shell silhouette.

This is a vector planning sketch, not shell CAD or a dimensioned assembly.
The two original styling images are retained separately without alteration.
"""
import argparse
import html
from pathlib import Path

import cairosvg

HERE = Path(__file__).resolve().parent
INK, MUTED, RED, BLUE = "#172b3a", "#526473", "#c93632", "#197fa3"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--preview-dir", type=Path)
    args = parser.parse_args()
    svg = ['<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="1160" viewBox="0 0 1200 1160">',
           '<title>Exterior shell panel plan</title>',
           '<desc>Side-profile planning sketch retaining the sloped black-and-red shell style. Five service groups identify split roof trim, side covers, front cheeks, rear hatch and lower nose trim. Open tracks and the raised LiDAR remain exposed. No dimensional or clearance qualification is implied.</desc>',
           '<defs><marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0 0 L10 5 L0 10Z" fill="#197fa3"/></marker></defs>',
           '<rect width="1200" height="1160" fill="#ffffff"/>',
           '<g font-family="DejaVu Sans,Arial,sans-serif" stroke-linejoin="round" stroke-linecap="round">']

    def text(x, y, value, size=18, colour=INK, bold=False, anchor="start"):
        for i, line in enumerate(value.split("\n")):
            svg.append(f'<text x="{x}" y="{y+i*(size+7)}" font-size="{size}" fill="{colour}" font-weight="{700 if bold else 400}" text-anchor="{anchor}">{html.escape(line)}</text>')

    def path(points, fill="none", stroke=INK, width=2, dash=False):
        svg.append(f'<path d="{points}" fill="{fill}" stroke="{stroke}" stroke-width="{width}"' + (' stroke-dasharray="7 5"' if dash else '') + '/>')

    def rect(x, y, w, h, fill, stroke=INK, radius=0):
        svg.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{radius}" fill="{fill}" stroke="{stroke}" stroke-width="2"/>')

    def circle(x, y, r, fill, stroke=INK, width=2):
        svg.append(f'<circle cx="{x}" cy="{y}" r="{r}" fill="{fill}" stroke="{stroke}" stroke-width="{width}"/>')

    def arrow(x1, y1, x2, y2):
        svg.append(f'<path d="M{x1} {y1} L{x2} {y2}" fill="none" stroke="{BLUE}" stroke-width="3" marker-end="url(#arrow)"/>')

    def outward(x, y):
        circle(x, y, 11, "white", BLUE)
        circle(x, y, 3.5, BLUE, BLUE)

    def callout(letter, x, y, tx, ty):
        path(f"M{x} {y} L{tx} {ty}", stroke=MUTED, width=1.5)
        circle(tx, ty, 3, INK)
        circle(x, y, 19, "white")
        text(x, y + 7, letter, 20, bold=True, anchor="middle")

    text(40, 47, "Exterior shell panel plan", 30, bold=True)
    text(40, 80, "Saved styling direction retained — proposed panel divisions and removal paths", 18, MUTED)
    path("M40 100 L1160 100", stroke="#d4dde3")
    text(40, 135, "SIDE PROFILE  /  FRONT →", 16, MUTED, True)
    text(1160, 135, "NOT TO SCALE", 15, MUTED, anchor="end")

    # Faceted shell profile follows the saved styling, without claiming a fitted surface.
    path("M245 505 L245 350 L285 285 L650 285 L1000 510 L1000 540 L245 540 Z", "#30363c")
    # Roof edge and upper vented shoulder.
    path("M285 285 L650 285 L683 308 L277 308 Z", "#535d66")
    path("M277 315 L642 315 L732 375 L250 375 L250 352 Z", "#414a52")
    for x in range(310, 620, 38):
        path(f"M{x} 332 L{x+18} 332 L{x+3} 359 L{x-15} 359 Z", "#171c20", "#171c20")
    # Large side cover and separate shallow front cheek.
    path("M250 382 L726 382 L810 490 L250 490 Z", "#292f35", "#596671")
    path("M650 315 L1000 510 L823 510 L737 383 Z", "#353d44", "#596671")
    path("M736 383 L821 497", stroke=RED, width=5)
    # Rear hatch and lower nose strip; actual fasteners remain to be located.
    path("M225 357 L245 350 L245 505 L225 505 Z", "#424b53")
    rect(810, 514, 190, 25, "#272d33", "#596671")
    for x in (951, 968):
        path(f"M{x} 520 L{x+9} 520 L{x+1} 533 L{x-8} 533 Z", RED, RED)
    text(777, 455, "SKALA", 18, RED, True)
    # A placeholder access opening; final openings come from the installed ports.
    rect(520, 406, 48, 50, "#11171c", "#65747e", 3)
    rect(530, 416, 28, 16, "#37444e", "#a4b0b8")
    rect(530, 440, 28, 8, "#255179", "#9aadb9")
    # Exposed scanner and its support remain outside the cosmetic enclosure.
    rect(415, 262, 240, 12, "#333c44", "#333c44")
    for x in (437, 613):
        rect(x, 207, 9, 55, "#acb3b6", "#65747e")
    rect(467, 169, 132, 58, "#20272d", "#424d56", 13)
    rect(482, 227, 101, 27, "#353e46", "#424d56", 7)
    # Camera side outline at the open nose; no enclosure is attached to its moving frame.
    rect(902, 497, 68, 9, "#161c21", "#596671")
    rect(918, 465, 31, 32, "#242c33", "#596671")
    rect(928, 410, 12, 58, "#1e252b", "#596671")
    rect(929, 383, 35, 54, "#303a42", "#596671", 6)
    rect(964, 394, 7, 31, RED, "#222b32", 2)
    # Existing tracks and printed structural parts remain black.
    rect(217, 529, 691, 155, "#22272c", "#515b63", 72)
    for x in (295, 830):
        circle(x, 606, 57, "#353c43", "#6b757d", 3)
        circle(x, 606, 17, "#242b32", "#6b757d")
    for x in range(275, 856, 23):
        rect(x, 531, 13, 14, "#404950", "#20262b", 2)
        rect(x, 668, 13, 13, "#404950", "#20262b", 2)

    # Symbols denote a service intent, not a tested removal trajectory.
    outward(370, 297)
    outward(434, 426)
    outward(850, 455)
    arrow(221, 472, 171, 472)
    arrow(1008, 526, 1080, 526)
    callout("A", 300, 205, 370, 290)
    callout("B", 109, 364, 422, 413)
    callout("C", 1081, 361, 861, 446)
    callout("D", 108, 503, 232, 420)
    callout("E", 1081, 609, 958, 527)
    text(40, 724, "⊙ = remove towards the viewer. Mirrored covers come away on the opposite side.", 17, BLUE)
    path("M40 746 L1160 746", stroke="#d4dde3")

    for x, y, letter, title, detail in [
        (45, 789, "A", "Split roof trim", "Separate around the LiDAR bridge.\nKeep the scanner mounted during removal."),
        (640, 789, "B", "Side service covers", "Open access to boards, ports and cable ties.\nPosition holes from actual plugged-in hardware."),
        (45, 921, "C", "Mirrored front cheeks", "Keep the symmetric recess and gradual slope.\nRemove a cheek to reach the camera mechanism."),
        (640, 921, "D", "Rear service hatch", "Size the opening around the selected power bank.\nKeep the central drive-battery route separate."),
    ]:
        circle(x + 18, y - 5, 17, "white")
        text(x + 18, y + 2, letter, 18, bold=True, anchor="middle")
        text(x + 48, y, title, 20, bold=True)
        text(x + 48, y + 33, detail, 17, MUTED)
    circle(63, 1048, 17, "white")
    text(63, 1055, "E", 18, bold=True, anchor="middle")
    text(93, 1053, "Detachable lower nose trim", 20, bold=True)
    text(93, 1083, "Keep access to the front fixings and check the camera image at downward tilt.", 17, MUTED)
    path("M40 1115 L1160 1115", stroke="#d4dde3")
    text(40, 1141, "Planning sketch • mounting tabs, final splits, optical clearance and removal paths remain to be modeled", 15, MUTED)
    svg.extend(["</g>", "</svg>"])
    path_out = HERE / "exterior-shell-panel-plan.svg"
    path_out.write_text("\n".join(svg) + "\n")
    if args.preview_dir:
        args.preview_dir.mkdir(parents=True, exist_ok=True)
        cairosvg.svg2png(url=str(path_out), write_to=str(args.preview_dir / "exterior-shell-panel-plan.png"))
    print(f"Generated {path_out}")


if __name__ == "__main__":
    main()
