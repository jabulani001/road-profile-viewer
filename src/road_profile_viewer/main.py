"""
Route Analyzer - Höhenprofil, Kalorien & Kraftstoffverbrauch
"""

import base64
import math

import defusedxml.ElementTree as ET
import numpy as np
from dash import Dash, html, dcc, Input, Output, State, ctx
import plotly.graph_objects as go


# ─────────────────────────────────────────────────────────────
# GPX PARSING
# ─────────────────────────────────────────────────────────────

def haversine(lat1, lon1, lat2, lon2):
    """Distanz zwischen zwei GPS-Koordinaten in km."""
    R = 6371.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    a = (math.sin((phi2 - phi1) / 2) ** 2
         + math.cos(phi1) * math.cos(phi2)
         * math.sin(math.radians(lon2 - lon1) / 2) ** 2)
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def parse_gpx(xml_string):
    """GPX-XML parsen, gibt (eles, distances_km, lats, lons) zurück oder None."""
    try:
        root = ET.fromstring(xml_string)
    except ET.ParseError:
        return None

    ns_match = root.tag.split('}')[0].lstrip('{') if '}' in root.tag else ''
    prefix = f'{{{ns_match}}}' if ns_match else ''

    trkpts = root.findall(f'.//{prefix}trkpt')
    if not trkpts:
        return None

    lats, lons, eles = [], [], []
    for pt in trkpts:
        try:
            lat = float(pt.get('lat'))
            lon = float(pt.get('lon'))
        except (TypeError, ValueError):
            continue
        ele_el = pt.find(f'{prefix}ele')
        try:
            ele = float(ele_el.text) if ele_el is not None else 0.0
        except (TypeError, ValueError):
            ele = 0.0
        eles.append(ele)
        lats.append(lat)
        lons.append(lon)

    if len(lats) < 2:
        return None

    distances = [0.0]
    for i in range(1, len(lats)):
        distances.append(distances[-1] + haversine(lats[i-1], lons[i-1], lats[i], lons[i]))

    return eles, distances, lats, lons


# ─────────────────────────────────────────────────────────────
# DEMO ROUTE
# ─────────────────────────────────────────────────────────────

def demo_route():
    """Synthetische 12 km hügelige Demo-Route (keine GPS-Koordinaten)."""
    n = 300
    t = np.linspace(0, 4 * math.pi, n)
    eles = (250 + 100 * np.sin(t) + 25 * np.sin(5 * t)).tolist()
    distances = np.linspace(0, 12, n).tolist()
    return eles, distances, [], []


# ─────────────────────────────────────────────────────────────
# BERECHNUNGEN
# ─────────────────────────────────────────────────────────────

def elevation_stats(eles):
    """Gibt (Aufstieg_m, Abstieg_m) zurück."""
    gain = loss = 0.0
    for i in range(1, len(eles)):
        d = eles[i] - eles[i - 1]
        if d > 0:
            gain += d
        else:
            loss -= d
    return gain, loss


def calories_cycling(weight_kg, distance_km, gain_m, speed_kmh=20):
    """Kalorienverbrauch Fahrrad (MET-basiert)."""
    time_h = distance_km / max(speed_kmh, 1)
    base = 8.0 * weight_kg * time_h
    climb = (gain_m / 100) * (weight_kg / 10) * 10
    return base + climb


def calories_running(weight_kg, distance_km, gain_m):
    """Kalorienverbrauch Laufen."""
    base = weight_kg * distance_km
    climb = gain_m * 0.1 * (weight_kg / 70)
    return base + climb


def fuel_liters(distance_km, gain_m, loss_m, base_l100=7.0):
    """Kraftstoffverbrauch in Litern. Bergauf mehr, bergab etwas weniger."""
    base = distance_km * base_l100 / 100
    extra = gain_m * 0.05 / 100
    saved = loss_m * 0.01 / 100
    return max(0.0, base + extra - saved)


# ─────────────────────────────────────────────────────────────
# DASH APP
# ─────────────────────────────────────────────────────────────

