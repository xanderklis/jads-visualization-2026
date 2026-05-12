from dash import Dash, html, dcc, Input, Output, ctx
import pandas as pd
import plotly.graph_objects as go

# =========================
# LOAD DATA
# =========================
tracks = pd.read_csv(
    "../data/tracks.csv",
    header=[0, 1],
    index_col=0
)
tracks.columns = ['_'.join(col) for col in tracks.columns.values]

tracks["year"]               = pd.to_datetime(tracks["album_date_released"], errors="coerce").dt.year
tracks["track_listens"]      = pd.to_numeric(tracks["track_listens"],   errors="coerce")
tracks["track_favorites"]    = pd.to_numeric(tracks["track_favorites"], errors="coerce")

# estimated Spotify revenue: $0.004 per stream
tracks["estimated_revenue"]  = tracks["track_listens"] * 0.004

# =========================
# ARTIST-LEVEL AGGREGATION
# =========================
def build_artist_df(track_df):
    grp = track_df.groupby("artist_name")

    agg = pd.DataFrame({
        "track_count":     grp["track_listens"].count(),
        "avg_listens":     grp["track_listens"].mean(),
        "max_listens":     grp["track_listens"].max(),
        "career_start":    grp["year"].min(),
        "genres":          grp["track_genre_top"].agg(lambda x: ", ".join(x.dropna().unique())),
        "total_missing":   grp.apply(lambda x: x.isna().sum().sum()),
        "total_fields":    grp.apply(lambda x: x.shape[0] * x.shape[1]),
        "total_revenue":   grp["estimated_revenue"].sum(),
        "avg_revenue":     grp["estimated_revenue"].mean(),
    }).reset_index()

    # one-hit wonder ratio
    agg["ratio"] = agg["max_listens"] / (agg["avg_listens"] + 1)

    # missing data percentage per artist (underground signal)
    agg["missing_pct"] = (agg["total_missing"] / agg["total_fields"] * 100).round(1)

    # avg_listens top 20% threshold
    p80 = agg["avg_listens"].quantile(0.80)
    agg["top_20pct_listens"] = agg["avg_listens"] >= p80

    # career start relative to max year in dataset
    max_year = agg["career_start"].max()
    agg["early_career"] = agg["career_start"] >= (max_year - 5)

    # label status
    label_col = "artist_associated_labels"
    if label_col in track_df.columns:
        label_map = track_df.groupby("artist_name")[label_col].first()
        agg["has_label"] = agg["artist_name"].map(label_map).notna()
        agg["has_label"] = (
            agg["has_label"] &
            agg["artist_name"].map(label_map).fillna("").astype(str).str.strip().ne("")
        )
    else:
        agg["has_label"] = False

    # talent flag: early career + few tracks + top 20% listens + no label
    agg["is_talent"] = (
        agg["early_career"] &
        (agg["track_count"] < 10) &
        agg["top_20pct_listens"] &
        ~agg["has_label"]
    )

    # one-hit wonder flag
    agg["is_one_hit"] = (agg["ratio"] > 5) & (agg["track_count"] > 1)

    return agg

artists_df = build_artist_df(tracks)

# =========================
# APP INIT
# =========================
app = Dash(__name__)

genres = sorted(tracks["track_genre_top"].dropna().unique())

# =========================
# THEME
# =========================
C = {
    "bg":      "#0f0f0f",
    "panel":   "#161616",
    "card":    "#1c1c1c",
    "border":  "#272727",
    "accent":  "#f5a623",
    "accent2": "#e05c2a",
    "teal":    "#4ecdc4",
    "green":   "#86efac",
    "text":    "#ede8df",
    "muted":   "#6b6560",
    "serif":   "Georgia, 'Times New Roman', serif",
    "mono":    "'Courier New', Courier, monospace",
}

PT = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family=C["mono"], color=C["text"], size=11),
    title_font=dict(family=C["serif"], size=15, color=C["text"]),
    title_x=0.03,
    margin=dict(l=44, r=16, t=46, b=40),
    xaxis=dict(gridcolor=C["border"], zerolinecolor=C["border"], tickfont_size=10),
    yaxis=dict(gridcolor=C["border"], zerolinecolor=C["border"], tickfont_size=10),
    hoverlabel=dict(bgcolor=C["card"], bordercolor=C["border"],
                    font_family=C["mono"], font_size=11, font_color=C["text"]),
    legend=dict(bgcolor="rgba(0,0,0,0)", bordercolor=C["border"],
                font=dict(family=C["mono"], size=10, color=C["muted"])),
)

# =========================
# LAYOUT HELPERS
# =========================
def section_label(txt):
    return html.P(txt, style={
        "fontFamily": C["mono"], "fontSize": "9px", "letterSpacing": "2.5px",
        "color": C["accent"], "textTransform": "uppercase", "margin": "0 0 10px 0",
    })

