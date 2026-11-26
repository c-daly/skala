#!/usr/bin/env python3
"""Prepare and validate Skala's Obsidian reading copy, then apply that bundle.

Source prose and CAD registers remain in this repository. Vault-specific context
stays in the vault. Only named files are touched; concurrent edits abort apply.
This is a one-way export: reconcile newer vault decisions and prose into the
repository before preparing a bundle. It does not import vault changes.
"""

import argparse
import hashlib
import json
import re
from pathlib import Path
from urllib.parse import unquote, urlsplit
from xml.etree import ElementTree


REPO = Path(__file__).resolve().parents[1]
PROJECT = "10-projects/skala/"
GUIDE = PROJECT + "2026-10-26-p0-assembly-guide.md"
BOM = PROJECT + "bill-of-materials.md"
SPEC = PROJECT + "2026-10-24-physical-design-spec.md"
REVIEW = PROJECT + "build-review.md"
CAD = PROJECT + "cad-workflow.md"
PARTS = PROJECT + "parts-and-interfaces.md"
PITCH = PROJECT + "pitch-actuator-comparison.md"
AUDIO = PROJECT + "audio-memory-handoff.md"
SYSTEM = PROJECT + "s1-system-design.md"
HOME = PROJECT + "Skala.md"
NARRATIVE = PROJECT + "narrative.md"
TALOS = "10-projects/LOGOS/talos/2026-10-24-capability-manifest-design.md"
MODULE = PROJECT + "attachments/s1-track-module.svg"
BASE = PROJECT + "attachments/s1-fixed-base.svg"
FIGURES = {
    "docs/assembly/figures/s1-00-idler-parts.svg": PROJECT + "attachments/s1-00-idler-parts.svg",
    "docs/assembly/figures/s1-01-overview.svg": BASE,
    "docs/assembly/figures/s1-02-motor.svg": MODULE,
    **{f"docs/assembly/figures/{name}.svg": PROJECT + f"attachments/{name}.svg"
       for name in ("s1-02-cable-route", "s1-03-idler", "s1-04-brackets", "s1-05-track", "s1-06-chassis", "s1-07-connections", "s1-08-lead-restraint")},
    **{f"docs/assembly/figures/{name}.svg": PROJECT + f"attachments/{name}.svg"
       for name in ("u1-01-deck-holes", "u1-02-board-layout", "u1-03-fastener-stacks")},
    **{f"docs/assembly/figures/{name}.svg": PROJECT + f"attachments/{name}.svg"
       for name in ("u2-01-sensor-layout", "u2-02-camera-pivot", "u2-03-sensor-stacks", "u2-04-completed-assembly",
                    "u2-05-camera-pan-assembly", "u2-06-camera-part-identification")},
}
PRINT_PARTS = json.loads((REPO / "cad/print_parts.json").read_text())
SENSOR_PARTS = json.loads((REPO / "cad/sensor_parts.json").read_text())
SENSOR_FILES = {"cad/out/stl/" + p["stl"]: PROJECT + "attachments/" + p["stl"] for p in SENSOR_PARTS}
SUPPORT_FILES = {
    "scripts/migrate_pi_to_jazzy.py": PROJECT + "attachments/migrate_pi_to_jazzy.py",
}
FIT_FILES = {"cad/out/stl/" + p["stl"]: PROJECT + "attachments/" + p["stl"]
             for p in PRINT_PARTS if p["export"] == "current"}
RETAINED_FILES = {"cad/out/stl/" + p["stl"]: PROJECT + "attachments/" + p["stl"]
                  for p in PRINT_PARTS if p["export"] == "retained"}
