## Create necessary Infrastructure for deploying Lambda
# S3 bucket
resource "random_pet" "lambda_bucket_name" {
  prefix = "aws-cost-optimization"
  length = 4
}

resource "aws_s3_bucket" "lambda_bucket" {
  bucket = random_pet.lambda_bucket_name.id

  acl           = "private"
  force_destroy = true

  tags = var.tags
}

# Retrieve DynamoDB table data
data "aws_dynamodb_table" "current" {
  name = var.dynamodb_table_name
}

# IAM policies and roles
resource "aws_iam_policy" "policy_cost_sync_lambda_exec_01" {
  name = "terraform-lambda-cost-sync-exec-01"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = [
          "ce:Get*",
          "cloudformation:ListStackResources",
          "cloudformation:DescribeStacks",
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents",
        ]
        Effect   = "Allow"
        Resource = "*"
      },
      {
        Action = ["dynamodb:BatchGetItem",
          "dynamodb:GetItem",
          "dynamodb:Query",
          "dynamodb:Scan",
          "dynamodb:BatchWriteItem",
          "dynamodb:PutItem",
          "dynamodb:UpdateItem",
          "dynamodb:DescribeTable",
          "dynamodb:CreateTable",
          "dynamodb:DeleteTable",
        ]
        # Just a comment line
        Resource = "${aws_dynamodb_table.current.arn}"
        Effect   = "Allow"
      },
      {
        "Sid" : "ListObjectsInBucket",
        "Effect" : "Allow",
        "Action" : ["s3:ListBucket"],
        "Resource" : "${aws_s3_bucket.lambda_bucket.arn}"
      },
      {
        "Sid" : "AllObjectActions",
        "Effect" : "Allow",
        "Action" : ["s3:*Object"],
        "Resource" : "${aws_s3_bucket.lambda_bucket.arn}/*"
      },
    ]
  })

  tags = var.tags
}

resource "aws_iam_role" "lambda_exec" {
  name = "aws_cost_optimization_cost_sync_lambda_exec_role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Sid    = ""
      Principal = {
        Service = "lambda.amazonaws.com"
      }
      }
    ]
  })

  managed_policy_arns = [aws_iam_policy.policy_cost_sync_lambda_exec_01.arn, ]

  tags = var.tags
}


# Cost-Sync Lambda Fn and supporting inf
data "archive_file" "lambda_cost_sync" {
  type = "zip"

  source_dir  = "${path.module}/lambda/cost-sync"
  output_path = "${path.module}/lambda/cost-sync.zip"
}

resource "aws_s3_bucket_object" "lambda_cost_sync" {
  bucket = aws_s3_bucket.lambda_bucket.id

  key    = "cost-sync.zip"
  source = data.archive_file.lambda_cost_sync.output_path

  etag = filemd5(data.archive_file.lambda_cost_sync.output_path)

  tags = var.tags
}

resource "aws_lambda_function" "cost_sync" {
  function_name = "AWS-Cost-Optimization-Cost-Sync"

  s3_bucket = aws_s3_bucket.lambda_bucket.id
  s3_key    = aws_s3_bucket_object.lambda_cost_sync.key

  runtime = "python3.7"
  handler = "lambda_function.lambda_handler"

  source_code_hash = data.archive_file.lambda_cost_sync.output_base64sha256

  role = aws_iam_role.lambda_exec.arn

  timeout = 900 # set to max value

  environment {
    variables = {
      "COST_REPORT_DDB_TABLE_NAME" = data.aws_dynamodb_table.current.name,
      "REGION"                     = var.aws_region
    }
  }

  tags = var.tags
}

resource "aws_cloudwatch_log_group" "cost_sync" {
  name = "/aws/lambda/${aws_lambda_function.cost_sync.function_name}"

  retention_in_days = 30

  tags = var.tags
}

#####  Scheduled Tasks #####
## Add Scheduled Tasks for Cost-Sync lambda functions
resource "aws_cloudwatch_event_rule" "cost_sync_event" {
  name                = "cost-sync-event"
  description         = "Cost Optimization Cost Sync Lambda - Fires at a given time"
  schedule_expression = var.cost_sync_event_schedule
}

resource "aws_cloudwatch_event_target" "run_cost_sync" {
  rule      = aws_cloudwatch_event_rule.cost_sync_event.name
  target_id = "cost_sync"
  arn       = aws_lambda_function.cost_sync.arn
}

resource "aws_lambda_permission" "allow_cloudwatch_to_call_cost_sync" {
  statement_id  = "AllowExecutionFromCloudWatch"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.cost_sync.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.cost_sync_event.arn
}
