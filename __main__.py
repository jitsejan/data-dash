import boto3
import datetime
import pandas as pd
import os

DAYS = 30
GRANULARITY = 'MONTHLY' # DAILY, HOURLY

session = boto3.session.Session()
ce_client = session.client('ce')

now = datetime.datetime.utcnow()
start = (now - datetime.timedelta(days=DAYS)).strftime('%Y-%m-%d')
end = now.strftime('%Y-%m-%d')


token = None
results = []

while True:
    if token:
        kwargs = {'NextPageToken': token}
    else:
        kwargs = {}
    data = ce_client.get_cost_and_usage(TimePeriod={'Start': start, 'End':  end},
                                     Granularity=GRANULARITY, Metrics=['UnblendedCost'],
                                     GroupBy=[{'Type': 'DIMENSION', 'Key': 'LINKED_ACCOUNT'},
                                              {'Type': 'DIMENSION', 'Key': 'SERVICE'}], 
                                     **kwargs)
    results += data['ResultsByTime']
    token = data.get('NextPageToken')
    if not token:
        break


df = pd.io.json.json_normalize(results)
gdf = df['Groups'].apply(pd.Series).stack().to_frame("groups").reset_index()
gdf = gdf.join(pd.io.json.json_normalize(gdf['groups'])).drop(['groups', 'level_1'], axis=1).set_index('level_0')
gdf['account'] = gdf['Keys'].apply(lambda x: x[0])
gdf['resource'] = gdf['Keys'].apply(lambda x: x[1])
gdf.drop(['Keys'], axis=1, inplace=True)

rdf = df.join(gdf).drop(['Groups'], axis=1)

rdf.rename(columns={
    'TimePeriod.End': 'end',
    'TimePeriod.Start': 'start',
    'Metrics.UnblendedCost.Amount': 'amount',
    'Metrics.UnblendedCost.Unit': 'unit',
}, inplace=True)
rdf.drop(['Estimated'], axis=1, inplace=True)
rdf[['start', 'end']] = rdf[['start', 'end']].astype('datetime64[ns]')
rdf[['amount']] = rdf[['amount']].astype('float')

print(rdf.head())