PROSE = {
    "docs/assembly/p0-assembly.md": GUIDE,
    "docs/assembly/p0-bom.md": BOM,
    "docs/design/physical-design-spec.md": SPEC,
    "docs/assembly/p0-build-review.md": REVIEW,
    "docs/assembly/s1-system-plan.md": SYSTEM,
    "docs/assembly/commissioning-procedures.md": PROJECT + "commissioning-procedures.md",
    "cad/README.md": CAD,
    "firmware/opencr_reflex/README.md": PROJECT + "opencr-control.md",
    "software/talos/README.md": PROJECT + "pi-body-software.md",
    "docs/research/2026-10-25-audio-memory-handoff.md": AUDIO,
    "docs/design/filament-guide-adventurer-5m-pro.md": PROJECT + "2026-10-24-filament-guide-adventurer-5m-pro.md",
}
TARGETS = {
    **PROSE,
    **FIGURES,
    **FIT_FILES,
    **RETAINED_FILES,
    **SENSOR_FILES,
    **SUPPORT_FILES,
    "README.md": HOME,
    "cad/staged_base.json": PARTS,
    "cad/actuator_options.json": PITCH,
    "cad/bom_r1.json": PITCH + "#R1 reference parts",
    "cad/release_p0.json": REVIEW + "#Release conditions",
    "cad/review/staged-base/REVIEW_STATUS.json": REVIEW + "#Geometry check details",
    "cad/validation/p0-s1-2026-11-02.txt": REVIEW + "#Geometry check details",
    "cad/validation/p0-s1-assembly-audit-2026-11-02.json": REVIEW + "#Assembly path check details",
    "cad/validation/p0-s1-carrier-backplate-2026-11-02.json": REVIEW + "#Carrier backplate check details",
    "cad/validation/p0-u1-2026-11-03.json": REVIEW + "#Upper mounting check details",
    "cad/validation/p0-u2-sensors-2026-11-06.json": REVIEW + "#Sensor mounting check details",
    "cad/out/SENSOR_FIT_ARTICLES.json": REVIEW + "#Sensor export details",
    "cad/sensor_parts.json": PARTS + "#Sensor mounting candidates",
    "cad/validation/p0-track-diagnosis-2026-10-28.txt": REVIEW + "#Track geometry diagnostic",
    "cad/review/staged-base/module.svg": MODULE,
    "cad/review/staged-base/base_top.svg": BASE,
    "docs/design/talos-capability-manifest.md": TALOS,
    "docs/design/filament-guide-adventurer-5m-pro.md": PROJECT + "2026-10-24-filament-guide-adventurer-5m-pro.md",
}
MD_LINK = re.compile(r"(!?)\[([^\]\n]+)\]\(([^)\n]+)\)")
WIKI_LINK = re.compile(r"!?\[\[([^\]\n]+)\]\]")
SOURCES = {}


def digest(data):
    return hashlib.sha256(data).hexdigest()


def source(name):
    data = (REPO / name).read_bytes()
    SOURCES[name] = digest(data)
    return data.decode()


def heading_text(text):
    text = re.sub(r"```.*?```", "", text, flags=re.S)
    return re.findall(r"^#{1,6} (.+?)\s*#*\s*$", text, re.M)


def slug(text):
    return re.sub(r"[^\w\- ]", "", text.lower()).replace(" ", "-")


def wiki(target, label=None, embed=False):
    path, sep, anchor = target.partition("#")
    if path.endswith(".md"):
        path = path[:-3]
    return ("!" if embed else "") + "[[" + path + sep + anchor + ("|" + label if label else "") + "]]"


def convert(text, repo_name):
    def replace(match):
        embed, label, url = match.groups()
        parsed = urlsplit(url)
        if parsed.scheme:
            return match.group(0)
        resolved = ((REPO / repo_name).parent.joinpath(unquote(parsed.path)).resolve()
                    if parsed.path else (REPO / repo_name).resolve())
        try:
            name = resolved.relative_to(REPO).as_posix()
        except ValueError:
            try:
                name = resolved.relative_to(REPO.parent / "vault").as_posix()
            except ValueError:
                raise ValueError(f"Unmapped reading link in {repo_name}: {url}")
            target = name
        else:
            if name == "cad/staged_base.py":
                return "`cad/staged_base.py` (assembly source in the Skala repository)"
            target = TARGETS[name]
        if parsed.fragment:
            headings = heading_text(resolved.read_text())
            anchor = next((h for h in headings if slug(h) == parsed.fragment), None)
            if anchor is None:
                raise ValueError(f"Missing source heading: {url}")
            target += "#" + anchor
        # Wiki aliases inside Markdown tables require an escaped pipe.
        line = text[text.rfind("\n", 0, match.start()) + 1:match.start()]
        result = wiki(target, None if embed else label, bool(embed))
        return result.replace("|", r"\|") if line.lstrip().startswith("|") else result
    return MD_LINK.sub(replace, text)


def review_date(*texts, default="2026-11-07"):
    """Keep explicit source review dates and never roll vault metadata back."""
    dates = [default]
    for text in texts:
        dates.extend(re.findall(
            r"(?:^updated:\s*|\b(?:updated|reviewed)\s+(?:\*\*)?)(\d{4}-\d{2}-\d{2})",
            text, flags=re.M | re.I))
    return max(dates)