def field_label(txt):
    return html.Div(txt, style={
        "fontSize": "10px", "color": C["muted"], "marginBottom": "4px",
    })

def card(*children, style=None):
    base = {"background": C["card"], "border": f"1px solid {C['border']}",
            "borderRadius": "3px", "padding": "8px"}
    if style:
        base.update(style)
    return html.Div(list(children), style=base)

def stat_block(value, caption, color):
    return html.Div([
        html.Div(value, style={"fontFamily": C["serif"], "fontSize": "22px",
                               "color": color, "lineHeight": "1"}),
        html.Div(caption, style={"fontFamily": C["mono"], "fontSize": "9px",
                                 "letterSpacing": "1.5px", "color": C["muted"],
                                 "textTransform": "uppercase", "marginTop": "3px"}),
    ], style={"textAlign": "center", "padding": "10px 4px"})

def tag(txt, color=None):
    col = color or C["accent"]
    return html.Span(txt, style={
        "color": col, "fontSize": "9px",
        "border": f"1px solid {col}",
        "padding": "1px 6px", "borderRadius": "3px",
        "marginRight": "4px", "marginBottom": "4px",
        "display": "inline-block",
    })

def fmt_revenue(val):
    if pd.isna(val): return "—"
    if val >= 1_000_000: return f"${val/1_000_000:.1f}M"
    if val >= 1_000:     return f"${val/1_000:.1f}K"
    return f"${val:.2f}"

