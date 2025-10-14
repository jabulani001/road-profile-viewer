# Road Profile Viewer

An interactive 2D road profile visualization tool built with Dash and Plotly.

## Features

- Displays a road profile with 50+ points from (0,0) to (150,y)
- Visualizes a camera mounted at (0, 1.5)
- Interactive camera ray with adjustable angle
- Calculates and highlights intersection between camera ray and road profile
- Shows distance from camera to intersection point on hover

## Installation

This project uses [uv](https://github.com/astral-sh/uv) for dependency management.

```bash
# Install dependencies
uv sync
```

## Usage

Run the application:

```bash
uv run src/road_profile_viewer/main.py
```

Then open your browser to `http://127.0.0.1:8050/` to view the interactive visualization.

## Project Structure

```
road-profile-viewer/
├── src/
│   └── road_profile_viewer/
│       ├── __init__.py
│       └── main.py          # Main application (intentionally monolithic for educational purposes)
├── pyproject.toml
├── README.md
└── .gitignore
```

## Educational Note

This project intentionally keeps all code in a single file (`main.py`) as a starting point for demonstrating code organization best practices. In production, you would typically separate concerns into multiple modules.