def frontmatter(existing, body, origin, updated="2026-10-30"):
    if existing.startswith("---\n"):
        header = existing.split("\n---\n", 1)[0]
        header = re.sub(r"^updated:.*$", "updated: " + updated, header, flags=re.M)
        header = re.sub(r"^source:.*$", "source: " + json.dumps(origin), header, flags=re.M)
        if not re.search(r"^updated:", header, re.M):
            header += "\nupdated: " + updated
        if not re.search(r"^source:", header, re.M):
            header += "\nsource: " + json.dumps(origin)
    else:
        header = (f'---\ncreated: {updated}\nupdated: {updated}\ntype: reference\n'
                  'project: skala\ntags: [skala, robotics]\nsource: ' + json.dumps(origin))
    return header + "\n---\n\n" + body.strip() + "\n"


def cell(value):
    if value is None:
        return "Not selected / not recorded"
    if isinstance(value, bool):
        return "Yes" if value else "No"
    if isinstance(value, (list, dict)):
        value = json.dumps(value, ensure_ascii=False)
    value = str(value)
    if value.startswith("https://"):
        value = "[Source](" + value + ")"
    return value.replace("|", r"\|").replace("\n", "<br>")


def table(rows):
    keys = list(dict.fromkeys(key for row in rows for key in row))
    return ("| " + " | ".join(k.replace("_", " ") for k in keys) + " |\n"
            + "| " + " | ".join("---" for _ in keys) + " |\n"
            + "\n".join("| " + " | ".join(cell(row.get(k, "")) for k in keys) + " |" for row in rows) + "\n\n")


def register(value, level=2):
    """Render every field so generated reading copies cannot omit new requirements."""
    if isinstance(value, dict):
        if all(not isinstance(v, dict) and
               (not isinstance(v, list) or all(not isinstance(x, (list, dict)) for x in v))
               for v in value.values()):
            return table([{"field": ("`" + k + "`" if "/" in k else k.replace("_", " ")), "value": v}
                          for k, v in value.items()])
        out = ""
        for key, item in value.items():
            title = key.replace("_", " ").capitalize()
            if isinstance(item, (dict, list)):
                out += "#" * level + " " + title + "\n\n" + register(item, min(level + 1, 6))
            else:
                out += "**" + title + ":** " + cell(item) + "\n\n"
        return out
    if isinstance(value, list):
        if not value:
            return "None recorded.\n\n"
        if all(isinstance(x, dict) for x in value):
            if all(not isinstance(v, (dict, list)) for x in value for v in x.values()):
                return table(value)
            return "".join(register(x, level) + "---\n\n" for x in value)
        return "\n".join("- " + cell(x) for x in value) + "\n\n"
    return cell(value) + "\n\n"


