from dash import Dash, html, dcc, Input, Output, ctx
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# =========================
# LOAD DATA  (original — unchanged)
# =========================
tracks = pd.read_csv(
    "data/tracks.csv",
    header=[0, 1],
    index_col=0
)
tracks.columns = ['_'.join(col) for col in tracks.columns.values]

# pre-compute year once
tracks["year"] = pd.to_datetime(tracks["album_date_released"], errors="coerce").dt.year
tracks["track_listens"]   = pd.to_numeric(tracks["track_listens"],   errors="coerce")
tracks["track_favorites"] = pd.to_numeric(tracks["track_favorites"], errors="coerce")

# =========================
# APP INIT  (original — unchanged)
# =========================
app = Dash(__name__)

genres  = tracks['track_genre_top'].dropna().unique()
artists = tracks['artist_name'].dropna().unique()

# =========================
# THEME
# =========================
C = {
    "bg":       "#0f0f0f",
    "panel":    "#161616",
    "card":     "#1c1c1c",
    "border":   "#272727",
    "accent":   "#f5a623",
    "accent2":  "#e05c2a",
    "teal":     "#4ecdc4",
    "text":     "#ede8df",
    "muted":    "#6b6560",
    "serif":    "Georgia, 'Times New Roman', serif",
    "mono":     "'Courier New', Courier, monospace",
}

PT = dict(                          # shared plotly layout kwargs
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family=C["mono"], color=C["text"], size=11),
    title_font=dict(family=C["serif"], size=15, color=C["text"]),
    title_x=0.03,
    margin=dict(l=44, r=16, t=46, b=40),
    colorway=[C["accent"], C["accent2"], C["teal"], "#c084fc", "#86efac", "#fbbf24"],
    xaxis=dict(gridcolor=C["border"], zerolinecolor=C["border"], tickfont_size=10),
    yaxis=dict(gridcolor=C["border"], zerolinecolor=C["border"], tickfont_size=10),
    hoverlabel=dict(bgcolor=C["card"], bordercolor=C["border"],
                    font_family=C["mono"], font_size=11),
    legend=dict(bgcolor="rgba(0,0,0,0)", bordercolor=C["border"],
                font=dict(family=C["mono"], size=10, color=C["muted"])),
)

# =========================
# LAYOUT HELPERS
# =========================
def label(txt):
    return html.P(txt, style={
        "fontFamily": C["mono"], "fontSize": "9px", "letterSpacing": "2.5px",
        "color": C["accent"], "textTransform": "uppercase", "margin": "0 0 8px 0",
    })

def card(*children, style=None):
    base = {"background": C["card"], "border": f"1px solid {C['border']}",
            "borderRadius": "3px", "padding": "8px"}
    if style:
        base.update(style)
    return html.Div(list(children), style=base)

def stat_block(value, caption, color):
    return html.Div([
        html.Div(value, style={"fontFamily": C["serif"], "fontSize": "26px",
                               "color": color, "lineHeight": "1"}),
        html.Div(caption, style={"fontFamily": C["mono"], "fontSize": "9px",
                                 "letterSpacing": "1.5px", "color": C["muted"],
                                 "textTransform": "uppercase", "marginTop": "3px"}),
    ], style={"textAlign": "center", "padding": "12px 8px"})

