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

person = pd.read_csv('https://github.com/ngpsu22/Funding/raw/main/person_ubi_funding.csv')

BLUE = '#1976D2'

population = person.asecwt.sum()

og_total_poor = (person.original_poor * person.asecwt).sum()
original_poverty_rate = (og_total_poor / population) * 100

person['spm_resources_per_person'] = person.spmtotres / person.pernum
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
                                    {'label': '  Social Security', 'value': 'ss'},
                                    {'label': '  Supplemental Security Income (SSI)', 'value': 'ssi'},
                                    {'label': '  Unemployment', 'value': 'unemp'},
                                    {'label': '  Earned Income Tax Credit', 'value': 'eitc'},
                                    {'label': '  Child Tax Credit', 'value': 'ctc'},
                                    {'label': '  Snap (food stamps)', 'value': 'snap'},
                                    {'label': '  Energy Subsidy (LIHEAP)', 'value': 'energy'}
                                    
                                ],
                                value=[],
                              labelStyle={'display': 'block'}
                            ),
                html.Br(),
                html.Label(['Flat Tax on AGI'],style={'font-weight': 'bold',
                                                            "text-align": "center",
                                                             "color":"white",
                                                            'fontSize':20}),
                dcc.Slider(
                            id='agi-slider',
                            min=0,
                            max=10,
                            step=1,
                            value=0,
                            marks={0: {'label': '0%', 'style': {'color': '#F8F8FF'}},
                                   1: {'label': '1%', 'style': {'color': '#F8F8FF'}},
                                   2: {'label': '2%', 'style': {'color': '#F8F8FF'}},
                                   3: {'label': '3%', 'style': {'color': '#F8F8FF'}},
                                   4: {'label': '4%', 'style': {'color': '#F8F8FF'}},
                                   5: {'label': '5%', 'style': {'color': '#F8F8FF'}},
                                   6: {'label': '6%', 'style': {'color': '#F8F8FF'}},
                                   7: {'label': '7%', 'style': {'color': '#F8F8FF'}},
                                   8: {'label': '8%', 'style': {'color': '#F8F8FF'}},
                                   9: {'label': '9%', 'style': {'color': '#F8F8FF'}},
                                   10: {'label': '10%', 'style': {'color': '#F8F8FF'}},
                                      }
                        ),
                        html.Div(id='slider-output-container'),
                
                                html.Br(),
                html.Label(['Flat Tax on Taxable Income'],style={'font-weight': 'bold',
                                                            "text-align": "center",
                                                             "color":"white",
                                                            'fontSize':20}),
                
                dcc.Slider(
                            id='taxable-slider',
                            min=0,
                            max=10,
                            step=1,
                            value=0,
                            marks={0: {'label': '0%', 'style': {'color': '#F8F8FF'}},
                                   1: {'label': '1%', 'style': {'color': '#F8F8FF'}},
                                   2: {'label': '2%', 'style': {'color': '#F8F8FF'}},
                                   3: {'label': '3%', 'style': {'color': '#F8F8FF'}},
                                   4: {'label': '4%', 'style': {'color': '#F8F8FF'}},
                                   5: {'label': '5%', 'style': {'color': '#F8F8FF'}},
                                   6: {'label': '6%', 'style': {'color': '#F8F8FF'}},
                                   7: {'label': '7%', 'style': {'color': '#F8F8FF'}},
                                   8: {'label': '8%', 'style': {'color': '#F8F8FF'}},
                                   9: {'label': '9%', 'style': {'color': '#F8F8FF'}},
                                   10: {'label': '10%', 'style': {'color': '#F8F8FF'}},
                                      }
                        ),
                        html.Div(id='slider-output-container2'),
                
                
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

app = dash.Dash(__name__,
                external_stylesheets=[dbc.themes.FLATLY])

server = app.server

app.layout = html.Div([
        # Row 1 - header
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
])

