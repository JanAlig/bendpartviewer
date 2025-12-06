# -*- coding: utf-8 -*-
"""
Bendpart Visualizer by Jan Alig

Funktionen:

- .bendpart (gzip+XML) laden
- Aussen- und Innenkonturen anzeigen
- Biegelinien:
  * Winkel < 0: rot gestrichelt
  * Winkel > 0: blau punktiert
  * Winkel = 0: blau gestrichelt
  * Winkeltext horizontal, mit weissem Hintergrund
  * Werkzeuge:
      - Default-Kombi: NICHT auf der Biegelinie angezeigt
      - Abweichende Kombis: O:/U: auf der Biegelinie, mit farbigem Hintergrund
- Kopfzeile: "Abwicklung – Datei: NAME" (fett)
- Unter den Buttons: Dicke, Material, Default-Ober-/Unterwerkzeug
  + Hinweis auf Anzahl spezieller Kombis
- Messen:
  * "Messen": Abstand zwischen zwei Linien (kürzester Weg), Bemassung grün
    - 4 Klicks: Linie1, Linie2, Masslinien-Position, Text-Position
  * "Punktmessung": direkter Abstand zwischen 2 Punkten
- Text + / Text -: ändert NUR Winkeltexte und Bemassungstexte
- Mausrad: Zoom (rein/raus, zentriert auf Maus)
- Pan (Verschieben): über die Standard-Toolbar

Aufruf:
    python BendPartViewer.py
    python BendPartViewer.py pfad\\teil.bendpart
    python BendPartViewer.py pfad\\ordner   (öffnet Dialog in diesem Ordner)
"""

import gzip
import math
import os
import sys
import xml.etree.ElementTree as ET

import matplotlib.pyplot as plt
from matplotlib.widgets import Button
import matplotlib as mpl

import tkinter as tk
from tkinter import filedialog

# UI Farben
BTN_FACE = "#4a90e2"   # Button normal
BTN_HOVER = "#6bb6ff"  # Button Hover
BTN_TEXT = "white"     # Button-Text
BG_COLOR = "#303030"   # Hintergrund dunkel

# Globale Styles
mpl.rcParams["figure.facecolor"] = BG_COLOR
mpl.rcParams["axes.facecolor"] = BG_COLOR

# globale Textgrösse nur für Winkel- und Masstexte
TEXT_SIZE = 8.0


# ------------------------------------------------------------
# .bendpart laden & Namespace entfernen
# ------------------------------------------------------------

def load_bendpart(path):
    # kann gzip oder plain XML sein
    with open(path, "rb") as f:
        raw = f.read()
    if raw.startswith(b"\x1f\x8b"):
        data = gzip.decompress(raw)
    else:
        data = raw
    root = ET.fromstring(data)
    strip_namespaces(root)
    return root


def strip_namespaces(elem):
    for e in elem.iter():
        if "}" in e.tag:
            e.tag = e.tag.split("}", 1)[1]


# ------------------------------------------------------------
# Geometrie & Bulge
# ------------------------------------------------------------

def arc_points(P0, P1, bulge, segments=24):
    """
    Erzeugt eine Punktliste für einen Kreisbogen zwischen P0 und P1
    anhand des Bulge-Werts.

    Bulge-Semantik (DXF/Bendpart):
        B = tan(theta / 4)
        theta = Mittelpunktswinkel (Vorzeichen → Richtung)
        Bulge gehört zum START-Vertex eines Segments.
    """
    x0, y0 = P0
    x1, y1 = P1
    b = float(bulge)

    # kein Bogen
    if abs(b) < 1e-9:
        return [P0, P1]

    theta = 4.0 * math.atan(b)  

    cdx, cdy = x1 - x0, y1 - y0
    c_len = math.hypot(cdx, cdy)
    if c_len < 1e-9:
        return [P0]

    sin_half = math.sin(theta / 2.0)
    if abs(sin_half) < 1e-9:
        return [P0, P1]

    # Radius
    R = abs(c_len / (2.0 * sin_half))

    # Sehnenmittelpunkt
    mx, my = (x0 + x1) / 2.0, (y0 + y1) / 2.0

    # Normale (linke Seite)
    nx, ny = -cdy / c_len, cdx / c_len
    if b < 0:
        nx, ny = -nx, -ny

    # Abstand vom Sehnenmittelpunkt zum Kreismittelpunkt
    h_sq = max(R * R - (c_len * c_len) / 4.0, 0.0)
    h = math.sqrt(h_sq)

    cx, cy = mx + nx * h, my + ny * h

    # Startwinkel
    a0 = math.atan2(y0 - cy, x0 - cx)

    # Anzahl Segmente abhängig vom Winkel
    segs = max(12, int(segments * abs(theta) / math.pi))

    pts = []
    for i in range(segs + 1):
        t = i / segs
        a = a0 + t * theta
        px = cx + R * math.cos(a)
        py = cy + R * math.sin(a)
        pts.append((px, py))
    return pts