app = Dash(__name__)

app.layout = html.Div([
    html.H1("Route Analyzer"),

    html.Div([
        dcc.Upload(
            id='gpx-upload',
            children=html.Button("GPX Datei hochladen"),
            accept='.gpx',
        ),
        html.Button("Demo Route", id='demo-btn', n_clicks=0,
                    style={'marginLeft': '10px'}),
        html.Span(id='file-info', style={'marginLeft': '10px', 'color': 'grey'}),
    ]),

    html.Div([
        html.Label("Modus:"),
        dcc.RadioItems(
            id='mode',
            options=[
                {'label': ' Fahrrad', 'value': 'bike'},
                {'label': ' Laufen',  'value': 'run'},
                {'label': ' Auto',    'value': 'car'},
            ],
            value='bike',
            inline=True,
            style={'display': 'inline-block', 'marginLeft': '10px'},
        ),
    ], style={'marginTop': '15px'}),

    html.Div(id='person-inputs', children=[
        html.Label("Gewicht (kg):"),
        dcc.Input(id='weight', type='number', value=75, min=30, max=200,
                  style={'width': '80px', 'marginLeft': '5px'}),
        html.Label(" Geschwindigkeit (km/h):", style={'marginLeft': '15px'}),
        dcc.Input(id='speed', type='number', value=20, min=5, max=60,
                  style={'width': '80px', 'marginLeft': '5px'}),
    ], style={'marginTop': '10px'}),

    html.Div(id='car-inputs', children=[
        html.Label("Verbrauch (L/100km):"),
        dcc.Input(id='fuel-base', type='number', value=7.0, min=3, max=30, step=0.5,
                  style={'width': '80px', 'marginLeft': '5px'}),
    ], style={'marginTop': '10px', 'display': 'none'}),

    dcc.Store(id='route-data'),

    dcc.Graph(id='elevation-chart', style={'marginTop': '20px'}),

    dcc.Graph(id='map-chart', style={'marginTop': '10px'}),

    html.Div(id='results', style={'marginTop': '20px', 'fontSize': '18px'}),
])


@app.callback(
    Output('person-inputs', 'style'),
    Output('car-inputs', 'style'),
    Input('mode', 'value'),
)
def toggle_inputs(mode):
    show = {'marginTop': '10px'}
    hide = {'marginTop': '10px', 'display': 'none'}
    if mode == 'car':
        return hide, show
    return show, hide


@app.callback(
    Output('route-data', 'data'),
    Output('file-info', 'children'),
    Input('gpx-upload', 'contents'),
    Input('demo-btn', 'n_clicks'),
    State('gpx-upload', 'filename'),
    prevent_initial_call=True,
)
def load_route(contents, n_clicks, filename):
    if ctx.triggered_id == 'demo-btn':
        eles, distances, lats, lons = demo_route()
        return {'eles': eles, 'distances': distances, 'lats': lats, 'lons': lons}, "Demo Route (12 km)"

    if contents is None:
        return None, ""

    try:
        _, content_string = contents.split(',', 1)
        xml_bytes = base64.b64decode(content_string)
        result = parse_gpx(xml_bytes.decode('utf-8', errors='replace'))
    except Exception:
        return None, "Fehler beim Lesen der GPX Datei."

    if result is None:
        return None, "Fehler beim Lesen der GPX Datei."
    eles, distances, lats, lons = result
    return (
        {'eles': eles, 'distances': distances, 'lats': lats, 'lons': lons},
        f"{filename} geladen ({distances[-1]:.1f} km)"
    )


