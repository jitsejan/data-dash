""" awscostparser.py """
import pandas as pd

from awscostexplorer import AWSCostExplorer


class AWSCostParser:
    """ Defines the AWSCostParer """

    def __init__(self, key=None, days=30, granularity='DAILY'):
        """ Initializes the AWSCostParser """
        self._key = key
        self._ace = AWSCostExplorer(days=days, granularity=granularity)
        self._df = self._get_dataframe()

    def _get_data(self):
        """ Get the data """
        if self.key:
            return self.ace.get_costs_per_tag_and_service(key=self.key)
        else:
            return self.ace.get_costs_per_account_and_service()
    
    def _get_dataframe(self):
        """ Get the dataframe """
        df = pd.io.json.json_normalize(self._get_data())
        gdf = self._get_groups_dataframe(df)
        df = df\
            .join(gdf)\
            .rename(columns={
                'TimePeriod.End': 'end',
                'TimePeriod.Start': 'start',
                'Metrics.UnblendedCost.Amount': 'amount',
                'Metrics.UnblendedCost.Unit': 'unit',
            })\
            .drop(['Groups', 'Estimated'], axis=1)\
            
        df[['start', 'end']] = df[['start', 'end']].astype('datetime64[ns]')
        df[['amount']] = df[['amount']].astype('float')
        return df

    def _get_groups_dataframe(self, df):
        """ Get the dataframe for the Groups column """
        gdf = df['Groups']\
            .apply(pd.Series)\
            .stack()\
            .to_frame("groups")\
            .reset_index()

        gdf = gdf.join(pd.io.json.json_normalize(gdf['groups']))\
            .drop(['groups', 'level_1'], axis=1)\
            .set_index('level_0')

        column = self.key if self.key else 'account'
        gdf[column] = gdf['Keys'].apply(lambda x: x[0])
        gdf['resource'] = gdf['Keys'].apply(lambda x: x[1])
        gdf.drop(['Keys'], axis=1, inplace=True)
        return gdf

    @property
    def ace(self):
        return self._ace

    @property
    def df(self):
        return self._df

    @property
    def key(self):
        return self._key