def build_poly_from_vertices(verts, segments=24):
    """
    Baut aus einer Liste von <Vertex>-Elementen eine geschlossene Polylinie,
    wobei Bulges als Bögen approximiert werden.

    Annahmen:
      - Kontur ist GESCHLOSSEN:
          * Segment von Vertex[i] -> Vertex[i+1]
          * plus Segment von letztem Vertex -> erstem Vertex
      - Bulge-Wert steht jeweils am START-Vertex eines Segments.
      - Location = "X Y" in mm.
    """
    pts = []
    n = len(verts)
    if n == 0:
        return pts

    if n == 1:
        loc0 = verts[0].get("Location")
        if loc0:
            try:
                x0, y0 = map(float, loc0.split()[:2])
                pts.append((x0, y0))
            except Exception:
                pass
        return pts

    for i in range(n):
        v0 = verts[i]
        v1 = verts[(i + 1) % n]

        loc0 = v0.get("Location")
        loc1 = v1.get("Location")
        if not loc0 or not loc1:
            continue

        try:
            x0, y0 = map(float, loc0.split()[:2])
            x1, y1 = map(float, loc1.split()[:2])
        except Exception:
            continue

        bulge_str = v0.get("Bulge")
        if bulge_str is None:
            b = 0.0
        else:
            try:
                b = float(bulge_str)
            except Exception:
                b = 0.0

        if not pts:
            pts.append((x0, y0))

        if abs(b) < 1e-9:
            if pts[-1] != (x1, y1):
                pts.append((x1, y1))
        else:
            arc_pts = arc_points((x0, y0), (x1, y1), b, segments=segments)
            if not arc_pts:
                continue
            pts.extend(arc_pts[1:])

    if pts and (pts[0][0] != pts[-1][0] or pts[0][1] != pts[-1][1]):
        pts.append(pts[0])

    return pts


# ------------------------------------------------------------
# Konturen aus Bendpart
# ------------------------------------------------------------

def parse_contours(root):
    """
    Liest alle äußeren UND inneren Konturen aus.
    Rückgabe: Liste von Dicts: {"points": [...], "type": "outer"/"inner"}.
    """
    contours = []
    bsm_root = root.find(".//BendSurfaceModels")
    if bsm_root is None:
        return contours

    for model in bsm_root.findall("BendSurfaceModel"):
        bend_surfaces = model.find("BendSurfaces")
        if bend_surfaces is None:
            continue

        for surf in bend_surfaces.findall("BendSurface"):
            # Außenkontur
            oc = surf.find("OuterContour")
            if oc is not None:
                verts_parent = oc.find("Vertices")
                if verts_parent is not None:
                    verts = verts_parent.findall("Vertex")
                    if len(verts) >= 2:
                        pts = build_poly_from_vertices(verts, segments=64)
                        if len(pts) >= 2:
                            contours.append({"points": pts, "type": "outer"})

            # Innenkonturen
            ics = surf.find("InnerContours")
            if ics is None:
                continue

            for ic in ics:
                if ic.tag not in ("InnerContour", "Contour"):
                    continue
                verts_parent = ic.find("Vertices")
                if verts_parent is None:
                    continue
                verts = verts_parent.findall("Vertex")
                if not verts:
                    continue

                pts = build_poly_from_vertices(verts, segments=64)
                if len(pts) >= 2:
                    contours.append({"points": pts, "type": "inner"})

    return contours


# ------------------------------------------------------------
# Biegelinien aus Bendpart + Werkzeuge
# ------------------------------------------------------------

def parse_bend_lines(root, meta):
    """
    Biegelinien-Geometrie (Start/Ende + Winkel) UND pro BendId die
    verwendeten Ober-/Unterwerkzeuge (upper_tool / lower_tool).

    Zusätzlich markieren wir pro Biegelinie, ob die Werkzeugkombi
    der Default-Kombi entspricht (is_default_combo).
    """
    bend_lines = []

    default_ut = meta.get("upper_tool")
    default_lt = meta.get("lower_tool")

    # Tool-IDs -> Toolnamen
    upper_map = {}
    lower_map = {}

    for elem in root.iter():
        if elem.tag == "Tool":
            uri = None
            tid = None
            for k, v in elem.attrib.items():
                if k.endswith("uri"):
                    uri = v
                if k.endswith("id"):
                    tid = v
            if uri and tid:
                if "/UpperTools/" in uri:
                    name = uri.split("/")[-1].split("#")[0]
                    upper_map[tid] = name
                elif "/LowerTools/" in uri:
                    name = uri.split("/")[-1].split("#")[0]
                    lower_map[tid] = name

    # BendProcess -> Tool-IDs & Namen
    bend_tools = {}  # BendId -> (upper_name, lower_name)
    bp_root = root.find(".//BendProcesses")
    nsref = "{http://www.bystronic.com/bysoft7/scheme}ref"

    if bp_root is not None:
        for bp in bp_root.findall("BendProcess"):
            bid = bp.attrib.get("BendId")
            if not bid:
                continue

            ut_ref = lt_ref = None
            ut_elem = bp.find("UpperTool")
            if ut_elem is not None:
                ut_ref = ut_elem.attrib.get(nsref)
            lt_elem = bp.find("LowerTool")
            if lt_elem is not None:
                lt_ref = lt_elem.attrib.get(nsref)

            upper_name = upper_map.get(ut_ref)
            lower_name = lower_map.get(lt_ref)
            bend_tools[bid] = (upper_name, lower_name)

    # Geometrie + Toolnamen
    bsm_root = root.find(".//BendSurfaceModels")
    if bsm_root is None:
        return bend_lines

    for model in bsm_root.findall("BendSurfaceModel"):
        bl_root = model.find("BendLines")
        if bl_root is None:
            continue

        for bl in bl_root.findall("BendSurfaceBendLine"):
            bend_id = bl.get("BendId")
            bend_angle = float(bl.get("BendAngle", "0") or 0)
            lines = bl.find("Lines")
            if lines is None:
                continue

            if bend_id in bend_tools:
                upper_name, lower_name = bend_tools[bend_id]
            else:
                upper_name = lower_name = None

            # Fallback auf Defaults, wenn leer
            if upper_name is None:
                upper_name = default_ut
            if lower_name is None:
                lower_name = default_lt

            is_default_combo = (upper_name == default_ut and lower_name == default_lt)

            for l in lines.findall("BendSurfaceLine"):
                start = l.get("Start")
                end = l.get("End")
                if not start or not end:
                    continue
                sx, sy = map(float, start.split())
                ex, ey = map(float, end.split())

                bend_lines.append(
                    {
                        "kind": "bend",
                        "bend_id": bend_id,
                        "angle": bend_angle,
                        "start": (sx, sy),
                        "end": (ex, ey),
                        "upper_tool": upper_name,
                        "lower_tool": lower_name,
                        "is_default_combo": is_default_combo,
                    }
                )

    return bend_lines


