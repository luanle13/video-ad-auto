#!/bin/bash
set -e

FUNCTION_NAME=$1
ZIP_FILE=$2
S3_BUCKET=$3

if [ -z "$FUNCTION_NAME" ] || [ -z "$ZIP_FILE" ] || [ -z "$S3_BUCKET" ]; then
    echo "Usage: $0 <function-name> <zip-file> <s3-bucket>"
    exit 1
fi

if [ ! -f "$ZIP_FILE" ]; then
    echo "Error: Zip file $ZIP_FILE does not exist"
    exit 1
fi

# Extract filename from path
ZIP_FILENAME=$(basename "$ZIP_FILE")

echo "Uploading $ZIP_FILE to s3://$S3_BUCKET/$ZIP_FILENAME"
aws s3 cp "$ZIP_FILE" "s3://$S3_BUCKET/$ZIP_FILENAME"

echo "Updating Lambda function $FUNCTION_NAME"
aws lambda update-function-code \
    --function-name "$FUNCTION_NAME" \
    --s3-bucket "$S3_BUCKET" \
    --s3-key "$ZIP_FILENAME"

echo "Waiting for function update to complete..."
aws lambda wait function-updated-v2 \
    --function-name "$FUNCTION_NAME"

echo "Lambda function $FUNCTION_NAME successfully updated and ready"