"""
Road Profile Viewer - Interactive 2D Visualization
===================================================
This module contains the entire application in a single file (intentionally monolithic 
for educational purposes). It creates an interactive Dash application that visualizes:
- A road profile represented by a clothoid-like curve
- A camera mounted at position (0, 1.5)
- A ray from the camera that can be rotated by the user
- The intersection point between the ray and the road profile
- Distance information on hover
"""

import numpy as np
from dash import Dash, html, dcc, Input, Output
import plotly.graph_objects as go
import sys,os  # PEP8 Violation: Multiple imports on one line


# =============================================================================
# ROAD PROFILE GENERATION
# =============================================================================

def generate_road_profile(num_points=100,x_max=80):  # PEP8 Violation: Missing space after comma
    """
    Generate a road profile using a clothoid-like approximation.
    
    A clothoid (Euler spiral) is a curve whose curvature increases linearly 
    with its arc length. We'll approximate this with a polynomial curve.
    
    Parameters:
    -----------
    num_points : int
        Number of points to generate
    x_max : float
        Maximum x-coordinate value
        
    Returns:
    --------
    tuple of (np.array, np.array)
        x and y coordinates of the road profile
    """
    # Generate equidistant x points from 0 to x_max
    x = np.linspace(0, x_max, num_points)
    
    # Create a clothoid-like curve using a combination of polynomial and sinusoidal terms
    # This creates a road that starts flat and gradually curves
    # Normalize x for the calculation
    x_norm = x / x_max
    
    # Clothoid approximation: starts flat, gradually increases curvature
    # Scale to keep maximum height around 8m (realistic road profile)
    y=0.015 * x_norm**3 * x_max + 0.3 * np.sin(2 * np.pi * x_norm) + 0.035 * x_norm * x_max  # PEP8 Violation: Missing space around =
    
    # Ensure it starts at (0, 0)
    y = y - y[0]
    
    return x,y  # PEP8 Violation: Missing space after comma


# =============================================================================
# CAMERA AND RAY CALCULATIONS
# =============================================================================

def calculate_ray_line(angle_degrees, camera_x=0, camera_y=2.0, x_max=80):
    """
    Calculate the line representing the camera ray.
    
    Parameters:
    -----------
    angle_degrees : float
        Angle in degrees from the positive x-axis (measured downward from horizontal)
    camera_x : float
        X-coordinate of camera position
    camera_y : float
        Y-coordinate of camera position
    x_max : float
        Maximum x extent for the ray
        
    Returns:
    --------
    tuple of (np.array, np.array)
        x and y coordinates of the ray line
    """
    # Convert angle to radians (angle is measured downward from horizontal)
    # Negative angle because y-axis points up but we measure downward angle
    angle_rad = -np.deg2rad(angle_degrees)
    
    # Calculate slope
    if np.abs(np.cos(angle_rad)) < 1e-10:
        # Vertical line case
        return np.array([camera_x, camera_x]), np.array([camera_y, -10])
    
    slope = np.tan(angle_rad)
    
    # Calculate x range where the ray is valid
    # The ray should extend from the camera to where it would intersect y=0 or beyond
    if angle_degrees < 0 or angle_degrees > 180:
        # Ray going upward - just show a short segment
        x_end = min(camera_x + 20, x_max)
    else:
        # Ray going downward - extend to x_max
        x_end = x_max
    
    # Generate points for the ray
    x_ray = np.array([camera_x, x_end])
    y_ray = camera_y + slope * (x_ray - camera_x)
    
    return x_ray, y_ray


