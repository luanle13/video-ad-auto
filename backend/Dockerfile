FROM public.ecr.aws/lambda/python:3.11-arm64

# Install build dependencies for packages that need compilation
RUN yum install -y gcc gcc-c++ make && yum clean all

# Install dependencies
COPY requirements.txt .

# Install numpy with prebuilt wheel first (avoid compilation with old GCC)
RUN pip install --no-cache-dir "numpy<2.0"

# Install remaining dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY src/ ${LAMBDA_TASK_ROOT}/src/

# Default handler - will be overridden per Lambda via image_config in Terraform
CMD ["src.lambda_api.handler"]
