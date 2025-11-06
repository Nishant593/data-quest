terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
  required_version = ">= 1.3.0"
}

provider "aws" {
  region                     = "us-east-1"
  s3_use_path_style           = true
  skip_credentials_validation = true
  skip_metadata_api_check     = true
  skip_requesting_account_id  = true

  endpoints {
    lambda = "http://localhost:4566"
    s3     = "http://localhost:4566"
    iam    = "http://localhost:4566"
    logs   = "http://localhost:4566"
    events = "http://localhost:4566"
  }
}

# Package Lambda
# data "archive_file" "lambda_zip" {
#   type        = "zip"
#   source_file = "${path.module}/lambda_build"
#   output_path = "${path.module}/lambda_function.zip"
# }

# IAM Role for Lambda
resource "aws_iam_role" "lambda_exec" {
  name = "lambda-exec-role"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action    = "sts:AssumeRole"
      Effect    = "Allow"
      Principal = { Service = "lambda.amazonaws.com" }
    }]
  })
}

# Lambda Function
resource "aws_lambda_function" "lambda" {
  function_name = "data-sync-lambda"
  filename      = "${path.module}/lambda_function.zip"
  handler       = "lambda_function.lambda_handler"
  runtime       = "python3.11"
  role          = aws_iam_role.lambda_exec.arn
  timeout       = 900

  environment {
    variables = {
      ENDPOINT_URL = "http://host.docker.internal:4566"
      RAW_BUCKET   = "raw-data"
      AWS_REGION   = "us-east-1"
    }
  }

  logging_config {
    log_group = "/aws/lambda/data-sync-lambda"
    log_format = "Text"
  }
}

# S3 Bucket for raw data
resource "aws_s3_bucket" "raw_bucket" {
  bucket        = "raw-data"
  force_destroy = true
}

resource "aws_s3_bucket" "processed_bucket" {
  bucket        = "processed-data"
  force_destroy = true
}

# CloudWatch Event (EventBridge) to trigger Lambda daily
resource "aws_cloudwatch_event_rule" "daily_rule" {
  name                = "daily-lambda-trigger"
  schedule_expression = "rate(1 day)"
}

resource "aws_cloudwatch_event_target" "lambda_target" {
  rule      = aws_cloudwatch_event_rule.daily_rule.name
  target_id = "data-sync-lambda"
  arn       = aws_lambda_function.lambda.arn
}

# Allow CloudWatch Events to invoke Lambda
resource "aws_lambda_permission" "allow_event" {
  statement_id  = "AllowExecutionFromCloudWatch"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.lambda.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.daily_rule.arn
}

output "lambda_name" {
  value = aws_lambda_function.lambda.function_name
}

output "s3_bucket_name" {
  value = aws_s3_bucket.raw_bucket.bucket
}
