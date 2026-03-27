# Configuration settings for the Dash app


DEBUG = True
HOST = '127.0.0.1'
PORT = 8050

EXTERNAL_STYLESHEETS = [
    'https://codepen.io/chriddyp/pen/bWLwgP.css'
]

pages = ["home", "cftc_positioning", "tff", "data_guide"]
page_default = "home"

page_active = [True if p == page_default else False for p in pages]

sidebar_style = {
    "position": "fixed",
    "top": 62.5,
    "left": 0,
    "bottom": 0,
    "width": "16rem",
    "height": "100%",
    "z-index": 1,
    "overflow-x": "hidden",
    "transition": "all 0.5s",
    "padding": "0.5rem 1rem",
    "background-color": "#f8f9fa",
}
sidebar_hidden_style = {
    "position": "fixed",
    "top": 62.5,
    "left": "-16rem",
    "bottom": 0,
    "width": "16rem",
    "height": "100%",
    "z-index": 1,
    "overflow-x": "hidden",
    "transition": "all 0.5s",
    "padding": "0rem 0rem",
    "background-color": "#f8f9fa",
}

content_style = {
    "transition": "margin-left 0.5s",
    "margin-left": "18rem",
    "margin-right": "2rem",
    "padding": "2rem 1rem",
    "background-color": "#f8f9fa",
}

content_hidden_style = {
    "transition": "margin-left 0.5s",
    "margin-left": "2rem",
    "margin-right": "2rem",
    "padding": "2rem 1rem",
    "background-color": "#f8f9fa",
}

styles = {
    "sidebar_style": sidebar_style,
    "sidebar_hidden_style": sidebar_hidden_style,
    "content_style": content_style,
    "content_hidden_style": content_hidden_style
}
page_cfg = {
    "pages": pages,
    "page_default": page_default,
    "page_active": page_active
}