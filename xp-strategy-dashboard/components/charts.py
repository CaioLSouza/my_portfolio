"""Plotly chart factories with one consistent visual system.

Categorical series colors follow a fixed CVD-validated order (blue, aqua,
yellow, violet, magenta, orange). Green/red are reserved for *sign* only
(gains/losses, inflow/outflow) and never used as series identity.
"""

from __future__ import annotations

from typing import Optional, Sequence

import pandas as pd
import plotly.graph_objects as go

# fixed categorical order — never cycled, never reassigned on filtering
SERIES = ["#2a78d6", "#1baf7a", "#eda100", "#4a3aa7", "#e87ba4", "#eb6834",
          "#184f95", "#52514e"]
GOOD = "#0ca30c"
BAD = "#d03b3b"
GOOD_TEXT = "#006300"
NEUTRAL_MID = "#f0efec"
GRID = "#e1e0d9"
INK = "#0b0b0b"
MUTED = "#898781"
SURFACE = "#fcfcfb"

# green ↔ red diverging with a neutral gray midpoint; values are always also
# printed (hover/labels) so sign never rides on color alone.
DIVERGING = [[0.0, BAD], [0.5, NEUTRAL_MID], [1.0, GOOD]]

_LAYOUT = dict(
    font=dict(family='system-ui, -apple-system, "Segoe UI", sans-serif',
              color=INK, size=12),
    paper_bgcolor=SURFACE,
    plot_bgcolor=SURFACE,
    margin=dict(l=10, r=10, t=30, b=10),
    hovermode="x unified",
    legend=dict(orientation="h", yanchor="bottom", y=1.01, x=0,
                font=dict(size=11)),
    xaxis=dict(gridcolor=GRID, zeroline=False, linecolor="#c3c2b7"),
    yaxis=dict(gridcolor=GRID, zeroline=False, linecolor="#c3c2b7"),
)


def _base(fig: go.Figure, height: int = 340, title: str = "") -> go.Figure:
    fig.update_layout(**_LAYOUT, height=height)
    if title:
        # reserve two rows in the top margin: title, then legend above plot
        fig.update_layout(
            title=dict(text=title, font=dict(size=14), x=0, xanchor="left",
                       y=1, yanchor="top", pad=dict(t=8)),
            margin=dict(l=10, r=10, t=76, b=10),
            legend=dict(orientation="h", yanchor="bottom", y=1.0, x=0,
                        font=dict(size=11)),
        )
    return fig


def line(df: pd.DataFrame, x: str, ys: Sequence[str], names: Optional[dict] = None,
         height: int = 340, title: str = "", pct: bool = False,
         normalize: bool = False) -> go.Figure:
    """Multi-series line chart; optional rebase to 100 for comparability."""
    fig = go.Figure()
    names = names or {}
    for i, col in enumerate(ys):
        s = df[col]
        if normalize:
            first = s.dropna()
            s = s / first.iloc[0] * 100 if len(first) else s
        fig.add_trace(go.Scatter(
            x=df[x], y=s, mode="lines", name=names.get(col, col),
            line=dict(width=2, color=SERIES[i % len(SERIES)]),
        ))
    fig = _base(fig, height, title)
    if pct:
        fig.update_yaxes(tickformat=".1%")
    return fig


def bar_mag(labels: Sequence, values: Sequence, height: int = 340,
            title: str = "", value_fmt: str = ",.1f",
            pct_axis: bool = False) -> go.Figure:
    """Horizontal magnitude bars in the neutral series blue (no sign)."""
    fig = go.Figure(go.Bar(
        x=list(values), y=list(labels), orientation="h",
        marker=dict(color=SERIES[0], line=dict(width=0)),
        hovertemplate="%{y}: %{x:" + value_fmt + "}<extra></extra>",
    ))
    fig.update_yaxes(autorange="reversed")
    fig = _base(fig, height, title)
    fig.update_layout(hovermode="closest", bargap=0.25, showlegend=False)
    if pct_axis:
        fig.update_xaxes(tickformat=".0%")
    return fig


