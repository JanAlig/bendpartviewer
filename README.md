# BPV v3 - Bendpart Visualizer

BPV v3 is a desktop viewer for Bystronic `.bendpart` files.

It combines a precise 2D flat-pattern view with a folded 3D sheet-metal view in one application, including measurement tools, persistent settings, and a Windows installer.

---

## English

### Overview

BPV v3 was built to make `.bendpart` files easier to inspect and understand in daily production work.

The application can:
- open `.bendpart` files stored as plain XML or gzip-compressed XML
- display the 2D flat pattern
- display the folded 3D part with material thickness
- calculate bend radii and folded geometry from the Bendpart surface model
- show bend angles and tool information
- measure distances directly in the 2D view
- store user settings between sessions

### Main Features

- Combined 2D and 3D workspace in one window
- Accurate folded 3D geometry for sheet-metal parts
- Material thickness included in the 3D model
- Bend radii displayed in the folded state
- Correct top side / underside coloring in 3D
- 2D measuring tools
  - line-to-line measurement
  - point-to-point measurement
- Bend-line display with angle labels
- Tool information for bends
  - default tool combinations stay hidden on the bend line
  - non-default combinations are shown directly on the bend line
- Persistent settings
  - default folder
  - language: German / English
  - angle display mode: outside angle / inside angle
- Bilingual UI
- Windows installer with:
  - desktop shortcut
  - Start menu shortcut
  - Installed Apps / uninstall entry in Windows

### 2D Viewer

The 2D viewer focuses on the flat pattern and supports:
- outer and inner contours
- bend lines
  - angle < 0: red dashed
  - angle > 0: blue dotted
  - angle = 0: blue dashed
- horizontal angle labels with a white background
- zoom with mouse wheel
- panning
- measurement workflow directly on the geometry

### 3D Viewer

The 3D viewer builds the folded part from the Bendpart surface model and includes:
- folded sheet-metal geometry
- thickness-aware faces
- bend radii
- top side / underside / bend face coloring
- interactive mouse navigation

### Settings

BPV v3 stores settings in `bendpart_viewer_settings.json`.

Currently supported settings:
- default folder
- language
- angle display mode

Angle display modes:
- `Aussenwinkel` / `Outside angle`: standard display
- `Innenwinkel` / `Inside angle`: reverse display

Example:
- `60°` can be displayed as `120°` in inside-angle mode

### Installation

For normal users on Windows:

1. Download `BPV_V3_Setup.exe` from the GitHub release
2. Run the installer
3. Start the program from the desktop shortcut or Start menu

Notes:
- intended for modern 64-bit Windows systems
- Python is not required on the target machine



### Development

Main entry file:

- `BendPartViewer_V3.py`

Example start commands:

```bash
python BendPartViewer_V3.py
python BendPartViewer_V3.py path\to\part.bendpart
python BendPartViewer_V3.py path\to\folder
```

---

## Deutsch

### Überblick

BPV v3 ist ein Desktop-Viewer für Bystronic `.bendpart` Dateien.

Die Anwendung wurde dafür gemacht, `.bendpart` Dateien im Alltag schneller und klarer zu prüfen.

Sie kann:
- `.bendpart` Dateien als normales XML oder gzip-komprimiertes XML öffnen
- die 2D-Abwicklung anzeigen
- das gefaltete 3D-Bauteil mit Materialdicke anzeigen
- Biegeradien und die gefaltete Geometrie aus dem Bendpart-Surface-Modell berechnen
- Biegewinkel und Werkzeuginformationen anzeigen
- Abstände direkt in der 2D-Ansicht messen
- Benutzereinstellungen dauerhaft speichern

### Hauptfunktionen

- Kombinierte 2D- und 3D-Ansicht in einem Fenster
- Exakte gefaltete 3D-Geometrie für Blechbauteile
- Materialdicke im 3D-Modell enthalten
- Biegeradien im gefalteten Zustand sichtbar
- Korrekte Farbtrennung für Oberseite / Unterseite / Biegebereiche
- 2D-Messfunktionen
  - Linien-zu-Linien-Messung
  - Punkt-zu-Punkt-Messung
- Anzeige von Biegelinien mit Winkeltexten
- Werkzeuganzeige für Biegungen
  - Standardkombinationen werden auf der Biegelinie nicht angezeigt
  - abweichende Kombinationen werden direkt auf der Biegelinie angezeigt
- Persistente Einstellungen
  - Standardordner
  - Sprache: Deutsch / Englisch
  - Winkelanzeige: Aussenwinkel / Innenwinkel
- Zweisprachige Oberfläche
- Windows-Installer mit:
  - Desktop-Verknüpfung
  - Startmenü-Eintrag
  - Eintrag in den installierten Programmen von Windows

### 2D-Ansicht

Die 2D-Ansicht konzentriert sich auf die Abwicklung und unterstützt:
- Außen- und Innenkonturen
- Biegelinien
  - Winkel < 0: rot gestrichelt
  - Winkel > 0: blau punktiert
  - Winkel = 0: blau gestrichelt
- horizontale Winkeltexte mit weißem Hintergrund
- Zoom mit dem Mausrad
- Pan / Verschieben
- Messfunktionen direkt auf der Geometrie

### 3D-Ansicht

Die 3D-Ansicht baut das gefaltete Teil aus dem Bendpart-Surface-Modell auf und enthält:
- gefaltete Blechgeometrie
- Flächen mit Materialdicke
- Biegeradien
- Farbtrennung für Oberseite, Unterseite und Biegebereiche
- interaktive Mausnavigation

### Einstellungen

BPV v3 speichert die Einstellungen in `bendpart_viewer_settings.json`.

Aktuell unterstützt:
- Standardordner
- Sprache
- Winkelanzeige

Modi für die Winkelanzeige:
- `Aussenwinkel`: Standardanzeige
- `Innenwinkel`: umgekehrte Anzeige

Beispiel:
- `60°` kann im Modus `Innenwinkel` als `120°` angezeigt werden

### Installation

Für normale Windows-Benutzer:

1. `BPV_V3_Setup.exe` aus dem GitHub-Release herunterladen
2. Installer starten
3. Programm über Desktop oder Startmenü öffnen

Hinweise:
- gedacht für aktuelle 64-Bit-Windows-Systeme
- auf dem Zielrechner ist keine Python-Installation nötig


### Entwicklung

Zentrale Datei:

- `BendPartViewer_V3.py`

Beispielaufrufe:

```bash
python BendPartViewer_V3.py
python BendPartViewer_V3.py pfad\zur\datei.bendpart
python BendPartViewer_V3.py pfad\zum\ordner
```
