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

# Import data from Ipums
person_raw = pd.read_csv("cps_00041.csv.gz")

# Create copy and lower column names
person = person_raw.copy(deep=True)
person.columns = person.columns.str.lower()
person.asecwt /= 3

# Crate booleans for demographics
person["adult"] = person.age > 17
person["child"] = person.age < 18

person["black"] = person.race == 200
person["white_non_hispanic"] = (person.race == 100) & (person.hispan == 0)
person["hispanic"] = (person.hispan > 1) & person.hispan < 700
person["pwd"] = person.diffany == 2
person["non_citizen"] = person.citizen == 5
person["non_citizen_child"] = (person.citizen == 5) & (person.age < 18)
person["non_citizen_adult"] = (person.citizen == 5) & (person.age > 17)

# Remove NIUs
person["taxinc"].replace({9999999: 0}, inplace=True)
person["adjginc"].replace({99999999: 0}, inplace=True)
person["incss"].replace({999999: 0}, inplace=True)
person["incssi"].replace({999999: 0}, inplace=True)
person["incunemp"].replace({99999: 0}, inplace=True)
person["incunemp"].replace({999999: 0}, inplace=True)
person["ctccrd"].replace({999999: 0}, inplace=True)
person["actccrd"].replace({99999: 0}, inplace=True)
person["eitcred"].replace({9999: 0}, inplace=True)
person["fica"].replace({99999: 0}, inplace=True)
person["fedtaxac"].replace({99999999: 0}, inplace=True)
person["stataxac"].replace({9999999: 0}, inplace=True)

# Change fip codes to state names
person["statefip"] = person["statefip"].astype(str)
person["statefip"].replace(
    {
        "1": "Alabama",
        "2": "Alaska",
        "4": "Arizona",
        "5": "Arkansas",
        "6": "California",
        "8": "Colorado",
        "9": "Connecticut",
        "10": "Delaware",
        "11": "District of Columbia",
        "12": "Florida",
        "13": "Georgia",
        "15": "Hawaii",
        "16": "Idaho",
        "17": "Illinois",
        "18": "Indiana",
        "19": "Iowa",
        "20": "Kansas",
        "21": "Kentucky",
        "22": "Louisiana",
        "23": "Maine",
        "24": "Maryland",
        "25": "Massachusetts",
        "26": "Michigan",
        "27": "Minnesota",
        "28": "Mississippi",
        "29": "Missouri",
        "30": "Montana",
        "31": "Nebraska",
        "32": "Nevada",
        "33": "New Hampshire",
        "34": "New Jersey",
        "35": "New Mexico",
        "36": "New York",
        "37": "North Carolina",
        "38": "North Dakota",
        "39": "Ohio",
        "40": "Oklahoma",
        "41": "Oregon",
        "42": "Pennsylvania",
        "44": "Rhode Island",
        "45": "South Carolina",
        "46": "South Dakota",
        "47": "Tennessee",
        "48": "Texas",
        "49": "Utah",
        "50": "Vermont",
        "51": "Virginia",
        "53": "Washington",
        "54": "West Virginia",
        "55": "Wisconsin",
        "56": "Wyoming",
    },
    inplace=True,
)

# Aggregate deductible and refundable child tax credits
person["ctc"] = person.ctccrd + person.actccrd

# Calculate the number of people per smp unit
person["person"] = 1
spm = person.groupby(["spmfamunit", "year"])[["person"]].sum()
spm.columns = ["numper"]
person = person.merge(spm, left_on=["spmfamunit", "year"], right_index=True)

person["weighted_state_tax"] = person.asecwt * person.stataxac
person["weighted_agi"] = person.asecwt * person.adjginc

# Calculate the total taxable income and total people in each state
state_groups_taxinc = person.groupby(["statefip"])[
    ["weighted_state_tax", "weighted_agi"]
].sum()
state_groups_taxinc.columns = ["state_tax_revenue", "state_taxable_income"]
person = person.merge(
    state_groups_taxinc, left_on=["statefip"], right_index=True
)

