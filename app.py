import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
import dash_bootstrap_components as dbc
import microdf as mdf
import os
import us

# Import data from Ipums
person = pd.read_csv("person.csv.gz")
spmu = pd.read_csv("spmu.csv.gz")
# import baseline poverty gap, gini by state & us
all_state_stats = pd.read_csv("all_state_stats.csv.gz", index_col=0)
# import baseline white/black/child etc. poverty rates & population
demog_stats = pd.read_csv("demog_stats.csv.gz")

# Colors
BLUE = "#1976D2"

# create a list of all states, including "US" as a state
states_no_us = person.state.unique().tolist()
states_no_us.sort()
states = ["US"] + states_no_us


# Create the 4 input cards
cards = dbc.CardDeck(
    [
        # define first card with state-dropdown component
        dbc.Card(
            [
                dbc.CardBody(
                    [
                        html.Label(
                            ["Select state:"],
                            style={
                                "font-weight": "bold",
                                "text-align": "center",
                                "color": "white",
                                "fontSize": 20,
                            },
                        ),
                        dcc.Dropdown(
                            # define component_id for input of app@callback function
                            id="state-dropdown",
                            multi=False,
                            value="US",
                            # create a list of dicts of states and their labels
                            # to be selected by user in dropdown
                            options=[{"label": x, "value": x} for x in states],
                        ),
                        html.Br(),
                        html.Label(
                            ["Reform level:"],
                            style={
                                "font-weight": "bold",
                                "text-align": "center",
                                "color": "white",
                                "fontSize": 20,
                            },
                        ),
                        dcc.RadioItems(
                            id="level",
                            options=[
                                {"label": "Federal", "value": "federal"},
                                {"label": "State", "value": "state"},
                            ],
                            value="federal",
                            labelStyle={"display": "block"},
                        ),
                    ]
                ),
            ],
            color="info",
            outline=False,
        ),
        # second card -
        # tax slider
        #   allows user to repeal certain federal and state taxes
        #   component_id: "taxes-checklist"
        # tax rate slider
        #   Allows user to adjust tax rate that determines ubi benefit amount
        #   component_id="agi-slider"
        dbc.Card(
            [
                dbc.CardBody(
                    [
                        # define attributes of taxes-checklist component
                        html.Label(
                            ["Repeal current taxes:"],
                            style={
                                "font-weight": "bold",
                                "text-align": "center",
                                "color": "white",
                                "fontSize": 20,
                            },
                        ),
                        html.Br(),
                        dcc.Checklist(
                            # define component id to be used in callback
                            id="taxes-checklist",
                            options=[
                                {"label": "Income taxes", "value": "fedtaxac"},
                                {
                                    "label": "Employee side payroll",
                                    "value": "fica",
                                },
                            ],
                            value=[],
                            labelStyle={"display": "block"},
                        ),
                        html.Br(),
                        # defines label/other HTML attributes of agi-slider component
                        html.Label(
                            ["Income tax rate"],
                            style={
                                "font-weight": "bold",
                                "text-align": "center",
                                "color": "white",
                                "fontSize": 20,
                            },
                        ),
                        dcc.Slider(
                            id="agi-slider",
                            min=0,
                            max=50,
                            step=1,
                            value=0,
                            # TODO make slider easier to see when it's over tick marks
                            tooltip={
                                "always_visible": True,
                                "placement": "bottom",
                            },
                            # define marker values to show increments on slider
                            marks={
                                0: {
                                    "label": "0%",
                                    "style": {"color": "#F8F8FF"},
                                },
                                10: {
                                    # "label": "10%",
                                    "style": {"color": "#F8F8FF"},
                                },
                                20: {
                                    # "label": "20%",
                                    "style": {"color": "#F8F8FF"},
                                },
                                30: {
                                    # "label": "30%",
                                    "style": {"color": "#F8F8FF"},
                                },
                                40: {
                                    # "label": "40%",
                                    "style": {"color": "#F8F8FF"},
                                },
                                50: {
                                    "label": "50%",
                                    "style": {"color": "#F8F8FF"},
                                },
                            },
                        ),
                        html.Div(id="slider-output-container"),
                    ]
                ),
                html.Br(),
            ],
            color="info",
            outline=False,
        ),
        # define third card where the repeal benefits checklist is displayed
        dbc.Card(
            [
                dbc.CardBody(
                    [
                        # label the card
                        html.Label(
                            ["Repeal benefits:"],
                            style={
                                "font-weight": "bold",
                                "text-align": "center",
                                "color": "white",
                                "fontSize": 20,
                            },
                        ),
                        # use  dash component to create checklist to choose
                        # which benefits to repeal
                        dcc.Checklist(
                            # this id string is a dash component_id
                            # and is referenced as in input in app.callback
                            id="benefits-checklist",
                            # 'options' here refers the selections available to the user in the
                            # checklist
                            options=[
                                {
                                    # label what user will see next to check box
                                    "label": "  Child Tax Credit",
                                    # to be used ________
                                    "value": "ctc",
                                },
                                {
                                    "label": "  Supplemental Security Income (SSI)",
                                    "value": "incssi",
                                },
                                {
                                    "label": "  SNAP (food stamps)",
                                    "value": "spmsnap",
                                },
                                {
                                    "label": "  Earned Income Tax Credit",
                                    "value": "eitcred",
                                },
                                {
                                    "label": "  Unemployment benefits",
                                    "value": "incunemp",
                                },
                                {
                                    "label": "  Energy subsidy (LIHEAP)",
                                    "value": "spmheat",
                                },
                            ],
                            # do not repeal benefits by default
                            value=[],
                            labelStyle={"display": "block"},
                        ),
                    ]
                ),
            ],
            color="info",
            outline=False,
        ),
        # exclude/include from UBI checklist
        dbc.Card(
            [
                dbc.CardBody(
                    [
                        html.Label(
                            ["Include in UBI:"],
                            style={
                                "font-weight": "bold",
                                "text-align": "center",
                                "color": "white",
                                "fontSize": 20,
                            },
                        ),
                        dcc.Checklist(
                            id="include-checklist",
                            options=[
                                {
                                    "label": "non-Citizens",
                                    "value": "non_citizens",
                                },
                                {"label": "Children", "value": "children"},
                                {"label": "Adult", "value": "adults"},
                            ],
                            # specify checked items
                            value=[
                                "adults",
                                "children",
                                "non_citizens",
                            ],
                            labelStyle={"display": "block"},
                        ),
                    ]
                ),
            ],
            color="info",
            outline=False,
        ),
    ]
)


