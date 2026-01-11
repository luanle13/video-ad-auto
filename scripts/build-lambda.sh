#!/bin/bash
set -e

FUNCTION=$1
OUTPUT_DIR=${2:-dist}

if [ -z "$FUNCTION" ]; then
    echo "Usage: $0 <function-name> [output-dir]"
    exit 1
fi

# Create package directory
rm -rf $OUTPUT_DIR
mkdir -p $OUTPUT_DIR/package

# Install dependencies
pip install -r backend/requirements.txt -t $OUTPUT_DIR/package/

# Copy source
cp -r backend/src $OUTPUT_DIR/package/

# Create zip
cd $OUTPUT_DIR/package
zip -r ../lambda-$FUNCTION.zip . -q

echo "Created $OUTPUT_DIR/lambda-$FUNCTION.zip"