# =========================
# LAYOUT
# =========================
app.layout = html.Div(style={"background": C["bg"], "minHeight": "100vh",
                              "fontFamily": C["mono"], "color": C["text"]}, children=[

    # ── HEADER ────────────────────────────────────────────────────
    html.Div(style={
        "background": C["panel"], "borderBottom": f"1px solid {C['border']}",
        "padding": "18px 32px", "display": "flex",
        "alignItems": "center", "justifyContent": "space-between",
    }, children=[
        html.Div([
            html.Span("FMA", style={"fontFamily": C["serif"], "fontSize": "26px",
                                    "color": C["accent"], "letterSpacing": "3px"}),
            html.Span(" Explorer", style={"fontFamily": C["serif"], "fontSize": "26px",
                                          "color": C["text"]}),
            html.Div("Free Music Archive · 106k tracks · metadata analysis",
                     style={"fontSize": "10px", "color": C["muted"],
                            "letterSpacing": "1px", "marginTop": "2px"}),
        ]),
        html.Div(id="header-badge"),
    ]),

    # ── BODY ──────────────────────────────────────────────────────
    html.Div(style={"display": "flex", "height": "calc(100vh - 65px)"}, children=[

        # LEFT PANEL
        html.Div(style={
            "width": "210px", "flexShrink": "0", "overflowY": "auto",
            "background": C["panel"], "borderRight": f"1px solid {C['border']}",
            "padding": "20px 16px",
        }, children=[

            label("Filters"),

            html.Div("Genre", style={"fontSize": "10px", "color": C["muted"],
                                     "marginBottom": "4px"}),
            dcc.Dropdown(
                id="genre-dropdown",
                options=[{"label": g, "value": g} for g in sorted(genres)],
                multi=True, placeholder="All genres",
                style={"fontSize": "11px", "marginBottom": "14px"},
            ),

            html.Div("Artist", style={"fontSize": "10px", "color": C["muted"],
                                      "marginBottom": "4px"}),
            dcc.Dropdown(
                id="artist-dropdown",
                options=[{"label": a, "value": a} for a in sorted(artists)[:1000]],
                multi=True, placeholder="All artists",
                style={"fontSize": "11px", "marginBottom": "14px"},
            ),

            html.Button("✕  Clear filters", id="clear-btn", n_clicks=0, style={
                "width": "100%", "background": "transparent",
                "border": f"1px solid {C['border']}", "color": C["muted"],
                "fontFamily": C["mono"], "fontSize": "10px", "padding": "7px",
                "cursor": "pointer", "marginBottom": "20px",
                "letterSpacing": "0.5px",
            }),

            html.Hr(style={"borderColor": C["border"], "margin": "4px 0 16px"}),
            label("Dataset"),
            html.Div(id="stats-panel"),
        ]),

        # CENTER PANEL
        html.Div(style={
            "flex": "1", "overflowY": "auto",
            "padding": "20px", "background": C["bg"],
        }, children=[

            # Row 1 — genre + artist
            html.Div(style={"display": "grid", "gridTemplateColumns": "1fr 1fr",
                            "gap": "14px", "marginBottom": "14px"}, children=[
                card(dcc.Graph(id="genre-bar",  config={"displayModeBar": False},
                               style={"height": "300px"})),
                card(dcc.Graph(id="artist-bar", config={"displayModeBar": False},
                               style={"height": "300px"})),
            ]),

            # Row 2 — trend + missing
            html.Div(style={"display": "grid", "gridTemplateColumns": "1fr 1fr",
                            "gap": "14px", "marginBottom": "14px"}, children=[
                card(dcc.Graph(id="trend-line",  config={"displayModeBar": False},
                               style={"height": "280px"})),
                card(dcc.Graph(id="missing-bar", config={"displayModeBar": False},
                               style={"height": "280px"})),
            ]),

            # Row 3 — scatter full width
            card(dcc.Graph(id="scatter-fig", config={"displayModeBar": False},
                           style={"height": "320px"}),
                 style={"marginBottom": "14px"}),

            # Row 4 — heatmap full width
            card(dcc.Graph(id="heatmap-fig", config={"displayModeBar": False},
                           style={"height": "340px"})),
        ]),

        # RIGHT PANEL
        html.Div(style={
            "width": "240px", "flexShrink": "0", "overflowY": "auto",
            "background": C["panel"], "borderLeft": f"1px solid {C['border']}",
            "padding": "20px 14px",
        }, children=[
            label("Track Details"),
            html.Div(id="details-panel",
                     style={"fontSize": "11px", "color": C["muted"]}),
        ]),
    ]),
])


# =========================
# CALLBACKS
# =========================

