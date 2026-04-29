from dash import Dash, html, dcc
import plotly.express as px
import pandas as pd

print("Hello World")

app = Dash(__name__)

app.layout = html.Div([

    # LEFT PANEL
    html.Div([
        html.H3("Input Panel"),

        dcc.Dropdown(
            id="genre-dropdown",
            options=[],
            placeholder="Select genre"
        ),

        dcc.Dropdown(
            id="artist-dropdown",
            options=[],
            placeholder="Select artist",
            multi=True
        )

    ], style={"width": "20%", "display": "inline-block", "verticalAlign": "top"}),

    # CENTER PANEL
    html.Div([
        html.H3("Main View"),

        html.Div("Genre distribution chart here"),
        html.Div("Top artists chart here"),
        html.Div("Trends over time chart here"),
        html.Div("Missing values chart here")

    ], style={"width": "60%", "display": "inline-block", "verticalAlign": "top"}),

    # RIGHT PANEL
    html.Div([
        html.H3("Details"),

        html.Div("Artist info will appear here")

    ], style={"width": "20%", "display": "inline-block", "verticalAlign": "top"})
])

if __name__ == "__main__":
    app.run(debug=True)