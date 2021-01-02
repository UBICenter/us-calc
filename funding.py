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

# Import data from Ipums
person_raw = pd.read_csv('https://github.com/UBICenter/us-calc/raw/main/cps_00035.csv.gz')

# Create copy and lower column names
person = person_raw.copy(deep=True)
person.columns = person.columns.str.lower()

# Crate booleans for demographics
person['adult'] = person.age > 17
person['child'] = person.age < 18

person['black'] = person.race == 200
person['white_non_hispanic'] = ((person.race == 100) & (person.hispan == 000))
person['hispanic'] = ((person.hispan > 1) & person.hispan < 700)
person['pwd'] = person.diffany == 2
person['non_citizen'] = person.citizen == 5

# Remove NIUs
person['taxinc'].replace({9999999: 0}, inplace=True)
person['adjginc'].replace({99999999: 0}, inplace=True)
person['incss'].replace({999999: 0}, inplace=True)
person['incssi'].replace({999999: 0}, inplace=True)
person['incunemp'].replace({99999: 0}, inplace=True)
person['incunemp'].replace({999999: 0}, inplace=True)
person['ctccrd'].replace({999999: 0}, inplace=True)
person['actccrd'].replace({99999: 0}, inplace=True)
person['eitcred'].replace({9999: 0}, inplace=True)
person['fica'].replace({99999: 0}, inplace=True)
person['fedtaxac'].replace({99999999: 0}, inplace=True)

# Aggregate deductible and refundable child tax credits
person['ctc'] = person.ctccrd + person.actccrd

# Determine people originally in poverty
person['original_poor'] = person.spmtotres < person.spmthresh

# Calculate the number of people per smp unit
person['person'] = 1
person['person'] = 1
spm = person.groupby(['spmfamunit'])[['person']].sum()
spm.columns = ['numper']
person = person.merge(spm,left_on=['spmfamunit'],
                      right_index=True)

# Calculate populations
population = person.asecwt.sum()
child_population = (person.child * person.asecwt)
non_citizen_population = (person.non_citizen * person.asecwt)

# Calculate orginal poverty rate
original_total_poor = (person.original_poor * person.asecwt).sum()
original_poverty_rate = (original_total_poor / population) * 100

# Create dataframe with aggregated spm unit data
PERSON_COLUMNS = ['adjginc', 'fica','fedtaxac', 'ctc', 'incssi', 'incunemp', 'eitcred', 'child', 'non_citizen', 'person']
SPMU_COLUMNS = ['spmheat', 'spmsnap', 'spmfamunit', 'spmthresh', 'spmtotres']

spmu = person.groupby(SPMU_COLUMNS)[PERSON_COLUMNS].sum().reset_index()
spmu[['fica','fedtaxac']] *= -1
spmu.rename(columns={'person':'numper'}, inplace=True)

sub_person = person[['spmfamunit', 'spmwt']]
spmu = spmu.merge(sub_person, on=['spmfamunit'])

# Calculate the original poverty gap
spmu['poverty_gap'] = np.where(spmu.spmtotres < spmu.spmthresh, 
                              spmu.spmthresh - spmu.spmtotres, 0)

original_poverty_gap = mdf.weighted_sum(spmu, 'poverty_gap', 'spmwt')

# Calculate the orginal demographic poverty rates
def pov_rate(column):
    return mdf.weighted_mean(person[person[column]], 'original_poor', 'asecwt') * 100

original_child_poverty_rate = pov_rate('child')
original_adult_poverty_rate = pov_rate('adult')
original_pwd_poverty_rate = pov_rate('pwd')
original_white_poverty_rate = pov_rate('white_non_hispanic')
original_black_poverty_rate = pov_rate('black')
original_hispanic_poverty_rate = pov_rate('hispanic')

# Caluclate original gini
person['spm_resources_per_person'] = person.spmtotres / person.numper
gini = (mdf.gini(person, 'spm_resources_per_person' , 'asecwt'))

