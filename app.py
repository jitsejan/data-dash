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


dailyresources =AWSCostParser(days=30, granularity="DAILY")
dailyr_df = dailyresources.df
dailyr_df.to_pickle('dailyr.df')
dailyr_df = pd.read_pickle('dailyr.df')

annualresources =AWSCostParser(days=365, granularity="MONTHLY")
annualresources = annualresources.df
annualresources.to_pickle('byaccount.df')
account_df = pd.read_pickle('byaccount.df')

key = 'source'
acpk = AWSCostParser(key=key, days=30, granularity="DAILY")
dfk = acpk.df
dfk.to_pickle('bysourcetag.df')
tag_df = pd.read_pickle('bysourcetag.df')

colors = {
    'background': '#eee',
    'text': 'rgb(242, 158, 57)',
    'graphtext': 'rgb(242, 158, 57)',
}
preffont = dict(
    size=10,
    color=colors['graphtext']
)
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
yestermonth = today - datetime.timedelta(days=31)

data_mask = account_df['start'] >= f'{yestermonth.year}-{yestermonth.month}-01'
print(account_df[data_mask].groupby(['account', 'start'], as_index=False)['amount'].sum().sort_values('amount', ascending=False).head())


# Current MTD versus last month - Total cost per account
data_mask = account_df['start'] >= f'{yestermonth.year}-{yestermonth.month}-01'
month_compare = account_df[data_mask] \
    .groupby(['account', 'start'], as_index=False)['amount'] \
    .sum() \
    .pivot(index='account', values='amount', columns='start')
month_compare['diff'] = month_compare.iloc[:, 1] - month_compare.iloc[:, 0]
month_compare.columns = ['Previous Month', 'Current Month', 'Difference'] 


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
    ),
    yaxis=dict(
        title='Amount (USD)',
    ),
    paper_bgcolor='rgba(0,0,0,0)',
    plot_bgcolor='rgba(0,0,0,0)',
    font=preffont
)
# Cost for AWS by resource [30 days, daily]
drdf = dailyr_df.groupby(['start', 'resource'], as_index=False)['amount'].sum()
daily_resource_cost = go.Figure()
for resource in drdf['resource'].unique():
    rsel = drdf[drdf['resource'] == resource]
    visible = resource in ['AWS Glue', 'AWS Lambda', 'Amazon Simple Storage Service', 'Amazon Redshift']
    params = {
        'name': resource,
        'x': rsel['start'],
        'y': rsel['amount']
    }
    if not visible:
        params['visible'] = 'legendonly'
    daily_resource_cost.add_trace(go.Line(**params))
## Add total line
total_df = dailyr_df.groupby(['start'], as_index=False)['amount'].sum()
params = {
    'name': 'total',
    'x': total_df['start'],
    'y': total_df['amount'],
}
daily_resource_cost.add_trace(go.Line(**params))
daily_resource_cost.update_layout(
    paper_bgcolor='rgba(0,0,0,0)',
    plot_bgcolor='rgba(0,0,0,0)',
    font=preffont
)
# Cost for AWS by resource [365 days, monthly]
rdf = account_df.groupby(['start', 'resource'], as_index=False)['amount'].sum()
resource_cost = go.Figure()
for index, resource in enumerate(rdf['resource'].unique()):
    rsel = rdf[rdf['resource'] == resource]
    visible = resource in ['AWS Glue', 'AWS Lambda', 'Amazon Simple Storage Service', 'Amazon Redshift']
    params = {
        'name': resource,
        'x': rsel['start'],
        'y': rsel['amount'],
        'fill': 'tonexty' if index == 0 else 'tonexty',
        'mode': 'lines'
    }
    if not visible:
        params['visible'] = 'legendonly'
    resource_cost.add_trace(go.Scatter(**params))
resource_cost.update_layout(
    paper_bgcolor='rgba(0,0,0,0)',
    plot_bgcolor='rgba(0,0,0,0)',
    font=preffont
)

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
    plot_bgcolor='rgba(0,0,0,0)',
    font=preffont
)

# Yesterday's untagged resources
mask = (tag_df['start'] >= yesterday.strftime('%Y-%m-%d')) & (tag_df['source'] == '')
ydf = tag_df[mask].groupby(['start', key, 'resource'], as_index=False)['amount'].sum().sort_values('amount', ascending=False)
fig_ydf = go.Figure(data=[go.Bar(
    x=ydf['resource'],
    y=ydf['amount'],
    text=ydf['amount'],
    textposition='auto',
)])
fig_ydf.update_layout(
    paper_bgcolor='rgba(0,0,0,0)',
    plot_bgcolor='rgba(0,0,0,0)',
    font=preffont
)

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
    textposition='auto'
)])
fig_merdf.update_layout(
    xaxis=dict(
        title='Amount (USD)',
    ),
    yaxis=dict(
        title='Resource',
        autorange='reversed',
    ),
    paper_bgcolor='rgba(0,0,0,0)',
    plot_bgcolor='rgba(0,0,0,0)',
    font=preffont
)

# Cost by source
source_df = tag_df[(tag_df['start'] >= f'{today.year}-{today.month}-01') & (tag_df['source'] != "")].groupby(['source', 'resource'], as_index=False)['amount'].sum().sort_values('source', ascending=False)
source_cost_fig = px.bar(source_df, x="amount", y="source", color="resource", orientation='h')
source_cost_fig.update_layout(
    xaxis=dict(
        title='Amount (USD)',
    ),
    yaxis=dict(
        title='Source',
        autorange='reversed',
    ),
    paper_bgcolor='rgba(0,0,0,0)',
    plot_bgcolor='rgba(0,0,0,0)',
    font=preffont,
    title={
        'text': "Plot Title",
        'font': {
            'size': 20
        },
        'y':1,
        'x':0.5,
        'xanchor': 'center',
        'yanchor': 'top'
    }
)

app.layout = html.Div(children=[
    html.Div([
        html.H1(children='AWS cost overview'),
        html.H2(children='Dashboard showing the data for the different accounts.')
    ] , className="header"),
    html.Div([
        html.Div([
            html.H3("Top 10 - Most expensive resources - All accounts total - MTD"),
            dcc.Graph(
                id="fig_merdf",
                figure=fig_merdf
            )]
        ),
        html.Div([
            html.H3("Costs for data accounts by resource - MTD"),
            dcc.Graph(
                id="fig_sub",
                figure=data_acc_fig
            )
        ]),
        html.Div([
            html.H3("Costs of AWS grouped by account"),
            dcc.Graph(
                id="account_cost",
                figure=account_cost            )
            ]
        ),
        html.Div([html.H3("Cost per resource")]),
        html.Div([
            html.Div([
                html.H4("Last year - Monthly"),
                dcc.Graph(
                    id="resource_cost",
                    figure=resource_cost           
                )], className="six columns",
            ),
            html.Div([
                html.H4("Last 30 days - Daily"),
                dcc.Graph(
                    id="daily_resource_cost",
                    figure=daily_resource_cost
                )
            ], className="six columns",
        )], className="row"),
        html.Div([
            html.H3("Yesterdays untagged resources"),
            dcc.Graph(
                id="fig_ydf",
                figure=fig_ydf
            )
        ]),
        html.Div([
            dcc.Graph(
                id="source_cost_fig",
                figure=source_cost_fig
            )
            ]
        )
    ] , className="container-wide"),
])

if __name__ == '__main__':
    app.run_server(debug=True)