# ------------------------------------------------------------
# Meta-Infos
# ------------------------------------------------------------

def parse_meta(root):
    """Material, Dicke, Ober-/Unterwerkzeug (Default) aus der Bendpart lesen."""
    # Material
    material = None
    mat_elem = root.find(".//Material")
    if mat_elem is not None:
        uri = None
        for k, v in mat_elem.attrib.items():
            if k.endswith("uri"):
                uri = v
                break
        if uri:
            core = uri.split("/")[-1]
            material = core.split("#")[0]

    # Dicke
    thickness = None

    th_elem = root.find(".//Thickness")
    if th_elem is not None:
        if "Value" in th_elem.attrib:
            try:
                thickness = float(th_elem.attrib["Value"])
            except Exception:
                thickness = None
        if thickness is None and th_elem.text:
            try:
                thickness = float(th_elem.text.strip())
            except Exception:
                thickness = None

    if thickness is None:
        sh_elem = root.find(".//SheetThickness")
        if sh_elem is not None:
            if "Value" in sh_elem.attrib:
                try:
                    thickness = float(sh_elem.attrib["Value"])
                except Exception:
                    thickness = None
            elif sh_elem.text:
                try:
                    thickness = float(sh_elem.text.strip())
                except Exception:
                    thickness = None

    if thickness is None:
        for elem in root.iter():
            for k, v in elem.attrib.items():
                if k.lower() == "thickness":
                    try:
                        thickness = float(v)
                        break
                    except Exception:
                        pass
            if thickness is not None:
                break

    if thickness is None:
        for elem in root.iter():
            if "thickness" in elem.tag.lower():
                for k, v in elem.attrib.items():
                    if k.lower() in ("value", "thickness", "th"):
                        try:
                            thickness = float(v)
                            break
                        except Exception:
                            pass
                if thickness is None and elem.text:
                    try:
                        thickness = float(elem.text.strip())
                    except Exception:
                        pass
                if thickness is not None:
                    break

    # Default Ober-/Unterwerkzeug
    upper_tool = None
    up_elem = root.find(".//UpperTool")
    if up_elem is not None:
        uri = None
        for k, v in up_elem.attrib.items():
            if k.endswith("uri"):
                uri = v
                break
        if uri:
            core = uri.split("/")[-1]
            upper_tool = core.split("#")[0]

    lower_tool = None
    low_elem = root.find(".//LowerTool")
    if low_elem is not None:
        uri = None
        for k, v in low_elem.attrib.items():
            if k.endswith("uri"):
                uri = v
                break
        if uri:
            core = uri.split("/")[-1]
            lower_tool = core.split("#")[0]

    return {
        "material": material,
        "thickness": thickness,
        "upper_tool": upper_tool,
        "lower_tool": lower_tool,
    }


# ------------------------------------------------------------
# Geometrie-Helfer (Segmente, Messen)
# ------------------------------------------------------------

def build_all_segments(contours, bend_lines):
    """
    Erzeugt eine Liste ALLER Segmente:
      - Aussen- und Innenkonturen (kind='contour')
      - Biegelinien (kind='bend')
    """
    segs = []

    for ci, c in enumerate(contours):
        poly = c["points"]
        n = len(poly)
        if n < 2:
            continue
        for i in range(n - 1):  # Polygon ist bereits geschlossen
            a = poly[i]
            b = poly[i + 1]
            segs.append(
                {
                    "kind": "contour",
                    "id": f"C{ci}_{i}",
                    "start": a,
                    "end": b,
                }
            )

    segs.extend(
        {
            "kind": "bend",
            "id": bl.get("bend_id", ""),
            "start": bl["start"],
            "end": bl["end"],
        }
        for bl in bend_lines
    )

    return segs


