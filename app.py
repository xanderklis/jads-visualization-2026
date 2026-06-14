from dash import Dash, html, dcc, Input, Output, State, ctx
import pandas as pd
import plotly.graph_objects as go
from src.theme import C, PT
from src.components import card, stat_block, tag, section_label, field_label, fmt_revenue
from src.logic import apply_filters


# Load the data
tracks     = pd.read_csv("data/clean/tracks_clean.csv")
artists_df = pd.read_csv("data/clean/artists_clean.csv")
trends     = pd.read_csv("data/clean/trends.csv")

# Initialize the app
app = Dash(__name__, suppress_callback_exceptions=True)

genres = sorted(tracks["track_genre_top"].dropna().unique()) # This needs to go, we can turn this into a .JSON to decrease processing

# Shared state stores
# brushed_genre:    genre clicked in genre-trend (string or None)
# brushed_artists:  artists clicked in talent-scatter (list or None)
# highlighted_artist: artist clicked in one-hit-scatter (string or None)
stores = [
    dcc.Store(id="brushed-genre",      data=None),
    dcc.Store(id="brushed-artists",    data=None),
    dcc.Store(id="highlighted-artist", data=None),
]

# App layout
app.layout = html.Div(style={"background": C["bg"], "minHeight": "100vh",
                              "fontFamily": C["mono"], "color": C["text"]}, children=[

    *stores,

    # HEADER
    html.Div(style={
        "background": C["panel"], "borderBottom": f"1px solid {C['border']}",
        "padding": "16px 32px", "display": "flex",
        "alignItems": "center", "justifyContent": "space-between",
    }, children=[
        html.Div([
            html.Span("FMA", style={"fontFamily": C["serif"], "fontSize": "24px",
                                    "color": C["accent"], "letterSpacing": "3px"}),
            html.Span(" Talent Scout", style={"fontFamily": C["serif"], "fontSize": "24px",
                                              "color": C["text"]}),
            html.Div("Free Music Archive · Artist discovery dashboard for music labels",
                     style={"fontSize": "10px", "color": C["muted"],
                            "letterSpacing": "1px", "marginTop": "2px"}),
        ]),
        html.Div(id="header-badge"),
    ]),

    # BODY
    html.Div(style={"display": "flex", "height": "calc(100vh - 61px)"}, children=[

        # LEFT PANEL
        html.Div(style={
            "width": "210px", "flexShrink": "0", "overflowY": "auto",
            "background": C["panel"], "borderRight": f"1px solid {C['border']}",
            "padding": "20px 16px",
        }, children=[

            section_label("Filters"),

            field_label("Genre"),
            dcc.Dropdown(
                id="genre-dropdown",
                options=[{"label": g, "value": g} for g in genres],
                multi=True, placeholder="All genres",
                style={"fontSize": "11px", "marginBottom": "14px"},
            ),

            field_label("Show only"),
            dcc.Checklist(
                id="filter-checklist",
                options=[
                    {"label": "  New talent",       "value": "talent"},
                    {"label": "  One-hit wonders",  "value": "one_hit"},
                    {"label": "  No label only",    "value": "no_label"},
                    {"label": "  Early career only","value": "early"},
                ],
                value=[],
                style={"fontSize": "11px", "marginBottom": "14px"},
                labelStyle={"color": "#ede8df", "display": "block",
                            "lineHeight": "2.2", "cursor": "pointer"},
                inputStyle={"marginRight": "7px", "accentColor": "#f5a623"},
            ),

            field_label("Max track count"),
            dcc.Slider(
                id="track-count-slider",
                min=1, max=50, step=1, value=50,
                marks={1: "1", 10: "10", 25: "25", 50: "50+"},
                tooltip={"placement": "bottom", "always_visible": True},
            ),

            html.Div(style={"marginTop": "20px"}),
            html.Button("✕  Clear filters", id="clear-btn", n_clicks=0, style={
                "width": "100%", "background": "transparent",
                "border": f"1px solid {C['border']}", "color": C["muted"],
                "fontFamily": C["mono"], "fontSize": "10px", "padding": "7px",
                "cursor": "pointer", "letterSpacing": "0.5px",
            }),

            html.Hr(style={"borderColor": C["border"], "margin": "20px 0 14px"}),
            section_label("Overview"),
            html.Div(id="stats-panel"),
        ]),

        # CENTER PANEL
        html.Div(style={
            "flex": "1", "overflowY": "auto",
            "padding": "20px", "background": C["bg"],
        }, children=[

            # Row 1 — talent discovery scatter (full width)
            card(dcc.Graph(id="talent-scatter",
                           config={"displayModeBar": False},
                           style={"height": "360px"}),
                 style={"marginBottom": "14px"}),

            # Row 2 — genre trend + one-hit wonder
            html.Div(style={"display": "grid", "gridTemplateColumns": "1fr 1fr",
                            "gap": "14px", "marginBottom": "14px"}, children=[
                card(dcc.Graph(id="genre-trend",
                               config={"displayModeBar": False},
                               style={"height": "300px"})),
                card(dcc.Graph(id="one-hit-scatter",
                               config={"displayModeBar": False},
                               style={"height": "300px"})),
            ]),

            # Row 3 — emerging genres + missing signal
            html.Div(style={"display": "grid", "gridTemplateColumns": "1fr 1fr",
                            "gap": "14px", "marginBottom": "14px"}, children=[
                card(dcc.Graph(id="emerging-genres",
                               config={"displayModeBar": False},
                               style={"height": "280px"})),
                card(dcc.Graph(id="missing-signal",
                               config={"displayModeBar": False},
                               style={"height": "280px"})),
            ]),

            # Row 4 — revenue charts (two side by side)
            html.Div(style={"display": "grid", "gridTemplateColumns": "1fr 1fr",
                            "gap": "14px"}, children=[
                card(dcc.Graph(id="revenue-artist",
                               config={"displayModeBar": False},
                               style={"height": "300px"})),
                card(dcc.Graph(id="revenue-genre",
                               config={"displayModeBar": False},
                               style={"height": "300px"})),
            ]),
        ]),

        # RIGHT PANEL — artist profile
        html.Div(style={
            "width": "250px", "flexShrink": "0", "overflowY": "auto",
            "background": C["panel"], "borderLeft": f"1px solid {C['border']}",
            "padding": "20px 14px",
        }, children=[
            section_label("Artist Profile"),
            html.Div(id="artist-panel",
                     style={"fontSize": "11px", "color": C["muted"]}),
        ]),
    ]),
])


