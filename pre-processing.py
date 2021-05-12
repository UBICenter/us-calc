# if kernel crashes, make sure pywin32 and pipywin32 are installed.
# Followed instructions here: https://github.com/jupyter/notebook/issues/4909
# import win32api

import pandas as pd
import numpy as np
import microdf as mdf
import os
import us

# Import data from Ipums
person = pd.read_csv("cps_00041.csv.gz")
# lower column names
person.columns = person.columns.str.lower()
# Divide by three for three years of data.
person[["asecwt", "spmwt"]] /= 3

# Create booleans for demographics
person["adult"] = person.age >= 18
person["child"] = person.age < 18

person["black"] = person.race == 200
person["white_non_hispanic"] = (person.race == 100) & (person.hispan == 0)
person["hispanic"] = person.hispan.between(1, 699)
person["pwd"] = person.diffany == 2
person["non_citizen"] = person.citizen == 5
person["non_citizen_child"] = (person.citizen == 5) & person.child
person["non_citizen_adult"] = (person.citizen == 5) & person.adult

# Remove NIUs
person["adjginc"].replace({99999999: 0}, inplace=True)
person["fedtaxac"].replace({99999999: 0}, inplace=True)
person["taxinc"].replace({9999999: 0}, inplace=True)
person["stataxac"].replace({9999999: 0}, inplace=True)
person["incss"].replace({999999: 0}, inplace=True)
person["incunemp"].replace({999999: 0}, inplace=True)
person["incssi"].replace({999999: 0}, inplace=True)
person["ctccrd"].replace({999999: 0}, inplace=True)
person["incunemp"].replace({99999: 0}, inplace=True)
person["actccrd"].replace({99999: 0}, inplace=True)
person["fica"].replace({99999: 0}, inplace=True)
person["eitcred"].replace({9999: 0}, inplace=True)

# Change fip codes to state names
person["state"] = (
    person["statefip"].astype(str)
    # pad leading zero or wrong number of states
    .apply("{:0>2}".format)
    # lookup full state name from fips code
    .apply(lambda x: us.states.lookup(x))
    # change us package formatting to string
    .astype(str)
)

# drop original statefip column from dataframe
person.drop(columns=["statefip"], inplace=True)

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
state_groups_taxinc = person.groupby(["state"])[
    ["weighted_state_tax", "weighted_agi"]
].sum()
state_groups_taxinc.columns = ["state_tax_revenue", "state_taxable_income"]
person = person.merge(state_groups_taxinc, left_on=["state"], right_index=True)

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
    "state",
    "state_tax_revenue",
    "state_taxable_income",
]

spmu = person.groupby(SPMU_COLUMNS, observed=False)[PERSON_COLUMNS].sum().reset_index()
spmu[["fica", "fedtaxac", "stataxac"]] *= -1
spmu.rename(columns={"person": "numper"}, inplace=True)

# write pre-processed dfs to csv files
person.to_csv("person.csv.gz", compression="gzip")
spmu.to_csv("spmu.csv.gz", compression="gzip")

# create boolean column for individual's poverty status, 1=poor
person["poor"] = person.spmthresh > person.spmtotres

# create a column for all selected demographic variables
# that will be used to calculate poverty rates
demog_cols = [
    "person",
    "adult",
    "child",
    "black",
    "white_non_hispanic",
    "hispanic",
    "pwd",
    "non_citizen",
    "non_citizen_adult",
    "non_citizen_child",
]

poor_pop = person[person.poor]

# calculate weighted sum of people living in poverty
mdf.weighted_sum(poor_pop, demog_cols, "asecwt")
# calculate poverty RATE for each DEMOGRAPHIC in US
pov_rate_us = mdf.weighted_sum(poor_pop, demog_cols, "asecwt") / mdf.weighted_sum(
    person, demog_cols, w="asecwt"
)
# add name to series
pov_rate_us.name = "US"
# calculate poverty RATE for each group by state
pov_rates = mdf.weighted_sum(
    poor_pop, demog_cols, "asecwt", groupby="state"
) / mdf.weighted_sum(person, demog_cols, w="asecwt", groupby="state")

# append US statistics as additional 'state'
pov_df = pov_rates.append(pov_rate_us)

# melt df from wide to long format
pov_df = pov_df.melt(ignore_index=False, var_name="demog")
# insert column indicating metric in question
pov_df.insert(loc=1, column="metric", value="pov_rate")


##
# calculate POPULATION for each DEMOGRAPHIC in US
pop_us = mdf.weighted_sum(person, demog_cols, w="asecwt")
# add name to series
pop_us.name = "US"
# calculate POPULATION for each group by state
pop_states = mdf.weighted_sum(person, demog_cols, w="asecwt", groupby="state")
# append US statistics as additional 'state'
pop_df = pop_states.append(pop_us)
# melt df from wide to long format
pop_df = pop_df.melt(ignore_index=False, var_name="demog")
pop_df.insert(loc=1, column="metric", value="pop")

# concat poverty and population dfs
demog_stats = pd.concat([pov_df, pop_df])
# write to csv file
demog_stats.to_csv("demog_stats.csv.gz", compression="gzip")

# Caluclate original gini
person["spm_resources_per_person"] = person.spmtotres / person.numper
# Caluclate original gini for US
gini_us = pd.Series(mdf.gini(df=person, col="spm_resources_per_person", w="asecwt"))
# add name to series
gini_us.index = ["US"]


# calculate gini for each group by state
gini_states = mdf.gini(
    df=person, col="spm_resources_per_person", w="asecwt", groupby="state"
)

# append US statistics as additional 'state'
gini_ser = gini_states.append(gini_us)
gini_ser.name = "gini"

# Calculate the original poverty gap
spmu["poverty_gap"] = np.where(
    spmu.spmtotres < spmu.spmthresh,
    spmu.spmthresh - spmu.spmtotres,
    0,
)
poverty_gap_us = pd.Series(mdf.weighted_sum(spmu, "poverty_gap", w="spmwt"))
# add name to series
poverty_gap_us.index = ["US"]
# calculate gini for each group by state
poverty_gap_states = mdf.weighted_sum(spmu, "poverty_gap", w="spmwt", groupby="state")
# append US statistics as additional 'state'
poverty_gap_ser = poverty_gap_states.append(poverty_gap_us)
poverty_gap_ser.name = "poverty_gap"

# calculate the sum total of everyone's resources in US
total_resources_us = pd.Series(mdf.weighted_sum(spmu, "spmtotres", w="spmwt"))
# add name to series
total_resources_us.index = ["US"]
# calculate gini for each group by state
total_resources_state = mdf.weighted_sum(
    df=spmu, col="spmtotres", w="spmwt", groupby="state"
)
# append US statistics as additional 'state'
total_resources_state = total_resources_state.append(total_resources_us)
total_resources_state.name = "total_resources"

# merge "total_resources","gini","poverty gap" into 1 df
all_state_stats = poverty_gap_ser.to_frame().join(total_resources_state.to_frame())
    gini_ser.to_frame(), left_index=True, right_index=True
)
all_state_stats = all_state_stats.merge(
    total_resources_state.to_frame(), left_index=True, right_index=True
)


all_state_stats.to_csv("all_state_stats.csv.gz", compression="gzip")
