# -*- coding: utf-8 -*-
import datetime
import dash
import dash_core_components as dcc
import dash_html_components as html
import pandas as pd
import plotly.express as px
import plotly.graph_objs as go

from awscostparser import AWSCostParser

acp = AWSCostParser(days=365, granularity="MONTHLY")
df = acp.df

key = 'source'
acpk = AWSCostParser(key=key, days=30, granularity="DAILY")
dfk = acpk.df

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

def generate_table(dataframe, max_rows=10):
    return html.Table(
        [html.Tr([html.Th(col) for col in dataframe.columns])] +

        [html.Tr([
            html.Td(dataframe.iloc[i][col]) for col in dataframe.columns
        ]) for i in range(min(len(dataframe), max_rows))]
    )

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

colors = {
    'background': '#eee',
    'text': '#7FDBFF'
}

adf = df.groupby(['start', 'account'], as_index=False)['amount'].sum()
fig2 = px.bar(adf, x="start", y="amount", color='account')
fig3 = px.line(adf, x="start", y="amount", color='account')

rdf = df.groupby(['start', 'resource'], as_index=False)['amount'].sum()
fig4 = px.bar(rdf, x="start", y="amount", color='resource')

adfk = dfk.groupby(['start',  key], as_index=False)['amount'].sum()
figk2 = px.bar(adfk, x="start", y="amount", color=key)
figk3 = px.line(adfk, x="start", y="amount", color=key)
yesterday = datetime.datetime.utcnow().now() - datetime.timedelta(days=1)
adfk2 = dfk[dfk['start'] >= yesterday.strftime('%Y-%m-%d')].groupby(['resource', key], as_index=False)['amount'].sum()
fadfk2 = adfk2[adfk2[key] == f"{key}$"]
figk4 = px.bar(fadfk2, x="resource", y="amount", color=key)


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
        'color': colors['text']
    }),

    html.Div(
        [
            html.H3("Cost per account - Stacked bar"),
            dcc.Graph(
                id="g1",
                figure=fig2
            )
        ],
    ),

    html.Div(
        [
            html.H3("Cost per account - Line"),
            dcc.Graph(
                id="g3",
                figure=fig3
            )
        ],
    ),

    html.Div(
        [
            html.H3("Cost per resource", style={
                'textAlign': 'center',
                'color': colors['text']
            }),
            dcc.Graph(
                id="g4",
                figure=fig4
            )
        ],
    ),

    html.Div(
        [
            html.H3("Cost per source", style={
                'textAlign': 'center',
                'color': colors['text']
            }),
            dcc.Graph(
                id="k2",
                figure=figk2
            )
        ],
    ),

    html.Div(
        [
            html.H3("Untagged resources", style={
                'textAlign': 'center',
                'color': colors['text']
            }),
            dcc.Graph(
                id="k4",
                figure=figk4
            )
        ],
    ),

    generate_table(df)
])

if __name__ == '__main__':
    app.run_server(debug=True)