charts = dbc.CardDeck(
    [
        dbc.Card(
            dcc.Graph(id="my-graph", figure={}),
            body=True,
            color="info",
        ),
        dbc.Card(
            dcc.Graph(id="my-graph2", figure={}),
            body=True,
            color="info",
        ),
    ]
)


text = (
    dbc.Card(
        [
            dbc.CardBody(
                [
                    html.Div(
                        id="ubi-output",
                        style={
                            "text-align": "left",
                            "color": "black",
                            "fontSize": 25,
                        },
                    ),
                    html.Div(
                        id="winners-output",
                        style={
                            "text-align": "left",
                            "color": "black",
                            "fontSize": 25,
                        },
                    ),
                    html.Div(
                        id="resources-output",
                        style={
                            "text-align": "left",
                            "color": "black",
                            "fontSize": 25,
                        },
                    ),
                ]
            ),
        ],
        color="white",
        outline=False,
    ),
)

# Get base pathname from an environment variable that CS will provide.
url_base_pathname = os.environ.get("URL_BASE_PATHNAME", "/")

app = dash.Dash(
    __name__,
    external_stylesheets=[
        dbc.themes.FLATLY,
        "https://fonts.googleapis.com/css2?family=Lato:wght@300;400&display=swap",
        "/assets/style.css",
    ],
    # Pass the url base pathname to Dash.
    url_base_pathname=url_base_pathname,
)