# Create the inputs card
card_main = dbc.Card(
    [
        dbc.CardBody(
            [
                html.H3("Select Funding", style={'text-align': 'center',
                                              'color': 'white'},
                        className="card-title"),
                html.Br(),
                html.Label(['Repeal Benefits:'],style={'font-weight': 'bold',
                                                            "text-align": "center",
                                                            "color": 'white',
                                                            'fontSize':20}),
                dcc.Checklist(id='my-checklist',
                                options=[
                                    {'label': '  Child Tax Credit', 'value': 'ctc'},
                                    {'label': '  Supplemental Security Income (SSI)', 'value': 'ssi'},
                                    {'label': '  Snap (food stamps)', 'value': 'snap'},
                                    {'label': '  Earned Income Tax Credit', 'value': 'eitc'},
                                    {'label': '  Unemployment', 'value': 'unemp'},
                                    {'label': '  Energy Subsidy (LIHEAP)', 'value': 'energy'}
                                    
                                ],
                                value=[],
                              labelStyle={'display': 'block'}
                            ),
                html.Br(),
                html.Label(['Repeal current taxes:'],style={'font-weight': 'bold',
                                                            "text-align": "center",
                                                             "color":"white",
                                                            'fontSize':20}),
                
                html.Br(),
                dcc.Checklist(id='my-checklist2',
                                options=[
                                    {'label': 'Income taxes', 'value': 'income_taxes'},
                                    {'label': 'Employee side payroll', 'value': 'fica'},
                                ],
                                value=[],
                              labelStyle={'display': 'block'}
                            ),
                
                 html.Br(),
                
                html.Label(['Add flat tax on AGI:'],style={'font-weight': 'bold',
                                                            "text-align": "center",
                                                             "color":"white",
                                                            'fontSize':20}),
                
                dcc.Slider(
                            id='agi-slider',
                            min=0,
                            max=50,
                            step=1,
                            value=0,
                            tooltip = { 'always_visible': True, 'placement': 'bottom'},
                            marks={0: {'label': '0%', 'style': {'color': '#F8F8FF'}},
                                   10: {'label': '10%', 'style': {'color': '#F8F8FF'}},
                                   20: {'label': '20%', 'style': {'color': '#F8F8FF'}},
                                   30: {'label': '30%', 'style': {'color': '#F8F8FF'}},
                                   40: {'label': '40%', 'style': {'color': '#F8F8FF'}},
                                   50: {'label': '50%', 'style': {'color': '#F8F8FF'}},
                                      }
                        ),
                        html.Div(id='slider-output-container'),
                                html.Br(),
                html.Label(['Exclude from UBI:'],style={'font-weight': 'bold',
                                                            "text-align": "center",
                                                             "color":"white",
                                                            'fontSize':20}),
                dcc.Checklist(id='my-checklist3',
                                options=[
                                    {'label': 'non-Citizens', 'value': 'non_citizens'},
                                    {'label': 'Children', 'value': 'children'},
                                ],
                                value=[],
                              labelStyle={'display': 'block'}
                            ),
                html.Br(),
                
            ]
        ),
    ],
    color="info",   
    outline=False,
)

# Create the summary figure output card
card_graph = dbc.Card(
        dcc.Graph(id='my-graph',
              figure={}), body=True, color="info",
)

# Create the poverty breakdown figure output card
card_graph2 = dbc.Card(
        dcc.Graph(id='my-graph2',
              figure={}), body=True, color="info",
)

app = dash.Dash(__name__,
                external_stylesheets=[dbc.themes.FLATLY])

server = app.server

# Design the app
app.layout = html.Div([
        # Row 1 - header
        dbc.Row(
            [
        dbc.Col(html.A([
        html.Img(src="https://blog.ubicenter.org/_static/ubi_center_logo_wide_blue.png", style={'height':'60%', 'width':'60%'})
        ], href='https://www.ubicenter.org/'),width=2)]),
        html.Br(),
        dbc.Row(
            [
            dbc.Col(html.H1("Explore funding mechanisms of UBI",
            style={'text-align': 'center', 'color': '#1976D2', 'fontSize': 50}),
                        width={'size': 8, 'offset': 2},
                        ),
            ]),
        html.Br(),
        html.Br(),
        dbc.Row(
            [
            dbc.Col(html.H4("Use the interactive below to explore different funding mechanisms for a UBI and their impact. You may choose between repealing benefits or adding new taxes.  When a benefit is repealed or a new tax is added, the new revenue automatically funds a UBI to all people equally to ensure each plan is budget neutral.",
            style={'text-align': 'left', 'color': 'black', 'fontSize': 25}),
                        width={'size': 8, 'offset': 2},
                        ),
            ]),
        html.Br(),
        html.Br(),
        dbc.Row([
            dbc.Col(card_main, width=3),
             dbc.Col(card_graph, width=6.8)],justify="around"),
        html.Br(),
        html.Br(),
        dbc.Row(
            dbc.Col(card_graph2, width={'size': 6, 'offset': 5}), justify="around"),
    html.Br(),
    html.Br(),
    html.Br(),
    html.Br(),
])