# Create dataframe with aggregated spm unit data
PERSON_COLUMNS = [
    "adjginc",
    "fica",
    "fedtaxac",
    "ctc",
    "incssi",
    "incunemp",
    "eitcred",
    "child",
    "adult",
    "non_citizen",
    "non_citizen_child",
    "non_citizen_adult",
    "person",
    "stataxac",
]
SPMU_COLUMNS = [
    "spmheat",
    "spmsnap",
    "spmfamunit",
    "spmthresh",
    "spmtotres",
    "spmwt",
    "year",
    "statefip",
    "state_tax_revenue",
    "state_taxable_income",
]

spmu = person.groupby(SPMU_COLUMNS)[PERSON_COLUMNS].sum().reset_index()
spmu[["fica", "fedtaxac", "stataxac"]] *= -1
spmu.rename(columns={"person": "numper"}, inplace=True)

spmu.spmwt /= 3

# Colors
BLUE = "#1976D2"

states_no_us = person.statefip.unique().tolist()
states_no_us.sort()
states = ["US"] + states_no_us


def change(new, old):
    return ((new - old) / old * 100).round(2)


# Create the inputs card
cards = dbc.CardDeck(
    [
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
                            id="state-dropdown",
                            multi=False,
                            value="US",
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
        dbc.Card(
            [
                dbc.CardBody(
                    [
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
                            tooltip={
                                "always_visible": True,
                                "placement": "bottom",
                            },
                            marks={
                                0: {
                                    "label": "0%",
                                    "style": {"color": "#F8F8FF"},
                                },
                                10: {
                                    "label": "10%",
                                    "style": {"color": "#F8F8FF"},
                                },
                                20: {
                                    "label": "20%",
                                    "style": {"color": "#F8F8FF"},
                                },
                                30: {
                                    "label": "30%",
                                    "style": {"color": "#F8F8FF"},
                                },
                                40: {
                                    "label": "40%",
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
        dbc.Card(
            [
                dbc.CardBody(
                    [
                        html.Label(
                            ["Repeal Benefits:"],
                            style={
                                "font-weight": "bold",
                                "text-align": "center",
                                "color": "white",
                                "fontSize": 20,
                            },
                        ),
                        dcc.Checklist(
                            id="benefits-checklist",
                            options=[
                                {
                                    "label": "  Child Tax Credit",
                                    "value": "ctc",
                                },
                                {
                                    "label": "  Supplemental Security Income (SSI)",
                                    "value": "incssi",
                                },
                                {
                                    "label": "  Snap (food stamps)",
                                    "value": "spmsnap",
                                },
                                {
                                    "label": "  Earned Income Tax Credit",
                                    "value": "eitcred",
                                },
                                {
                                    "label": "  Unemployment",
                                    "value": "incunemp",
                                },
                                {
                                    "label": "  Energy Subsidy (LIHEAP)",
                                    "value": "spmheat",
                                },
                            ],
                            value=[],
                            labelStyle={"display": "block"},
                        ),
                    ]
                ),
            ],
            color="info",
            outline=False,
        ),
        dbc.Card(
            [
                dbc.CardBody(
                    [
                        html.Label(
                            ["Exclude from UBI:"],
                            style={
                                "font-weight": "bold",
                                "text-align": "center",
                                "color": "white",
                                "fontSize": 20,
                            },
                        ),
                        dcc.Checklist(
                            id="exclude-checklist",
                            options=[
                                {
                                    "label": "non-Citizens",
                                    "value": "non_citizens",
                                },
                                {"label": "Children", "value": "children"},
                                {"label": "Adult", "value": "adults"},
                            ],
                            value=[],
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
            dcc.Graph(id="my-graph", figure={}), body=True, color="info",
        ),
        dbc.Card(
            dcc.Graph(id="my-graph2", figure={}), body=True, color="info",
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
                    href="https://www.ubicenter.org", target="blank"
                ),
                dbc.NavbarToggler(id="navbar-toggler"),
            ]
        ),
        # Row 1 - header
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
                        "The results of your reform:",
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
    Input(component_id="exclude-checklist", component_property="value"),
)
def ubi(statefip, level, agi_tax, benefits, taxes, exclude):

    if level == "federal":
        # combine lists and initialize
        taxes_benefits = taxes + benefits
        spmu["new_resources"] = spmu.spmtotres
        revenue = 0

        # Calculate the new revenue and spmu resources from tax and benefit change
        for tax_benefit in taxes_benefits:
            spmu.new_resources -= spmu[tax_benefit]
            revenue += mdf.weighted_sum(spmu, tax_benefit, "spmwt")

        if ("fedtaxac" in taxes_benefits) & ("ctc" in taxes_benefits):
            spmu.new_resources += spmu.ctc
            revenue -= mdf.weighted_sum(spmu, "ctc", "spmwt")

        if ("fedtaxac" in taxes_benefits) & ("eitcred" in taxes_benefits):
            spmu.new_resources += spmu.eitcred
            revenue -= mdf.weighted_sum(spmu, "eitcred", "spmwt")

        # Calculate the new taxes from flat tax on AGI
        tax_rate = agi_tax / 100
        spmu["new_taxes"] = np.maximum(spmu.adjginc, 0) * tax_rate

        spmu.new_resources -= spmu.new_taxes
        revenue += mdf.weighted_sum(spmu, "new_taxes", "spmwt")

        # Calculate the total UBI a spmu recieves based on exclusions
        spmu["numper_ubi"] = spmu.numper

        if "children" in exclude:
            spmu["numper_ubi"] -= spmu.child

        if "non_citizens" in exclude:
            spmu["numper_ubi"] -= spmu.non_citizen

        if ("children" in exclude) and ("non_citizens" in exclude):
            spmu["numper_ubi"] += spmu.non_citizen_child

        if "adults" in exclude:
            spmu["numper_ubi"] -= spmu.adult

        if ("adults" in exclude) and ("non_citizens" in exclude):
            spmu["numper_ubi"] += spmu.non_citizen_adult

        # Assign UBI
        ubi_population = (spmu.numper_ubi * spmu.spmwt).sum()
        ubi = revenue / ubi_population
        spmu["total_ubi"] = ubi * spmu.numper_ubi

        # Calculate change in resources
        spmu.new_resources += spmu.total_ubi
        spmu["new_resources_per_person"] = spmu.new_resources / spmu.numper
        # Sort by state
        if statefip == "US":
            target_spmu = spmu.copy(deep=True)
        else:
            target_spmu = spmu[spmu.statefip == statefip].copy(deep=True)

    if level == "state":

        # Sort by state
        if statefip == "US":
            target_spmu = spmu.copy(deep=True)
        else:
            target_spmu = spmu[spmu.statefip == statefip].copy(deep=True)

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

        if "children" in exclude:
            target_spmu["numper_ubi"] -= target_spmu.child

        if "non_citizens" in exclude:
            target_spmu["numper_ubi"] -= target_spmu.non_citizen

        if ("children" in exclude) and ("non_citizens" in exclude):
            target_spmu["numper_ubi"] += target_spmu.non_citizen_child

        if "adults" in exclude:
            target_spmu["numper_ubi"] -= target_spmu.adult

        if ("adults" in exclude) and ("non_citizens" in exclude):
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

    # Merge and create target_persons
    sub_spmu = target_spmu[
        ["spmfamunit", "year", "new_resources", "new_resources_per_person"]
    ]
    target_persons = person.merge(sub_spmu, on=["spmfamunit", "year"])

    # Calculate populations
    population = target_persons.asecwt.sum()
    child_population = (target_persons.child * target_persons.asecwt).sum()
    non_citizen_population = (
        target_persons.non_citizen * target_persons.asecwt
    ).sum()
    non_citizen_child_population = (
        target_persons.non_citizen_child * target_persons.asecwt
    ).sum()

    # Calculate total change in resources
    original_total_resources = (
        target_spmu.spmtotres * target_spmu.spmwt
    ).sum()
    new_total_resources = (target_spmu.new_resources * target_spmu.spmwt).sum()
    change_total_resources = new_total_resources - original_total_resources
    change_pp = change_total_resources / population

    # Determine people originally in poverty
    target_persons["original_poor"] = (
        target_persons.spmtotres < target_persons.spmthresh
    )

    # Calculate original poverty rate
    original_total_poor = (
        target_persons.original_poor * target_persons.asecwt
    ).sum()
    original_poverty_rate = (original_total_poor / population) * 100

    # Calculate the original poverty gap
    target_spmu["poverty_gap"] = np.where(
        target_spmu.spmtotres < target_spmu.spmthresh,
        target_spmu.spmthresh - target_spmu.spmtotres,
        0,
    )

    original_poverty_gap = mdf.weighted_sum(
        target_spmu, "poverty_gap", "spmwt"
    )

    # Calculate the orginal demographic poverty rates
    def pov_rate(column):
        return (
            mdf.weighted_mean(
                target_persons[target_persons[column]],
                "original_poor",
                "asecwt",
            )
            * 100
        )

    original_child_poverty_rate = pov_rate("child")
    original_adult_poverty_rate = pov_rate("adult")
    original_pwd_poverty_rate = pov_rate("pwd")
    original_white_poverty_rate = pov_rate("white_non_hispanic")
    original_black_poverty_rate = pov_rate("black")
    original_hispanic_poverty_rate = pov_rate("hispanic")

    # Caluclate original gini
    target_persons["spm_resources_per_person"] = (
        target_persons.spmtotres / target_persons.numper
    )
    original_gini = mdf.gini(
        target_persons, "spm_resources_per_person", "asecwt"
    )

    # Calculate poverty gap
    target_spmu["new_poverty_gap"] = np.where(
        target_spmu.new_resources < target_spmu.spmthresh,
        target_spmu.spmthresh - target_spmu.new_resources,
        0,
    )
    poverty_gap = mdf.weighted_sum(target_spmu, "new_poverty_gap", "spmwt")
    poverty_gap_change = (
        (poverty_gap - original_poverty_gap) / original_poverty_gap * 100
    ).round(1)

    # Calculate the change in poverty rate
    target_persons["poor"] = (
        target_persons.new_resources < target_persons.spmthresh
    )
    total_poor = (target_persons.poor * target_persons.asecwt).sum()
    poverty_rate = (total_poor / population) * 100
    poverty_rate_change = (
        (poverty_rate - original_poverty_rate) / original_poverty_rate * 100
    ).round(1)

    # Calculate change in Gini
    gini = mdf.gini(target_persons, "new_resources_per_person", "asecwt")
    gini_change = ((gini - original_gini) / original_gini * 100).round(1)

    # Calculate percent winners
    target_persons["winner"] = (
        target_persons.new_resources > target_persons.spmtotres
    )
    total_winners = (target_persons.winner * target_persons.asecwt).sum()
    percent_winners = (total_winners / population * 100).round(1)

    # Calculate the new poverty rate for each demographic
    def pv_rate(column):
        return (
            mdf.weighted_mean(
                target_persons[target_persons[column]], "poor", "asecwt"
            )
            * 100
        )

    child_poverty_rate = pv_rate("child")
    adult_poverty_rate = pv_rate("adult")
    pwd_poverty_rate = pv_rate("pwd")
    white_poverty_rate = pv_rate("white_non_hispanic")
    black_poverty_rate = pv_rate("black")
    hispanic_poverty_rate = pv_rate("hispanic")

    # Calculate the percent change in poverty rate for each demographic
    child_poverty_rate_change = (
        (child_poverty_rate - original_child_poverty_rate)
        / original_child_poverty_rate
        * 100
    ).round(1)
    adult_poverty_rate_change = (
        (adult_poverty_rate - original_adult_poverty_rate)
        / original_adult_poverty_rate
        * 100
    ).round(1)
    pwd_poverty_rate_change = (
        (pwd_poverty_rate - original_pwd_poverty_rate)
        / original_pwd_poverty_rate
        * 100
    ).round(1)
    white_poverty_rate_change = (
        (white_poverty_rate - original_white_poverty_rate)
        / original_white_poverty_rate
        * 100
    ).round(1)
    black_poverty_rate_change = (
        (black_poverty_rate - original_black_poverty_rate)
        / original_black_poverty_rate
        * 100
    ).round(1)
    hispanic_poverty_rate_change = (
        (hispanic_poverty_rate - original_hispanic_poverty_rate)
        / original_hispanic_poverty_rate
        * 100
    ).round(1)

    # Round all numbers for display in hover
    original_poverty_rate_string = str(round(original_poverty_rate, 1))
    poverty_rate_string = str(round(poverty_rate, 1))
    original_child_poverty_rate_string = str(
        round(original_child_poverty_rate, 1)
    )
    child_poverty_rate_string = str(round(child_poverty_rate, 1))
    original_adult_poverty_rate_string = str(
        round(original_adult_poverty_rate, 1)
    )
    adult_poverty_rate_string = str(round(adult_poverty_rate, 1))
    original_pwd_poverty_rate_string = str(round(original_pwd_poverty_rate, 1))
    pwd_poverty_rate_string = str(round(pwd_poverty_rate, 1))
    original_white_poverty_rate_string = str(
        round(original_white_poverty_rate, 1)
    )
    white_poverty_rate_string = str(round(white_poverty_rate, 1))
    original_black_poverty_rate_string = str(
        round(original_black_poverty_rate, 1)
    )
    black_poverty_rate_string = str(round(black_poverty_rate, 1))
    original_hispanic_poverty_rate_string = str(
        round(original_hispanic_poverty_rate, 1)
    )
    hispanic_poverty_rate_string = str(round(hispanic_poverty_rate, 1))

    original_poverty_gap_billions = original_poverty_gap / 1e9
    original_poverty_gap_billions = int(original_poverty_gap_billions)
    original_poverty_gap_billions = "{:,}".format(
        original_poverty_gap_billions
    )

    poverty_gap_billions = poverty_gap / 1e9
    poverty_gap_billions = int(poverty_gap_billions)
    poverty_gap_billions = "{:,}".format(poverty_gap_billions)

    original_gini_string = str(round(original_gini, 3))
    gini_string = str(round(gini, 3))

    # Convert UBI and winners to string for title of chart
    ubi_int = int(ubi)
    ubi_int = "{:,}".format(ubi_int)
    ubi_string = str(ubi_int)
    winners_string = str(percent_winners)
    change_pp = int(change_pp)
    change_pp = "{:,}".format(change_pp)
    resources_string = str(change_pp)

    ubi_line = "UBI amount: $" + ubi_string
    winners_line = "Percent better off: " + winners_string + "%"
    resources_line = (
        "Average change in resources per person: $" + resources_string
    )

    # Create x-axis labels for each chart
    x = ["Poverty Rate", "Poverty Gap", "Inequality (Gini)"]
    x2 = [
        "Child",
        "Adult",
        "People<br>with<br>disabilities",
        "White",
        "Black",
        "Hispanic",
    ]

    fig = go.Figure(
        [
            go.Bar(
                x=x,
                y=[poverty_rate_change, poverty_gap_change, gini_change],
                text=[poverty_rate_change, poverty_gap_change, gini_change],
                hovertemplate=[
                    "Original poverty rate: "
                    + original_poverty_rate_string
                    + "%<br><extra></extra>"
                    "New poverty rate: " + poverty_rate_string + "%",
                    "Original poverty gap: $"
                    + original_poverty_gap_billions
                    + "B<br><extra></extra>"
                    "New poverty gap: $" + poverty_gap_billions + "B",
                    "Original gini: <extra></extra>"
                    + original_gini_string
                    + "<br>New gini: "
                    + gini_string,
                ],
                marker_color=BLUE,
            )
        ]
    )

    # Edit text and display the UBI amount and percent winners in title
    fig.update_layout(
        uniformtext_minsize=10, uniformtext_mode="hide", plot_bgcolor="white"
    )
    fig.update_traces(texttemplate="%{text}%", textposition="auto")
    fig.update_layout(title_text="Economic overview", title_x=0.5)

    fig.update_xaxes(
        tickangle=0, title_text="", tickfont={"size": 14}, title_standoff=25
    )

    fig.update_yaxes(
        # title_text = "Percent change",
        ticksuffix="%",
        tickprefix="",
        tickfont={"size": 14},
        title_standoff=25,
    )

    fig.update_layout(
        hoverlabel=dict(bgcolor="white", font_size=14, font_family="Roboto")
    )

    fig.update_xaxes(title_font=dict(size=14, family="Roboto", color="black"))
    fig.update_yaxes(title_font=dict(size=14, family="Roboto", color="black"))

    fig2 = go.Figure(
        [
            go.Bar(
                x=x2,
                y=[
                    child_poverty_rate_change,
                    adult_poverty_rate_change,
                    pwd_poverty_rate_change,
                    white_poverty_rate_change,
                    black_poverty_rate_change,
                    hispanic_poverty_rate_change,
                ],
                text=[
                    child_poverty_rate_change,
                    adult_poverty_rate_change,
                    pwd_poverty_rate_change,
                    white_poverty_rate_change,
                    black_poverty_rate_change,
                    hispanic_poverty_rate_change,
                ],
                hovertemplate=[
                    "Original child poverty rate: "
                    + original_child_poverty_rate_string
                    + "%<br><extra></extra>"
                    "New child poverty rate: "
                    + child_poverty_rate_string
                    + "%",
                    "Original adult poverty rate: "
                    + original_adult_poverty_rate_string
                    + "%<br><extra></extra>"
                    "New adult poverty rate: "
                    + adult_poverty_rate_string
                    + "%",
                    "Original pwd poverty rate: "
                    + original_pwd_poverty_rate_string
                    + "%<br><extra></extra>"
                    "New pwd poverty rate: " + pwd_poverty_rate_string + "%",
                    "Original White poverty rate: "
                    + original_white_poverty_rate_string
                    + "%<br><extra></extra>"
                    "New White poverty rate: "
                    + white_poverty_rate_string
                    + "%",
                    "Original Black poverty rate: "
                    + original_black_poverty_rate_string
                    + "%<br><extra></extra>"
                    "New Black poverty rate: "
                    + black_poverty_rate_string
                    + "%",
                    "Original Hispanic poverty rate: "
                    + original_hispanic_poverty_rate_string
                    + "%<br><extra></extra>"
                    "New Hispanic poverty rate: "
                    + hispanic_poverty_rate_string
                    + "%",
                ],
                marker_color=BLUE,
            )
        ]
    )

    fig2.update_layout(
        uniformtext_minsize=10, uniformtext_mode="hide", plot_bgcolor="white"
    )
    fig2.update_traces(texttemplate="%{text}%", textposition="auto")
    fig2.update_layout(title_text="Poverty rate breakdown", title_x=0.5)

    fig2.update_xaxes(
        tickangle=0, title_text="", tickfont={"size": 14}, title_standoff=25
    )

    fig2.update_yaxes(
        # title_text = "Percent change",
        ticksuffix="%",
        tickprefix="",
        tickfont={"size": 14},
        title_standoff=25,
    )

    fig2.update_layout(
        hoverlabel=dict(bgcolor="white", font_size=14, font_family="Roboto")
    )

    fig2.update_xaxes(title_font=dict(size=14, family="Roboto", color="black"))
    fig2.update_yaxes(title_font=dict(size=14, family="Roboto", color="black"))

    return ubi_line, winners_line, resources_line, fig, fig2


@app.callback(
    Output("exclude-checklist", "options"),
    Input("exclude-checklist", "value"),
)
def update(checklist):

    if "adults" in checklist:
        return [
            {"label": "non-Citizens", "value": "non_citizens"},
            {"label": "Children", "value": "children", "disabled": True},
            {"label": "Adults", "value": "adults"},
        ]
    elif "children" in checklist:
        return [
            {"label": "non-Citizens", "value": "non_citizens"},
            {"label": "Children", "value": "children"},
            {"label": "Adults", "value": "adults", "disabled": True},
        ]
    else:
        return [
            {"label": "non-Citizens", "value": "non_citizens"},
            {"label": "Children", "value": "children"},
            {"label": "Adults", "value": "adults"},
        ]


@app.callback(
    Output("benefits-checklist", "options"), Input("level", "value"),
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
                "label": "  Snap (food stamps)",
                "value": "spmsnap",
                "disabled": True,
            },
            {
                "label": "  Earned Income Tax Credit",
                "value": "eitcred",
                "disabled": True,
            },
            {"label": "  Unemployment", "value": "incunemp", "disabled": True},
            {
                "label": "  Energy Subsidy (LIHEAP)",
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
            {"label": "  Snap (food stamps)", "value": "spmsnap"},
            {"label": "  Earned Income Tax Credit", "value": "eitcred"},
            {"label": "  Unemployment", "value": "incunemp"},
            {"label": "  Energy Subsidy (LIHEAP)", "value": "spmheat"},
        ]


@app.callback(
    Output("taxes-checklist", "options"), Input("level", "value"),
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