@app.callback(
    Output(component_id='my-graph', component_property='figure'),
    Input(component_id='agi-slider', component_property='value'),
    Input(component_id='taxable-slider', component_property='value'),
    Input(component_id='my-checklist', component_property='value')
)
def ubi(agi_tax, taxable_tax, benefits):
    
    target_persons = person.copy(deep=True) 
    
    # Calculate the new taxes each person pays
    tax_rate = agi_tax / 100
    target_persons['new_taxes'] = target_persons.adjginc * tax_rate
    
    # Calculate the total tax increase of an SPM unit
    spmu = target_persons.groupby(['spmfamunit'])[['new_taxes']].sum()
    spmu.columns = ['total_tax_increase']
    target_persons = target_persons.merge(spmu,left_on=['spmfamunit'],
                                           right_index=True)

    
    # Calculate the new taxes each person pays
    tax_rate2 = taxable_tax / 100
    target_persons['new_taxes2'] = target_persons.taxinc * tax_rate2
    
    # Calculate the total tax increase of an SPM unit
    spmu2 = target_persons.groupby(['spmfamunit'])[['new_taxes2']].sum()
    spmu2.columns = ['total_tax_increase2']
    target_persons = target_persons.merge(spmu2,left_on=['spmfamunit'],
                                           right_index=True)
    
    # Calculate tax revenue
    tax_revenue = ((target_persons.new_taxes * target_persons.asecwt).sum() + 
                  (target_persons.new_taxes2 * target_persons.asecwt).sum())
    
    if 'ss' in benefits:
        ubi_ss = (target_persons.incss * target_persons.asecwt).sum()
        target_persons['new_ssspm'] = 0
    else: 
        ubi_ss = 0
        target_persons['new_ssspm'] = target_persons.spmss
        
    if 'ssi' in benefits:
        ubi_ssi = (target_persons.incssi * target_persons.asecwt).sum()
        target_persons['new_ssispm'] = 0 
    else:
        ubi_ssi = 0
        target_persons['new_ssispm'] = target_persons.spmssi
    
    if 'unemp' in benefits:
        ubi_unemp = (target_persons.incunemp * target_persons.asecwt).sum()
        target_persons['new_spmincunemp'] = 0 
    else:
        ubi_unemp = 0
        target_persons['new_spmincunemp'] = target_persons.spmincunemp
        
    if 'eitc' in benefits:
        ubi_eitc = (target_persons.eitcred * target_persons.asecwt).sum()
        target_persons['new_spmeitc'] = 0
    else:
        ubi_eitc = 0
        target_persons['new_spmeitc'] = target_persons.spmeitc
        
    if 'ctc' in benefits:
        ubi_ctc = (target_persons.ctc * target_persons.asecwt).sum()
        target_persons['new_spmctc'] = 0
    else:
        ubi_ctc = 0
        target_persons['new_spmctc'] = target_persons.spmctc
        
    if 'snap' in benefits:
        ubi_snap = (target_persons.snap_pp * target_persons.asecwt).sum()
        target_persons['new_spmsnap'] = 0
    else:
        ubi_snap = 0
        target_persons['new_spmsnap'] = target_persons.spmsnap
    
    if 'energy' in benefits:
        ubi_energy = (target_persons.energy_pp * target_persons.asecwt).sum()
        target_persons['new_spmenergy'] = 0
    else:
        ubi_energy = 0
        target_persons['new_spmenergy'] = target_persons.spmheat

    funding = (ubi_ss + ubi_ssi + ubi_unemp + ubi_eitc + ubi_ctc + 
               ubi_snap + ubi_energy + tax_revenue)
    ubi = funding / population
    target_persons['total_ubi'] = ubi * target_persons.pernum

    # Calculate new total resources
    target_persons['new_spm_resources'] = (target_persons.spmtotres + 
                                           target_persons.new_ssspm -
                                           target_persons.spmss + 
                                           target_persons.new_ssispm -
                                           target_persons.spmssi +
                                           target_persons.new_spmincunemp -
                                           target_persons.spmincunemp +
                                           target_persons.new_spmeitc -
                                           target_persons.spmeitc +
                                           target_persons.new_spmctc -
                                           target_persons.spmctc +
                                           target_persons.new_spmsnap -
                                           target_persons.spmsnap +
                                           target_persons.new_spmenergy -
                                           target_persons.spmheat +
                                           target_persons.total_ubi -
                                           target_persons.total_tax_increase +
                                            target_persons.total_tax_increase2)
  
    target_persons['new_resources_per_person'] = (target_persons.new_spm_resources /
                                                  target_persons.pernum)
    
    # Calculate the change in poverty rate
    target_persons['poor'] = (target_persons.new_spm_resources < 
                              target_persons.spmthresh)
  
    total_poor = (target_persons.poor * target_persons.asecwt).sum()
    poverty_rate = (total_poor / population) * 100

    poverty_change = ((poverty_rate - original_poverty_rate) / 
                      original_poverty_rate * 100).round(2)

    # Calculate change in Gini
    new_gini = (mdf.gini(target_persons, 'new_resources_per_person' , 'asecwt'))
    gini_change = ((new_gini - gini) / gini * 100).round(2)
    
    ubi_int = int(ubi)
    ubi_int = "{:,}".format(ubi_int)
    ubi_string = str(ubi_int)
    
    x=['Poverty Change', 'Inequality Change']

    fig = go.Figure([go.Bar(x=x, y=[poverty_change, gini_change],
                            text=[poverty_change, gini_change],
                           marker_color=BLUE)])
    
    fig.update_layout(uniformtext_minsize=10, uniformtext_mode='hide', plot_bgcolor='white')
    fig.update_traces(texttemplate='%{text}%', textposition='auto')
    fig.update_layout(title_text='Your changes would fund an annual UBI of $'+ ubi_string + ' per person')

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

    return fig

if __name__ == '__main__':
    app.run_server(debug=True, port=8000, host='127.0.0.1')
