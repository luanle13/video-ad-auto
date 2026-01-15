import os
from unittest.mock import patch

import boto3
import pytest
from moto import mock_aws

from tests.fixtures.mocks import create_mock_openai_client


@pytest.fixture
def aws_credentials():
    """Mock AWS credentials."""
    os.environ["AWS_ACCESS_KEY_ID"] = "testing"
    os.environ["AWS_SECRET_ACCESS_KEY"] = "testing"
    os.environ["AWS_DEFAULT_REGION"] = "ap-southeast-1"


@pytest.fixture
def dynamodb_client(aws_credentials):
    """Create mock DynamoDB client."""
    with mock_aws():
        client = boto3.client("dynamodb", region_name=os.environ["AWS_DEFAULT_REGION"])
        yield client


@pytest.fixture
def create_tables(dynamodb_client):
    """Create all test tables."""
    # Create users table
    dynamodb_client.create_table(
        TableName="users",
        KeySchema=[
            {
                'AttributeName': 'user_id',
                'KeyType': 'HASH'
            }
        ],
        AttributeDefinitions=[
            {
                'AttributeName': 'user_id',
                'AttributeType': 'S'
            }
        ],
        BillingMode='PAY_PER_REQUEST'
    )

    # Create products table
    dynamodb_client.create_table(
        TableName="products",
        KeySchema=[
            {
                'AttributeName': 'product_id',
                'KeyType': 'HASH'
            }
        ],
        AttributeDefinitions=[
            {
                'AttributeName': 'product_id',
                'AttributeType': 'S'
            },
            {
                'AttributeName': 'user_id',
                'AttributeType': 'S'
            }
        ],
        GlobalSecondaryIndexes=[
            {
                'IndexName': 'UserIdIndex',
                'KeySchema': [
                    {
                        'AttributeName': 'user_id',
                        'KeyType': 'HASH'
                    }
                ],
                'Projection': {
                    'ProjectionType': 'ALL'
                }
            }
        ],
        BillingMode='PAY_PER_REQUEST'
    )

    # Create jobs table
    dynamodb_client.create_table(
        TableName="jobs",
        KeySchema=[
            {
                'AttributeName': 'job_id',
                'KeyType': 'HASH'
            }
        ],
        AttributeDefinitions=[
            {
                'AttributeName': 'job_id',
                'AttributeType': 'S'
            },
            {
                'AttributeName': 'user_id',
                'AttributeType': 'S'
            }
        ],
        GlobalSecondaryIndexes=[
            {
                'IndexName': 'UserIdIndex',
                'KeySchema': [
                    {
                        'AttributeName': 'user_id',
                        'KeyType': 'HASH'
                    }
                ],
                'Projection': {
                    'ProjectionType': 'ALL'
                }
            }
        ],
        BillingMode='PAY_PER_REQUEST'
    )

    yield {
        "users": "users",
        "products": "products",
        "jobs": "jobs"
    }


@pytest.fixture
def s3_client(aws_credentials):
    """Create mock S3 client."""
    with mock_aws():
        client = boto3.client("s3", region_name=os.environ["AWS_DEFAULT_REGION"])
        yield client


@pytest.fixture
def create_buckets(s3_client):
    """Create test buckets."""
    # Create bucket with proper region configuration
    location_constraint = {'LocationConstraint': os.environ["AWS_DEFAULT_REGION"]}
    s3_client.create_bucket(
        Bucket="test-images",
        CreateBucketConfiguration=location_constraint
    )
    s3_client.create_bucket(
        Bucket="test-videos",
        CreateBucketConfiguration=location_constraint
    )
    return {"images": "test-images", "videos": "test-videos"}


@pytest.fixture
def mock_openai_client():
    """Mock OpenAI client for testing agents."""
    with patch("src.agents.base.get_openai_client") as mock_get:
        mock_client = create_mock_openai_client()
        mock_get.return_value = mock_client
        yield mock_client