server = app.server

# Design the app
app.layout = html.Div(
    [
        # navbar
        dbc.Navbar(
            [
                html.A(
                    dbc.Row(
                        [
                            dbc.Col(
                                html.Img(
                                    src="https://blog.ubicenter.org/_static/ubi_center_logo_wide_blue.png",
                                    height="30px",
                                )
                            ),
                        ],
                        align="center",
                        no_gutters=True,
                    ),
                    href="https://www.ubicenter.org",
                    target="blank",
                ),
                dbc.NavbarToggler(id="navbar-toggler"),
            ]
        ),
        html.Br(),
        dbc.Row(
            [
                dbc.Col(
                    html.H1(
                        "Explore funding mechanisms of UBI",
                        id="header",
                        style={
                            "text-align": "center",
                            "color": "#1976D2",
                            "fontSize": 50,
                            "letter-spacing": "2px",
                            "font-weight": 300,
                        },
                    ),
                    width={"size": 8, "offset": 2},
                ),
            ]
        ),
        html.Br(),
        dbc.Row(
            [
                dbc.Col(
                    html.H4(
                        "Use the interactive below to explore different funding mechanisms for a UBI and their impact. You may choose between repealing benefits or adding new taxes.  When a benefit is repealed or a new tax is added, the new revenue automatically funds a UBI to all people equally to ensure each plan is budget neutral.",
                        style={
                            "text-align": "left",
                            "color": "black",
                            "fontSize": 25,
                        },
                    ),
                    width={"size": 8, "offset": 2},
                ),
            ]
        ),
        html.Br(),
        dbc.Row([dbc.Col(cards, width={"size": 10, "offset": 1})]),
        html.Br(),
        dbc.Row(
            [
                dbc.Col(
                    html.H1(
                        "Results of your reform:",
                        style={
                            "text-align": "center",
                            "color": "#1976D2",
                            "fontSize": 30,
                        },
                    ),
                    width={"size": 8, "offset": 2},
                ),
            ]
        ),
        dbc.Row([dbc.Col(text, width={"size": 6, "offset": 3})]),
        html.Br(),
        dbc.Row([dbc.Col(charts, width={"size": 10, "offset": 1})]),
        html.Br(),
        html.Br(),
        html.Br(),
        html.Br(),
        html.Br(),
        html.Br(),
    ]
)

# Assign callbacks