# Callbacks

# Single callback handling clear + all 3 linking interactions
@app.callback(
    Output("genre-dropdown",     "value"),
    Output("filter-checklist",   "value"),
    Output("track-count-slider", "value"),
    Output("brushed-genre",      "data"),
    Output("brushed-artists",    "data"),
    Output("highlighted-artist", "data"),
    Input("clear-btn",       "n_clicks"),
    Input("genre-trend",     "clickData"),
    Input("talent-scatter",  "clickData"),
    Input("one-hit-scatter", "clickData"),
    State("genre-dropdown",     "value"),
    State("filter-checklist",   "value"),
    State("track-count-slider", "value"),
    State("brushed-genre",      "data"),
    State("brushed-artists",    "data"),
    State("highlighted-artist", "data"),
    prevent_initial_call=True,
)
def handle_interactions(clear_clicks, genre_click, talent_click, ohw_click,
                        cur_dropdown, cur_checklist, cur_slider,
                        cur_genre, cur_artists, cur_highlighted):
    triggered = ctx.triggered_id

    # Clear everything
    if triggered == "clear-btn":
        return None, [], 50, None, None, None

    # Linking 1: click genre line in genre-trend → brush genre in talent + OHW
    if triggered == "genre-trend" and genre_click:
        point = genre_click["points"][0]
        genre_name = None
        if point.get("customdata"):
            genre_name = point["customdata"][0]
        if not genre_name:
            genre_name = point.get("fullData", {}).get("name")
        new_genre = None if genre_name == cur_genre else genre_name
        return cur_dropdown, cur_checklist, cur_slider, new_genre, cur_artists, cur_highlighted

    # Linking 2: click artist in talent-scatter → highlight in OHW scatter
    if triggered == "talent-scatter" and talent_click:
        name = talent_click["points"][0].get("text")
        new_artists = None if (cur_artists and len(cur_artists) == 1 and cur_artists[0] == name) else ([name] if name else None)
        return cur_dropdown, cur_checklist, cur_slider, cur_genre, new_artists, cur_highlighted

    # Linking 3: click artist in one-hit-scatter → highlight in talent scatter
    if triggered == "one-hit-scatter" and ohw_click:
        name = ohw_click["points"][0].get("text")
        new_highlighted = None if name == cur_highlighted else name
        return cur_dropdown, cur_checklist, cur_slider, cur_genre, cur_artists, new_highlighted

    return cur_dropdown, cur_checklist, cur_slider, cur_genre, cur_artists, cur_highlighted


