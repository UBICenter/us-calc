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


BLUE = '#1976D2'

person = pd.read_csv('https://raw.githubusercontent.com/ngpsu22/Funding/main/person_ubi_funding%20(7).csv')

# Calculate orginal poverty
population = person.asecwt.sum()
original_total_poor = (person.original_poor * person.asecwt).sum()
original_poverty_rate = (original_total_poor / population) * 100

spmu = person.drop_duplicates(subset=['spmfamunit'])
spmu['original_poverty_gap'] = person.spmthresh - person.spmtotres
original_poverty_gap = (((spmu.original_poor * spmu.original_poverty_gap *
                         spmu.asecwth).sum()))

# Calculate original child poverty
child_population = (person.child * person.asecwt).sum()
original_child_poor = (person.child * person.original_poor * person.asecwt).sum()
original_child_poverty_rate = (original_child_poor / child_population) * 100

# Calculate original adult poverty
adult_population = (person.adult * person.asecwt).sum()
original_adult_poor = (person.adult * person.original_poor * person.asecwt).sum()
original_adult_poverty_rate = (original_adult_poor / adult_population) * 100

# Calculate original pwb poverty
pwb_population = (person.pwb * person.asecwt).sum()
original_pwb_poor = (person.pwb * person.original_poor * person.asecwt).sum()
original_pwb_poverty_rate = (original_pwb_poor / pwb_population) * 100

# Calculate original White poverty
white_population = (person.white_non_hispanic * person.asecwt).sum()
original_white_poor = (person.white_non_hispanic * person.original_poor * person.asecwt).sum()
original_white_poverty_rate = (original_white_poor / white_population) * 100

# Calculate original Black poverty
black_population = (person.black * person.asecwt).sum()
original_black_poor = (person.black * person.original_poor * person.asecwt).sum()
original_black_poverty_rate = (original_black_poor / black_population) * 100

# Calculate original Hispanic poverty
hispanic_population = (person.hispanic * person.asecwt).sum()
original_hispanic_poor = (person.hispanic * person.original_poor * person.asecwt).sum()
original_hispanic_poverty_rate = (original_hispanic_poor / hispanic_population) * 100

# Caluclate original gini
gini = (mdf.gini(person, 'spm_resources_per_person' , 'asecwt'))

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
            ]
        ),
    ],
    color="info",   
    outline=False,
)

card_graph = dbc.Card(
        dcc.Graph(id='my-graph',
              figure={}), body=True, color="info",
)

card_graph2 = dbc.Card(
        dcc.Graph(id='my-graph2',
              figure={}), body=True, color="info",
)


app = dash.Dash(__name__,
                external_stylesheets=[dbc.themes.FLATLY])

server = app.server

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