def distance_point_to_segment(px, py, ax, ay, bx, by):
    vx, vy = bx - ax, by - ay
    wx, wy = px - ax, py - ay
    seg_len2 = vx * vx + vy * vy
    if seg_len2 == 0:
        return math.hypot(px - ax, py - ay), (ax, ay)
    t = (wx * vx + wy * vy) / seg_len2
    t_clamped = max(0.0, min(1.0, t))
    cx = ax + t_clamped * vx
    cy = ay + t_clamped * vy
    return math.hypot(px - cx, py - cy), (cx, cy)


def find_nearest_segment(click_point, segments):
    px, py = click_point
    best = None
    best_dist = None
    best_point_on_seg = None
    for seg in segments:
        (sx, sy) = seg["start"]
        (ex, ey) = seg["end"]
        d, cp = distance_point_to_segment(px, py, sx, sy, ex, ey)
        if best_dist is None or d < best_dist:
            best_dist = d
            best = seg
            best_point_on_seg = cp
    return best, best_point_on_seg


def closest_points_between_segments(a1, a2, b1, b2, samples=25):
    best = None
    best_dist = None

    ax1, ay1 = a1
    ax2, ay2 = a2
    bx1, by1 = b1
    bx2, by2 = b2

    for i in range(samples + 1):
        t = i / samples
        px = ax1 + t * (ax2 - ax1)
        py = ay1 + t * (ay2 - ay1)
        d, cp = distance_point_to_segment(px, py, bx1, by1, bx2, by2)
        if best_dist is None or d < best_dist:
            best_dist = d
            best = ((px, py), cp)

    for i in range(samples + 1):
        t = i / samples
        px = bx1 + t * (bx2 - bx1)
        py = by1 + t * (by2 - by1)
        d, cp = distance_point_to_segment(px, py, ax1, ay1, ax2, ay2)
        if best_dist is None or d < best_dist:
            best_dist = d
            best = (cp, (px, py))

    (p1, p2) = best
    return p1, p2, best_dist


# ------------------------------------------------------------
# Zeichnen (inkl. Werkzeuglogik)
# ------------------------------------------------------------

def draw_part(ax, contours, bend_lines, dim_texts, meta):
    """
    Konturen + Biegelinien + Winkel-/Tooltexte zeichnen.

    Tools:
      - Default-Kombi (meta["upper_tool"]/meta["lower_tool"]) → nur Winkel
      - Abweichende Kombis → Winkel + O:/U:, mit farbigem Hintergrund
    """
    global TEXT_SIZE

    default_ut = meta.get("upper_tool")
    default_lt = meta.get("lower_tool")

    # alle nicht-default Kombis sammeln
    special_combos = set()
    for bl in bend_lines:
        if not bl.get("is_default_combo", False):
            ut = bl.get("upper_tool")
            lt = bl.get("lower_tool")
            if ut or lt:
                special_combos.add((ut, lt))

    special_combos = sorted(special_combos, key=lambda c: ((c[0] or ""), (c[1] or "")))
    palette = [
        "#ffe6cc",  # helles orange
        "#e0f7e9",  # helles grün
        "#e0ecff",  # helles blau
        "#ffe6f2",  # helles pink
        "#f4f4d7",  # helles gelb
    ]
    combo_colors = {}
    for i, combo in enumerate(special_combos):
        combo_colors[combo] = palette[i % len(palette)]

    # Aussen- und Innenkonturen
    for c in contours:
        poly = c["points"]
        if len(poly) < 2:
            continue
        xs = [p[0] for p in poly]
        ys = [p[1] for p in poly]

        if c["type"] == "outer":
            # Blechfläche
            ax.fill(xs, ys,
                    facecolor="#e0e0e0", edgecolor="black", linewidth=0.8)
        else:
            # Löcher → dunkel wie Hintergrund, aber mit hellem Rand
            ax.fill(xs, ys,
                    facecolor=BG_COLOR, edgecolor="#dddddd", linewidth=0.7)


    # Biegelinien + Winkel + Tools
    seen_ids = set()
    for bl in bend_lines:
        sx, sy = bl["start"]
        ex, ey = bl["end"]
        angle = bl["angle"]
        bid = bl["bend_id"]

        if angle < 0:
            color = "#ff5555"
            style = "--"
        elif angle > 0:
            color = "#66aaff"
            style = ":"
        else:
            color = "#66aaff"
            style = "--"

        ax.plot([sx, ex], [sy, ey], color=color, linestyle=style, linewidth=1.5)

        if bid not in seen_ids:
            seen_ids.add(bid)
            mx, my = (sx + ex) / 2.0, (sy + ey) / 2.0
            dx, dy = ex - sx, ey - sy
            length = math.hypot(dx, dy)
            if length > 0:
                tx, ty = dx / length, dy / length
                nx, ny = -ty, tx
            else:
                tx, ty = 1.0, 0.0
                nx, ny = 0.0, 1.0

            text_x = mx + tx * 8.0 + nx * 5.0
            text_y = my + ty * 8.0 + ny * 5.0

            sign = "+" if angle > 0 else "-" if angle < 0 else "±"
            text_str = f"{sign}{abs(angle):.1f}°"

            ut = bl.get("upper_tool")
            lt = bl.get("lower_tool")
            combo = (ut, lt)

            # nur anzeigen, wenn NICHT Default-Kombi
            show_tools = not bl.get("is_default_combo", False) and (ut or lt)
            if show_tools:
                tool_lines = []
                if ut:
                    tool_lines.append(f"{ut}")
                if lt:
                    tool_lines.append(f"{lt}")
                if tool_lines:
                    text_str += "\n" + " / ".join(tool_lines)
                facecolor = combo_colors.get(combo, "#f5f5f5")
            else:
                facecolor = "white"

            t = ax.text(
                text_x,
                text_y,
                text_str,
                fontsize=TEXT_SIZE,
                color=color,
                rotation=0.0,
                rotation_mode="anchor",
                ha="center",
                va="center",
                bbox=dict(
                    facecolor=facecolor,
                    edgecolor="none",
                    alpha=0.9,
                    boxstyle="round,pad=0.15",
                ),
            )
            dim_texts.append(t)