# Main charts
@app.callback(
    Output("talent-scatter",  "figure"),
    Output("genre-trend",     "figure"),
    Output("one-hit-scatter", "figure"),
    Output("emerging-genres", "figure"),
    Output("missing-signal",  "figure"),
    Output("revenue-artist",  "figure"),
    Output("revenue-genre",   "figure"),
    Output("stats-panel",     "children"),
    Output("header-badge",    "children"),
    Input("genre-dropdown",      "value"),
    Input("filter-checklist",    "value"),
    Input("track-count-slider",  "value"),
    Input("brushed-genre",       "data"),
    Input("brushed-artists",     "data"),
    Input("highlighted-artist",  "data"),
)
def update_charts(sel_genres, checks, max_tracks,
                  brushed_genre, brushed_artists, highlighted_artist):

    adf = apply_filters(artists_df, sel_genres, checks or [], max_tracks)

    palette = [C["accent"], C["accent2"], C["teal"], "#c084fc",
               "#86efac", "#fbbf24", "#f87171", "#60a5fa"]

    p80 = artists_df["avg_listens"].quantile(0.80)

    # Talent discovery scatter
    adf_plot = adf.dropna(subset=["avg_listens", "track_count"])

    def talent_color(row):
        name = row["artist_name"]
        if brushed_genre and brushed_genre not in str(row.get("genres", "")):
            return "rgba(100,100,100,0.12)"
        if brushed_artists and name not in brushed_artists:
            return "rgba(100,100,100,0.12)"
        if highlighted_artist and name == highlighted_artist:
            return C["teal"]
        if row["is_talent"]:  return C["green"]
        if row["is_one_hit"]: return C["accent"]
        return C["muted"]

    def talent_size(row):
        name = row["artist_name"]
        if highlighted_artist and name == highlighted_artist:
            return 14
        if brushed_artists and name in brushed_artists:
            return 10
        return 6

    colors = adf_plot.apply(talent_color, axis=1).tolist()
    sizes  = adf_plot.apply(talent_size,  axis=1).tolist()

    talent_fig = go.Figure()
    talent_fig.add_shape(type="rect",
        x0=0, x1=10, y0=p80, y1=adf_plot["avg_listens"].max() * 1.1,
        fillcolor="rgba(134,239,172,0.06)",
        line=dict(color="rgba(134,239,172,0.25)", width=1, dash="dot"),
    )
    talent_fig.add_annotation(
        x=5, y=adf_plot["avg_listens"].max() * 1.05,
        text="Discovery Zone", showarrow=False,
        font=dict(family=C["mono"], size=9, color=C["green"]),
    )
    talent_fig.add_trace(go.Scatter(
        x=adf_plot["track_count"],
        y=adf_plot["avg_listens"],
        mode="markers",
        marker=dict(color=colors, size=sizes, opacity=0.85,
                    line=dict(width=0.5, color=C["border"])),
        text=adf_plot["artist_name"],
        customdata=adf_plot[["track_count", "avg_listens", "career_start",
                              "genres", "avg_revenue"]].values,
        hovertemplate=(
            "<b>%{text}</b><br>"
            "Tracks: %{customdata[0]}<br>"
            "Avg listens: %{customdata[1]:,.0f}<br>"
            "Est. revenue: $%{customdata[4]:,.2f}<br>"
            "Career start: %{customdata[2]}<br>"
            "Genres: %{customdata[3]}<extra></extra>"
        ),
    ))
    for lbl, col in [("New talent", C["green"]),
                     ("One-hit wonder", C["accent"]),
                     ("Other", C["muted"])]:
        talent_fig.add_trace(go.Scatter(
            x=[None], y=[None], mode="markers",
            marker=dict(color=col, size=8),
            name=lbl, showlegend=True,
        ))

    suffix = []
    if brushed_genre:      suffix.append(f"genre: {brushed_genre}")
    if brushed_artists:    suffix.append(f"{len(brushed_artists)} selected")
    if highlighted_artist: suffix.append(f"↑ {highlighted_artist}")
    talent_title = "Talent Discovery · Track Count vs Avg Listens"
    if suffix: talent_title += "  ·  " + "  ·  ".join(suffix)

    talent_fig.update_layout(
        title=talent_title,
        xaxis_title="Number of tracks",
        yaxis_title="Avg listens per track (log scale)",
        yaxis_type="log",
        **PT,
    )

    # Genre trends over time
    if sel_genres:
        trend_filtered = trends[trends["track_genre_top"].isin(sel_genres)]
        top_genres = sel_genres
    else:
        top_genres = trends["track_genre_top"].value_counts().head(8).index.tolist() # This ain't work anymore?
        trend_filtered = trends

    genre_trend_fig = go.Figure()
    for i, g in enumerate(top_genres):
        # Count the total amount of track listens per year for each genre
        sub = (trend_filtered[trend_filtered["track_genre_top"] == g]
               .groupby("year")["track_listens"].sum()
               .reset_index(name="count"))

        if brushed_genre:
            if g == brushed_genre:
                lw, opacity = 3, 1.0
                color = palette[i % len(palette)]
            else:
                lw, opacity = 1, 0.2
                color = "rgba(150,150,150,0.3)"
        else:
            lw, opacity = 2, 1.0
            color = palette[i % len(palette)]

        genre_trend_fig.add_trace(go.Scatter(
            x=sub["year"], y=sub["count"],
            mode="lines", name=g,
            opacity=opacity,
            line=dict(color=color, width=lw),
            customdata=[[g]] * len(sub),
            hovertemplate=f"{g} · %{{x}}: <b>%{{y:,}}</b> total listens · click to filter<extra></extra>",
        ))
    genre_trend_fig.update_layout(
        title="Genre Trends Over Time",
        yaxis_title="Total listens",
        xaxis_title="Year",
        **PT,
    )

    # One-hit wonder scatter
    # Outlier detection via IQR: artist is OHW if ratio > Q3 + 1.5*IQR
    # Artists with only 1 track are excluded
    ohw_all = adf.dropna(subset=["avg_listens", "max_listens"]).copy()
    ohw_all = ohw_all[ohw_all["track_count"] > 1]
    if not ohw_all.empty:
        Q1  = ohw_all["ratio"].quantile(0.25)
        Q3  = ohw_all["ratio"].quantile(0.75)
        IQR = Q3 - Q1
        ohw_threshold = Q3 + 1.5 * IQR
        ohw_all["is_ohw_outlier"] = ohw_all["ratio"] > ohw_threshold
    else:
        ohw_all["is_ohw_outlier"] = False

    ohw = ohw_all

    def ohw_color(row):
        name = row["artist_name"]
        if highlighted_artist and name == highlighted_artist:
            return C["teal"]
        if brushed_genre and brushed_genre not in str(row.get("genres", "")):
            return "rgba(100,100,100,0.10)"
        if brushed_artists:
            if name in brushed_artists:
                return C["accent"]
            return "rgba(100,100,100,0.10)"
        return C["accent"] if row["is_ohw_outlier"] else C["muted"]

    def ohw_size(row):
        name = row["artist_name"]
        if highlighted_artist and name == highlighted_artist:
            return 14
        if brushed_artists and name in brushed_artists:
            return 9
        return 5

    ohw_colors = ohw.apply(ohw_color, axis=1).tolist()
    ohw_sizes  = ohw.apply(ohw_size,  axis=1).tolist()

    ohw_fig = go.Figure(go.Scatter(
        x=ohw["avg_listens"], y=ohw["max_listens"],
        mode="markers",
        marker=dict(color=ohw_colors, size=ohw_sizes, opacity=0.85),
        text=ohw["artist_name"],
        customdata=ohw["ratio"].round(1).values,
        hovertemplate=(
            "<b>%{text}</b><br>"
            "Avg listens: %{x:,.0f}<br>"
            "Max listens: %{y:,.0f}<br>"
            "Ratio: %{customdata}<br>"
            "Click to highlight in talent scatter<extra></extra>"
        ),
    ))
    max_val = ohw["max_listens"].quantile(0.99) if not ohw.empty else 1
    ohw_fig.add_trace(go.Scatter(
        x=[0, max_val], y=[0, max_val], mode="lines",
        line=dict(color=C["border"], width=1, dash="dot"),
        showlegend=False, hoverinfo="skip",
    ))
    if not ohw_all.empty:
        ohw_fig.add_hline(
            y=ohw_threshold,
            line=dict(color=C["accent"], width=1, dash="dot"),
            annotation_text=f"Outlier threshold (Q3+1.5×IQR = {ohw_threshold:,.0f})",
            annotation_font=dict(color=C["accent"], size=9, family=C["mono"]),
            annotation_position="top right",
        )
    ohw_fig.update_layout(
        title="One-Hit Wonder Detection · Avg vs Max Listens",
        xaxis_title="Avg listens",
        yaxis_title="Max listens (best track)",
        **PT,
    )

    # Emerging genres
    new_artists = artists_df[artists_df["early_career"]]["artist_name"] # What is early career...?
    new_tracks  = tracks[tracks["artist_name"].isin(new_artists)] # Who are these????
    if sel_genres:
        new_tracks = new_tracks[new_tracks["track_genre_top"].isin(sel_genres)] # Wtf is sel_genres????
    emerging = (new_tracks["track_genre_top"]
                .value_counts().head(12).reset_index())
    emerging.columns = ["genre", "count"]
    emerging_fig = go.Figure(go.Bar(
        x=emerging["count"], y=emerging["genre"], orientation="h",
        marker=dict(color=emerging["count"],
                    colorscale=[[0, "#1a1a1a"], [1, C["teal"]]]),
        hovertemplate="%{y}: <b>%{x}</b> tracks<extra></extra>",
    ))
    emerging_fig.update_layout(title="Emerging Genres (Early-Career Artists)", **PT)
    emerging_fig.update_yaxes(categoryorder="total ascending")

    # Missing data / hidden talent signal
    sig = adf.dropna(subset=["avg_listens", "missing_pct"])
    sig_colors = [
        C["green"] if (row["avg_listens"] >= p80 and row["missing_pct"] > 50)
        else C["muted"]
        for _, row in sig.iterrows()
    ]
    missing_fig = go.Figure(go.Scatter(
        x=sig["missing_pct"], y=sig["avg_listens"],
        mode="markers",
        marker=dict(color=sig_colors, size=5, opacity=0.65),
        text=sig["artist_name"],
        hovertemplate=(
            "<b>%{text}</b><br>"
            "Missing data: %{x:.1f}%<br>"
            "Avg listens: %{y:,.0f}<extra></extra>"
        ),
    ))
    missing_fig.add_annotation(
        x=75, y=sig["avg_listens"].quantile(0.95) if not sig.empty else 1,
        text="Hidden talent zone", showarrow=False,
        font=dict(family=C["mono"], size=9, color=C["green"]),
    )
    missing_fig.update_layout(
        title="Hidden Talent Signal · Missing Data vs Avg Listens",
        xaxis_title="Missing metadata (%)",
        yaxis_title="Avg listens",
        **PT,
    )

    # Revenue — top artists (unsigned highlighted)
    rev = (adf.dropna(subset=["total_revenue"])
              .sort_values("total_revenue", ascending=False)
              .head(15))
    rev_colors = [C["green"] if not v else C["muted"] for v in rev["has_label"]]

    revenue_artist_fig = go.Figure()
    revenue_artist_fig.add_trace(go.Bar(
        x=rev["total_revenue"], y=rev["artist_name"],
        orientation="h",
        marker_color=rev_colors,
        customdata=rev[["track_count", "has_label"]].values,
        hovertemplate=(
            "<b>%{y}</b><br>"
            "Est. revenue: %{x:$,.0f}<br>"
            "Tracks: %{customdata[0]}<br>"
            "Has label: %{customdata[1]}<extra></extra>"
        ),
        showlegend=False,
    ))
    for lbl, col in [("No label (unsigned)", C["green"]),
                     ("Has label", C["muted"])]:
        revenue_artist_fig.add_trace(go.Scatter(
            x=[None], y=[None], mode="markers",
            marker=dict(color=col, size=8, symbol="square"),
            name=lbl, showlegend=True,
        ))
    revenue_artist_fig.update_layout(
        title="Est. Revenue · Top Artists (@ $0.004/stream)",
        xaxis_title="Estimated revenue (USD)",
        **PT,
    )
    revenue_artist_fig.update_yaxes(categoryorder="total ascending")

    # Revenue — by genre
    genre_rev = (tracks
                 .dropna(subset=["track_genre_top", "estimated_revenue"])
                 .groupby("track_genre_top")["estimated_revenue"]
                 .sum()
                 .sort_values(ascending=False)
                 .head(12)
                 .reset_index())
    genre_rev.columns = ["genre", "total_revenue"]

    revenue_genre_fig = go.Figure(go.Bar(
        x=genre_rev["total_revenue"], y=genre_rev["genre"],
        orientation="h",
        marker=dict(color=genre_rev["total_revenue"],
                    colorscale=[[0, "#1a1a1a"], [1, C["accent"]]]),
        text=[fmt_revenue(v) for v in genre_rev["total_revenue"]],
        textposition="outside",
        textfont=dict(color=C["muted"], size=9),
        hovertemplate="%{y}: <b>%{text}</b> est. revenue<extra></extra>",
    ))
    revenue_genre_fig.update_layout(
        title="Est. Revenue by Genre (@ $0.004/stream)",
        xaxis_title="Estimated revenue (USD)",
        **PT,
    )
    revenue_genre_fig.update_yaxes(categoryorder="total ascending")

    # Stats
    total_rev = adf["total_revenue"].sum()
    n_talent  = int(adf["is_talent"].sum())
    n_one_hit = int(ohw_all["is_ohw_outlier"].sum()) if not ohw_all.empty else 0
    stats = html.Div([
        stat_block(f"{len(adf):,}",       "artists",    C["accent"]),
        stat_block(f"{n_talent}",          "new talent", C["green"]),
        stat_block(f"{n_one_hit}",         "one-hit",    C["accent2"]),
        stat_block(fmt_revenue(total_rev), "est. rev.",  C["teal"]),
    ], style={"display": "grid", "gridTemplateColumns": "1fr 1fr",
              "gap": "6px", "marginTop": "4px"})

    # Badge
    parts = []
    if sel_genres:         parts.append(f"{len(sel_genres)} genre(s)")
    if checks:             parts.append(" · ".join(checks))
    if max_tracks < 50:    parts.append(f"≤{max_tracks} tracks")
    if brushed_genre:      parts.append(f"genre: {brushed_genre}")
    if brushed_artists:    parts.append(f"{len(brushed_artists)} selected")
    if highlighted_artist: parts.append(f"↑ {highlighted_artist}")
    badge = None
    if parts:
        badge = html.Span(" · ".join(parts), style={
            "fontFamily": C["mono"], "fontSize": "10px",
            "color": C["accent"], "border": f"1px solid {C['accent']}",
            "padding": "3px 12px", "borderRadius": "20px",
        })

    return (talent_fig, genre_trend_fig, ohw_fig,
            emerging_fig, missing_fig,
            revenue_artist_fig, revenue_genre_fig,
            stats, badge)