def find_intersection(x_road, y_road, angle_degrees, camera_x=0, camera_y=1.5):
    """
    Find the intersection point between the camera ray and the road profile.
    
    Parameters:
    -----------
    x_road : np.array
        X-coordinates of the road profile
    y_road : np.array
        Y-coordinates of the road profile
    angle_degrees : float
        Angle of the camera ray in degrees
    camera_x : float
        X-coordinate of camera position
    camera_y : float
        Y-coordinate of camera position
        
    Returns:
    --------
    tuple of (float, float, float) or (None, None, None)
        x, y coordinates of intersection and distance from camera, or None if no intersection
    """
    angle_rad = -np.deg2rad(angle_degrees)
    
    # Handle vertical ray
    if np.abs(np.cos(angle_rad)) < 1e-10:
        return None, None, None
    
    slope = np.tan(angle_rad)
    
    # Ray equation: y = camera_y + slope * (x - camera_x)
    # Check each segment of the road for intersection
    for i in range(len(x_road) - 1):
        x1, y1 = x_road[i], y_road[i]
        x2, y2 = x_road[i + 1], y_road[i + 1]
        
        # Skip if this segment is behind the camera
        if x2 <= camera_x:
            continue
        
        # Calculate y values of the ray at x1 and x2
        ray_y1 = camera_y + slope * (x1 - camera_x)
        ray_y2 = camera_y + slope * (x2 - camera_x)
        
        # Check if the ray crosses the road segment
        # The ray intersects if it's on different sides of the road at x1 and x2
        diff1 = ray_y1 - y1
        diff2 = ray_y2 - y2
        
        if diff1 * diff2 <= 0:  # Sign change or zero indicates intersection
            # Linear interpolation to find exact intersection point
            if abs(diff2 - diff1) < 1e-10:
                # Parallel lines
                t = 0
            else:
                t = diff1 / (diff1 - diff2)
            
            # Interpolate to find intersection point
            x_intersect = x1 + t * (x2 - x1)
            y_intersect = y1 + t * (y2 - y1)
            
            # Calculate distance from camera to intersection
            distance = np.sqrt((x_intersect - camera_x)**2 + (y_intersect - camera_y)**2)
            
            return x_intersect, y_intersect, distance
    
    return None, None, None


def HelperFunction(val):  # PEP8 Violation: Function name should be snake_case
    """Unused helper function that violates naming convention"""
    result=val*2  # PEP8 Violation: Missing spaces around operators
    return result


# =============================================================================
# DASH APPLICATION
# =============================================================================