@app.callback(
    Output(component_id='my-graph', component_property='figure'),
    Output(component_id='my-graph2', component_property='figure'),
    Input(component_id='agi-slider', component_property='value'),
    Input(component_id='my-checklist', component_property='value'),
    Input(component_id='my-checklist2', component_property='value')
)
def ubi(agi_tax, benefits, taxes): 
    target_persons = person.copy(deep=True) 
    
    # Calculate the new taxes from tax on AGI
    tax_rate = agi_tax / 100
    target_persons['new_taxes'] = target_persons.adjginc * tax_rate
    
    # Calculate the total tax increase of an SPM unit
    spmu = target_persons.groupby(['spmfamunit'])[['new_taxes']].sum()
    spmu.columns = ['total_tax_increase']
    target_persons = target_persons.merge(spmu,left_on=['spmfamunit'],
                                           right_index=True)
    
    # Calculate funding from taxes
    funding = (target_persons.new_taxes * target_persons.asecwt).sum()
    
    #Calculate SPM unit new resources after taxes
    target_persons['new_spm_resources'] = target_persons.spmtotres - target_persons.total_tax_increase
    
    if 'ssi' in benefits:
        funding += (target_persons.incssi * target_persons.asecwt).sum()
        target_persons.new_spm_resources -= target_persons.incssi
    
    if 'unemp' in benefits:
        funding += (target_persons.incunemp * target_persons.asecwt).sum()
        target_persons.new_spm_resources -= target_persons.incunemp
        
    if 'eitc' in benefits:
        funding += (target_persons.eitcred * target_persons.asecwt).sum()
        target_persons.new_spm_resources -= target_persons.spmeitc
        
    if 'ctc' in benefits:
        funding += (target_persons.ctc * target_persons.asecwt).sum()
        target_persons.new_spm_resources -= target_persons.spmctc
        
    if 'snap' in benefits:
        funding += (target_persons.snap_pp * target_persons.asecwt).sum()
        target_persons.new_spm_resources -= target_persons.snap_pp
        
    if 'energy' in benefits:
        funding += (target_persons.energy_pp * target_persons.asecwt).sum()
        target_persons.new_spm_resources -= target_persons.energy_pp
    
    if 'income_taxes' in taxes:
        funding -= (target_persons.fedtaxac * target_persons.asecwt).sum()
        target_persons.new_spm_resources += target_persons.fedtaxac
    
    if 'fica' in taxes:
        funding -= (target_persons.fica * target_persons.asecwt).sum()
        target_persons.new_spm_resources += target_persons.fica
    
    if ('income_taxes' in taxes) & ('ctc' in benefits):
        funding -= (target_persons.ctc * target_persons.asecwt).sum()
        target_persons.new_spm_resources += target_persons.spmctc
    
    if ('income_taxes' in taxes) & ('eitc' in benefits):
        funding -= (target_persons.eitcred * target_persons.asecwt).sum()
        target_persons.new_spm_resources += target_persons.spmeitc
    

    ubi = funding / population
    target_persons['total_ubi'] = ubi * target_persons.numper
    target_persons.new_spm_resources += target_persons.total_ubi
  
    target_persons['new_resources_per_person'] = (target_persons.new_spm_resources /
                                                  target_persons.numper)
    
    # Calculate the change in poverty rate
    target_persons['poor'] = (target_persons.new_spm_resources < 
                              target_persons.spmthresh)
    total_poor = (target_persons.poor * target_persons.asecwt).sum()
    poverty_rate = (total_poor / population) * 100
    poverty_rate_change = ((poverty_rate - original_poverty_rate) / 
                      original_poverty_rate * 100).round(2)
    
    # Calculate the change in child poverty
    total_child_poor = (target_persons.child * target_persons.poor * target_persons.asecwt).sum()
    child_poverty_rate = (total_child_poor / child_population) * 100
    child_poverty_rate_change = ((child_poverty_rate - original_child_poverty_rate)/
                                original_child_poverty_rate * 100).round(2)
    
    # Calculate the change in poverty gap
    target_persons['poverty_gap'] = target_persons.spmthresh - target_persons.new_spm_resources
    spmu = target_persons.drop_duplicates(subset=['spmfamunit'])
    poverty_gap = (((spmu.poor * spmu.poverty_gap
                             * spmu.asecwth).sum()))
    poverty_gap_change = ((poverty_gap - original_poverty_gap) /
                        original_poverty_gap * 100).round(1)

    # Calculate change in Gini
    new_gini = (mdf.gini(target_persons, 'new_resources_per_person' , 'asecwt'))
    gini_change = ((new_gini - gini) / gini * 100).round(2)
    
    # Calculate percent winners
    target_persons['winner'] = (target_persons.new_spm_resources > 
                                target_persons.spmtotres)
    total_winners = (target_persons.winner * target_persons.asecwt).sum()
    percent_winners = (total_winners / population * 100).round(1)
    
    # Calculate adult poverty
    total_adult_poor = (target_persons.adult * target_persons.poor * target_persons.asecwt).sum()
    adult_poverty_rate = (total_adult_poor / adult_population) * 100
    adult_poverty_rate_change = ((adult_poverty_rate - original_adult_poverty_rate)/
                                original_adult_poverty_rate * 100).round(2)
    
    # Calculate pwb poverty
    total_pwb_poor = (target_persons.pwb * target_persons.poor * target_persons.asecwt).sum()
    pwb_poverty_rate = (total_pwb_poor / pwb_population) * 100
    pwb_poverty_rate_change = ((pwb_poverty_rate - original_pwb_poverty_rate)/
                                original_pwb_poverty_rate * 100).round(2)
    
    # Calculate White poverty
    total_white_poor = (target_persons.white_non_hispanic * target_persons.poor * target_persons.asecwt).sum()
    white_poverty_rate = (total_white_poor / white_population) * 100
    white_poverty_rate_change = ((white_poverty_rate - original_white_poverty_rate)/
                                original_white_poverty_rate * 100).round(2)
    
    # Calculate Black poverty
    total_black_poor = (target_persons.black * target_persons.poor * target_persons.asecwt).sum()
    black_poverty_rate = (total_black_poor / black_population) * 100
    black_poverty_rate_change = ((black_poverty_rate - original_black_poverty_rate)/
                                original_black_poverty_rate * 100).round(2)
    
    # Calculate Hispanic poverty
    total_hispanic_poor = (target_persons.hispanic * target_persons.poor * target_persons.asecwt).sum()
    hispanic_poverty_rate = (total_hispanic_poor / hispanic_population) * 100
    hispanic_poverty_rate_change = ((hispanic_poverty_rate - original_hispanic_poverty_rate)/
                                original_hispanic_poverty_rate * 100).round(2)
    
    ubi_int = int(ubi)
    ubi_int = "{:,}".format(ubi_int)
    ubi_string = str(ubi_int)
    winners_string = str(percent_winners)
    
    x2=['Child', 'Adult', 'People<br>with<br>disabilities', 'White<br>non<br>Hispanic', 'Black', 'Hispanic']

    fig2 = go.Figure([go.Bar(x=x2, y=[child_poverty_rate_change,
                                     adult_poverty_rate_change,
                                     pwb_poverty_rate_change,
                                     white_poverty_rate_change,
                                     black_poverty_rate_change,
                                     hispanic_poverty_rate_change],
                            text=[child_poverty_rate_change,
                                     adult_poverty_rate_change,
                                     pwb_poverty_rate_change,
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
    
    x=['Poverty Rate', 'Poverty Gap', 'Inequality (Gini)']

    fig = go.Figure([go.Bar(x=x, y=[child_poverty_rate_change, poverty_rate_change, poverty_gap_change, gini_change],
                            text=[child_poverty_rate_change, poverty_rate_change, poverty_gap_change, gini_change],
                           marker_color=BLUE)])
    
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
    
    return fig, fig2


if __name__ == '__main__':
    app.run_server(debug=True, port=8000, host='127.0.0.1')