# Artist profile panel
@app.callback(
    Output("artist-panel", "children"),
    Input("talent-scatter",   "clickData"),
    Input("one-hit-scatter",  "clickData"),
    Input("revenue-artist",   "clickData"),
)
def update_artist_panel(talent_click, ohw_click, rev_click):

    click = talent_click or ohw_click or rev_click
    if not click:
        return html.P("Click any artist on the charts to see their profile.",
                      style={"color": C["muted"], "lineHeight": "1.8"})

    artist_name = click["points"][0].get("text") or click["points"][0].get("y")
    if not artist_name:
        return html.P("No artist data available.", style={"color": C["muted"]})

    row = artists_df[artists_df["artist_name"] == artist_name]
    if row.empty:
        return html.P("Artist not found.", style={"color": C["muted"]})
    row = row.iloc[0]

    artist_tracks = tracks[tracks["artist_name"] == artist_name]
    location = (artist_tracks["artist_location"].dropna().iloc[0]
                if "artist_location" in artist_tracks.columns
                and not artist_tracks["artist_location"].dropna().empty else "—")
    website  = (artist_tracks["artist_website"].dropna().iloc[0]
                if "artist_website" in artist_tracks.columns
                and not artist_tracks["artist_website"].dropna().empty else None)

    flags = []
    if row["is_talent"]:     flags.append(("NEW TALENT",     C["green"]))
    if row["is_one_hit"]:    flags.append(("ONE-HIT WONDER", C["accent"]))
    if not row["has_label"]: flags.append(("NO LABEL",       C["teal"]))
    if row["early_career"]:  flags.append(("EARLY CAREER",   C["accent2"]))

    def metric_row(lbl, value):
        return html.Div([
            html.Span(lbl, style={"color": C["muted"], "fontSize": "9px",
                                  "letterSpacing": "1px", "textTransform": "uppercase"}),
            html.Span(str(value), style={"color": C["text"], "fontSize": "12px",
                                          "fontFamily": C["serif"], "float": "right"}),
        ], style={"padding": "7px 0", "borderBottom": f"1px solid {C['border']}",
                  "overflow": "hidden"})

    avg_l   = f'{row["avg_listens"]:,.0f}'  if pd.notna(row["avg_listens"])  else "—"
    max_l   = f'{row["max_listens"]:,.0f}'  if pd.notna(row["max_listens"])  else "—"
    ratio   = f'{row["ratio"]:.1f}x'        if pd.notna(row["ratio"])        else "—"
    c_start = str(int(row["career_start"])) if pd.notna(row["career_start"]) else "—"
    miss    = f'{row["missing_pct"]:.1f}%'  if pd.notna(row["missing_pct"])  else "—"
    t_rev   = fmt_revenue(row["total_revenue"])
    a_rev   = fmt_revenue(row["avg_revenue"])

    top_tracks = (artist_tracks[["track_title", "track_listens", "estimated_revenue"]]
                  .dropna()
                  .sort_values("track_listens", ascending=False)
                  .head(5))

    track_rows = []
    for _, tr in top_tracks.iterrows():
        track_rows.append(html.Div([
            html.Div(str(tr["track_title"]), style={
                "color": C["text"], "fontSize": "10px",
                "whiteSpace": "nowrap", "overflow": "hidden",
                "textOverflow": "ellipsis", "maxWidth": "200px",
            }),
            html.Div([
                html.Span(f'♫ {int(tr["track_listens"]):,}',
                          style={"color": C["muted"], "fontSize": "9px",
                                 "marginRight": "8px"}),
                html.Span(fmt_revenue(tr["estimated_revenue"]),
                          style={"color": C["accent"], "fontSize": "9px"}),
            ]),
        ], style={"padding": "5px 0", "borderBottom": f"1px solid {C['border']}"}))

    return html.Div([
        html.Div(artist_name, style={
            "fontFamily": C["serif"], "fontSize": "17px",
            "color": C["text"], "marginBottom": "8px", "lineHeight": "1.3",
        }),
        html.Div([tag(f, col) for f, col in flags],
                 style={"marginBottom": "12px", "lineHeight": "2"}),
        html.Div([
            html.Span("Genres", style={"color": C["muted"], "fontSize": "9px",
                                       "textTransform": "uppercase", "letterSpacing": "1px"}),
            html.Div(str(row["genres"]) if pd.notna(row["genres"]) else "—",
                     style={"color": C["text"], "fontSize": "10px",
                            "marginTop": "2px", "marginBottom": "10px"}),
        ]),
        html.Div([
            metric_row("Tracks",        int(row["track_count"])),
            metric_row("Career start",  c_start),
            metric_row("Avg listens",   avg_l),
            metric_row("Best track",    max_l),
            metric_row("OHW ratio",     ratio),
            metric_row("Total revenue", t_rev),
            metric_row("Avg rev/track", a_rev),
            metric_row("Missing data",  miss),
            metric_row("Location",      location),
        ], style={"marginBottom": "14px"}),
        (html.A("↗ Artist website", href=str(website), target="_blank",
                style={"color": C["teal"], "fontSize": "10px", "textDecoration": "none"})
         if website and str(website) != "nan" else html.Span()),
        html.Hr(style={"borderColor": C["border"], "margin": "14px 0 10px"}),
        html.Div("Top Tracks", style={"fontSize": "9px", "color": C["accent"],
                                      "letterSpacing": "2px", "textTransform": "uppercase",
                                      "marginBottom": "6px"}),
        html.Div(track_rows),
    ])


# Executing the code
if __name__ == "__main__":
    app.run(debug=True)