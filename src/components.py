from dash import html
from .theme import C
import pandas as pd

# This is why you don´t let Claude do everything, I don´t know what all this damn code does -Xander
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
