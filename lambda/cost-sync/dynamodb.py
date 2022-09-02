import os
import boto3
import logging
from boto3.dynamodb.conditions import Attr

LOG = logging.getLogger()
LOG.setLevel(logging.INFO)

import utils as u
import cost_explorer as ce

REGION=os.environ.get('REGION')
COST_REPORT_DDB_TABLE_NAME = os.environ.get("COST_REPORT_DDB_TABLE_NAME")
PARTITION_KEY = "EnvironmentName"
SORT_KEY = "Owner"

def update_env_item(dynamodb_client, app_env, current_month_cost, last_month_cost, forecast_cost):
    try:
        env_name = app_env.get("EnvironmentName")
        LOG.info(f"Updating cost info for App env: {env_name}")
        response =  dynamodb_client.update_item(
                        TableName=COST_REPORT_DDB_TABLE_NAME,
                        Key={
                            "Owner": {"S": app_env["Owner"] },
                            "EnvironmentName": {"S": env_name }
                        },
                        AttributeUpdates={
                              "Cost.CurrentMonth" : {'Value': {'S': current_month_cost } },
                              "Cost.LastMonth" : {'Value': {'S': last_month_cost } },
                              "Cost.ProjectionMonthEnd" : {'Value': {'S': forecast_cost } }
                        }
                    )
        return True
    except Exception as e:
        LOG.error(f"Error Updating App env:  {env_name} cost info to DynamoDB Table {COST_REPORT_DDB_TABLE_NAME}: {e}")
        raise e

def update_cost_info_by_owner(dynamodb_client, ce_client, env_items, owner):   
    updated_env_items = []
    for app_env in env_items:
        env_name = app_env.get('EnvironmentName')
        LOG.info(f"Working on {app_env} Env created by: {owner}") 
        (last_month_cost, current_month_cost) = ce.get_spent_cost_info(ce_client, u.get_last_month_start_date(), u.get_today_date(), env_name=env_name)
        LOG.info(f"{owner} has spent last month: {last_month_cost} and this month: {current_month_cost}")
        forecast_cost = ce.get_cost_forecast(ce_client, u.get_today_date(), u.get_month_end_date(), env_name=env_name)
        LOG.info(f"Cost forecast this month: {forecast_cost}")
        update_env_item(dynamodb_client, app_env, current_month_cost, last_month_cost, forecast_cost)
        app_env['Cost.CurrentMonth'] = float(current_month_cost)
        app_env['Cost.LastMonth'] = float(last_month_cost)
        app_env['Cost.ProjectionMonthEnd'] = float(forecast_cost)
        updated_env_items.append(app_env)
    return updated_env_items
    

def get_all_items(projection_expression=None):
    try:
        dynamodb = boto3.resource('dynamodb', region_name=REGION)
        table = dynamodb.Table(COST_REPORT_DDB_TABLE_NAME)
        if projection_expression is None:
            response = table.scan()
        else:
            response = table.scan(ProjectionExpression=projection_expression)
        data = response['Items']
        
        while 'LastEvaluatedKey' in response:
            response = table.scan(ExclusiveStartKey=response['LastEvaluatedKey'])
            data.extend(response['Items'])
        return data
    except Exception as e:
        LOG.error(f"Fetching App env from DynamoDB: {e}")
        raise e
        
    
def get_items_by_owner(owner):
    try:
        dynamodb = boto3.resource('dynamodb', region_name=REGION)
        table = dynamodb.Table(COST_REPORT_DDB_TABLE_NAME)
        response = table.scan(FilterExpression=Attr('Owner').eq(owner))
        data = response['Items']
        while 'LastEvaluatedKey' in response:
            response = table.scan(ExclusiveStartKey=response['LastEvaluatedKey'])
            data.extend(response['Items'])
        return data
    except Exception as e:
        LOG.error(f"Fetching App env from DynamoDB: {e}")
        raise e