def bar_signed(labels: Sequence, values: Sequence, height: int = 340,
               title: str = "", horizontal: bool = True,
               value_fmt: str = ",.1f") -> go.Figure:
    """Diverging bar chart: sign carries green/red, values printed on hover."""
    colors = [GOOD if v >= 0 else BAD for v in values]
    if horizontal:
        fig = go.Figure(go.Bar(
            x=list(values), y=list(labels), orientation="h",
            marker=dict(color=colors, line=dict(width=0)),
            hovertemplate="%{y}: %{x:" + value_fmt + "}<extra></extra>",
        ))
        fig.update_yaxes(autorange="reversed")
    else:
        fig = go.Figure(go.Bar(
            x=list(labels), y=list(values),
            marker=dict(color=colors, line=dict(width=0)),
            hovertemplate="%{x}: %{y:" + value_fmt + "}<extra></extra>",
        ))
    fig = _base(fig, height, title)
    fig.update_layout(hovermode="closest", bargap=0.25, showlegend=False)
    if "%" in value_fmt:
        if horizontal:
            fig.update_xaxes(tickformat=".0%")
        else:
            fig.update_yaxes(tickformat=".0%")
    return fig


def grouped_bars(df: pd.DataFrame, x: str, ys: Sequence[str],
                 names: Optional[dict] = None, height: int = 340,
                 title: str = "", stacked: bool = False) -> go.Figure:
    fig = go.Figure()
    names = names or {}
    for i, col in enumerate(ys):
        fig.add_trace(go.Bar(x=df[x], y=df[col], name=names.get(col, col),
                             marker=dict(color=SERIES[i % len(SERIES)],
                                         line=dict(width=0))))
    fig = _base(fig, height, title)
    fig.update_layout(barmode="relative" if stacked else "group", bargap=0.2)
    return fig


def heatmap(z: pd.DataFrame, height: int = 380, title: str = "",
            fmt: str = ".1%", zmid: float = 0.0,
            sequential: bool = False, show_text: bool = True) -> go.Figure:
    """Heatmap. Diverging green/red around 0 by default; ``sequential=True``
    switches to a one-hue blue ramp for pure magnitudes (e.g. weights)."""
    zdf = pd.DataFrame(z)
    if sequential:
        scale = [[0.0, "#cde2fb"], [0.5, "#3987e5"], [1.0, "#0d366b"]]
        zmin, zmax_, mid = None, None, None
    else:
        scale = DIVERGING
        zmax_ = float(zdf.abs().max().max() or 1)
        zmin, mid = -zmax_, zmid
    fig = go.Figure(go.Heatmap(
        z=zdf.values, x=list(zdf.columns), y=list(zdf.index),
        colorscale=scale, zmid=mid, zmin=zmin, zmax=zmax_,
        texttemplate=("%{z:" + fmt + "}") if show_text else None,
        textfont=dict(size=11),
        hovertemplate="%{y} · %{x}: %{z:" + fmt + "}<extra></extra>",
        colorbar=dict(tickformat=fmt, outlinewidth=0, thickness=12),
        xgap=2 if show_text else 1, ygap=2 if show_text else 1,
        hoverongaps=False,
    ))
    fig = _base(fig, height, title)
    fig.update_layout(hovermode="closest")
    fig.update_xaxes(side="top", showgrid=False)
    fig.update_yaxes(showgrid=False, autorange="reversed")
    return fig


def scatter(df: pd.DataFrame, x: str, y: str, text: str,
            color_by_sign: Optional[str] = None, height: int = 420,
            title: str = "", x_pct: bool = False, y_pct: bool = False) -> go.Figure:
    colors = (
        [GOOD if v >= 0 else BAD for v in df[color_by_sign]]
        if color_by_sign else SERIES[0]
    )
    fig = go.Figure(go.Scatter(
        x=df[x], y=df[y], mode="markers", text=df[text],
        marker=dict(size=9, color=colors, opacity=0.85,
                    line=dict(width=1, color=SURFACE)),
        hovertemplate="<b>%{text}</b><br>" + x + ": %{x:,.2f}<br>" + y +
        ": %{y:,.2f}<extra></extra>",
    ))
    fig = _base(fig, height, title)
    fig.update_layout(hovermode="closest", showlegend=False)
    if x_pct:
        fig.update_xaxes(tickformat=".0%")
    if y_pct:
        fig.update_yaxes(tickformat=".0%")
    return fig


def area(df: pd.DataFrame, x: str, ys: Sequence[str], names: Optional[dict] = None,
         height: int = 300, title: str = "", pct: bool = False) -> go.Figure:
    fig = go.Figure()
    names = names or {}
    for i, col in enumerate(ys):
        fig.add_trace(go.Scatter(
            x=df[x], y=df[col], mode="lines", stackgroup="one",
            name=names.get(col, col),
            line=dict(width=1, color=SERIES[i % len(SERIES)]),
        ))
    fig = _base(fig, height, title)
    if pct:
        fig.update_yaxes(tickformat=".0%")
    return fig
