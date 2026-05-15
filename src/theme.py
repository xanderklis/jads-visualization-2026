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