# if kernel crashes, make sure pywin32 and pipywin32 are installed.
# Followed instructions here: https://github.com/jupyter/notebook/issues/4909
# import win32api

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
person_raw = pd.read_csv("cps_00041.csv.gz")

# Create copy and lower column names
person = person_raw.copy(deep=True)
person.columns = person.columns.str.lower()
person.asecwt /= 3

# Create booleans for demographics
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
person["statefip"]=person["statefip"].astype(str)
person["statefip"]=person["statefip"].apply(lambda x: us.states.lookup(x))
person["statefip"]=person["statefip"].astype('str')

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

spmu = person.groupby(SPMU_COLUMNS, observed=False)[PERSON_COLUMNS].sum().reset_index()
spmu[["fica", "fedtaxac", "stataxac"]] *= -1
spmu.rename(columns={"person": "numper"}, inplace=True)

spmu.spmwt /= 3

# write pre-processed dfs to csv files
person.to_csv("person.csv.gz", compression="gzip")
spmu.to_csv("spmu.csv.gz", compression="gzip")