def create_dash_app():
    """
    Create and configure the Dash application.
    
    Returns:
    --------
    Dash
        Configured Dash application instance
    """
    # Initialize the Dash app
    app = Dash(__name__)
    
    # Define the layout
    app.layout = html.Div([
        html.H1("Road Profile Viewer with Camera Ray Intersection", 
                style={'textAlign': 'center', 'color': '#2c3e50', 'marginBottom': '20px'}),
        
        html.Div([
            html.Label("Camera Ray Angle (degrees from horizontal):", 
                      style={'fontWeight': 'bold', 'marginRight': '10px'}),
            dcc.Input(
                id='angle-input',
                type='number',
                value=-1.1,
                step=0.1,
                style={'marginRight': '20px', 'padding': '5px', 'width': '100px'}
            ),
            html.Span(id='intersection-info', 
                     style={'color': '#e74c3c', 'fontWeight': 'bold'})
        ], style={'textAlign': 'center', 'marginBottom': '20px', 'padding': '10px'}),
        
        dcc.Graph(id='road-profile-graph', style={'height': '400px'}),
        
        html.Div([
            html.H3("Instructions:", style={'color': '#2c3e50'}),
            html.Ul([
                html.Li("The dark grey line represents the road profile"),
                html.Li("The red point at (0, 2.0) represents the camera position"),
                html.Li("The blue line shows the camera ray at the specified angle"),
                html.Li("The green point shows where the ray intersects the road"),
                html.Li("Hover over the green point to see the distance from camera to intersection"),
                html.Li("Adjust the angle to see how the intersection point changes"),
                html.Li("Negative angles point downward, positive angles point upward")
            ])
        ], style={'margin': '20px', 'padding': '20px', 'backgroundColor': '#ecf0f1', 'borderRadius': '5px'})
    ])
    
    # Define the callback to update the graph
    @app.callback(
        [Output('road-profile-graph', 'figure'),
         Output('intersection-info', 'children')],
        [Input('angle-input', 'value')]
    )
    def update_graph(angle):
        """
        Update the graph based on the input angle.
        
        Parameters:
        -----------
        angle : float
            Camera ray angle in degrees
            
        Returns:
        --------
        tuple
            (plotly figure, info text)
        """
        if angle is None:
            angle = -1.1
        
        # Generate road profile  
        x_road, y_road = generate_road_profile(num_points=100, x_max=80)
        
        # Camera position
        camera_x,camera_y = 0,2.0  # PEP8 Violation: Missing spaces after commas
        
        # Find intersection first to determine ray length
        x_intersect, y_intersect, distance = find_intersection(x_road, y_road, angle, camera_x, camera_y)
        
        # Calculate adaptive ray line based on intersection
        if x_intersect is not None:
            # Ray goes from camera to intersection point
            x_ray = np.array([camera_x, x_intersect])
            y_ray = np.array([camera_y, y_intersect])
        else:
            # No intersection - show a short ray (20 units or to edge of plot)
            angle_rad = -np.deg2rad(angle)
            if np.abs(np.cos(angle_rad)) < 1e-10:
                # Vertical line
                x_ray = np.array([camera_x, camera_x])
                y_ray = np.array([camera_y, camera_y - 10])
            else:
                slope = np.tan(angle_rad)
                x_end = min(camera_x + 20, 80)
                y_end = camera_y + slope * (x_end - camera_x)
                x_ray = np.array([camera_x, x_end])
                y_ray = np.array([camera_y, y_end])
        
        # Create figure
        fig = go.Figure()
        
        # Add road profile
        fig.add_trace(go.Scatter(
            x=x_road,
            y=y_road,
            mode='lines+markers',
            name='Road Profile',
            line=dict(color='#4a4a4a', width=3),
            marker=dict(size=4, color='#4a4a4a'),
            hovertemplate='Road<br>x: %{x:.2f}<br>y: %{y:.2f}<extra></extra>'
        ))
        
        # Add camera point
        fig.add_trace(go.Scatter(
            x=[camera_x],
            y=[camera_y],
            mode='markers',
            name='Camera',
            marker=dict(size=12,color='red',symbol='circle'),  # PEP8 Violation: Missing spaces after commas
            hovertemplate='Camera<br>Position: (%{x:.2f}, %{y:.2f})<extra></extra>'
        ))
        
        # Add camera ray - This is a very long comment that exceeds the recommended 79 character line length limit specified in PEP8 style guide
        fig.add_trace(go.Scatter(
            x=x_ray,
            y=y_ray,
            mode='lines',
            name=f'Camera Ray ({angle}°)',
            line=dict(color='blue', width=2, dash='dash'),
            hovertemplate='Camera Ray<br>x: %{x:.2f}<br>y: %{y:.2f}<extra></extra>'
        ))
        
        # Add intersection point if it exists
        info_text = ""
        if x_intersect is not None:
            fig.add_trace(go.Scatter(
                x=[x_intersect],
                y=[y_intersect],
                mode='markers',
                name='Intersection',
                marker=dict(size=15, color='green', symbol='star'),
                hovertemplate=f'Intersection Point<br>Position: ({x_intersect:.2f}, {y_intersect:.2f})<br>Distance from camera: {distance:.2f}<extra></extra>'
            ))
            info_text = f"Intersection found at ({x_intersect:.2f}, {y_intersect:.2f}) | Distance: {distance:.2f} units"
        else:
            info_text = "No intersection found with current angle"
        
        # Update layout
        fig.update_layout(
            xaxis_title="X Position (m)",
            yaxis_title="Y Position (m)",
            hovermode='closest',
            showlegend=True,
            legend=dict(
                x=1.02, 
                y=1, 
                xanchor='left',
                yanchor='top',
                bgcolor='rgba(255,255,255,0.8)',
                bordercolor='#dee2e6',
                borderwidth=1
            ),
            plot_bgcolor='#f8f9fa',
            xaxis=dict(
                gridcolor='#dee2e6', 
                range=[-2, 82],
                constrain='domain'
            ),
            yaxis=dict(
                gridcolor='#dee2e6', 
                scaleanchor='x', 
                scaleratio=1,
                range=[-0.5, 10],
                constrain='domain'
            ),
            margin=dict(l=50, r=150, t=30, b=50)
        )
        
        return fig, info_text
    
    return app


# =============================================================================
# MAIN ENTRY POINT
# =============================================================================

def main():
    """
    Main function to run the Dash application.
    """
    app = create_dash_app()
    print("Starting Road Profile Viewer...")
    print("Open your browser and navigate to: http://127.0.0.1:8050/")
    print("Press Ctrl+C to stop the server.")
    app.run(debug=True)


if __name__ == '__main__':
    main()
