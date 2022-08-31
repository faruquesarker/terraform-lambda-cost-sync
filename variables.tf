variable "aws_region" {
  description = "Default AWS region for all resources."

  type    = string
  default = "eu-west-1"
}

variable "dynamodb_table_name" {
  description = "DynamoDB table where resource info are stored"

  type    = string
  default = "AWSCostOptimization"
}


variable "tags" {
  description = "A map of tags to add to the resources"
  type        = map(string)
  default     = {}
}

variable "cost_sync_event_schedule" {
  description = "CRON or rate expression for scheduling Cost-Sync Lambda function"

  type    = string
  default = "cron(0 2 ? * SUN *)"
}