# =========================
# LAYOUT
# =========================
app.layout = html.Div(style={"background": C["bg"], "minHeight": "100vh",
                              "fontFamily": C["mono"], "color": C["text"]}, children=[

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


# =========================
# HELPERS
# =========================
def apply_filters(adf, sel_genres, checks, max_tracks):
    df = adf.copy()
    if sel_genres:
        df = df[df["genres"].apply(
            lambda g: any(genre in str(g) for genre in sel_genres)
        )]
    if max_tracks < 50:
        df = df[df["track_count"] <= max_tracks]
    if "talent"   in checks: df = df[df["is_talent"]]
    if "one_hit"  in checks: df = df[df["is_one_hit"]]
    if "no_label" in checks: df = df[~df["has_label"]]
    if "early"    in checks: df = df[df["early_career"]]
    return df


# =========================
# CALLBACKS
# =========================

# Clear
@app.callback(
    Output("genre-dropdown",    "value"),
    Output("filter-checklist",  "value"),
    Output("track-count-slider","value"),
    Input("clear-btn", "n_clicks"),
    prevent_initial_call=True,
)
def clear_filters(_):
    return None, [], 50


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
    Input("genre-dropdown",    "value"),
    Input("filter-checklist",  "value"),
    Input("track-count-slider","value"),
)
def update_charts(sel_genres, checks, max_tracks):

    adf = apply_filters(artists_df, sel_genres, checks or [], max_tracks)

    palette = [C["accent"], C["accent2"], C["teal"], "#c084fc",
               "#86efac", "#fbbf24", "#f87171", "#60a5fa"]

    p80 = artists_df["avg_listens"].quantile(0.80)

    # ── 1. Talent discovery scatter ───────────────────────────────
    def point_color(row):
        if row["is_talent"]:  return C["green"]
        if row["is_one_hit"]: return C["accent"]
        return C["muted"]

    adf_plot = adf.dropna(subset=["avg_listens", "track_count"])
    colors   = adf_plot.apply(point_color, axis=1).tolist()

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
        marker=dict(color=colors, size=6, opacity=0.75,
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
    talent_fig.update_layout(
        title="Talent Discovery · Track Count vs Avg Listens",
        xaxis_title="Number of tracks",
        yaxis_title="Avg listens per track",
        **PT,
    )

    # ── 2. Genre trend over time ───────────────────────────────────
    trend_df = tracks.dropna(subset=["track_genre_top", "year"]).copy()
    trend_df["year"] = trend_df["year"].astype(int)
    trend_df = trend_df[trend_df["year"].between(1990, 2024)]
    if sel_genres:
        trend_df  = trend_df[trend_df["track_genre_top"].isin(sel_genres)]
        top_genres = sel_genres
    else:
        top_genres = trend_df["track_genre_top"].value_counts().head(8).index.tolist()

    genre_trend_fig = go.Figure()
    for i, g in enumerate(top_genres):
        sub = (trend_df[trend_df["track_genre_top"] == g]
               .groupby("year").size().reset_index(name="count"))
        genre_trend_fig.add_trace(go.Scatter(
            x=sub["year"], y=sub["count"], mode="lines", name=g,
            line=dict(color=palette[i % len(palette)], width=2),
            hovertemplate=f"{g} · %{{x}}: <b>%{{y}}</b> tracks<extra></extra>",
        ))
    genre_trend_fig.update_layout(title="Genre Trends Over Time", **PT)

    # ── 3. One-hit wonder scatter ─────────────────────────────────
    ohw = adf.dropna(subset=["avg_listens", "max_listens"])
    ohw_colors = [C["accent"] if v else C["muted"] for v in ohw["is_one_hit"]]
    ohw_fig = go.Figure(go.Scatter(
        x=ohw["avg_listens"], y=ohw["max_listens"],
        mode="markers",
        marker=dict(color=ohw_colors, size=5, opacity=0.7),
        text=ohw["artist_name"],
        customdata=ohw["ratio"].round(1).values,
        hovertemplate=(
            "<b>%{text}</b><br>"
            "Avg listens: %{x:,.0f}<br>"
            "Max listens: %{y:,.0f}<br>"
            "Ratio: %{customdata}<extra></extra>"
        ),
    ))
    max_val = ohw["max_listens"].quantile(0.99) if not ohw.empty else 1
    ohw_fig.add_trace(go.Scatter(
        x=[0, max_val], y=[0, max_val], mode="lines",
        line=dict(color=C["border"], width=1, dash="dot"),
        showlegend=False, hoverinfo="skip",
    ))
    ohw_fig.update_layout(
        title="One-Hit Wonder Detection · Avg vs Max Listens",
        xaxis_title="Avg listens",
        yaxis_title="Max listens (best track)",
        **PT,
    )

    # ── 4. Emerging genres ────────────────────────────────────────
    new_artists = artists_df[artists_df["early_career"]]["artist_name"]
    new_tracks  = tracks[tracks["artist_name"].isin(new_artists)]
    if sel_genres:
        new_tracks = new_tracks[new_tracks["track_genre_top"].isin(sel_genres)]
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

    # ── 5. Missing data / hidden talent signal ────────────────────
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

    # ── 6. Revenue — top artists (unsigned highlighted) ───────────
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
    # invisible scatter traces just for the legend
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

    # ── 7. Revenue — by genre ─────────────────────────────────────
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

    # ── Stats ─────────────────────────────────────────────────────
    total_rev = adf["total_revenue"].sum()
    n_talent  = int(adf["is_talent"].sum())
    n_one_hit = int(adf["is_one_hit"].sum())
    stats = html.Div([
        stat_block(f"{len(adf):,}",      "artists",    C["accent"]),
        stat_block(f"{n_talent}",         "new talent", C["green"]),
        stat_block(f"{n_one_hit}",        "one-hit",    C["accent2"]),
        stat_block(fmt_revenue(total_rev),"est. rev.",  C["teal"]),
    ], style={"display": "grid", "gridTemplateColumns": "1fr 1fr",
              "gap": "6px", "marginTop": "4px"})

    # ── Badge ─────────────────────────────────────────────────────
    parts = []
    if sel_genres:       parts.append(f"{len(sel_genres)} genre(s)")
    if checks:           parts.append(" · ".join(checks))
    if max_tracks < 50:  parts.append(f"≤{max_tracks} tracks")
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
    if row["is_talent"]:    flags.append(("NEW TALENT",     C["green"]))
    if row["is_one_hit"]:   flags.append(("ONE-HIT WONDER", C["accent"]))
    if not row["has_label"]:flags.append(("NO LABEL",       C["teal"]))
    if row["early_career"]: flags.append(("EARLY CAREER",   C["accent2"]))

    def metric_row(lbl, value):
        return html.Div([
            html.Span(lbl, style={"color": C["muted"], "fontSize": "9px",
                                  "letterSpacing": "1px", "textTransform": "uppercase"}),
            html.Span(str(value), style={"color": C["text"], "fontSize": "12px",
                                          "fontFamily": C["serif"], "float": "right"}),
        ], style={"padding": "7px 0", "borderBottom": f"1px solid {C['border']}",
                  "overflow": "hidden"})

    avg_l   = f'{row["avg_listens"]:,.0f}'  if pd.notna(row["avg_listens"])   else "—"
    max_l   = f'{row["max_listens"]:,.0f}'  if pd.notna(row["max_listens"])   else "—"
    ratio   = f'{row["ratio"]:.1f}x'        if pd.notna(row["ratio"])         else "—"
    c_start = str(int(row["career_start"])) if pd.notna(row["career_start"])  else "—"
    miss    = f'{row["missing_pct"]:.1f}%'  if pd.notna(row["missing_pct"])   else "—"
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


# =========================
# RUN
# =========================
if __name__ == "__main__":
    app.run(debug=True)