# -*- coding: utf-8 -*-
import datetime
import dash
import dash_core_components as dcc
import dash_html_components as html
import os
import pandas as pd
import plotly.express as px
import plotly.graph_objs as go
from plotly.subplots import make_subplots
import sys

from awscostparser import AWSCostParser

if not os.environ.get('AWS_PROFILE'):
    print("Error: Please set `AWS_PROFILE` in your environment variables (i.e. export AWS_PROFILE='prod')")
    sys.exit(2)


# acp = AWSCostParser(days=365, granularity="MONTHLY")
# df = acp.df
# df.to_pickle('byaccount.df')
account_df = pd.read_pickle('byaccount.df')

key = 'source'
# acpk = AWSCostParser(key=key, days=30, granularity="DAILY")
# dfk = acpk.df
# dfk.to_pickle('bysourcetag.df')
tag_df = pd.read_pickle('bysourcetag.df')

colors = {
    'background': '#fff',
    'text': 'rgb(242, 158, 57)',
    'amazon': 'rgb(242, 158, 57)',
    'graphtext': 'rgb(242, 158, 57)',
}
external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

def generate_table(dataframe, max_rows=10):
    return html.Table(
        [html.Tr([html.Th(col) for col in dataframe.columns])] +

        [html.Tr([
            html.Td(dataframe.iloc[i][col]) for col in dataframe.columns
        ]) for i in range(min(len(dataframe), max_rows))]
    )

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

today = datetime.datetime.utcnow().now() 
yesterday = today - datetime.timedelta(days=1)

# Cost for AWS by account
adf = account_df.groupby(['start', 'account'], as_index=False)['amount'].sum()
account_cost = go.Figure()
for account in adf['account'].unique():
    sel = adf[adf['account'] == account]
    visible = account in ['Data Prod', 'Data Dev']
    params = {
        'name': account,
        'x': sel['start'],
        'y': sel['amount']
    }
    if not visible:
        params['visible'] = 'legendonly'
    account_cost.add_trace(go.Bar(**params))
account_cost.update_layout(
    xaxis=dict(
        title='Month',
        color=colors['graphtext']
    ),
    yaxis=dict(
        title='Amount (USD)',
        color=colors['graphtext']
    ),
    paper_bgcolor='rgba(0,0,0,0)',
    plot_bgcolor='rgba(0,0,0,0)'
)
# Cost for AWS by resource
rdf = account_df.groupby(['start', 'resource'], as_index=False)['amount'].sum()
resource_cost = go.Figure()
for resource in rdf['resource'].unique():
    rsel = rdf[rdf['resource'] == resource]
    visible = resource in ['AWS Glue', 'AWS Lambda', 'Amazon Simple Storage Service', 'Amazon Redshift']
    params = {
        'name': resource,
        'x': rsel['start'],
        'y': rsel['amount']
    }
    if not visible:
        params['visible'] = 'legendonly'
    resource_cost.add_trace(go.Line(**params))

# Root, Data Dev & Prod
data_mask = (account_df['account'].isin(['Data Dev', 'Data Prod', 'Root'])) & (account_df['start'] >= f'{today.year}-{today.month}-01') & (account_df['amount'] > 1)
data = account_df[data_mask]
data_acc_fig = px.bar(data, x="resource", y="amount", color="account", barmode="group")
data_acc_fig.update_layout(
    xaxis=dict(
        title='Resource',
    ),
    yaxis=dict(
        title='Amount (USD)',
    ),
    paper_bgcolor='rgba(0,0,0,0)',
    plot_bgcolor='rgba(0,0,0,0)'
)

# Yesterday's untagged resources
mask = (tag_df['start'] >= yesterday.strftime('%Y-%m-%d')) & (tag_df['source'] == '')
ydf = tag_df[mask].groupby(['start', key, 'resource'], as_index=False)['amount'].sum().sort_values('amount', ascending=False)
fig_ydf = go.Figure(data=[go.Bar(
    x=ydf['resource'],
    y=ydf['amount'],
    text=ydf['amount'],
    textposition='auto',
    marker_color=colors['amazon'],
)])

