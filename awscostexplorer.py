""" awscostexplorer.py """
import boto3
import datetime

class AWSCostExplorer:
    """ Defines the AWS Cost Explorer class """
    
    def __init__(self, days=30, granularity="DAILY"):
        """ Initialize the AWSCostExplorer """
        self._days = days
        self._granularity = granularity
        self._session = boto3.session.Session()
        self._client = self.session.client('ce')
    
    def get_costs_per_tag_and_service(self, key):
        """ Get the costs per tag and service """
        group_by = [
            {
                'Type': 'TAG',
                'Key': key
            },{
                'Type': 'DIMENSION',
                'Key': 'SERVICE'
            }
        ]
        return self._get_results(group_by)

    def get_costs_per_account_and_service(self):
        """ Get the costs per account and service """
        group_by = [
            {
                'Type': 'DIMENSION',
                'Key': 'LINKED_ACCOUNT'
            },{
                'Type': 'DIMENSION',
                'Key': 'SERVICE'}
        ]
        return self._get_results(group_by)

    def _get_results(self, group_by):
        """ Get the results """
        time_period = {
            'Start': self.start,
            'End':  self.end
        }
        token = None
        results = []
        while True:
            if token:
                kwargs = {'NextPageToken': token}
            else:
                kwargs = {}
            data = self.client.get_cost_and_usage(
                TimePeriod=time_period,
                Granularity=self.granularity,
                Metrics=['UnblendedCost'],
                GroupBy=group_by, 
                **kwargs
            )
            results += data['ResultsByTime']
            token = data.get('NextPageToken')
            if not token:
                break
        return results

    @property
    def client(self):
        return self._client

    @property
    def days(self):
        return self._days

    @property
    def end(self):
        return self.now.strftime('%Y-%m-%d')

    @property
    def granularity(self):
        return self._granularity

    @property
    def now(self):
        return datetime.datetime.utcnow().now()

    @property
    def session(self):
        return self._session
        
    @property
    def start(self):
        return (self.now - datetime.timedelta(days=self.days)).strftime('%Y-%m-%d')