# Assign callbacks
@app.callback(
    Output(component_id='my-graph', component_property='figure'),
    Output(component_id='my-graph2', component_property='figure'),
    Input(component_id='agi-slider', component_property='value'),
    Input(component_id='my-checklist', component_property='value'),
    Input(component_id='my-checklist2', component_property='value'),
    Input(component_id='my-checklist3', component_property='value')
)
def ubi(agi_tax, benefits, taxes, exclude):
    
    # combine lists and initialize
    taxes_benefits = taxes + benefits
    spmu['new_resources'] = spmu.spmtotres
    revenue = 0
    
    # Calculate the new revenue and spmu resources from tax and benefit change
    for tax_benefit in taxes_benefits:
        if not ('fedtaxac' in taxes_benefits) and (tax_benefit in ['eitc', 'ctc']):
            spmu.new_resources -= spmu[tax_benefit]
            revenue += mdf.weighted_sum(spmu, 'tax_benefit', 'spmwt')
    
    # Calculate the new taxes from flat tax on AGI
    tax_rate = agi_tax / 100
    spmu['new_taxes'] = spmu.adjginc * tax_rate
    
    spmu.new_resources -= spmu.new_taxes
    revenue += mdf.weighted_sum(spmu, 'new_taxes', 'spmwt')
    
    # Calculate the total UBI a spmu recieves based on exclusions
    if ('children' in exclude) and ('non_citizens' not in exclude):
        ubi_population = population - child_population
        ubi = revenue / ubi_population
        spmu['total_ubi'] = ubi * (spmu.numper - spmu.child)
    
    if ('children' not in exclude) and ('non_citizens' in exclude):
        ubi_population = population - non_citizen_population
        ubi = revenue / ubi_population
        spmu['total_ubi'] = ubi * (spmu.numper - spmu.non_citizen)
    
    if ('children' in exclude) and ('non_citizens' in exclude):
        ubi_population = population - non_citizen_population - child_population
        ubi = revenue / ubi_population
        spmu['total_ubi'] = ubi * (spmu.numper - spmu.child - spmu.non_citizen)
    
    else: 
        ubi_population = population
        ubi = revenue / ubi_population
        spmu['total_ubi'] = ubi * spmu.numper
    
    # Calculate 
    spmu.new_resources += spmu.total_ubi
    spmu['new_resources_per_person'] = (spmu.new_resources /
                                                  spmu.numper)
    
    # Calculate poverty gap
    spmu['new_poverty_gap'] = np.where(spmu.new_resources < spmu.spmthresh, 
                               spmu.spmthresh - spmu.new_resources, 0)
    poverty_gap = mdf.weighted_sum(spmu, 'new_poverty_gap', 'spmwt')
    poverty_gap_change = ((poverty_gap - original_poverty_gap) /
                        original_poverty_gap * 100).round(1)
    
    # Merge person and spmu dataframes
    sub_spmu = spmu[['spmfamunit', 'new_resources', 'new_resources_per_person']]
    target_persons = person.merge(sub_spmu, on=['spmfamunit'])
    
    # Calculate the change in poverty rate
    target_persons['poor'] = (target_persons.new_resources < 
                              target_persons.spmthresh)
    total_poor = (target_persons.poor * target_persons.asecwt).sum()
    poverty_rate = (total_poor / population) * 100
    poverty_rate_change = ((poverty_rate - original_poverty_rate) / 
                      original_poverty_rate * 100).round(2)

    # Calculate change in Gini
    new_gini = (mdf.gini(target_persons, 'new_resources_per_person' , 'asecwt'))
    gini_change = ((new_gini - gini) / gini * 100).round(2)
    
    # Calculate percent winners
    target_persons['winner'] = (target_persons.new_resources > 
                                target_persons.spmtotres)
    total_winners = (target_persons.winner * target_persons.asecwt).sum()
    percent_winners = (total_winners / population * 100).round(1)
    
    # Calculate the new poverty rate for each demographic
    def pv_rate(column):
        return mdf.weighted_mean(target_persons[target_persons[column]], 'poor', 'asecwt') * 100
        
    child_poverty_rate = pv_rate('child')
    adult_poverty_rate = pv_rate('adult')
    pwd_poverty_rate = pv_rate('pwd')
    white_poverty_rate = pv_rate('white_non_hispanic')
    black_poverty_rate = pv_rate('black')
    hispanic_poverty_rate = pv_rate('hispanic')

    # Calculate the percent change in poverty rate for each demographic
    child_poverty_rate_change = ((child_poverty_rate - original_child_poverty_rate)/
                                original_child_poverty_rate * 100).round(2)
    adult_poverty_rate_change = ((adult_poverty_rate - original_adult_poverty_rate)/
                                original_adult_poverty_rate * 100).round(2)
    pwd_poverty_rate_change = ((pwd_poverty_rate - original_pwd_poverty_rate)/
                                original_pwd_poverty_rate * 100).round(2)
    white_poverty_rate_change = ((white_poverty_rate - original_white_poverty_rate)/
                                original_white_poverty_rate * 100).round(2)
    black_poverty_rate_change = ((black_poverty_rate - original_black_poverty_rate)/
                                original_black_poverty_rate * 100).round(2)
    hispanic_poverty_rate_change = ((hispanic_poverty_rate - original_hispanic_poverty_rate)/
                                original_hispanic_poverty_rate * 100).round(2)
    
    # Convert UBI and winners to string for title of chart
    ubi_int = int(ubi)
    ubi_int = "{:,}".format(ubi_int)
    ubi_string = str(ubi_int)
    winners_string = str(percent_winners)
    
    # Bar colors
    BLUE = '#1976D2'
    
    # Create x-axis labels for each chart
    x=['Poverty Rate', 'Poverty Gap', 'Inequality (Gini)']
    x2=['Child', 'Adult', 'People<br>with<br>disabilities', 'White<br>non<br>Hispanic', 'Black', 'Hispanic']
    
    # MAKE THESE TWO CHARS A SIMPLIFIED FUNCITON ONCE CODE IS WORKING AGAIN #
    fig = go.Figure([go.Bar(x=x, y=[poverty_rate_change,
                                    poverty_gap_change, 
                                    gini_change],
                            text=[poverty_rate_change,
                                  poverty_gap_change,
                                  gini_change],
                           marker_color=BLUE)])
    
    # Edit text and display the UBI amount and percent winners in title
    fig.update_layout(uniformtext_minsize=10, uniformtext_mode='hide', plot_bgcolor='white')
    fig.update_traces(texttemplate='%{text}%', textposition='auto')
    fig.update_layout(title_text='Your changes would fund an annual UBI of $'+ ubi_string + ' per person.<br>' + 
                     winners_string + '% of people would be better off under this plan.')
    
    
    fig.update_xaxes(
        tickangle = 0,
        title_text = "",
        tickfont = {"size": 14},
        title_standoff = 25)

    fig.update_yaxes(
        title_text = "Percent change",
        ticksuffix ="%",
        tickprefix = "",
        tickfont = {'size':14},
        title_standoff = 25)

    fig.update_xaxes(title_font=dict(size=14, family='Roboto', color='black'))
    fig.update_yaxes(title_font=dict(size=14, family='Roboto', color='black'))
    
    fig2 = go.Figure([go.Bar(x=x2, y=[child_poverty_rate_change,
                                     adult_poverty_rate_change,
                                     pwd_poverty_rate_change,
                                     white_poverty_rate_change,
                                     black_poverty_rate_change,
                                     hispanic_poverty_rate_change],
                            text=[child_poverty_rate_change,
                                     adult_poverty_rate_change,
                                     pwd_poverty_rate_change,
                                     white_poverty_rate_change,
                                     black_poverty_rate_change,
                                     hispanic_poverty_rate_change],
                           marker_color=BLUE)])
    
    fig2.update_layout(uniformtext_minsize=10, uniformtext_mode='hide', plot_bgcolor='white')
    fig2.update_traces(texttemplate='%{text}%', textposition='auto')
    fig2.update_layout(title_text='Poverty rate breakdown')

    fig2.update_xaxes(
        tickangle = 0,
        title_text = "",
        tickfont = {"size": 14},
        title_standoff = 25)

    fig2.update_yaxes(
        title_text = "Percent change",
        ticksuffix ="%",
        tickprefix = "",
        tickfont = {'size':14},
        title_standoff = 25)

    fig2.update_xaxes(title_font=dict(size=14, family='Roboto', color='black'))
    fig2.update_yaxes(title_font=dict(size=14, family='Roboto', color='black'))
    
    return fig, fig2

if __name__ == '__main__':
    app.run_server(debug=True, port=8000, host='127.0.0.1')
