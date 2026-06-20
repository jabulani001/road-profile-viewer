# Route Analyzer

Lade eine GPX-Datei hoch und analysiere deine Route — Höhenprofil, Kalorien oder Tankverbrauch.

## Features

- GPX-Datei hochladen oder Demo Route nutzen
- Interaktives Höhenprofil (Plotly)
- **Fahrrad** — Kalorienverbrauch + Zeit (MET-basiert)
- **Laufen** — Kalorienverbrauch + Zeit
- **Auto** — Kraftstoffverbrauch in Liter (berücksichtigt Steigung)

## Installation

```bash
uv sync
```

## Starten

```bash
uv run src/road_profile_viewer/main.py
```

Dann im Browser: `http://127.0.0.1:8050/`

## Geplante Features

- [ ] Kartenansicht (Leaflet)
- [ ] CO2-Vergleich Auto vs. Fahrrad
- [ ] Streckenvergleich (mehrere GPX Dateien)
- [ ] Export als PDF/PNG
- [ ] Herzfrequenzzonen (Fahrrad/Laufen)
