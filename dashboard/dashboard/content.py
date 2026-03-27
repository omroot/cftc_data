from dash import dcc, html
import dash_bootstrap_components as dbc

import datetime
from dash.dependencies import Input, Output, State

from dashboard.dashboard.layout.page_home import page_home
from dashboard.dashboard.layout.page_cftc_positioning import page_cftc_positioning
from dashboard.dashboard.layout.page_tff import page_tff
from dashboard.dashboard.layout.page_data_guide import page_data_guide

from dashboard.dashboard.index import app

# register callbacks (import triggers decoration)
import dashboard.dashboard.layout.callbacks.callbacks_cftc  # noqa: F401
import dashboard.dashboard.layout.callbacks.callbacks_tff   # noqa: F401
import dashboard.dashboard.layout.callbacks.callbacks_home  # noqa: F401

import dashboard.dashboard.config as cfg


def server_layout():
    # layout
    navbar = dbc.NavbarSimple(
        children=[
            dbc.Button(
                "Sidebar",
                color="primary",
                className="mr-1",
                id="btn_sidebar",
            ),
        ],
        brand="CFTC Positioning Dashboard",
        brand_href="#",
        color="dark",
        dark=True,
        fluid=True,
    )
    sidebar = html.Div(
        [
            html.H4("Contents"),
            html.Hr(),
            dbc.Nav(
                [
                    dbc.NavLink("Home", href="/home", id="link_home"),
                    dbc.NavLink("CFTC Positioning", href="/cftc_positioning", id="link_cftc_positioning"),
                    dbc.NavLink("TFF Positioning", href="/tff", id="link_tff"),
                    dbc.NavLink("Data Guide", href="/data_guide", id="link_data_guide"),
                ],
                vertical=True,
                pills=True,
            ),
        ],
        id="sidebar",
        style=cfg.styles["sidebar_style"],
    )

    content = html.Div(id="page_content", style=cfg.styles["content_style"])
    layout = html.Div([
        dcc.Store(id="date_today"),
        dcc.Interval(id="interval_update_date",
                     interval=1000 * 60 * 60 * 3,
                     n_intervals=0),
        dcc.Store(id="sidebar_click"),
        dcc.Location(id="url"),
        navbar,
        sidebar,
        content,
    ])
    return layout


app.layout = server_layout


@app.callback(
    Output("date_today", "data"),
    Input("interval_update_date", "n_intervals"),
)
def update_date(n):
    return datetime.date.today()


@app.callback(
    [
        Output("sidebar", "style"),
        Output("page_content", "style"),
        Output("sidebar_click", "data"),
    ],
    [Input("btn_sidebar", "n_clicks")],
    [State("sidebar_click", "data")],
)
def toggle_sidebar(btn_sidebar, sidebar_click_state):
    if btn_sidebar:
        if sidebar_click_state == "SHOW":
            sidebar_style = cfg.styles["sidebar_hidden_style"]
            content_style = cfg.styles["content_hidden_style"]
            cur_sidebar_click_state = "HIDDEN"
        else:
            sidebar_style = cfg.styles["sidebar_style"]
            content_style = cfg.styles["content_style"]
            cur_sidebar_click_state = "SHOW"
    else:
        sidebar_style = cfg.styles["sidebar_style"]
        content_style = cfg.styles["content_style"]
        cur_sidebar_click_state = "SHOW"
    return sidebar_style, content_style, cur_sidebar_click_state


@app.callback(
    [Output(f"link_{name}", "active") for name in cfg.page_cfg["pages"]],
    [Input("url", "pathname")],
)
def toggle_active_links(pathname):
    if pathname == "/":
        return cfg.page_cfg["page_active"]
    return [pathname == f"/{name}" for name in cfg.page_cfg["pages"]]


@app.callback(
    Output("page_content", "children"),
    [Input("url", "pathname")],
)
def render_page_content(pathname):
    if pathname in ["/", "/home"]:
        return page_home
    if pathname == "/cftc_positioning":
        return page_cftc_positioning
    if pathname == "/tff":
        return page_tff
    if pathname == "/data_guide":
        return page_data_guide
    return html.Div([
        html.H3("404 - Page not found", className="text-danger"),
        html.P(f"The pathname '{pathname}' was not recognised."),
    ])