# ------------------------------------------------------------
# Dateiauswahl
# ------------------------------------------------------------

def choose_bendpart_file(initial_dir=None):
    root = tk.Tk()
    root.withdraw()
    if initial_dir is None:
        initial_dir = os.getcwd()
    filename = filedialog.askopenfilename(
        initialdir=initial_dir,
        filetypes=[("Bendpart-Dateien", "*.bendpart"), ("Alle Dateien", "*.*")],
        title="Bendpart-Datei auswählen",
    )
    root.destroy()
    return filename if filename else None


# ------------------------------------------------------------
# Interaktive GUI
# ------------------------------------------------------------

def interactive_dim(initial_path):
    global TEXT_SIZE

    state = {
        "path": initial_path,
        "contours": [],
        "bend_lines": [],
        "segments": [],
        "bounds": None,
        "diag": None,
        "meta": {},
    }

    def load_geometry(path):
        try:
            root = load_bendpart(path)
        except Exception as e:
            print(f"Fehler beim Laden von {path}: {e}")
            return False

        contours = parse_contours(root)
        meta = parse_meta(root)
        bend_lines = parse_bend_lines(root, meta)
        segments = build_all_segments(contours, bend_lines)

        xs = [p[0] for c in contours for p in c["points"]]
        ys = [p[1] for c in contours for p in c["points"]]
        if xs and ys:
            min_x, max_x = min(xs), max(xs)
            min_y, max_y = min(ys), max(ys)
            state["bounds"] = (min_x, max_x, min_y, max_y)
            dx = max_x - min_x
            dy = max_y - min_y
            state["diag"] = math.hypot(dx, dy)
        else:
            state["bounds"] = None
            state["diag"] = None

        state["path"] = path
        state["contours"] = contours
        state["bend_lines"] = bend_lines
        state["segments"] = segments
        state["meta"] = meta
        print(f"Geladen: {path}")
        return True

    if not load_geometry(initial_path):
        return

    fig, ax = plt.subplots(figsize=(10, 7))
    
    plt.subplots_adjust(bottom=0.19, top=0.95)

    try:
        fig.canvas.manager.set_window_title("Bendpart Visualizer by Jan Alig")
    except Exception:
        pass

    dim_texts = []   # Winkel- und Masstexte
    dim_artists = [] # alle Bemassungs-Linien/Marker/Texte

    # Info unter den Buttons
    info_text = fig.text(
        0.5,
        0.035,
        "",
        fontsize=11.0,
        ha="center",
        va="top",
        color="white",
        transform=fig.transFigure,
    )

    def update_info_text():
        meta = state["meta"] or {}
        th = meta.get("thickness")
        mat = meta.get("material") or "-"
        up = meta.get("upper_tool") or "-"
        low = meta.get("lower_tool") or "-"

        th_str = f"{th:.1f} mm" if isinstance(th, (int, float)) else "-"

        # Anzahl spezieller Kombis (nicht Default)
        special_combos = set()
        for bl in state["bend_lines"]:
            if not bl.get("is_default_combo", False):
                ut = bl.get("upper_tool")
                lt = bl.get("lower_tool")
                if ut or lt:
                    special_combos.add((ut, lt))

        txt = (
            f"Dicke: {th_str}    Material: {mat}    "
            f"Oberwerkzeug: {up}   Unterwerkzeug: {low}"
        )
        if special_combos:
            txt += f"    spezielle Kombis: {len(special_combos)}"

        info_text.set_text(txt)

    def apply_bounds():
        if not state["bounds"]:
            return
        min_x, max_x, min_y, max_y = state["bounds"]
        dx = max_x - min_x
        dy = max_y - min_y
        pad_x = dx * 0.05 if dx > 0 else 5.0
        pad_y = dy * 0.10 if dy > 0 else 2.0
        ax.set_xlim(min_x - pad_x, max_x + pad_x)
        ax.set_ylim(min_y - pad_y, max_y + pad_y)

    def style_axes():
        ax.set_facecolor(BG_COLOR)
        ax.xaxis.label.set_color("white")
        ax.yaxis.label.set_color("white")
        ax.tick_params(axis="x", colors="white")
        ax.tick_params(axis="y", colors="white")
        for spine in ax.spines.values():
            spine.set_color("white")

    def redraw_geometry():
        dim_texts.clear()
        ax.cla()
        draw_part(ax, state["contours"], state["bend_lines"], dim_texts, state["meta"])
        apply_bounds()
        ax.set_aspect("equal")

        ax.set_xlabel("X [mm]")
        ax.set_ylabel("Y [mm]")

        title_str = f"Abwicklung – Datei: {os.path.basename(state['path'])}"
        ax.set_title(title_str, fontweight="bold", color="white")

        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)

        style_axes()
        update_info_text()

    redraw_geometry()

    status_text = fig.text(
        0.02, 0.02,
        "Messen aus",
        fontsize=7.0,
        color="white",
        transform=fig.transFigure
    )

    def set_status(msg):
        status_text.set_text(msg)
        fig.canvas.draw_idle()

    # Snap-Funktion für Punktmessung (Ende + Mittelpunkt)
    def snap_point(x, y):
        segs = state["segments"]
        diag = state["diag"] or 0.0
        if not segs:
            return x, y, False

        snap_radius = max(2.0, (diag * 0.02 if diag > 0 else 10.0))

        best = None
        best_dist = None
        for seg in segs:
            sx, sy = seg["start"]
            ex, ey = seg["end"]
            mx, my = (sx + ex) / 2.0, (sy + ey) / 2.0
            for px, py in ((sx, sy), (ex, ey), (mx, my)):
                d = math.hypot(x - px, y - py)
                if best_dist is None or d < best_dist:
                    best_dist = d
                    best = (px, py)

        if best is not None and best_dist <= snap_radius:
            return best[0], best[1], True
        return x, y, False

    # Zustände
    measure = {
        "enabled": False,
        "step": 0,
        "seg1": None,
        "seg2": None,
        "p1_base": None,
        "p2_base": None,
        "mid_base": None,
        "dist": None,
        "dim_p1": None,
        "dim_p2": None,
    }

    point_measure = {
        "enabled": False,
        "step": 0,
        "p1": None,
    }

    # Buttons – etwas kleiner & tiefer
    btn_h = 0.05
    btn_y = 0.08

    ax_open = fig.add_axes([0.03, btn_y, 0.14, btn_h])
    btn_open = Button(ax_open, "Öffnen", color=BTN_FACE, hovercolor=BTN_HOVER)
    btn_open.label.set_color(BTN_TEXT)

    ax_measure = fig.add_axes([0.19, btn_y, 0.14, btn_h])
    btn_measure = Button(ax_measure, "Messen\nLinie zu Linie",
                         color=BTN_FACE, hovercolor=BTN_HOVER)
    btn_measure.label.set_color(BTN_TEXT)

    ax_pmeasure = fig.add_axes([0.35, btn_y, 0.14, btn_h])
    btn_pmeasure = Button(ax_pmeasure, "Punktmessung\nExperimentell",
                          color=BTN_FACE, hovercolor=BTN_HOVER)
    btn_pmeasure.label.set_color(BTN_TEXT)

    ax_reset = fig.add_axes([0.51, btn_y, 0.14, btn_h])
    btn_reset = Button(ax_reset, "Bemassung\nlöschen",
                       color=BTN_FACE, hovercolor=BTN_HOVER)
    btn_reset.label.set_color(BTN_TEXT)

    ax_tplus = fig.add_axes([0.67, btn_y, 0.13, btn_h])
    btn_tplus = Button(ax_tplus, "Text +",
                       color=BTN_FACE, hovercolor=BTN_HOVER)
    btn_tplus.label.set_color(BTN_TEXT)

    ax_tminus = fig.add_axes([0.82, btn_y, 0.13, btn_h])
    btn_tminus = Button(ax_tminus, "Text -",
                        color=BTN_FACE, hovercolor=BTN_HOVER)
    btn_tminus.label.set_color(BTN_TEXT)

    def apply_text_size():
        for t in dim_texts:
            t.set_fontsize(TEXT_SIZE)
        fig.canvas.draw_idle()

    def toggle_measure(event):
        # Punktmessung ausschalten
        if point_measure["enabled"]:
            point_measure["enabled"] = False
            point_measure["step"] = 0
            btn_pmeasure.label.set_text("Punktmessung")

        if not measure["enabled"]:
            measure["enabled"] = True
            measure["step"] = 1
            measure["seg1"] = None
            measure["seg2"] = None
            measure["p1_base"] = None
            measure["p2_base"] = None
            measure["mid_base"] = None
            measure["dist"] = None
            measure["dim_p1"] = None
            measure["dim_p2"] = None
            btn_measure.label.set_text("Messen (AN)")
            btn_measure.label.set_color(BTN_TEXT)
            set_status("Messen: Punkt 1 (Linie) auswählen")
        else:
            measure["enabled"] = False
            measure["step"] = 0
            btn_measure.label.set_text("Messen")
            btn_measure.label.set_color(BTN_TEXT)
            set_status("Messen aus")

    def toggle_point_measure(event):
        # Linienmessung ausschalten
        if measure["enabled"]:
            measure["enabled"] = False
            measure["step"] = 0
            btn_measure.label.set_text("Messen")
            btn_measure.label.set_color(BTN_TEXT)

        if not point_measure["enabled"]:
            point_measure["enabled"] = True
            point_measure["step"] = 1
            point_measure["p1"] = None
            btn_pmeasure.label.set_text("Punktmessung (AN)")
            btn_pmeasure.label.set_color(BTN_TEXT)
            set_status("Punktmessung: Punkt 1 auswählen")
        else:
            point_measure["enabled"] = False
            point_measure["step"] = 0
            btn_pmeasure.label.set_text("Punktmessung")
            btn_pmeasure.label.set_color(BTN_TEXT)
            set_status("Punktmessung aus")

    def reset_dims(event):
        for art in dim_artists:
            try:
                art.remove()
            except Exception:
                pass
        dim_artists.clear()
        fig.canvas.draw_idle()

        if measure["enabled"]:
            measure["step"] = 1
            set_status("Messen: Punkt 1 auswählen")
        elif point_measure["enabled"]:
            point_measure["step"] = 1
            set_status("Punktmessung: Punkt 1 auswählen")
        else:
            set_status("Messen aus")

    def text_plus(event):
        global TEXT_SIZE
        TEXT_SIZE += 1.0
        apply_text_size()

    def text_minus(event):
        global TEXT_SIZE
        TEXT_SIZE = max(4.0, TEXT_SIZE - 1.0)
        apply_text_size()

    def open_new_file(event):
        initial_dir = os.path.dirname(state["path"]) if state["path"] else None
        new_path = choose_bendpart_file(initial_dir)
        if not new_path:
            return

        if not load_geometry(new_path):
            return

        for art in dim_artists:
            try:
                art.remove()
            except Exception:
                pass
        dim_artists.clear()

        measure.update(
            {
                "enabled": False,
                "step": 0,
                "seg1": None,
                "seg2": None,
                "p1_base": None,
                "p2_base": None,
                "mid_base": None,
                "dist": None,
                "dim_p1": None,
                "dim_p2": None,
            }
        )
        point_measure.update(
            {
                "enabled": False,
                "step": 0,
                "p1": None,
            }
        )
        btn_measure.label.set_text("Messen")
        btn_measure.label.set_color(BTN_TEXT)
        btn_pmeasure.label.set_text("Punktmessung")
        btn_pmeasure.label.set_color(BTN_TEXT)
        set_status("Messen aus")

        redraw_geometry()
        apply_text_size()

    btn_open.on_clicked(open_new_file)
    btn_measure.on_clicked(toggle_measure)
    btn_pmeasure.on_clicked(toggle_point_measure)
    btn_reset.on_clicked(reset_dims)
    btn_tplus.on_clicked(text_plus)
    btn_tminus.on_clicked(text_minus)

    # Scroll-Zoom
    def on_scroll(event):
        if event.inaxes != ax:
            return

        zoom = 0.9 if event.button == "up" else 1.1

        xlim = ax.get_xlim()
        ylim = ax.get_ylim()
        xdata, ydata = event.xdata, event.ydata
        if xdata is None or ydata is None:
            return

        new_xrange = (xdata - (xdata - xlim[0]) * zoom,
                    xdata + (xlim[1] - xdata) * zoom)
        new_yrange = (ydata - (ydata - ylim[0]) * zoom,
                    ydata + (ylim[1] - ydata) * zoom)

        ax.set_xlim(new_xrange)
        ax.set_ylim(new_yrange)
        fig.canvas.draw_idle()




    cid_scroll = fig.canvas.mpl_connect("scroll_event", on_scroll)

    # Klick-Logik
    def on_click(event):
        if event.inaxes != ax or event.button != 1:
            return

        toolbar = getattr(getattr(fig.canvas.manager, "toolbar", None), "mode", "")
        if toolbar:
            # wenn Toolbar (Pan/Zoom) aktiv -> unsere Logik aussetzen
            return

        x, y = event.xdata, event.ydata
        if x is None or y is None:
            return

        # --- Linien-Messung (Messen) ---
        if measure["enabled"]:
            step = measure["step"]

            if step == 1:
                seg1, cp1 = find_nearest_segment((x, y), state["segments"])
                if seg1 is None:
                    return
                measure["seg1"] = seg1

                m = ax.plot(cp1[0], cp1[1], "o", color="orange", markersize=4)[0]
                dim_artists.append(m)

                measure["step"] = 2
                set_status("Messen: Punkt 2 (Linie) auswählen")
                fig.canvas.draw_idle()
                return

            if step == 2:
                seg2, cp2 = find_nearest_segment((x, y), state["segments"])
                if seg2 is None:
                    return
                measure["seg2"] = seg2

                m = ax.plot(cp2[0], cp2[1], "o", color="orange", markersize=4)[0]
                dim_artists.append(m)

                s1 = measure["seg1"]
                s2 = measure["seg2"]
                p1, p2, dist = closest_points_between_segments(
                    s1["start"], s1["end"], s2["start"], s2["end"]
                )
                measure["p1_base"] = p1
                measure["p2_base"] = p2
                measure["mid_base"] = ((p1[0] + p2[0]) / 2.0, (p1[1] + p2[1]) / 2.0)
                measure["dist"] = dist

                measure["step"] = 3
                set_status("Messen: Masslinie positionieren")
                fig.canvas.draw_idle()
                return

            if step == 3:
                p1_base = measure["p1_base"]
                p2_base = measure["p2_base"]
                mid_base = measure["mid_base"]
                dist = measure["dist"]
                if p1_base is None or p2_base is None or dist is None or dist == 0:
                    return

                s1 = measure["seg1"]
                sx0, sy0 = s1["start"]
                ex0, ey0 = s1["end"]
                dx, dy = ex0 - sx0, ey0 - sy0
                len1 = math.hypot(dx, dy)
                if len1 == 0:
                    vx = p2_base[0] - p1_base[0]
                    vy = p2_base[1] - p1_base[1]
                    lenv = math.hypot(vx, vy)
                    if lenv == 0:
                        return
                    tx, ty = -vy / lenv, vx / lenv
                else:
                    tx, ty = dx / len1, dy / len1

                vx = x - mid_base[0]
                vy = y - mid_base[1]
                t_param = vx * tx + vy * ty

                dim_p1 = (p1_base[0] + tx * t_param, p1_base[1] + ty * t_param)
                dim_p2 = (p2_base[0] + tx * t_param, p2_base[1] + ty * t_param)

                line = ax.plot(
                    [dim_p1[0], dim_p2[0]],
                    [dim_p1[1], dim_p2[1]],
                    color="#00aa00",
                    linewidth=0.8,
                )[0]
                dim_artists.append(line)

                ext1 = ax.plot(
                    [p1_base[0], dim_p1[0]],
                    [p1_base[1], dim_p1[1]],
                    color="#00aa00",
                    linewidth=0.5,
                )[0]
                ext2 = ax.plot(
                    [p2_base[0], dim_p2[0]],
                    [p2_base[1], dim_p2[1]],
                    color="#00aa00",
                    linewidth=0.5,
                )[0]
                dim_artists.extend([ext1, ext2])

                measure["dim_p1"] = dim_p1
                measure["dim_p2"] = dim_p2
                measure["step"] = 4
                set_status("Messen: Bemassung positionieren")
                fig.canvas.draw_idle()
                return

            if step == 4:
                dist = measure["dist"]
                if dist is None:
                    return

                txt = ax.text(
                    x,
                    y,
                    f"{dist:.1f} mm",
                    fontsize=TEXT_SIZE,
                    color="#00aa00",
                    rotation=0.0,
                    rotation_mode="anchor",
                    ha="center",
                    va="center",
                    bbox=dict(
                        facecolor="white",
                        edgecolor="none",
                        alpha=0.8,
                        boxstyle="round,pad=0.1",
                    ),
                )
                dim_artists.append(txt)
                dim_texts.append(txt)

                measure["step"] = 1
                set_status("Messen: Punkt 1 auswählen")
                fig.canvas.draw_idle()
                return

        # --- Punktmessung (gelb, mit Fang) ---
        if point_measure["enabled"]:
            step = point_measure["step"]

            if step == 1:
                sx, sy, _ = snap_point(x, y)
                point_measure["p1"] = (sx, sy)
                m = ax.plot(sx, sy, "o", color="yellow", markersize=4)[0]
                dim_artists.append(m)
                point_measure["step"] = 2
                set_status("Punktmessung: Punkt 2 auswählen")
                fig.canvas.draw_idle()
                return

            if step == 2:
                sx, sy, _ = snap_point(x, y)
                p1 = point_measure["p1"]
                if p1 is None:
                    return
                p2 = (sx, sy)

                line = ax.plot(
                    [p1[0], p2[0]],
                    [p1[1], p2[1]],
                    color="#ffcc00",
                    linewidth=0.8,
                )[0]
                dim_artists.append(line)

                midx = (p1[0] + p2[0]) / 2.0
                midy = (p1[1] + p2[1]) / 2.0
                vx = p2[0] - p1[0]
                vy = p2[1] - p1[1]
                lenv = math.hypot(vx, vy)
                if lenv > 0:
                    nx, ny = -vy / lenv, vx / lenv
                else:
                    nx, ny = 0.0, -1.0
                tx_pos = midx + nx * 5.0
                ty_pos = midy + ny * 5.0

                dist = math.hypot(p2[0] - p1[0], p2[1] - p1[1])
                txt = ax.text(
                    tx_pos,
                    ty_pos,
                    f"{dist:.1f} mm",
                    fontsize=TEXT_SIZE,
                    color="#ffcc00",
                    rotation=0.0,
                    rotation_mode="anchor",
                    ha="center",
                    va="center",
                    bbox=dict(
                        facecolor="white",
                        edgecolor="none",
                        alpha=0.8,
                        boxstyle="round,pad=0.1",
                    ),
                )
                dim_artists.append(txt)
                dim_texts.append(txt)

                point_measure["step"] = 1
                set_status("Punktmessung: Punkt 1 auswählen")
                fig.canvas.draw_idle()
                return

    cid_click = fig.canvas.mpl_connect("button_press_event", on_click)

    plt.show()

    fig.canvas.mpl_disconnect(cid_click)
    fig.canvas.mpl_disconnect(cid_scroll)


# ------------------------------------------------------------
# main
# ------------------------------------------------------------

def main():
    if len(sys.argv) < 2:
        path = choose_bendpart_file()
        if not path:
            print("Keine Datei gewählt, Programm beendet.")
            return
    else:
        arg = sys.argv[1]
        if os.path.isdir(arg):
            path = choose_bendpart_file(arg)
            if not path:
                print("Keine Datei gewählt, Programm beendet.")
                return
        else:
            path = arg

    interactive_dim(path)


if __name__ == "__main__":
    main()