def build(vault):
    out = {}
    def existing(path):
        file = vault / path
        return file.read_text() if file.exists() else ""
    def add(path, body, origin):
        updated = review_date(existing(path), body)
        if path != HOME:
            body = re.sub(r"^(# .+\n)", lambda m: m.group(1) + "\n"
                          + wiki(HOME, "Project overview") + "\n", body, count=1)
        out[path] = frontmatter(existing(path), body, origin, updated).encode()

    catalog = json.loads(source("cad/print_parts.json"))
    sensor_catalog = json.loads(source("cad/sensor_parts.json"))
    for repo_name in ("docs/assembly/p0-assembly.md", "docs/assembly/p0-bom.md"):
        lines = source(repo_name).splitlines()
        for part in catalog:
            if not any(line.startswith("| " + part["id"] + " ") and part["name"] in line and part["stl"] in line for line in lines):
                raise ValueError(f'Part name/filename mismatch in {repo_name}: {part["id"]}')
        for part in sensor_catalog:
            if not any(line.startswith("| " + part["id"] + " ") and part["name"] in line and part["stl"] in line for line in lines):
                raise ValueError(f'Sensor name/filename mismatch in {repo_name}: {part["id"]}')
    for repo_name, target in PROSE.items():
        body = source(repo_name)
        if target == REVIEW:
            body = body.replace(
                "; the [run log](../../cad/validation/p0-s1-2026-11-02.txt) preserves the output.",
                ". Individual results, limitations and source hashes are included below.")
        if target == AUDIO:
            body = body.replace(
                "The [Cliste evidence index](../../../cliste/docs/audio-compatibility/README.md)\n"
                "and [latest result](../../../cliste/docs/audio-compatibility/sequence-result.md)\n"
                "provide methods, all conditions, figures, saved-home replay and original failures.",
                "The [[10-projects/cliste/experiments/2026-10-25-audio-sequence-results|Cliste sequence result]]\n"
                "summarizes the measured outcome. Full methods, figures and replay commands live in\n"
                "`docs/audio-compatibility/` in the Cliste repository.")
            body = body.replace(
                "Use the native API or the [documented CLI command](../../../cliste/docs/audio-compatibility/sequence-result.md#cost-use-and-validation)",
                "Use the native API or the CLI command documented in the Cliste repository's\n"
                "`docs/audio-compatibility/sequence-result.md`, under ‘Cost, use and validation’,")
        body = convert(body, repo_name)
        if target == REVIEW:
            system_sources = json.loads(source("cad/vendor/system_sources.json"))
            for entry in system_sources["sources"]:
                name = "cad/vendor/" + entry["file"]
                if digest((REPO / name).read_bytes()) != entry["sha256"]:
                    raise ValueError(f"System source differs from reviewed copy: {name}")
                SOURCES[name] = entry["sha256"]
            receipt = json.loads(source("cad/review/staged-base/REVIEW_STATUS.json"))
            # A stale receipt must not be published as evidence for current sources.
            for name, expected in receipt["source_sha256"].items():
                if digest((REPO / "cad" / name).read_bytes()) != expected:
                    raise ValueError(f"Review receipt is stale: cad/{name}")
                SOURCES["cad/" + name] = expected
            body += "\n## Geometry check details\n\n" + register(receipt, 3)
            audit = json.loads(source("cad/validation/p0-s1-assembly-audit-2026-11-02.json"))
            for name, expected in audit["source_sha256"].items():
                if digest((REPO / name).read_bytes()) != expected:
                    raise ValueError(f"Assembly audit is stale: {name}")
                SOURCES[name] = expected
            if audit["failures"]:
                raise ValueError("Assembly path audit contains unresolved failures")
            body += "\n## Assembly path check details\n\n" + register(audit, 3)
            backplate = json.loads(source("cad/validation/p0-s1-carrier-backplate-2026-11-02.json"))
            for name, expected in backplate["source_sha256"].items():
                if digest((REPO / name).read_bytes()) != expected:
                    raise ValueError(f"Carrier backplate check is stale: {name}")
                SOURCES[name] = expected
            if any(case["accepted"] != case["expected_accept"] for case in backplate["cases"]):
                raise ValueError("Carrier backplate regression contains a failure")
            body += "\n## Carrier backplate check details\n\n" + register(backplate, 3)
            upper = json.loads(source("cad/validation/p0-u1-2026-11-03.json"))
            for name, expected in upper["source_sha256"].items():
                if digest((REPO / name).read_bytes()) != expected:
                    raise ValueError(f"Upper mounting audit is stale: {name}")
                SOURCES[name] = expected
            if upper["failures"]:
                raise ValueError("Upper mounting audit contains unresolved failures")
            body += "\n## Upper mounting check details\n\n" + register(upper, 3)
            sensors = json.loads(source("cad/validation/p0-u2-sensors-2026-11-06.json"))
            for name, expected in sensors["source_sha256"].items():
                if digest((REPO / name).read_bytes()) != expected:
                    raise ValueError(f"Sensor mounting audit is stale: {name}")
                SOURCES[name] = expected
            if sensors["failures"]:
                raise ValueError("Sensor mounting audit contains unresolved failures")
            body += "\n## Sensor mounting check details\n\n" + register(sensors, 3)
            body += "\n## Sensor export details\n\n" + register(json.loads(source("cad/out/SENSOR_FIT_ARTICLES.json")), 3)
            body += "\n## Track geometry diagnostic\n\n```text\n" + source("cad/validation/p0-track-diagnosis-2026-10-28.txt").rstrip() + "\n```\n"
        add(target, body, "Skala repository " + repo_name + "; generated vault reading copy")

    data = json.loads(source("cad/staged_base.json"))
    add(PARTS, "# Skala parts and interfaces\n\n"
        "These are the active S0/S1 counts and configured interfaces. Four-module counts cover propulsion, not complete powered joints. "
        "Later two-pitch layouts and four legs with pitch/lateral movement are compared in "
        + wiki(SPEC + "#Form-factor choices and joint counts", "the development-layout table") + "; these lower fit articles do not qualify those future loads. "
        "Deck/OpenCR/bare-Pi hardware is specified in the guide and BOM. " + wiki(SYSTEM, "The complete-system design") + " owns power, harness endpoints, remaining sensor supports and H01-H10 closure conditions. Use " + wiki(GUIDE, "the assembly guide") + " for procedure and "
        + wiki(BOM, "the purchasing BOM") + " for lower and upper hardware links, package sizes and combined order quantities.\n\n"
        + "## Printed part filenames\n\n"
        + table([{"id": p["id"], "name": p["name"], "file": wiki(PROJECT + "attachments/" + p["stl"], p["stl"]), "identification": p["identify"]} for p in catalog])
        + register(data) + "\n## Sensor mounting candidates\n\n"
        + table([{**p, "stl": wiki(PROJECT + "attachments/" + p["stl"], p["stl"])} for p in sensor_catalog]),
        "Skala repository cad/staged_base.json, cad/print_parts.json and cad/sensor_parts.json; generated tables")
    data = json.loads(source("cad/actuator_options.json"))
    add(PITCH, "# Later tracked-leg actuator comparison\n\n"
        "Development options beyond S1: budget DIY BLDC/cycloidal joints, integrated brushless robot joints, and high-end aspirational Dynamixels. "
        "The destination is four powerful tracked legs with pitch and lateral movement; two-pitch layouts are possible intermediate stages. "
        "Bare BLDC motors need external phase-driver channels; integrated robot joints contain their motor drivers. "
        "Read " + wiki(SPEC + "#Options from budget to aspirational", "the cost-tier comparison") + ", "
        + wiki(SPEC + "#Form-factor choices and joint counts", "the form-factor and quantity comparison") + ", "
        + wiki(SPEC + "#BLDC fit and power screen", "the fit/power screen") + " and "
        + wiki(SPEC + "#If BLDC cycloidal pitch is selected", "the required project changes") + " before selecting parts. "
        "Prices below retain their recorded date; the separately labelled proposal prices are unverified, and no complete joint cost is established.\n\n"
        + register(data) + "## R1 reference parts\n\n"
        "This retained engineering comparison is not an approved purchase list.\n\n"
        + register(json.loads(source("cad/bom_r1.json")), 3),
        "Skala repository cad/actuator_options.json and cad/bom_r1.json; generated tables")

    figure_receipt = json.loads(source("docs/assembly/figures/s1-figure-sources.json"))
    for name, expected in figure_receipt["source_sha256"].items():
        if digest((REPO / name).read_bytes()) != expected:
            raise ValueError(f"Assembly figures are stale: {name}")
        SOURCES[name] = expected
    upper_figures = json.loads(source("docs/assembly/figures/u1-figure-sources.json"))
    for name, expected in upper_figures["source_sha256"].items():
        if digest((REPO / name).read_bytes()) != expected:
            raise ValueError(f"Upper assembly figures are stale: {name}")
        SOURCES[name] = expected
    sensor_figures = json.loads(source("docs/assembly/figures/u2-figure-sources.json"))
    for name, expected in sensor_figures["source_sha256"].items():
        if digest((REPO / name).read_bytes()) != expected:
            raise ValueError(f"Sensor figures are stale: {name}")
        SOURCES[name] = expected
    completed_view = json.loads(source("docs/assembly/figures/u2-04-completed-assembly-sources.json"))
    for name, expected in completed_view["source_sha256"].items():
        if digest((REPO / name).read_bytes()) != expected:
            raise ValueError(f"Completed assembly view is stale: {name}")
        SOURCES[name] = expected
    completed_svg = "docs/assembly/figures/" + completed_view["figure"]
    if digest((REPO / completed_svg).read_bytes()) != completed_view["output_sha256"]:
        raise ValueError("Completed assembly SVG differs from its receipt")
    camera_figures = json.loads(source("docs/assembly/figures/u2-camera-assembly-sources.json"))
    for name, expected in camera_figures["source_sha256"].items():
        if digest((REPO / name).read_bytes()) != expected:
            raise ValueError(f"Camera assembly figures are stale: {name}")
        SOURCES[name] = expected
    for filename, expected in camera_figures["output_sha256"].items():
        if digest((REPO / "docs/assembly/figures" / filename).read_bytes()) != expected:
            raise ValueError(f"Camera assembly SVG differs from its receipt: {filename}")
    for name, target in FIGURES.items():
        data = (REPO / name).read_bytes()
        ElementTree.fromstring(data)
        SOURCES[name] = digest(data)
        out[target] = data
    for name, target in SUPPORT_FILES.items():
        data = (REPO / name).read_bytes()
        SOURCES[name] = digest(data)
        out[target] = data
    fit = json.loads(source("cad/out/FIT_ARTICLES.json"))
    for name, expected in fit["source_sha256"].items():
        if digest((REPO / "cad" / name).read_bytes()) != expected:
            raise ValueError(f"Fit articles are stale: {name}")
        SOURCES["cad/" + name] = expected
    for name, target in FIT_FILES.items():
        data = (REPO / name).read_bytes()
        article = fit["parts"][Path(name).stem]
        if not article.get("stl_validation", {}).get("closed_single_solid"):
            raise ValueError(f"Fit STL has no closed-solid validation: {name}")
        if digest(data) != article["stl_sha256"]:
            raise ValueError(f"Fit STL differs from receipt: {name}")
        SOURCES[name] = digest(data)
        out[target] = data

    sensor_fit = json.loads(source("cad/out/SENSOR_FIT_ARTICLES.json"))
    for name, expected in sensor_fit["source_sha256"].items():
        if digest((REPO / name).read_bytes()) != expected:
            raise ValueError(f"Sensor fit articles are stale: {name}")
        SOURCES[name] = expected
    for name, target in SENSOR_FILES.items():
        data = (REPO / name).read_bytes()
        article = sensor_fit["parts"][Path(name).stem]
        if not article.get("stl_validation", {}).get("closed_single_solid") or digest(data) != article["stl_sha256"]:
            raise ValueError(f"Sensor STL lacks matching closed-solid validation: {name}")
        SOURCES[name] = digest(data)
        out[target] = data

    # These are named retained files, not newly qualified fit articles.
    for name, target in RETAINED_FILES.items():
        data = (REPO / name).read_bytes()
        SOURCES[name] = digest(data)
        out[target] = data

    # One maintained progress/navigation source, not a chain of dated replacements.
    home = convert(source("README.md"), "README.md")
    home += "\n## Decision history\n\n" + wiki(NARRATIVE, "Dated narrative") + (
        " records earlier choices and corrections. Historical decisions are not current build instructions.\n")
    add(HOME, home, "Skala repository README.md; generated project overview")

    narrative = existing(NARRATIVE)
    intro = ("Skala is being developed toward four powered tracked flippers and stair climbing. "
             "The first useful research vehicle uses two fixed track modules with Pi/OpenCR, LiDAR, camera and audio input. "
             "Current instructions live in the repo; dated entries below record decisions at the time.")
    replacement = ("These dated entries preserve decisions and corrections at the time they occurred. "
                   "Older dimensions, purchase suggestions, torque assumptions and unfinished-work statements below "
                   "are historical, not current instructions. Use "
                   + wiki(HOME, "the current project overview") + " for progress, next steps and maintained build documents.")
    if intro in narrative:
        narrative = narrative.replace(intro, replacement)
    elif replacement not in narrative:
        raise ValueError("Cannot locate narrative introduction")
    heading = "## 2026-11-07 — Owned power banks and one project overview"
    if heading not in narrative:
        narrative += ("\n\n" + heading + "\n\n"
            "Several 5 V/3 A USB power banks are available. Current planning reuses one for the Pi and its downstream sensors; "
            "the owned LB-012 remains the drive/head source. No new compute bank or converter is required. "
            "The 2.85 A worksheet is an estimate, not evidence that 3 A is inadequate. "
            "Select the actual bank and cable using fit, loaded voltage, temperature, runtime and shutdown checks. "
            "WM8960 takes 5 V/GND through the Pi's 40-pin header, with no separate power lead. "
            "Keep a purchased Pololu head regulator if present; Hobbywing is a lower-cost candidate if one still needs buying. "
            "The single-battery/DFRobot option is retained only as an evaluated alternative. "
            "The vault landing page now collects physical construction, CAD, software, power and commissioning progress "
            "with links to each maintained source. Partial assembly and the prior TurtleBot3 installations are recorded "
            "separately from uncompleted Skala qualification. See " + wiki(HOME, "the project overview") + ".\n")
    latest = max(re.findall(r"^## (\d{4}-\d{2}-\d{2})\b", narrative, re.M))
    narrative = re.sub(r"^updated:.*$", "updated: " + latest, narrative, flags=re.M)
    out[NARRATIVE] = narrative.encode()

    # Keep dated evidence, but remove stale 'accepted' status and broken navigation.
    history = {
        "2026-10-24-prototype-0-from-turtlebot3-parts.md": (
            "superseded",
            "The original pitching-front-arm/passive-skid configuration, zero-new-parts claim and stall-torque "
            "margin are superseded. Current construction uses two fixed tracks; no pitch motor is selected or "
            "qualified. The dated text below is retained as the decision record, not a purchasing or load-rating instruction."),
        "2026-10-24-pla-first-tpu-only-new-filament.md": (
            "historical",
            "PLA-first remains a fit-prototyping approach. The broad material-adequacy assertions below do not "
            "qualify structural strength, creep or temperature. Current S1 uses owned ICT-01 links; printed TPU "
            "treads are not a baseline requirement. Use the current guide and filament guidance for each part."),
        "2026-10-24-parametric-code-cad-as-source.md": (
            "historical",
            "Code-based CAD and cad/out remain the workflow. The single-params.py and assembly_p0.py description "
            "below belongs to the superseded articulated model. Current build.py calls the lower/board and sensor "
            "exporters; the CAD workflow identifies their source files and receipts.")
    }
    for name, (status, explanation) in history.items():
        path = PROJECT + "decisions/" + name
        old = existing(path)
        if not old:
            raise ValueError("Missing historical decision: " + path)
        old = re.sub(r"^status:.*$", "status: " + status, old, flags=re.M)
        old = re.sub(r"^" + re.escape("**Status:**") + r".*$", "**Status:** " + status.capitalize(), old, flags=re.M)
        old = re.sub(r"^" + re.escape("**Full text:**") + r".*$", "**Current guidance:** "
                     + wiki(SPEC, "Physical design") + " and "
                     + wiki(GUIDE, "Assembly guide"), old, flags=re.M)
        # Normalize old relative wiki links so the whole project can be validated.
        def historical_link(match):
            target, _, label = match.group(1).partition("|")
            if target.startswith("10-projects/"):
                return match.group(0)
            target = (REPO / Path(path).parent / target).resolve().relative_to(REPO).as_posix()
            return wiki(target, label or None)
        old = WIKI_LINK.sub(historical_link, old)
        notice = "**Current applicability (2026-11-07):**"
        if notice not in old:
            marker = "\n## Decision\n"
            if marker not in old:
                raise ValueError("Missing decision section: " + path)
            old = old.replace(marker, "\n" + notice + " " + explanation + " See "
                              + wiki(HOME, "current progress") + " and " + wiki(CAD, "CAD workflow")
                              + ".\n" + marker, 1)
        out[path] = old.encode()

    talos = existing(TALOS)
    # Retire stale Skala implementation and power-off claims in the shared design context.
    for before, after in (
        ("Skala is the first body written against it.", "Skala is a planned body integration; its repository currently contains requirements, not a live body implementation."),
        ("This note belongs to talos (the LOGOS hardware-interface layer) and is mirrored here because skala is the first body written against it. Design date 2026-10-24; editable original https://claude.ai/artifact/Bpau2znAarDhkKruEdU6iF.", "The generic interface proposal dates from 2026-10-24; it is historical design context, not an assessment of the current shared Talos implementation. The Skala S1 profile below is maintained with the current robot decisions (reviewed 2026-11-07). Reuse and check the actual maintained Talos interfaces before implementing the Skala adapter; do not build a competing protocol from this earlier sketch."),
        ("Skala's `climb_step` will be a scripted state machine over IMU pitch and servo current; a later body might offer a behaviour backed by a policy network.", "A future articulated Skala could offer a `climb_step` behavior, using feedback available from its eventual qualified joints. It is outside current S1 scope; XL430 inferred load is not measured current. A different body might offer a behavior backed by a policy network."),
        ("link to the agent lost; the body holds position and stops drives on its own", "link lost; Skala stops and disarms locally. Power-off position holding is not provided"),
        ("These need a decision before the manifest schema becomes code. None blocks the OpenCR firmware.", "The questions below were recorded with the original 2026-10-24 interface proposal. They are historical design questions, not a claim that current Talos lacks a schema or transport. Resolve Skala's remaining adapter choices against the maintained shared implementation and the current S1 system plan."),
        ("What to do next, in order: settle the first two questions, write `manifest.py` with the four kinds and a validator, write skala's manifest as its test fixture, then write the OpenCR firmware against the actuators and sensors it must expose.", "Current Skala sequence: preserve and inventory the existing hardware software, qualify stationary sensors and power/stop behavior, adapt two-track control, then map the exercised devices into the maintained Talos interfaces. Implement a Skala-specific adapter and recorder where needed; do not assume a new shared manifest schema or library is required."),
    ):
        talos = talos.replace(before, after)
    current = source("docs/design/talos-capability-manifest.md")
    section = current.split("## Skala S1 capability plan", 1)[1].split("## Open questions", 1)[0]
    section = convert(section, "docs/design/talos-capability-manifest.md")
    talos, count = re.subn(r"## Skala(?:'s manifest \(prototype 0\)| S1 capability plan).*?(?=## Open questions)",
        "## Skala S1 capability plan" + section, talos, flags=re.S)
    if count != 1:
        raise ValueError("Cannot locate the existing Skala profile in the Talos note")
    talos = re.sub(r"^updated:.*$", "updated: " + review_date(talos, current), talos, flags=re.M)
    talos = re.sub(r"^source:.*$", 'source: "Talos design note; Skala profile refreshed from Skala repository docs/design/talos-capability-manifest.md"', talos, flags=re.M)
    out[TALOS] = talos.encode()
    return out


