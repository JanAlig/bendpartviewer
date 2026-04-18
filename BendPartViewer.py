# -*- coding: utf-8 -*-
"""
Bendpart Visualizer by Jan Alig.

This module contains the full desktop viewer for Bendpart files.
It covers flat 2D drawing, folded 3D rendering, measurement tools,
and persistent user settings.

Usage examples:
    python BendPartViewer_V3.py
    python BendPartViewer_V3.py path\\to\\part.bendpart
    python BendPartViewer_V3.py path\\to\\folder
"""

import gzip
import importlib.machinery
import importlib.util
import json
import math
import os
import sys
import xml.etree.ElementTree as ET

from shapely.geometry import MultiPolygon, Polygon

import matplotlib.pyplot as plt
import matplotlib as mpl
import numpy as np
from PIL import Image, ImageTk
import vtk

import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from vtkmodules.util.numpy_support import vtk_to_numpy

sys.modules.setdefault("vtk", vtk)
sys.modules.setdefault("BendPartViewer_V3", sys.modules[__name__])

# Shared UI colors
BTN_FACE = "#4a90e2"   # default button color
BTN_HOVER = "#6bb6ff"  # hover state
BTN_TEXT = "white"     # button text
BG_COLOR = "#303030"   # dark workspace background

# Keep the Matplotlib surfaces visually aligned with the dark Tk UI.
mpl.rcParams["figure.facecolor"] = BG_COLOR
mpl.rcParams["axes.facecolor"] = BG_COLOR

# Shared text size for bend-angle labels and measurement labels.
TEXT_SIZE = 8.0
_VTK_FOLD_MODULE = None
SETTINGS_FILENAME = "bendpart_viewer_settings.json"
APP_ICON_FILENAME = "BPV_v3_icon.ico"
DEFAULT_SETTINGS = {
    "default_folder": "",
    "reverse_angle_display": False,
    "language": "de",
}

TRANSLATIONS = {
    "de": {
        "app_title": "Bendpart Visualizer by Jan Alig",
        "app_name": "Bendpart Visualizer",
        "no_file_loaded": "Keine Datei geladen",
        "angle_display": "Winkelanzeige",
        "inside_angle": "Innenwinkel",
        "outside_angle": "Aussenwinkel",
        "file": "Datei",
        "thickness": "Dicke",
        "material": "Material",
        "upper_tool": "Oberwerkzeug",
        "lower_tool": "Unterwerkzeug",
        "special_combos": "spezielle Kombis",
        "sheet_2d": "2D Abwicklung",
        "view_3d": "3D Ansicht",
        "file_and_view": "Datei & Ansicht",
        "text_group": "Text",
        "view_3d_loading": "3D Ansicht wird aufgebaut ...",
        "view_3d_waiting": "3D Ansicht wartet auf eine Datei",
        "status_measure_off": "Messen aus",
        "empty_canvas": "Keine Bendpart-Datei geladen\nMit 'Öffnen' eine Datei wählen",
        "open": "Öffnen",
        "center_view": "Ansicht zentrieren",
        "rotate_2d": "2D drehen",
        "settings": "Einstellungen",
        "larger_2d": "2D größer",
        "larger_3d": "3D größer",
        "measure": "Messen",
        "measure_active": "Messen aktiv",
        "point_measure": "Punktmessung",
        "point_measure_active": "Punktmessung aktiv",
        "clear_dimensions": "Bemaßung löschen",
        "text_plus": "Text +",
        "text_minus": "Text -",
        "settings_title": "Einstellungen",
        "default_folder": "Standardordner",
        "choose_folder": "Ordner wählen",
        "choose_default_folder": "Standardordner auswählen",
        "language": "Sprache",
        "german": "Deutsch",
        "english": "Englisch",
        "cancel": "Abbrechen",
        "save": "Speichern",
        "invalid_folder_title": "Ungültiger Ordner",
        "invalid_folder_msg": "Der Standardordner existiert nicht.",
        "bendpart_files": "Bendpart-Dateien",
        "all_files": "Alle Dateien",
        "choose_bendpart": "Bendpart-Datei auswählen",
        "load_error_title": "Fehler beim Laden",
        "file_loaded": "Datei geladen",
        "status_fit_2d": "2D Ansicht automatisch eingepasst",
        "status_rotate_2d": "2D Ansicht: {angle}°",
        "status_measure_pick_first": "Messen: Punkt 1 (Linie) auswählen",
        "status_measure_pick_second": "Messen: Punkt 2 (Linie) auswählen",
        "status_measure_line_pos": "Messen: Maßlinie positionieren",
        "status_measure_text_pos": "Messen: Bemaßung positionieren",
        "status_point_pick_first": "Punktmessung: Punkt 1 auswählen",
        "status_point_pick_second": "Punktmessung: Punkt 2 auswählen",
        "status_point_off": "Punktmessung aus",
    },
    "en": {
        "app_title": "Bendpart Visualizer by Jan Alig",
        "app_name": "Bendpart Visualizer",
        "no_file_loaded": "No file loaded",
        "angle_display": "Angle display",
        "inside_angle": "Inside angle",
        "outside_angle": "Outside angle",
        "file": "File",
        "thickness": "Thickness",
        "material": "Material",
        "upper_tool": "Upper tool",
        "lower_tool": "Lower tool",
        "special_combos": "special combos",
        "sheet_2d": "2D Flat Pattern",
        "view_3d": "3D View",
        "file_and_view": "File & View",
        "text_group": "Text",
        "view_3d_loading": "Building 3D view ...",
        "view_3d_waiting": "3D view is waiting for a file",
        "status_measure_off": "Measurement off",
        "empty_canvas": "No Bendpart file loaded\nUse 'Open' to choose a file",
        "open": "Open",
        "center_view": "Center view",
        "rotate_2d": "Rotate 2D",
        "settings": "Settings",
        "larger_2d": "Larger 2D",
        "larger_3d": "Larger 3D",
        "measure": "Measure",
        "measure_active": "Measure active",
        "point_measure": "Point measure",
        "point_measure_active": "Point measure active",
        "clear_dimensions": "Clear dimensions",
        "text_plus": "Text +",
        "text_minus": "Text -",
        "settings_title": "Settings",
        "default_folder": "Default folder",
        "choose_folder": "Choose folder",
        "choose_default_folder": "Choose default folder",
        "language": "Language",
        "german": "German",
        "english": "English",
        "cancel": "Cancel",
        "save": "Save",
        "invalid_folder_title": "Invalid folder",
        "invalid_folder_msg": "The default folder does not exist.",
        "bendpart_files": "Bendpart files",
        "all_files": "All files",
        "choose_bendpart": "Choose Bendpart file",
        "load_error_title": "Load error",
        "file_loaded": "File loaded",
        "status_fit_2d": "2D view fitted automatically",
        "status_rotate_2d": "2D view: {angle}°",
        "status_measure_pick_first": "Measure: select point 1 (line)",
        "status_measure_pick_second": "Measure: select point 2 (line)",
        "status_measure_line_pos": "Measure: place dimension line",
        "status_measure_text_pos": "Measure: place dimension text",
        "status_point_pick_first": "Point measure: select point 1",
        "status_point_pick_second": "Point measure: select point 2",
        "status_point_off": "Point measure off",
    },
}


def get_resource_base_dir():
    if getattr(sys, "frozen", False):
        meipass = getattr(sys, "_MEIPASS", None)
        if meipass:
            return meipass
        return os.path.dirname(os.path.abspath(sys.executable))
    return os.path.dirname(os.path.abspath(__file__))


def get_writable_base_dir():
    if getattr(sys, "frozen", False):
        return os.path.dirname(os.path.abspath(sys.executable))
    return os.path.dirname(os.path.abspath(__file__))


def get_settings_path():
    return os.path.join(get_writable_base_dir(), SETTINGS_FILENAME)


def get_resource_path(filename):
    return os.path.join(get_resource_base_dir(), filename)


def apply_app_icon(root):
    icon_path = get_resource_path(APP_ICON_FILENAME)
    if not os.path.exists(icon_path):
        return
    try:
        root.iconbitmap(icon_path)
    except Exception:
        pass


def load_settings():
    settings = dict(DEFAULT_SETTINGS)
    path = get_settings_path()
    if not os.path.exists(path):
        return settings

    try:
        with open(path, "r", encoding="utf-8") as handle:
            loaded = json.load(handle)
    except Exception:
        return settings

    if isinstance(loaded, dict):
        settings.update(loaded)

    default_folder = settings.get("default_folder") or ""
    if default_folder and not os.path.isdir(default_folder):
        settings["default_folder"] = ""
    settings["reverse_angle_display"] = bool(settings.get("reverse_angle_display", False))
    if settings.get("language") not in TRANSLATIONS:
        settings["language"] = DEFAULT_SETTINGS["language"]
    return settings


def save_settings(settings):
    merged = dict(DEFAULT_SETTINGS)
    merged.update(settings or {})
    with open(get_settings_path(), "w", encoding="utf-8") as handle:
        json.dump(merged, handle, indent=2, ensure_ascii=False)


def get_initial_folder(settings, fallback=None):
    candidate = (settings or {}).get("default_folder") or ""
    if candidate and os.path.isdir(candidate):
        return candidate
    if fallback and os.path.isdir(fallback):
        return fallback
    return os.getcwd()


def format_display_angle(angle_value, reverse_display=False):
    if abs(angle_value) <= 1e-9:
        return "±0.0°"

    sign = "+" if angle_value > 0 else "-"
    magnitude = abs(angle_value)
    if reverse_display:
        magnitude = max(0.0, 180.0 - magnitude)
    return f"{sign}{magnitude:.1f}°"


def translate(language, key, **kwargs):
    table = TRANSLATIONS.get(language, TRANSLATIONS[DEFAULT_SETTINGS["language"]])
    text = table.get(key) or TRANSLATIONS["de"].get(key) or key
    if kwargs:
        return text.format(**kwargs)
    return text


def get_angle_mode_label(reverse_display=False, language="de"):
    return translate(language, "inside_angle" if reverse_display else "outside_angle")


# ------------------------------------------------------------
# Bendpart loading and XML cleanup
# ------------------------------------------------------------

def load_bendpart(path):
    """Load a Bendpart file from disk and normalize the XML namespace layout."""
    # Bendpart files may arrive as gzip-compressed XML or as plain XML.
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