@app.callback(
    Output(component_id="ubi-output", component_property="children"),
    Output(component_id="winners-output", component_property="children"),
    Output(component_id="resources-output", component_property="children"),
    Output(component_id="my-graph", component_property="figure"),
    Output(component_id="my-graph2", component_property="figure"),
    Input(component_id="state-dropdown", component_property="value"),
    Input(component_id="level", component_property="value"),
    Input(component_id="agi-slider", component_property="value"),
    Input(component_id="benefits-checklist", component_property="value"),
    Input(component_id="taxes-checklist", component_property="value"),
    Input(component_id="include-checklist", component_property="value"),
)
def ubi(state, level, agi_tax, benefits, taxes, include):
    """this does everything from microsimulation to figure creation.
        Dash does something automatically where it takes the input arguments
        in the order given in the @app.callback decorator
    Args:
        state:  takes input from callback input, component_id="state-dropdown"
        level:  component_id="level"
        agi_tax:  component_id="agi-slider"
        benefits:  component_id="benefits-checklist"
        taxes:  component_id="taxes-checklist"
        include: component_id="include-checklist"

    Returns:
        ubi_line: outputs to  "ubi-output" in @app.callback
        winners_line: outputs to "winners-output" in @app.callback
        resources_line: outputs to "resources-output" in @app.callback
        fig: outputs to "my-graph" in @app.callback
        fig2: outputs to "my-graph2" in @app.callback
    """
    # if the "Reform level" selected by the user is federal
    if level == "federal":
        # combine taxes and benefits checklists into one list to be used to
        #  subset spmu dataframe
        taxes_benefits = taxes + benefits
        # initialize new resources column with old resources as baseline
        spmu["new_resources"] = spmu.spmtotres
        # initialize revenue at zero
        revenue = 0

        # Calculate the new revenue and spmu resources from tax and benefit change
        for tax_benefit in taxes_benefits:
            # subtract taxes and benefits that have been changed from spm unit's resources
            spmu.new_resources -= spmu[tax_benefit]
            # add that same value to revenue
            revenue += mdf.weighted_sum(spmu, tax_benefit, "spmwt")

        # if "Income taxes" = ? and "child_tax_credit" = ?
        # in taxes/benefits checklist
        if ("fedtaxac" in taxes_benefits) & ("ctc" in taxes_benefits):
            spmu.new_resources += spmu.ctc
            revenue -= mdf.weighted_sum(spmu, "ctc", "spmwt")

        if ("fedtaxac" in taxes_benefits) & ("eitcred" in taxes_benefits):
            spmu.new_resources += spmu.eitcred
            revenue -= mdf.weighted_sum(spmu, "eitcred", "spmwt")

        # Calculate the new taxes from flat tax on AGI
        tax_rate = agi_tax / 100
        spmu["new_taxes"] = np.maximum(spmu.adjginc, 0) * tax_rate
        # subtract new taxes from new resources
        spmu.new_resources -= spmu.new_taxes
        # add new revenue when new taxes are applied on spmus, multiplied by weights
        revenue += mdf.weighted_sum(spmu, "new_taxes", "spmwt")

        # Calculate the total UBI a spmu recieves based on exclusions
        spmu["numper_ubi"] = spmu.numper

        if "children" not in include:
            # subtract the number of children from the number of
            # people in spm unit receiving ubi benefit
            spmu["numper_ubi"] -= spmu.child

        if "non_citizens" not in include:
            spmu["numper_ubi"] -= spmu.non_citizen

        if ("children" not in include) and ("non_citizens" not in include):
            spmu["numper_ubi"] += spmu.non_citizen_child

        if "adults" not in include:
            spmu["numper_ubi"] -= spmu.adult

        if ("adults" not in include) and ("non_citizens" not in include):
            spmu["numper_ubi"] += spmu.non_citizen_adult

        # Assign UBI
        ubi_population = (spmu.numper_ubi * spmu.spmwt).sum()
        ubi = revenue / ubi_population
        spmu["total_ubi"] = ubi * spmu.numper_ubi

        # Calculate change in resources
        spmu.new_resources += spmu.total_ubi
        spmu["new_resources_per_person"] = spmu.new_resources / spmu.numper
        # Sort by state

        # NOTE: the "target" here refers to the population being
        # measured for gini/poverty rate/etc.
        # I.e. the total population of the state/country and
        # INCLUDING those excluding form recieving ubi payments

        # state here refers to the selection from the drop down, not the reform level
        if state == "US":
            target_spmu = spmu
        else:
            target_spmu = spmu[spmu.state == state]

    # if the "Reform level" dropdown selected by the user is State
    if level == "state":

        # Sort by state
        if state == "US":
            target_spmu = spmu
        else:
            target_spmu = spmu[spmu.state == state]

        # Initialize
        target_spmu["new_resources"] = target_spmu.spmtotres
        revenue = 0

        # Change income tax repeal to state level
        if "fedtaxac" in taxes:
            target_spmu.new_resources -= target_spmu.stataxac
            revenue += mdf.weighted_sum(target_spmu, "stataxac", "spmwt")

        # Calculate change in tax revenue
        tax_rate = agi_tax / 100
        target_spmu["new_taxes"] = target_spmu.adjginc * tax_rate

        target_spmu.new_resources -= target_spmu.new_taxes
        revenue += mdf.weighted_sum(target_spmu, "new_taxes", "spmwt")

        # Calculate the total UBI a spmu recieves based on exclusions
        target_spmu["numper_ubi"] = target_spmu.numper

        if "children" not in include:
            target_spmu["numper_ubi"] -= target_spmu.child

        if "non_citizens" not in include:
            target_spmu["numper_ubi"] -= target_spmu.non_citizen

        if ("children" not in include) and ("non_citizens" not in include):
            target_spmu["numper_ubi"] += target_spmu.non_citizen_child

        if "adults" not in include:
            target_spmu["numper_ubi"] -= target_spmu.adult

        if ("adults" not in include) and ("non_citizens" not in include):
            target_spmu["numper_ubi"] += target_spmu.non_citizen_adult

        # Assign UBI
        ubi_population = (target_spmu.numper_ubi * target_spmu.spmwt).sum()
        ubi = revenue / ubi_population
        target_spmu["total_ubi"] = ubi * target_spmu.numper_ubi

        # Calculate change in resources
        target_spmu.new_resources += target_spmu.total_ubi
        target_spmu["new_resources_per_person"] = (
            target_spmu.new_resources / target_spmu.numper
        )

    # Merge and create target_persons -
    # NOTE: the "target" here refers to the population being
    # measured for gini/poverty rate/etc.
    # I.e. the total population of the state/country and
    # INCLUDING those excluding form recieving ubi payments
    sub_spmu = target_spmu[
        ["spmfamunit", "year", "new_resources", "new_resources_per_person"]
    ]
    target_persons = person.merge(sub_spmu, on=["spmfamunit", "year"])

    # filter demog_stats for selected state from dropdown
    baseline_demog = demog_stats[(demog_stats.state == state)]

    def return_demog(demog, metric):
        """
        retrieve pre-processed data by demographic
        args:
            demog - string one of
                ['person', 'adult', 'child', 'black', 'white_non_hispanic',
            'hispanic', 'pwd', 'non_citizen', 'non_citizen_adult',
            'non_citizen_child']
            metric - string, one of ['pov_rate', 'pop']
        returns:
            value - float
        """

        value = baseline_demog.loc[
            (baseline_demog["demog"] == demog) & (baseline_demog["metric"] == metric),
            "value",
            # NOTE: returns the first value as a float, be careful if you redefine baseline_demog
        ].values[0]

        return value

    population = return_demog(demog="person", metric="pop")
    child_population = return_demog(demog="child", metric="pop")
    non_citizen_population = return_demog(demog="non_citizen", metric="pop")
    non_citizen_child_population = return_demog(demog="non_citizen_child", metric="pop")

    # filter all state stats gini, poverty_gap, etc. for dropdown state
    baseline_all_state_stats = all_state_stats[(all_state_stats.index == state)]

    def return_all_state(metric):
        """filter baseline_all_state_stats and return value of select metric

        Keyword arguments:
        metric - string, one of 'poverty_gap', 'gini', 'total_resources'

        returns:
            value- float
        """

        return baseline_all_state_stats[metric].values[0]

    # Calculate total change in resources
    original_total_resources = return_all_state("total_resources")
    # DO NOT PREPROCESS, new_resources
    new_total_resources = (target_spmu.new_resources * target_spmu.spmwt).sum()
    change_total_resources = new_total_resources - original_total_resources
    change_pp = change_total_resources / population

    original_poverty_rate = return_demog("person", "pov_rate")

    original_poverty_gap = return_all_state("poverty_gap")

    original_child_poverty_rate = return_demog("child", "pov_rate")
    original_adult_poverty_rate = return_demog("adult", "pov_rate")
    original_pwd_poverty_rate = return_demog("pwd", "pov_rate")
    original_white_poverty_rate = return_demog("white_non_hispanic", "pov_rate")
    original_black_poverty_rate = return_demog("black", "pov_rate")
    original_hispanic_poverty_rate = return_demog("hispanic", "pov_rate")

    # define orignal gini coefficient
    original_gini = return_all_state("gini")

    # function to calculate rel difference between one number and another
    def change(new, old, round=3):
        return ((new - old) / old).round(round)

    # Calculate poverty gap
    target_spmu["new_poverty_gap"] = np.where(
        target_spmu.new_resources < target_spmu.spmthresh,
        target_spmu.spmthresh - target_spmu.new_resources,
        0,
    )
    poverty_gap = mdf.weighted_sum(target_spmu, "new_poverty_gap", "spmwt")
    poverty_gap_change = change(poverty_gap, original_poverty_gap)

    # Calculate the change in poverty rate
    target_persons["poor"] = target_persons.new_resources < target_persons.spmthresh
    total_poor = (target_persons.poor * target_persons.asecwt).sum()
    # TODO fix thism, the default  poverty rate is too high
    poverty_rate = total_poor / population
    poverty_rate_change = change(poverty_rate, original_poverty_rate)

    # Calculate change in Gini
    gini = mdf.gini(target_persons, "new_resources_per_person", "asecwt")
    gini_change = change(gini, original_gini, 3)

    # Calculate percent winners
    target_persons["winner"] = target_persons.new_resources > target_persons.spmtotres
    total_winners = (target_persons.winner * target_persons.asecwt).sum()
    percent_winners = (total_winners / population * 100).round(1)

    # Calculate the new poverty rate for each demographic
    def pv_rate(column):
        return mdf.weighted_mean(
            target_persons[target_persons[column]], "poor", "asecwt"
        )

    child_poverty_rate = pv_rate("child")
    adult_poverty_rate = pv_rate("adult")
    pwd_poverty_rate = pv_rate("pwd")
    white_poverty_rate = pv_rate("white_non_hispanic")
    black_poverty_rate = pv_rate("black")
    hispanic_poverty_rate = pv_rate("hispanic")

    # Calculate the percent change in poverty rate for each demographic
    child_poverty_rate_change = change(child_poverty_rate, original_child_poverty_rate)
    adult_poverty_rate_change = change(adult_poverty_rate, original_adult_poverty_rate)
    pwd_poverty_rate_change = change(pwd_poverty_rate, original_pwd_poverty_rate)
    white_poverty_rate_change = change(white_poverty_rate, original_white_poverty_rate)
    black_poverty_rate_change = change(black_poverty_rate, original_black_poverty_rate)
    hispanic_poverty_rate_change = change(
        hispanic_poverty_rate, original_hispanic_poverty_rate
    )

    # Round all numbers for display in hover
    def hover_string(metric, round_by=1):
        """formats 0.121 to 12.1%"""
        string = str(round(metric * 100, round_by))
        return string

    original_poverty_rate_string = hover_string(original_poverty_rate)
    poverty_rate_string = hover_string(poverty_rate)
    original_child_poverty_rate_string = hover_string(original_child_poverty_rate)
    child_poverty_rate_string = hover_string(child_poverty_rate)
    original_adult_poverty_rate_string = hover_string(original_adult_poverty_rate)
    adult_poverty_rate_string = hover_string(adult_poverty_rate)
    original_pwd_poverty_rate_string = hover_string(original_pwd_poverty_rate)
    pwd_poverty_rate_string = hover_string(pwd_poverty_rate)
    original_white_poverty_rate_string = hover_string(original_white_poverty_rate)
    white_poverty_rate_string = hover_string(white_poverty_rate)
    original_black_poverty_rate_string = hover_string(original_black_poverty_rate)
    black_poverty_rate_string = hover_string(black_poverty_rate)
    original_hispanic_poverty_rate_string = hover_string(original_hispanic_poverty_rate)
    hispanic_poverty_rate_string = hover_string(hispanic_poverty_rate)

    original_poverty_gap_billions = original_poverty_gap / 1e9
    original_poverty_gap_billions = int(original_poverty_gap_billions)
    original_poverty_gap_billions = "{:,}".format(original_poverty_gap_billions)

    poverty_gap_billions = poverty_gap / 1e9
    poverty_gap_billions = int(poverty_gap_billions)
    poverty_gap_billions = "{:,}".format(poverty_gap_billions)

    original_gini_string = str(round(original_gini, 3))
    gini_string = str(round(gini, 3))

    # Convert UBI and winners to string for title of chart
    ubi_string = str("{:,}".format(int(round(ubi / 12))))
    winners_string = str(percent_winners)
    change_pp = int(change_pp)
    change_pp = "{:,}".format(change_pp)
    resources_string = str(change_pp)

    ubi_line = "Monthly UBI: $" + ubi_string
    winners_line = "Percent better off: " + winners_string + "%"
    resources_line = "Average change in resources per person: $" + resources_string

    # Create x-axis labels for each chart
    x = ["Poverty rate", "Poverty gap", "Gini index"]
    x2 = [
        "Child",
        "Adult",
        "People<br>with<br>disabilities",
        "White",
        "Black",
        "Hispanic",
    ]
    econ_fig_cols = [poverty_rate_change, poverty_gap_change, gini_change]
    econ_fig = go.Figure(
        [
            go.Bar(
                x=x,
                y=econ_fig_cols,
                text=econ_fig_cols,
                hovertemplate=[
                    "Original poverty rate: "
                    + original_poverty_rate_string
                    + "%<br><extra></extra>"
                    "New poverty rate: " + poverty_rate_string + "%",
                    "Original poverty gap: $"
                    + original_poverty_gap_billions
                    + "B<br><extra></extra>"
                    "New poverty gap: $" + poverty_gap_billions + "B",
                    "Original Gini index: <extra></extra>"
                    + original_gini_string
                    + "<br>New Gini index: "
                    + gini_string,
                ],
                marker_color=BLUE,
            )
        ]
    )

    # Edit text and display the UBI amount and percent winners in title
    econ_fig.update_layout(
        uniformtext_minsize=10, uniformtext_mode="hide", plot_bgcolor="white"
    )
    econ_fig.update_traces(texttemplate="%{text:.1%f}", textposition="auto")
    econ_fig.update_layout(title_text="Economic overview", title_x=0.5)

    econ_fig.update_xaxes(
        tickangle=0, title_text="", tickfont={"size": 14}, title_standoff=25
    )

    econ_fig.update_yaxes(
        tickprefix="",
        tickfont={"size": 14},
        title_standoff=25,
    )

    econ_fig.update_layout(
        hoverlabel=dict(bgcolor="white", font_size=14, font_family="Roboto"),
        yaxis_tickformat="%",
    )

    econ_fig.update_xaxes(title_font=dict(size=14, family="Roboto", color="black"))
    econ_fig.update_yaxes(title_font=dict(size=14, family="Roboto", color="black"))

    breakdown_fig_cols = [
        child_poverty_rate_change,
        adult_poverty_rate_change,
        pwd_poverty_rate_change,
        white_poverty_rate_change,
        black_poverty_rate_change,
        hispanic_poverty_rate_change,
    ]

    breakdown_fig = go.Figure(
        [
            go.Bar(
                x=x2,
                y=breakdown_fig_cols,
                text=breakdown_fig_cols,
                hovertemplate=[
                    "Original child poverty rate: "
                    + original_child_poverty_rate_string
                    + "%<br><extra></extra>"
                    "New child poverty rate: " + child_poverty_rate_string + "%",
                    "Original adult poverty rate: "
                    + original_adult_poverty_rate_string
                    + "%<br><extra></extra>"
                    "New adult poverty rate: " + adult_poverty_rate_string + "%",
                    "Original pwd poverty rate: "
                    + original_pwd_poverty_rate_string
                    + "%<br><extra></extra>"
                    "New pwd poverty rate: " + pwd_poverty_rate_string + "%",
                    "Original White poverty rate: "
                    + original_white_poverty_rate_string
                    + "%<br><extra></extra>"
                    "New White poverty rate: " + white_poverty_rate_string + "%",
                    "Original Black poverty rate: "
                    + original_black_poverty_rate_string
                    + "%<br><extra></extra>"
                    "New Black poverty rate: " + black_poverty_rate_string + "%",
                    "Original Hispanic poverty rate: "
                    + original_hispanic_poverty_rate_string
                    + "%<br><extra></extra>"
                    "New Hispanic poverty rate: " + hispanic_poverty_rate_string + "%",
                ],
                marker_color=BLUE,
            )
        ]
    )

    breakdown_fig.update_layout(
        uniformtext_minsize=10, uniformtext_mode="hide", plot_bgcolor="white"
    )
    breakdown_fig.update_traces(texttemplate="%{text:.1%f}", textposition="auto")
    breakdown_fig.update_layout(title_text="Poverty rate breakdown", title_x=0.5)

    breakdown_fig.update_xaxes(
        tickangle=0, title_text="", tickfont={"size": 14}, title_standoff=25
    )

    breakdown_fig.update_yaxes(
        tickprefix="",
        tickfont={"size": 14},
        title_standoff=25,
    )

    breakdown_fig.update_layout(
        hoverlabel=dict(bgcolor="white", font_size=14, font_family="Roboto"),
        yaxis_tickformat="%",
    )

    breakdown_fig.update_xaxes(title_font=dict(size=14, family="Roboto", color="black"))
    breakdown_fig.update_yaxes(title_font=dict(size=14, family="Roboto", color="black"))

    return ubi_line, winners_line, resources_line, econ_fig, breakdown_fig


