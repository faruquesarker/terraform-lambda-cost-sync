
import logging

LOG = logging.getLogger()
LOG.setLevel(logging.INFO)

# Top level constants
GRANULARITY = 'MONTHLY'
TAG_KEY_OWNER = 'Owner'
TAG_KEY_ENV_NAME = 'EnvironmentName'
COST_METRICS = 'UnblendedCost'
UNBLENDED_COST = 'UNBLENDED_COST'
DATA_UNAVAILABLE = '-1'

def get_spent_cost_info(ce_client, start_date, end_date, owner=None, env_name=None):
  try:
    response = ce_client.get_cost_and_usage(
        TimePeriod={
            'Start': start_date,
            'End': end_date
        },
        Granularity=GRANULARITY,
        Filter={
            'Tags': {
                'Key': TAG_KEY_OWNER if owner else TAG_KEY_ENV_NAME,
                'Values': [owner if owner else env_name, ],
            },
      
        },
        Metrics=[COST_METRICS, ]
    )
    last_month_cost = response['ResultsByTime'][0]['Total']['UnblendedCost']
    current_month_cost = response['ResultsByTime'][1]['Total']['UnblendedCost']
    last_month_cost = last_month_cost['Amount']
    current_month_cost = current_month_cost['Amount']
    return (last_month_cost, current_month_cost)
  except ce_client.exceptions.DataUnavailableException: 
    return (-1, -1) # Data unavilable
  except Exception as e:
    LOG.error(f"Error fetching Spent Cost Info from CostExplorer API: {e}")
    raise e

def get_cost_forecast(ce_client, start_date, end_date, owner=None, env_name=None):
  # Avoid client error for the last day of month 
  if start_date == end_date:
    return DATA_UNAVAILABLE
  try:
    resp = ce_client.get_cost_forecast(
        TimePeriod={
            'Start': start_date,
            'End': end_date
        },
        Granularity=GRANULARITY,
        Filter={
            'Tags': {
                'Key': TAG_KEY_OWNER if owner else TAG_KEY_ENV_NAME,
                'Values':[owner if owner else env_name, ],
            },
      
        },
        Metric= UNBLENDED_COST
    )
    forecast_cost = resp['Total']['Amount']
    return forecast_cost
  except ce_client.exceptions.DataUnavailableException: 
    return DATA_UNAVAILABLE # Data unavilable
  except Exception as e:
    LOG.error(f"Error fetching Spent Cost Info from CostExplorer API..: {e}")
    raise e
  