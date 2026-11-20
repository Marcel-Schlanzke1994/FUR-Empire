# Bearbeitbare Originale

- Die SVG-Master liegen nach Paketen unter diesem Ordner. Die Kopien in `01_TERRA` und `02_ORBIT` sind direkt im Spiel nutzbar.
- `terra` und `orbit` enthalten die flachen nativen PNG-Master bildgenerierter Motive, üblicherweise mit passender `.prompt.txt`-Datei. Für Social, technische Overlays, Kacheln und Effekte existieren zusätzlich tatsächlich getrennte OpenRaster-Layer, soweit bei der Produktion angelegt.
- Die Atlas-Originaldatei enthält separate Terrain-Layer und Grundterrain. Die Rechtecke aus der Atlas-JSON bestimmen den Zuschnitt jedes enthaltenen Tiles.
- Die fünf Effekt-Master enthalten Partikel, Farbe/Kern und Streulicht in getrennten Ebenen. Die statischen Varianten stammen aus dem Bildindex, den jede JSON-Datei unter `static_frame` angibt.
- `orbit/concepts` enthält Silhouettenstudien und Motivbriefings aus der Vorproduktion.