def get_attr_ending_with(elem, suffix):
    if elem is None:
        return None
    suffix = suffix.lower()
    for key, value in elem.attrib.items():
        tag = key.split("}", 1)[-1].lower()
        if tag == suffix or tag.endswith(suffix):
            return value
    return None


# ------------------------------------------------------------
# Geometry helpers and bulge handling
# ------------------------------------------------------------

def arc_points(P0, P1, bulge, segments=24):
    """
    Build a point list for a circular arc between P0 and P1 from a bulge value.

    Bendpart uses the same bulge convention as DXF:
        B = tan(theta / 4)
        theta = signed center angle
        the bulge value belongs to the start vertex of a segment
    """
    x0, y0 = P0
    x1, y1 = P1
    b = float(bulge)

    # No arc here, so we can return the straight segment immediately.
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

    # Radius of the supporting circle.
    R = abs(c_len / (2.0 * sin_half))

    # Midpoint of the chord.
    mx, my = (x0 + x1) / 2.0, (y0 + y1) / 2.0

    # Unit normal on the left side of the chord.
    nx, ny = -cdy / c_len, cdx / c_len
    if b < 0:
        nx, ny = -nx, -ny

    # Offset from the chord midpoint to the circle center.
    h_sq = max(R * R - (c_len * c_len) / 4.0, 0.0)
    h = math.sqrt(h_sq)

    cx, cy = mx + nx * h, my + ny * h

    # Starting angle on the circle.
    a0 = math.atan2(y0 - cy, x0 - cx)

    # Use more interpolation segments for larger bend angles.
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
    Build a closed polyline from a list of <Vertex> elements.

    Bulged edges are approximated as circular arcs.
    Assumptions:
    - the contour is closed
    - the bulge value is stored on the start vertex of each segment
    - Location is stored as "X Y" in millimeters
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
# Contours from Bendpart
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
            # Outer contour
            oc = surf.find("OuterContour")
            if oc is not None:
                verts_parent = oc.find("Vertices")
                if verts_parent is not None:
                    verts = verts_parent.findall("Vertex")
                    if len(verts) >= 2:
                        pts = build_poly_from_vertices(verts, segments=64)
                        if len(pts) >= 2:
                            contours.append({"points": pts, "type": "outer"})

            # Inner cutouts
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
# Bend lines from Bendpart plus tool information
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

    # Map tool IDs to readable tool names.
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

    # Resolve tool assignments from the bend process section.
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

    # Combine geometric bend-line data with the resolved tool names.
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

            # Fall back to the default tools if the bend-specific values are empty.
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
# Metadata
# ------------------------------------------------------------

def parse_meta(root):
    """Material, Dicke, Ober-/Unterwerkzeug (Default) aus der Bendpart lesen."""
    # Material
    material = None
    mat_elem = root.find(".//Material")
    if mat_elem is not None:
        uri = get_attr_ending_with(mat_elem, "uri")
        if uri:
            core = uri.split("/")[-1]
            material = core.split("#")[0]

    if material is None:
        props = root.get("Properties")
        if props:
            parts = props.split("|")
            if len(parts) >= 3 and parts[2]:
                material = parts[2]

    # Thickness
    thickness = None
    root_thickness = root.get("Thickness")
    if root_thickness:
        try:
            thickness = float(root_thickness)
        except Exception:
            thickness = None

    th_elem = root.find(".//Thickness")
    if thickness is None and th_elem is not None:
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

    if thickness is None:
        props = root.get("Properties")
        if props:
            parts = props.split("|")
            if len(parts) >= 4 and parts[3]:
                try:
                    thickness = float(parts[3])
                except Exception:
                    thickness = None

    # Default upper and lower tools
    upper_tool = None
    up_elem = root.find(".//UpperTool")
    if up_elem is not None:
        uri = get_attr_ending_with(up_elem, "uri")
        if uri:
            core = uri.split("/")[-1]
            upper_tool = core.split("#")[0]

    lower_tool = None
    low_elem = root.find(".//LowerTool")
    if low_elem is not None:
        uri = get_attr_ending_with(low_elem, "uri")
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
# 3D backend / VTK viewer
# ------------------------------------------------------------

def load_vtk_fold_module():
    """Load the compiled 3D backend module that holds the fold-model logic."""
    global _VTK_FOLD_MODULE
    if _VTK_FOLD_MODULE is not None:
        return _VTK_FOLD_MODULE

    cache_dir = os.path.join(get_resource_base_dir(), "__pycache__")
    candidates = [
        os.path.join(cache_dir, "BendPartViewer_VTK_Reset.cpython-313.pyc"),
        os.path.join(cache_dir, "BendPartViewer_VTK_Prototype.cpython-313.pyc"),
    ]

    errors = []
    for candidate in candidates:
        if not os.path.isfile(candidate):
            continue
        try:
            loader = importlib.machinery.SourcelessFileLoader(
                "_bendpart_vtk_backend",
                candidate,
            )
            spec = importlib.util.spec_from_loader(loader.name, loader)
            module = importlib.util.module_from_spec(spec)
            loader.exec_module(module)
            _VTK_FOLD_MODULE = module
            return module
        except Exception as exc:
            errors.append(f"{os.path.basename(candidate)}: {exc}")

    detail = "; ".join(errors) if errors else "no VTK backend was found in __pycache__"
    raise RuntimeError(f"3D-Backend konnte nicht geladen werden ({detail}).")


def append_polydata(vtk_mod, polydata_items):
    vtk = vtk_mod.vtk
    appender = vtk.vtkAppendPolyData()
    count = 0
    for polydata in polydata_items:
        if polydata is None:
            continue
        if polydata.GetNumberOfPoints() == 0:
            continue
        appender.AddInputData(polydata)
        count += 1

    if count == 0:
        return None

    appender.Update()
    cleaner = vtk.vtkCleanPolyData()
    cleaner.SetInputConnection(appender.GetOutputPort())
    cleaner.Update()

    merged = vtk.vtkPolyData()
    merged.ShallowCopy(cleaner.GetOutput())
    return merged


def prepare_polydata(vtk_mod, polydata, feature_angle=55.0):
    if polydata is None or polydata.GetNumberOfPoints() == 0:
        return None

    vtk = vtk_mod.vtk
    triangles = vtk.vtkTriangleFilter()
    triangles.SetInputData(polydata)
    triangles.Update()

    normals = vtk.vtkPolyDataNormals()
    normals.SetInputConnection(triangles.GetOutputPort())
    normals.SetFeatureAngle(feature_angle)
    normals.ConsistencyOn()
    normals.AutoOrientNormalsOn()
    normals.SplittingOn()
    normals.Update()

    prepared = vtk.vtkPolyData()
    prepared.ShallowCopy(normals.GetOutput())
    return prepared


def transform_surface_point(matrix, x_coord, y_coord, z_coord=0.0):
    return (
        float(matrix[0, 0] * x_coord + matrix[0, 1] * y_coord + matrix[0, 2] * z_coord + matrix[0, 3]),
        float(matrix[1, 0] * x_coord + matrix[1, 1] * y_coord + matrix[1, 2] * z_coord + matrix[1, 3]),
        float(matrix[2, 0] * x_coord + matrix[2, 1] * y_coord + matrix[2, 2] * z_coord + matrix[2, 3]),
    )


def build_surface_base_polygon(surface):
    outer = surface.get("outer") or []
    if len(outer) < 4:
        return None

    shell = outer[:-1] if outer[0] == outer[-1] else outer
    holes = []
    for inner in surface.get("inners") or []:
        if len(inner) < 4:
            continue
        hole = inner[:-1] if inner[0] == inner[-1] else inner
        holes.append(hole)

    polygon = Polygon(shell=shell, holes=holes)
    if polygon.is_empty:
        return None
    if not polygon.is_valid:
        polygon = polygon.buffer(0)
    if polygon.is_empty:
        return None
    return polygon


def clip_polygon_with_bend_setback(polygon, bend_line, thickness):
    if polygon is None or polygon.is_empty:
        return polygon

    start = bend_line.get("start")
    end = bend_line.get("end")
    if start is None or end is None:
        return polygon

    dx = float(end[0] - start[0])
    dy = float(end[1] - start[1])
    length = math.hypot(dx, dy)
    if length <= 1e-9:
        return polygon

    angle = abs(float(bend_line.get("angle") or 0.0))
    if angle <= 1e-9:
        return polygon

    bend_radius = float(bend_line.get("bend_radius") or 0.0)
    setback = (bend_radius + thickness * 0.5) * math.tan(math.radians(angle) * 0.5)
    if setback <= 1e-9:
        return polygon

    sample = polygon.representative_point()
    signed_cross = dx * (sample.y - start[1]) - dy * (sample.x - start[0])
    side_sign = 1.0 if signed_cross >= 0.0 else -1.0

    tangent_x = dx / length
    tangent_y = dy / length
    inward_normal_x = (-tangent_y) * side_sign
    inward_normal_y = tangent_x * side_sign

    shifted_start = (
        float(start[0]) + inward_normal_x * setback,
        float(start[1]) + inward_normal_y * setback,
    )
    shifted_end = (
        float(end[0]) + inward_normal_x * setback,
        float(end[1]) + inward_normal_y * setback,
    )

    # Trim only the local strip that is consumed by the bend transition.
    tangent_padding = max(setback * 0.25, 1e-5)
    trim_strip = Polygon(
        [
            (
                float(start[0]) - tangent_x * tangent_padding,
                float(start[1]) - tangent_y * tangent_padding,
            ),
            (
                float(end[0]) + tangent_x * tangent_padding,
                float(end[1]) + tangent_y * tangent_padding,
            ),
            (
                shifted_end[0] + tangent_x * tangent_padding,
                shifted_end[1] + tangent_y * tangent_padding,
            ),
            (
                shifted_start[0] - tangent_x * tangent_padding,
                shifted_start[1] - tangent_y * tangent_padding,
            ),
        ]
    )

    clipped = polygon.difference(trim_strip)
    if clipped.is_empty:
        return clipped
    if not clipped.is_valid:
        clipped = clipped.buffer(0)
    return clipped


def build_trimmed_surface_polygon(surface, bend_lines, thickness):
    """Build the flat surface face after removing the local bend setbacks."""
    polygon = build_surface_base_polygon(surface)
    if polygon is None:
        return None

    for bend_line in bend_lines:
        polygon = clip_polygon_with_bend_setback(polygon, bend_line, thickness)
        if polygon is None or polygon.is_empty:
            return polygon

    return polygon


