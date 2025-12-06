# bendpartviewer
a viewer for Bystronic .bendparts


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
