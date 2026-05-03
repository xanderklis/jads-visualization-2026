from dash import Dash, html, dcc, Input, Output
import pandas as pd
import plotly.express as px

# =========================
# LOAD DATA
# =========================
tracks = pd.read_csv(
    "data/tracks.csv",
    header=[0, 1],
    index_col=0
)

# flatten columns
tracks.columns = ['_'.join(col) for col in tracks.columns.values]

# =========================
# APP INIT
# =========================
app = Dash(__name__)

# dropdown values
genres = tracks['track_genre_top'].dropna().unique()
artists = tracks['artist_name'].dropna().unique()

# =========================
# LAYOUT (a)
# =========================
app.layout = html.Div([

    # LEFT PANEL
    html.Div([

        html.H3("Filters"),

        dcc.Dropdown(
            id="genre-dropdown",
            options=[{"label": g, "value": g} for g in genres],
            multi=True,
            placeholder="Select genre(s)"
        ),

        dcc.Dropdown(
            id="artist-dropdown",
            options=[{"label": a, "value": a} for a in artists[:1000]],
            multi=True,
            placeholder="Select artist(s)"
        ),

    ], style={"width": "20%", "display": "inline-block", "verticalAlign": "top"}),

    # CENTER PANEL
    html.Div([

        html.H3("Visualizations"),

        dcc.Graph(id="genre-bar"),
        dcc.Graph(id="artist-bar"),
        dcc.Graph(id="trend-line"),
        dcc.Graph(id="missing-bar")

    ], style={"width": "60%", "display": "inline-block"}),

    # RIGHT PANEL
    html.Div([

        html.H3("Details"),
        html.Div(id="details")

    ], style={"width": "20%", "display": "inline-block", "verticalAlign": "top"})
])


# =========================
# (b)(c)(d) VISUALS
# =========================
@app.callback(
    Output("genre-bar", "figure"),
    Output("artist-bar", "figure"),
    Output("trend-line", "figure"),
    Output("missing-bar", "figure"),
    Input("genre-dropdown", "value"),
    Input("artist-dropdown", "value")
)
def update_graphs(selected_genres, selected_artists):

    df = tracks.copy()

    # filters
    if selected_genres:
        df = df[df["track_genre_top"].isin(selected_genres)]

    if selected_artists:
        df = df[df["artist_name"].isin(selected_artists)]

    # =========================
    # BAR 1: GENRES
    # =========================
    genre_counts = df["track_genre_top"].value_counts().reset_index()
    genre_counts.columns = ["genre", "count"]

    genre_fig = px.bar(
        genre_counts,
        x="genre",
        y="count",
        title="Genre Distribution"
    )

    # =========================
    # BAR 2: ARTISTS
    # =========================
    artist_counts = df["artist_name"].value_counts().head(10).reset_index()
    artist_counts.columns = ["artist", "count"]

    artist_fig = px.bar(
        artist_counts,
        x="artist",
        y="count",
        title="Top Artists"
    )

    # =========================
    # LINE: TIME TREND
    # =========================
    if "album_date_released" in df.columns:
        df["year"] = pd.to_datetime(df["album_date_released"], errors="coerce").dt.year
        trend = df["year"].value_counts().sort_index().reset_index()
        trend.columns = ["year", "count"]

        trend_fig = px.line(
            trend,
            x="year",
            y="count",
            title="Tracks Over Time"
        )
    else:
        trend_fig = px.line(title="No time data available")

    # =========================
    # MISSING VALUES
    # =========================
    missing = df.isna().sum().sort_values(ascending=False).head(10).reset_index()
    missing.columns = ["attribute", "missing_count"]

    missing_fig = px.bar(
        missing,
        x="attribute",
        y="missing_count",
        title="Missing Values per Attribute"
    )

    return genre_fig, artist_fig, trend_fig, missing_fig


# =========================
# RUN APP
# =========================
if __name__ == "__main__":
    app.run(debug=True)