def polygon_to_surface_polydata(vtk_mod, polygon, transform, z_offset):
    """Triangulate a shapely polygon and convert it into VTK polydata."""
    if polygon is None or polygon.is_empty:
        return None

    vtk = vtk_mod.vtk
    polygons = [polygon] if isinstance(polygon, Polygon) else list(polygon.geoms) if isinstance(polygon, MultiPolygon) else []
    polydata_parts = []

    for shape in polygons:
        loops = [list(shape.exterior.coords)[:-1]]
        loops.extend(list(ring.coords)[:-1] for ring in shape.interiors)

        points = vtk.vtkPoints()
        lines = vtk.vtkCellArray()
        point_id = 0

        for loop in loops:
            if len(loop) < 3:
                continue

            polyline = vtk.vtkPolyLine()
            polyline.GetPointIds().SetNumberOfIds(len(loop) + 1)
            first_point_id = point_id

            for index, (x_coord, y_coord) in enumerate(loop):
                point = transform_surface_point(transform, x_coord, y_coord, z_offset)
                points.InsertNextPoint(*point)
                polyline.GetPointIds().SetId(index, point_id)
                point_id += 1

            polyline.GetPointIds().SetId(len(loop), first_point_id)
            lines.InsertNextCell(polyline)

        if point_id == 0:
            continue

        contour_data = vtk.vtkPolyData()
        contour_data.SetPoints(points)
        contour_data.SetLines(lines)

        triangulator = vtk.vtkContourTriangulator()
        triangulator.SetInputData(contour_data)
        triangulator.Update()

        output = triangulator.GetOutput()
        if output is None or output.GetNumberOfCells() == 0:
            continue

        face = vtk.vtkPolyData()
        face.ShallowCopy(output)
        polydata_parts.append(face)

    return append_polydata(vtk_mod, polydata_parts)


def build_folded_part_polydata(path):
    """
    Build the three colored mesh groups for the 3D viewer.

    The result is split into top faces, bottom faces, side walls, and bend faces
    so the viewer can color them independently.
    """
    backend = load_vtk_fold_module()
    root = load_bendpart(path)
    meta = parse_meta(root)

    thickness = meta.get("thickness")
    if thickness is None or thickness <= 0:
        raise ValueError("Keine gueltige Materialdicke in der Bendpart-Datei gefunden.")

    surfaces, bend_surface_lines = backend.parse_surface_model(root)
    if not surfaces:
        raise ValueError("Keine BendSurfaceModel-Geometrie fuer die 3D-Ansicht gefunden.")

    if hasattr(backend, "build_hinge_transforms"):
        transforms, _ = backend.build_hinge_transforms(
            surfaces,
            bend_surface_lines,
        )
    else:
        transforms, _ = backend.build_centerline_transforms(
            surfaces,
            bend_surface_lines,
            float(thickness),
        )

    bend_lines_by_surface = {}
    for bend_line in bend_surface_lines:
        bend_lines_by_surface.setdefault(bend_line.get("left_surface"), []).append(bend_line)
        bend_lines_by_surface.setdefault(bend_line.get("right_surface"), []).append(bend_line)

    top_parts = []
    bottom_parts = []
    side_parts = []
    bend_parts = []

    for surface_id, surface in surfaces.items():
        trimmed_polygon = build_trimmed_surface_polygon(
            surface,
            bend_lines_by_surface.get(surface_id, []),
            float(thickness),
        )

        parts = backend.make_surface_polydata_parts(
            surface,
            transforms[surface_id],
            float(thickness),
            bend_surface_lines,
            surfaces,
            transforms,
        )
        rebuilt_top = polygon_to_surface_polydata(
            backend,
            trimmed_polygon,
            transforms[surface_id],
            float(thickness) * 0.5,
        )
        rebuilt_bottom = polygon_to_surface_polydata(
            backend,
            trimmed_polygon,
            transforms[surface_id],
            -float(thickness) * 0.5,
        )
        top_parts.append(rebuilt_top if rebuilt_top is not None else parts.get("top"))
        bottom_parts.append(rebuilt_bottom if rebuilt_bottom is not None else parts.get("bottom"))
        side_parts.append(parts.get("sides"))

    for bend_line in bend_surface_lines:
        bend_faces = backend.build_bend_faces_vtk(
            bend_line,
            surfaces,
            transforms,
            float(thickness),
        )
        parts = backend.make_bend_polydata_parts(bend_faces)
        bend_parts.append(parts.get("top"))
        bend_parts.append(parts.get("bottom"))
        bend_parts.append(parts.get("sides"))

    top = prepare_polydata(backend, append_polydata(backend, top_parts))
    bottom = prepare_polydata(backend, append_polydata(backend, bottom_parts))
    sides = prepare_polydata(backend, append_polydata(backend, side_parts))
    bends = prepare_polydata(backend, append_polydata(backend, bend_parts))
    return {
        "meta": meta,
        "surfaces": len(surfaces),
        "bends": len(bend_surface_lines),
        "top": top,
        "bottom": bottom,
        "sides": sides,
        "bend_faces": bends,
    }


def make_vtk_actor(vtk_mod, polydata, color, opacity=1.0):
    if polydata is None or polydata.GetNumberOfPoints() == 0:
        return None

    vtk = vtk_mod.vtk
    mapper = vtk.vtkPolyDataMapper()
    mapper.SetInputData(polydata)

    actor = vtk.vtkActor()
    actor.SetMapper(mapper)
    prop = actor.GetProperty()
    prop.SetColor(*color)
    prop.SetOpacity(opacity)
    prop.SetInterpolationToFlat()
    prop.SetLighting(False)
    prop.SetAmbient(1.0)
    prop.SetDiffuse(0.0)
    prop.SetSpecular(0.0)
    prop.SetSpecularPower(1.0)
    return actor


def open_folded_3d_view(path):
    backend = load_vtk_fold_module()
    vtk = backend.vtk
    folded = build_folded_part_polydata(path)

    renderer = vtk.vtkRenderer()
    renderer.SetBackground(0.12, 0.14, 0.18)
    renderer.SetBackground2(0.03, 0.04, 0.06)
    renderer.GradientBackgroundOn()
    try:
        renderer.UseFXAAOn()
    except Exception:
        pass

    render_window = vtk.vtkRenderWindow()
    render_window.AddRenderer(renderer)
    render_window.SetSize(1280, 840)
    render_window.SetWindowName(f"3D Bendpart - {os.path.basename(path)}")

    interactor = vtk.vtkRenderWindowInteractor()
    interactor.SetRenderWindow(render_window)
    interactor.SetInteractorStyle(vtk.vtkInteractorStyleTrackballCamera())

    top_actor = make_vtk_actor(backend, folded["top"], (0.42, 0.66, 0.98))
    bottom_actor = make_vtk_actor(backend, folded["bottom"], (0.98, 0.72, 0.16))
    side_actor = make_vtk_actor(backend, folded["sides"], (0.18, 0.68, 0.32))
    bend_actor = make_vtk_actor(backend, folded.get("bend_faces"), (0.18, 0.68, 0.32))
    for actor in (top_actor, bottom_actor, side_actor, bend_actor):
        if actor is not None:
            renderer.AddActor(actor)

    light = vtk.vtkLight()
    light.SetLightTypeToHeadlight()
    light.SetIntensity(1.0)
    renderer.AddLight(light)

    axes = vtk.vtkAxesActor()
    axes.SetTotalLength(35.0, 35.0, 35.0)
    marker = vtk.vtkOrientationMarkerWidget()
    marker.SetOrientationMarker(axes)
    marker.SetInteractor(interactor)
    marker.SetViewport(0.0, 0.0, 0.16, 0.16)
    marker.SetEnabled(1)
    marker.InteractiveOff()

    meta = folded["meta"]
    material = meta.get("material") or "-"
    thickness = meta.get("thickness")
    thickness_text = f"{thickness:.1f} mm" if isinstance(thickness, (int, float)) else "-"
    info = (
        f"{os.path.basename(path)}\n"
        f"Material: {material}    Dicke: {thickness_text}\n"
        f"BendSurfaces: {folded['surfaces']}    BendLines: {folded['bends']}"
    )
    text_actor = vtk.vtkTextActor()
    text_actor.SetInput(info)
    text_prop = text_actor.GetTextProperty()
    text_prop.SetFontSize(18)
    text_prop.SetColor(0.96, 0.97, 0.99)
    text_prop.SetShadow(1)
    text_actor.SetDisplayPosition(18, 18)
    renderer.AddActor2D(text_actor)

    renderer.ResetCamera()
    camera = renderer.GetActiveCamera()
    camera.Azimuth(28)
    camera.Elevation(22)
    camera.Dolly(1.15)
    renderer.ResetCameraClippingRange()

    render_window.Render()
    interactor.Initialize()
    interactor.Start()


# ------------------------------------------------------------
# Geometry helpers for segments and measurements
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
# Drawing, including the bend-tool display logic
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

    # Collect all non-default tool combinations so we can label only the exceptions.
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

    # Draw outer and inner contours first.
    for c in contours:
        poly = c["points"]
        if len(poly) < 2:
            continue
        xs = [p[0] for p in poly]
        ys = [p[1] for p in poly]

        if c["type"] == "outer":
            # Main sheet area
            ax.fill(xs, ys,
                    facecolor="#e0e0e0", edgecolor="black", linewidth=0.8)
        else:
            # Cutouts stay dark like the workspace, but keep a visible edge.
            ax.fill(xs, ys,
                    facecolor=BG_COLOR, edgecolor="#dddddd", linewidth=0.7)


    # Draw bend lines, angle labels, and optional tool labels.
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

            # Only show tool labels when the bend uses a non-default tool setup.
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
# File selection
# ------------------------------------------------------------

def choose_bendpart_file(initial_dir=None):
    root = tk.Tk()
    root.withdraw()
    settings = load_settings()
    language = settings.get("language", DEFAULT_SETTINGS["language"])
    if initial_dir is None:
        initial_dir = get_initial_folder(settings)
    filename = filedialog.askopenfilename(
        initialdir=initial_dir,
        filetypes=[(translate(language, "bendpart_files"), "*.bendpart"), (translate(language, "all_files"), "*.*")],
        title=translate(language, "choose_bendpart"),
    )
    root.destroy()
    return filename if filename else None