# Clear filters
@app.callback(
    Output("genre-dropdown",  "value"),
    Output("artist-dropdown", "value"),
    Input("clear-btn", "n_clicks"),
    prevent_initial_call=True,
)
def clear_filters(_):
    return None, None


# Main update
@app.callback(
    Output("genre-bar",    "figure"),
    Output("artist-bar",   "figure"),
    Output("trend-line",   "figure"),
    Output("missing-bar",  "figure"),
    Output("scatter-fig",  "figure"),
    Output("heatmap-fig",  "figure"),
    Output("stats-panel",  "children"),
    Output("header-badge", "children"),
    Input("genre-dropdown",  "value"),
    Input("artist-dropdown", "value"),
    Input("genre-bar",       "clickData"),
)
def update_graphs(sel_genres, sel_artists, genre_click):

    # cross-filter via bar click (only when no dropdown active)
    clicked_genre = None
    if genre_click and not sel_genres:
        clicked_genre = genre_click["points"][0]["x"]

    df = tracks.copy()
    if sel_genres:
        df = df[df["track_genre_top"].isin(sel_genres)]
    if sel_artists:
        df = df[df["artist_name"].isin(sel_artists)]
    if clicked_genre:
        df = df[df["track_genre_top"] == clicked_genre]

    # ── 1. Genre bar ──────────────────────────────────────────────
    gc = df["track_genre_top"].value_counts().reset_index()
    gc.columns = ["genre", "count"]

    if clicked_genre:
        colors = [C["accent"] if g == clicked_genre else "#2a2a2a" for g in gc["genre"]]
        genre_fig = go.Figure(go.Bar(
            x=gc["genre"], y=gc["count"], marker_color=colors,
            hovertemplate="%{x}: <b>%{y}</b> tracks<extra></extra>",
        ))
    else:
        genre_fig = go.Figure(go.Bar(
            x=gc["genre"], y=gc["count"],
            marker=dict(color=gc["count"],
                        colorscale=[[0, "#222"], [1, C["accent"]]]),
            hovertemplate="%{x}: <b>%{y}</b> tracks<extra></extra>",
        ))
    genre_fig.update_layout(title="Genre Distribution", **PT)

    # ── 2. Artist bar (horizontal) ────────────────────────────────
    ac = df["artist_name"].value_counts().head(12).reset_index()
    ac.columns = ["artist", "count"]
    artist_fig = go.Figure(go.Bar(
        x=ac["count"], y=ac["artist"], orientation="h",
        marker=dict(color=ac["count"],
                    colorscale=[[0, "#222"], [1, C["accent2"]]]),
        hovertemplate="%{y}: <b>%{x}</b> tracks<extra></extra>",
    ))
    artist_fig.update_layout(title="Top Artists by Track Count", **PT)
    artist_fig.update_yaxes(categoryorder="total ascending")

    # ── 3. Time trend ─────────────────────────────────────────────
    trend = (df["year"].dropna()
               .astype(int)
               .value_counts()
               .sort_index()
               .reset_index())
    trend.columns = ["year", "count"]
    trend = trend[trend["year"].between(1960, 2025)]

    trend_fig = go.Figure()
    trend_fig.add_trace(go.Scatter(
        x=trend["year"], y=trend["count"],
        mode="lines+markers",
        line=dict(color=C["accent"], width=2),
        marker=dict(color=C["accent"], size=4),
        fill="tozeroy", fillcolor="rgba(245,166,35,0.07)",
        hovertemplate="Year %{x}: <b>%{y}</b> tracks<extra></extra>",
    ))
    trend_fig.update_layout(title="Tracks Released Over Time", **PT)

    # ── 4. Missing values ─────────────────────────────────────────
    missing = (df.isna().sum()
                 .sort_values(ascending=False)
                 .head(10)
                 .reset_index())
    missing.columns = ["attribute", "missing_count"]
    missing["pct"] = (missing["missing_count"] / max(len(df), 1) * 100).round(1)
    missing["short"] = missing["attribute"].str.replace("track_", "").str.replace("album_", "").str.replace("artist_", "")

    missing_fig = go.Figure(go.Bar(
        x=missing["missing_count"], y=missing["short"], orientation="h",
        marker=dict(color=missing["pct"],
                    colorscale=[[0, "#222"], [1, C["accent2"]]]),
        customdata=missing["pct"],
        hovertemplate="%{y}: <b>%{x}</b> missing (<b>%{customdata}%</b>)<extra></extra>",
    ))
    missing_fig.update_layout(title="Missing Values per Attribute", **PT)
    missing_fig.update_yaxes(categoryorder="total ascending")

    # ── 5. Scatter: listens vs favourites ─────────────────────────
    scatter_fig = go.Figure()
    if "track_listens" in df.columns and "track_favorites" in df.columns:
        title_col = "track_title" if "track_title" in df.columns else None
        cols = ["track_listens", "track_favorites", "track_genre_top"]
        if title_col:
            cols.append(title_col)
        sdf = df[cols].dropna()
        sample = sdf.sample(min(3000, len(sdf)), random_state=42)

        palette = [C["accent"], C["accent2"], C["teal"],
                   "#c084fc", "#86efac", "#fbbf24", "#f87171", "#60a5fa"]
        for i, genre in enumerate(sample["track_genre_top"].dropna().unique()[:8]):
            sub = sample[sample["track_genre_top"] == genre]
            hover = sub[title_col] if title_col else sub.index.astype(str)
            scatter_fig.add_trace(go.Scatter(
                x=sub["track_listens"], y=sub["track_favorites"],
                mode="markers", name=genre,
                marker=dict(size=4, opacity=0.55, color=palette[i % len(palette)]),
                text=hover,
                hovertemplate="<b>%{text}</b><br>Listens: %{x:,}<br>Favs: %{y:,}<extra></extra>",
            ))
        scatter_fig.update_xaxes(type="log", title="Listens (log)")
        scatter_fig.update_yaxes(type="log", title="Favourites (log)")
    scatter_fig.update_layout(title="Popularity: Listens vs Favourites", **PT)

    # ── 6. Genre × Decade heatmap ─────────────────────────────────
    heatmap_fig = go.Figure()
    h = df.dropna(subset=["track_genre_top", "year"]).copy()
    h["decade"] = (h["year"].astype(int) // 10 * 10).astype(str) + "s"
    pivot = h.groupby(["track_genre_top", "decade"]).size().unstack(fill_value=0)
    top_g = pivot.sum(axis=1).nlargest(12).index
    pivot = pivot.loc[top_g]
    heatmap_fig.add_trace(go.Heatmap(
        z=pivot.values,
        x=pivot.columns.tolist(),
        y=pivot.index.tolist(),
        colorscale=[[0, C["card"]], [0.25, "#3a2505"], [1, C["accent"]]],
        hovertemplate="Genre: <b>%{y}</b><br>Decade: %{x}<br>Tracks: <b>%{z}</b><extra></extra>",
    ))
    heatmap_fig.update_layout(title="Genre Activity by Decade", **PT)

    # ── Stats sidebar ─────────────────────────────────────────────
    stats = html.Div([
        stat_block(f"{len(df):,}",                    "tracks",  C["accent"]),
        stat_block(str(df["track_genre_top"].nunique()), "genres",  C["accent2"]),
        stat_block(f"{df['artist_name'].nunique():,}", "artists", C["teal"]),
    ], style={"display": "grid", "gridTemplateColumns": "1fr 1fr",
              "gap": "6px", "marginTop": "4px"})

    # ── Header badge ──────────────────────────────────────────────
    badge = None
    if sel_genres or sel_artists or clicked_genre:
        parts = []
        if clicked_genre:  parts.append(f"genre: {clicked_genre}")
        if sel_genres:     parts.append(f"{len(sel_genres)} genre(s)")
        if sel_artists:    parts.append(f"{len(sel_artists)} artist(s)")
        badge = html.Span(" · ".join(parts), style={
            "fontFamily": C["mono"], "fontSize": "10px",
            "color": C["accent"], "border": f"1px solid {C['accent']}",
            "padding": "3px 12px", "borderRadius": "20px",
        })

    return (genre_fig, artist_fig, trend_fig, missing_fig,
            scatter_fig, heatmap_fig, stats, badge)


# Details panel
@app.callback(
    Output("details-panel", "children"),
    Input("genre-bar",      "clickData"),
    Input("artist-bar",     "clickData"),
    Input("scatter-fig",    "clickData"),
    Input("genre-dropdown", "value"),
    Input("artist-dropdown","value"),
)
def update_details(genre_click, artist_click, scatter_click,
                   sel_genres, sel_artists):

    df = tracks.copy()
    if sel_genres:
        df = df[df["track_genre_top"].isin(sel_genres)]
    if sel_artists:
        df = df[df["artist_name"].isin(sel_artists)]

    clicked_genre = clicked_artist = clicked_track = None
    if genre_click:   clicked_genre  = genre_click["points"][0]["x"]
    if artist_click:  clicked_artist = artist_click["points"][0]["y"]
    if scatter_click: clicked_track  = scatter_click["points"][0].get("text")

    sub = df.copy()
    if clicked_genre:                              sub = sub[sub["track_genre_top"] == clicked_genre]
    if clicked_artist:                             sub = sub[sub["artist_name"]     == clicked_artist]
    if clicked_track and "track_title" in sub.columns:
        sub = sub[sub["track_title"] == clicked_track]

    if sub.empty:
        return html.P("Click any chart to inspect tracks.",
                      style={"color": C["muted"], "lineHeight": "1.8"})

    keep = [c for c in ["track_title","artist_name","track_genre_top","year","track_listens"]
            if c in sub.columns]
    disp = sub[keep].dropna(subset=[keep[0]]).head(30)
    if "track_listens" in disp.columns:
        disp = disp.sort_values("track_listens", ascending=False)

    rows = []
    for _, row in disp.iterrows():
        title   = str(row.get("track_title",      "—"))
        artist  = str(row.get("artist_name",      "—"))
        genre   = str(row.get("track_genre_top",  "—"))
        year    = str(int(row["year"])) if "year" in row and pd.notna(row.get("year")) else "—"
        listens = (f'{int(row["track_listens"]):,}'
                   if "track_listens" in row and pd.notna(row.get("track_listens")) else None)

        rows.append(html.Div([
            html.Div(title, style={
                "color": C["text"], "fontWeight": "500", "fontSize": "11px",
                "whiteSpace": "nowrap", "overflow": "hidden",
                "textOverflow": "ellipsis", "maxWidth": "210px",
            }),
            html.Div(artist, style={"color": C["muted"], "fontSize": "10px",
                                    "marginBottom": "3px"}),
            html.Div([
                html.Span(genre, style={
                    "color": C["accent"], "fontSize": "9px",
                    "border": f"1px solid {C['accent']}",
                    "padding": "1px 5px", "borderRadius": "3px", "marginRight": "5px",
                }),
                html.Span(year, style={"color": C["muted"], "fontSize": "9px",
                                       "marginRight": "5px"}),
                (html.Span(f"♫ {listens}", style={"color": C["muted"], "fontSize": "9px"})
                 if listens else html.Span()),
            ]),
        ], style={"padding": "9px 0", "borderBottom": f"1px solid {C['border']}"}))

    header = html.Div([
        html.Span(f"{len(sub):,}", style={"color": C["accent"], "fontFamily": C["serif"],
                                           "fontSize": "20px"}),
        html.Span(" tracks", style={"color": C["muted"], "fontSize": "10px"}),
    ], style={"marginBottom": "12px"})

    return [header] + rows


# =========================
# RUN
# =========================
if __name__ == "__main__":
    app.run(debug=True)