def contained(root, relative):
    path = (root / relative).resolve()
    if not path.is_relative_to(root.resolve()):
        raise ValueError(f"Path escapes root: {relative}")
    return path


def validate(out, vault):
    count = 0
    def content(path):
        return out[path] if path in out else contained(vault, path).read_bytes()
    for name, data in out.items():
        if not name.endswith(".md"):
            continue
        text = re.sub(r"```.*?```", "", data.decode(), flags=re.S)
        for _, _, url in MD_LINK.findall(text):
            if not urlsplit(url).scheme:
                raise ValueError(f"Non-vault reading link in {name}: {url}")
        for link in WIKI_LINK.findall(text):
            target = link.replace(r"\|", "|").split("|", 1)[0]
            path, _, anchor = target.partition("#")
            if not path:
                path = name
            elif not Path(path).suffix:
                path += ".md"
            # Older contextual pages may use unique basename links.
            if "/" not in path:
                matches = sorted(set([p for p in out if Path(p).name == path] +
                    [p.relative_to(vault).as_posix() for p in vault.rglob(path)]))
                if len(matches) != 1:
                    raise ValueError(f"Ambiguous or missing note in {name}: {target}")
                path = matches[0]
            target_data = content(path)
            if anchor and anchor not in heading_text(target_data.decode()):
                raise ValueError(f"Missing Obsidian heading in {name}: {target}")
            count += 1
    return count