# ------------------------------------------------------------
# Interactive GUI
# ------------------------------------------------------------

def interactive_dim(initial_path=None):
    """
    Create the main application window and wire together the full viewer workflow.

    This function owns the Tk layout, the 2D canvas interactions, the 3D preview,
    and all command callbacks that operate on the currently loaded Bendpart file.
    """
    global TEXT_SIZE

    settings = load_settings()
    ui_refs = {}

    def tr(key, **kwargs):
        return translate(settings.get("language", DEFAULT_SETTINGS["language"]), key, **kwargs)

    state = {
        "path": None,
        "raw_contours": [],
        "raw_bend_lines": [],
        "contours": [],
        "bend_lines": [],
        "segments": [],
        "raw_bounds": None,
        "bounds": None,
        "diag": None,
        "meta": {},
        "view_rotation_override": None,
        "view_rotation_actual": 0,
        "view_center": None,
        "view_scale": None,
        "pan_anchor": None,
        "canvas_size": (1, 1),
        "settings": settings,
    }

    root = tk.Tk()
    root.title(tr("app_title"))
    root.geometry("1680x980")
    root.minsize(1200, 760)
    root.configure(bg="#20242c")
    apply_app_icon(root)

    style = ttk.Style(root)
    try:
        style.theme_use("clam")
    except Exception:
        pass
    style.configure("App.TFrame", background="#20242c")
    style.configure("Panel.TFrame", background="#262b34")
    style.configure("InfoPanel.TFrame", background="#1c2129")
    style.configure("Card.TLabelframe", background="#262b34", foreground="white", borderwidth=0)
    style.configure("Card.TLabelframe.Label", background="#262b34", foreground="white", font=("Segoe UI", 10, "bold"))
    style.configure("Title.TLabel", background="#20242c", foreground="white", font=("Segoe UI", 18, "bold"))
    style.configure("Meta.TLabel", background="#20242c", foreground="#e6edf8", font=("Segoe UI", 13, "bold"))
    style.configure("InfoCaption.TLabel", background="#1c2129", foreground="#8ea0b8", font=("Segoe UI", 9, "bold"))
    style.configure("InfoValue.TLabel", background="#1c2129", foreground="#f7fbff", font=("Segoe UI", 15, "bold"))
    style.configure("Status.TLabel", background="#171b22", foreground="#eef3ff", font=("Segoe UI", 10))
    style.configure("App.TButton", background="#3d7be0", foreground="white", borderwidth=0, focusthickness=0, padding=(12, 8))
    style.map("App.TButton", background=[("active", "#5b98ff"), ("pressed", "#3368c2")])
    style.configure("Accent.TButton", background="#2f9d67", foreground="white", borderwidth=0, focusthickness=0, padding=(12, 8))
    style.map("Accent.TButton", background=[("active", "#3db87b"), ("pressed", "#268154")])
    style.configure("Measure.TButton", background="#1e8f68", foreground="white", borderwidth=0, focusthickness=0, padding=(16, 10))
    style.map("Measure.TButton", background=[("active", "#27a57a"), ("pressed", "#187456")])

    dim_texts = []
    dim_records = []

    header_frame = ttk.Frame(root, style="App.TFrame", padding=(14, 10, 14, 8))
    header_frame.pack(fill="x")
    header_left = ttk.Frame(header_frame, style="App.TFrame")
    header_left.pack(side="left", fill="both", expand=True)
    header_right = ttk.Frame(header_frame, style="InfoPanel.TFrame", padding=(18, 10))
    header_right.pack(side="right", fill="y", anchor="ne")

    title_var = tk.StringVar(value=tr("app_name"))
    status_var = tk.StringVar(value=tr("status_measure_off"))
    info_value_vars = {
        "thickness": tk.StringVar(value="-"),
        "material": tk.StringVar(value="-"),
        "angle_display": tk.StringVar(value="-"),
        "upper_tool": tk.StringVar(value="-"),
        "lower_tool": tk.StringVar(value="-"),
        "special_combos": tk.StringVar(value="-"),
    }

    ttk.Label(header_left, textvariable=title_var, style="Title.TLabel").pack(anchor="w")
    info_fields = [
        ("thickness", 0, 0),
        ("material", 0, 1),
        ("angle_display", 0, 2),
        ("upper_tool", 1, 0),
        ("lower_tool", 1, 1),
        ("special_combos", 1, 2),
    ]
    for field_name, row_idx, col_idx in info_fields:
        field_frame = ttk.Frame(header_right, style="InfoPanel.TFrame", padding=(8, 2))
        field_frame.grid(row=row_idx, column=col_idx, sticky="nsew", padx=(0 if col_idx == 0 else 10, 0), pady=(0 if row_idx == 0 else 8, 0))
        caption = ttk.Label(field_frame, style="InfoCaption.TLabel", anchor="w")
        caption.pack(anchor="w")
        value = ttk.Label(field_frame, textvariable=info_value_vars[field_name], style="InfoValue.TLabel", anchor="w")
        value.pack(anchor="w", pady=(2, 0))
        ui_refs[f"info_caption_{field_name}"] = caption
        ui_refs[f"info_value_{field_name}"] = value
    for col_idx in range(3):
        header_right.columnconfigure(col_idx, weight=1)

    controls_frame = ttk.Frame(header_left, style="App.TFrame", padding=(0, 8, 0, 0))
    controls_frame.pack(fill="x")

    body_pane = tk.PanedWindow(
        root,
        orient=tk.HORIZONTAL,
        bg="#20242c",
        sashwidth=8,
        sashrelief=tk.RAISED,
        bd=0,
        relief=tk.FLAT,
    )
    body_pane.pack(fill="both", expand=True, padx=14, pady=(0, 10))

    left_panel = ttk.Frame(body_pane, style="Panel.TFrame", padding=8)
    right_panel = ttk.Frame(body_pane, style="Panel.TFrame", padding=8)
    body_pane.add(left_panel, minsize=520, stretch="always")
    body_pane.add(right_panel, minsize=420, stretch="always")

    plot_frame = ttk.LabelFrame(left_panel, text=tr("sheet_2d"), style="Card.TLabelframe", padding=8)
    plot_frame.pack(fill="both", expand=True)
    canvas_frame = ttk.Frame(plot_frame, style="Panel.TFrame")
    canvas_frame.pack(fill="both", expand=True)

    viewer3d_frame = ttk.LabelFrame(right_panel, text=tr("view_3d"), style="Card.TLabelframe", padding=8)
    viewer3d_frame.pack(fill="both", expand=True)

    status_frame = ttk.Frame(root, style="App.TFrame", padding=(14, 0, 14, 12))
    status_frame.pack(fill="x")
    ttk.Label(status_frame, textvariable=status_var, style="Status.TLabel", anchor="w").pack(fill="x")

    canvas_widget = tk.Canvas(canvas_frame, bg=BG_COLOR, highlightthickness=0, bd=0, relief=tk.FLAT)
    canvas_widget.pack(fill="both", expand=True)

    viewer3d_label = tk.Label(
        viewer3d_frame,
        bg="#141820",
        fg="#d8dee9",
        text=tr("view_3d_loading"),
        anchor="center",
    )
    viewer3d_label.pack(fill="both", expand=True)
    vtk_backend = load_vtk_fold_module()
    vtk = vtk_backend.vtk
    render_window = vtk.vtkRenderWindow()
    render_window.SetOffScreenRendering(1)
    renderer = vtk.vtkRenderer()
    renderer.SetBackground(0.12, 0.14, 0.18)
    renderer.SetBackground2(0.03, 0.04, 0.06)
    renderer.GradientBackgroundOn()
    try:
        renderer.UseFXAAOff()
    except Exception:
        pass
    render_window.AddRenderer(renderer)
    try:
        render_window.SetMultiSamples(0)
    except Exception:
        pass
    viewer3d_state = {"photo": None, "drag": None, "drag_button": None, "camera_home": None}

    def set_status(msg):
        status_var.set(msg)
        root.update_idletasks()

    def update_info_text():
        meta = state["meta"] or {}
        thickness = meta.get("thickness")
        material = meta.get("material") or "-"
        upper_tool = meta.get("upper_tool") or "-"
        lower_tool = meta.get("lower_tool") or "-"
        thickness_text = f"{thickness:.1f} mm" if isinstance(thickness, (int, float)) else "-"
        angle_mode = get_angle_mode_label(
            state["settings"].get("reverse_angle_display", False),
            state["settings"].get("language", DEFAULT_SETTINGS["language"]),
        )

        info_value_vars["angle_display"].set(angle_mode)

        if not state["path"]:
            title_var.set(tr("app_name"))
            info_value_vars["thickness"].set("-")
            info_value_vars["material"].set("-")
            info_value_vars["upper_tool"].set("-")
            info_value_vars["lower_tool"].set("-")
            info_value_vars["special_combos"].set(tr("no_file_loaded"))
            return

        special_combos = set()
        for bend_line in state["bend_lines"]:
            if not bend_line.get("is_default_combo", False):
                upper = bend_line.get("upper_tool")
                lower = bend_line.get("lower_tool")
                if upper or lower:
                    special_combos.add((upper, lower))

        title_var.set(f"{tr('app_name')}  |  {os.path.basename(state['path'])}")
        info_value_vars["thickness"].set(thickness_text)
        info_value_vars["material"].set(material)
        info_value_vars["upper_tool"].set(upper_tool)
        info_value_vars["lower_tool"].set(lower_tool)
        info_value_vars["special_combos"].set(str(len(special_combos)) if special_combos else "-")

    def calc_bounds(contours):
        xs = [point[0] for contour in contours for point in contour["points"]]
        ys = [point[1] for contour in contours for point in contour["points"]]
        if not xs or not ys:
            return None
        return (min(xs), max(xs), min(ys), max(ys))

    def rotate_point(point, angle_deg, center):
        px, py = point
        cx, cy = center
        radians = math.radians(angle_deg)
        cos_a = math.cos(radians)
        sin_a = math.sin(radians)
        dx = px - cx
        dy = py - cy
        return (
            cx + dx * cos_a - dy * sin_a,
            cy + dx * sin_a + dy * cos_a,
        )

    def choose_best_view_rotation():
        override = state.get("view_rotation_override")
        if override is not None:
            return override

        bounds = state.get("raw_bounds")
        if not bounds:
            return 0

        canvas_width = max(canvas_widget.winfo_width(), 1)
        canvas_height = max(canvas_widget.winfo_height(), 1)
        if canvas_width < 10 or canvas_height < 10:
            return 0

        width = max(bounds[1] - bounds[0], 1.0)
        height = max(bounds[3] - bounds[2], 1.0)
        target_ratio = canvas_width / canvas_height
        ratio_0 = width / height
        ratio_90 = height / width

        error_0 = abs(math.log(ratio_0 / target_ratio))
        error_90 = abs(math.log(ratio_90 / target_ratio))
        return 90 if error_90 < error_0 else 0

    def apply_2d_view_transform():
        raw_contours = state.get("raw_contours") or []
        raw_bend_lines = state.get("raw_bend_lines") or []
        bounds = state.get("raw_bounds")
        if not bounds:
            state["contours"] = raw_contours
            state["bend_lines"] = raw_bend_lines
            state["segments"] = build_all_segments(raw_contours, raw_bend_lines)
            state["bounds"] = None
            state["diag"] = None
            state["view_rotation_actual"] = 0
            return

        rotation = choose_best_view_rotation()
        center = ((bounds[0] + bounds[1]) * 0.5, (bounds[2] + bounds[3]) * 0.5)

        if rotation % 360 == 0:
            contours = [{**contour, "points": list(contour["points"])} for contour in raw_contours]
            bend_lines = [dict(bend_line) for bend_line in raw_bend_lines]
        else:
            contours = []
            for contour in raw_contours:
                transformed = dict(contour)
                transformed["points"] = [rotate_point(point, rotation, center) for point in contour["points"]]
                contours.append(transformed)

            bend_lines = []
            for bend_line in raw_bend_lines:
                transformed = dict(bend_line)
                transformed["start"] = rotate_point(bend_line["start"], rotation, center)
                transformed["end"] = rotate_point(bend_line["end"], rotation, center)
                bend_lines.append(transformed)

        display_bounds = calc_bounds(contours)
        state["contours"] = contours
        state["bend_lines"] = bend_lines
        state["segments"] = build_all_segments(contours, bend_lines)
        state["bounds"] = display_bounds
        if display_bounds:
            state["diag"] = math.hypot(display_bounds[1] - display_bounds[0], display_bounds[3] - display_bounds[2])
        else:
            state["diag"] = None
        state["view_rotation_actual"] = rotation

    def load_geometry(path_value):
        try:
            bendpart_root = load_bendpart(path_value)
        except Exception as exc:
            messagebox.showerror(tr("load_error_title"), str(exc), parent=root)
            return False

        contours = parse_contours(bendpart_root)
        meta = parse_meta(bendpart_root)
        bend_lines = parse_bend_lines(bendpart_root, meta)
        raw_bounds = calc_bounds(contours)

        state["path"] = path_value
        state["raw_contours"] = contours
        state["raw_bend_lines"] = bend_lines
        state["raw_bounds"] = raw_bounds
        state["meta"] = meta
        apply_2d_view_transform()
        print(f"{tr('file_loaded')}: {path_value}")
        return True

    def clear_geometry():
        state["path"] = None
        state["raw_contours"] = []
        state["raw_bend_lines"] = []
        state["raw_bounds"] = None
        state["contours"] = []
        state["bend_lines"] = []
        state["segments"] = []
        state["bounds"] = None
        state["diag"] = None
        state["meta"] = {}
        state["view_center"] = None
        state["view_scale"] = None

    if initial_path:
        if not load_geometry(initial_path):
            clear_geometry()
    else:
        clear_geometry()

    def fit_geometry_to_canvas():
        if not state["bounds"]:
            return

        min_x, max_x, min_y, max_y = state["bounds"]
        width = max(max_x - min_x, 1.0)
        height = max(max_y - min_y, 1.0)
        pad_x = width * 0.02
        pad_y = height * 0.02

        min_x -= pad_x
        max_x += pad_x
        min_y -= pad_y
        max_y += pad_y

        canvas_width = max(canvas_widget.winfo_width(), 1)
        canvas_height = max(canvas_widget.winfo_height(), 1)
        scale_x = canvas_width / max(max_x - min_x, 1.0)
        scale_y = canvas_height / max(max_y - min_y, 1.0)
        state["view_scale"] = max(min(scale_x, scale_y), 0.01)
        state["view_center"] = ((min_x + max_x) * 0.5, (min_y + max_y) * 0.5)

    def world_to_canvas(point):
        center = state.get("view_center")
        scale = state.get("view_scale")
        if center is None or scale in (None, 0):
            return (0.0, 0.0)
        width = max(canvas_widget.winfo_width(), 1)
        height = max(canvas_widget.winfo_height(), 1)
        x, y = point
        cx, cy = center
        return (
            (x - cx) * scale + width * 0.5,
            height * 0.5 - (y - cy) * scale,
        )

    def canvas_to_world(x, y):
        center = state.get("view_center")
        scale = state.get("view_scale")
        if center is None or scale in (None, 0):
            return (0.0, 0.0)
        width = max(canvas_widget.winfo_width(), 1)
        height = max(canvas_widget.winfo_height(), 1)
        cx, cy = center
        return (
            (x - width * 0.5) / scale + cx,
            (height * 0.5 - y) / scale + cy,
        )

    def create_text_box(x, y, text_value, text_color, fill_color, tag):
        text_id = canvas_widget.create_text(
            x,
            y,
            text=text_value,
            fill=text_color,
            font=("Segoe UI", max(int(round(TEXT_SIZE)), 6)),
            justify="center",
            tags=tag,
        )
        bbox = canvas_widget.bbox(text_id)
        if bbox:
            rect_id = canvas_widget.create_rectangle(
                bbox[0] - 4,
                bbox[1] - 2,
                bbox[2] + 4,
                bbox[3] + 2,
                fill=fill_color,
                outline="",
                tags=tag,
            )
            canvas_widget.tag_lower(rect_id, text_id)
        dim_texts.append(text_id)
        return text_id

    def draw_part_on_canvas():
        default_ut = state["meta"].get("upper_tool")
        default_lt = state["meta"].get("lower_tool")

        special_combos = set()
        for bend_line in state["bend_lines"]:
            if not bend_line.get("is_default_combo", False):
                ut = bend_line.get("upper_tool")
                lt = bend_line.get("lower_tool")
                if ut or lt:
                    special_combos.add((ut, lt))

        special_combos = sorted(special_combos, key=lambda combo: ((combo[0] or ""), (combo[1] or "")))
        palette = ["#ffe6cc", "#e0f7e9", "#e0ecff", "#ffe6f2", "#f4f4d7"]
        combo_colors = {combo: palette[i % len(palette)] for i, combo in enumerate(special_combos)}

        for contour in state["contours"]:
            if len(contour["points"]) < 2:
                continue
            points = []
            for point in contour["points"]:
                px, py = world_to_canvas(point)
                points.extend((px, py))
            if contour["type"] == "outer":
                canvas_widget.create_polygon(points, fill="#e0e0e0", outline="black", width=1.0, tags="geom")
            else:
                canvas_widget.create_polygon(points, fill=BG_COLOR, outline="#dddddd", width=1.0, tags="geom")

        seen_ids = set()
        for bend_line in state["bend_lines"]:
            sx, sy = world_to_canvas(bend_line["start"])
            ex, ey = world_to_canvas(bend_line["end"])
            angle = bend_line["angle"]
            bend_id = bend_line["bend_id"]

            if angle < 0:
                color = "#ff5555"
                dash = (8, 4)
            elif angle > 0:
                color = "#66aaff"
                dash = (2, 3)
            else:
                color = "#66aaff"
                dash = (6, 4)

            canvas_widget.create_line(sx, sy, ex, ey, fill=color, width=1.5, dash=dash, tags="geom")

            if bend_id in seen_ids:
                continue
            seen_ids.add(bend_id)

            mx = (bend_line["start"][0] + bend_line["end"][0]) * 0.5
            my = (bend_line["start"][1] + bend_line["end"][1]) * 0.5
            dx = bend_line["end"][0] - bend_line["start"][0]
            dy = bend_line["end"][1] - bend_line["start"][1]
            length = math.hypot(dx, dy)
            if length > 0:
                tx, ty = dx / length, dy / length
                nx, ny = -ty, tx
            else:
                tx, ty = 1.0, 0.0
                nx, ny = 0.0, 1.0

            text_point = (mx + tx * 8.0 + nx * 5.0, my + ty * 8.0 + ny * 5.0)
            text_x, text_y = world_to_canvas(text_point)

            text_value = format_display_angle(
                angle,
                reverse_display=state["settings"].get("reverse_angle_display", False),
            )

            ut = bend_line.get("upper_tool")
            lt = bend_line.get("lower_tool")
            show_tools = not bend_line.get("is_default_combo", False) and (ut or lt)
            if show_tools:
                tool_parts = []
                if ut:
                    tool_parts.append(f"{ut}")
                if lt:
                    tool_parts.append(f"{lt}")
                if tool_parts:
                    text_value += "\n" + " / ".join(tool_parts)
                fill_color = combo_colors.get((ut, lt), "#f5f5f5")
            else:
                fill_color = "white"

            create_text_box(text_x, text_y, text_value, color, fill_color, "geom")

    def draw_marker(point, color):
        x, y = world_to_canvas(point)
        canvas_widget.create_oval(x - 4, y - 4, x + 4, y + 4, fill=color, outline="", tags="overlay")

    def draw_measurements():
        for record in dim_records:
            if record["type"] == "line_distance":
                p1_base = record["p1_base"]
                p2_base = record["p2_base"]
                dim_p1 = record["dim_p1"]
                dim_p2 = record["dim_p2"]
                text_pos = record["text_pos"]
                x1, y1 = world_to_canvas(dim_p1)
                x2, y2 = world_to_canvas(dim_p2)
                bx1, by1 = world_to_canvas(p1_base)
                bx2, by2 = world_to_canvas(p2_base)
                tx, ty = world_to_canvas(text_pos)
                canvas_widget.create_line(x1, y1, x2, y2, fill="#00aa00", width=2, tags="overlay")
                canvas_widget.create_line(bx1, by1, x1, y1, fill="#00aa00", width=1, tags="overlay")
                canvas_widget.create_line(bx2, by2, x2, y2, fill="#00aa00", width=1, tags="overlay")
                create_text_box(tx, ty, f"{record['dist']:.1f} mm", "#00aa00", "white", "overlay")
            elif record["type"] == "point_distance":
                p1 = record["p1"]
                p2 = record["p2"]
                x1, y1 = world_to_canvas(p1)
                x2, y2 = world_to_canvas(p2)
                canvas_widget.create_line(x1, y1, x2, y2, fill="#ffcc00", width=2, tags="overlay")
                draw_marker(p1, "yellow")
                draw_marker(p2, "yellow")
                midx = (p1[0] + p2[0]) * 0.5
                midy = (p1[1] + p2[1]) * 0.5
                vx = p2[0] - p1[0]
                vy = p2[1] - p1[1]
                vec_len = math.hypot(vx, vy)
                nx, ny = (-vy / vec_len, vx / vec_len) if vec_len > 0 else (0.0, -1.0)
                text_pos = (midx + nx * 5.0, midy + ny * 5.0)
                tx, ty = world_to_canvas(text_pos)
                create_text_box(tx, ty, f"{record['dist']:.1f} mm", "#ffcc00", "white", "overlay")

        if measure["enabled"]:
            if measure.get("seg1_point") is not None:
                draw_marker(measure["seg1_point"], "orange")
            if measure.get("seg2_point") is not None:
                draw_marker(measure["seg2_point"], "orange")
            if measure.get("dim_p1") is not None and measure.get("dim_p2") is not None:
                x1, y1 = world_to_canvas(measure["dim_p1"])
                x2, y2 = world_to_canvas(measure["dim_p2"])
                bx1, by1 = world_to_canvas(measure["p1_base"])
                bx2, by2 = world_to_canvas(measure["p2_base"])
                canvas_widget.create_line(x1, y1, x2, y2, fill="#00aa00", width=2, tags="overlay")
                canvas_widget.create_line(bx1, by1, x1, y1, fill="#00aa00", width=1, tags="overlay")
                canvas_widget.create_line(bx2, by2, x2, y2, fill="#00aa00", width=1, tags="overlay")

        if point_measure["enabled"] and point_measure.get("p1") is not None:
            draw_marker(point_measure["p1"], "yellow")

    def apply_text_size():
        redraw_geometry(fit_view=False)

    def redraw_geometry(fit_view=True):
        apply_2d_view_transform()
        canvas_widget.delete("all")
        dim_texts.clear()
        if not state["path"] or not state["contours"]:
            update_info_text()
            canvas_widget.create_text(
                max(canvas_widget.winfo_width(), 1) * 0.5,
                max(canvas_widget.winfo_height(), 1) * 0.5,
                text=tr("empty_canvas"),
                fill="#d8dee9",
                font=("Segoe UI", 16, "bold"),
                justify="center",
            )
            return
        if fit_view or state.get("view_scale") is None or state.get("view_center") is None:
            fit_geometry_to_canvas()
        draw_part_on_canvas()
        draw_measurements()
        update_info_text()

    def clear_renderer():
        renderer.RemoveAllViewProps()

    def capture_camera_home():
        camera = renderer.GetActiveCamera()
        viewer3d_state["camera_home"] = {
            "position": camera.GetPosition(),
            "focal_point": camera.GetFocalPoint(),
            "view_up": camera.GetViewUp(),
            "parallel_scale": camera.GetParallelScale(),
            "view_angle": camera.GetViewAngle(),
        }

    def reset_3d_camera():
        home = viewer3d_state.get("camera_home")
        if not home:
            return
        camera = renderer.GetActiveCamera()
        camera.SetPosition(*home["position"])
        camera.SetFocalPoint(*home["focal_point"])
        camera.SetViewUp(*home["view_up"])
        camera.SetParallelScale(home["parallel_scale"])
        camera.SetViewAngle(home["view_angle"])
        camera.OrthogonalizeViewUp()
        renderer.ResetCameraClippingRange()
        render_3d_snapshot()

    def render_3d_snapshot():
        width = max(viewer3d_label.winfo_width(), 320)
        height = max(viewer3d_label.winfo_height(), 240)
        render_window.SetSize(width, height)
        render_window.Render()

        window_to_image = vtk.vtkWindowToImageFilter()
        window_to_image.SetInput(render_window)
        window_to_image.ReadFrontBufferOff()
        window_to_image.Update()

        image_data = window_to_image.GetOutput()
        dimensions = image_data.GetDimensions()
        scalars = image_data.GetPointData().GetScalars()
        if scalars is None:
            return

        array = vtk_to_numpy(scalars).reshape(dimensions[1], dimensions[0], -1)
        array = np.flipud(array)
        mode = "RGBA" if array.shape[2] == 4 else "RGB"
        image = Image.fromarray(array.astype(np.uint8), mode=mode)
        photo = ImageTk.PhotoImage(image=image)
        viewer3d_label.configure(image=photo, text="")
        viewer3d_label.image = photo
        viewer3d_state["photo"] = photo

    def refresh_3d_view():
        if not state["path"]:
            clear_renderer()
            viewer3d_label.configure(image="", text=tr("view_3d_waiting"))
            viewer3d_label.image = None
            viewer3d_state["photo"] = None
            return
        folded = build_folded_part_polydata(state["path"])
        clear_renderer()
        top_actor = make_vtk_actor(vtk_backend, folded["top"], (0.45, 0.72, 0.98))
        bottom_actor = make_vtk_actor(vtk_backend, folded["bottom"], (0.99, 0.76, 0.20))
        side_actor = make_vtk_actor(vtk_backend, folded["sides"], (0.18, 0.68, 0.32))
        bend_actor = make_vtk_actor(vtk_backend, folded.get("bend_faces"), (0.18, 0.68, 0.32))
        for actor in (top_actor, bottom_actor, side_actor, bend_actor):
            if actor is not None:
                renderer.AddActor(actor)
        renderer.ResetCamera()
        camera = renderer.GetActiveCamera()
        camera.Azimuth(28)
        camera.Elevation(22)
        camera.Dolly(1.15)
        camera.OrthogonalizeViewUp()
        renderer.ResetCameraClippingRange()
        capture_camera_home()
        render_3d_snapshot()

    def set_split_ratio(left_fraction):
        root.update_idletasks()
        total_width = body_pane.winfo_width()
        if total_width <= 0:
            return
        try:
            body_pane.sash_place(0, int(total_width * left_fraction), 1)
        except Exception:
            pass
        root.after(40, lambda: redraw_geometry(fit_view=True))
        root.after(60, refresh_3d_view)

    def snap_point(x, y):
        if not state["segments"]:
            return x, y, False

        snap_radius = max(2.0, ((state["diag"] or 0.0) * 0.02 if state["diag"] else 10.0))
        best = None
        best_dist = None
        for segment in state["segments"]:
            sx, sy = segment["start"]
            ex, ey = segment["end"]
            mx, my = (sx + ex) / 2.0, (sy + ey) / 2.0
            for px, py in ((sx, sy), (ex, ey), (mx, my)):
                dist = math.hypot(x - px, y - py)
                if best_dist is None or dist < best_dist:
                    best_dist = dist
                    best = (px, py)

        if best is not None and best_dist <= snap_radius:
            return best[0], best[1], True
        return x, y, False

    measure = {
        "enabled": False,
        "step": 0,
        "seg1": None,
        "seg2": None,
        "seg1_point": None,
        "seg2_point": None,
        "p1_base": None,
        "p2_base": None,
        "mid_base": None,
        "dist": None,
        "dim_p1": None,
        "dim_p2": None,
    }
    point_measure = {"enabled": False, "step": 0, "p1": None}

    def update_button_states():
        btn_measure.configure(text=tr("measure_active") if measure["enabled"] else tr("measure"))
        btn_pmeasure.configure(text=tr("point_measure_active") if point_measure["enabled"] else tr("point_measure"))

    def reset_modes():
        measure.update(
            {
                "enabled": False,
                "step": 0,
                "seg1": None,
                "seg2": None,
                "seg1_point": None,
                "seg2_point": None,
                "p1_base": None,
                "p2_base": None,
                "mid_base": None,
                "dist": None,
                "dim_p1": None,
                "dim_p2": None,
            }
        )
        point_measure.update({"enabled": False, "step": 0, "p1": None})
        update_button_states()

    def toggle_measure():
        if point_measure["enabled"]:
            point_measure["enabled"] = False
            point_measure["step"] = 0

        if not measure["enabled"]:
            measure["enabled"] = True
            measure["step"] = 1
            measure["seg1"] = None
            measure["seg2"] = None
            measure["seg1_point"] = None
            measure["seg2_point"] = None
            measure["p1_base"] = None
            measure["p2_base"] = None
            measure["mid_base"] = None
            measure["dist"] = None
            measure["dim_p1"] = None
            measure["dim_p2"] = None
            set_status(tr("status_measure_pick_first"))
        else:
            measure["enabled"] = False
            measure["step"] = 0
            set_status(tr("status_measure_off"))
        update_button_states()

    def toggle_point_measure():
        if measure["enabled"]:
            measure["enabled"] = False
            measure["step"] = 0

        if not point_measure["enabled"]:
            point_measure["enabled"] = True
            point_measure["step"] = 1
            point_measure["p1"] = None
            set_status(tr("status_point_pick_first"))
        else:
            point_measure["enabled"] = False
            point_measure["step"] = 0
            set_status(tr("status_point_off"))
        update_button_states()

    def reset_dims():
        dim_records.clear()
        redraw_geometry(fit_view=False)
        if measure["enabled"]:
            measure["step"] = 1
            set_status(tr("status_measure_pick_first"))
        elif point_measure["enabled"]:
            point_measure["step"] = 1
            set_status(tr("status_point_pick_first"))
        else:
            set_status(tr("status_measure_off"))

    def text_plus():
        global TEXT_SIZE
        TEXT_SIZE += 1.0
        apply_text_size()

    def text_minus():
        global TEXT_SIZE
        TEXT_SIZE = max(4.0, TEXT_SIZE - 1.0)
        apply_text_size()

    def open_new_file():
        initial_dir = get_initial_folder(
            state["settings"],
            os.path.dirname(state["path"]) if state["path"] else None,
        )
        new_path = filedialog.askopenfilename(
            parent=root,
            initialdir=initial_dir,
            filetypes=[(tr("bendpart_files"), "*.bendpart"), (tr("all_files"), "*.*")],
            title=tr("choose_bendpart"),
        )
        if not new_path:
            return
        if not load_geometry(new_path):
            return
        reset_dims()
        reset_modes()
        redraw_geometry(fit_view=True)
        apply_text_size()
        refresh_3d_view()
        set_status(tr("file_loaded"))

    def open_settings_dialog():
        dialog = tk.Toplevel(root)
        dialog.title(tr("settings_title"))
        dialog.transient(root)
        dialog.grab_set()
        dialog.configure(bg="#20242c")
        dialog.resizable(False, False)

        content = ttk.Frame(dialog, style="App.TFrame", padding=14)
        content.pack(fill="both", expand=True)

        folder_var = tk.StringVar(value=state["settings"].get("default_folder", ""))
        reverse_var = tk.BooleanVar(value=state["settings"].get("reverse_angle_display", False))
        language_var = tk.StringVar(value=state["settings"].get("language", DEFAULT_SETTINGS["language"]))

        ttk.Label(content, text=tr("default_folder"), style="Meta.TLabel").grid(row=0, column=0, sticky="w")
        folder_entry = ttk.Entry(content, textvariable=folder_var, width=56)
        folder_entry.grid(row=1, column=0, padx=(0, 8), pady=(6, 12), sticky="ew")

        def browse_folder():
            selected = filedialog.askdirectory(
                parent=dialog,
                initialdir=get_initial_folder({"default_folder": folder_var.get()}),
                title=tr("choose_default_folder"),
            )
            if selected:
                folder_var.set(selected)

        ttk.Button(content, text=tr("choose_folder"), style="App.TButton", command=browse_folder).grid(row=1, column=1, pady=(6, 12))

        ttk.Label(content, text=tr("angle_display"), style="Meta.TLabel").grid(row=2, column=0, sticky="w")
        mode_row = ttk.Frame(content, style="App.TFrame")
        mode_row.grid(row=3, column=0, columnspan=2, sticky="w", pady=(6, 0))
        ttk.Radiobutton(mode_row, text=tr("outside_angle"), value=False, variable=reverse_var).pack(side="left")
        ttk.Radiobutton(mode_row, text=tr("inside_angle"), value=True, variable=reverse_var).pack(side="left", padx=(12, 0))

        ttk.Label(content, text=tr("language"), style="Meta.TLabel").grid(row=4, column=0, sticky="w", pady=(12, 0))
        lang_row = ttk.Frame(content, style="App.TFrame")
        lang_row.grid(row=5, column=0, columnspan=2, sticky="w", pady=(6, 0))
        ttk.Radiobutton(lang_row, text=tr("german"), value="de", variable=language_var).pack(side="left")
        ttk.Radiobutton(lang_row, text=tr("english"), value="en", variable=language_var).pack(side="left", padx=(12, 0))

        button_row = ttk.Frame(content, style="App.TFrame")
        button_row.grid(row=6, column=0, columnspan=2, sticky="e", pady=(14, 0))

        def save_and_close():
            folder_value = folder_var.get().strip()
            if folder_value and not os.path.isdir(folder_value):
                messagebox.showerror(tr("invalid_folder_title"), tr("invalid_folder_msg"), parent=dialog)
                return
            state["settings"]["default_folder"] = folder_value
            state["settings"]["reverse_angle_display"] = bool(reverse_var.get())
            state["settings"]["language"] = language_var.get() if language_var.get() in TRANSLATIONS else DEFAULT_SETTINGS["language"]
            save_settings(state["settings"])
            apply_ui_language()
            redraw_geometry(fit_view=False)
            dialog.destroy()

        ttk.Button(button_row, text=tr("cancel"), style="App.TButton", command=dialog.destroy).pack(side="right")
        ttk.Button(button_row, text=tr("save"), style="Accent.TButton", command=save_and_close).pack(side="right", padx=(0, 8))

        content.columnconfigure(0, weight=1)
        folder_entry.focus_set()

    def apply_ui_language():
        root.title(tr("app_title"))
        if "plot_frame" in ui_refs:
            ui_refs["plot_frame"].configure(text=tr("sheet_2d"))
        if "viewer3d_frame" in ui_refs:
            ui_refs["viewer3d_frame"].configure(text=tr("view_3d"))
        if "file_group" in ui_refs:
            ui_refs["file_group"].configure(text=tr("file_and_view"))
        if "measure_group" in ui_refs:
            ui_refs["measure_group"].configure(text=tr("measure"))
        if "text_group" in ui_refs:
            ui_refs["text_group"].configure(text=tr("text_group"))
        if "btn_open" in ui_refs:
            ui_refs["btn_open"].configure(text=tr("open"))
        if "btn_fit" in ui_refs:
            ui_refs["btn_fit"].configure(text=tr("center_view"))
        if "btn_rotate_2d" in ui_refs:
            ui_refs["btn_rotate_2d"].configure(text=tr("rotate_2d"))
        if "btn_settings" in ui_refs:
            ui_refs["btn_settings"].configure(text=tr("settings"))
        if "btn_clear_dims" in ui_refs:
            ui_refs["btn_clear_dims"].configure(text=tr("clear_dimensions"))
        if "btn_text_plus" in ui_refs:
            ui_refs["btn_text_plus"].configure(text=tr("text_plus"))
        if "btn_text_minus" in ui_refs:
            ui_refs["btn_text_minus"].configure(text=tr("text_minus"))
        for field_name, key in (
            ("thickness", "thickness"),
            ("material", "material"),
            ("angle_display", "angle_display"),
            ("upper_tool", "upper_tool"),
            ("lower_tool", "lower_tool"),
            ("special_combos", "special_combos"),
        ):
            caption_ref = ui_refs.get(f"info_caption_{field_name}")
            if caption_ref is not None:
                caption_ref.configure(text=tr(key))
        update_button_states()
        update_info_text()
        if not state["path"]:
            status_var.set(tr("status_measure_off"))
            viewer3d_label.configure(text=tr("view_3d_waiting"))

    def fit_2d_view():
        state["view_rotation_override"] = None
        redraw_geometry(fit_view=True)
        set_status(tr("status_fit_2d"))

    def rotate_2d_view():
        current = state.get("view_rotation_actual", 0) % 180
        state["view_rotation_override"] = 90 if current == 0 else 0
        redraw_geometry(fit_view=True)
        set_status(tr("status_rotate_2d", angle=state["view_rotation_override"]))

    def on_2d_zoom(canvas_x, canvas_y, zoom_factor):
        center = state.get("view_center")
        scale = state.get("view_scale")
        if center is None or scale in (None, 0):
            return
        world_before = canvas_to_world(canvas_x, canvas_y)
        state["view_scale"] = max(scale * zoom_factor, 0.01)
        world_after = canvas_to_world(canvas_x, canvas_y)
        state["view_center"] = (
            center[0] + (world_before[0] - world_after[0]),
            center[1] + (world_before[1] - world_after[1]),
        )
        redraw_geometry(fit_view=False)

    def on_canvas_click(event):
        x, y = canvas_to_world(event.x, event.y)

        if measure["enabled"]:
            if measure["step"] == 1:
                seg1, cp1 = find_nearest_segment((x, y), state["segments"])
                if seg1 is None:
                    return
                measure["seg1"] = seg1
                measure["seg1_point"] = cp1
                measure["step"] = 2
                set_status(tr("status_measure_pick_second"))
                redraw_geometry(fit_view=False)
                return

            if measure["step"] == 2:
                seg2, cp2 = find_nearest_segment((x, y), state["segments"])
                if seg2 is None:
                    return
                measure["seg2"] = seg2
                measure["seg2_point"] = cp2
                p1, p2, dist = closest_points_between_segments(
                    measure["seg1"]["start"],
                    measure["seg1"]["end"],
                    seg2["start"],
                    seg2["end"],
                )
                measure["p1_base"] = p1
                measure["p2_base"] = p2
                measure["mid_base"] = ((p1[0] + p2[0]) / 2.0, (p1[1] + p2[1]) / 2.0)
                measure["dist"] = dist
                measure["step"] = 3
                set_status(tr("status_measure_line_pos"))
                redraw_geometry(fit_view=False)
                return

            if measure["step"] == 3:
                p1_base = measure["p1_base"]
                p2_base = measure["p2_base"]
                mid_base = measure["mid_base"]
                dist = measure["dist"]
                if p1_base is None or p2_base is None or dist in (None, 0):
                    return

                sx0, sy0 = measure["seg1"]["start"]
                ex0, ey0 = measure["seg1"]["end"]
                dx, dy = ex0 - sx0, ey0 - sy0
                seg_len = math.hypot(dx, dy)
                if seg_len == 0:
                    vx = p2_base[0] - p1_base[0]
                    vy = p2_base[1] - p1_base[1]
                    base_len = math.hypot(vx, vy)
                    if base_len == 0:
                        return
                    tx, ty = -vy / base_len, vx / base_len
                else:
                    tx, ty = dx / seg_len, dy / seg_len

                vx = x - mid_base[0]
                vy = y - mid_base[1]
                t_param = vx * tx + vy * ty
                dim_p1 = (p1_base[0] + tx * t_param, p1_base[1] + ty * t_param)
                dim_p2 = (p2_base[0] + tx * t_param, p2_base[1] + ty * t_param)

                measure["dim_p1"] = dim_p1
                measure["dim_p2"] = dim_p2
                measure["step"] = 4
                set_status(tr("status_measure_text_pos"))
                redraw_geometry(fit_view=False)
                return

            if measure["step"] == 4 and measure["dist"] is not None:
                dim_records.append(
                    {
                        "type": "line_distance",
                        "p1_base": measure["p1_base"],
                        "p2_base": measure["p2_base"],
                        "dim_p1": measure["dim_p1"],
                        "dim_p2": measure["dim_p2"],
                        "dist": measure["dist"],
                        "text_pos": (x, y),
                    }
                )
                measure["step"] = 1
                measure["seg1"] = None
                measure["seg2"] = None
                measure["seg1_point"] = None
                measure["seg2_point"] = None
                measure["p1_base"] = None
                measure["p2_base"] = None
                measure["mid_base"] = None
                measure["dist"] = None
                measure["dim_p1"] = None
                measure["dim_p2"] = None
                set_status(tr("status_measure_pick_first"))
                redraw_geometry(fit_view=False)
                return

        if point_measure["enabled"]:
            if point_measure["step"] == 1:
                sx, sy, _ = snap_point(x, y)
                point_measure["p1"] = (sx, sy)
                point_measure["step"] = 2
                set_status(tr("status_point_pick_second"))
                redraw_geometry(fit_view=False)
                return

            if point_measure["step"] == 2 and point_measure["p1"] is not None:
                sx, sy, _ = snap_point(x, y)
                p1 = point_measure["p1"]
                p2 = (sx, sy)
                dim_records.append(
                    {
                        "type": "point_distance",
                        "p1": p1,
                        "p2": p2,
                        "dist": math.hypot(p2[0] - p1[0], p2[1] - p1[1]),
                    }
                )
                point_measure["p1"] = None
                point_measure["step"] = 1
                set_status(tr("status_point_pick_first"))
                redraw_geometry(fit_view=False)

    control_groups = ttk.Frame(controls_frame, style="App.TFrame")
    control_groups.pack(fill="x")

    measure_group = ttk.LabelFrame(control_groups, text=tr("measure"), style="Card.TLabelframe", padding=6)
    measure_group.pack(side="left", padx=(0, 10))
    file_group = ttk.LabelFrame(control_groups, text=tr("file_and_view"), style="Card.TLabelframe", padding=6)
    file_group.pack(side="left", padx=(0, 10))
    text_group = ttk.LabelFrame(control_groups, text=tr("text_group"), style="Card.TLabelframe", padding=6)
    text_group.pack(side="left")
    ui_refs["plot_frame"] = plot_frame
    ui_refs["viewer3d_frame"] = viewer3d_frame
    ui_refs["file_group"] = file_group
    ui_refs["measure_group"] = measure_group
    ui_refs["text_group"] = text_group

    btn_measure = ttk.Button(measure_group, text=tr("measure"), style="Measure.TButton", command=toggle_measure)
    btn_measure.grid(row=0, column=0, padx=4, pady=4, sticky="ew")
    btn_pmeasure = ttk.Button(measure_group, text=tr("point_measure"), style="Measure.TButton", command=toggle_point_measure)
    btn_pmeasure.grid(row=0, column=1, padx=4, pady=4, sticky="ew")
    btn_clear_dims = ttk.Button(measure_group, text=tr("clear_dimensions"), style="App.TButton", command=reset_dims)
    btn_clear_dims.grid(row=0, column=2, padx=4, pady=4, sticky="ew")

    btn_open = ttk.Button(file_group, text=tr("open"), style="App.TButton", command=open_new_file)
    btn_open.grid(row=0, column=0, padx=4, pady=4, sticky="ew")
    btn_fit = ttk.Button(file_group, text=tr("center_view"), style="Accent.TButton", command=fit_2d_view)
    btn_fit.grid(row=0, column=1, padx=4, pady=4, sticky="ew")
    btn_rotate_2d = ttk.Button(file_group, text=tr("rotate_2d"), style="App.TButton", command=rotate_2d_view)
    btn_rotate_2d.grid(row=0, column=2, padx=4, pady=4, sticky="ew")
    btn_settings = ttk.Button(file_group, text=tr("settings"), style="App.TButton", command=open_settings_dialog)
    btn_settings.grid(row=0, column=3, padx=4, pady=4, sticky="ew")

    btn_text_plus = ttk.Button(text_group, text=tr("text_plus"), style="App.TButton", command=text_plus)
    btn_text_plus.grid(row=0, column=0, padx=4, pady=4, sticky="ew")
    btn_text_minus = ttk.Button(text_group, text=tr("text_minus"), style="App.TButton", command=text_minus)
    btn_text_minus.grid(row=0, column=1, padx=4, pady=4, sticky="ew")
    ui_refs.update(
        {
            "btn_open": btn_open,
            "btn_fit": btn_fit,
            "btn_rotate_2d": btn_rotate_2d,
            "btn_settings": btn_settings,
            "btn_measure": btn_measure,
            "btn_pmeasure": btn_pmeasure,
            "btn_clear_dims": btn_clear_dims,
            "btn_text_plus": btn_text_plus,
            "btn_text_minus": btn_text_minus,
        }
    )

    def on_canvas_resize(event):
        if event.width > 10 and event.height > 10:
            state["canvas_size"] = (event.width, event.height)
            root.after_idle(lambda: redraw_geometry(fit_view=state.get("view_scale") is None))

    def start_2d_pan(event):
        state["pan_anchor"] = (event.x, event.y)

    def move_2d_pan(event):
        anchor = state.get("pan_anchor")
        center = state.get("view_center")
        scale = state.get("view_scale")
        if anchor is None or center is None or scale in (None, 0):
            return
        dx = event.x - anchor[0]
        dy = event.y - anchor[1]
        state["view_center"] = (
            center[0] - dx / scale,
            center[1] + dy / scale,
        )
        state["pan_anchor"] = (event.x, event.y)
        redraw_geometry(fit_view=False)

    def end_2d_pan(event):
        state["pan_anchor"] = None

    def on_2d_mousewheel(event):
        zoom_factor = 1.12 if getattr(event, "delta", 0) > 0 else 1.0 / 1.12
        on_2d_zoom(event.x, event.y, zoom_factor)

    def on_2d_mousewheel_linux_up(event):
        on_2d_zoom(event.x, event.y, 1.12)

    def on_2d_mousewheel_linux_down(event):
        on_2d_zoom(event.x, event.y, 1.0 / 1.12)

    canvas_widget.bind("<Configure>", on_canvas_resize)
    canvas_widget.bind("<Button-1>", on_canvas_click)
    canvas_widget.bind("<ButtonPress-2>", start_2d_pan)
    canvas_widget.bind("<B2-Motion>", move_2d_pan)
    canvas_widget.bind("<ButtonRelease-2>", end_2d_pan)
    canvas_widget.bind("<ButtonPress-3>", start_2d_pan)
    canvas_widget.bind("<B3-Motion>", move_2d_pan)
    canvas_widget.bind("<ButtonRelease-3>", end_2d_pan)
    canvas_widget.bind("<MouseWheel>", on_2d_mousewheel)
    canvas_widget.bind("<Button-4>", on_2d_mousewheel_linux_up)
    canvas_widget.bind("<Button-5>", on_2d_mousewheel_linux_down)

    def on_3d_resize(event):
        if event.width > 10 and event.height > 10:
            root.after_idle(render_3d_snapshot)

    def pan_3d_camera(dx, dy):
        camera = renderer.GetActiveCamera()
        position = np.array(camera.GetPosition(), dtype=float)
        focal_point = np.array(camera.GetFocalPoint(), dtype=float)
        view_up = np.array(camera.GetViewUp(), dtype=float)
        direction = focal_point - position
        distance = np.linalg.norm(direction)
        if distance <= 1e-9:
            return

        direction /= distance
        view_up_norm = np.linalg.norm(view_up)
        if view_up_norm <= 1e-9:
            return
        view_up /= view_up_norm
        right = np.cross(direction, view_up)
        right_norm = np.linalg.norm(right)
        if right_norm <= 1e-9:
            return
        right /= right_norm
        up = np.cross(right, direction)
        up_norm = np.linalg.norm(up)
        if up_norm <= 1e-9:
            return
        up /= up_norm

        scale = max(distance * 0.0014, 0.2)
        shift = (-dx * scale) * right + (dy * scale) * up
        camera.SetPosition(*(position + shift))
        camera.SetFocalPoint(*(focal_point + shift))
        renderer.ResetCameraClippingRange()

    def start_3d_drag(event):
        viewer3d_state["drag"] = (event.x, event.y)
        viewer3d_state["drag_button"] = event.num

    def move_3d_drag(event):
        last_drag = viewer3d_state.get("drag")
        if not last_drag:
            return
        dx = event.x - last_drag[0]
        dy = event.y - last_drag[1]
        drag_button = viewer3d_state.get("drag_button")
        if drag_button == 3:
            pan_3d_camera(dx, dy)
        else:
            camera = renderer.GetActiveCamera()
            camera.Azimuth(-dx * 0.6)
            camera.Elevation(dy * 0.6)
            camera.OrthogonalizeViewUp()
            renderer.ResetCameraClippingRange()
        viewer3d_state["drag"] = (event.x, event.y)
        render_3d_snapshot()

    def end_3d_drag(event):
        viewer3d_state["drag"] = None
        viewer3d_state["drag_button"] = None

    def on_3d_mousewheel(event):
        camera = renderer.GetActiveCamera()
        if getattr(event, "delta", 0) > 0:
            camera.Dolly(1.12)
        else:
            camera.Dolly(0.89)
        renderer.ResetCameraClippingRange()
        render_3d_snapshot()

    def on_3d_mousewheel_linux_up(event):
        camera = renderer.GetActiveCamera()
        camera.Dolly(1.12)
        renderer.ResetCameraClippingRange()
        render_3d_snapshot()

    def on_3d_mousewheel_linux_down(event):
        camera = renderer.GetActiveCamera()
        camera.Dolly(0.89)
        renderer.ResetCameraClippingRange()
        render_3d_snapshot()

    viewer3d_label.bind("<Configure>", on_3d_resize)
    viewer3d_label.bind("<ButtonPress-1>", start_3d_drag)
    viewer3d_label.bind("<B1-Motion>", move_3d_drag)
    viewer3d_label.bind("<ButtonPress-3>", start_3d_drag)
    viewer3d_label.bind("<B3-Motion>", move_3d_drag)
    viewer3d_label.bind("<ButtonRelease-1>", end_3d_drag)
    viewer3d_label.bind("<ButtonRelease-3>", end_3d_drag)
    viewer3d_label.bind("<Double-Button-1>", lambda event: reset_3d_camera())
    viewer3d_label.bind("<MouseWheel>", on_3d_mousewheel)
    viewer3d_label.bind("<Button-4>", on_3d_mousewheel_linux_up)
    viewer3d_label.bind("<Button-5>", on_3d_mousewheel_linux_down)

    def on_close():
        root.destroy()

    root.protocol("WM_DELETE_WINDOW", on_close)

    apply_ui_language()
    redraw_geometry(fit_view=True)
    refresh_3d_view()
    update_button_states()
    root.update_idletasks()
    set_split_ratio(0.56)
    root.mainloop()
# ------------------------------------------------------------
# Entry point
# ------------------------------------------------------------

def main():
    path = None
    if len(sys.argv) < 2:
        path = None
    else:
        arg = sys.argv[1]
        if os.path.isdir(arg):
            path = None
        else:
            path = arg

    interactive_dim(path)


if __name__ == "__main__":
    main()
