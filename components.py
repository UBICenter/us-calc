import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
import dash_bootstrap_components as dbc


def make_html_label(label_text):
    """returns formatted html.Label instance for 4 input card bodies"""
    return html.Label(
        [label_text],
        style={
            "font-weight": "bold",
            "text-align": "center",
            "color": "white",
            "fontSize": 20,
        },
    )


def set_options(label_value_dict):
    """returns a list of options for dropdown/checklist/radio inputs
    Args
        dict: dictionary of {label : value} pairs for inputs
        NOTE: values must be strings. labels are visible to user, values
        are referenced by the component_id in the app.callback() function
    Returns
    -------
    list
        list of dictionary objects with keys "label" and "value"
    """
    return [{"label": k, "value": v} for k, v in label_value_dict.items()]
