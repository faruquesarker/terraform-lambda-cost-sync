import json
import os
import logging
import boto3

import utils
import dynamodb
import cost_explorer as ce

LOG = logging.getLogger()
LOG.setLevel(logging.INFO)

# DynamoDB
dynamodb_client = boto3.client('dynamodb')

# CostExplorer
ce_client = boto3.client('ce')

## Main lambda handler
def lambda_handler(event, context):
    # Get a list of App env owner from DynamoDB
    all_items = dynamodb.get_all_items(projection_expression="Owner")
    owners = set([item.get('Owner') for item in all_items ])
    num_owners = len(owners)
    LOG.info(f"Got: {num_owners} owners from DynamoDB: {owners}")
    
    for owner in owners:
      env_items = dynamodb.get_items_by_owner(owner)
      LOG.info("Found: " + str(len(env_items)) + " App envs for: " + owner)
      updated_env_items = dynamodb.update_cost_info_by_owner(dynamodb_client, ce_client, env_items, owner)
                 
    return {
        'statusCode': 200,
        'body': json.dumps('Finished Running AWS Cost Optimization Cost Sync Lambda Function!')
    }
