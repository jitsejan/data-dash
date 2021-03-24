""" __main__.py """
from awscostparser import AWSCostParser

acp = AWSCostParser("Name")
print(acp.df.head())

acp = AWSCostParser()
print(acp.df.head())
