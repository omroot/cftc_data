import datetime
import dash
import dash_bootstrap_components as dbc

from dash.dependencies import Input, Output, State



# Initialize the Dash app
app = dash.Dash(external_stylesheets= [dbc.themes.BOOTSTRAP])
app.title = "CFTC Positioning Dashboard"
app.config.suppress_callback_exceptions = True
