#!/bin/bash
set -e

echo "Starting local development environment..."

# Start docker-compose services
echo "Starting Docker services..."
docker-compose up -d

# Wait for LocalStack to be ready
echo "Waiting for LocalStack to be ready..."
sleep 10

# Create S3 buckets
echo "Creating S3 buckets..."
aws --endpoint-url=http://localhost:4566 s3 mb s3://ai-video-platform-artifacts
aws --endpoint-url=http://localhost:4566 s3 mb s3://ai-video-platform-webapp
aws --endpoint-url=http://localhost:4566 s3 mb s3://ai-video-platform-media

# Create DynamoDB tables
echo "Creating DynamoDB tables..."

# Users table
aws --endpoint-url=http://localhost:4566 dynamodb create-table \
    --table-name users \
    --attribute-definitions \
        AttributeName=user_id,AttributeType=S \
    --key-schema \
        AttributeName=user_id,KeyType=HASH \
    --billing-mode PAY_PER_REQUEST

# Products table
aws --endpoint-url=http://localhost:4566 dynamodb create-table \
    --table-name products \
    --attribute-definitions \
        AttributeName=product_id,AttributeType=S \
        AttributeName=user_id,AttributeType=S \
    --key-schema \
        AttributeName=product_id,KeyType=HASH \
    --global-secondary-indexes \
        "IndexName=UserIdIndex,KeySchema=[{AttributeName=user_id,KeyType=HASH}],Projection={ProjectionType=ALL},BillingMode=PAY_PER_REQUEST" \
    --billing-mode PAY_PER_REQUEST

# Jobs table
aws --endpoint-url=http://localhost:4566 dynamodb create-table \
    --table-name jobs \
    --attribute-definitions \
        AttributeName=job_id,AttributeType=S \
        AttributeName=user_id,AttributeType=S \
    --key-schema \
        AttributeName=job_id,KeyType=HASH \
    --global-secondary-indexes \
        "IndexName=UserIdIndex,KeySchema=[{AttributeName=user_id,KeyType=HASH}],Projection={ProjectionType=ALL},BillingMode=PAY_PER_REQUEST" \
    --billing-mode PAY_PER_REQUEST

# Wait for tables to be active
echo "Waiting for DynamoDB tables to be active..."
aws --endpoint-url=http://localhost:4566 dynamodb wait table-exists --table-name users
aws --endpoint-url=http://localhost:4566 dynamodb wait table-exists --table-name products
aws --endpoint-url=http://localhost:4566 dynamodb wait table-exists --table-name jobs

# Create secrets in SecretsManager
echo "Creating secrets in Secrets Manager..."
aws --endpoint-url=http://localhost:4566 secretsmanager create-secret \
    --name OPENAI_API_KEY \
    --secret-string '{"OPENAI_API_KEY":"sk-xxx"}'

aws --endpoint-url=http://localhost:4566 secretsmanager create-secret \
    --name KLING_AI_API_KEY \
    --secret-string '{"KLING_AI_API_KEY":"kl-xxx"}'

aws --endpoint-url=http://localhost:4566 secretsmanager create-secret \
    --name ELEVENLABS_API_KEY \
    --secret-string '{"ELEVENLABS_API_KEY":"el-xxx"}'

# Seed test data
echo "Seeding test data..."

# Seed a test user
cat << EOF > /tmp/test-user.json
{
  "user_id": {"S": "test-user-123"},
  "email": {"S": "test@example.com"},
  "created_at": {"S": "$(date -u +%Y-%m-%dT%H:%M:%SZ)"}
}
EOF

aws --endpoint-url=http://localhost:4566 dynamodb put-item \
    --table-name users \
    --item file:///tmp/test-user.json

echo "Local development environment setup complete!"
echo ""
echo "Services:"
echo "- LocalStack: http://localhost:4566"
echo "- PostgreSQL: localhost:5432"
echo ""
echo "S3 Buckets created:"
echo "- ai-video-platform-artifacts"
echo "- ai-video-platform-webapp"
echo "- ai-video-platform-media"
echo ""
echo "DynamoDB Tables created:"
echo "- users"
echo "- products"
echo "- jobs"
echo ""
echo "To start developing:"
echo "1. Copy backend/.env.example to backend/.env"
echo "2. Update the environment variables in backend/.env"
echo "3. Start the backend: cd backend && uvicorn src.api.main:app --reload"
echo "4. Start the frontend: cd frontend && npm run dev"