@app.callback(
    Output('elevation-chart', 'figure'),
    Output('map-chart', 'figure'),
    Output('results', 'children'),
    Input('route-data', 'data'),
    Input('mode', 'value'),
    Input('weight', 'value'),
    Input('speed', 'value'),
    Input('fuel-base', 'value'),
)
def update_charts(data, mode, weight, speed, fuel_base):
    if data is None:
        empty = go.Figure()
        empty.update_layout(
            title="Keine Route geladen — GPX hochladen oder Demo Route klicken",
            xaxis_title="Distanz (km)",
            yaxis_title="Höhe (m)",
        )
        return empty, go.Figure(), ""

    eles = data['eles']
    distances = data['distances']
    lats = data.get('lats', [])
    lons = data.get('lons', [])
    gain, loss = elevation_stats(eles)
    total_km = max(distances[-1], 0.001)

    # Elevation chart
    elev_fig = go.Figure()
    elev_fig.add_trace(go.Scatter(
        x=distances,
        y=eles,
        fill='tozeroy',
        mode='lines',
        name='Höhenprofil',
        line=dict(color='#2196F3', width=2),
        hovertemplate='%{x:.2f} km | %{y:.0f} m<extra></extra>',
    ))
    elev_fig.update_layout(
        title=f"Höhenprofil — {total_km:.1f} km | +{gain:.0f} m / -{loss:.0f} m",
        xaxis_title="Distanz (km)",
        yaxis_title="Höhe (m)",
        hovermode='x unified',
    )

    # Map chart
    if lats and lons:
        center_lat = sum(lats) / len(lats)
        center_lon = sum(lons) / len(lons)
        map_fig = go.Figure(go.Scattermapbox(
            lat=lats,
            lon=lons,
            mode='lines+markers',
            marker=dict(
                size=5,
                color=eles,
                colorscale='RdYlGn',
                reversescale=True,
                colorbar=dict(title='Höhe (m)'),
            ),
            line=dict(width=3, color='#2196F3'),
            hovertemplate='%{lat:.5f}, %{lon:.5f}<extra></extra>',
            name='Route',
        ))
        map_fig.update_layout(
            mapbox=dict(
                style='open-street-map',
                center=dict(lat=center_lat, lon=center_lon),
                zoom=12,
            ),
            margin=dict(l=0, r=0, t=30, b=0),
            title='Route auf Karte (Farbe = Höhe)',
            height=450,
        )
    else:
        map_fig = go.Figure()
        map_fig.update_layout(
            title='Karte nur mit GPX-Upload verfügbar (Demo hat keine GPS-Koordinaten)',
            height=80,
            margin=dict(t=30, b=0),
        )

    # Results
    weight = weight or 75
    speed = speed or 20
    fuel_base = fuel_base or 7.0

    if mode == 'bike':
        kcal = calories_cycling(weight, total_km, gain, speed)
        lines = [
            html.B("Fahrrad"), html.Br(),
            f"Distanz: {total_km:.1f} km", html.Br(),
            f"Höhengewinn: {gain:.0f} m  |  Höhenverlust: {loss:.0f} m", html.Br(),
            f"Kalorienverbrauch: {kcal:.0f} kcal", html.Br(),
            f"Geschätzte Zeit: {total_km / speed * 60:.0f} min",
        ]
    elif mode == 'run':
        kcal = calories_running(weight, total_km, gain)
        lines = [
            html.B("Laufen"), html.Br(),
            f"Distanz: {total_km:.1f} km", html.Br(),
            f"Höhengewinn: {gain:.0f} m  |  Höhenverlust: {loss:.0f} m", html.Br(),
            f"Kalorienverbrauch: {kcal:.0f} kcal", html.Br(),
            f"Geschätzte Zeit: {total_km / speed * 60:.0f} min",
        ]
    else:
        liters = fuel_liters(total_km, gain, loss, fuel_base)
        lines = [
            html.B("Auto"), html.Br(),
            f"Distanz: {total_km:.1f} km", html.Br(),
            f"Höhengewinn: {gain:.0f} m  |  Höhenverlust: {loss:.0f} m", html.Br(),
            f"Kraftstoffverbrauch: {liters:.2f} L", html.Br(),
            f"Eff. Verbrauch: {liters / total_km * 100:.1f} L/100km",
        ]

    return elev_fig, map_fig, lines


def main():
    print("Route Analyzer läuft auf http://127.0.0.1:8050/")
    app.run(debug=True)


if __name__ == '__main__':
    main()