# Top 10 most expensive resources MTD
merdf = account_df[account_df['start'] >= f'{today.year}-{today.month}-01']\
    .groupby(['resource', 'start'], as_index=False)\
    .sum()\
    .nlargest(10, 'amount')
fig_merdf = go.Figure(data=[go.Bar(
    x=merdf['amount'],
    y=merdf['resource'],
    text=merdf['amount'],
    orientation='h',
    textposition='auto',
    marker_color=colors['amazon'],
)])
fig_merdf.update_layout(
    xaxis=dict(
        title='Amount (USD)',
        color=colors['graphtext']
    ),
    yaxis=dict(
        title='Resource',
        autorange='reversed',
        color=colors['graphtext']
    ),
    paper_bgcolor='rgba(0,0,0,0)',
    plot_bgcolor='rgba(0,0,0,0)'
)

# Cost by source
source_df = tag_df[(tag_df['start'] >= f'{today.year}-{today.month}-01') & (tag_df['source'] != "")].groupby(['source', 'resource', 'start'], as_index=False)['amount'].sum().sort_values('source', ascending=False)
source_cost_fig = px.bar(source_df, x="amount", y="source", color="resource", orientation='h')
source_cost_fig.update_layout(
    xaxis=dict(
        title='Amount (USD)',
        color=colors['graphtext']
    ),
    yaxis=dict(
        title='Source',
        autorange='reversed',
        color=colors['graphtext']
    ),
    paper_bgcolor='rgba(0,0,0,0)',
    plot_bgcolor='rgba(0,0,0,0)',
    font=dict(
        family="Courier New, monospace",
        size=10,
        color="#7f7f7f"
    )
)

app.layout = html.Div(style={'backgroundColor': colors['background']}, children=[
    html.H1(
        children='Cost overview',
        style={
            'textAlign': 'center',
            'color': colors['text']
        }
    ),

    html.Div(children='Dashboard showing the data for the different accounts.', style={
        'textAlign': 'center',
        'color': colors['text'],
        'backgroundColor': colors['background']
    }),

    html.Div(
        [
            html.H3("Top 10 - Most expensive resources - All accounts total - MTD", style={
        'textAlign': 'center',
        'color': colors['text'],
        'backgroundColor': colors['background']
    }),
            dcc.Graph(
                id="fig_merdf",
                figure=fig_merdf            )
        ],
    ),
    html.Div([
        html.H3("Costs for data accounts by resource - MTD", style={
            'textAlign': 'center',
            'color': colors['text'],
            'backgroundColor': colors['background']
        }),
        dcc.Graph(
            id="fig_sub",
            figure=data_acc_fig            )
    ]),
    html.Div(
        [
            html.H3("Costs of AWS grouped by account", style={
            'textAlign': 'center',
            'color': colors['text'],
            'backgroundColor': colors['background']
        }),
            dcc.Graph(
                id="account_cost",
                figure=account_cost            )
        ],
    ),
    html.Div(
        [
            html.H3("Costs of AWS grouped by resource", style={
            'textAlign': 'center',
            'color': colors['text'],
            'backgroundColor': colors['background']
        }),
            dcc.Graph(
                id="resource_cost",
                figure=resource_cost            )
        ],
    ),
    html.Div(
        [
            html.H3("Yesterdays untagged resources", style={
        'textAlign': 'center',
        'color': colors['text'],
        'backgroundColor': colors['background']
    }),
            dcc.Graph(
                id="fig_ydf",
                figure=fig_ydf            )
        ],
    ),
    html.Div(
        [
            html.H3("Costs by source", style={
        'textAlign': 'center',
        'color': colors['text'],
        'backgroundColor': colors['background']
    }),
            dcc.Graph(
                id="source_cost_fig",
                figure=source_cost_fig            )
        ],
    ),
    # generate_table(df)
])

if __name__ == '__main__':
    app.run_server(debug=True)