def prepare(stage, vaults):
    out = build(vaults[0])
    manifest = {"vaults": {}, "sources": SOURCES, "files": {}}
    counts = {}
    for vault in vaults:
        counts[str(vault)] = validate(out, vault)
        before = {}
        for name in out:
            file = contained(vault, name)
            before[name] = digest(file.read_bytes()) if file.exists() else None
            # Never overwrite a different edit in the viewing peer.
            primary = vaults[0] / name
            if file.exists() and primary.exists() and file.read_bytes() != primary.read_bytes():
                raise ValueError(f"Vault peers differ; reconcile before export: {name}")
        manifest["vaults"][str(vault)] = before
    for name, data in out.items():
        file = contained(stage / "files", name)
        file.parent.mkdir(parents=True, exist_ok=True)
        file.write_bytes(data)
        manifest["files"][name] = digest(data)
    stage.mkdir(parents=True, exist_ok=True)
    (stage / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps({"staged": str(stage), "files": len(out), "vault_links_checked": counts}, indent=2))


def apply(stage):
    manifest = json.loads((stage / "manifest.json").read_text())
    out = {name: contained(stage / "files", name).read_bytes() for name in manifest["files"]}
    for name, data in out.items():
        if digest(data) != manifest["files"][name]:
            raise ValueError(f"Prepared file changed: {name}")
    for name, expected in manifest["sources"].items():
        if digest(contained(REPO, name).read_bytes()) != expected:
            raise ValueError(f"Repository source changed; regenerate: {name}")
    for root, before in manifest["vaults"].items():
        vault = Path(root)
        validate(out, vault)
        for name, expected in before.items():
            file = contained(vault, name)
            actual = digest(file.read_bytes()) if file.exists() else None
            if actual not in (expected, manifest["files"][name]):
                raise ValueError(f"Vault edit since preparation; preserved: {file}")
    changed = 0
    for root in manifest["vaults"]:
        for name, data in out.items():
            file = contained(Path(root), name)
            if file.exists() and file.read_bytes() == data:
                continue
            file.parent.mkdir(parents=True, exist_ok=True)
            file.write_bytes(data)
            changed += 1
    for root in manifest["vaults"]:
        for name, expected in manifest["files"].items():
            if digest((Path(root) / name).read_bytes()) != expected:
                raise ValueError(f"Installed copy differs: {root}/{name}")
    print(f"Applied {changed} file updates; both vault copies match the validated bundle.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stage", type=Path, required=True)
    parser.add_argument("--vault", type=Path, action="append")
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    if args.apply:
        apply(args.stage.resolve())
    elif args.vault:
        prepare(args.stage.resolve(), [p.resolve() for p in args.vault])
    else:
        parser.error("--vault is required when preparing a bundle")


if __name__ == "__main__":
    main()