@app.callback(
    Output("include-checklist", "options"),
    Input("include-checklist", "value"),
)
def update(checklist):
    """[summary]
    prevent users from excluding both adults and children
    Parameters
    ----------
    checklist : list
        takes the input "include-checklist" from the callback

    Returns
    -------
    "Include in UBI" checklist with correct options
    """
    if "adults" not in checklist:
        return [
            {"label": "Non-Citizens", "value": "non_citizens"},
            {"label": "Children", "value": "children", "disabled": True},
            {"label": "Adults", "value": "adults"},
        ]
    elif "children" not in checklist:
        return [
            {"label": "Non-Citizens", "value": "non_citizens"},
            {"label": "Children", "value": "children"},
            {"label": "Adults", "value": "adults", "disabled": True},
        ]
    else:
        return [
            {"label": "Non-Citizens", "value": "non_citizens"},
            {"label": "Children", "value": "children"},
            {"label": "Adults", "value": "adults"},
        ]


@app.callback(
    Output("benefits-checklist", "options"),
    Input("level", "value"),
)
def update(radio):

    if "state" in radio:
        return [
            {"label": "  Child Tax Credit", "value": "ctc", "disabled": True},
            {
                "label": "  Supplemental Security Income (SSI)",
                "value": "incssi",
                "disabled": True,
            },
            {
                "label": "  SNAP (food stamps)",
                "value": "spmsnap",
                "disabled": True,
            },
            {
                "label": "  Earned Income Tax Credit",
                "value": "eitcred",
                "disabled": True,
            },
            {
                "label": "  Unemployment benefits",
                "value": "incunemp",
                "disabled": True,
            },
            {
                "label": "  Energy subsidy (LIHEAP)",
                "value": "spmheat",
                "disabled": True,
            },
        ]
    else:
        return [
            {"label": "  Child Tax Credit", "value": "ctc"},
            {
                "label": "  Supplemental Security Income (SSI)",
                "value": "incssi",
            },
            {"label": "  SNAP (food stamps)", "value": "spmsnap"},
            {"label": "  Earned Income Tax Credit", "value": "eitcred"},
            {"label": "  Unemployment benefits", "value": "incunemp"},
            {"label": "  Energy subsidy (LIHEAP)", "value": "spmheat"},
        ]


@app.callback(
    Output("taxes-checklist", "options"),
    Input("level", "value"),
)
def update(radio):

    if "state" in radio:
        return [
            {"label": "Income taxes", "value": "fedtaxac"},
            {
                "label": "Employee side payroll",
                "value": "fica",
                "disabled": True,
            },
        ]
    else:
        return [
            {"label": "Income taxes", "value": "fedtaxac"},
            {"label": "Employee side payroll", "value": "fica"},
        ]


if __name__ == "__main__":
    app.run_server(debug=True, port=8000, host="127.0.0.1")
