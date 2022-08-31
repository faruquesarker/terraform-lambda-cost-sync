# Introduction

TF Lambda Resource Sync module is a helper module for optimizing cost of AWS cloud resources. The Terraform code provisions the necessary infrastructure to run the below AWS Lambda functions written in Python `3.7.x`.


*   *`AWS-Cost-Optimization-Cost-Sync`* - This Lambda function provides the following capabilities:

    *   Queries the AWS Cost Explorer API and DynamoDB table to collect the relevant cost information and updates the DynamoDB table items.


## Running AWS Lambda Function

To run the AWS Lambda function in a different time, update the cron schedule for the following entries in the local `terraform.tfvars` file:

*   `cost_sync_event_schedule`


The Cron job schedule expression must be compliant with [AWS guidelines](https://docs.aws.amazon.com/AmazonCloudWatch/latest/events/ScheduledEvents.html).
